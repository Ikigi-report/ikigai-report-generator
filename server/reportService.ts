import { spawn } from "node:child_process";
import { mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import type { ReportRequest } from "../shared/reportValidation";

const kitRoot = path.resolve(process.cwd(), "report-kit");
const generatorPath = path.join(kitRoot, "scripts", "generate_report.py");
const printStylesheetPath = path.join(kitRoot, "ikigai.css");

type ProcessResult = { stdout: string; stderr: string };

function runProcess(command: string, args: string[], env: NodeJS.ProcessEnv = process.env): Promise<ProcessResult> {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, { cwd: kitRoot, env, shell: false });
    let stdout = "";
    let stderr = "";
    child.stdout.on("data", chunk => { stdout += chunk.toString(); });
    child.stderr.on("data", chunk => { stderr += chunk.toString(); });
    child.on("error", reject);
    child.on("close", code => {
      if (code === 0) return resolve({ stdout, stderr });
      reject(new Error(stderr.trim() || stdout.trim() || `Report process exited with code ${code}.`));
    });
  });
}

function testPayload(input: ReportRequest) {
  return {
    tests: Object.fromEntries(
      input.measurements.map(item => [item.key, {
        result: item.result,
        ...(item.notes ? { interpretation: item.notes } : {}),
      }]),
    ),
  };
}

export async function generateReportArtifacts(input: ReportRequest) {
  const workDir = await mkdtemp(path.join(tmpdir(), "ikigai-report-"));
  const markdownPath = path.join(workDir, "report.md");
  const calculationsPath = path.join(workDir, "calculations.json");
  const testsPath = path.join(workDir, "supplied-measurements.json");

  try {
    const args = [generatorPath, "--name", input.fullName, "--date", input.birthDate, "--time", input.birthTime, "--place", input.birthPlace, "--out", markdownPath, "--data-out", calculationsPath];
    if (input.arabicName) args.push("--name-ar", input.arabicName);
    if (input.measurements.length > 0) {
      await writeFile(testsPath, JSON.stringify(testPayload(input)), "utf8");
      args.push("--tests", testsPath);
    }
    await runProcess("python3", args);
    const [markdown, calculations] = await Promise.all([readFile(markdownPath, "utf8"), readFile(calculationsPath, "utf8")]);
    return { markdown, calculations };
  } finally {
    await rm(workDir, { recursive: true, force: true });
  }
}

export async function buildPdfArtifact(markdown: string) {
  const workDir = await mkdtemp(path.join(tmpdir(), "ikigai-pdf-"));
  const markdownPath = path.join(workDir, "report.md");
  const htmlPath = path.join(workDir, "report.html");
  const pdfPath = path.join(workDir, "report.pdf");
  try {
    await writeFile(markdownPath, markdown, "utf8");
    await runProcess("pandoc", [
      markdownPath,
      "--from", "markdown+raw_html+pipe_tables+fenced_divs",
      "--to", "html5",
      "--standalone",
      "--metadata", "title=Ikigai Calculation Report",
      "--css", printStylesheetPath,
      "--output", htmlPath,
    ]);
    await runProcess(process.env.BROWSER_BIN || "chromium", [
      "--headless",
      "--disable-gpu",
      "--no-sandbox",
      "--disable-dev-shm-usage",
      "--no-pdf-header-footer",
      `--print-to-pdf=${pdfPath}`,
      htmlPath,
    ]);
    return await readFile(pdfPath);
  } finally {
    await rm(workDir, { recursive: true, force: true });
  }
}
