#!/usr/bin/env python3
"""
Genera la síntesis diaria de movilizaciones SSC-CDMX y la envía por correo.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "data" / "ssc_config.json"
DATA_PATH = ROOT / "data" / "movilizaciones_ssc.json"
SMTP_LOCAL = ROOT / "data" / "ssc_smtp.local.json"
HTML_OUT = ROOT / "public" / "sintesis-ssc" / "ultima.html"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _resumen_ejecutivo(data: dict) -> str:
    t = data["totales"]
    partes = [
        f"Para el {data['fecha_agenda']} se registran {t['marchas']} marcha(s) "
        f"y {t['concentraciones']} concentración(es) en la Ciudad de México."
    ]
    if t["alertas_maxima"]:
        orgs = ", ".join(ev["organizacion"][:60] for ev in data["alertas_maxima"][:3])
        partes.append(
            f"Se detectó {t['alertas_maxima']} movilización(es) con vínculo directo al IMSS: {orgs}."
        )
    elif t["alertas_alta"]:
        partes.append(
            f"Hay {t['alertas_alta']} evento(s) con posible impacto en salud, pensiones o sector médico."
        )
    else:
        partes.append("No se detectaron movilizaciones con vínculo directo al IMSS en la agenda del día.")
    return " ".join(partes)


def _event_card(event: dict, destacado: bool = False) -> str:
    bg = "#fde8ea" if destacado else "#ffffff"
    border = "#611232" if destacado else "#e3e2dd"
    etiqueta = event.get("alerta_etiqueta", "Normal")
    color_etiqueta = "#611232" if event["alerta_nivel"] == "maxima" else "#a57f2c" if event["alerta_nivel"] == "alta" else "#1a5c45"
    tipo = "MARCHA" if event["tipo"] == "marcha" else "CONCENTRACIÓN"
    destino = f"<div><strong>Destino:</strong> {escape(event.get('destino', ''))}</div>" if event.get("destino") else ""
    obs = f"<div style='margin-top:6px;font-size:12px;color:#6b6b6e'><strong>Observaciones:</strong> {escape(event.get('observaciones', ''))}</div>" if event.get("observaciones") else ""
    return f"""
    <div style="background:{bg};border:1px solid {border};border-left:5px solid {color_etiqueta};border-radius:8px;padding:14px 16px;margin-bottom:12px;">
      <div style="font-size:11px;font-weight:800;color:{color_etiqueta};letter-spacing:.4px;text-transform:uppercase;">{tipo} — {escape(etiqueta)}</div>
      <div style="font-size:16px;font-weight:700;color:#23232a;margin:6px 0 4px;">{escape(event['organizacion'])}</div>
      <div style="font-size:13px;color:#444;margin-bottom:8px;">
        <strong>{escape(event.get('alcaldia', ''))}</strong> · <strong>{escape(event.get('hora', ''))} h</strong>
        {f" · Aforo: {event['aforo']}" if event.get('aforo') is not None else ""}
      </div>
      <div style="font-size:13px;line-height:1.45"><strong>Lugar:</strong> {escape(event.get('lugar', ''))}</div>
      {destino}
      <div style="font-size:13px;line-height:1.45;margin-top:6px"><strong>Demanda:</strong> {escape(event.get('demanda', ''))}</div>
      {obs}
    </div>
    """


def _table_rows(eventos: list[dict]) -> str:
    rows = []
    for ev in sorted(eventos, key=lambda e: e.get("hora", "99:99")):
        alerta = ev.get("alerta_etiqueta", "Normal")
        color = "#611232" if ev["alerta_nivel"] == "maxima" else "#a57f2c" if ev["alerta_nivel"] == "alta" else "#1a5c45"
        tipo = "Marcha" if ev["tipo"] == "marcha" else "Concentración"
        lugar = ev.get("lugar", "")
        if ev.get("destino"):
            lugar = f"{lugar} → {ev['destino']}"
        rows.append(
            "<tr>"
            f"<td style='padding:8px 10px;border-bottom:1px solid #ecebe6;font-weight:600'>{escape(ev.get('hora', ''))}</td>"
            f"<td style='padding:8px 10px;border-bottom:1px solid #ecebe6'>{tipo}</td>"
            f"<td style='padding:8px 10px;border-bottom:1px solid #ecebe6'>{escape(ev.get('organizacion', ''))}</td>"
            f"<td style='padding:8px 10px;border-bottom:1px solid #ecebe6'>{escape(ev.get('alcaldia', ''))}</td>"
            f"<td style='padding:8px 10px;border-bottom:1px solid #ecebe6;font-size:12px'>{escape(lugar)}</td>"
            f"<td style='padding:8px 10px;border-bottom:1px solid #ecebe6;text-align:center'>{ev.get('aforo', '')}</td>"
            f"<td style='padding:8px 10px;border-bottom:1px solid #ecebe6;font-size:11px;font-weight:700;color:{color}'>{escape(alerta)}</td>"
            "</tr>"
        )
    return "\n".join(rows)


def build_html(data: dict) -> str:
    t = data["totales"]
    resumen = _resumen_ejecutivo(data)
    alertas_html = "".join(_event_card(ev, destacado=True) for ev in data["alertas_maxima"])
    if not alertas_html:
        alertas_html = "<p style='color:#1a5c45;font-weight:600'>Sin alertas máximas IMSS para el día.</p>"

    todos = data["marchas"] + data["concentraciones"]
    table_html = _table_rows(todos)

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Síntesis Movilizaciones CDMX — {escape(data['fecha_agenda'])}</title>
</head>
<body style="margin:0;padding:0;background:#f4f5f3;font-family:'Segoe UI',Arial,sans-serif;color:#23232a;">
  <div style="max-width:860px;margin:0 auto;background:#fff;">
    <div style="background:#611232;color:#fff;padding:20px 24px;">
      <div style="font-size:11px;opacity:.85;text-transform:uppercase;letter-spacing:1px;">Monitoreo IMSS · Comando Central</div>
      <h1 style="margin:8px 0 0;font-size:22px;">Síntesis de Movilizaciones CDMX</h1>
      <div style="margin-top:6px;font-size:14px;opacity:.92">{escape(data['fecha_agenda'])}</div>
    </div>

    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:0;border-bottom:1px solid #e3e2dd;">
      <div style="padding:14px;text-align:center;border-right:1px solid #e3e2dd;"><div style="font-size:10px;color:#6b6b6e;text-transform:uppercase;">Marchas</div><div style="font-size:24px;font-weight:800;color:#1a5c45;">{t['marchas']}</div></div>
      <div style="padding:14px;text-align:center;border-right:1px solid #e3e2dd;"><div style="font-size:10px;color:#6b6b6e;text-transform:uppercase;">Concentraciones</div><div style="font-size:24px;font-weight:800;color:#13795c;">{t['concentraciones']}</div></div>
      <div style="padding:14px;text-align:center;border-right:1px solid #e3e2dd;"><div style="font-size:10px;color:#6b6b6e;text-transform:uppercase;">Alerta máxima</div><div style="font-size:24px;font-weight:800;color:#611232;">{t['alertas_maxima']}</div></div>
      <div style="padding:14px;text-align:center;"><div style="font-size:10px;color:#6b6b6e;text-transform:uppercase;">Alerta alta</div><div style="font-size:24px;font-weight:800;color:#a57f2c;">{t['alertas_alta']}</div></div>
    </div>

    <div style="padding:20px 24px;background:#fafaf8;border-bottom:1px solid #e3e2dd;">
      <div style="font-size:11px;font-weight:800;color:#611232;text-transform:uppercase;letter-spacing:.5px;margin-bottom:8px;">Resumen ejecutivo</div>
      <p style="margin:0;font-size:14px;line-height:1.55">{escape(resumen)}</p>
    </div>

    <div style="padding:20px 24px;">
      <div style="font-size:11px;font-weight:800;color:#611232;text-transform:uppercase;letter-spacing:.5px;margin-bottom:12px;">Alertas prioritarias IMSS</div>
      {alertas_html}
    </div>

    <div style="padding:0 24px 24px;">
      <div style="font-size:11px;font-weight:800;color:#611232;text-transform:uppercase;letter-spacing:.5px;margin-bottom:12px;">Detalle — Marchas y concentraciones</div>
      <div style="overflow-x:auto;">
        <table style="width:100%;border-collapse:collapse;font-size:13px;">
          <thead>
            <tr style="background:#611232;color:#fff;">
              <th style="padding:9px 10px;text-align:left;">Hora</th>
              <th style="padding:9px 10px;text-align:left;">Tipo</th>
              <th style="padding:9px 10px;text-align:left;">Organización</th>
              <th style="padding:9px 10px;text-align:left;">Alcaldía</th>
              <th style="padding:9px 10px;text-align:left;">Lugar / destino</th>
              <th style="padding:9px 10px;text-align:center;">Aforo</th>
              <th style="padding:9px 10px;text-align:left;">Alerta</th>
            </tr>
          </thead>
          <tbody>{table_html}</tbody>
        </table>
      </div>
    </div>

    <div style="background:#f4f5f3;padding:14px 24px;font-size:11px;color:#6b6b6e;border-top:1px solid #e3e2dd;">
      Fuente: {escape(data['fuente'])} · Consultado: {escape(data['consultado_legible'])}<br>
      Uso interno · CVOED–CPES / Comando Central
    </div>
  </div>
</body>
</html>"""


