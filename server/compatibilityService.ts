import type { CompatibilityRequest, ReportRequest } from "../shared/reportValidation";
import { generateReportArtifacts } from "./reportService";

type RecordValue = Record<string, unknown>;

type ComparisonRow = {
  dimension: string;
  first: string;
  second: string;
  status: "shared" | "different" | "unavailable";
  note: string;
};

function asRecord(value: unknown): RecordValue | undefined {
  return value && typeof value === "object" && !Array.isArray(value) ? value as RecordValue : undefined;
}

function atPath(source: unknown, path: string[]): unknown {
  return path.reduce<unknown>((current, key) => asRecord(current)?.[key], source);
}

function text(value: unknown): string | undefined {
  if (typeof value === "string" || typeof value === "number") return String(value);
  return undefined;
}

function firstText(source: unknown, paths: string[][]) {
  for (const path of paths) {
    const value = text(atPath(source, path));
    if (value) return value;
  }
  return undefined;
}

function table(headers: string[], rows: string[][]) {
  return [`| ${headers.join(" | ")} |`, `|${headers.map(() => "---").join("|")}|`, ...rows.map(row => `| ${row.map(cell => cell.replace(/\|/g, "\\|").replace(/\n/g, " ")).join(" | ")} |`)].join("\n");
}

function compare(dimension: string, first: string | undefined, second: string | undefined, sharedNote: string, differentNote: string): ComparisonRow {
  if (!first || !second) return { dimension, first: first || "Unavailable", second: second || "Unavailable", status: "unavailable", note: "This calculated output was unavailable for one or both people in this run." };
  const shared = first.toLocaleLowerCase() === second.toLocaleLowerCase();
  return { dimension, first, second, status: shared ? "shared" : "different", note: shared ? sharedNote : differentNote };
}

function inputForIndividual(person: CompatibilityRequest["personOne"]): ReportRequest {
  return {
    fullName: person.fullName,
    arabicName: person.arabicName,
    birthDate: person.birthDate,
    birthTime: person.birthTime,
    birthPlace: person.birthPlace,
    language: "en",
    measurements: [],
  };
}

