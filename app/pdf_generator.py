import io
import json
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, PageBreak, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from datetime import datetime


# ── COLORES ──────────────────────────────────────────────────────
AZUL_OSCURO  = colors.HexColor("#0a2540")
AZUL_MEDIO   = colors.HexColor("#1a6bbf")
AZUL_CLARO   = colors.HexColor("#e6f1fb")
GRIS_LINEA   = colors.HexColor("#d0d7e0")
ROJO         = colors.HexColor("#dc3545")
ROJO_CLARO   = colors.HexColor("#fde8ea")
NARANJA      = colors.HexColor("#fd7e14")
NARANJA_CLARO= colors.HexColor("#fff0e0")
AMARILLO_CL  = colors.HexColor("#fff8cc")
VERDE        = colors.HexColor("#198754")
VERDE_CLARO  = colors.HexColor("#e8f5ee")
BLANCO       = colors.white
GRIS_FONDO   = colors.HexColor("#f8f9fa")


def nivel_color(nivel: str):
    m = {"Alto": (ROJO, ROJO_CLARO), "Medio": (NARANJA, NARANJA_CLARO), "Bajo": (VERDE, VERDE_CLARO)}
    return m.get(nivel, (AZUL_MEDIO, AZUL_CLARO))


# ── GRÁFICO: MATRIZ DE CALOR ─────────────────────────────────────
def make_heat_map(riesgos: list) -> io.BytesIO:
    # Más ancho para dar espacio a la leyenda lateral
    fig, (ax, ax_leg) = plt.subplots(1, 2, figsize=(11, 6),
                                      gridspec_kw={"width_ratios": [5, 3]})
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    # ── Colores de celdas ──
    cell_colors = {
        (1,1):"#d4edda",(1,2):"#d4edda",(1,3):"#d4edda",(1,4):"#fff3cd",(1,5):"#fff3cd",
        (2,1):"#d4edda",(2,2):"#d4edda",(2,3):"#fff3cd",(2,4):"#fff3cd",(2,5):"#fde8ea",
        (3,1):"#d4edda",(3,2):"#fff3cd",(3,3):"#fff3cd",(3,4):"#fde8ea",(3,5):"#fde8ea",
        (4,1):"#fff3cd",(4,2):"#fff3cd",(4,3):"#fde8ea",(4,4):"#fde8ea",(4,5):"#fde8ea",
        (5,1):"#fff3cd",(5,2):"#fde8ea",(5,3):"#fde8ea",(5,4):"#fde8ea",(5,5):"#fde8ea",
    }

    nivel_bg = {"Alto": "#fde8ea", "Medio": "#fff3cd", "Bajo": "#d4edda"}
    nivel_fg = {"Alto": "#dc3545", "Medio": "#fd7e14", "Bajo": "#198754"}

    for (p, i), c in cell_colors.items():
        rect = patches.Rectangle((i-1, p-1), 1, 1,
                                  facecolor=c, edgecolor="#adb5bd", linewidth=0.8)
        ax.add_patch(rect)

    # ── Score en cada celda (esquina superior derecha, muy tenue) ──
    for p in range(1, 6):
        for i in range(1, 6):
            score = p * i
            ax.text(i - 0.08, p - 0.1, str(score),
                    ha="right", va="top", fontsize=7,
                    color="#999999", fontstyle="italic")

    # ── Plotear riesgos — manejo de colisiones con offset radial ──
    from collections import defaultdict
    cell_count = defaultdict(int)
    offsets = [
        (0.0,  0.0),   # 1er riesgo: centro
        (-0.2, 0.15),  # 2do: arriba izquierda
        ( 0.2, 0.15),  # 3ro: arriba derecha
        (-0.2,-0.15),  # 4to: abajo izquierda
        ( 0.2,-0.15),  # 5to: abajo derecha
    ]

    for r in riesgos:
        p   = r.get("probabilidad", 1)
        imp = r.get("impacto", 1)
        key = (p, imp)
        idx = cell_count[key]
        cell_count[key] += 1
        ox, oy = offsets[min(idx, len(offsets)-1)]

        cx = imp - 0.5 + ox
        cy = p   - 0.5 + oy

        nivel = r.get("nivel", "Medio")
        dot_color = nivel_fg.get(nivel, "#0a2540")

        # Círculo coloreado por nivel
        ax.plot(cx, cy, "o", markersize=20, color=dot_color,
                alpha=0.85, zorder=5)
        # ID del riesgo dentro del círculo
        rid = r["id"]  # "R01", "R02"…
        ax.text(cx, cy, rid, ha="center", va="center",
                fontsize=7, color="white", fontweight="bold", zorder=6)

    # ── Etiquetas de ejes completas ──
    ax.set_xlim(0, 5)
    ax.set_ylim(0, 5)
    ax.set_xticks([0.5, 1.5, 2.5, 3.5, 4.5])
    ax.set_xticklabels(
        ["1 — Mínimo", "2 — Bajo", "3 — Moderado", "4 — Alto", "5 — Catastrófico"],
        fontsize=8, rotation=20, ha="right"
    )
    ax.set_yticks([0.5, 1.5, 2.5, 3.5, 4.5])
    ax.set_yticklabels(
        ["1 — Raro", "2 — Poco probable", "3 — Posible", "4 — Probable", "5 — Casi seguro"],
        fontsize=8
    )
    ax.set_xlabel("Impacto", fontsize=10, fontweight="bold", labelpad=10)
    ax.set_ylabel("Probabilidad", fontsize=10, fontweight="bold", labelpad=10)
    ax.set_title("Matriz de Riesgo — Probabilidad × Impacto",
                 fontsize=11, fontweight="bold", pad=12)
    ax.tick_params(length=0)
    for spine in ax.spines.values():
        spine.set_edgecolor("#adb5bd")
        spine.set_linewidth(0.5)

    # ── Leyenda lateral con todos los riesgos ──
    ax_leg.axis("off")
    ax_leg.set_title("Referencias", fontsize=9, fontweight="bold",
                     loc="left", pad=4, color="#333333")

    # Encabezados de la leyenda
    ax_leg.text(0.0, 0.97, "ID", fontsize=8, fontweight="bold",
                color="#555555", transform=ax_leg.transAxes, va="top")
    ax_leg.text(0.18, 0.97, "Riesgo", fontsize=8, fontweight="bold",
                color="#555555", transform=ax_leg.transAxes, va="top")
    ax_leg.text(0.78, 0.97, "Nivel", fontsize=8, fontweight="bold",
                color="#555555", transform=ax_leg.transAxes, va="top")

    # Línea separadora
    ax_leg.plot([0, 1], [0.94, 0.94], color="#cccccc",
                linewidth=0.8, transform=ax_leg.transAxes)

    step = 0.085
    for idx, r in enumerate(riesgos):
        y = 0.91 - idx * step
        if y < 0.02:
            break

        nivel  = r.get("nivel", "Medio")
        bg_col = nivel_bg.get(nivel, "#fff3cd")
        fg_col = nivel_fg.get(nivel, "#fd7e14")
        rid    = r.get("id", "")
        nombre = r.get("nombre", "")

        # Fondo alterno suave
        if idx % 2 == 0:
            bg_rect = patches.FancyBboxPatch(
                (-0.02, y - 0.01), 1.04, step - 0.008,
                boxstyle="round,pad=0.01",
                facecolor="#f8f9fa", edgecolor="none",
                transform=ax_leg.transAxes, clip_on=False
            )
            ax_leg.add_patch(bg_rect)

        # Punto de color (nivel)
        ax_leg.plot(0.04, y + step/2 - 0.01, "o", markersize=8,
                    color=fg_col, transform=ax_leg.transAxes,
                    zorder=5, clip_on=False)
        ax_leg.text(0.04, y + step/2 - 0.01, rid[-2:],
                    ha="center", va="center", fontsize=5.5,
                    color="white", fontweight="bold",
                    transform=ax_leg.transAxes, clip_on=False)

        # Nombre del riesgo (recortado si muy largo)
        nombre_corto = nombre if len(nombre) <= 28 else nombre[:26] + "…"
        ax_leg.text(0.14, y + step/2 - 0.012, nombre_corto,
                    fontsize=7, color="#333333", va="center",
                    transform=ax_leg.transAxes, clip_on=False)

        # Badge de nivel
        ax_leg.text(0.82, y + step/2 - 0.012, nivel,
                    fontsize=6.5, color=fg_col, fontweight="bold",
                    va="center", transform=ax_leg.transAxes, clip_on=False)

    # Leyenda de colores (abajo)
    ax_leg.plot([0, 1], [0.12, 0.12], color="#cccccc",
                linewidth=0.8, transform=ax_leg.transAxes)
    ax_leg.text(0.0, 0.09, "Nivel de riesgo:", fontsize=7.5,
                fontweight="bold", color="#555", transform=ax_leg.transAxes)
    for i, (nivel, col) in enumerate([("Alto","#dc3545"),
                                       ("Medio","#fd7e14"),
                                       ("Bajo","#198754")]):
        ax_leg.plot(0.04 + i*0.33, 0.05, "o", markersize=8,
                    color=col, transform=ax_leg.transAxes)
        ax_leg.text(0.10 + i*0.33, 0.05, nivel, fontsize=7,
                    color=col, fontweight="bold", va="center",
                    transform=ax_leg.transAxes)

    plt.tight_layout(pad=1.5)
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close()
    buf.seek(0)
    return buf