def build_text(data: dict) -> str:
    lines = [
        f"SÍNTESIS MOVILIZACIONES CDMX — {data['fecha_agenda']}",
        "=" * 60,
        _resumen_ejecutivo(data),
        "",
    ]
    if data["alertas_maxima"]:
        lines.append("ALERTAS MÁXIMAS IMSS")
        lines.append("-" * 30)
        for ev in data["alertas_maxima"]:
            tipo = "MARCHA" if ev["tipo"] == "marcha" else "CONCENTRACIÓN"
            lines.append(f"• [{tipo}] {ev['organizacion']} | {ev.get('alcaldia', '')} | {ev.get('hora', '')} h")
            lines.append(f"  Lugar: {ev.get('lugar', '')}")
            if ev.get("destino"):
                lines.append(f"  Destino: {ev['destino']}")
            lines.append(f"  Demanda: {ev.get('demanda', '')}")
            lines.append("")
    lines.append("DETALLE COMPLETO")
    lines.append("-" * 30)
    for ev in sorted(data["marchas"] + data["concentraciones"], key=lambda e: e.get("hora", "99:99")):
        tipo = "Marcha" if ev["tipo"] == "marcha" else "Concentración"
        lines.append(
            f"• {ev.get('hora', '')} | {tipo} | {ev.get('alerta_etiqueta', '')} | "
            f"{ev['organizacion']} | {ev.get('alcaldia', '')} | Aforo {ev.get('aforo', 's/d')}"
        )
    lines.extend(
        [
            "",
            f"Fuente: {data['fuente']}",
            f"Consultado: {data['consultado_legible']}",
        ]
    )
    return "\n".join(lines)


