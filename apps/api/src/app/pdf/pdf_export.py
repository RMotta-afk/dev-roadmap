"""PDF export functionality for roadmap analysis results.

Generates a clean, Portuguese-language PDF roadmap from analysis results
using ReportLab."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from io import BytesIO
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)

logger = logging.getLogger("api.pdf_export")


def parse_full_name(full_name: str) -> str:
    """Parse full name for use in filename.

    Single name becomes just the name. Multiple names become
    FirstName_LastName (first token + last token).
    Extra whitespace is collapsed and replaced with underscores.

    Examples:
        "João Silva" → "João_Silva"
        "Maria" → "Maria"
        "José  da  Silva" → "José_da_Silva"
    """
    if not full_name or not full_name.strip():
        return "Usuario"
    parts = full_name.strip().split()
    if len(parts) == 1:
        return parts[0]
    return "_".join(parts)


def _translate_level(level: str) -> str:
    """Translate level labels to Portuguese."""
    translations: dict[str, str] = {
        "junior": "Júnior",
        "mid": "Pleno",
        "senior": "Sênior",
        "staff": "Especialista",
        "unknown": "Desconhecido",
    }
    return translations.get(level.lower().strip(), level)


def _stars(importance: int) -> str:
    """Convert importance score (0-20 per node) to star display."""
    pct = min(100, max(0, importance))
    filled = (pct + 19) // 20
    filled = max(0, min(5, filled))
    return "★" * filled + "☆" * (5 - filled)


_LEVEL_LABELS_PT = {
    "junior": "Júnior",
    "mid": "Pleno",
    "senior": "Sênior",
    "staff": "Especialista",
}


def build_pdf(
    result: dict[str, Any],
    user_name: str,
) -> bytes:
    """Generate a Portuguese PDF roadmap from analysis result data.

    Args:
        result: The analysis result dict from the database.
        user_name: The user's full name for the document header.

    Returns:
        PDF file content as bytes.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "PTitle",
        parent=styles["Title"],
        fontSize=18,
        leading=22,
        spaceAfter=4,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#1a1a2e"),
    )

    subtitle_style = ParagraphStyle(
        "PSub",
        parent=styles["Normal"],
        fontSize=10,
        leading=13,
        spaceAfter=2,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#555555"),
    )

    h2_style = ParagraphStyle(
        "PH2",
        parent=styles["Heading2"],
        fontSize=13,
        leading=16,
        spaceBefore=14,
        spaceAfter=6,
        textColor=colors.HexColor("#1a1a2e"),
    )

    h3_style = ParagraphStyle(
        "PH3",
        parent=styles["Heading3"],
        fontSize=11,
        leading=14,
        spaceBefore=10,
        spaceAfter=4,
        textColor=colors.HexColor("#333333"),
    )

    body_style = ParagraphStyle(
        "PBody",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        spaceAfter=4,
        alignment=TA_JUSTIFY,
    )

    bullet_style = ParagraphStyle(
        "PBullet",
        parent=body_style,
        leftIndent=12,
        bulletIndent=0,
        spaceBefore=1,
        spaceAfter=1,
    )

    node_name_style = ParagraphStyle(
        "PNodeName",
        parent=styles["Normal"],
        fontSize=11,
        leading=14,
        spaceAfter=1,
    )

    node_meta_style = ParagraphStyle(
        "PNodeMeta",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#666666"),
    )

    node_desc_style = ParagraphStyle(
        "PNodeDesc",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        spaceAfter=4,
        leftIndent=6,
    )

    story: list[Any] = []

    today = datetime.now(UTC).strftime("%d/%m/%Y")

    story.append(Paragraph("ROADMAP DE DESENVOLVIMENTO DE CARREIRA", title_style))
    story.append(Paragraph(f"{user_name}", subtitle_style))
    story.append(Paragraph(f"Gerado em: {today}", subtitle_style))
    story.append(Spacer(1, 6 * mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cccccc")))
    story.append(Spacer(1, 4 * mm))

    level_resume = result.get("level_resume") or {}
    if isinstance(level_resume, dict):
        story.append(Paragraph("Avaliação de Nível", h2_style))

        est_level = level_resume.get("estimated_level", "Desconhecido")
        est_level_pt = _LEVEL_LABELS_PT.get(str(est_level).lower().strip(), str(est_level))
        story.append(Paragraph(f"<b>Nível estimado:</b> {est_level_pt}", body_style))

        score = result.get("compatibility_score", 0)
        try:
            score_int = int(score)
        except (TypeError, ValueError):
            score_int = 0
        score_clamped = max(0, min(100, score_int))
        story.append(Paragraph(f"<b>Pontuação de compatibilidade:</b> {score_clamped} / 100", body_style))
        story.append(Spacer(1, 2 * mm))

        summary = level_resume.get("summary", "")
        if summary:
            story.append(Paragraph("<b>Resumo</b>", h3_style))
            story.append(Paragraph(summary, body_style))

        strong_points = level_resume.get("strong_points", [])
        if strong_points:
            story.append(Paragraph("<b>Pontos fortes</b>", h3_style))
            for pt in strong_points:
                story.append(Paragraph(f"• {pt}", bullet_style))

        weak_points = level_resume.get("weak_points", [])
        if weak_points:
            story.append(Paragraph("<b>Áreas para desenvolvimento</b>", h3_style))
            for pt in weak_points:
                story.append(Paragraph(f"• {pt}", bullet_style))
    else:
        est_level = result.get("level_estimate", "unknown")
        story.append(Paragraph("Avaliação de Nível", h2_style))
        story.append(Paragraph(f"Nível estimado: {_translate_level(str(est_level))}", body_style))

    story.append(Spacer(1, 4 * mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cccccc")))
    story.append(Spacer(1, 4 * mm))

    roadmap = result.get("personalized_roadmap", [])
    if isinstance(roadmap, list) and roadmap:
        story.append(Paragraph(f"Roadmap Personalizado ({len(roadmap)} objetivos de aprendizado)", h2_style))
        story.append(Spacer(1, 2 * mm))

        for idx, node in enumerate(roadmap, start=1):
            if not isinstance(node, dict):
                continue
            node_name = node.get("name", f"Objetivo {idx}")
            node_cat = node.get("category", "—")
            node_level = node.get("level", "—")
            node_level_pt = _LEVEL_LABELS_PT.get(str(node_level).lower().strip(), str(node_level))
            node_importance = node.get("importance", 0)
            try:
                node_imp_int = int(node_importance)
            except (TypeError, ValueError):
                node_imp_int = 0
            node_imp_str = _stars(node_imp_int)
            node_desc = node.get("description", "Sem descrição disponível.")

            story.append(Paragraph(f"<b>{idx}. {node_name}</b>", node_name_style))

            meta_parts = []
            if node_cat:
                meta_parts.append(f"Categoria: {node_cat}")
            if node_level_pt:
                meta_parts.append(f"Nível: {node_level_pt}")
            meta_parts.append(f"Importância: {node_imp_str}")
            story.append(Paragraph(" · ".join(meta_parts), node_meta_style))

            if node_desc and node_desc != "Sem descrição disponível.":
                story.append(Paragraph(node_desc, node_desc_style))

            story.append(Spacer(1, 2 * mm))

    errors = result.get("errors", [])
    if isinstance(errors, list) and errors:
        story.append(Spacer(1, 4 * mm))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cccccc")))
        story.append(Spacer(1, 4 * mm))
        story.append(Paragraph("<b>Avisos do pipeline</b>", h2_style))
        for err in errors:
            story.append(Paragraph(f"• {err}", bullet_style))

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes