#!/usr/bin/env python3
"""
Descarga y parsea la Agenda de Movilizaciones Sociales de la SSC-CDMX.
Filtra marchas y concentraciones; clasifica alertas IMSS.
"""

from __future__ import annotations

import json
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "data" / "ssc_config.json"
OUT_PATH = ROOT / "data" / "movilizaciones_ssc.json"
PDF_CACHE = ROOT / "data" / ".ssc_agenda_cache.pdf"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ssc_parser import parse_pdf_bytes  # noqa: E402


def load_config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def download_pdf(url: str, attempts: int = 4, timeout: int = 120) -> bytes:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "application/pdf,application/octet-stream,*/*",
        "Accept-Language": "es-MX,es;q=0.9",
        "Connection": "keep-alive",
    }
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = resp.read()
            if len(data) < 1000:
                raise RuntimeError(f"PDF demasiado pequeño ({len(data)} bytes)")
            return data
        except (urllib.error.URLError, TimeoutError, RuntimeError) as exc:
            last_error = exc
            print(f"Intento {attempt}/{attempts} fallido: {exc}", file=sys.stderr)
            if attempt < attempts:
                wait = attempt * 15
                print(f"Reintentando en {wait}s...", file=sys.stderr)
                time.sleep(wait)
    raise RuntimeError(f"No se pudo descargar el PDF de la SSC: {last_error}") from last_error
