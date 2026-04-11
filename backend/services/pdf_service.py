"""
pdf_service.py — ReportLab PDF generation for CircuitMap Target Validation Reports.

Generates a professionally formatted A4 PDF with all 11 report sections.
"""
import os
from datetime import date
from typing import Optional

SESSIONS_DIR = os.getenv("SESSIONS_DIR", "./sessions")


def generate_pdf(
    session_id: str,
    report_sections: dict,
    target: str,
    indication: str,
    expression_image_path: Optional[str] = None,
    disease_image_path: Optional[str] = None,
    overlap_score: Optional[dict] = None,
) -> str:
    """
    Generate a PDF report and save it to the session directory.

    Args:
        session_id: Session ID (used for output path)
        report_sections: Dict of section_name -> section_text (11 sections)
        target: Gene/target name (e.g. 'SUV39H1')
        indication: Disease indication (e.g. 'Alzheimer's disease')
        expression_image_path: Absolute path to expression map PNG (optional)
        disease_image_path: Absolute path to disease map PNG (optional)
        overlap_score: Dict with r and percentile values (optional)

    Returns:
        Absolute path to generated PDF file
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib.colors import HexColor, black, white, grey
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        HRFlowable, PageBreak
    )
    from reportlab.platypus import Image as RLImage

    output_dir = os.path.join(SESSIONS_DIR, session_id)
    os.makedirs(output_dir, exist_ok=True)

    today = date.today().strftime("%Y-%m-%d")
    safe_indication = indication.replace(" ", "-").replace("'", "")
    filename = f"CircuitMap_{target}_{safe_indication}_{today}.pdf"
    output_path = os.path.join(output_dir, filename)

    # Colors
    BRAND_BLUE = HexColor("#1E40AF")
    LIGHT_GRAY = HexColor("#F3F4F6")
    MED_GRAY = HexColor("#6B7280")
    GREEN = HexColor("#059669")
    AMBER = HexColor("#D97706")
    RED = HexColor("#DC2626")

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2.5 * cm,
        bottomMargin=2.5 * cm,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "Title",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=20,
        textColor=BRAND_BLUE,
        spaceAfter=6,
    )
    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=11,
        textColor=MED_GRAY,
        spaceAfter=4,
    )
    section_header_style = ParagraphStyle(
        "SectionHeader",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        textColor=BRAND_BLUE,
        spaceBefore=16,
        spaceAfter=6,
        borderPad=4,
    )
    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        spaceAfter=4,
    )
    footer_style = ParagraphStyle(
        "Footer",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        textColor=MED_GRAY,
        alignment=1,  # center
    )

    story = []

    # ── HEADER ──────────────────────────────────────────────────────────────
    story.append(Paragraph("CircuitMap", title_style))
    story.append(Paragraph("CNS Drug Target Validation Report", subtitle_style))
    story.append(Paragraph(f"Target: <b>{target}</b> &nbsp;|&nbsp; Indication: <b>{indication}</b> &nbsp;|&nbsp; Date: {today}", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=BRAND_BLUE, spaceAfter=12))

    # ── REPORT SECTIONS ─────────────────────────────────────────────────────
    SECTION_ORDER = [
        ("Executive Summary", ["executive_summary", "Executive Summary"]),
        ("Molecular Target Profile", ["target_identification", "Molecular Target Profile"]),
        ("Brain Expression Analysis", ["expression_analysis", "Brain Expression Analysis"]),
        ("Functional Circuit Context", ["circuit_interpretation", "Functional Circuit Context"]),
        ("Target-Pathology Overlap", ["spatial_overlap", "Target-Pathology Overlap"]),
        ("Off-Target Risk Assessment", ["off_target_risk", "Off-Target Risk Assessment"]),
        ("Literature Evidence Summary", ["literature_context", "Literature Evidence Summary"]),
        ("Recommended Clinical Endpoints", ["recommendations", "Recommended Clinical Endpoints"]),
        ("Confidence Assessment", ["confidence_assessment", "Confidence Assessment"]),
        (
            "Pre-Clinical Validation Recommendations",
            ["preclinical_validation", "Pre-Clinical Validation Recommendations", "references", "References"],
        ),
        ("Data Sources & Limitations", ["limitations", "Data Sources & Limitations"]),
    ]

    for section_name, candidate_keys in SECTION_ORDER:
        section_text = None
        for candidate_key in candidate_keys:
            if candidate_key in report_sections:
                section_text = report_sections[candidate_key]
                break

        if section_text is None:
            # Match legacy keys case-insensitively if needed
            for key, val in report_sections.items():
                if key.lower().strip() in {candidate.lower().strip() for candidate in candidate_keys}:
                    section_text = val
                    break

        if not section_text:
            continue

        story.append(Paragraph(section_name, section_header_style))

        # Embed brain maps after Brain Expression Analysis section
        if section_name == "Brain Expression Analysis":
            img_row = []
            for img_path, label in [
                (expression_image_path, "Target Expression Map"),
                (disease_image_path, "Disease Anatomy Map"),
            ]:
                if img_path and os.path.exists(img_path):
                    try:
                        img = RLImage(img_path, width=8 * cm, height=5 * cm)
                        img_row.append(img)
                    except Exception:
                        img_row.append(Paragraph(f"[{label} unavailable]", body_style))
                else:
                    img_row.append(Paragraph(f"[{label} not generated]", body_style))

            if img_row:
                t = Table([img_row], colWidths=[8.5 * cm, 8.5 * cm])
                t.setStyle(TableStyle([
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ]))
                story.append(t)
                story.append(Spacer(1, 6))

            # Overlap score box
            if overlap_score and "r" in overlap_score:
                r = overlap_score.get("r", 0)
                pct = overlap_score.get("percentile", 0)
                interp = overlap_score.get("interpretation", "moderate")
                color = GREEN if pct >= 75 else (AMBER if pct >= 50 else RED)

                score_data = [
                    ["Target-Pathology Overlap Score"],
                    [f"r = {r:.3f}   |   {pct}th percentile   |   {interp.upper()} alignment"],
                ]
                t_score = Table(score_data, colWidths=[17 * cm])
                t_score.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (0, 0), BRAND_BLUE),
                    ("TEXTCOLOR", (0, 0), (0, 0), white),
                    ("FONTNAME", (0, 0), (0, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (0, 0), 10),
                    ("BACKGROUND", (0, 1), (0, 1), LIGHT_GRAY),
                    ("FONTNAME", (0, 1), (0, 1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 1), (0, 1), 12),
                    ("TEXTCOLOR", (0, 1), (0, 1), color),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("BOX", (0, 0), (-1, -1), 1, MED_GRAY),
                ]))
                story.append(t_score)
                story.append(Spacer(1, 8))

        # Render section text
        for line in section_text.strip().split("\n"):
            line = line.strip()
            if not line:
                story.append(Spacer(1, 4))
                continue
            # Simple markdown-like: lines starting with - or * become bullets
            if line.startswith(("- ", "* ", "• ")):
                line = "&bull; " + line[2:]
            story.append(Paragraph(_escape_xml(line), body_style))

    # ── FOOTER ───────────────────────────────────────────────────────────────
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=1, color=MED_GRAY))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "Generated by CircuitMap — Pre-clinical computational evidence only. Not for clinical use.",
        footer_style
    ))
    story.append(Paragraph(
        f"Data sources: Allen Human Brain Atlas, Neurosynth, ChEMBL | {today}",
        footer_style
    ))

    doc.build(story)
    return os.path.abspath(output_path)


def _escape_xml(text: str) -> str:
    """Escape XML special characters for ReportLab Paragraph."""
    return (
        text
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        # Re-allow our bullet entity
        .replace("&amp;bull;", "&bull;")
    )


if __name__ == "__main__":
    test_sections = {
        "Executive Summary": "This is a test report. SUV39H1 shows strong hippocampal expression. Recommend advancing with monitoring.",
        "Molecular Target Profile": "Target: SUV39H1 | Class: Histone methyltransferase | Ki: 0.8 µM | Source: ChEMBL",
        "Brain Expression Analysis": "Top regions: hippocampus (98th pct), entorhinal cortex (94th pct), prefrontal cortex (88th pct)",
        "Functional Circuit Context": "The high-expression regions are strongly associated with episodic memory, spatial navigation, and memory consolidation.",
        "Target-Pathology Overlap": "r = 0.61 | 89th percentile | Strong alignment",
        "Off-Target Risk Assessment": "- Cerebellum: 42nd pct | Motor coordination | LOW risk",
        "Literature Evidence Summary": "- Smith et al., 2023, Nature Neuroscience: SUV39H1 regulates BDNF in hippocampus.",
        "Recommended Clinical Endpoints": "- CANTAB paired-associate learning task\n- ADNI hippocampal volume MRI",
        "Confidence Assessment": "Target resolution: HIGH | Circuit alignment: MODERATE | Literature support: HIGH",
        "Pre-Clinical Validation Recommendations": "1. Measure H3K9me3 in post-mortem AD hippocampal tissue.\n2. Run SUV39H1 KO mouse Morris water maze.",
        "Data Sources & Limitations": "AHBA (2012), Neurosynth (2011), ChEMBL (2019). Limitation: AHBA uses post-mortem healthy tissue.",
    }

    pdf_path = generate_pdf(
        session_id="test_pdf_session",
        report_sections=test_sections,
        target="SUV39H1",
        indication="Alzheimer's disease",
        overlap_score={"r": 0.61, "percentile": 89, "interpretation": "strong"}
    )
    print(f"PDF generated: {pdf_path}")
    assert os.path.exists(pdf_path), f"PDF not found at {pdf_path}"
    print("pdf_service TEST PASSED")
