import { describe, expect, it } from "vitest";
import { normalizeDownloadUrl } from "./downloadUrl";

describe("normalizeDownloadUrl", () => {
  it("accepts an absolute signed download URL", () => {
    expect(normalizeDownloadUrl("https://storage.example/report.pdf?signature=abc", "https://app.example")).toBe("https://storage.example/report.pdf?signature=abc");
  });

  it("resolves a same-origin storage path", () => {
    expect(normalizeDownloadUrl("/manus-storage/reports/report.pdf", "https://app.example")).toBe("https://app.example/manus-storage/reports/report.pdf");
  });

  it("rejects malformed and unsupported download links before browser navigation", () => {
    expect(() => normalizeDownloadUrl("https://[invalid", "https://app.example")).toThrow("invalid download link");
    expect(() => normalizeDownloadUrl("file:///tmp/report.pdf", "https://app.example")).toThrow("unsupported download link");
  });
});