# ── GRÁFICO: MONTE CARLO ─────────────────────────────────────────
def make_monte_carlo(data: dict, presupuesto: float) -> io.BytesIO:
    riesgos = data.get("riesgos", [])
    np.random.seed(42)
    N = 10_000
    total = np.zeros(N)

    for r in riesgos:
        mn  = r.get("impacto_economico_min_usd", 0)
        mx  = r.get("impacto_economico_max_usd", 0)
        mp  = (mn + mx) / 2
        p   = r.get("probabilidad", 1) / 5
        ocurre = np.random.rand(N) < p
        costo  = np.random.triangular(mn, mp, mx, N)
        total += ocurre * costo

    resultados = presupuesto + total
    p50 = float(np.percentile(resultados, 50))
    p80 = float(np.percentile(resultados, 80))
    p90 = float(np.percentile(resultados, 90))

    fig, ax = plt.subplots(figsize=(6.5, 3.5))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    ax.hist(resultados / 1e6, bins=60, color="#1a6bbf", alpha=0.7, edgecolor="white", linewidth=0.3)

    for val, label, col in [(p50,"P50","#198754"), (p80,"P80","#fd7e14"), (p90,"P90","#dc3545")]:
        ax.axvline(val/1e6, color=col, linewidth=1.8, linestyle="--", zorder=5)
        ax.text(val/1e6 + 0.015, ax.get_ylim()[1]*0.85 if ax.get_ylim()[1] > 0 else 100,
                f"{label}\n${val/1e6:.2f}M", fontsize=8, color=col, fontweight="bold")

    ax.set_xlabel("Costo total del proyecto (millones USD)", fontsize=9)
    ax.set_ylabel("Frecuencia (de 10,000 escenarios)", fontsize=9)
    ax.set_title("Simulación Monte Carlo — Distribución de Costo", fontsize=10, fontweight="bold")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    for spine in ["bottom","left"]:
        ax.spines[spine].set_edgecolor("#adb5bd")
        ax.spines[spine].set_linewidth(0.5)
    ax.tick_params(labelsize=8, length=0)
    ax.yaxis.grid(True, linestyle="--", alpha=0.4, linewidth=0.4)
    ax.set_axisbelow(True)

    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close()
    buf.seek(0)
    return buf, p50, p80, p90


