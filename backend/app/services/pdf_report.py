"""Professional PDF report generation (ReportLab)."""

from __future__ import annotations

import io
from datetime import UTC, datetime
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.schemas import AnalyzeResponse


def build_pdf_bytes(result: AnalyzeResponse, title: str = "LogGuard AI — Threat Assessment") -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=letter,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54,
    )
    styles = getSampleStyleSheet()
    h1 = ParagraphStyle(
        name="H1",
        parent=styles["Heading1"],
        textColor=colors.HexColor("#b91c1c"),
        spaceAfter=12,
    )
    h2 = ParagraphStyle(
        name="H2",
        parent=styles["Heading2"],
        textColor=colors.HexColor("#e5e5e5"),
        backColor=colors.HexColor("#171717"),
        borderPadding=6,
        spaceAfter=10,
    )
    body = ParagraphStyle(name="Body", parent=styles["Normal"], fontSize=10, leading=14)

    story: list = []
    story.append(Paragraph(title, h1))
    story.append(
        Paragraph(
            f"Generated (UTC): {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S')} — "
            f"Processing time: {result.processing_time_ms} ms",
            body,
        )
    )
    story.append(Spacer(1, 0.15 * inch))

    sev_color = {
        "critical": "#dc2626",
        "high": "#ea580c",
        "medium": "#ca8a04",
        "low": "#16a34a",
        "info": "#64748b",
    }.get(result.severity, "#64748b")

    story.append(Paragraph("<b>Severity</b>", h2))
    story.append(
        Paragraph(
            f'<font color="{sev_color}"><b>{result.severity.upper()}</b></font> '
            f"(score {result.severity_score}) — Format: <b>{result.format_detected}</b>",
            body,
        )
    )
    story.append(Spacer(1, 0.1 * inch))

    story.append(Paragraph("<b>Executive summary</b>", h2))
    story.append(Paragraph(result.executive_summary.replace("\n", "<br/>"), body))
    story.append(Spacer(1, 0.1 * inch))

    story.append(Paragraph("<b>Risk explanation</b>", h2))
    story.append(Paragraph(result.risk_explanation.replace("\n", "<br/>"), body))
    story.append(Spacer(1, 0.1 * inch))

    story.append(Paragraph("<b>MITRE ATT&amp;CK mapping</b>", h2))
    if result.mitre_techniques:
        mt_data = [["ID", "Name", "Confidence"]]
        for m in result.mitre_techniques:
            mt_data.append([m.id, m.name, f"{m.confidence:.2f}"])
        t = Table(mt_data, colWidths=[1 * inch, 3.6 * inch, 1 * inch])
        t.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#262626")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#404040")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#fafafa"), colors.HexColor("#f4f4f5")]),
                ]
            )
        )
        story.append(t)
    else:
        story.append(Paragraph("No high-confidence technique mapping.", body))
    story.append(Spacer(1, 0.1 * inch))

    story.append(Paragraph("<b>Indicators of Compromise (IOCs)</b>", h2))
    if result.iocs:
        ioc_data = [["Type", "Value", "Context"]]
        for i in result.iocs[:40]:
            ioc_data.append([i.type, i.value[:80], (i.context or "")[:40]])
        ti = Table(ioc_data, colWidths=[0.9 * inch, 3.2 * inch, 1.5 * inch])
        ti.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#262626")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#404040")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#fafafa"), colors.HexColor("#f4f4f5")]),
                ]
            )
        )
        story.append(ti)
    else:
        story.append(Paragraph("No structured IOCs extracted.", body))
    story.append(Spacer(1, 0.1 * inch))

    story.append(Paragraph("<b>Sector playbook</b>", h2))
    story.append(Paragraph(f"Sector: <b>{result.playbook.sector}</b>", body))
    for p in result.playbook.items:
        story.append(Spacer(1, 0.05 * inch))
        story.append(Paragraph(f"<b>{p.title}</b><br/>{p.action}", body))
        if p.sample_query:
            story.append(Paragraph(f"<font face='Courier'>Query:</font> <i>{p.sample_query}</i>", body))

    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph("<b>Detection rule (Sigma)</b>", h2))
    story.append(Paragraph(escape(result.detection_rules.title), body))
    sig_snip = escape(result.detection_rules.sigma_yaml[:2000]).replace("\n", "<br/>")
    story.append(Paragraph(f"<font face='Courier' size='6'>{sig_snip}</font>", body))

    if result.model_notes:
        story.append(Spacer(1, 0.15 * inch))
        story.append(Paragraph("<b>Model / pipeline notes</b>", h2))
        story.append(Paragraph(result.model_notes.replace("\n", "<br/>"), body))

    doc.build(story)
    return buf.getvalue()
