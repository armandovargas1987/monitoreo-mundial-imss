#!/usr/bin/env python3
"""Parser de la Agenda de Movilizaciones Sociales (SSC-CDMX)."""

from __future__ import annotations

import re
from typing import Any

try:
    import fitz  # pymupdf
except ImportError as exc:
    raise SystemExit("Instala pymupdf: pip install pymupdf") from exc

ALCALDIAS = [
    "Álvaro Obregón",
    "Azcapotzalco",
    "Benito Juárez",
    "Coyoacán",
    "Cuajimalpa de Morelos",
    "Cuajimalpa",
    "Cuauhtémoc",
    "Gustavo A. Madero",
    "Iztacalco",
    "Iztapalapa",
    "La Magdalena Contreras",
    "Magdalena Contreras",
    "Miguel Hidalgo",
    "Milpa Alta",
    "Tláhuac",
    "Tlalpan",
    "Venustiano Carranza",
    "Xochimilco",
]

SKIP_LINES = frozenset({"H", "E", "R", "M", "O", "D"})
STOP_MARKERS = (
    "C I T A S",
    "CITAS AGENDADAS",
    "RODADAS CICLISTAS",
    "RODADAS DE AUTOS",
    "AGENDA DE EVENTOS",
    "EVENTOS DE ESPARCIMIENTO",
)
FIELD_MARKERS = (
    "Hora:",
    "Lugar:",
    "Destino:",
    "Demanda:",
    "Actividades:",
    "Organizaciones",
    "Observaciones:",
    "Aforo:",
)


def _normalize_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _strip_pdf_noise(text: str) -> str:
    for phrase in (
        "H E R M O D",
        "AGENDA DE MOVILIZACIONES SOCIALES",
        "AGENDA DE",
        "MOVILIZACIONES SOCIALES",
        "M A R C H A S",
        "C O N C E N T R A C I O N E S",
    ):
        text = text.replace(phrase, " ")
    return _normalize_spaces(text)


def _clean_page_lines(text: str) -> list[str]:
    lines: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line in SKIP_LINES:
            continue
        if line.startswith("AGENDA DE") and "MOVILIZACIONES" not in line:
            continue
        if line == "MOVILIZACIONES SOCIALES":
            continue
        lines.append(line)
    return lines


def _reflow_lines(lines: list[str]) -> list[str]:
    out: list[str] = []
    buf: list[str] = []
    for line in lines:
        if line.startswith("M A R C H A S") or line.startswith("C O N C E N T R A C I O N E S"):
            if buf:
                out.append(_normalize_spaces(" ".join(buf)))
                buf = []
            out.append(line)
            continue
        if any(line.startswith(marker) for marker in FIELD_MARKERS):
            if buf:
                out.append(_normalize_spaces(" ".join(buf)))
                buf = []
            out.append(line)
        else:
            buf.append(line)
    if buf:
        out.append(_normalize_spaces(" ".join(buf)))
    return out


def _split_org_alcaldia(pre_hora: str) -> tuple[str, str]:
    text = _normalize_spaces(pre_hora)
    if not text:
        return "Sin identificar en agenda", ""
    for alcaldia in sorted(ALCALDIAS, key=len, reverse=True):
        if text.lower() == alcaldia.lower():
            return "Sin identificar en agenda", alcaldia
        if text.lower().endswith(alcaldia.lower()):
            org = text[: -len(alcaldia)].strip(" -–—")
            if org:
                return org, alcaldia
    return text, ""


def _extract_lugares(block: str) -> str:
    lugares = re.findall(
        r"Lugar(?:\s+\d+)?:\s*(.*?)(?=Lugar(?:\s+\d+)?:|Destino:|Demanda:|Actividades:|Organizaciones|Observaciones:|Aforo:|$)",
        block,
        flags=re.I | re.S,
    )
    if lugares:
        return _normalize_spaces(" / ".join(_normalize_spaces(lugar) for lugar in lugares))
    return _extract_field(
        block,
        "Lugar",
        r"Destino:|Demanda:|Actividades:|Organizaciones|Observaciones:|Aforo:",
    )


def _extract_field(block: str, name: str, nxt: str) -> str:
    pattern = rf"{re.escape(name)}:\s*(.*?)(?={nxt})"
    match = re.search(pattern, block, flags=re.I | re.S)
    return _normalize_spaces(match.group(1)) if match else ""