# ── GENERADOR PRINCIPAL ───────────────────────────────────────────
def generate_pdf(data: dict) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm,  bottomMargin=2*cm
    )

    styles = getSampleStyleSheet()
    story  = []

    # ── Estilos personalizados ──
    def st(name, **kw):
        return ParagraphStyle(name, parent=styles["Normal"], **kw)

    s_titulo    = st("titulo",    fontSize=28, textColor=BLANCO, fontName="Helvetica-Bold",
                     leading=34, alignment=TA_CENTER)
    s_subtitulo = st("subtitulo", fontSize=13, textColor=AZUL_CLARO, fontName="Helvetica",
                     leading=18, alignment=TA_CENTER)
    s_meta      = st("meta",      fontSize=10, textColor=AZUL_CLARO, leading=16, alignment=TA_CENTER)
    s_h1        = st("h1",        fontSize=14, textColor=AZUL_OSCURO, fontName="Helvetica-Bold",
                     leading=18, spaceBefore=14, spaceAfter=6)
    s_h2        = st("h2",        fontSize=11, textColor=AZUL_MEDIO,  fontName="Helvetica-Bold",
                     leading=14, spaceBefore=10, spaceAfter=4)
    s_body      = st("body",      fontSize=9,  textColor=colors.HexColor("#333333"),
                     leading=14, alignment=TA_JUSTIFY)
    s_cell      = st("cell",      fontSize=8,  textColor=colors.HexColor("#333333"), leading=11)
    s_cell_b    = st("cell_b",    fontSize=8,  textColor=AZUL_OSCURO, fontName="Helvetica-Bold", leading=11)
    s_small     = st("small",     fontSize=8,  textColor=colors.HexColor("#666666"), leading=11)

    proy = data.get("proyecto", {})
    riesgos = data.get("riesgos", [])
    presupuesto = proy.get("presupuesto_usd", 0)

    # ──────────────────────────────────────────────────
    # PÁGINA 1 — PORTADA
    # ──────────────────────────────────────────────────

    # Fondo azul simulado con tabla de una celda
    portada_content = [
        [Paragraph("REPORTE DE GESTIÓN DE RIESGOS", s_titulo)],
        [Spacer(1, 0.3*cm)],
        [Paragraph(proy.get("nombre", "Proyecto"), s_subtitulo)],
        [Spacer(1, 0.6*cm)],
        [HRFlowable(width="60%", thickness=1, color=AZUL_CLARO, hAlign="CENTER")],
        [Spacer(1, 0.6*cm)],
        [Paragraph(f"Ubicación: {proy.get('ubicacion','—')}", s_meta)],
        [Paragraph(f"Tipo: {proy.get('tipo','—')}", s_meta)],
        [Paragraph(f"Presupuesto: ${presupuesto:,.0f} USD", s_meta)],
        [Paragraph(f"Plazo: {proy.get('plazo_meses','—')} meses", s_meta)],
        [Paragraph(f"Contrato: {proy.get('tipo_contrato','—')}", s_meta)],
        [Spacer(1, 0.6*cm)],
        [HRFlowable(width="60%", thickness=1, color=AZUL_CLARO, hAlign="CENTER")],
        [Spacer(1, 0.6*cm)],
        [Paragraph(f"Fecha: {datetime.now().strftime('%d/%m/%Y')}", s_meta)],
        [Paragraph("Generado por Agente IA — Gestión de Riesgos", s_meta)],
    ]

    portada_table = Table([[item] for item in [
        Paragraph("REPORTE DE GESTIÓN DE RIESGOS", s_titulo),
        Spacer(1, 0.4*cm),
        Paragraph(proy.get("nombre", "Proyecto"), s_subtitulo),
        Spacer(1, 0.8*cm),
        HRFlowable(width="80%", thickness=1, color=AZUL_CLARO, hAlign="CENTER"),
        Spacer(1, 0.8*cm),
        Paragraph(f"<b>Ubicación:</b>  {proy.get('ubicacion','—')}", s_meta),
        Paragraph(f"<b>Tipo:</b>  {proy.get('tipo','—')}", s_meta),
        Paragraph(f"<b>Presupuesto:</b>  ${presupuesto:,.0f} USD", s_meta),
        Paragraph(f"<b>Plazo contractual:</b>  {proy.get('plazo_meses','—')} meses", s_meta),
        Paragraph(f"<b>Tipo de contrato:</b>  {proy.get('tipo_contrato','—')}", s_meta),
        Spacer(1, 0.8*cm),
        HRFlowable(width="80%", thickness=1, color=AZUL_CLARO, hAlign="CENTER"),
        Spacer(1, 0.8*cm),
        Paragraph(f"Fecha de emisión: {datetime.now().strftime('%d de %B de %Y')}", s_meta),
        Paragraph("Generado con Agente IA · ISO 31000 / PMBOK", s_meta),
    ]], colWidths=[17*cm])

    portada_table.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), AZUL_OSCURO),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING",    (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ("LEFTPADDING",   (0,0), (-1,-1), 30),
        ("RIGHTPADDING",  (0,0), (-1,-1), 30),
    ]))

    story.append(portada_table)
    story.append(PageBreak())

    # ──────────────────────────────────────────────────
    # PÁGINA 2 — RESUMEN EJECUTIVO
    # ──────────────────────────────────────────────────
    story.append(Paragraph("1. Resumen Ejecutivo", s_h1))
    story.append(HRFlowable(width="100%", thickness=1, color=AZUL_MEDIO))
    story.append(Spacer(1, 0.4*cm))

    resumen = data.get("resumen_ejecutivo", "Sin resumen disponible.")
    story.append(Paragraph(resumen, s_body))
    story.append(Spacer(1, 0.5*cm))

    # Métricas clave en cards
    altos  = sum(1 for r in riesgos if r.get("nivel") == "Alto")
    medios = sum(1 for r in riesgos if r.get("nivel") == "Medio")
    bajos  = sum(1 for r in riesgos if r.get("nivel") == "Bajo")
    contingencia = data.get("contingencia_recomendada_usd", 0)

    def metric_cell(label, value, bg):
        return Table(
            [[Paragraph(label, s_small)], [Paragraph(f"<b>{value}</b>",
              st("mv", fontSize=18, textColor=AZUL_OSCURO, fontName="Helvetica-Bold",
                 leading=22, alignment=TA_CENTER))]],
            colWidths=[3.8*cm]
        )

    metrics = Table([
        [
            Table([[Paragraph("Riesgos Altos",   st("ml",fontSize=8,textColor=colors.HexColor("#666"),leading=11,alignment=TA_CENTER))],
                   [Paragraph(f"<b>{altos}</b>",   st("mv",fontSize=22,textColor=ROJO,fontName="Helvetica-Bold",leading=26,alignment=TA_CENTER))]],
                  colWidths=[3.6*cm]),
            Table([[Paragraph("Riesgos Medios", st("ml",fontSize=8,textColor=colors.HexColor("#666"),leading=11,alignment=TA_CENTER))],
                   [Paragraph(f"<b>{medios}</b>",  st("mv",fontSize=22,textColor=NARANJA,fontName="Helvetica-Bold",leading=26,alignment=TA_CENTER))]],
                  colWidths=[3.6*cm]),
            Table([[Paragraph("Riesgos Bajos",  st("ml",fontSize=8,textColor=colors.HexColor("#666"),leading=11,alignment=TA_CENTER))],
                   [Paragraph(f"<b>{bajos}</b>",   st("mv",fontSize=22,textColor=VERDE,fontName="Helvetica-Bold",leading=26,alignment=TA_CENTER))]],
                  colWidths=[3.6*cm]),
            Table([[Paragraph("Contingencia rec.",st("ml",fontSize=8,textColor=colors.HexColor("#666"),leading=11,alignment=TA_CENTER))],
                   [Paragraph(f"<b>${contingencia/1000:.0f}K</b>",st("mv",fontSize=22,textColor=AZUL_MEDIO,fontName="Helvetica-Bold",leading=26,alignment=TA_CENTER))]],
                  colWidths=[3.6*cm]),
        ]
    ], colWidths=[4.0*cm, 4.0*cm, 4.0*cm, 4.0*cm])

    metrics.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (0,-1), ROJO_CLARO),
        ("BACKGROUND",    (1,0), (1,-1), NARANJA_CLARO),
        ("BACKGROUND",    (2,0), (2,-1), VERDE_CLARO),
        ("BACKGROUND",    (3,0), (3,-1), AZUL_CLARO),
        ("ROUNDEDCORNERS",(0,0), (-1,-1), [6,6,6,6]),
        ("TOPPADDING",    (0,0), (-1,-1), 10),
        ("BOTTOMPADDING", (0,0), (-1,-1), 10),
        ("LEFTPADDING",   (0,0), (-1,-1), 8),
        ("RIGHTPADDING",  (0,0), (-1,-1), 8),
        ("ALIGN",         (0,0), (-1,-1), "CENTER"),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ("LINEAFTER",     (0,0), (2,-1), 0.5, GRIS_LINEA),
    ]))
    story.append(metrics)
    story.append(PageBreak())

    # ──────────────────────────────────────────────────
    # PÁGINA 3 — TABLA DE RIESGOS
    # ──────────────────────────────────────────────────
    story.append(Paragraph("2. Registro de Riesgos Identificados", s_h1))
    story.append(HRFlowable(width="100%", thickness=1, color=AZUL_MEDIO))
    story.append(Spacer(1, 0.4*cm))

    # Encabezado de tabla
    headers = ["ID", "Riesgo", "Cat.", "P", "I", "Score", "Nivel", "Acción recomendada"]
    table_data = [[Paragraph(h, st("th", fontSize=8, textColor=BLANCO,
                                   fontName="Helvetica-Bold", leading=11, alignment=TA_CENTER))
                   for h in headers]]

    col_w = [1.0*cm, 3.8*cm, 1.6*cm, 0.7*cm, 0.7*cm, 1.0*cm, 1.2*cm, 6.5*cm]

    style_cmds = [
        ("BACKGROUND",    (0,0), (-1,0), AZUL_OSCURO),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [BLANCO, GRIS_FONDO]),
        ("LINEBELOW",     (0,0), (-1,-1), 0.3, GRIS_LINEA),
        ("VALIGN",        (0,0), (-1,-1), "TOP"),
        ("TOPPADDING",    (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING",   (0,0), (-1,-1), 4),
        ("RIGHTPADDING",  (0,0), (-1,-1), 4),
        ("ALIGN",         (0,0), (0,-1), "CENTER"),
        ("ALIGN",         (3,0), (5,-1), "CENTER"),
    ]

    for i, r in enumerate(riesgos, start=1):
        nivel = r.get("nivel", "Medio")
        fg, bg = nivel_color(nivel)
        nivel_para = Paragraph(
            f"<b>{nivel}</b>",
            st(f"nv{i}", fontSize=7, textColor=fg, fontName="Helvetica-Bold",
               leading=10, alignment=TA_CENTER)
        )
        row = [
            Paragraph(r.get("id",""), st("rid",fontSize=8,textColor=AZUL_MEDIO,fontName="Helvetica-Bold",leading=11,alignment=TA_CENTER)),
            Paragraph(r.get("nombre",""), s_cell),
            Paragraph(r.get("categoria",""), st("cat",fontSize=7,textColor=colors.HexColor("#555"),leading=10)),
            Paragraph(str(r.get("probabilidad","")), st("pv",fontSize=9,fontName="Helvetica-Bold",leading=12,alignment=TA_CENTER)),
            Paragraph(str(r.get("impacto","")),      st("iv",fontSize=9,fontName="Helvetica-Bold",leading=12,alignment=TA_CENTER)),
            Paragraph(f"<b>{r.get('score','')}</b>", st("sv",fontSize=9,fontName="Helvetica-Bold",leading=12,alignment=TA_CENTER)),
            nivel_para,
            Paragraph(r.get("accion",""), s_cell),
        ]
        table_data.append(row)
        # Color fondo celda nivel
        style_cmds.append(("BACKGROUND", (6, i), (6, i), bg))

    risk_table = Table(table_data, colWidths=col_w, repeatRows=1)
    risk_table.setStyle(TableStyle(style_cmds))
    story.append(risk_table)
    story.append(PageBreak())

    # ──────────────────────────────────────────────────
    # PÁGINA 4 — GRÁFICOS
    # ──────────────────────────────────────────────────
    story.append(Paragraph("3. Análisis Visual de Riesgos", s_h1))
    story.append(HRFlowable(width="100%", thickness=1, color=AZUL_MEDIO))
    story.append(Spacer(1, 0.3*cm))

    # Matriz de calor
    story.append(Paragraph("3.1 Matriz de Calor Probabilidad × Impacto", s_h2))
    heatmap_buf = make_heat_map(riesgos)
    story.append(Image(heatmap_buf, width=16*cm, height=8.5*cm, hAlign="CENTER"))
    story.append(Spacer(1, 0.5*cm))

    # Monte Carlo
    story.append(Paragraph("3.2 Simulación Monte Carlo — Distribución de Costo Total", s_h2))
    mc_buf, p50, p80, p90 = make_monte_carlo(data, presupuesto)
    story.append(Image(mc_buf, width=14*cm, height=7*cm, hAlign="CENTER"))
    story.append(Spacer(1, 0.4*cm))

    # Tabla de percentiles
    perc_data = [
        [Paragraph("Percentil", st("ph",fontSize=9,textColor=BLANCO,fontName="Helvetica-Bold",leading=12,alignment=TA_CENTER)),
         Paragraph("Costo estimado",st("ph",fontSize=9,textColor=BLANCO,fontName="Helvetica-Bold",leading=12,alignment=TA_CENTER)),
         Paragraph("Reserva sobre presupuesto",st("ph",fontSize=9,textColor=BLANCO,fontName="Helvetica-Bold",leading=12,alignment=TA_CENTER)),
         Paragraph("Interpretación",st("ph",fontSize=9,textColor=BLANCO,fontName="Helvetica-Bold",leading=12,alignment=TA_CENTER))],
        [Paragraph("<b>P50</b>",st("pc",fontSize=9,textColor=VERDE,fontName="Helvetica-Bold",leading=12,alignment=TA_CENTER)),
         Paragraph(f"${p50:,.0f}",st("pv",fontSize=9,leading=12,alignment=TA_CENTER)),
         Paragraph(f"+${p50-presupuesto:,.0f}",st("pv",fontSize=9,leading=12,alignment=TA_CENTER)),
         Paragraph("Escenario base — 50% de probabilidad",st("pv",fontSize=8,leading=12))],
        [Paragraph("<b>P80</b>",st("pc",fontSize=9,textColor=NARANJA,fontName="Helvetica-Bold",leading=12,alignment=TA_CENTER)),
         Paragraph(f"${p80:,.0f}",st("pv",fontSize=9,leading=12,alignment=TA_CENTER)),
         Paragraph(f"+${p80-presupuesto:,.0f}",st("pv",fontSize=9,leading=12,alignment=TA_CENTER)),
         Paragraph("Recomendado para reserva de contingencia",st("pv",fontSize=8,leading=12))],
        [Paragraph("<b>P90</b>",st("pc",fontSize=9,textColor=ROJO,fontName="Helvetica-Bold",leading=12,alignment=TA_CENTER)),
         Paragraph(f"${p90:,.0f}",st("pv",fontSize=9,leading=12,alignment=TA_CENTER)),
         Paragraph(f"+${p90-presupuesto:,.0f}",st("pv",fontSize=9,leading=12,alignment=TA_CENTER)),
         Paragraph("Escenario pesimista — planificación de riesgo máximo",st("pv",fontSize=8,leading=12))],
    ]
    perc_table = Table(perc_data, colWidths=[2.5*cm, 3.5*cm, 4.5*cm, 6.5*cm])
    perc_table.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0), AZUL_OSCURO),
        ("BACKGROUND",    (0,1), (-1,1), VERDE_CLARO),
        ("BACKGROUND",    (0,2), (-1,2), NARANJA_CLARO),
        ("BACKGROUND",    (0,3), (-1,3), ROJO_CLARO),
        ("LINEBELOW",     (0,0), (-1,-1), 0.3, GRIS_LINEA),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING",    (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ("LEFTPADDING",   (0,0), (-1,-1), 6),
        ("RIGHTPADDING",  (0,0), (-1,-1), 6),
    ]))
    story.append(perc_table)

    doc.build(story)
    return buf.getvalue()
