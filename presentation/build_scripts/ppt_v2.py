from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from PIL import Image
import os

# ---------------------------------------------------------------- setup
prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)

NAVY      = RGBColor(0x0E, 0x2A, 0x47)
NAVY_DEEP = RGBColor(0x09, 0x1C, 0x30)
BLUE      = RGBColor(0x1F, 0x4E, 0x79)
BLUE_MID  = RGBColor(0x2E, 0x6D, 0xA4)
GOLD      = RGBColor(0xE8, 0xA8, 0x38)
GOLD_SOFT = RGBColor(0xF6, 0xD3, 0x8A)
GREEN     = RGBColor(0x2E, 0x8B, 0x57)
WHITE     = RGBColor(0xFF, 0xFF, 0xFF)
OFFWHITE  = RGBColor(0xF7, 0xF9, 0xFC)
CARD      = RGBColor(0xEF, 0xF3, 0xF8)
GRAY      = RGBColor(0x5A, 0x6B, 0x80)
DARK      = RGBColor(0x1B, 0x26, 0x33)

SLIDE_W = 13.333
SLIDE_H = 7.5
LOGO_PATH = r"C:\Btech Project Important Files\Timeline\dtu_logo.png"

MI = Image.open(LOGO_PATH)
LOGO_AR = MI.width / MI.height
MI.close()


# ---------------------------------------------------------------- helpers
def bg(slide, color):
    f = slide.background.fill
    f.solid()
    f.fore_color.rgb = color


def rect(slide, x, y, w, h, color, shape=MSO_SHAPE.RECTANGLE, line=None, lw=1.0, radius=None):
    s = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    if color is None:
        s.fill.background()
    else:
        s.fill.solid()
        s.fill.fore_color.rgb = color
    if line is None:
        s.line.fill.background()
    else:
        s.line.color.rgb = line
        s.line.width = Pt(lw)
    s.shadow.inherit = False
    if radius is not None and shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        try:
            s.adjustments[0] = radius
        except Exception:
            pass
    return s


def tx(slide, x, y, w, h, text, size=14, bold=False, color=DARK, align=PP_ALIGN.LEFT,
       font="Calibri", space_after=0, anchor=MSO_ANCHOR.TOP, line_spacing=None):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    tf.margin_left = 0
    tf.margin_right = 0
    tf.margin_top = 0
    tf.margin_bottom = 0
    tf.vertical_anchor = anchor
    lines = text.split("\n")
    for i, ln in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = ln
        p.alignment = align
        p.font.size = Pt(size)
        p.font.bold = bold
        p.font.color.rgb = color
        p.font.name = font
        if space_after:
            p.space_after = Pt(space_after)
        if line_spacing:
            p.line_spacing = line_spacing
    return box


def bullets(slide, x, y, w, items, size=12, gap=0.42, color=DARK, marker="\u25AA",
            marker_color=BLUE_MID, bold_lead=False):
    cy = y
    for it in items:
        if isinstance(it, tuple):
            lead, rest = it
        else:
            lead, rest = None, it
        tx(slide, x, cy - 0.02, 0.22, 0.3, marker, size=size + 2, bold=True,
           color=marker_color, align=PP_ALIGN.LEFT)
        if lead:
            b = tx(slide, x + 0.25, cy, w - 0.25, 0.50, "", size=size, color=color,
                   line_spacing=1.05)
            tf = b.text_frame
            p = tf.paragraphs[0]
            r1 = p.add_run()
            r1.text = lead
            r1.font.bold = True
            r1.font.size = Pt(size)
            r1.font.color.rgb = NAVY
            r1.font.name = "Calibri"
            r2 = p.add_run()
            r2.text = rest
            r2.font.size = Pt(size)
            r2.font.color.rgb = color
            r2.font.name = "Calibri"
        else:
            tx(slide, x + 0.25, cy, w - 0.25, 0.50, rest, size=size, color=color,
               line_spacing=1.05)
        cy += gap


