#!/usr/bin/env python3
"""
Sincroniza UMF cercanas a las 3 sedes del Mundial 2026
desde el Sistema de Regionalización IMSS (11.22.41.200).
"""

from __future__ import annotations

import json
import math
import re
import sys
import urllib.request
from pathlib import Path

BASE = "http://11.22.41.200/region/recursos/js"
OUT = Path(__file__).resolve().parent.parent / "data" / "estadios_umf.json"

STADIUMS = {
    "Estadio Azteca": {"lat": 19.3029, "lon": -99.1506, "delegaciones": [40, 39]},
    "Estadio Akron": {"lat": 20.6819, "lon": -103.4616, "delegaciones": [14]},
    "Estadio BBVA": {"lat": 25.6866, "lon": -100.2451, "delegaciones": [20]},
}

DELEG = {
    39: "CD México Norte",
    40: "CD México Sur",
    14: "Jalisco",
    20: "Nuevo León",
}


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def fetch_catalog(cve: int) -> str:
    url = f"{BASE}/catalogo_{cve}.js"
    with urllib.request.urlopen(url, timeout=20) as resp:
        return resp.read().decode("latin-1")


def parse_js_array(text: str, varname: str) -> list[dict]:
    match = re.search(rf"var {varname} = new Array \((.*)\);\s*(?:var |$)", text, re.DOTALL)
    if not match:
        return []
    items = re.findall(r"\{([^}]+)\}", match.group(1))
    rows: list[dict] = []
    for item in items:
        row: dict = {}
        for key, val in re.findall(r'(\w+):"([^"]*)"', item):
            row[key] = val
        for key, val in re.findall(r"(\w+):([\d.-]+)", item):
            if key not in row:
                row[key] = float(val) if "." in val else val
        rows.append(row)
    return rows


def build() -> dict:
    catalogs = {cve: fetch_catalog(cve) for cve in {39, 40, 14, 20}}
    result: dict[str, list] = {}

    for stadium, cfg in STADIUMS.items():
        nearby = []
        for cve in cfg["delegaciones"]:
            text = catalogs[cve]
            coords = {}
            for row in parse_js_array(text, "cat_datos"):
                lat = float(row.get("latitud", 0) or 0)
                lon = float(row.get("longitud", 0) or 0)
                if lat and lon and row.get("tipo", "") in ("UMF", "UMFH", "UMAA"):
                    coords[row["desde"]] = (lat, lon, row.get("tipo", ""))

            details = {r["nombre_1N"]: r for r in parse_js_array(text, "cat_est_1N")}

            for name, (lat, lon, tipo) in coords.items():
                dist = haversine(cfg["lat"], cfg["lon"], lat, lon)
                if dist > 10:
                    continue
                det = details.get(name, {})
                nearby.append(
                    {
                        "nombre": name,
                        "tipo": tipo,
                        "delegacion": DELEG[cve],
                        "lat": lat,
                        "lon": lon,
                        "dist_km": round(dist, 1),
                        "hospital": det.get("nombre_2N", ""),
                        "cve": det.get("cve_presupuestal", ""),
                        "cons_mf": det.get("cons_mf", ""),
                        "pamf": det.get("pamf", ""),
                        "dist_hosp": det.get("distancia", ""),
                        "tiempo_hosp": det.get("tiempo", ""),
                        "urgencias": det.get("Urgencias", "0"),
                        "atencion_continua": det.get("Atencion_Medica_Continua", "0"),
                    }
                )

        nearby.sort(key=lambda x: x["dist_km"])
        result[stadium] = nearby

    return result


def main() -> int:
    data = build()
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    for stadium, rows in data.items():
        print(f"{stadium}: {len(rows)} UMF")
    print(f"Guardado en {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
