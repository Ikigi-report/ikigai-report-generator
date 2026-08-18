import { beforeEach, describe, expect, it, vi } from "vitest";
import { appRouter } from "./routers";
import type { TrpcContext } from "./_core/context";
import * as compatibilityService from "./compatibilityService";
import * as db from "./db";
import * as reportService from "./reportService";
import * as translationService from "./reportTranslationService";
import * as storage from "./storage";

vi.mock("./db", () => ({
  createReport: vi.fn(),
  getReportByIdForUser: vi.fn(),
  listReportsForUser: vi.fn(),
  savePdfKey: vi.fn(),
}));
vi.mock("./reportService", () => ({
  buildPdfArtifact: vi.fn(),
  generateReportArtifacts: vi.fn(),
}));
vi.mock("./compatibilityService", () => ({
  generateCompatibilityArtifacts: vi.fn(),
}));
vi.mock("./reportTranslationService", () => ({
  translateMarkdownToArabic: vi.fn(),
}));
vi.mock("./storage", () => ({
  storageGetSignedUrl: vi.fn(),
  storagePut: vi.fn(),
}));

const report = {
  id: 24,
  userId: 7,
  recipientName: "Casey Example",
  secondaryName: null,
  reportType: "personal" as const,
  language: "en" as const,
  birthDate: "1990-01-15",
  birthPlace: "Sample City, Example Country",
  status: "ready" as const,
  markdownKey: "reports/7/report.md",
  calculationsKey: "reports/7/calculations.json",
  pdfKey: null,
  errorMessage: null,
  createdAt: new Date("2026-08-18T00:00:00Z"),
  updatedAt: new Date("2026-08-18T00:00:00Z"),
};

function callerForUser() {
  const ctx = {
    user: {
      id: 7,
      openId: "user-7",
      email: "alex@example.com",
      name: "Alex",
      loginMethod: "manus",
      role: "user" as const,
      createdAt: new Date(),
      updatedAt: new Date(),
      lastSignedIn: new Date(),
    },
  } as TrpcContext;
  return appRouter.createCaller(ctx);
}