function buildCompatibilityMarkdown(input: CompatibilityRequest, firstRaw: RecordValue, secondRaw: RecordValue) {
  const firstCalculations = asRecord(firstRaw.calculations) || {};
  const secondCalculations = asRecord(secondRaw.calculations) || {};
  const rows: ComparisonRow[] = [
    compare("Life Path", firstText(firstCalculations, [["numerology", "life_path", "display"]]), firstText(secondCalculations, [["numerology", "life_path", "display"]]), "The same numerology reduction appears in both calculation records.", "The two records show different Life Path reductions."),
    compare("Personal Year", firstText(firstCalculations, [["numerology", "personal_year", "display"]]), firstText(secondCalculations, [["numerology", "personal_year", "display"]]), "Both calculation records place you in the same Personal Year number for this report year.", "The calculation records place you in different Personal Year numbers for this report year."),
    compare("Tropical Sun sign", firstText(firstCalculations, [["chart", "tropical", "planets", "Sun", "sign"], ["chart", "tropical", "planets", "Sun", "formatted"]]), firstText(secondCalculations, [["chart", "tropical", "planets", "Sun", "sign"], ["chart", "tropical", "planets", "Sun", "formatted"]]), "The same calculated Sun placement appears in both records.", "The calculated Sun placements differ."),
    compare("Midheaven sign", firstText(firstCalculations, [["chart", "tropical", "midheaven", "sign"], ["chart", "tropical", "midheaven", "formatted"]]), firstText(secondCalculations, [["chart", "tropical", "midheaven", "sign"], ["chart", "tropical", "midheaven", "formatted"]]), "The same calculated Midheaven placement appears in both records.", "The calculated Midheaven placements differ."),
    compare("Human Design type", firstText(firstCalculations, [["extended", "human_design", "type"]]), firstText(secondCalculations, [["extended", "human_design", "type"]]), "The same calculated Human Design type appears in both records.", "The calculated Human Design types differ."),
    compare("Human Design profile", firstText(firstCalculations, [["extended", "human_design", "profile"]]), firstText(secondCalculations, [["extended", "human_design", "profile"]]), "The same calculated Human Design profile appears in both records.", "The calculated Human Design profiles differ."),
    compare("Chinese zodiac", firstText(firstCalculations, [["extended", "bazi", "zodiac_animal"]]), firstText(secondCalculations, [["extended", "bazi", "zodiac_animal"]]), "The same calculated Chinese zodiac animal appears in both records.", "The calculated Chinese zodiac animals differ."),
  ];

  const comparable = rows.filter(row => row.status !== "unavailable");
  const shared = comparable.filter(row => row.status === "shared");
  const overall = comparable.length ? Math.round(35 + (shared.length / comparable.length) * 45) : 35;
  const directionRows = rows.filter(row => ["Life Path", "Personal Year", "Midheaven sign"].includes(row.dimension) && row.status !== "unavailable");
  const rhythmRows = rows.filter(row => ["Human Design type", "Human Design profile", "Chinese zodiac"].includes(row.dimension) && row.status !== "unavailable");
  const scoreFor = (items: ComparisonRow[]) => items.length ? Math.round(30 + (items.filter(item => item.status === "shared").length / items.length) * 50) : 30;

  const summary = shared.length
    ? `${shared.length} of ${comparable.length} comparable calculated outputs match exactly in this run. The remaining visible outputs differ, which gives you specific conversation points rather than a verdict.`
    : "No directly matching calculated outputs were available in this run. The report therefore focuses on transparent side-by-side differences rather than an overall claim.";

  const sharedRows = rows.filter(row => row.status === "shared");
  const differentRows = rows.filter(row => row.status === "different");
  const locationOne = `${input.personOne.birthDate} · ${input.personOne.birthPlace}`;
  const locationTwo = `${input.personTwo.birthDate} · ${input.personTwo.birthPlace}`;

  return `<div class="doc-title">IKIGAI COMPATIBILITY REPORT</div>
<div class="doc-name">${input.personOne.fullName} × ${input.personTwo.fullName}</div>
<div class="doc-meta">${locationOne} &nbsp; | &nbsp; ${locationTwo}</div>
<div class="doc-prepared">A comparison of two calculation records · Birth-data-first edition</div>

> **Symbolic alignment index: ${overall}% — ${shared.length} exact match${shared.length === 1 ? "" : "es"} across ${comparable.length} comparable calculated outputs. This is a transparent heuristic, not a scientific measurement or relationship verdict.**

# 1. The short answer

${summary}

${table(["Dimension", "Symbolic alignment index", "What it reflects"], [
  ["Direction and timing", `${scoreFor(directionRows)}%`, "Life Path, Personal Year and Midheaven comparisons available in this run."],
  ["Work and energy rhythm", `${scoreFor(rhythmRows)}%`, "Human Design and zodiac comparison points available in this run."],
  ["Overall calculated overlap", `${overall}%`, "The proportion of matching values among comparable calculated outputs."],
])}

# 2. The similarities — ranked by calculation match

${sharedRows.length ? table(["#", "Shared calculated point", "Why it appears"], sharedRows.map((row, index) => [String(index + 1), `${row.dimension}: ${row.first}`, row.note])) : "No exact shared calculated outputs were available in this run. This is not evidence of incompatibility; it only means the visible deterministic values differed."}

# 3. The differences — conversation points, not friction claims

${differentRows.length ? table(["Axis", input.personOne.fullName, input.personTwo.fullName, "What the comparison shows"], differentRows.map(row => [row.dimension, row.first, row.second, row.note])) : "All comparable outputs matched exactly in this run. Treat that as a prompt for conversation, not proof of compatibility."}

# 4. What to do with this comparison

1. Start with the rows that actually matter to a shared choice, such as workload, decision timing, communication, or a joint project.
2. Compare the symbolic output against lived evidence: actual patterns, completed assessments, and explicit agreements.
3. If either person adds a real Group A measurement later, keep it separate from this calculated comparison; do not infer it from birth data.

# 5. Calculation record and limitations

${table(["Person", "Input used"], [
  [input.personOne.fullName, `${input.personOne.birthDate} · ${input.personOne.birthTime} local · ${input.personOne.birthPlace}`],
  [input.personTwo.fullName, `${input.personTwo.birthDate} · ${input.personTwo.birthTime} local · ${input.personTwo.birthPlace}`],
])}

> **Method boundary:** This report compares deterministic outputs from symbolic systems implemented in the report kit. It does not calculate personality, emotional health, relationship quality, marriage suitability, hiring fit, values, skills, or future outcomes. Do not make a high-stakes life decision from the percentage above. Use it only as a structured prompt for discussion alongside real-world evidence.`;
}

export async function generateCompatibilityArtifacts(input: CompatibilityRequest) {
  const [first, second] = await Promise.all([
    generateReportArtifacts(inputForIndividual(input.personOne)),
    generateReportArtifacts(inputForIndividual(input.personTwo)),
  ]);
  const firstRaw = JSON.parse(first.calculations) as RecordValue;
  const secondRaw = JSON.parse(second.calculations) as RecordValue;
  const markdown = buildCompatibilityMarkdown(input, firstRaw, secondRaw);
  const calculations = JSON.stringify({
    report_type: "compatibility",
    language: input.language,
    person_one: { name: input.personOne.fullName, calculations: firstRaw },
    person_two: { name: input.personTwo.fullName, calculations: secondRaw },
  }, null, 2);
  return { markdown, calculations };
}
