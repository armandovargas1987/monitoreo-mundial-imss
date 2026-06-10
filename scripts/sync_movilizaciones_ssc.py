#!/usr/bin/env python3
"""
Descarga y parsea la Agenda de Movilizaciones Sociales de la SSC-CDMX.
Filtra marchas y concentraciones; clasifica alertas IMSS.
"""

from __future__ import annotations

import json
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
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


def _compile_patterns(words: list[str]) -> re.Pattern[str]:
    parts = [re.escape(word) for word in words if word.strip()]
    return re.compile("|".join(parts), re.I)


def classify_alert(event: dict, cfg: dict) -> dict:
    blob = " ".join(
        str(event.get(key, ""))
        for key in (
            "organizacion",
            "alcaldia",
            "lugar",
            "destino",
            "demanda",
            "apoyo",
            "observaciones",
        )
    )
    maxima = _compile_patterns(cfg.get("alerta_maxima", []))
    alta = _compile_patterns(cfg.get("alerta_alta", []))

    if maxima.search(blob):
        nivel = "maxima"
        etiqueta = "ALERTA MÁXIMA"
    elif alta.search(blob):
        nivel = "alta"
        etiqueta = "ALERTA ALTA"
    else:
        nivel = "normal"
        etiqueta = "Normal"

    return {
        **event,
        "alerta_nivel": nivel,
        "alerta_etiqueta": etiqueta,
    }


def build_payload(pdf_bytes: bytes, cfg: dict, source_url: str) -> dict:
    parsed = parse_pdf_bytes(pdf_bytes)
    marchas = [classify_alert(ev, cfg) for ev in parsed["marchas"]]
    concentraciones = [classify_alert(ev, cfg) for ev in parsed["concentraciones"]]
    eventos = marchas + concentraciones
    alertas_maxima = [ev for ev in eventos if ev["alerta_nivel"] == "maxima"]
    alertas_alta = [ev for ev in eventos if ev["alerta_nivel"] == "alta"]

    now_mx = datetime.now(ZoneInfo("America/Mexico_City"))
    return {
        "ok": True,
        "fuente": "SSC-CDMX — Agenda de Movilizaciones Sociales",
        "fuente_url": source_url,
        "fecha_agenda": parsed["fecha"],
        "resumen_portada": parsed["resumen_portada"],
        "consultado_en": now_mx.isoformat(),
        "consultado_legible": now_mx.strftime("%d/%m/%Y %H:%M hrs (CDMX)"),
        "totales": {
            "marchas": len(marchas),
            "concentraciones": len(concentraciones),
            "eventos": len(eventos),
            "alertas_maxima": len(alertas_maxima),
            "alertas_alta": len(alertas_alta),
        },
        "alertas_maxima": alertas_maxima,
        "alertas_alta": alertas_alta,
        "marchas": marchas,
        "concentraciones": concentraciones,
    }


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Sincroniza agenda SSC-CDMX")
    parser.add_argument(
        "--from-cache",
        action="store_true",
        help="Usar PDF ya descargado en data/.ssc_agenda_cache.pdf",
    )
    args = parser.parse_args()

    cfg = load_config()
    url = cfg["pdf_url"]
    if args.from_cache and PDF_CACHE.exists():
        print(f"Usando PDF en caché: {PDF_CACHE}")
        pdf_bytes = PDF_CACHE.read_bytes()
    else:
        print(f"Descargando agenda SSC: {url}")
        pdf_bytes = download_pdf(url)
        PDF_CACHE.parent.mkdir(parents=True, exist_ok=True)
        PDF_CACHE.write_bytes(pdf_bytes)
    payload = build_payload(pdf_bytes, cfg, url)
    OUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    t = payload["totales"]
    print(
        f"OK — {payload['fecha_agenda']}: "
        f"{t['marchas']} marchas, {t['concentraciones']} concentraciones, "
        f"{t['alertas_maxima']} alerta(s) máxima(s)"
    )
    print(f"Guardado: {OUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
