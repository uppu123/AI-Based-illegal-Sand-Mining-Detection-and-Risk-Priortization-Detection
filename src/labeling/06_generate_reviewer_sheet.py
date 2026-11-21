# -*- coding: utf-8 -*-
"""Phase B: build a self-contained human label-review package from the FIXED chips.

Reads only from ``chips_fixed`` and the historical candidate manifest, and writes
everything into a NEW folder (default: C:\\New folder\\label_review).

Outputs
-------
reviewer_sheet.csv   one row per chip: candidate + measured index statistics
Label_Review_Sheet.pdf   print-friendly contact sheet (truecolour | NDSI per chip)
previews/            copies of the truecolour + NDSI PNGs used in the PDF
"""
from __future__ import annotations

import argparse
import csv
import shutil
import sys
from pathlib import Path

import numpy as np
import rasterio
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (Image, PageBreak, Paragraph, SimpleDocTemplate,
                                Spacer, Table, TableStyle)

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from config import project_config as cfg  # noqa: E402

FIXED_Q2 = Path(r"C:\New folder\chips_fixed\2023_Q2")
OLD_MANIFEST = Path(r"C:\New folder\yamuna_work\labeling\label_manifest.csv")
DEFAULT_OUT = Path(r"C:\New folder\label_review")

NAVY = colors.HexColor("#0E2A47")
GOLD = colors.HexColor("#E8A838")
LIGHT = colors.HexColor("#EEF3F8")
GREY = colors.HexColor("#5A6570")

INDEX_BANDS = {"NDVI": 11, "NDWI": 12, "NDBI": 13, "NDSI": 14}


def old_to_new(chip_id: str) -> str:
    """T004_2023Q2 -> T004_2023_Q2."""
    return chip_id.replace("_2023Q2", "_2023_Q2")


def chip_stats(tif: Path) -> dict:
    with rasterio.open(tif) as src:
        arr = {name: src.read(b).astype(np.float64) / 5000.0 - 1.0
               for name, b in INDEX_BANDS.items()}
    valid = np.isfinite(arr["NDSI"]) & (arr["NDSI"] > -1.5)
    out = {}
    for name, a in arr.items():
        out["mean_" + name] = round(float(np.mean(a[valid])), 4) if valid.any() else ""
    # Bare sediment signature: low NDSI (water-positive convention) and low NDVI.
    sand = (arr["NDSI"] < -0.1) & (arr["NDVI"] < 0.3)
    out["sand_frac"] = round(float(np.mean(sand[valid])), 4) if valid.any() else ""
    return out


def load_candidates(path: Path) -> dict[str, str]:
    candidates = {}
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            candidates[old_to_new(row["chip_id"].strip())] = row.get("label_A", "").strip()
    return candidates


