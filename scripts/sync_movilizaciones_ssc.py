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


def download_pdf(url: str) -> bytes:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; MonitoreoIMSS/1.0)"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()


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
    cfg = load_config()
    url = cfg["pdf_url"]
    print(f"Descargando agenda SSC: {url}")
    pdf_bytes = download_pdf(url)
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
