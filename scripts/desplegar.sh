#!/bin/bash
# Despliegue permanente en GitHub Pages (funciona aunque apagues la Mac).
set -e
cd "$(dirname "$0")/.."
ROOT="$(pwd)"
GH="$ROOT/bin/gh"

if [[ ! -x "$GH" ]]; then
  ARCH=$(uname -m | sed 's/x86_64/amd64/;s/arm64/arm64/')
  mkdir -p bin
  URL=$(curl -fsSL "https://api.github.com/repos/cli/cli/releases/latest" | python3 -c "import sys,json; r=json.load(sys.stdin); print([a['browser_download_url'] for a in r['assets'] if 'macOS_${ARCH}' in a['name'] or ('macOS' in a['name'] and '${ARCH}' in a['name'])][0])")
  curl -fsSL "$URL" -o /tmp/gh.zip
  unzip -qo /tmp/gh.zip -d /tmp/ghdir
  cp "$(find /tmp/ghdir -name gh -type f | head -1)" "$GH"
  chmod +x "$GH"
fi

if ! "$GH" auth status >/dev/null 2>&1; then
  echo ""
  echo "Primera vez: inicia sesión en GitHub (se abre el navegador)."
  echo ""
  "$GH" auth login -h github.com -p https -w
fi

REPO_NAME="${REPO_NAME:-monitoreo-mundial-imss}"

if [[ -z "$(git config user.email 2>/dev/null)" ]]; then
  git config user.email "$("$GH" api user -q .email)"
  git config user.name "$("$GH" api user -q .login)"
fi

git add -A
if git diff --cached --quiet; then
  echo "Sin cambios nuevos que subir."
else
  git commit -m "Publicar centro de monitoreo IMSS Mundial 2026"
fi

if ! git remote get-url origin >/dev/null 2>&1; then
  "$GH" repo create "$REPO_NAME" --public --source=. --remote=origin --push --description "Centro de Monitoreo Marchas y Manifestaciones · Mundial 2026 · IMSS"
else
  git push -u origin main
fi

OWNER=$("$GH" api user -q .login)
"$GH" api -X POST "/repos/$OWNER/$REPO_NAME/pages" \
  -f build_type=workflow \
  >/dev/null 2>&1 || true

echo ""
echo "════════════════════════════════════════════════════════"
echo "  Despliegue en curso (1–2 min en la primera vez)."
echo ""
echo "  Liga permanente para tus jefes:"
echo "  https://$OWNER.github.io/$REPO_NAME/monitor.html"
echo ""
echo "  También: https://$OWNER.github.io/$REPO_NAME/"
echo "════════════════════════════════════════════════════════"
echo ""
echo "Estado: https://github.com/$OWNER/$REPO_NAME/actions"
