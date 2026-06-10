#!/usr/bin/env python3
"""Genera versión visual de Agenda de Previsiones (HTML + DOCX)."""

from pathlib import Path
import shutil
import base64

from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

# Colores institucionales IMSS
GUINDA = RGBColor(0x61, 0x12, 0x32)
VERDE = RGBColor(0x1A, 0x5C, 0x45)
VERDE2 = RGBColor(0x13, 0x79, 0x5C)
GOLD = RGBColor(0xA5, 0x7F, 0x2C)
GRAY = RGBColor(0x6B, 0x6B, 0x6E)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
BG_LIGHT = RGBColor(0xF4, 0xF5, 0xF3)

DATA = {
    "titulo": "AGENDA DE PREVISIONES",
    "fecha_doc": "11 de junio de 2026",
    "evento": "Manifestación en CDMX en CMN La Raza",
    "tipo": "Manifestación pacífica",
    "fuente": "Redes Abiertas",
    "links": [
        "https://www.facebook.com/reel/4567326883543258",
        "https://www.facebook.com/photo?fbid=1684799556159263&set=a.113724509933450",
    ],
    "organizacion": "Personal de Salud, pensionados y jubilados del IMSS",
    "antecedentes": (
        "Existen documentos recibidos por diversos medios Institucionales "
        "solicitando el regreso del RJP."
    ),
    "liderazgo": "Mery Meryta Barragan y Jefe Viny",
    "liderazgo_detalle": "Persona jubilada y en activo",
    "fecha_hora": "Jueves 11 de junio a las 7:00 a.m.",
    "lugar": (
        "Instalaciones de CMN la Raza, Av. Circuito Interior a un lado del "
        "Hospital de Infectología. Se sumarán a la megamarcha con madres "
        "buscadoras, maestros, jubilados de CFE y Pemex."
    ),
    "peticiones": "Regreso del Régimen de Jubilaciones y Pensiones (RJP).",
    "escenarios": [
        "Poca asistencia sin diálogo dirigiéndose a la Megamanifestación.",
        "Asistencia moderada / cierre de vialidades.",
    ],
}

IMG1 = Path("/tmp/docx_extract/word/media/image1.png")
IMG2 = Path("/tmp/docx_extract/word/media/image2.png")
LOGO = Path(__file__).resolve().parent.parent / "assets" / "img" / "imss-logo.png"
OUT_DIR = Path("/Users/vargas/Downloads")


def set_cell_shading(cell, hex_color: str):
    shading = OxmlElement("w:shd")
    shading.set(qn("w:fill"), hex_color)
    shading.set(qn("w:val"), "clear")
    cell._tc.get_or_add_tcPr().append(shading)


def add_label_value_table(doc, rows):
    table = doc.add_table(rows=len(rows), cols=2)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    for i, (label, value) in enumerate(rows):
        lc, vc = table.rows[i].cells
        lc.width = Cm(4.5)
        vc.width = Cm(12.5)
        set_cell_shading(lc, "611232")
        p = lc.paragraphs[0]
        run = p.add_run(label)
        run.bold = True
        run.font.color.rgb = WHITE
        run.font.size = Pt(9)
        run.font.name = "Segoe UI"
        if isinstance(value, list):
            for j, item in enumerate(value):
                bp = vc.paragraphs[0] if j == 0 else vc.add_paragraph()
                bp.style = "List Bullet"
                run2 = bp.add_run(item)
                run2.font.size = Pt(10)
                run2.font.name = "Segoe UI"
        else:
            p2 = vc.paragraphs[0]
            run2 = p2.add_run(value)
            run2.font.size = Pt(10)
            run2.font.name = "Segoe UI"
        if i % 2 == 0:
            set_cell_shading(vc, "F4F5F3")
    doc.add_paragraph()