def logo_card(slide, x=0.34, y=0.14, h=0.84):
    """DTU logo on a white rounded card (keeps transparent PNG readable)."""
    w = h * LOGO_AR
    pad = 0.10
    rect(slide, x, y, w + pad * 2, h + pad * 2, WHITE,
         shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.10)
    slide.shapes.add_picture(LOGO_PATH, Inches(x + pad), Inches(y + pad),
                             Inches(w), Inches(h))
    return x + w + pad * 2


def header(slide, title, kicker=None):
    rect(slide, 0, 0, SLIDE_W, 1.12, NAVY)
    rect(slide, 0, 1.12, SLIDE_W, 0.05, GOLD)
    right = logo_card(slide)
    tx(slide, right + 0.28, 0.20, 9.0, 0.5, title, size=30, bold=True, color=WHITE)
    if kicker:
        tx(slide, right + 0.30, 0.70, 9.0, 0.3, kicker, size=11.5, color=GOLD_SOFT)
    # small tag right side
    tx(slide, SLIDE_W - 2.05, 0.44, 1.7, 0.3, "DTU  \u2022  IT", size=10, bold=True,
       color=RGBColor(0x8E, 0xA8, 0xC4), align=PP_ALIGN.RIGHT)


def loader(slide, x, y, w, pct, label, sub=None, height=0.30):
    """Segmented progress loader with fill + knob + percentage."""
    rect(slide, x, y, w, height, RGBColor(0xDD, 0xE6, 0xEF),
         shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.5)
    fill_w = max(0.14, w * pct / 100.0)
    rect(slide, x, y, fill_w, height, BLUE_MID,
         shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.5)
    # knob
    knob = height * 1.35
    rect(slide, x + fill_w - knob / 2, y + (height - knob) / 2, knob, knob,
         WHITE, shape=MSO_SHAPE.OVAL, line=BLUE_MID, lw=2.0)
    tx(slide, x, y - 0.34, w, 0.28, label, size=11, bold=True, color=NAVY)
    tx(slide, x + w - 1.5, y - 0.36, 1.5, 0.32, "%d%%" % pct, size=15, bold=True,
       color=BLUE, align=PP_ALIGN.RIGHT)
    if sub:
        tx(slide, x, y + height + 0.10, w, 0.28, sub, size=9.5, color=GRAY)


# ================================================================ SLIDE 1
s1 = prs.slides.add_slide(prs.slide_layouts[6])
bg(s1, NAVY)
# decorative
rect(s1, SLIDE_W - 3.6, -1.2, 5.2, 5.2, RGBColor(0x11, 0x33, 0x56), shape=MSO_SHAPE.OVAL)
rect(s1, -1.6, SLIDE_H - 2.6, 4.6, 4.6, RGBColor(0x11, 0x33, 0x56), shape=MSO_SHAPE.OVAL)
rect(s1, 0, 0, SLIDE_W, 0.12, GOLD)
rect(s1, 0, SLIDE_H - 0.12, SLIDE_W, 0.12, GOLD)

logo_card(s1, x=0.55, y=0.34, h=1.05)

# institution block (top right)
tx(s1, 8.6, 0.42, 4.3, 1.1,
   "DELHI TECHNOLOGICAL UNIVERSITY\nDepartment of Information Technology",
   size=12, bold=True, color=RGBColor(0xC5, 0xD6, 0xE8), align=PP_ALIGN.RIGHT)

tx(s1, 1.0, 1.95, 11.333, 0.4,
   "BTECH  FINAL  YEAR  PROJECT   \u2022   PROGRESS  REVIEW", size=12,
   bold=True, color=GOLD, align=PP_ALIGN.CENTER)

tx(s1, 0.9, 2.45, 11.533, 1.7,
   "AI-BASED ILLEGAL SAND MINING DETECTION\nAND RISK PRIORITIZATION SYSTEM ON YAMUNA RIVER",
   size=33, bold=True, color=WHITE, align=PP_ALIGN.CENTER, line_spacing=1.1)

rect(s1, 5.35, 4.18, 2.63, 0.05, GOLD)

