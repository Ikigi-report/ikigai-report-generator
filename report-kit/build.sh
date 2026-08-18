#!/usr/bin/env bash
# Build a styled PDF report from markdown.
#
#   ./build.sh my-report.md              -> my-report.pdf
#   ./build.sh my-report.md out.pdf      -> out.pdf
#
# Requires: pandoc, and one Chromium-based browser.
# Override detection with:  BROWSER_BIN=/path/to/browser ./build.sh my-report.md
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"

SRC="${1:?usage: build.sh <input.md> [output.pdf]}"
OUT="${2:-${SRC%.md}.pdf}"
HTML="$DIR/.build.html"

command -v pandoc >/dev/null 2>&1 || {
  echo "error: pandoc not found. Install it (macOS: brew install pandoc)." >&2
  exit 1
}

find_browser() {
  if [[ -n "${BROWSER_BIN:-}" ]]; then
    echo "$BROWSER_BIN"; return
  fi
  local candidates=(
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    "/Applications/Chromium.app/Contents/MacOS/Chromium"
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"
    "/Applications/Opera GX.app/Contents/MacOS/Opera"
    "/Applications/Opera.app/Contents/MacOS/Opera"
  )
  local c
  for c in "${candidates[@]}"; do
    [[ -x "$c" ]] && { echo "$c"; return; }
  done
  for c in google-chrome google-chrome-stable chromium chromium-browser brave-browser microsoft-edge; do
    command -v "$c" >/dev/null 2>&1 && { command -v "$c"; return; }
  done
  return 1
}

BROWSER="$(find_browser)" || {
  echo "error: no Chromium-based browser found." >&2
  echo "Install Chrome/Chromium/Brave/Edge, or set BROWSER_BIN=/path/to/browser." >&2
  exit 1
}

echo "pandoc  -> $HTML"
pandoc "$SRC" \
  --from markdown+raw_html+pipe_tables+fenced_divs \
  --to html5 \
  --standalone \
  --metadata title="Report" \
  --css ikigai.css \
  --output "$HTML"

echo "browser -> $OUT   ($(basename "$BROWSER"))"
"$BROWSER" \
  --headless \
  --disable-gpu \
  --no-pdf-header-footer \
  --print-to-pdf="$OUT" \
  "$HTML" >/dev/null 2>&1

rm -f "$HTML"
echo "built: $OUT"