def resolve_smtp(cfg: dict) -> dict | None:
    smtp = dict(cfg.get("smtp", {}))
    if SMTP_LOCAL.exists():
        smtp.update(load_json(SMTP_LOCAL))
    smtp["host"] = os.environ.get("SSC_SMTP_HOST") or smtp.get("host", "")
    smtp["user"] = os.environ.get("SSC_SMTP_USER") or smtp.get("user", "")
    smtp["password"] = os.environ.get(smtp.get("password_env", "SSC_SMTP_PASSWORD", "")) or smtp.get("password", "")
    smtp["from_email"] = os.environ.get("SSC_SMTP_FROM") or smtp.get("from_email") or smtp.get("user", "")
    if not smtp.get("host") or not smtp.get("user") or not smtp.get("password"):
        return None
    return smtp


def send_email(cfg: dict, subject: str, html_body: str, text_body: str) -> None:
    smtp = resolve_smtp(cfg)
    if not smtp:
        raise RuntimeError(
            "SMTP no configurado. Crea data/ssc_smtp.local.json o define "
            "SSC_SMTP_HOST, SSC_SMTP_USER y SSC_SMTP_PASSWORD."
        )

    recipients = cfg.get("destinatarios", [])
    if not recipients:
        raise RuntimeError("No hay destinatarios en data/ssc_config.json")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{smtp.get('from_name', 'Monitoreo IMSS')} <{smtp['from_email']}>"
    msg["To"] = ", ".join(recipients)
    msg.attach(MIMEText(text_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    port = int(smtp.get("port", 587))
    context = ssl.create_default_context()
    with smtplib.SMTP(smtp["host"], port, timeout=30) as server:
        if smtp.get("use_tls", True):
            server.starttls(context=context)
        server.login(smtp["user"], smtp["password"])
        server.sendmail(smtp["from_email"], recipients, msg.as_string())


def main() -> int:
    parser = argparse.ArgumentParser(description="Genera y envía síntesis SSC-CDMX")
    parser.add_argument("--enviar-correo", action="store_true", help="Enviar por correo electrónico")
    parser.add_argument("--solo-html", action="store_true", help="Solo generar HTML local")
    args = parser.parse_args()

    if not DATA_PATH.exists():
        print(f"No existe {DATA_PATH}. Ejecuta primero scripts/sync_movilizaciones_ssc.py")
        return 1

    cfg = load_json(CONFIG_PATH)
    data = load_json(DATA_PATH)
    html = build_html(data)
    text = build_text(data)

    HTML_OUT.parent.mkdir(parents=True, exist_ok=True)
    HTML_OUT.write_text(html, encoding="utf-8")
    print(f"HTML: {HTML_OUT}")

    t = data["totales"]
    subject = (
        f"Síntesis Movilizaciones CDMX — {data['fecha_agenda']} — "
        f"{t['eventos']} eventos | {t['alertas_maxima']} alerta(s) IMSS"
    )

    if args.enviar_correo:
        send_email(cfg, subject, html, text)
        print(f"Correo enviado a: {', '.join(cfg['destinatarios'])}")
    elif not args.solo_html:
        print("Síntesis generada. Usa --enviar-correo para mandarla.")
        if not resolve_smtp(cfg):
            print("SMTP pendiente: crea data/ssc_smtp.local.json (ver data/ssc_smtp.local.json.example)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