def build_docx(out_path: Path):
    doc = Document()
    section = doc.sections[0]
    section.top_margin = Cm(1.2)
    section.bottom_margin = Cm(1.2)
    section.left_margin = Cm(1.5)
    section.right_margin = Cm(1.5)

    # Encabezado
    hdr = doc.add_table(rows=1, cols=2)
    hdr.autofit = False
    c1, c2 = hdr.rows[0].cells
    set_cell_shading(c1, "FFFFFF")
    set_cell_shading(c2, "611232")
    c1.width = Cm(3.2)
    c2.width = Cm(13.8)
    p1 = c1.paragraphs[0]
    p1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if LOGO.exists():
        r1 = p1.add_run()
        r1.add_picture(str(LOGO), width=Cm(2.4))
    else:
        r1 = p1.add_run("IMSS")
        r1.bold = True
        r1.font.size = Pt(14)
        r1.font.color.rgb = VERDE
    p2 = c2.paragraphs[0]
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r2 = p2.add_run(DATA["titulo"])
    r2.bold = True
    r2.font.size = Pt(16)
    r2.font.color.rgb = WHITE
    doc.add_paragraph()

    # Alerta / fecha
    alert = doc.add_paragraph()
    alert.alignment = WD_ALIGN_PARAGRAPH.CENTER
    ar = alert.add_run(f"  EVENTO PROGRAMADO — {DATA['fecha_doc'].upper()}  ")
    ar.bold = True
    ar.font.size = Pt(11)
    ar.font.color.rgb = GUINDA
    doc.add_paragraph()

    # Resumen rápido (3 columnas)
    kpi = doc.add_table(rows=2, cols=3)
    kpi.alignment = WD_TABLE_ALIGNMENT.CENTER
    kpis = [
        ("TIPO", DATA["tipo"], "1A5C45"),
        ("FECHA / HORA", DATA["fecha_hora"], "13795C"),
        ("FUENTE", DATA["fuente"], "A57F2C"),
    ]
    for j, (lbl, val, color) in enumerate(kpis):
        hc = kpi.rows[0].cells[j]
        vc = kpi.rows[1].cells[j]
        set_cell_shading(hc, color)
        set_cell_shading(vc, "FFFFFF")
        hp = hc.paragraphs[0]
        hp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        hr = hp.add_run(lbl)
        hr.bold = True
        hr.font.size = Pt(8)
        hr.font.color.rgb = WHITE
        vp = vc.paragraphs[0]
        vp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        vr = vp.add_run(val)
        vr.font.size = Pt(9)
        vr.font.name = "Segoe UI"
    doc.add_paragraph()

    # Detalle
    h = doc.add_paragraph()
    hr = h.add_run("DETALLE DEL EVENTO")
    hr.bold = True
    hr.font.size = Pt(11)
    hr.font.color.rgb = GUINDA

    add_label_value_table(
        doc,
        [
            ("EVENTO", DATA["evento"]),
            ("ORGANIZACIÓN", DATA["organizacion"]),
            ("LIDERAZGO", f"{DATA['liderazgo']}\n({DATA['liderazgo_detalle']})"),
            ("LUGAR", DATA["lugar"]),
            ("PETICIÓN", DATA["peticiones"]),
            ("ANTECEDENTES", DATA["antecedentes"]),
            ("ESCENARIO ESPERADO", DATA["escenarios"]),
        ],
    )

    # Enlaces
    h2 = doc.add_paragraph()
    h2r = h2.add_run("FUENTES Y EVIDENCIA")
    h2r.bold = True
    h2r.font.size = Pt(11)
    h2r.font.color.rgb = GUINDA
    for link in DATA["links"]:
        lp = doc.add_paragraph(style="List Bullet")
        lr = lp.add_run(link)
        lr.font.size = Pt(9)
        lr.font.color.rgb = VERDE2

    # Imágenes
    h3 = doc.add_paragraph()
    h3r = h3.add_run("CAPTURAS DE REDES SOCIALES")
    h3r.bold = True
    h3r.font.size = Pt(11)
    h3r.font.color.rgb = GUINDA

    if IMG1.exists() and IMG2.exists():
        img_table = doc.add_table(rows=1, cols=2)
        for idx, img_path in enumerate([IMG1, IMG2]):
            cell = img_table.rows[0].cells[idx]
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run()
            run.add_picture(str(img_path), width=Inches(2.8))
            cap = cell.add_paragraph()
            cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
            labels = ["Publicación — Jefe Viny", "Reel — Convocatoria laboral"]
            cr = cap.add_run(labels[idx])
            cr.italic = True
            cr.font.size = Pt(8)
            cr.font.color.rgb = GRAY

    doc.save(out_path)