describe("reports router", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("generates and stores Markdown and JSON records under the authenticated user", async () => {
    vi.mocked(reportService.generateReportArtifacts).mockResolvedValue({ markdown: "# Generated", calculations: '{"calculations":{}}' });
    vi.mocked(storage.storagePut)
      .mockResolvedValueOnce({ key: "reports/7/report.md", url: "/manus-storage/reports/7/report.md" })
      .mockResolvedValueOnce({ key: "reports/7/calculations.json", url: "/manus-storage/reports/7/calculations.json" });
    vi.mocked(db.createReport).mockResolvedValue(report);

    const result = await callerForUser().reports.create({
      fullName: "Casey Example", arabicName: "", birthDate: "1990-01-15", birthTime: "14:30", birthPlace: "Sample City, Example Country", measurements: [],
    });

    expect(result.markdown).toBe("# Generated");
    expect(db.createReport).toHaveBeenCalledWith(expect.objectContaining({ userId: 7, reportType: "personal", language: "en", markdownKey: "reports/7/report.md", calculationsKey: "reports/7/calculations.json" }));
    expect(storage.storagePut).toHaveBeenCalledTimes(2);
  });

  it("stores a consented two-person compatibility record under the authenticated user", async () => {
    vi.mocked(compatibilityService.generateCompatibilityArtifacts).mockResolvedValue({ markdown: "# Compatibility", calculations: '{"report_type":"compatibility"}' });
    vi.mocked(storage.storagePut)
      .mockResolvedValueOnce({ key: "reports/7/compatibility-report.md", url: "/manus-storage/reports/7/compatibility-report.md" })
      .mockResolvedValueOnce({ key: "reports/7/compatibility-calculations.json", url: "/manus-storage/reports/7/compatibility-calculations.json" });
    vi.mocked(db.createReport).mockResolvedValue({ ...report, secondaryName: "Riley Example", reportType: "compatibility" });

    const result = await callerForUser().reports.createCompatibility({
      language: "en",
      personOne: { fullName: "Casey Example", arabicName: "", birthDate: "1990-01-15", birthTime: "14:30", birthPlace: "Sample City, Example Country", consent: true },
      personTwo: { fullName: "Riley Example", arabicName: "", birthDate: "1992-04-21", birthTime: "10:15", birthPlace: "Other City, Example Country", consent: true },
      comparisonConsent: true,
    });

    expect(result.markdown).toBe("# Compatibility");
    expect(db.createReport).toHaveBeenCalledWith(expect.objectContaining({ userId: 7, recipientName: "Casey Example", secondaryName: "Riley Example", reportType: "compatibility", language: "en" }));
  });

  it("translates Arabic personal report output before storage", async () => {
    vi.mocked(reportService.generateReportArtifacts).mockResolvedValue({ markdown: "# English report", calculations: '{"calculations":{}}' });
    vi.mocked(translationService.translateMarkdownToArabic).mockResolvedValue("<div dir=\"rtl\"># تقرير</div>");
    vi.mocked(storage.storagePut)
      .mockResolvedValueOnce({ key: "reports/7/report-ar.md", url: "/manus-storage/reports/7/report-ar.md" })
      .mockResolvedValueOnce({ key: "reports/7/calculations.json", url: "/manus-storage/reports/7/calculations.json" });
    vi.mocked(db.createReport).mockResolvedValue({ ...report, language: "ar" });

    await callerForUser().reports.create({
      fullName: "Casey Example", arabicName: "", birthDate: "1990-01-15", birthTime: "14:30", birthPlace: "Sample City, Example Country", language: "ar", measurements: [],
    });

    expect(translationService.translateMarkdownToArabic).toHaveBeenCalledWith("# English report");
    expect(storage.storagePut).toHaveBeenCalledWith(expect.any(String), "<div dir=\"rtl\"># تقرير</div>", "text/markdown; charset=utf-8");
  });

  it("lists only the authenticated user's report records", async () => {
    vi.mocked(db.listReportsForUser).mockResolvedValue([report]);
    const result = await callerForUser().reports.list();
    expect(db.listReportsForUser).toHaveBeenCalledWith(7);
    expect(result).toEqual([expect.objectContaining({ id: 24, recipientName: "Casey Example", reportType: "personal", hasPdf: false })]);
  });

  it("reads Markdown through a user-scoped report lookup", async () => {
    vi.mocked(db.getReportByIdForUser).mockResolvedValue(report);
    vi.mocked(storage.storageGetSignedUrl).mockResolvedValue("https://storage.example/report.md");
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, text: async () => "# Stored report" }));

    const result = await callerForUser().reports.get({ id: 24 });

    expect(db.getReportByIdForUser).toHaveBeenCalledWith(24, 7);
    expect(result.markdown).toBe("# Stored report");
  });

  it("returns a secure download URL only after a user-scoped lookup", async () => {
    vi.mocked(db.getReportByIdForUser).mockResolvedValue(report);
    vi.mocked(storage.storageGetSignedUrl).mockResolvedValue("https://storage.example/calculations.json");
    await expect(callerForUser().reports.download({ id: 24, format: "calculations" })).resolves.toEqual({ downloadUrl: "https://storage.example/calculations.json" });
    expect(db.getReportByIdForUser).toHaveBeenCalledWith(24, 7);
  });

  it("reuses a previously exported PDF rather than rebuilding it", async () => {
    vi.mocked(db.getReportByIdForUser).mockResolvedValue({ ...report, pdfKey: "reports/7/report.pdf" });
    vi.mocked(storage.storageGetSignedUrl).mockResolvedValue("https://storage.example/report.pdf");
    await expect(callerForUser().reports.exportPdf({ id: 24 })).resolves.toEqual({ downloadUrl: "https://storage.example/report.pdf", filename: "Casey Example-ikigai-report.pdf" });
    expect(reportService.buildPdfArtifact).not.toHaveBeenCalled();
  });

  it("builds and saves a PDF for a compatibility report when no export exists yet", async () => {
    const compatibilityReport = { ...report, secondaryName: "Riley Example", reportType: "compatibility" as const, pdfKey: null };
    vi.mocked(db.getReportByIdForUser).mockResolvedValue(compatibilityReport);
    vi.mocked(storage.storageGetSignedUrl)
      .mockResolvedValueOnce("https://storage.example/compatibility.md")
      .mockResolvedValueOnce("https://storage.example/compatibility.pdf");
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, text: async () => "# Compatibility" }));
    vi.mocked(reportService.buildPdfArtifact).mockResolvedValue(Buffer.from("%PDF-1.7"));
    vi.mocked(storage.storagePut).mockResolvedValue({ key: "reports/7/24/report.pdf", url: "/manus-storage/reports/7/24/report.pdf" });

    await expect(callerForUser().reports.exportPdf({ id: 24 })).resolves.toEqual({ downloadUrl: "https://storage.example/compatibility.pdf", filename: "Casey Example-ikigai-report.pdf" });
    expect(db.savePdfKey).toHaveBeenCalledWith(24, 7, "reports/7/24/report.pdf");
  });

  it("exports Arabic compatibility Markdown with special-character names through a signed HTTPS link", async () => {
    const arabicCompatibilityReport = {
      ...report,
      recipientName: "Casey O'Neil",
      secondaryName: "Riley D'Angelo",
      reportType: "compatibility" as const,
      language: "ar" as const,
      pdfKey: null,
    };
    vi.mocked(db.getReportByIdForUser).mockResolvedValue(arabicCompatibilityReport);
    vi.mocked(storage.storageGetSignedUrl)
      .mockResolvedValueOnce("https://storage.example/compatibility-ar.md?signature=abc%2F123")
      .mockResolvedValueOnce("https://storage.example/compatibility-ar.pdf?signature=abc%2F123");
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, text: async () => '<div dir="rtl"># تقرير التوافق — اختبار</div>' }));
    vi.mocked(reportService.buildPdfArtifact).mockResolvedValue(Buffer.from("%PDF-1.7"));
    vi.mocked(storage.storagePut).mockResolvedValue({ key: "reports/7/24/compatibility-ar.pdf", url: "/manus-storage/reports/7/24/compatibility-ar.pdf" });

    await expect(callerForUser().reports.exportPdf({ id: 24 })).resolves.toEqual({
      downloadUrl: "https://storage.example/compatibility-ar.pdf?signature=abc%2F123",
      filename: "Casey O'Neil-ikigai-report.pdf",
    });
    expect(reportService.buildPdfArtifact).toHaveBeenCalledWith('<div dir="rtl"># تقرير التوافق — اختبار</div>');
    expect(db.savePdfKey).toHaveBeenCalledWith(24, 7, "reports/7/24/compatibility-ar.pdf");
  });

  it("does not expose a report that the user-scoped lookup cannot find", async () => {
    vi.mocked(db.getReportByIdForUser).mockResolvedValue(null);
    await expect(callerForUser().reports.get({ id: 999 })).rejects.toMatchObject({ code: "NOT_FOUND" });
  });
});
