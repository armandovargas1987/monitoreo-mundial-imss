#!/bin/bash
# Ejecuta la síntesis diaria SSC-CDMX (descarga, parseo y correo).
# Automatización principal: .github/workflows/sintesis-movilizaciones-diaria.yml
# Uso local/manual:
#   ./scripts/ejecutar_sintesis_diaria.sh

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

export PATH="/usr/local/bin:/usr/bin:/bin:$PATH"

python3 "$ROOT/scripts/sync_movilizaciones_ssc.py"
python3 "$ROOT/scripts/generar_sintesis_ssc.py" --enviar-correo
