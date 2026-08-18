import { generateCompatibilityArtifacts } from "../server/compatibilityService.ts";

const artifacts = await generateCompatibilityArtifacts({
  language: "en",
  personOne: { fullName: "Casey Example", arabicName: "", birthDate: "1990-01-15", birthTime: "14:30", birthPlace: "Sample City, Example Country", consent: true },
  personTwo: { fullName: "Riley Example", arabicName: "", birthDate: "1992-04-21", birthTime: "10:15", birthPlace: "Other City, Example Country", consent: true },
  comparisonConsent: true,
});

if (!artifacts.markdown.includes("IKIGAI COMPATIBILITY REPORT")) throw new Error("Compatibility Markdown did not include its report title.");
if (!artifacts.markdown.includes("Calculation record and limitations")) throw new Error("Compatibility Markdown did not include the method boundary.");
if (!artifacts.calculations.includes("person_one") || !artifacts.calculations.includes("person_two")) throw new Error("Compatibility JSON did not retain both calculation records.");

console.log("Compatibility generator smoke test passed.");
