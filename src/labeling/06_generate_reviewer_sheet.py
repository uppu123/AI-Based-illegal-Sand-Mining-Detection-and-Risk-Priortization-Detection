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


def build_csv(rows: list[dict], out: Path,
              filename: str = "reviewer_sheet.csv") -> None:
    cols = ["chip_id", "quarter", "transect_id", "candidate_label_AUTO_ONLY",
            "mean_NDVI", "mean_NDWI", "mean_NDBI", "mean_NDSI", "sand_frac",
            "water_frac", "cmi_mean", "distance_mean_m", "distance_min_m",
            "reviewer_final_label", "reviewer_initials", "notes"]
    with (out / filename).open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in cols})


def build_pdf(rows: list[dict], out: Path, quarter: str = "2023_Q2") -> None:
    """Print-ready contact sheet.

    Uses real Image flowables in fixed-width columns instead of <img> tags inside
    a Paragraph. The earlier version overflowed two 118 pt images into a 66 mm
    cell, which made the pictures overlap the statistics column.
    """
    ss = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", parent=ss["Heading1"], fontName="Helvetica-Bold",
                        fontSize=15, textColor=NAVY, spaceAfter=5)
    body = ParagraphStyle("body", parent=ss["BodyText"], fontName="Helvetica",
                          fontSize=8.2, leading=12.0, alignment=TA_LEFT)
    small = ParagraphStyle("small", parent=body, fontSize=7.4, leading=10.5, spaceAfter=0)
    tiny = ParagraphStyle("tiny", parent=body, fontSize=6.6, leading=9.0,
                          textColor=GREY, spaceAfter=0)
    th = ParagraphStyle("th", parent=small, fontName="Helvetica-Bold",
                        textColor=colors.white)

    story = [Paragraph(f"Label Review Sheet - Sentinel-2 {quarter} (REBUILT CHIPS)", h1)]
    story.append(Paragraph(
        "Any candidate label shown is <b>auto-generated, NOT ground truth</b>. For each chip, "
        "view both panels and write your decision in the last column. In the NDSI panel, bare "
        "sand trends blue and open water trends red. Mining requires visible extraction "
        "signatures (bare bars, pits, spoil heaps, tracks, barges) - sand alone is not enough. "
        "Use UNSURE rather than guessing.", body))
    story.append(Paragraph(
        "Features: <b>sand</b> = bare-sediment fraction (NDSI&lt;-0.1 and NDVI&lt;0.3); "
        "<b>water</b> = fraction above the scene water threshold; <b>CMI</b> = "
        "(B11-B12)/(B11+B12), the Coal Mine Index of Mukherjee et al. used here as a "
        "bare-exposure ratio; <b>dist</b> = metres from the river centreline. Candidates are "
        "carried over from the earlier Q2 pass only.", body))
    story.append(Spacer(1, 4))

    col_w = [22 * mm, 34 * mm, 34 * mm, 58 * mm, 30 * mm]  # 178 mm < 180 mm available
    img_w = img_h = 30 * mm
    per_page = 5

    for i in range(0, len(rows), per_page):
        page = rows[i:i + per_page]
        data = [[Paragraph(t, th) for t in
                 ("CHIP", "TRUE COLOUR", "NDSI", "MEASURED / CANDIDATE", "YOUR LABEL")]]
        for r in page:
            cells = []
            for suffix in ("truecolour", "NDSI"):
                p = out / "previews" / f"{r['chip_id']}_{suffix}.png"
                cells.append(Image(str(p), width=img_w, height=img_h)
                             if p.exists() else Paragraph("missing", tiny))
            stats = (
                "<b>NDVI</b> {mean_NDVI} &nbsp; <b>NDSI</b> {mean_NDSI}<br/>"
                "<b>sand</b> {sand_frac} &nbsp; <b>cand</b> {candidate_label_AUTO_ONLY}<br/>"
                "<b>water</b> {water_frac} &nbsp; <b>CMI</b> {cmi_mean}<br/>"
                "<b>dist</b> {distance_mean_m} m &nbsp; (min {distance_min_m} m)"
            ).format(**r)
            write_in = Paragraph("MINING / NOT / UNSURE<br/>&nbsp;<br/>&nbsp;", small)
            data.append([
                Paragraph(f"<b>{r['chip_id']}</b>", small),
                cells[0],
                cells[1],
                Paragraph(stats, small),
                write_in,
            ])

        t = Table(data, colWidths=col_w, repeatRows=1, hAlign="LEFT")
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), NAVY),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#C9D3DD")),
            ("BACKGROUND", (0, 1), (0, -1), LIGHT),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 3),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
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


QUARTERS = ("2023_Q1", "2023_Q2", "2023_Q3", "2023_Q4", "2024_Q1", "2024_Q2")
CHIPS_ROOT = Path(r"C:\New folder\chips_fixed")
FEATURES_CSV = Path(r"C:\New folder\extra_features\chip_features.csv")


def load_features(path: Path) -> dict[str, dict]:
    import csv as _csv
    if not path.exists():
        return {}
    with path.open(newline="", encoding="utf-8-sig") as f:
        return {r["chip_id"]: r for r in _csv.DictReader(f)}


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate the human label-review package")
    ap.add_argument("--out-root", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--candidate-csv", type=Path, default=OLD_MANIFEST)
    ap.add_argument("--features-csv", type=Path, default=FEATURES_CSV)
    ap.add_argument("--all-quarters", action="store_true",
                    help="build a sheet for each of the 6 quarters (default: Q2 only)")
    args = ap.parse_args()

    candidates = load_candidates(args.candidate_csv)
    features = load_features(args.features_csv)
    quarters = QUARTERS if args.all_quarters else ("2023_Q2",)

    master = []
    for q in quarters:
        chips_dir = CHIPS_ROOT / q
        out = args.out_root / q
        (out / "previews").mkdir(parents=True, exist_ok=True)
        tifs = sorted(chips_dir.glob(f"T*_{q}.tif"))
        print(f"\n=== {q}: {len(tifs)} chips ===")
        rows = []
        for tif in tifs:
            chip_id = tif.stem
            for suffix in ("truecolour", "NDSI"):
                src = chips_dir / "previews" / f"{chip_id}_{suffix}.png"
                if src.exists():
                    shutil.copy2(src, out / "previews" / src.name)
            row = {
                "chip_id": chip_id,
                "quarter": q,
                "transect_id": chip_id.split("_")[0],
                "candidate_label_AUTO_ONLY": candidates.get(chip_id, ""),
            }
            row.update(chip_stats(tif))
            f = features.get(chip_id, {})
            for k in ("water_frac", "cmi_mean", "distance_mean_m", "distance_min_m"):
                row[k] = f.get(k, "")
            rows.append(row)
        master.extend(rows)
        build_csv(rows, out)
        build_pdf(rows, out, q)
        print("  written:", out / "reviewer_sheet.csv")
        print("  written:", out / "Label_Review_Sheet.pdf")

    # Master CSV across all quarters (one row per chip/scene).
    build_csv(master, args.out_root, "all_chips_review.csv")
    print(f"\nTOTAL chip rows: {len(master)}")
    print("written:", args.out_root / "all_chips_review.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