# import io
# import json
# from reportlab.lib.pagesizes import A4
# from reportlab.lib import colors
# from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
# from reportlab.lib.units import cm
# from reportlab.platypus import (
#     SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
#     Image, PageBreak, HRFlowable
# )
# from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
# import matplotlib
# matplotlib.use("Agg")
# import matplotlib.pyplot as plt
# import matplotlib.patches as patches
# import numpy as np
# from datetime import datetime


# # ── COLORES ──────────────────────────────────────────────────────
# AZUL_OSCURO  = colors.HexColor("#0a2540")
# AZUL_MEDIO   = colors.HexColor("#1a6bbf")
# AZUL_CLARO   = colors.HexColor("#e6f1fb")
# GRIS_LINEA   = colors.HexColor("#d0d7e0")
# ROJO         = colors.HexColor("#dc3545")
# ROJO_CLARO   = colors.HexColor("#fde8ea")
# NARANJA      = colors.HexColor("#fd7e14")
# NARANJA_CLARO= colors.HexColor("#fff0e0")
# AMARILLO_CL  = colors.HexColor("#fff8cc")
# VERDE        = colors.HexColor("#198754")
# VERDE_CLARO  = colors.HexColor("#e8f5ee")
# BLANCO       = colors.white
# GRIS_FONDO   = colors.HexColor("#f8f9fa")