# info card
card_x, card_y, card_w, card_h = 2.05, 4.55, 9.23, 2.05
rect(s1, card_x, card_y, card_w, card_h, RGBColor(0x0B, 0x22, 0x3A),
     shape=MSO_SHAPE.ROUNDED_RECTANGLE, line=GOLD, lw=1.5, radius=0.05)

tx(s1, card_x + 0.45, card_y + 0.22, 3.0, 0.3, "GROUP  NUMBER", size=9.5, bold=True,
   color=RGBColor(0x8E, 0xA8, 0xC4))
tx(s1, card_x + 0.45, card_y + 0.46, 3.0, 0.32, "GROUP  162", size=15, bold=True, color=GOLD)

tx(s1, card_x + 3.75, card_y + 0.22, 4.0, 0.3, "TEAM  MEMBERS", size=9.5, bold=True,
   color=RGBColor(0x8E, 0xA8, 0xC4))
tx(s1, card_x + 3.75, card_y + 0.48, 5.1, 0.32,
   "Upendra Kumar  \u2013  23/IT/165", size=13.5, bold=True, color=WHITE)
tx(s1, card_x + 3.75, card_y + 0.80, 5.1, 0.32,
   "Somya Tripathi  \u2013  23/IT/162", size=13.5, bold=True, color=WHITE)

rect(s1, card_x + 0.45, card_y + 1.24, card_w - 0.9, 0.02, RGBColor(0x1E, 0x3F, 0x60))

tx(s1, card_x + 0.45, card_y + 1.38, 2.4, 0.3, "PROJECT  SUPERVISOR", size=9.5, bold=True,
   color=RGBColor(0x8E, 0xA8, 0xC4))
tx(s1, card_x + 2.55, card_y + 1.34, 6.2, 0.34, "Dr. Anita Thakur", size=14, bold=True,
   color=RGBColor(0xD9, 0xE6, 0xF3))

tx(s1, 0.9, 6.92, 11.533, 0.3,
   "Academic Year 2025\u201326   |   Delhi Technological University, Delhi",
   size=10, color=RGBColor(0x7E, 0x9B, 0xB8), align=PP_ALIGN.CENTER)


# ================================================================ SLIDE 2
s2 = prs.slides.add_slide(prs.slide_layouts[6])
bg(s2, WHITE)
header(s2, "PROGRESS  SO  FAR", "Literature review  \u2022  dataset engineering  \u2022  code written & executed")

# progress banner
rect(s2, 0.5, 1.42, 12.33, 1.24, OFFWHITE, shape=MSO_SHAPE.ROUNDED_RECTANGLE,
     line=RGBColor(0xD7, 0xE2, 0xEE), lw=1.0, radius=0.06)
tx(s2, 0.85, 1.58, 3.2, 0.3, "OVERALL  PROJECT  COMPLETION", size=10, bold=True,
   color=GRAY)
loader(s2, 0.85, 2.16, 8.55, 55,
       "Data collection & labeling (largest chunk) complete",
       None, height=0.26)
tx(s2, 9.9, 1.62, 2.6, 0.85, "55%", size=44, bold=True, color=BLUE, align=PP_ALIGN.RIGHT)
tx(s2, 9.9, 2.40, 2.6, 0.28, "work completed", size=10, color=GRAY, align=PP_ALIGN.RIGHT)

# ---- left card: literature review
lx, ly, lw_, lh = 0.5, 2.88, 5.95, 4.32
rect(s2, lx, ly, lw_, lh, CARD, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.04)
rect(s2, lx, ly, lw_, 0.46, BLUE, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.18)
rect(s2, lx, ly + 0.30, lw_, 0.16, BLUE)
tx(s2, lx + 0.28, ly + 0.09, 5.0, 0.3, "LITERATURE  REVIEW", size=13, bold=True, color=WHITE)

