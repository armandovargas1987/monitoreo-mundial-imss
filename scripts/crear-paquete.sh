#!/bin/bash
set -e
cd "$(dirname "$0")/.."
OUT="${1:-$HOME/Downloads/monitoreo-imss-mundial2026.zip}"
zip -r "$OUT" \
  index.html monitor.html acceso.html admin.html preview.html fanfest-cdmx.html \
  assets data .nojekyll \
  -x "*.DS_Store"
echo ""
echo "Paquete listo: $OUT"
echo "Súbelo en https://app.netlify.com/drop o en Add new site → Deploy manually"
