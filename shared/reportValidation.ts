import { z } from "zod";

export const supportedMeasurementKeys = ["big_five", "via", "wdq", "cbi"] as const;
export const reportLanguages = ["en", "ar"] as const;

export type MeasurementKey = (typeof supportedMeasurementKeys)[number];

export const measurementLabels: Record<MeasurementKey, string> = {
  big_five: "Big Five",
  via: "VIA Character Strengths",
  wdq: "Work Design Questionnaire",
  cbi: "Copenhagen Burnout Inventory",
};

const latinNamePattern = /^[A-Za-zÀ-ÖØ-öø-ÿ' -]+$/;
const arabicNamePattern = /^[\u0600-\u06FF\s'’-]+$/;
const isoDatePattern = /^\d{4}-\d{2}-\d{2}$/;
const time24Pattern = /^(?:[01]\d|2[0-3]):[0-5]\d$/;

function isValidBirthDate(value: string) {
  if (!isoDatePattern.test(value)) return false;
  const parsed = new Date(`${value}T12:00:00Z`);
  return !Number.isNaN(parsed.getTime()) && parsed.toISOString().slice(0, 10) === value && parsed <= new Date();
}

export const suppliedMeasurementSchema = z.object({
  key: z.enum(supportedMeasurementKeys),
  result: z.string().trim().min(2, "Enter a real result or remove this measurement.").max(3500),
  notes: z.string().trim().max(1200).optional(),
  confirmed: z.literal(true, { error: "Confirm that this is a result you supplied from a completed test." }),
});

export const birthDataSchema = z.object({
  fullName: z.string().trim().min(2).max(160).regex(latinNamePattern, "Use Latin letters, spaces, apostrophes, or hyphens only."),
  arabicName: z.string().trim().max(160).regex(arabicNamePattern, "Use Arabic characters only.").optional().or(z.literal("")),
  birthDate: z.string().refine(isValidBirthDate, "Use a real past or current ISO date in YYYY-MM-DD format."),
  birthTime: z.string().regex(time24Pattern, "Use a 24-hour time in HH:MM format."),
  birthPlace: z.string().trim().min(2).max(240),
});

export const reportRequestSchema = birthDataSchema.extend({
  language: z.enum(reportLanguages).default("en"),
  measurements: z.array(suppliedMeasurementSchema).max(supportedMeasurementKeys.length).default([]),
}).superRefine((value, ctx) => {
  const keys = value.measurements.map(item => item.key);
  if (new Set(keys).size !== keys.length) {
    ctx.addIssue({ code: "custom", path: ["measurements"], message: "Each supplied measurement can be added only once." });
  }
});

export type ReportRequest = z.infer<typeof reportRequestSchema>;

export const compatibilityPersonSchema = birthDataSchema.extend({
  consent: z.literal(true, { error: "Confirm that this person has agreed to this private compatibility report." }),
});

export const compatibilityRequestSchema = z.object({
  language: z.enum(reportLanguages).default("en"),
  personOne: compatibilityPersonSchema,
  personTwo: compatibilityPersonSchema,
  comparisonConsent: z.literal(true, { error: "Confirm that both people agreed to this private symbolic comparison." }),
}).superRefine((value, ctx) => {
  if (value.personOne.fullName.trim().toLocaleLowerCase() === value.personTwo.fullName.trim().toLocaleLowerCase() && value.personOne.birthDate === value.personTwo.birthDate) {
    ctx.addIssue({ code: "custom", path: ["personTwo", "fullName"], message: "Enter a second person with distinct birth details." });
  }
});

export type CompatibilityRequest = z.infer<typeof compatibilityRequestSchema>;