# def nivel_color(nivel: str):
#     m = {"Alto": (ROJO, ROJO_CLARO), "Medio": (NARANJA, NARANJA_CLARO), "Bajo": (VERDE, VERDE_CLARO)}
#     return m.get(nivel, (AZUL_MEDIO, AZUL_CLARO))


# # ── GRÁFICO: MATRIZ DE CALOR ─────────────────────────────────────
# def make_heat_map(riesgos: list) -> io.BytesIO:
#     fig, ax = plt.subplots(figsize=(6, 5))
#     fig.patch.set_facecolor("white")
#     ax.set_facecolor("white")

#     # Colores de celdas
#     cell_colors = {
#         (1,1):"#d4edda",(1,2):"#d4edda",(1,3):"#d4edda",(1,4):"#fff3cd",(1,5):"#fff3cd",
#         (2,1):"#d4edda",(2,2):"#d4edda",(2,3):"#fff3cd",(2,4):"#fff3cd",(2,5):"#fde8ea",
#         (3,1):"#d4edda",(3,2):"#fff3cd",(3,3):"#fff3cd",(3,4):"#fde8ea",(3,5):"#fde8ea",
#         (4,1):"#fff3cd",(4,2):"#fff3cd",(4,3):"#fde8ea",(4,4):"#fde8ea",(4,5):"#fde8ea",
#         (5,1):"#fff3cd",(5,2):"#fde8ea",(5,3):"#fde8ea",(5,4):"#fde8ea",(5,5):"#fde8ea",
#     }

#     for (p, i), c in cell_colors.items():
#         rect = patches.Rectangle((i-1, p-1), 1, 1, facecolor=c, edgecolor="#adb5bd", linewidth=0.5)
#         ax.add_patch(rect)

#     # Plotear riesgos
#     plotted = {}
#     for r in riesgos:
#         p = r.get("probabilidad", 1)
#         i = r.get("impacto", 1)
#         key = (p, i)
#         offset = plotted.get(key, 0) * 0.15
#         ax.plot(i - 0.5 + offset, p - 0.5, "o", markersize=9,
#                 color="#0a2540", zorder=5)
#         ax.text(i - 0.5 + offset, p - 0.5, r["id"].replace("R0","").replace("R",""),
#                 ha="center", va="center", fontsize=6, color="white", fontweight="bold", zorder=6)
#         plotted[key] = plotted.get(key, 0) + 1

#     ax.set_xlim(0, 5)
#     ax.set_ylim(0, 5)
#     ax.set_xticks([0.5,1.5,2.5,3.5,4.5])
#     ax.set_xticklabels(["1\nMínimo","2\nBajo","3\nModerado","4\nAlto","5\nCatastrófico"], fontsize=8)
#     ax.set_yticks([0.5,1.5,2.5,3.5,4.5])
#     ax.set_yticklabels(["1\nRaro","2\nPoco\nprobable","3\nPosible","4\nProbable","5\nCasi\nseguro"], fontsize=8)
#     ax.set_xlabel("Impacto", fontsize=9, fontweight="bold", labelpad=8)
#     ax.set_ylabel("Probabilidad", fontsize=9, fontweight="bold", labelpad=8)
#     ax.set_title("Matriz de Riesgo", fontsize=11, fontweight="bold", pad=10)
#     ax.tick_params(length=0)
#     for spine in ax.spines.values():
#         spine.set_edgecolor("#adb5bd")
#         spine.set_linewidth(0.5)

#     plt.tight_layout()
#     buf = io.BytesIO()
#     plt.savefig(buf, format="png", dpi=150, bbox_inches="tight")
#     plt.close()
#     buf.seek(0)
#     return buf


# # ── GRÁFICO: MONTE CARLO ─────────────────────────────────────────
# def make_monte_carlo(data: dict, presupuesto: float) -> io.BytesIO:
#     riesgos = data.get("riesgos", [])
#     np.random.seed(42)
#     N = 10_000
#     total = np.zeros(N)

#     for r in riesgos:
#         mn  = r.get("impacto_economico_min_usd", 0)
#         mx  = r.get("impacto_economico_max_usd", 0)
#         mp  = (mn + mx) / 2
#         p   = r.get("probabilidad", 1) / 5
#         ocurre = np.random.rand(N) < p
#         costo  = np.random.triangular(mn, mp, mx, N)
#         total += ocurre * costo

