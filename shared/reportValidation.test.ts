import { describe, expect, it } from "vitest";
import { compatibilityRequestSchema, reportRequestSchema } from "./reportValidation";

const validBaseInput = {
  fullName: "Casey Example",
  arabicName: "",
  birthDate: "1990-01-15",
  birthTime: "14:30",
  birthPlace: "Sample City, Example Country",
  measurements: [],
};

describe("reportRequestSchema", () => {
  it("accepts a report without optional supplied measurements", () => {
    expect(reportRequestSchema.safeParse(validBaseInput).success).toBe(true);
  });

  it("requires the full name field to remain Latin-script", () => {
    const result = reportRequestSchema.safeParse({ ...validBaseInput, fullName: "عبدالله فقيه" });
    expect(result.success).toBe(false);
  });

  it("requires a 24-hour local birth time", () => {
    const result = reportRequestSchema.safeParse({ ...validBaseInput, birthTime: "2:30 PM" });
    expect(result.success).toBe(false);
  });

  it("rejects an unconfirmed supplied measurement rather than implying a score", () => {
    const result = reportRequestSchema.safeParse({
      ...validBaseInput,
      measurements: [{ key: "big_five", result: "Openness 72", confirmed: false }],
    });
    expect(result.success).toBe(false);
  });

  it("accepts a recipient-confirmed supplied measurement unchanged", () => {
    const result = reportRequestSchema.safeParse({
      ...validBaseInput,
      measurements: [{ key: "via", result: "Top strengths: Curiosity, Love of Learning", notes: "Copied from completed VIA report.", confirmed: true }],
    });
    expect(result.success).toBe(true);
    if (result.success) expect(result.data.measurements[0]?.result).toBe("Top strengths: Curiosity, Love of Learning");
  });

  it("requires two consented people before validating a compatibility request", () => {
    const person = { fullName: "Casey Example", arabicName: "", birthDate: "1990-01-15", birthTime: "14:30", birthPlace: "Sample City, Example Country", consent: true };
    expect(compatibilityRequestSchema.safeParse({ language: "ar", personOne: person, personTwo: { ...person, fullName: "Riley Example", birthDate: "1992-04-21" }, comparisonConsent: true }).success).toBe(true);
    expect(compatibilityRequestSchema.safeParse({ language: "en", personOne: { ...person, consent: false }, personTwo: { ...person, fullName: "Riley Example", birthDate: "1992-04-21" }, comparisonConsent: true }).success).toBe(false);
  });
});
