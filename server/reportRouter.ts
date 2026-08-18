import { TRPCError } from "@trpc/server";
import { randomUUID } from "node:crypto";
import { z } from "zod";
import { createReport, getReportByIdForUser, listReportsForUser, savePdfKey } from "./db";
import { generateCompatibilityArtifacts } from "./compatibilityService";
import { buildPdfArtifact, generateReportArtifacts } from "./reportService";
import { translateMarkdownToArabic } from "./reportTranslationService";
import { storageGetSignedUrl, storagePut } from "./storage";
import { compatibilityRequestSchema, reportRequestSchema } from "../shared/reportValidation";
import { protectedProcedure, router } from "./_core/trpc";

const reportIdSchema = z.object({ id: z.number().int().positive() });

async function readStoredText(key: string) {
  const signedUrl = await storageGetSignedUrl(key);
  const response = await fetch(signedUrl);
  if (!response.ok) throw new Error("The stored report could not be read.");
  return response.text();
}

function privateReportSummary(report: NonNullable<Awaited<ReturnType<typeof getReportByIdForUser>>>) {
  return {
    id: report.id,
    recipientName: report.recipientName,
    secondaryName: report.secondaryName,
    reportType: report.reportType,
    language: report.language,
    birthDate: report.birthDate,
    birthPlace: report.birthPlace,
    status: report.status,
    hasPdf: Boolean(report.pdfKey),
    createdAt: report.createdAt,
  };
}

export const reportRouter = router({
  create: protectedProcedure.input(reportRequestSchema).mutation(async ({ ctx, input }) => {
    try {
      const generated = await generateReportArtifacts(input);
      const markdown = input.language === "ar" ? await translateMarkdownToArabic(generated.markdown) : generated.markdown;
      const artifactId = randomUUID();
      const prefix = `ikigai-reports/${ctx.user.id}/${artifactId}`;
      const [markdownStored, calculationsStored] = await Promise.all([
        storagePut(`${prefix}/report.md`, markdown, "text/markdown; charset=utf-8"),
        storagePut(`${prefix}/calculations.json`, generated.calculations, "application/json; charset=utf-8"),
      ]);
      const report = await createReport({
        userId: ctx.user.id,
        recipientName: input.fullName,
        reportType: "personal",
        language: input.language,
        birthDate: input.birthDate,
        birthPlace: input.birthPlace,
        markdownKey: markdownStored.key,
        calculationsKey: calculationsStored.key,
      });
      if (!report) throw new Error("Report metadata could not be loaded.");
      return { report: privateReportSummary(report), markdown };
    } catch (error) {
      console.error("[Report] Generation failed", error);
      throw new TRPCError({
        code: "INTERNAL_SERVER_ERROR",
        message: "The report could not be generated. Check the birth place and try again.",
      });
    }
  }),

  createCompatibility: protectedProcedure.input(compatibilityRequestSchema).mutation(async ({ ctx, input }) => {
    try {
      const generated = await generateCompatibilityArtifacts(input);
      const markdown = input.language === "ar" ? await translateMarkdownToArabic(generated.markdown) : generated.markdown;
      const artifactId = randomUUID();
      const prefix = `ikigai-reports/${ctx.user.id}/${artifactId}`;
      const [markdownStored, calculationsStored] = await Promise.all([
        storagePut(`${prefix}/compatibility-report.md`, markdown, "text/markdown; charset=utf-8"),
        storagePut(`${prefix}/compatibility-calculations.json`, generated.calculations, "application/json; charset=utf-8"),
      ]);
      const report = await createReport({
        userId: ctx.user.id,
        recipientName: input.personOne.fullName,
        secondaryName: input.personTwo.fullName,
        reportType: "compatibility",
        language: input.language,
        birthDate: input.personOne.birthDate,
        birthPlace: input.personOne.birthPlace,
        markdownKey: markdownStored.key,
        calculationsKey: calculationsStored.key,
      });
      if (!report) throw new Error("Compatibility report metadata could not be loaded.");
      return { report: privateReportSummary(report), markdown };
    } catch (error) {
      console.error("[Compatibility] Generation failed", error);
      throw new TRPCError({
        code: "INTERNAL_SERVER_ERROR",
        message: "The compatibility report could not be generated. Check both birth places and try again.",
      });
    }
  }),

  list: protectedProcedure.query(async ({ ctx }) => {
    const results = await listReportsForUser(ctx.user.id);
    return results.map(report => privateReportSummary(report));
  }),

  get: protectedProcedure.input(reportIdSchema).query(async ({ ctx, input }) => {
    const report = await getReportByIdForUser(input.id, ctx.user.id);
    if (!report) throw new TRPCError({ code: "NOT_FOUND", message: "Report not found." });
    const markdown = await readStoredText(report.markdownKey);
    return { report: privateReportSummary(report), markdown };
  }),

  exportPdf: protectedProcedure.input(reportIdSchema).mutation(async ({ ctx, input }) => {
    const report = await getReportByIdForUser(input.id, ctx.user.id);
    if (!report) throw new TRPCError({ code: "NOT_FOUND", message: "Report not found." });
    if (report.pdfKey) {
      return { downloadUrl: await storageGetSignedUrl(report.pdfKey), filename: `${report.recipientName}-ikigai-report.pdf` };
    }
    try {
      const markdown = await readStoredText(report.markdownKey);
      const pdf = await buildPdfArtifact(markdown);
      const artifact = await storagePut(`ikigai-reports/${ctx.user.id}/${report.id}/report.pdf`, pdf, "application/pdf");
      await savePdfKey(report.id, ctx.user.id, artifact.key);
      return { downloadUrl: await storageGetSignedUrl(artifact.key), filename: `${report.recipientName}-ikigai-report.pdf` };
    } catch (error) {
      console.error("[Report] PDF export failed", error);
      throw new TRPCError({ code: "INTERNAL_SERVER_ERROR", message: "The PDF could not be prepared. Please try again." });
    }
  }),

  download: protectedProcedure.input(z.object({ id: z.number().int().positive(), format: z.enum(["markdown", "calculations", "pdf"]) })).mutation(async ({ ctx, input }) => {
    const report = await getReportByIdForUser(input.id, ctx.user.id);
    if (!report) throw new TRPCError({ code: "NOT_FOUND", message: "Report not found." });
    const key = input.format === "markdown" ? report.markdownKey : input.format === "calculations" ? report.calculationsKey : report.pdfKey;
    if (!key) throw new TRPCError({ code: "NOT_FOUND", message: "The requested PDF has not been exported yet." });
    return { downloadUrl: await storageGetSignedUrl(key) };
  }),
});
