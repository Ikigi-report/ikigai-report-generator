import { buildPdfArtifact } from "../server/reportService.ts";

const pdf = await buildPdfArtifact("<div class=\"doc-title\">IKIGAI CALCULATION REPORT</div>\n\n# Test export\n\n| Group | Status |\n|---|---|\n| B | Calculated symbolic output |\n");

if (!pdf.subarray(0, 4).equals(Buffer.from("%PDF"))) {
  throw new Error("PDF export did not return a valid PDF header.");
}

console.log("On-demand PDF export smoke test passed.");
