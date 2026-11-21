# -*- coding: utf-8 -*-
r"""Generate the full documentation pack as PDFs in docs/documentation_pdfs."""
import io, os, re
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
                                PageBreak, KeepTogether)

from pathlib import Path as _Path
_REPO = _Path(__file__).resolve().parents[1]

OUT = str(_REPO / "docs" / "documentation_pdfs")
os.makedirs(OUT, exist_ok=True)

NAVY = colors.HexColor("#0E2A47")
GOLD = colors.HexColor("#B8862B")
LIGHT = colors.HexColor("#EEF3F8")
CREAM = colors.HexColor("#FDF6E6")
GREY = colors.HexColor("#5A6570")
WHITE = colors.white

REPL = {
    "\u2192": "->", "\u2190": "<-", "\u2013": "-", "\u2014": "-", "\u2212": "-",
    "\u00d7": "x", "\u2265": ">=", "\u2264": "<=", "\u03ba": "kappa",
    "\u2713": "PASS", "\u2717": "FAIL", "\u26a0": "!", "\u2022": "-",
    "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
    "\u00b1": "+/-", "\u00b0": "deg", "\u2103": "C", "\u2026": "...",
}


def safe(s):
    s = str(s)
    for k, v in REPL.items():
        s = s.replace(k, v)
    return s.encode("ascii", "replace").decode("ascii")


ss = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=ss["Heading1"], fontName="Helvetica-Bold",
                    fontSize=15, leading=19, textColor=NAVY, spaceBefore=12, spaceAfter=7)
H2 = ParagraphStyle("H2", parent=ss["Heading2"], fontName="Helvetica-Bold",
                    fontSize=11.5, leading=15.5, textColor=GOLD, spaceBefore=10, spaceAfter=5)
BODY = ParagraphStyle("BODY", parent=ss["BodyText"], fontName="Helvetica",
                      fontSize=9, leading=13.0, spaceAfter=5, alignment=TA_LEFT)
SMALL = ParagraphStyle("SMALL", parent=BODY, fontSize=7.6, leading=11.2, spaceAfter=0)
SMALLB = ParagraphStyle("SMALLB", parent=SMALL, fontName="Helvetica-Bold")
TITLE = ParagraphStyle("TITLE", parent=ss["Title"], fontName="Helvetica-Bold",
                       fontSize=20, leading=25, textColor=NAVY, spaceAfter=4, alignment=TA_LEFT)
SUB = ParagraphStyle("SUB", parent=BODY, fontSize=10.5, leading=14.2, textColor=GREY, spaceAfter=12)
CALLOUT = ParagraphStyle("CALLOUT", parent=BODY, fontSize=8.6, leading=12.4,
                         textColor=NAVY, backColor=CREAM, borderPadding=6,
                         leftIndent=4, rightIndent=4, spaceBefore=6, spaceAfter=8)


def P(t, st=BODY):
    return Paragraph(safe(t), st)


def bullets(items):
    text = "<br/>".join("&bull;&nbsp; " + safe(it) for it in items)
    return Paragraph(text, BODY)


def tbl(headers, rows, widths=None, font=7.6):
    data = [[Paragraph("<b>%s</b>" % safe(h), ParagraphStyle("th", parent=SMALL,
             textColor=WHITE, fontName="Helvetica-Bold", fontSize=font,
             leading=font + 3.6)) for h in headers]]
    for r in rows:
        data.append([Paragraph(safe(c), ParagraphStyle("td", parent=SMALL,
                     fontSize=font, leading=font + 3.6)) for c in r])
    t = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#C9D3DD")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT]),
    ]
    t.setStyle(TableStyle(style))
    return t


def page_decor(canvas, doc):
    canvas.saveState()
    w, h = A4
    canvas.setFillColor(NAVY)
    canvas.rect(0, h - 13 * mm, w, 13 * mm, stroke=0, fill=1)
    canvas.setFillColor(WHITE)
    canvas.setFont("Helvetica-Bold", 8)
    canvas.drawString(14 * mm, h - 8.6 * mm, "YAMUNA SAND MINING DETECTION  |  GROUP 162  |  PROJECT DOCUMENTATION")
    canvas.setFillColor(GOLD)
    canvas.rect(0, h - 13.8 * mm, w, 0.8 * mm, stroke=0, fill=1)
    canvas.setFillColor(GREY)
    canvas.setFont("Helvetica", 7.5)
    canvas.drawString(14 * mm, 9 * mm, "Generated 2026-11-21  |  C:\\New folder\\Documentations")
    canvas.drawRightString(w - 14 * mm, 9 * mm, "Page %d" % doc.page)
    canvas.restoreState()