bullets(s2, lx + 0.28, ly + 0.66, lw_ - 0.56, [
    ("LMS-Net (2025) \u2014 ", "98.07% accuracy at 1/10th of U-Net parameters."),
    ("Sutlej morphometry (2025) \u2014 ", "23-yr series; bank shift 8.6 m, erosion 2,263 ha."),
    ("AHP + ML risk mapping (2025) \u2014 ", "AUC-ROC > 0.93 from 8 conditioning parameters."),
    ("JIIT Noida index study \u2014 ", "NDVI / NDWI / NDBI / NDSI sand thresholds."),
    ("Research gap \u2014 ", "no integrated detection + risk pipeline for Indian rivers."),
], size=10.5, gap=0.64, color=DARK, marker_color=BLUE_MID)

tx(s2, lx + 0.28, ly + lh - 0.42, lw_ - 0.56, 0.3,
   "20+ papers reviewed  \u2022  CV  \u2022  GIS  \u2022  hydrology", size=9.5, bold=True, color=GRAY)

# ---- right card: code
rx, ry, rw, rh = 6.88, 2.88, 5.95, 4.32
rect(s2, rx, ry, rw, rh, CARD, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.04)
rect(s2, rx, ry, rw, 0.46, NAVY, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.18)
rect(s2, rx, ry + 0.30, rw, 0.16, NAVY)
tx(s2, rx + 0.28, ry + 0.09, 5.0, 0.3, "CODE  WRITTEN  &  EXECUTED", size=13, bold=True, color=WHITE)

code_bits = [
    ("extract_yamuna_data.py", "S2 / S1 / Landsat-8 ingestion, 14-band composites"),
    ("build_centerline.py", "S1-VV Otsu threshold \u2192 50.21 km centreline"),
    ("make_transects.py", "51 perpendicular transects @ 1 km spacing"),
    ("extract_chips.py", "42 chips (256\u00d7256\u00d714) + 6-quarter stacks"),
    ("compute_indices.py", "NDVI / NDWI / NDBI / NDSI raster generation"),
    ("verify_indices.py", "5-check validation suite \u2192 band-order fix"),
]
cy = ry + 0.58
for fname, desc in code_bits:
    rect(s2, rx + 0.26, cy + 0.05, 0.09, 0.30, GREEN, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.4)
    tx(s2, rx + 0.46, cy + 0.01, rw - 0.75, 0.22, fname, size=10, bold=True, color=BLUE,
       font="Consolas")
    tx(s2, rx + 0.46, cy + 0.20, rw - 0.75, 0.22, desc, size=9, color=GRAY)
    cy += 0.47

# mini terminal
ty = ry + rh - 0.86
rect(s2, rx + 0.26, ty, rw - 0.52, 0.74, NAVY_DEEP, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.08)
tx(s2, rx + 0.42, ty + 0.09, rw - 0.8, 0.6,
   "PS> python verify_indices.py\n     NDSI PASS | NDVI PASS | NDWI PASS | NDBI PASS",
   size=9, color=RGBColor(0x7E, 0xD9, 0x9A), font="Consolas", line_spacing=1.25)


# ================================================================ SLIDE 3
s3 = prs.slides.add_slide(prs.slide_layouts[6])
bg(s3, WHITE)
header(s3, "TASKS  LEFT  TO  BE  DONE", "Model building, dashboard and reporting \u2014 the data groundwork is already finished")

rect(s3, 0.5, 1.42, 12.33, 0.62, RGBColor(0xE9, 0xF5, 0xEE),
     shape=MSO_SHAPE.ROUNDED_RECTANGLE, line=RGBColor(0xC2, 0xE3, 0xCE), lw=1.0, radius=0.14)
tx(s3, 0.82, 1.58, 11.7, 0.32,
   "DONE  \u2014  satellite data collection and chip labeling (the heaviest part, ~55% of the work).  "
   "Only modeling, dashboard and reporting remain.", size=11, bold=True, color=GREEN)