#     resultados = presupuesto + total
#     p50 = float(np.percentile(resultados, 50))
#     p80 = float(np.percentile(resultados, 80))
#     p90 = float(np.percentile(resultados, 90))

#     fig, ax = plt.subplots(figsize=(6.5, 3.5))
#     fig.patch.set_facecolor("white")
#     ax.set_facecolor("white")

#     ax.hist(resultados / 1e6, bins=60, color="#1a6bbf", alpha=0.7, edgecolor="white", linewidth=0.3)

#     for val, label, col in [(p50,"P50","#198754"), (p80,"P80","#fd7e14"), (p90,"P90","#dc3545")]:
#         ax.axvline(val/1e6, color=col, linewidth=1.8, linestyle="--", zorder=5)
#         ax.text(val/1e6 + 0.015, ax.get_ylim()[1]*0.85 if ax.get_ylim()[1] > 0 else 100,
#                 f"{label}\n${val/1e6:.2f}M", fontsize=8, color=col, fontweight="bold")

#     ax.set_xlabel("Costo total del proyecto (millones USD)", fontsize=9)
#     ax.set_ylabel("Frecuencia (de 10,000 escenarios)", fontsize=9)
#     ax.set_title("Simulación Monte Carlo — Distribución de Costo", fontsize=10, fontweight="bold")
#     ax.spines["top"].set_visible(False)
#     ax.spines["right"].set_visible(False)
#     for spine in ["bottom","left"]:
#         ax.spines[spine].set_edgecolor("#adb5bd")
#         ax.spines[spine].set_linewidth(0.5)
#     ax.tick_params(labelsize=8, length=0)
#     ax.yaxis.grid(True, linestyle="--", alpha=0.4, linewidth=0.4)
#     ax.set_axisbelow(True)

#     plt.tight_layout()
#     buf = io.BytesIO()
#     plt.savefig(buf, format="png", dpi=150, bbox_inches="tight")
#     plt.close()
#     buf.seek(0)
#     return buf, p50, p80, p90


# # ── GENERADOR PRINCIPAL ───────────────────────────────────────────
# def generate_pdf(data: dict) -> bytes:
#     buf = io.BytesIO()
#     doc = SimpleDocTemplate(
#         buf, pagesize=A4,
#         leftMargin=2*cm, rightMargin=2*cm,
#         topMargin=2*cm,  bottomMargin=2*cm
#     )

#     styles = getSampleStyleSheet()
#     story  = []

#     # ── Estilos personalizados ──
#     def st(name, **kw):
#         return ParagraphStyle(name, parent=styles["Normal"], **kw)

#     s_titulo    = st("titulo",    fontSize=28, textColor=BLANCO, fontName="Helvetica-Bold",
#                      leading=34, alignment=TA_CENTER)
#     s_subtitulo = st("subtitulo", fontSize=13, textColor=AZUL_CLARO, fontName="Helvetica",
#                      leading=18, alignment=TA_CENTER)
#     s_meta      = st("meta",      fontSize=10, textColor=AZUL_CLARO, leading=16, alignment=TA_CENTER)
#     s_h1        = st("h1",        fontSize=14, textColor=AZUL_OSCURO, fontName="Helvetica-Bold",
#                      leading=18, spaceBefore=14, spaceAfter=6)
#     s_h2        = st("h2",        fontSize=11, textColor=AZUL_MEDIO,  fontName="Helvetica-Bold",
#                      leading=14, spaceBefore=10, spaceAfter=4)
#     s_body      = st("body",      fontSize=9,  textColor=colors.HexColor("#333333"),
#                      leading=14, alignment=TA_JUSTIFY)
#     s_cell      = st("cell",      fontSize=8,  textColor=colors.HexColor("#333333"), leading=11)
#     s_cell_b    = st("cell_b",    fontSize=8,  textColor=AZUL_OSCURO, fontName="Helvetica-Bold", leading=11)
#     s_small     = st("small",     fontSize=8,  textColor=colors.HexColor("#666666"), leading=11)

#     proy = data.get("proyecto", {})
#     riesgos = data.get("riesgos", [])
#     presupuesto = proy.get("presupuesto_usd", 0)

#     # ──────────────────────────────────────────────────
#     # PÁGINA 1 — PORTADA
#     # ──────────────────────────────────────────────────

#     # Fondo azul simulado con tabla de una celda
#     portada_content = [
#         [Paragraph("REPORTE DE GESTIÓN DE RIESGOS", s_titulo)],
#         [Spacer(1, 0.3*cm)],
#         [Paragraph(proy.get("nombre", "Proyecto"), s_subtitulo)],
#         [Spacer(1, 0.6*cm)],
#         [HRFlowable(width="60%", thickness=1, color=AZUL_CLARO, hAlign="CENTER")],
#         [Spacer(1, 0.6*cm)],
#         [Paragraph(f"Ubicación: {proy.get('ubicacion','—')}", s_meta)],
#         [Paragraph(f"Tipo: {proy.get('tipo','—')}", s_meta)],
#         [Paragraph(f"Presupuesto: ${presupuesto:,.0f} USD", s_meta)],
#         [Paragraph(f"Plazo: {proy.get('plazo_meses','—')} meses", s_meta)],
#         [Paragraph(f"Contrato: {proy.get('tipo_contrato','—')}", s_meta)],
#         [Spacer(1, 0.6*cm)],
#         [HRFlowable(width="60%", thickness=1, color=AZUL_CLARO, hAlign="CENTER")],
#         [Spacer(1, 0.6*cm)],
#         [Paragraph(f"Fecha: {datetime.now().strftime('%d/%m/%Y')}", s_meta)],
#         [Paragraph("Generado por Agente IA — Gestión de Riesgos", s_meta)],
#     ]

#     portada_table = Table([[item] for item in [
#         Paragraph("REPORTE DE GESTIÓN DE RIESGOS", s_titulo),
#         Spacer(1, 0.4*cm),
#         Paragraph(proy.get("nombre", "Proyecto"), s_subtitulo),
#         Spacer(1, 0.8*cm),
#         HRFlowable(width="80%", thickness=1, color=AZUL_CLARO, hAlign="CENTER"),
#         Spacer(1, 0.8*cm),
#         Paragraph(f"<b>Ubicación:</b>  {proy.get('ubicacion','—')}", s_meta),
#         Paragraph(f"<b>Tipo:</b>  {proy.get('tipo','—')}", s_meta),
#         Paragraph(f"<b>Presupuesto:</b>  ${presupuesto:,.0f} USD", s_meta),
#         Paragraph(f"<b>Plazo contractual:</b>  {proy.get('plazo_meses','—')} meses", s_meta),
#         Paragraph(f"<b>Tipo de contrato:</b>  {proy.get('tipo_contrato','—')}", s_meta),
#         Spacer(1, 0.8*cm),
#         HRFlowable(width="80%", thickness=1, color=AZUL_CLARO, hAlign="CENTER"),
#         Spacer(1, 0.8*cm),
#         Paragraph(f"Fecha de emisión: {datetime.now().strftime('%d de %B de %Y')}", s_meta),
#         Paragraph("Generado con Agente IA · ISO 31000 / PMBOK", s_meta),
#     ]], colWidths=[17*cm])

