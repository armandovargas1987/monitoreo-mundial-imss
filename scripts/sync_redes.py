#!/usr/bin/env python3
"""
Monitorea @zoerobledo y @Tu_IMSS en torno al Mundial 2026
e interés operativo del IMSS. Combina lectura de perfiles X (vía Jina)
y titulares de Google Noticias que citan sus declaraciones.
"""

from __future__ import annotations

import json
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "data" / "redes_config.json"
OUT = ROOT / "data" / "redes_sociales.json"
SEED = ROOT / "data" / "redes_seed.json"

MUNDIAL_RE = None
IMSS_RE = None


def load_config():
    global MUNDIAL_RE, IMSS_RE
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    MUNDIAL_RE = re.compile("|".join(re.escape(k) for k in cfg["filtro_mundial"]), re.I)
    IMSS_RE = re.compile("|".join(re.escape(k) for k in cfg["filtro_imss"]), re.I)
    return cfg


def relevant(text: str, handle: str) -> bool:
    if not text or len(text) < 25:
        return False
    if not MUNDIAL_RE.search(text):
        return False
    if handle == "Tu_IMSS":
        return bool(IMSS_RE.search(text) or MUNDIAL_RE.search(text))
    return bool(
        IMSS_RE.search(text)
        or re.search(r"@Tu_IMSS|instituto mexicano del seguro social|seguro social", text, re.I)
    )


def clean_text(raw: str) -> str:
    t = re.sub(r"!\[[^\]]*\]\([^\)]*\)", "", raw)
    t = re.sub(r"\[[^\]]*\]\([^\)]*\)", "", t)
    t = re.sub(r"https?://\S+", "", t)
    t = re.sub(r"x\.com/\S+", "", t)
    return re.sub(r"\s+", " ", t).strip()


def fetch_jina_profile(handle: str) -> str:
    url = f"https://r.jina.ai/https://x.com/{handle}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=35) as resp:
        return resp.read().decode("utf-8", errors="replace")


def parse_profile_posts(handle: str, nombre: str, md: str) -> list[dict]:
    posts: list[dict] = []
    seen: set[str] = set()

    # Oraciones / bloques con contexto mundial
    for match in MUNDIAL_RE.finditer(md):
        start = max(0, match.start() - 200)
        end = min(len(md), match.end() + 280)
        chunk = clean_text(md[start:end])
        if not relevant(chunk, handle):
            continue
        key = chunk[:80]
        if key in seen:
            continue
        seen.add(key)
        posts.append(
            {
                "id": f"x-{handle}-{len(posts)+1}",
                "cuenta": handle,
                "handle": f"@{handle}",
                "nombre": nombre,
                "texto": chunk[:480],
                "url": f"https://x.com/{handle}",
                "fuente": "X · perfil público",
                "tipo": "publicacion",
                "relevancia": "alta"
                if re.search(r"comando central|operativo|253|sesión permanente", chunk, re.I)
                else "media",
                "fecha": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            }
        )

    return posts[:15]


def fetch_google_news(query: str) -> list[dict]:
    q = urllib.parse.quote(query)
    url = (
        "https://news.google.com/rss/search?"
        f"q={q}&hl=es-419&gl=MX&ceid=MX:es-419"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=25) as resp:
        xml = resp.read()
    root = ET.fromstring(xml)
    items = []
    for item in root.findall(".//item")[:12]:
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub = (item.findtext("pubDate") or "")[:16]
        source = item.find("source")
        src = source.text if source is not None else "Google Noticias"
        texto = f"{title}"
        handle = "zoerobledo" if re.search(r"zoé|zoe robledo", texto, re.I) else "Tu_IMSS"
        if not relevant(texto, handle if handle != "Tu_IMSS" else "Tu_IMSS"):
            continue
        items.append(
            {
                "id": f"gn-{abs(hash(link)) % 10**8}",
                "cuenta": handle,
                "handle": "@zoerobledo" if handle == "zoerobledo" else "@Tu_IMSS",
                "nombre": "Zoé Robledo Aburto" if handle == "zoerobledo" else "IMSS Oficial",
                "texto": title,
                "url": link,
                "fuente": src,
                "tipo": "noticia-cita",
                "relevancia": "alta" if re.search(r"comando central|mega operativo|253", texto, re.I) else "media",
                "fecha": pub,
            }
        )
    return items


def merge_unique(posts: list[dict]) -> list[dict]:
    out: list[dict] = []
    seen: set[str] = set()
    for p in sorted(posts, key=lambda x: (0 if x.get("relevancia") == "alta" else 1, x.get("texto", ""))):
        key = re.sub(r"\W+", "", (p.get("texto") or "").lower())[:60]
        if key in seen:
            continue
        seen.add(key)
        out.append(p)
    return out


def main() -> int:
    cfg = load_config()
    all_posts: list[dict] = []

    if SEED.exists():
        seed = json.loads(SEED.read_text(encoding="utf-8"))
        all_posts.extend(seed.get("publicaciones", []))

    for acc in cfg["cuentas"]:
        try:
            md = fetch_jina_profile(acc["handle"])
            all_posts.extend(parse_profile_posts(acc["handle"], acc["nombre"], md))
            print(f"  {acc['handle']}: perfil leído")
        except Exception as exc:
            print(f"  {acc['handle']}: no disponible ({exc})")

    for q in cfg["consultas_noticias"]:
        try:
            items = fetch_google_news(q)
            all_posts.extend(items)
            print(f"  Noticias «{q}»: {len(items)}")
        except Exception as exc:
            print(f"  Noticias «{q}»: error ({exc})")

    publicaciones = merge_unique(all_posts)
    payload = {
        "ok": True,
        "actualizado": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "cuentas": cfg["cuentas"],
        "publicaciones": publicaciones,
        "total": len(publicaciones),
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Guardadas {len(publicaciones)} publicaciones en {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
