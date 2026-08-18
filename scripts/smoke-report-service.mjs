import { generateReportArtifacts } from "../server/reportService.ts";

const artifacts = await generateReportArtifacts({
  fullName: "Casey Example",
  arabicName: "",
  birthDate: "1990-01-15",
  birthTime: "14:30",
  birthPlace: "Sample City, Example Country",
  measurements: [],
});

if (!artifacts.markdown.includes("IKIGAI CALCULATION REPORT")) {
  throw new Error("Generated Markdown did not contain the report title.");
}
if (!artifacts.calculations.includes("calculations")) {
  throw new Error("Generated JSON did not contain calculation data.");
}

console.log("Node-to-Python generator smoke test passed.");