#     portada_table.setStyle(TableStyle([
#         ("BACKGROUND",    (0,0), (-1,-1), AZUL_OSCURO),
#         ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
#         ("TOPPADDING",    (0,0), (-1,-1), 6),
#         ("BOTTOMPADDING", (0,0), (-1,-1), 6),
#         ("LEFTPADDING",   (0,0), (-1,-1), 30),
#         ("RIGHTPADDING",  (0,0), (-1,-1), 30),
#     ]))

#     story.append(portada_table)
#     story.append(PageBreak())

#     # ──────────────────────────────────────────────────
#     # PÁGINA 2 — RESUMEN EJECUTIVO
#     # ──────────────────────────────────────────────────
#     story.append(Paragraph("1. Resumen Ejecutivo", s_h1))
#     story.append(HRFlowable(width="100%", thickness=1, color=AZUL_MEDIO))
#     story.append(Spacer(1, 0.4*cm))

#     resumen = data.get("resumen_ejecutivo", "Sin resumen disponible.")
#     story.append(Paragraph(resumen, s_body))
#     story.append(Spacer(1, 0.5*cm))

#     # Métricas clave en cards
#     altos  = sum(1 for r in riesgos if r.get("nivel") == "Alto")
#     medios = sum(1 for r in riesgos if r.get("nivel") == "Medio")
#     bajos  = sum(1 for r in riesgos if r.get("nivel") == "Bajo")
#     contingencia = data.get("contingencia_recomendada_usd", 0)

#     def metric_cell(label, value, bg):
#         return Table(
#             [[Paragraph(label, s_small)], [Paragraph(f"<b>{value}</b>",
#               st("mv", fontSize=18, textColor=AZUL_OSCURO, fontName="Helvetica-Bold",
#                  leading=22, alignment=TA_CENTER))]],
#             colWidths=[3.8*cm]
#         )

#     metrics = Table([
#         [
#             Table([[Paragraph("Riesgos Altos",   st("ml",fontSize=8,textColor=colors.HexColor("#666"),leading=11,alignment=TA_CENTER))],
#                    [Paragraph(f"<b>{altos}</b>",   st("mv",fontSize=22,textColor=ROJO,fontName="Helvetica-Bold",leading=26,alignment=TA_CENTER))]],
#                   colWidths=[3.6*cm]),
#             Table([[Paragraph("Riesgos Medios", st("ml",fontSize=8,textColor=colors.HexColor("#666"),leading=11,alignment=TA_CENTER))],
#                    [Paragraph(f"<b>{medios}</b>",  st("mv",fontSize=22,textColor=NARANJA,fontName="Helvetica-Bold",leading=26,alignment=TA_CENTER))]],
#                   colWidths=[3.6*cm]),
#             Table([[Paragraph("Riesgos Bajos",  st("ml",fontSize=8,textColor=colors.HexColor("#666"),leading=11,alignment=TA_CENTER))],
#                    [Paragraph(f"<b>{bajos}</b>",   st("mv",fontSize=22,textColor=VERDE,fontName="Helvetica-Bold",leading=26,alignment=TA_CENTER))]],
#                   colWidths=[3.6*cm]),
#             Table([[Paragraph("Contingencia rec.",st("ml",fontSize=8,textColor=colors.HexColor("#666"),leading=11,alignment=TA_CENTER))],
#                    [Paragraph(f"<b>${contingencia/1000:.0f}K</b>",st("mv",fontSize=22,textColor=AZUL_MEDIO,fontName="Helvetica-Bold",leading=26,alignment=TA_CENTER))]],
#                   colWidths=[3.6*cm]),
#         ]
#     ], colWidths=[4.0*cm, 4.0*cm, 4.0*cm, 4.0*cm])

#     metrics.setStyle(TableStyle([
#         ("BACKGROUND",    (0,0), (0,-1), ROJO_CLARO),
#         ("BACKGROUND",    (1,0), (1,-1), NARANJA_CLARO),
#         ("BACKGROUND",    (2,0), (2,-1), VERDE_CLARO),
#         ("BACKGROUND",    (3,0), (3,-1), AZUL_CLARO),
#         ("ROUNDEDCORNERS",(0,0), (-1,-1), [6,6,6,6]),
#         ("TOPPADDING",    (0,0), (-1,-1), 10),
#         ("BOTTOMPADDING", (0,0), (-1,-1), 10),
#         ("LEFTPADDING",   (0,0), (-1,-1), 8),
#         ("RIGHTPADDING",  (0,0), (-1,-1), 8),
#         ("ALIGN",         (0,0), (-1,-1), "CENTER"),
#         ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
#         ("LINEAFTER",     (0,0), (2,-1), 0.5, GRIS_LINEA),
#     ]))
#     story.append(metrics)
#     story.append(PageBreak())

#     # ──────────────────────────────────────────────────
#     # PÁGINA 3 — TABLA DE RIESGOS
#     # ──────────────────────────────────────────────────
#     story.append(Paragraph("2. Registro de Riesgos Identificados", s_h1))
#     story.append(HRFlowable(width="100%", thickness=1, color=AZUL_MEDIO))
#     story.append(Spacer(1, 0.4*cm))

#     # Encabezado de tabla
#     headers = ["ID", "Riesgo", "Cat.", "P", "I", "Score", "Nivel", "Acción recomendada"]
#     table_data = [[Paragraph(h, st("th", fontSize=8, textColor=BLANCO,
#                                    fontName="Helvetica-Bold", leading=11, alignment=TA_CENTER))
#                    for h in headers]]

#     col_w = [1.0*cm, 3.8*cm, 1.6*cm, 0.7*cm, 0.7*cm, 1.0*cm, 1.2*cm, 6.5*cm]

#     style_cmds = [
#         ("BACKGROUND",    (0,0), (-1,0), AZUL_OSCURO),
#         ("ROWBACKGROUNDS",(0,1), (-1,-1), [BLANCO, GRIS_FONDO]),
#         ("LINEBELOW",     (0,0), (-1,-1), 0.3, GRIS_LINEA),
#         ("VALIGN",        (0,0), (-1,-1), "TOP"),
#         ("TOPPADDING",    (0,0), (-1,-1), 5),
#         ("BOTTOMPADDING", (0,0), (-1,-1), 5),
#         ("LEFTPADDING",   (0,0), (-1,-1), 4),
#         ("RIGHTPADDING",  (0,0), (-1,-1), 4),
#         ("ALIGN",         (0,0), (0,-1), "CENTER"),
#         ("ALIGN",         (3,0), (5,-1), "CENTER"),
#     ]

