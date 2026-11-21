# -*- coding: utf-8 -*-
"""Generate the honest self-training / pseudo-mask results PDF."""
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

NAVY = colors.HexColor("#0E2A47")
GOLD = colors.HexColor("#B8862B")
LIGHT = colors.HexColor("#EEF3F8")
GREY = colors.HexColor("#5A6570")

ss = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=ss["Heading1"], fontSize=15, textColor=NAVY, spaceAfter=8)
H2 = ParagraphStyle("H2", parent=ss["Heading2"], fontSize=11.5, textColor=NAVY, spaceBefore=10, spaceAfter=5)
BODY = ParagraphStyle("BODY", parent=ss["BodyText"], fontSize=9.2, leading=13, spaceAfter=5)
SMALL = ParagraphStyle("SMALL", parent=BODY, fontSize=8, textColor=GREY)
CALLOUT = ParagraphStyle("CALLOUT", parent=BODY, backColor=LIGHT, borderColor=GOLD,
                         borderWidth=0.8, borderPadding=6, leftIndent=3, rightIndent=3)

OUT_DIRS = [
    Path(r"C:\New folder\Documentations"),
    Path(r"C:\Users\upend\AI-Based-illegal-Sand-Mining-Detection-and-Risk-Priortization\docs\documentation_pdfs"),
]
NAME = "10_Self_Training_Results.pdf"

story = [
    Paragraph("Self-Training / Pseudo-Mask Results (Option B)", H1),
    Paragraph("Honest record of applying the trained LMS-Net folds to all 252 chips", SMALL),
    Paragraph("1. What was run", H2),
    Paragraph(
        "Command: <b>python -u models/self_train_masks.py "
        "&lt;segmentation_runs\\20261122_044039&gt; 0.7</b>. "
        "The three LMS-Net fold checkpoints (best epoch per fold, selected on held-out transects) were averaged "
        "per chip. A pixel was written as 255 only when the mean probability was at least 0.70. "
        "Two setup faults were fixed first: the launcher's quoting of a path with spaces, and a mean/std "
        "broadcast shape (saved as 1x14x1x1, reshaped to 14x1x1 for single-chip inference).", BODY),
    Paragraph("2. Measured output", H2),
    Table([
        ["Chips processed", "252 (42 x 6 quarters)"],
        ["Mask files written", "252"],
        ["Empty pseudo-masks", "224 (88.9%)"],
        ["Non-empty pseudo-masks", "28 (11.1%)"],
        ["Positive fraction: median / max", "0.0000 / 0.0137"],
        ["Mean confidence: median / max", "0.0085 / 0.1022"],
        ["Highest-confidence chips", "T019_2023_Q1, T020_2023_Q1, T015_2023_Q1"],
    ], colWidths=[70 * mm, 100 * mm], style=TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ])),
    Paragraph("3. Interpretation (no inflated claims)", H2),
    Paragraph(
        "The output is consistent with the held-out result: LMS-Net reached IoU 0.0059, and no chip produced a "
        "mean probability above 0.11. At threshold 0.70 almost every pseudo-mask is therefore empty, and the 28 "
        "non-empty ones cover at most 1.37% of a chip. These files are <b>pseudo-masks only</b>: they are not human "
        "ground truth, they have no measured accuracy, and they are too sparse to support defensible risk ranking.",
        CALLOUT),
    Paragraph("4. Consequence and next step", H2),
    Paragraph(
        "Option B is complete as an engineering demonstration of the full pipeline: checkpoints load, all 252 "
        "chips are inferred, confidence-scored masks and a summary CSV are written. It does <b>not</b> solve the "
        "detection problem. The recommended next step is to improve the 28 human masks (only 12 currently contain "
        "paint, 0.2-3.1% positive pixels) and retrain, then repeat self-training. Lowering the threshold would "
        "manufacture more painted pixels without adding evidence, so it is not presented as a fix.", BODY),
    Paragraph(
        "Evidence: C:\\New folder\\segmentation_runs\\20261122_044039\\auto_mask_summary.csv, "
        "self_train_note.txt and auto_masks\\ (252 PNG files).", SMALL),
]

from copy import deepcopy

for d in OUT_DIRS:
    d.mkdir(parents=True, exist_ok=True)
    SimpleDocTemplate(str(d / NAME), pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
                      topMargin=16 * mm, bottomMargin=16 * mm,
                      title="Self-Training Results", author="Group 162 - IT").build(deepcopy(story))
    print("PDF:", d / NAME)
