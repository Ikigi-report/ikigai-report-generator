import { afterEach, describe, expect, it, vi } from "vitest";
import { openDownload } from "../client/src/lib/openDownload";

describe("openDownload", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("uses a safe anchor navigation for a valid relative report download", () => {
    const click = vi.fn();
    const remove = vi.fn();
    const appendChild = vi.fn();
    const anchor = { href: "", target: "", rel: "", click, remove };
    vi.stubGlobal("window", { location: { origin: "https://app.example" } });
    vi.stubGlobal("document", { createElement: vi.fn(() => anchor), body: { appendChild } });

    openDownload("/manus-storage/reports/compatibility.pdf");

    expect(anchor.href).toBe("https://app.example/manus-storage/reports/compatibility.pdf");
    expect(anchor.target).toBe("_blank");
    expect(anchor.rel).toBe("noopener noreferrer");
    expect(appendChild).toHaveBeenCalledWith(anchor);
    expect(click).toHaveBeenCalledOnce();
    expect(remove).toHaveBeenCalledOnce();
  });
});
