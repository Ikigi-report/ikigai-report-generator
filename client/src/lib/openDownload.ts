import { normalizeDownloadUrl } from "@shared/downloadUrl";

export function openDownload(downloadUrl: string): void {
  const normalizedUrl = normalizeDownloadUrl(downloadUrl, window.location.origin);
  const link = document.createElement("a");
  link.href = normalizedUrl;
  link.target = "_blank";
  link.rel = "noopener noreferrer";
  document.body.appendChild(link);
  link.click();
  link.remove();
}