#     for i, r in enumerate(riesgos, start=1):
#         nivel = r.get("nivel", "Medio")
#         fg, bg = nivel_color(nivel)
#         nivel_para = Paragraph(
#             f"<b>{nivel}</b>",
#             st(f"nv{i}", fontSize=7, textColor=fg, fontName="Helvetica-Bold",
#                leading=10, alignment=TA_CENTER)
#         )
#         row = [
#             Paragraph(r.get("id",""), st("rid",fontSize=8,textColor=AZUL_MEDIO,fontName="Helvetica-Bold",leading=11,alignment=TA_CENTER)),
#             Paragraph(r.get("nombre",""), s_cell),
#             Paragraph(r.get("categoria",""), st("cat",fontSize=7,textColor=colors.HexColor("#555"),leading=10)),
#             Paragraph(str(r.get("probabilidad","")), st("pv",fontSize=9,fontName="Helvetica-Bold",leading=12,alignment=TA_CENTER)),
#             Paragraph(str(r.get("impacto","")),      st("iv",fontSize=9,fontName="Helvetica-Bold",leading=12,alignment=TA_CENTER)),
#             Paragraph(f"<b>{r.get('score','')}</b>", st("sv",fontSize=9,fontName="Helvetica-Bold",leading=12,alignment=TA_CENTER)),
#             nivel_para,
#             Paragraph(r.get("accion",""), s_cell),
#         ]
#         table_data.append(row)
#         # Color fondo celda nivel
#         style_cmds.append(("BACKGROUND", (6, i), (6, i), bg))

#     risk_table = Table(table_data, colWidths=col_w, repeatRows=1)
#     risk_table.setStyle(TableStyle(style_cmds))
#     story.append(risk_table)
#     story.append(PageBreak())

#     # ──────────────────────────────────────────────────
#     # PÁGINA 4 — GRÁFICOS
#     # ──────────────────────────────────────────────────
#     story.append(Paragraph("3. Análisis Visual de Riesgos", s_h1))
#     story.append(HRFlowable(width="100%", thickness=1, color=AZUL_MEDIO))
#     story.append(Spacer(1, 0.3*cm))

#     # Matriz de calor
#     story.append(Paragraph("3.1 Matriz de Calor Probabilidad × Impacto", s_h2))
#     heatmap_buf = make_heat_map(riesgos)
#     story.append(Image(heatmap_buf, width=10*cm, height=8.5*cm, hAlign="CENTER"))
#     story.append(Spacer(1, 0.5*cm))

#     # Monte Carlo
#     story.append(Paragraph("3.2 Simulación Monte Carlo — Distribución de Costo Total", s_h2))
#     mc_buf, p50, p80, p90 = make_monte_carlo(data, presupuesto)
#     story.append(Image(mc_buf, width=14*cm, height=7*cm, hAlign="CENTER"))
#     story.append(Spacer(1, 0.4*cm))

#     # Tabla de percentiles
#     perc_data = [
#         [Paragraph("Percentil", st("ph",fontSize=9,textColor=BLANCO,fontName="Helvetica-Bold",leading=12,alignment=TA_CENTER)),
#          Paragraph("Costo estimado",st("ph",fontSize=9,textColor=BLANCO,fontName="Helvetica-Bold",leading=12,alignment=TA_CENTER)),
#          Paragraph("Reserva sobre presupuesto",st("ph",fontSize=9,textColor=BLANCO,fontName="Helvetica-Bold",leading=12,alignment=TA_CENTER)),
#          Paragraph("Interpretación",st("ph",fontSize=9,textColor=BLANCO,fontName="Helvetica-Bold",leading=12,alignment=TA_CENTER))],
#         [Paragraph("<b>P50</b>",st("pc",fontSize=9,textColor=VERDE,fontName="Helvetica-Bold",leading=12,alignment=TA_CENTER)),
#          Paragraph(f"${p50:,.0f}",st("pv",fontSize=9,leading=12,alignment=TA_CENTER)),
#          Paragraph(f"+${p50-presupuesto:,.0f}",st("pv",fontSize=9,leading=12,alignment=TA_CENTER)),
#          Paragraph("Escenario base — 50% de probabilidad",st("pv",fontSize=8,leading=12))],
#         [Paragraph("<b>P80</b>",st("pc",fontSize=9,textColor=NARANJA,fontName="Helvetica-Bold",leading=12,alignment=TA_CENTER)),
#          Paragraph(f"${p80:,.0f}",st("pv",fontSize=9,leading=12,alignment=TA_CENTER)),
#          Paragraph(f"+${p80-presupuesto:,.0f}",st("pv",fontSize=9,leading=12,alignment=TA_CENTER)),
#          Paragraph("Recomendado para reserva de contingencia",st("pv",fontSize=8,leading=12))],
#         [Paragraph("<b>P90</b>",st("pc",fontSize=9,textColor=ROJO,fontName="Helvetica-Bold",leading=12,alignment=TA_CENTER)),
#          Paragraph(f"${p90:,.0f}",st("pv",fontSize=9,leading=12,alignment=TA_CENTER)),
#          Paragraph(f"+${p90-presupuesto:,.0f}",st("pv",fontSize=9,leading=12,alignment=TA_CENTER)),
#          Paragraph("Escenario pesimista — planificación de riesgo máximo",st("pv",fontSize=8,leading=12))],
#     ]
#     perc_table = Table(perc_data, colWidths=[2.5*cm, 3.5*cm, 4.5*cm, 6.5*cm])
#     perc_table.setStyle(TableStyle([
#         ("BACKGROUND",    (0,0), (-1,0), AZUL_OSCURO),
#         ("BACKGROUND",    (0,1), (-1,1), VERDE_CLARO),
#         ("BACKGROUND",    (0,2), (-1,2), NARANJA_CLARO),
#         ("BACKGROUND",    (0,3), (-1,3), ROJO_CLARO),
#         ("LINEBELOW",     (0,0), (-1,-1), 0.3, GRIS_LINEA),
#         ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
#         ("TOPPADDING",    (0,0), (-1,-1), 6),
#         ("BOTTOMPADDING", (0,0), (-1,-1), 6),
#         ("LEFTPADDING",   (0,0), (-1,-1), 6),
#         ("RIGHTPADDING",  (0,0), (-1,-1), 6),
#     ]))
#     story.append(perc_table)

#     doc.build(story)
#     return buf.getvalue()