def build(fname, title, subtitle, story):
    path = os.path.join(OUT, fname)
    doc = SimpleDocTemplate(path, pagesize=A4,
                            leftMargin=14 * mm, rightMargin=14 * mm,
                            topMargin=19 * mm, bottomMargin=15 * mm,
                            title=safe(title), author="Group 162")
    full = [P(title, TITLE), P(subtitle, SUB)] + story
    doc.build(full, onFirstPage=page_decor, onLaterPages=page_decor)
    print("PDF:", fname, "|", os.path.getsize(path) // 1024, "KB")
    return path


# ============================================================ 00 INDEX
build("00_Documentation_Index.pdf", "Documentation Index",
      "Complete documentation pack - read this first", [
    P("1. What this pack contains", H1),
    tbl(["File", "Contents", "Use it when"], [
        ["01_Work_Completed_To_Date.pdf", "Full table of everything done so far, with evidence files and dates", "You need to tell the panel what you did"],
        ["02_Data_and_Sensors.pdf", "Satellites, scene counts, all 14 bands, products, chips, band-order defect", "Someone asks 'what is your data?'"],
        ["03_Pipeline_Scripts.pdf", "Every script: what it does, real filename, command, output, execution order", "Someone asks 'which file does what?'"],
        ["04_Models_and_Justification.pdf", "The 4 models, which one is used where and why, metrics, risk factors", "Someone asks 'what models and why?'"],
        ["05_Literature_and_Reasons.pdf", "The 5 core papers (incl. Mukherjee CMI), why each was chosen, what was taken and rejected", "Someone asks 'why this paper?'"],
        ["06_Remaining_Steps.pdf", "Every remaining step, owner, estimate, and the 3 hard gates", "Before we start execution"],
        ["07_Phase_A_Data_Repair_Report.pdf", "Band-order fix, 11 rebuilt composites, 252 clean chips, all checks PASS", "Someone asks 'is the data fixed?'"],
        ["08_Extra_Features_and_Thresholds.pdf", "Water fraction, CMI, river distance, and the Otsu threshold decision", "Someone asks about the extra labeling features"],
        ["09_Annotation_Guide_for_Mining_Masks.pdf", "NDSI rules, water overlay, dry-chip rule, extraction signatures, workflow, common mistakes", "While drawing the 28 human pixel masks (Option B)"],
    ], [58 * mm, 78 * mm, 46 * mm]),
    Spacer(1, 10),
    P("2. Current status", H1),
    tbl(["Item", "Value"], [
        ["Title", "AI-Based Illegal Sand Mining Detection and Risk Prioritization System on Yamuna River"],
        ["Group / Dept", "162 / Information Technology, DTU"],
        ["Team", "Upendra Kumar (23/IT/165), Somya Tripathi (23/IT/162)"],
        ["Supervisor", "Dr. Anita Thakur"],
        ["Progress claimed on slide 2", "55% (data engineering + labeling set complete)"],
        ["Models / dashboard", "Not started"],
        ["Data status", "Band-order defect fixed in code AND rebuilt into NEW folders; originals byte-identical"],
    ], [55 * mm, 127 * mm]),
    Spacer(1, 8),
    P("3. Ground rules for the remaining work", H1),
    bullets([
        "Nothing under C:\\New folder\\yamuna_data or C:\\New folder\\yamuna_work\\chips will be modified. All rebuilt data goes to new folders.",
        "Three things require you: draw 28 human pixel masks, approve the AHP weights, freeze the dashboard MVP scope.",
        "A10 verification and B7 label sign-off are DONE. Two hard gates remain: 28/28 masks signed off, risk ranking validated (C15).",
        "No metric or result will be fabricated. If something is not measured, it will say 'not measured'.",
    ]),
])

# ============================================================ 01 WORK COMPLETED
done_rows = [
    ["1", "Synopsis and problem definition", "2026-09", "Project_Synopsis_Final.docx / .pdf; synopsis .md", "Problem, objectives, 5 references, methodology written"],
    ["2", "Literature review", "2026-09/10", "Synopsis references + slide 2", "20+ papers scanned; 5 core selected: LMS-Net, Sutlej morphometry, AHP+ML, JIIT Noida indices, Mukherjee CMI"],
    ["3", "Download pipeline written", "2026-10", "C:\\New folder\\extract_yamuna_data.py (~1,900 lines)", "CDSE OData OAuth2 + USGS M2M clients, scene selection, parallel download with resume, SCL masked median composite"],
    ["4", "Imagery downloaded", "2026-10", "download_state.json, s1_extract_state.json, l8_download_state.json", "100 scenes: 39 Sentinel-2 (S2A 19 / S2B 20), 55 Sentinel-1A, 6 Landsat-8/9. 134 GB on disk"],
    ["5", "Products generated", "2026-10", "yamuna_data\\{sentinel2,sentinel1,landsat8}", "29 GeoTIFFs: 11 S2 (5 annual + 6 quarterly), 12 S1 (VV/VH x 6), 6 L8 thermal"],
    ["6", "Inventory validation", "2026-10", "scripts\\01_verify_inventory.py, metadata\\inventory_check.csv", "All 29 files checked for bands, dtype, CRS, resolution, nodata, AOI overlap"],
    ["7", "River centreline", "2026-10", "generate_centerline.py (failed), generate_centerline_s1.py (used)", "NDWI on dry-season S2 failed; switched to S1 VV + Otsu. Result: 50.21 km, geojson + gpkg"],
    ["8", "Centreline validation", "2026-10", "scripts\\02_validate_centerline.py", "CRS, geometry, length, direction, segment lengths, self-intersections checked"],
    ["9", "Sampling design", "2026-10", "scripts\\03_make_transects.py, transects\\", "51 perpendicular transects at 1 km spacing, 3 km long; points, lines, CSV, map"],
    ["10", "Chip extraction", "2026-10", "scripts\\04_extract_training_chips.py, extract_chips_all_quarters.py, extract_sar_chips.py", "42 transects retained of 51 (9 rejected: barrage/urban). 252 S2 chips (14-band) + 252 S1 chips (2-band), 6 quarters"],
    ["11", "Spectral indices", "2026-10", "extract_yamuna_data.py lines 1020-1026", "NDVI, NDWI, NDBI, NDSI computed by band NAME; written as bands 11-14 with x5000 encoding"],
    ["12", "Labeling setup and sign-off", "2026-10/11", "scripts\\05_prepare_labeling.py, 06_generate_reviewer_sheet.py, 07_finalize_labels.py", "Rubric + 6 quarterly review packages; 252 human-reviewed labels FROZEN: 55 MINING / 45 NOT MINING / 152 UNSURE"],
    ["13", "Index verification", "2026-10-28", "scripts\\08_verify_indices.py, index_verification_report.md", "5-check suite. Found NDVI/NDWI/NDBI mismatch (~0.27 max diff) while NDSI passed"],
    ["14", "Root-cause diagnosis", "2026-10-28", "scripts\\09_band_mapping_check.py, band_mapping_report.md", "Brute-force band-pair search proved B8 written at position 4 instead of 7. Stored indices correct; output band order wrong"],
    ["15", "Band-order fix AND rebuild", "2026-10/11", "src/acquisition/rebuild_composites_from_local.py, C:\\New folder\\yamuna_data_fixed, chips_fixed", "S2_SPECTRAL_BANDS corrected; 11 composites + 252 chips rebuilt into NEW folders; 11/11 band-position PASS, 5/5 index checks PASS; originals untouched"],
    ["16", "Progress deck", "2026-10-28", "Project_Progress_Presentation.pptx (4 slides)", "Navy/gold theme, DTU logo on every slide, 55% visual loader, proportional day timeline, speaker notes on all 4 slides"],
    ["17", "Presentation script", "2026-10-28", "Presentation_Script_and_Reasoning.docx / .pdf (13 pages)", "Verbatim script, reasoning per slide, paper justifications, 12 Q&A, numbers cheat sheet"],
    ["18", "Deck audit and export", "2026-10-28", "audit_ppt.py, .pdf exports", "No text overflow or out-of-bounds except 2 intentional decorative circles; PowerPoint opens with no repair prompt"],
    ["19", "Persistent notes", "2026-10-28", "C:\\scamshield vault", "Project memory + workflows updated and pushed to GitHub"],
    ["20", "Extra features", "2026-11-22", "src/processing/compute_extra_features.py, 08_Extra_Features_and_Thresholds.pdf", "Water fraction (Otsu clamped to >=0), CMI=(B11-B12)/(B11+B12) bare-exposure ratio, distance to centreline for 11 scenes + 252 chips"],
    ["21", "Decisive-label caveat", "2026-11-22", "data/verified_labels.csv, label_validation.txt", "100 decisive labels perfectly separable by sand_frac > 0.575. Documented as transparent bare-sediment rule, NOT a measured accuracy"],
    ["22", "Reviewer packages", "2026-11-22", "C:\\New folder\\label_review\\<quarter>\\", "6 quarterly PDFs + CSVs + previews covering all 252 chips; geometrically verified clean (0 overlaps)"],
    ["23", "Pixel-mask annotation tool", "2026-11-22", "src/labeling/08_select_annotation_chips.py, annotation_server.py, annotation_ui.html", "28 chips (16 original + 12 river), cyan water overlay, 24 unique transects; Flask server on 127.0.0.1:8765; 256x256 binary masks (16/28 saved so far)"],
    ["24", "NDSI annotation guide", "2026-11-22", "docs/documentation_pdfs/09_Annotation_Guide_for_Mining_Masks.pdf", "Colour convention, sand-vs-mining distinction, extraction signatures, workflow, common mistakes; also embedded in the annotation UI"],
]

open_rows = [
    ["O1", "Draw 16 human pixel masks in the browser tool", "Blocks U-Net/LMS-Net training"],
    ["O2", "Train U-Net/LMS-Net with 3-fold GroupKFold by transect", "Need real IoU/Dice/F1 before any claim"],
    ["O3", "Self-training loop to auto-mask all 252 chips", "Needed for full-dataset risk ranking"],
    ["O4", "Approve AHP weights and validate hotspot ranking", "C15 hard gate"],
    ["O5", "Fix deck slide 2 script names and slide 4 fixed-day timeline", "Now stale"],
]

build("01_Work_Completed_To_Date.pdf", "Work Completed To Date",
      "What has already been done, with the evidence file for each item", [
    P("1. Completed work", H1),
    P("Every row below is verifiable: the evidence column names the file that proves it.", BODY),
    tbl(["#", "Work item", "When", "Evidence file / location", "What was actually produced"],
        done_rows, [8 * mm, 34 * mm, 17 * mm, 50 * mm, 73 * mm], font=7.2),
    PageBreak(),
    P("2. Open items carried forward", H1),
    tbl(["#", "Item", "Why it matters"], open_rows, [10 * mm, 82 * mm, 90 * mm]),
    Spacer(1, 8),
    P("3. Honest completion statement", H1),
    P("The deck reports 55%. That is the weight of the data-engineering and labeling block, which is now closed end-to-end "
      "(rebuild PASS, 252 labels frozen). The strictly usable share today is therefore about 55%, not more: the 16 human "
      "pixel masks are still outstanding, so U-Net/LMS-Net training has not started and no metric is claimed. Models (30%), "
      "dashboard (10%) and reporting (5%) remain. Do not claim more than 55%.", CALLOUT),
])

# ============================================================ 02 DATA
build("02_Data_and_Sensors.pdf", "Data and Sensors Documentation",
      "Exactly what imagery exists, where it came from, and what each band means", [
    P("1. Source scenes", H1),
    tbl(["Satellite", "Scenes", "Detail"], [
        ["Sentinel-2A", "19", "Multispectral optical, L2A surface reflectance"],
        ["Sentinel-2B", "20", "Same; combined S2 total = 39"],
        ["Sentinel-1A", "55", "C-band SAR GRD IW; 61 attempted, 6 partials skipped, 0 failed"],
        ["Landsat-8 (LC08)", "4", "Thermal infrared"],
        ["Landsat-9 (LC09)", "2", "Thermal infrared; Landsat total = 6"],
        ["TOTAL", "100", "134.4 GB on disk, 5,293 files"],
    ], [42 * mm, 22 * mm, 118 * mm]),
    Spacer(1, 6),
    P("Cross-check: 39 S2 scenes x 68 JP2 band files = 2,652 JP2 files on disk. 55 S1 scenes x 2 polarisations = 110 TIFFs.", SMALL),
    Spacer(1, 10),

    P("2. Deliverable products (29 rasters)", H1),
    tbl(["Product", "Count", "Geometry / bands", "Purpose"], [
        ["S2 annual composite", "5", "2018-2022, 1661x2450 px, 14 bands, 124 MB", "Long-term context"],
        ["S2 quarterly composite", "6", "2023 Q1 - 2024 Q2, 1661x2450 px, 14 bands, 124 MB", "Study period, change detection"],
        ["S1 VV / VH raster", "12", "6 quarters x 2 polarisations, 1661x2450 px, 1 band, 6 MB", "Monsoon coverage + centreline"],
        ["L8 thermal raster", "6", "554x817 px, 3 bands (B10 + red + NIR), float32 K, 4 MB", "Independent physical check"],
    ], [42 * mm, 16 * mm, 70 * mm, 54 * mm]),
    Spacer(1, 6),
    P("Extent: lon 77.150-77.320, lat 28.540-28.760 (EPSG:4326), about 16.6 x 24.4 km. "
      "Optical/SAR pixel size 10.0 x 9.93 m. Nodata = 0. Reflectance stored as uint16 (L2A x 10000). "
      "Indices packed as (index+1)x5000, decoded as raw/5000-1.", SMALL),
    PageBreak(),

    P("3. The 14-band Sentinel-2 stack", H1),
    tbl(["#", "Band", "Wavelength", "Native res", "What it shows / why we keep it"], [
        ["1", "B2 Blue", "490 nm", "10 m", "Turbidity and shallow water; true-colour preview"],
        ["2", "B3 Green", "560 nm", "10 m", "Green peak; input to NDWI and NDSI"],
        ["3", "B4 Red", "665 nm", "10 m", "Chlorophyll absorption; input to NDVI"],
        ["4", "B5 Red-edge", "705 nm", "20 m", "Vegetation stress on disturbed bars"],
        ["5", "B6 Red-edge", "740 nm", "20 m", "Red-edge slope, bare vs vegetated"],
        ["6", "B7 Red-edge", "783 nm", "20 m", "Red-edge slope"],
        ["7", "B8 NIR", "842 nm", "10 m", "Key NIR band; denominator of NDVI, NDWI, NDBI"],
        ["8", "B8A narrow NIR", "865 nm", "20 m", "Loaded but not used in the four indices (open question)"],
        ["9", "B11 SWIR-1", "1610 nm", "20 m", "Dry sand bright, wet sand dark; drives NDBI and NDSI"],
        ["10", "B12 SWIR-2", "2190 nm", "20 m", "Mineral / clay, sand vs built-up"],
        ["11", "NDVI", "(B8-B4)/(B8+B4)", "derived", "Vegetation confuser suppression"],
        ["12", "NDWI", "(B3-B8)/(B3+B8)", "derived", "Open water vs dry bar"],
        ["13", "NDBI", "(B11-B8)/(B11+B8)", "derived", "Bare surface, stockpiles, access roads"],
        ["14", "NDSI", "(B3-B11)/(B3+B11)", "derived", "Water positive, sand negative in this AOI"],
    ], [9 * mm, 27 * mm, 32 * mm, 20 * mm, 94 * mm], font=7.2),
    Spacer(1, 10),

    P("4. Chips (model input)", H1),
    tbl(["Type", "Size", "Bands", "Per quarter", "Quarters", "Unique total", "Files on disk"], [
        ["S2 chip", "256x256 (2.56 km square)", "14", "42", "6", "252", "294 (42 duplicates in 2023_Q2)"],
        ["S1 chip", "256x256", "2 (VV, VH)", "42", "6", "252", "252"],
    ], [20 * mm, 39 * mm, 20 * mm, 22 * mm, 20 * mm, 24 * mm, 37 * mm], font=7.2),
    Spacer(1, 8),
    P("9 of the 51 transects were rejected (barrage, bridge, fully urbanised bank with no floodplain). "
      "42 chips remain per quarter.", SMALL),
    PageBreak(),

    P("5. The band-order defect - exact diagnosis", H1),
    tbl(["Position", "On disk now (pre-fix build)", "Correct order"], [
        ["1-3", "B2, B3, B4", "B2, B3, B4"],
        ["4", "B8", "B5"],
        ["5", "B5", "B6"],
        ["6", "B6", "B7"],
        ["7", "B7", "B8"],
        ["8-10", "B8A, B11, B12", "B8A, B11, B12"],
        ["11-14", "NDVI, NDWI, NDBI, NDSI (CORRECT)", "NDVI, NDWI, NDBI, NDSI"],
    ], [24 * mm, 72 * mm, 72 * mm]),
    Spacer(1, 8),
    P("Root cause: S2_10M_BANDS = [B2,B3,B4,B8] was concatenated before the 20 m bands, placing B8 at position 4. "
      "The four indices were computed by band NAME, so they are correct. NDSI passed verification because it uses only "
      "B3 and B11 (positions 2 and 9, both correct); NDVI/NDWI/NDBI failed with max diff about 0.27 because they all "
      "depend on B8. The script is fixed at line 99; the products still need rebuilding.", CALLOUT),
    Spacer(1, 8),
    P("Rule until rebuild completes: index bands 11-14 are usable; raw spectral bands 4-7 are NOT.", BODY),
])

# ============================================================ 03 SCRIPTS
script_rows = [
    ["extract_yamuna_data.py", "extract_yamuna_data.py", "Download + process all sensors; 14-band composites incl. index math (lines 1020-1026)", "AOI + dates", "29 GeoTIFFs + CSVs", "python extract_yamuna_data.py --sources sentinel2 --workers 4 --base-path <dir> --yes"],
    ["build_centerline.py", "generate_centerline_s1.py\n(generate_centerline.py = failed NDWI attempt)", "S1 VV Otsu threshold, largest component, skeleton -> ordered polyline", "S1 VV raster", "yamuna_centerline.geojson, 50.21 km", "python scripts/generate_centerline_s1.py"],
    ["make_transects.py", "03_make_transects.py", "1 km spacing, local-tangent perpendicular, 3 km long, clipped", "centreline", "51 points + lines + table + map", "python scripts/03_make_transects.py"],
    ["extract_chips.py", "04_extract_chips.py\nextract_all_quarters.py\nextract_s1_chips.py", "256x256 windowed reads, nodata rejection, previews; quarter and S1 variants", "composites + transects", "252 S2 + 252 S1 chips", "python scripts/04_extract_chips.py"],
    ["compute_indices.py", "inline in extract_yamuna_data.py (lines 1020-1026)", "NDVI / NDWI / NDBI / NDSI from band-name lookups", "10 reflectance bands", "4 index bands (11-14)", "runs inside composite processing"],
    ["verify_indices.py", "08_verify_indices.py\n09_band_mapping_check.py", "5-check validation suite + brute-force band-pair forensic diagnosis (read-only)", "chips + composite", "index_verification_report.md, band_mapping_report.md", "python scripts/08_verify_indices.py"],
]
extra_rows = [
    ["01_verify_inventory.py", "Checks all 29 rasters: existence, bands, dtype, CRS, resolution, nodata, AOI overlap", "inventory_check.csv"],
    ["02_validate_centerline.py", "CRS, geometry, length, direction, segment lengths, self-intersections", "validation report + map"],
    ["05_prepare_labeling.py", "Copies reviewer-approved chips, creates rubric, manifest, agreement log", "labeling/ folder"],
]

build("03_Pipeline_Scripts.pdf", "Pipeline Scripts and Execution Order",
      "Which file does what, the real filename, and the command to run it", [
    P("1. The six names on slide 2 mapped to real files", H1),
    P("Three of the six names on slide 2 do not exist as files. This table is the authoritative mapping.", CALLOUT),
    tbl(["Slide 2 label", "Real file that exists", "What it does", "Input", "Output", "Command"],
        script_rows, [26 * mm, 38 * mm, 46 * mm, 18 * mm, 27 * mm, 27 * mm], font=6.8),
    Spacer(1, 10),
    P("2. Scripts not shown on slide 2", H1),
    tbl(["Script", "Purpose", "Output"], extra_rows, [44 * mm, 88 * mm, 50 * mm]),
    PageBreak(),
    P("3. Execution order", H1),
    P("Download/process first, then geometry, then sampling, then chips, then labeling, then verification. "
      "Each step's output is the next step's input.", BODY),
    tbl(["Order", "Script", "Produces"], [
        ["0", "extract_yamuna_data.py", "29 composites + inventory CSVs"],
        ["1", "01_verify_inventory.py", "inventory_check.csv"],
        ["2", "generate_centerline_s1.py", "centreline geojson (50.21 km)"],
        ["3", "02_validate_centerline.py", "centreline validation"],
        ["4", "03_make_transects.py", "51 transects"],
        ["5", "04_extract_training_chips.py", "42 chips (one quarter)"],
        ["6", "05_prepare_labeling.py", "labeling set + manifest"],
        ["7", "extract_all_quarters.py / extract_s1_chips.py", "252 S2 + 252 S1 chips"],
        ["8", "08_verify_indices.py", "index verification report"],
        ["9", "09_band_mapping_check.py", "band mapping diagnosis"],
    ], [16 * mm, 70 * mm, 96 * mm]),
    Spacer(1, 8),
    P("4. Location of all scripts", H1),
    bullets([
        "Main download/processing: C:\\New folder\\extract_yamuna_data.py",
        "Pipeline steps: C:\\New folder\\yamuna_work\\scripts\\",
        "Deck builder: C:\\New folder\\ppt_v2.py (canonical), ppt_45d.py, ppt_final.py",
        "Script document builder: C:\\New folder\\make_script_doc.py",
        "Docs pack builder: C:\\New folder\\build_documentation_pack.py (this pack)",
    ]),
])

# ============================================================ 04 MODELS
build("04_Models_and_Justification.pdf", "Detection and Risk Models - Design and Justification",
      "Which model is used at each stage, why, and how it is evaluated", [
    P("Status: these four models are DESIGNED but NOT YET TRAINED. Everything below is the plan, not a result.", CALLOUT),
    P("1. The four models", H1),
    tbl(["#", "Model", "Input", "Output", "Why this model", "Evaluation"], [
        ["1", "Random Forest / XGBoost", "14 values per pixel (10 bands + 4 indices)", "mining probability", "Cheap sanity benchmark (an afternoon). If trees already work, the deep model is confirmation not a gamble. Gives feature importances proving the indices carry signal. Also the fallback detector.", "Precision, recall, F1; feature importance ranking"],
        ["2", "U-Net / LMS-Net segmentation", "256x256x14 chip", "256x256 mining mask", "The main detector. Segmentation not classification, because the deliverable is a pixel-level map and risk needs area. LMS-Net multi-scale handles pits and kilometre-long bars; 98.07% at 1/10 U-Net parameters matches the lightweight constraint.", "IoU, F1, per-class PR, confusion matrix"],
        ["3", "S2 + S1 late fusion", "optical probability map + VV/VH probability map", "fused probability map", "Monsoon (June-Sept) is cloud-blocked and is peak mining season. SAR is all-weather. Late fusion means the optical model still works standalone when SAR is missing.", "Compare fused vs optical-only, especially on Q2/Q3"],
        ["4", "Risk-score regressor", "detection area + persistence + morphology + access + vegetation loss", "0-100 score per 1 km segment", "Enforcement needs a priority list, not just detection. AHP weights are auditable; learned calibration improves fit. The Nair paper reports the hybrid beats either component alone (AUC > 0.93).", "Rank correlation against known hotspots (Palla, Jaitpur-Kondli)"],
    ], [8 * mm, 32 * mm, 33 * mm, 25 * mm, 58 * mm, 26 * mm], font=6.9),
    PageBreak(),

    P("2. How they chain", H1),
    P("14-band chips -> (1) RF/XGB baseline -> (2) segmentation mask -> (3) S1 fusion -> hectares per segment "
      "-> (4) risk score -> priority table -> dashboard.", BODY),
    Spacer(1, 8),
    P("3. Risk factors and proposed AHP weights", H1),
    tbl(["Factor", "Measure", "Weight", "Reason"], [
        ["Detection intensity", "mining pixels -> hectares per segment", "30%", "Direct evidence of extraction"],
        ["Temporal persistence", "how many of 6 quarters flagged (0-6)", "25%", "Permanent pit vs one-off disturbance"],
        ["Morphological change", "bank shift, width change, erosion/deposition", "20%", "Physical damage, from the Sutlej method"],
        ["Access proximity", "distance to roads, settlements, bridges", "15%", "Mining needs machinery access"],
        ["Vegetation loss", "NDVI drop on a previously stable bar", "10%", "Disturbance signature"],
    ], [36 * mm, 66 * mm, 16 * mm, 64 * mm]),
    Spacer(1, 6),
    P("Tiers: High >= 70, Medium 40-70, Low < 40. Weights are a proposed starting matrix requiring your approval.", SMALL),
    Spacer(1, 10),
    P("4. The honest answer on risk labels", H1),
    P("No dataset contains a per-pixel 'risk' label. The training target is the AHP composite score itself, with a "
      "learned model calibrating it; validation is external - does the model rank the known illegal-extraction clusters "
      "(Palla, Jaitpur-Kondli) above quiet reaches? Report rank correlation, NOT a fabricated risk accuracy.", CALLOUT),
    Spacer(1, 8),
    P("5. Hard dependency", H1),
    P("Models 1 and 2 ingest all 14 bands. The current composites have raw bands 4-7 permuted. "
      "Phase A (rebuild + verification) must pass before any training starts. The index bands 11-14 are correct today, "
      "but they are not enough for the segmentation model.", CALLOUT),
    Spacer(1, 8),
    P("6. Anticipated questions", H1),
    tbl(["Question", "Answer"], [
        ["Why 30 days for 250 images?", "Compute is hours; the time is label verification, spatial CV and error analysis."],
        ["What if the deep model underperforms?", "Fall back to RF + indices: weaker ceiling, still a working product."],
        ["Why spatial cross-validation?", "Neighbouring chips overlap geographically; random splits leak and inflate accuracy."],
        ["Is this just thresholding?", "No. Thresholding makes labels; the network learns spatial context the indices cannot express."],
    ], [58 * mm, 124 * mm]),
])

# ============================================================ 05 LITERATURE
build("05_Literature_and_Reasons.pdf", "Literature Review - Why Each Paper Was Used",
      "What each paper says, why it was chosen, what was taken, and what was rejected", [
    P("1. The five core papers", H1),
    tbl(["Paper", "What it says", "Why we chose it", "What we take", "What we do NOT take"], [
        ["Zhang, Liu & Liu (2025), Remote Sensing 17(2):227 - LMS-Net", "Lightweight multi-scale segmentation of riverbank sand mining areas; 98.07% accuracy at ~1/10 U-Net parameters", "Same label definition as ours; matches the 'lightweight, laptop-deployable' constraint in our problem statement; multi-scale covers pit-to-kilometre patch range", "Multi-scale backbone idea; accuracy/parameter trade-off as benchmark", "Their trained weights - different sensor, river and season"],
        ["Kaur, Gani, Pathak & Tiwari (2025), Env. Geochem. Health 47(11):459 - Sutlej", "23-year morphometric study: channel width variation, 8.6 m bank shift, 2,263 ha erosion vs 1,562 ha deposition", "Supplies the PHYSICAL quantities risk needs; Sutlej is a Himalayan-fed monsoonal sand-bed river like the Yamuna, so magnitudes transfer", "Change-metric definitions; annual-composite comparison design; sanity band", "Discharge-based calibration - no gauge data for Delhi"],
        ["Nair et al. (2025), Geocarto International 40(1):2551261 - AHP + ML", "AHP weighting plus 8 ML models over 8 conditioning parameters; AUC-ROC > 0.93", "Our prioritization blueprint; all 8 parameters derivable from free data; hybrid beats either component alone, justifying expert weights + learned calibration", "Parameter set, AHP procedure, hybrid evaluation", "Flood-vulnerability target variable - we predict mining intensity"],
        ["India-specific multispectral sandbank detection study (JIIT Noida)", "India-calibrated NDVI/NDWI/NDBI/NDSI for sand vs water vs vegetation vs built-up", "Defines the MANUAL-LABELING model used for our reviewer sheets: compute indices, threshold, then human-verify. This is the India-specific paper, NOT the IIT Kharagpur study", "Index family, separability logic, starting threshold ranges", "Thresholds as final - we recalibrated on our 252 chips"],
        ["Mukherjee et al. - Coal Mine Index (CMI)", "CMI = (B11 - B12)/(B11 + B12): SWIR-I minus SWIR-II over their sum, an exposed-surface contrast ratio", "Adds an independent bare-exposure feature alongside NDVI/NDWI/NDBI/NDSI. B11/B12 are already in our 14-band chips, so it costs no extra download", "Bare-exposure ratio only; used as an extra feature for labeling and risk", "Treating it as a COAL detector. We have no coal in the AOI; the index is reused as a generic SWIR exposure ratio"],
    ], [32 * mm, 43 * mm, 52 * mm, 37 * mm, 28 * mm], font=6.4),
    PageBreak(),
    P("2. Approaches reviewed and deliberately rejected", H1),
    tbl(["Approach", "Reason for rejection"], [
        ["Generic U-Net / DeepLab baselines", "No handling of the extreme scale range of mining patches; no domain prior"],
        ["Deep learning on commercial imagery (WorldView, Planet)", "Not free; breaks reproducibility and the lightweight-deployment claim"],
        ["Global water-mapping products (30-500 m)", "Too coarse for pit-scale features - a pit is a few pixels"],
        ["Earth-Engine-only pipelines", "Ineligible for non-commercial access; pipeline would not be portable"],
        ["sentinelsat / old SciHub", "Decommissioned; the archive is now the Copernicus Data Space Ecosystem OData API"],
    ], [68 * mm, 114 * mm]),
    Spacer(1, 10),
    P("3. Sensor rationale", H1),
    tbl(["Sensor", "Why"], [
        ["Sentinel-2 MSI (primary)", "10 m visible/NIR, 20 m red-edge/SWIR, 5-day revisit, free, L2A surface reflectance. SWIR B11/B12 needed for NDBI and for dry vs damp sand."],
        ["Sentinel-1 C-band SAR", "All-weather day/night. Monsoon is the cloudiest and highest-risk season. VV separates dry rough sand from wet channel; also produced a better centreline than NDWI."],
        ["Landsat-8/9 TIRS", "Thermal B10 gives an independent physical check: dry sand heats and cools differently from wet ground. 30 m, corroboration only."],
    ], [45 * mm, 137 * mm]),
    Spacer(1, 8),
    P("4. Index formulas", H1),
    tbl(["Index", "Formula", "Source", "Role"], [
        ["NDVI", "(B8-B4)/(B8+B4)", "Rouse 1974", "Vegetation suppression"],
        ["NDWI", "(B3-B8)/(B3+B8)", "McFeeters 1996", "Open water vs dry bar"],
        ["NDBI", "(B11-B8)/(B11+B8)", "Zha 2003", "Bare / built surface"],
        ["NDSI", "(B3-B11)/(B3+B11)", "Dozier 1989 / Xu 2006", "Water positive, sand negative in this AOI"],
    ], [20 * mm, 43 * mm, 45 * mm, 74 * mm]),
    Spacer(1, 8),
    P("5. Design decisions and their reasons", H1),
    tbl(["Decision", "Value", "Reason"], [
        ["Study reach", "Palla to Jaitpur", "Administrative Delhi stretch with known active clusters; matches the enforcing jurisdiction"],
        ["Centreline", "50.21 km from S1 VV", "NDWI failed in dry season (mostly exposed sand); Otsu on backscatter works year-round"],
        ["Transects", "51 at 1 km, 3 km long", "One decision unit per river-km; long enough to cross both banks"],
        ["Chip size", "256x256 at 10 m = 2.56 km", "Matches a mining cluster; standard CNN tile size"],
        ["Chips kept", "42 of 51", "9 fell on barrage, bridge or fully urbanised bank"],
        ["Temporal sampling", "6 quarters 2023Q1-2024Q2", "Mining visibility peaks in dry pre-monsoon; one date cannot separate permanent bar from active pit"],
        ["Bands", "10 spectral + 4 indices", "Red-edge detects stressed vegetation; indices are explicit physical features"],
        ["Compositing", "SCL mask + median", "Median removes cloud/shadow better than mean"],
    ], [34 * mm, 42 * mm, 106 * mm], font=7.2),
])

# ============================================================ 06 REMAINING STEPS
build("06_Remaining_Steps.pdf", "Remaining Steps - Full Execution Plan",
      "Every step from here to delivery, with owner, estimate and hard gates", [
    P("1. Phase A - Data repair (COMPLETE)", H1),
    P("All outputs went to NEW folders. Nothing under yamuna_data or chips was modified. 11/11 band-position PASS, 5/5 index checks PASS.", CALLOUT),
    tbl(["#", "Action", "Output", "Owner", "Est."], [
        ["A1", "Snapshot originals (file list + hashes)", "baseline inventory", "Me", "5 min"],
        ["A2", "Confirm band-order fix at extract_yamuna_data.py line 99", "verified list", "Me", "2 min"],
        ["A3", "Build driver to process local SAFE dirs (no download)", "driver script", "Me", "20 min"],
        ["A4", "Rebuild 5 annual S2 composites", "5 x 14-band GeoTIFF", "Me", "25 min"],
        ["A5", "Rebuild 6 quarterly S2 composites", "6 x 14-band GeoTIFF", "Me", "25 min"],
        ["A6", "Check band positions in rebuilt files", "layout report", "Me", "5 min"],
        ["A7", "Regenerate 252 S2 chips in chips_fixed", "252 x 256x256x14", "Me", "30 min"],
        ["A8", "Drop duplicate 2023_Q2 set", "42 files not 84", "Me", "5 min"],
        ["A9", "Relink 252 S1 chips (unaffected)", "new path", "Me", "10 min"],
        ["A10", "Re-run 08_verify_indices + 09_band_mapping_check", "fresh reports", "Me", "20 min"],
    ], [12 * mm, 82 * mm, 46 * mm, 18 * mm, 18 * mm], font=7.2),
    P("GATE A10: PASSED — all five checks PASS on the rebuilt data. Phase B chip labels are also complete.", CALLOUT),
    PageBreak(),

    P("2. Phase B - Labels (one human step)", H1),
    tbl(["#", "Action", "Output", "Owner", "Est."], [
        ["B1", "Freeze labeling rubric", "1-page rule set", "Me", "DONE"],
        ["B2", "Regenerate candidates on rebuilt chips", "candidate manifest", "Me", "DONE"],
        ["B3", "Build 6 quarterly reviewer sheets", "252-chip review packs", "Me", "DONE"],
        ["B4", "Human-verify all 252 chips", "verified_labels.csv: 55/45/152", "YOU", "DONE"],
        ["B5", "Freeze chip labels + split roles", "data/verified_labels.csv", "Me", "DONE"],
        ["B6", "Select 28 chips + build annotation tool", "browser tool on :8765", "Me", "DONE"],
        ["B7", "Draw 16 human pixel masks", "16 binary PNG masks", "YOU", "~1 h"],
        ["B8", "Mask sign-off (28/28)", "training-ready dataset", "YOU", "10 min"],
    ], [12 * mm, 82 * mm, 46 * mm, 18 * mm, 18 * mm], font=7.2),
    P("GATE B8: no segmentation training before 28/28 masks. Chip-label sign-off (B7 in the old plan) is already DONE.", CALLOUT),
    Spacer(1, 8),

    P("3. Phase C - Models (critical path)", H1),
    tbl(["#", "Action", "Output", "Owner", "Est."], [
        ["C1", "Environment check: sklearn / xgboost / torch / GPU or Colab", "working runtime", "Me", "10 min"],
        ["C2", "Build pixel dataset with transect ID as grouping key", "arrays + groups", "Me", "30 min"],
        ["C3", "Train RF / XGBoost baseline", "model + importances", "Me", "45 min"],
        ["C4", "Evaluate baseline, go/no-go report", "metrics", "Me", "10 min"],
        ["C5", "Implement U-Net / LMS-Net for the 28 real masks", "architecture code", "Me", "60 min"],
        ["C6", "Train with BCE+Dice, augmentation, 3-fold GroupKFold by transect", "3 trained folds", "Me", "2-4 h GPU / 8-12 h CPU"],
        ["C7", "Evaluate IoU, Dice, precision, recall, F1, confusion matrix", "metrics table", "Me", "30 min"],
        ["C8", "Error analysis: worst transects + mask visuals", "error report", "Me", "30 min"],
        ["C8b", "Self-training: apply trained model to all 252 chips, keep high-confidence masks", "auto-masks + confidence", "Me", "1-2 h"],
        ["C9", "Implement S1 late fusion", "fusion code", "Me", "60 min"],
        ["C10", "Train and compare optical-only vs fused", "comparison table", "Me", "60 min"],
        ["C11", "Morphology change metrics from 6 quarters", "bank shift / area table", "Me", "60 min"],
        ["C12", "Propose 5-factor AHP matrix", "draft weights", "Me", "20 min"],
        ["C13", "Approve AHP weights", "final weights", "YOU", "20 min"],
        ["C14", "Train risk calibrator, score 51 segments, tier them", "risk table", "Me", "60 min"],
        ["C15", "Validate against Palla / Jaitpur-Kondli hotspots", "rank report", "Me", "30 min"],
    ], [12 * mm, 82 * mm, 46 * mm, 18 * mm, 18 * mm], font=7.2),
    P("GATE C15: ranking must be behaviourally correct. Report rank correlation, never an invented risk accuracy.", CALLOUT),
    PageBreak(),

    P("4. Phase D - Dashboard (parallel)", H1),
    tbl(["#", "Action", "Output", "Owner", "Est."], [
        ["D1", "Freeze MVP: map + overlay + priority table", "scope decision", "YOU", "10 min"],
        ["D2", "Define API contract", "endpoint spec", "Me", "20 min"],
        ["D3", "Scaffold Node/Express + MongoDB (or SQLite fallback)", "running backend", "Me", "30 min"],
        ["D4", "Schema: Segment, Chip, Mask, Label, RiskScore", "data models", "Me", "20 min"],
        ["D5", "Backend CRUD + mask serving", "working API", "Me", "60 min"],
        ["D6", "React shell + Leaflet map with AOI boundary", "map view", "Me", "45 min"],
        ["D7", "Mining-mask overlay with opacity toggle", "visible overlay", "Me", "45 min"],
        ["D8", "Priority table (risk, hectares, tier, sortable)", "UI table", "Me", "30 min"],
        ["D9", "Wire model outputs into the app", "live dashboard", "Me", "30 min"],
        ["D10", "Integration test + click-test", "verified demo", "YOU", "30 min"],
    ], [12 * mm, 82 * mm, 46 * mm, 18 * mm, 18 * mm], font=7.2),
    Spacer(1, 6),
    P("5. Phase E - Reports and deck", H1),
    tbl(["#", "Action", "Owner", "Est."], [
        ["E1", "Draft paper: abstract, method, results, 5 papers, limitations", "Me", "90 min"],
        ["E2", "Assemble thesis section from PROJECT_LOG.md", "Me", "60 min"],
        ["E3", "Fix slide 2 script names -> real filenames", "Me", "15 min"],
        ["E4", "Replace slide 4 fixed-day axis with milestone order (no deadline)", "Me", "15 min"],
        ["E5", "Remove fixed-day estimates from slide 3", "Me", "10 min"],
        ["E6", "Update speaker notes", "Me", "15 min"],
        ["E7", "Re-export pptx, script docx and both PDFs", "Me", "10 min"],
        ["E8", "Verify 4 slides, no repair, text extractable", "Me", "10 min"],
    ], [12 * mm, 138 * mm, 22 * mm, 18 * mm], font=7.2),
    Spacer(1, 6),
    P("6. Phase F - Handover", H1),
    tbl(["#", "Action", "Owner", "Est."], [
        ["F1", "Timed rehearsal against the deck (9-10 min)", "Me + You", "30 min"],
        ["F2", "Run through the 12-question Q&A bank", "YOU", "20 min"],
        ["F3", "Final checklist: Group 162, names, rolls, supervisor, logo", "YOU", "10 min"],
        ["F4", "Present", "YOU", "10 min"],
    ], [12 * mm, 138 * mm, 22 * mm, 18 * mm], font=7.2),
    Spacer(1, 10),
    P("7. Totals", H1),
    tbl(["Owner", "Time"], [
        ["Me - coding, execution, reports, deck", "~22-27 hours"],
        ["You - labels, 3 approvals, click-test, rehearsal, presentation", "~2.5-3.5 hours"],
        ["Calendar time if run back-to-back", "2-4 days (shorter with Colab T4)"],
    ], [110 * mm, 72 * mm]),
    Spacer(1, 8),
    P("Three hard gates: A10 verification, B7 label sign-off, C15 risk validation.", CALLOUT),
])

print("\nALL DOCS DONE:", OUT)