def _parse_event_block(block: str, tipo: str) -> dict[str, Any] | None:
    block = _strip_pdf_noise(block)
    if not block or "Hora:" not in block:
        return None

    hora_match = re.search(r"Hora:\s*(.+?)(?=\s+Lugar\b)", block, re.I)
    aforo_match = re.search(r"Aforo:\s*([\d,]+)", block, re.I)
    if not hora_match:
        return None

    hora = hora_match.group(1)
    aforo = int(aforo_match.group(1).replace(",", "")) if aforo_match else None
    org, alcaldia = _split_org_alcaldia(block[: hora_match.start()])

    lugar = _extract_lugares(block)
    next_fields = r"Destino:|Demanda:|Actividades:|Organizaciones|Observaciones:|Aforo:"
    destino = _extract_field(block, "Destino", r"Demanda:|Actividades:|Organizaciones|Observaciones:|Aforo:")
    demanda = _extract_field(block, "Demanda", r"Actividades:|Organizaciones|Observaciones:|Aforo:")
    actividades = _extract_field(block, "Actividades", r"Organizaciones|Observaciones:|Aforo:")
    if actividades and not demanda:
        demanda = f"Actividades: {actividades}"
    elif actividades:
        demanda = f"{demanda} Actividades: {actividades}"

    apoyo = _extract_field(block, "Organizaciones en apoyo", r"Observaciones:|Aforo:")
    observaciones = _extract_field(block, "Observaciones", r"Aforo:")

    if org == "Sin identificar en agenda" and apoyo:
        org = apoyo.split(",")[0].strip()
    elif org == "Sin identificar en agenda" and demanda:
        org = demanda[:80] + ("…" if len(demanda) > 80 else "")

    return {
        "tipo": tipo,
        "organizacion": org,
        "alcaldia": alcaldia,
        "hora": hora,
        "lugar": lugar,
        "destino": destino,
        "demanda": demanda,
        "apoyo": apoyo,
        "observaciones": observaciones,
        "aforo": aforo,
    }


def _events_from_section(section_text: str, tipo: str) -> list[dict[str, Any]]:
    section_text = _strip_pdf_noise(section_text)
    parts = re.split(r"Aforo:\s*([\d,]+)", section_text)
    events: list[dict[str, Any]] = []
    for idx in range(1, len(parts), 2):
        body = parts[idx - 1]
        aforo = int(parts[idx].replace(",", ""))
        event = _parse_event_block(body, tipo)
        if not event:
            continue
        event["aforo"] = aforo
        events.append(event)
    return events


def _concat_movilizaciones_pages(doc: fitz.Document) -> str:
    chunks: list[str] = []
    for page_index in range(1, doc.page_count):
        text = doc[page_index].get_text()
        if any(marker in text for marker in STOP_MARKERS):
            break
        chunks.append(text)
    return "\n".join(chunks)


def parse_pdf_bytes(pdf_bytes: bytes) -> dict[str, Any]:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    full_text = "\n".join(doc[i].get_text() for i in range(doc.page_count))

    fecha_match = re.search(r"AGENDA DE LA SSC-CDMX\s*\n\s*([^\n]+)", full_text)
    fecha = fecha_match.group(1).strip() if fecha_match else ""

    resumen_match = re.search(
        r"Marchas\s+(\d+)\s*\nConcentraciones\s+(\d+)",
        full_text,
        re.I,
    )
    resumen = {
        "marchas": int(resumen_match.group(1)) if resumen_match else None,
        "concentraciones": int(resumen_match.group(2)) if resumen_match else None,
    }

    movilizaciones_text = _concat_movilizaciones_pages(doc)
    marchas_start = movilizaciones_text.find("M A R C H A S")
    concentraciones_start = movilizaciones_text.find("C O N C E N T R A C I O N E S", marchas_start + 1)

    marchas: list[dict[str, Any]] = []
    concentraciones: list[dict[str, Any]] = []

    if marchas_start >= 0 and concentraciones_start > marchas_start:
        marchas = _events_from_section(
            movilizaciones_text[marchas_start:concentraciones_start],
            "marcha",
        )
        concentraciones = _events_from_section(
            movilizaciones_text[concentraciones_start:],
            "concentracion",
        )
    elif concentraciones_start >= 0:
        concentraciones = _events_from_section(
            movilizaciones_text[concentraciones_start:],
            "concentracion",
        )

    return {
        "fecha": fecha,
        "resumen_portada": resumen,
        "marchas": marchas,
        "concentraciones": concentraciones,
        "total_eventos": len(marchas) + len(concentraciones),
    }
