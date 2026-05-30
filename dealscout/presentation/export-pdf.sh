#!/usr/bin/env bash
# Export DealPulse Scout HTML slides to PDF (landscape, one slide per page)
set -e

DIR="$(cd "$(dirname "$0")" && pwd)"
HTML="file://${DIR}/index.html"
OUT="${DIR}/DealPulse_Scout_Slides.pdf"

# macOS Chrome paths (try common locations)
CHROME=""
for candidate in \
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  "/Applications/Chromium.app/Contents/MacOS/Chromium" \
  "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge" \
  "google-chrome" \
  "chromium"; do
  if command -v "$candidate" &>/dev/null || [ -x "$candidate" ]; then
    CHROME="$candidate"
    break
  fi
done

if [ -z "$CHROME" ]; then
  echo "No Chrome/Chromium/Edge found."
  echo "Fallback: open index.html → Cmd+P → Save as PDF (landscape, background graphics on)"
  echo "  open ${DIR}/index.html"
  exit 1
fi

echo "Exporting slides to ${OUT}..."
"$CHROME" \
  --headless=new \
  --disable-gpu \
  --no-pdf-header-footer \
  --print-to-pdf="${OUT}" \
  "${HTML}" 2>/dev/null || \
"$CHROME" \
  --headless \
  --disable-gpu \
  --no-pdf-header-footer \
  --print-to-pdf="${OUT}" \
  "${HTML}"

if [ -f "${OUT}" ]; then
  echo "Done: ${OUT} ($(wc -c < "${OUT}" | tr -d ' ') bytes)"
else
  echo "PDF export failed. Use browser Print → Save as PDF instead."
  exit 1
fi
