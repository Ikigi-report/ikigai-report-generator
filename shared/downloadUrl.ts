export function normalizeDownloadUrl(downloadUrl: string, origin: string): string {
  if (typeof downloadUrl !== "string" || !downloadUrl.trim()) {
    throw new Error("The export service returned an empty download link.");
  }

  let resolved: URL;
  try {
    resolved = new URL(downloadUrl, origin);
  } catch {
    throw new Error("The export service returned an invalid download link.");
  }

  if (resolved.protocol !== "https:" && resolved.protocol !== "http:") {
    throw new Error("The export service returned an unsupported download link.");
  }

  return resolved.toString();
}