def build_csv(rows: list[dict], out: Path) -> None:
    cols = ["chip_id", "transect_id", "candidate_label_AUTO_ONLY",
            "mean_NDVI", "mean_NDWI", "mean_NDBI", "mean_NDSI", "sand_frac",
            "reviewer_final_label", "reviewer_initials", "notes"]
    with (out / "reviewer_sheet.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in cols})


def build_pdf(rows: list[dict], out: Path) -> None:
    ss = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", parent=ss["Heading1"], fontName="Helvetica-Bold",
                        fontSize=16, textColor=NAVY, spaceAfter=6)
    h2 = ParagraphStyle("h2", parent=ss["Heading2"], fontName="Helvetica-Bold",
                        fontSize=11, textColor=GOLD, spaceBefore=8, spaceAfter=4)
    body = ParagraphStyle("body", parent=ss["BodyText"], fontName="Helvetica",
                          fontSize=8.6, leading=11.5, alignment=TA_LEFT)
    small = ParagraphStyle("small", parent=body, fontSize=7.4, leading=9.2, spaceAfter=0)

    story = [Paragraph("Label Review Sheet - Sentinel-2 2023 Q2 (REBUILT CHIPS)", h1)]
    story.append(Paragraph(
        "42 candidate labels, computed from spectral indices, are <b>NOT ground truth</b>. "
        "For each chip: view the true-colour and NDSI panels, then write MINING / NOT MINING / "
        "UNSURE in the last column. Use UNSURE rather than guessing. Sand is dark/blue-to-red "
        "in NDSI under the (B3-B11) convention used here; active mining needs visible extraction "
        "signatures (bare sediment bars, pits, spoil heaps, tracks, barges), not sand alone.", body))
    story.append(Paragraph(
        "Truecolour and NDSI previews were generated from the FIXED composites (correct B8 "
        "band order). The candidate column is carried over from the earlier pass and must be "
        "confirmed or corrected.", body))
    story.append(Spacer(1, 6))

    per_page = 6
    for i in range(0, len(rows), per_page):
        page = rows[i:i + per_page]
        data = []
        for r in page:
            tc = out / "previews" / f"{r['chip_id']}_truecolour.png"
            nd = out / "previews" / f"{r['chip_id']}_NDSI.png"
            img_cell = ""
            if tc.exists() and nd.exists():
                img_cell = ('<table><tr><td><img src="%s" width="118" height="118"/></td>'
                            '<td><img src="%s" width="118" height="118"/></td></tr></table>'
                            % (tc.as_posix(), nd.as_posix()))
            stats = ("NDVI {mean_NDVI} | NDSI {mean_NDSI}<br/>"
                     "sand {sand_frac} | cand <b>{candidate_label_AUTO_ONLY}</b>").format(**r)
            data.append([
                Paragraph(f"<b>{r['chip_id']}</b>", small),
                Paragraph(img_cell, small),
                Paragraph(stats, small),
                "____________",
            ])
        t = Table(data, colWidths=[26 * mm, 66 * mm, 55 * mm, 27 * mm], repeatRows=0)
        t.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#C9D3DD")),
            ("BACKGROUND", (0, 0), (0, -1), LIGHT),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(t)
        if i + per_page < len(rows):
            story.append(PageBreak())

    doc = SimpleDocTemplate(
        str(out / "Label_Review_Sheet.pdf"), pagesize=A4,
        leftMargin=15 * mm, rightMargin=15 * mm, topMargin=15 * mm, bottomMargin=15 * mm,
        title="Label Review Sheet - Yamuna 2023 Q2", author="Group 162 - IT",
    )

    def decor(canvas, d):
        canvas.saveState()
        w, h = A4
        canvas.setFillColor(NAVY)
        canvas.rect(0, h - 11 * mm, w, 11 * mm, stroke=0, fill=1)
        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica-Bold", 8.5)
        canvas.drawString(15 * mm, h - 7.5 * mm, "GROUP 162  |  LABEL REVIEW - REBUILT CHIPS")
        canvas.setFillColor(GREY)
        canvas.setFont("Helvetica", 8)
        canvas.drawRightString(w - 15 * mm, 9 * mm, "Page %d" % d.page)
        canvas.restoreState()

    doc.build(story, onFirstPage=decor, onLaterPages=decor)


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate the human label-review package")
    ap.add_argument("--chips-dir", type=Path, default=FIXED_Q2)
    ap.add_argument("--candidate-csv", type=Path, default=OLD_MANIFEST)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()

    out = args.out
    (out / "previews").mkdir(parents=True, exist_ok=True)

    candidates = load_candidates(args.candidate_csv)

    rows = []
    tifs = sorted(args.chips_dir.glob("T*_2023_Q2.tif"))
    print(f"chips found: {len(tifs)}")
    for tif in tifs:
        chip_id = tif.stem
        tid = chip_id.split("_")[0]
        for suffix in ("truecolour", "NDSI"):
            src = args.chips_dir / "previews" / f"{chip_id}_{suffix}.png"
            if src.exists():
                shutil.copy2(src, out / "previews" / src.name)
        row = {
            "chip_id": chip_id,
            "transect_id": tid,
            "candidate_label_AUTO_ONLY": candidates.get(chip_id, "(missing)"),
        }
        row.update(chip_stats(tif))
        rows.append(row)

    build_csv(rows, out)
    build_pdf(rows, out)
    from collections import Counter
    print("candidate counts:", dict(Counter(r["candidate_label_AUTO_ONLY"] for r in rows)))
    print("written:", out / "reviewer_sheet.csv")
    print("written:", out / "Label_Review_Sheet.pdf")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
