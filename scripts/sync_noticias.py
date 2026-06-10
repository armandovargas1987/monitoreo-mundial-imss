#!/usr/bin/env python3
"""Actualiza data/noticias.json desde el API del sitio de monitoreo (requiere red IMSS)."""

import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "data" / "noticias.json"
BASE = "https://monitoreoimss.djuridicaimss.net"


def login():
    import http.cookiejar
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    data = urllib.parse.urlencode({
        "usuario": "marvin.ortiz",
        "clave": "DH2026!",
        "next": "index.php",
    }).encode()
    opener.open(f"{BASE}/login.php", data, timeout=20)
    return opener


def main():
    opener = login()
    with opener.open(f"{BASE}/api_noticias.php", timeout=30) as r:
        payload = json.loads(r.read().decode())
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Guardadas {len(payload.get('noticias', []))} noticias en {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
