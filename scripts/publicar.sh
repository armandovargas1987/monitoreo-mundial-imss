#!/bin/bash
# Publica el monitor en internet (túnel Cloudflare) para compartir con terceros.
set -e
cd "$(dirname "$0")/.."
ROOT="$(pwd)"
PORT="${PORT:-8765}"
CF="$ROOT/bin/cloudflared"

if ! lsof -i ":$PORT" >/dev/null 2>&1; then
  echo "→ Servidor local en puerto $PORT…"
  python3 -m http.server "$PORT" &
  sleep 1
fi

if [[ ! -x "$CF" ]]; then
  ARCH=$(uname -m | sed 's/x86_64/amd64/;s/arm64/arm64/')
  mkdir -p bin
  curl -fsSL "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-darwin-${ARCH}.tgz" -o /tmp/cloudflared.tgz
  tar -xzf /tmp/cloudflared.tgz -C bin cloudflared
  chmod +x bin/cloudflared
fi

echo ""
echo "Liga pública (monitor):"
echo "  https://…trycloudflare.com/monitor.html"
echo ""
echo "Mantén esta ventana abierta. Ctrl+C para cerrar el túnel."
echo ""

exec "$CF" tunnel --url "http://127.0.0.1:$PORT"