def img_to_b64(path: Path) -> str:
    if not path.exists():
        return ""
    data = path.read_bytes()
    return base64.b64encode(data).decode("ascii")


def build_html(out_path: Path):
    b64_1 = img_to_b64(IMG1)
    b64_2 = img_to_b64(IMG2)
    b64_logo = img_to_b64(LOGO)
    links_html = "".join(
        f'<li><a href="{u}" target="_blank">{u}</a></li>' for u in DATA["links"]
    )
    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{DATA['titulo']} — {DATA['fecha_doc']}</title>
<style>
  :root {{
    --guinda:#611232; --verde:#1a5c45; --verde-2:#13795c; --gold:#a57f2c;
    --gray:#6b6b6e; --line:#e3e2dd; --bg:#f4f5f3; --panel:#fff; --ink:#23232a;
    --shadow:0 2px 8px rgba(20,20,30,.08),0 8px 24px rgba(20,20,30,.06);
  }}
  * {{ box-sizing:border-box; margin:0; padding:0; }}
  body {{ font-family:"Segoe UI",system-ui,Arial,sans-serif; background:var(--bg); color:var(--ink); line-height:1.45; }}
  .page {{ max-width:900px; margin:24px auto; background:var(--panel); box-shadow:var(--shadow); border-radius:12px; overflow:hidden; }}
  .topbar {{ display:flex; align-items:stretch; }}
  .seal {{ background:#fff; padding:12px 16px; display:flex; align-items:center; justify-content:center; min-width:110px; border-right:1px solid var(--line); }}
  .seal img {{ height:72px; width:auto; display:block; }}
  .title-block {{ flex:1; background:var(--guinda); color:#fff; padding:18px 24px; display:flex; flex-direction:column; justify-content:center; }}
  .title-block h1 {{ font-size:22px; font-weight:800; letter-spacing:.5px; }}
  .title-block .sub {{ font-size:12px; opacity:.85; margin-top:4px; text-transform:uppercase; letter-spacing:1px; }}
  .alert-bar {{ background:#fde8ea; border-left:5px solid var(--guinda); padding:12px 24px; display:flex; align-items:center; gap:12px; }}
  .alert-bar .dot {{ width:10px; height:10px; border-radius:50%; background:var(--guinda); animation:pulse 1.5s infinite; }}
  @keyframes pulse {{ 0%,100%{{opacity:1}} 50%{{opacity:.4}} }}
  .alert-bar strong {{ color:var(--guinda); font-size:13px; text-transform:uppercase; letter-spacing:.3px; }}
  .kpis {{ display:grid; grid-template-columns:repeat(3,1fr); gap:0; border-bottom:1px solid var(--line); }}
  .kpi {{ padding:16px 18px; text-align:center; border-right:1px solid var(--line); }}
  .kpi:last-child {{ border-right:0; }}
  .kpi .label {{ font-size:10px; font-weight:800; text-transform:uppercase; letter-spacing:.6px; color:#fff; padding:4px 10px; border-radius:6px; display:inline-block; margin-bottom:8px; }}
  .kpi:nth-child(1) .label {{ background:var(--verde); }}
  .kpi:nth-child(2) .label {{ background:var(--verde-2); }}
  .kpi:nth-child(3) .label {{ background:var(--gold); }}
  .kpi .value {{ font-size:13px; font-weight:600; }}
  .content {{ padding:24px; }}
  .section-title {{ font-size:12px; font-weight:800; text-transform:uppercase; letter-spacing:.6px; color:var(--guinda); margin-bottom:14px; padding-bottom:6px; border-bottom:2px solid var(--line); }}
  .fields {{ display:grid; gap:10px; margin-bottom:28px; }}
  .field {{ display:grid; grid-template-columns:160px 1fr; border-radius:8px; overflow:hidden; border:1px solid var(--line); }}
  .field:nth-child(even) {{ background:var(--bg); }}
  .field .lbl {{ background:var(--guinda); color:#fff; font-size:10px; font-weight:800; text-transform:uppercase; letter-spacing:.4px; padding:10px 14px; display:flex; align-items:center; }}
  .field .val {{ padding:10px 14px; font-size:13px; }}
  .field .val ul {{ margin:0; padding-left:18px; }}
  .field .val li {{ font-size:13px; margin-bottom:4px; }}
  .links {{ list-style:none; margin-bottom:28px; }}
  .links li {{ margin-bottom:6px; }}
  .links a {{ color:var(--verde-2); font-size:12px; word-break:break-all; }}
  .gallery {{ display:grid; grid-template-columns:1fr 1fr; gap:16px; }}
  .shot {{ border:1px solid var(--line); border-radius:10px; overflow:hidden; background:#fafafa; }}
  .shot img {{ width:100%; display:block; max-height:420px; object-fit:contain; background:#111; }}
  .shot figcaption {{ padding:8px 12px; font-size:11px; color:var(--gray); font-style:italic; text-align:center; border-top:1px solid var(--line); }}
  .footer {{ background:var(--bg); padding:14px 24px; font-size:10px; color:var(--gray); text-align:center; border-top:1px solid var(--line); }}
  @media print {{
    body {{ background:#fff; }}
    .page {{ box-shadow:none; margin:0; border-radius:0; max-width:100%; }}
    .alert-bar .dot {{ animation:none; }}
  }}
</style>
</head>
<body>
<div class="page">
  <div class="topbar">
    <div class="seal"><img src="data:image/png;base64,{b64_logo}" alt="Logosímbolo IMSS"></div>
    <div class="title-block">
      <h1>{DATA['titulo']}</h1>
      <div class="sub">Monitoreo de eventos · {DATA['fecha_doc']}</div>
    </div>
  </div>
  <div class="alert-bar">
    <span class="dot"></span>
    <strong>Evento programado</strong>
    <span>— {DATA['evento']}</span>
  </div>
  <div class="kpis">
    <div class="kpi"><div class="label">Tipo</div><div class="value">{DATA['tipo']}</div></div>
    <div class="kpi"><div class="label">Fecha y hora</div><div class="value">{DATA['fecha_hora']}</div></div>
    <div class="kpi"><div class="label">Fuente</div><div class="value">{DATA['fuente']}</div></div>
  </div>
  <div class="content">
    <div class="section-title">Detalle del evento</div>
    <div class="fields">
      <div class="field"><div class="lbl">Evento</div><div class="val">{DATA['evento']}</div></div>
      <div class="field"><div class="lbl">Organización</div><div class="val">{DATA['organizacion']}</div></div>
      <div class="field"><div class="lbl">Liderazgo</div><div class="val">{DATA['liderazgo']}<br><small style="color:var(--gray)">{DATA['liderazgo_detalle']}</small></div></div>
      <div class="field"><div class="lbl">Lugar</div><div class="val">{DATA['lugar']}</div></div>
      <div class="field"><div class="lbl">Petición</div><div class="val">{DATA['peticiones']}</div></div>
      <div class="field"><div class="lbl">Antecedentes</div><div class="val">{DATA['antecedentes']}</div></div>
      <div class="field"><div class="lbl">Escenario esperado</div><div class="val"><ul><li>{DATA['escenarios'][0]}</li><li>{DATA['escenarios'][1]}</li></ul></div></div>
    </div>
    <div class="section-title">Fuentes y evidencia</div>
    <ul class="links">{links_html}</ul>
    <div class="section-title">Capturas de redes sociales</div>
    <div class="gallery">
      <figure class="shot"><img src="data:image/png;base64,{b64_1}" alt="Publicación Facebook"><figcaption>Publicación — Jefe Viny (726 reacciones)</figcaption></figure>
      <figure class="shot"><img src="data:image/png;base64,{b64_2}" alt="Reel convocatoria"><figcaption>Reel — Convocatoria laboral CMN La Raza</figcaption></figure>
    </div>
  </div>
  <div class="footer">Documento generado para previsión operativa · Uso interno</div>
</div>
</body>
</html>"""
    out_path.write_text(html, encoding="utf-8")


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    html_out = OUT_DIR / "AGENDA DE PREVISIONES 11 JUNIO 26 - VISUAL.html"

    build_html(html_out)
    print(f"HTML: {html_out}")


if __name__ == "__main__":
    main()