cols = [
    ("01", "INDEX MODEL  +  AUTO-LABELING", GOLD, [
        "Compute NDVI / NDWI / NDBI / NDSI per the JIIT Noida paper",
        "Calibrate sand-vs-water-vs-vegetation thresholds on 42 chips",
        "Model auto-labels every chip \u2192 MINING / NOT MINING / UNSURE",
        "Human spot-check of auto-labels, resolve borderline cases",
    ], "7 DAYS"),
    ("02", "DETECTION  &  RISK  MODELS", BLUE_MID, [
        "Baseline RF / XGBoost on 14-band chips (sanity benchmark)",
        "U-Net / LMS-Net segmentation with spatial cross-validation",
        "Sentinel-2 + Sentinel-1 SAR late-fusion model",
        "Risk-score regressor from detection + morphology change",
    ], "30 DAYS"),
    ("03", "MERN  DASHBOARD  +  DELIVERY", NAVY, [
        "React dashboard with risk map and pixel-level overlay",
        "Node / Express REST API + MongoDB label store",
        "Chip browser, labeling UI, segment priority table",
        "Integration, testing, conference paper and thesis",
    ], "20 DAYS"),
]

x = 0.5
cw = 3.94
gap = 0.26
for num, title, color, items, days in cols:
    rect(s3, x, 2.26, cw, 4.08, OFFWHITE, shape=MSO_SHAPE.ROUNDED_RECTANGLE,
         line=RGBColor(0xDA, 0xE4, 0xEF), lw=1.0, radius=0.04)
    rect(s3, x, 2.26, cw, 0.10, color)
    tx(s3, x + 0.26, 2.50, 0.7, 0.42, num, size=22, bold=True, color=color)
    tx(s3, x + 0.26, 2.96, cw - 0.52, 0.6, title, size=11.5, bold=True, color=NAVY,
       line_spacing=1.05)
    rect(s3, x + 0.26, 3.62, cw - 0.52, 0.02, RGBColor(0xDA, 0xE4, 0xEF))
    bullets(s3, x + 0.26, 3.74, cw - 0.52, items, size=10, gap=0.53, marker_color=color)
    rect(s3, x + 0.26, 5.86, cw - 0.52, 0.34, color, shape=MSO_SHAPE.ROUNDED_RECTANGLE,
         radius=0.4)
    tx(s3, x + 0.26, 5.93, cw - 0.52, 0.24, "ESTIMATED  ~ " + days.upper(), size=9.5,
       bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    x += cw + gap

tx(s3, 0.5, 6.55, 12.33, 0.3,
   "Tracks 01 and 03 run in parallel with track 02 \u2014 total elapsed time ~45 days   |   "
   "weekly commits  \u2022  bi-weekly supervisor review",
   size=9.5, color=GRAY, align=PP_ALIGN.CENTER)


# ================================================================ SLIDE 4
s4 = prs.slides.add_slide(prs.slide_layouts[6])
bg(s4, WHITE)
header(s4, "EXPECTED  TIMELINE  OF  COMPLETION",
       "45 days left  \u2014  milestones placed proportionally on a day axis")

# ---- effort summary row
cards = [
    ("DATA COLLECTION & LABELING", "COMPLETED", "55%", GREEN, True),
    ("MODEL  BUILDING", "~30 days", "30%", BLUE_MID, False),
    ("MERN  DASHBOARD", "~20 days", "10%", NAVY, False),
    ("REPORTING  &  DEFENSE", "~7 days", "5%", GOLD, False),
]
cx = 0.5
cw2 = 2.95
for name, val, pct, color, done in cards:
    rect(s4, cx, 1.45, cw2, 0.86, OFFWHITE, shape=MSO_SHAPE.ROUNDED_RECTANGLE,
         line=RGBColor(0xDA, 0xE4, 0xEF), lw=1.0, radius=0.10)
    rect(s4, cx, 1.45, 0.09, 0.86, color)
    tx(s4, cx + 0.22, 1.54, cw2 - 0.4, 0.24, name, size=9, bold=True, color=GRAY)
    tx(s4, cx + 0.22, 1.78, 1.5, 0.3, pct, size=15, bold=True, color=color)
    tx(s4, cx + 0.22, 2.06, cw2 - 0.4, 0.22, val, size=9.5, bold=True,
       color=GREEN if done else BLUE)
    cx += cw2 + 0.16

# ---- timeline line (45-day sprint, proportional spacing)
LINE_Y = 4.62
X0, X1 = 0.95, 12.25
SPAN = float(X1 - X0)
TOTAL_DAYS = 45.0

points = [
    (0,  "DAY 0",   "Today",            "55% complete",     GREEN),
    (7,  "DAY 7",   "Index model",      "auto-labeling",    BLUE_MID),
    (16, "DAY 16",  "Labels verified",  "baseline RF / XGB", BLUE_MID),
    (26, "DAY 26",  "Segmentation",     "U-Net / LMS-Net",  BLUE_MID),
    (34, "DAY 34",  "S2 + S1 fusion",   "risk scoring",     NAVY),
    (40, "DAY 40",  "MERN dashboard",   "live risk maps",   NAVY),
    (45, "DAY 45",  "Paper & thesis",   "defense ready",    GOLD),
]


def lerp(c1, c2, t):
    return RGBColor(int(c1[0] + (c2[0] - c1[0]) * t),
                    int(c1[1] + (c2[1] - c1[1]) * t),
                    int(c1[2] + (c2[2] - c1[2]) * t))


GOLD_RGB = (0xE8, 0xA8, 0x38)
NAVY_RGB = (0x0E, 0x2A, 0x47)

# base track
rect(s4, X0, LINE_Y - 0.035, SPAN, 0.07, RGBColor(0xDC, 0xE5, 0xEE),
     shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.5)

positions = [X0 + SPAN * d / TOTAL_DAYS for d, _a, _b, _c, _e in points]

# graded segments between milestones
for i in range(len(points) - 1):
    seg_x = positions[i]
    seg_w = positions[i + 1] - positions[i]
    col = lerp(GOLD_RGB, NAVY_RGB, i / float(len(points) - 2))
    rect(s4, seg_x, LINE_Y - 0.035, seg_w, 0.07, col,
         shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.5)

for i, (day, label, name, note, color) in enumerate(points):
    px = positions[i]
    above = (i % 2 == 0)
    # connector
    if above:
        rect(s4, px - 0.012, LINE_Y - 0.72, 0.024, 0.72, RGBColor(0xDD, 0xE6, 0xEF))
    else:
        rect(s4, px - 0.012, LINE_Y, 0.024, 0.72, RGBColor(0xDD, 0xE6, 0xEF))
    # node
    rect(s4, px - 0.13, LINE_Y - 0.13, 0.26, 0.26, WHITE, shape=MSO_SHAPE.OVAL,
         line=color, lw=2.5)
    rect(s4, px - 0.065, LINE_Y - 0.065, 0.13, 0.13, color, shape=MSO_SHAPE.OVAL)

    bw = 1.72
    bx = min(max(px - bw / 2, 0.30), SLIDE_W - bw - 0.30)
    if above:
        by = LINE_Y - 1.52
    else:
        by = LINE_Y + 0.30
    tx(s4, bx, by, bw, 0.24, label, size=9.5, bold=True, color=color,
       align=PP_ALIGN.CENTER)
    tx(s4, bx, by + 0.26, bw, 0.26, name, size=10.5, bold=True, color=NAVY,
       align=PP_ALIGN.CENTER)
    tx(s4, bx, by + 0.53, bw, 0.24, note, size=8.5, color=GRAY,
       align=PP_ALIGN.CENTER)

# ---- bottom note
rect(s4, 0.5, 6.42, 12.33, 0.62, RGBColor(0xFD, 0xF6, 0xE6),
     shape=MSO_SHAPE.ROUNDED_RECTANGLE, line=RGBColor(0xF2, 0xD9, 0xA5), lw=1.0, radius=0.16)
tx(s4, 0.78, 6.53, 11.8, 0.44,
   "Dataset collection and labeling \u2014 the largest single block \u2014 is already complete.  "
   "Model training is the critical path (~30 days); the MERN dashboard runs in parallel from day 12 "
   "and is ready by day 40.",
   size=10, bold=True, color=RGBColor(0x8A, 0x62, 0x14))

# ---------------------------------------------------------------- save
out = r"C:\Btech Project Important Files\Timeline\Project_Progress_Presentation.pptx"
os.makedirs(os.path.dirname(out), exist_ok=True)
prs.save(out)
print("SAVED:", out)
