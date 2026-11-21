from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE
import os

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)

DARK_BLUE = RGBColor(0x1A, 0x3C, 0x5E)
MEDIUM_BLUE = RGBColor(0x2D, 0x5A, 0x87)
LIGHT_BLUE = RGBColor(0x4A, 0x6F, 0xA5)
ACCENT_GOLD = RGBColor(0xE8, 0xA8, 0x38)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT_GRAY = RGBColor(0xF0, 0xF0, 0xF0)
DARK_GRAY = RGBColor(0x33, 0x33, 0x33)

def add_tb(slide, left, top, width, height, text, size=18, bold=False, color=WHITE, align=PP_ALIGN.LEFT):
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(size)
    p.font.bold = bold
    p.font.color.rgb = color
    p.font.name = 'Calibri'
    p.alignment = align
    return txBox

# SLIDE 1
slide1 = prs.slides.add_slide(prs.slide_layouts[6])
bg = slide1.background
bg.fill.solid()
bg.fill.fore_color.rgb = DARK_BLUE
sh = slide1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(0.15))
sh.fill.solid()
sh.fill.fore_color.rgb = ACCENT_GOLD
sh.line.fill.background()
txBox = slide1.shapes.add_textbox(Inches(1), Inches(1.2), Inches(11.333), Inches(1.5))
tf = txBox.text_frame
tf.word_wrap = True
p = tf.paragraphs[0]
p.text = 'AI-BASED ILLEGAL SAND MINING DETECTION AND RISK PRIORITIZATION SYSTEM\nON YAMUNA RIVER'
p.font.size = Pt(36)
p.font.bold = True
p.font.color.rgb = WHITE
p.font.name = 'Calibri'
p.alignment = PP_ALIGN.CENTER
sh = slide1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(4.5), Inches(2.9), Inches(4.333), Inches(0.04))
sh.fill.solid()
sh.fill.fore_color.rgb = ACCENT_GOLD
sh.line.fill.background()
txBox = slide1.shapes.add_textbox(Inches(1), Inches(3.1), Inches(11.333), Inches(0.8))
tf = txBox.text_frame
tf.word_wrap = True
p = tf.paragraphs[0]
p.text = 'BTech Final Year Project | Department of Computer Science & Engineering'
p.font.size = Pt(20)
p.font.color.rgb = RGBColor(0xBB,0xCC,0xDD)
p.font.name = 'Calibri'
p.alignment = PP_ALIGN.CENTER
ib = slide1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(2.5), Inches(4.2), Inches(8.333), Inches(2.2))
ib.fill.solid()
ib.fill.fore_color.rgb = RGBColor(0x15,0x2D,0x4A)
ib.line.color.rgb = ACCENT_GOLD
ib.line.width = Pt(2)
add_tb(slide1, Inches(3), Inches(4.4), Inches(7.333), Inches(0.5), 'GROUP NUMBER: [GROUP NO.]', 18, True, ACCENT_GOLD, PP_ALIGN.CENTER)
add_tb(slide1, Inches(3), Inches(4.9), Inches(7.333), Inches(0.5), 'TEAM MEMBERS:', 16, True, WHITE, PP_ALIGN.LEFT)
add_tb(slide1, Inches(3.5), Inches(5.3), Inches(6.333), Inches(0.4), '[Member 1 Name] - [Roll No.]     |     [Member 2 Name] - [Roll No.]     |     [Member 3 Name] - [Roll No.]', 14, False, RGBColor(0xCC,0xCC,0xCC), PP_ALIGN.LEFT)
add_tb(slide1, Inches(3), Inches(5.8), Inches(7.333), Inches(0.5), 'PROJECT SUPERVISOR: [SUPERVISOR NAME] - [DESIGNATION]', 16, True, RGBColor(0xBB,0xCC,0xDD), PP_ALIGN.CENTER)
sh = slide1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(7.35), Inches(13.333), Inches(0.15))
sh.fill.solid()
sh.fill.fore_color.rgb = ACCENT_GOLD
sh.line.fill.background()
add_tb(slide1, Inches(1), Inches(7.0), Inches(11.333), Inches(0.5), 'BTech Final Year Project | Department of Computer Science & Engineering | Academic Year 2025-26', 12, False, RGBColor(0x88,0x99,0xAA), PP_ALIGN.CENTER)

# SLIDE 2
slide2 = prs.slides.add_slide(prs.slide_layouts[6])
bg = slide2.background
bg.fill.solid()
bg.fill.fore_color.rgb = WHITE
sh = slide2.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(1.1))
sh.fill.solid()
sh.fill.fore_color.rgb = DARK_BLUE
sh.line.fill.background()
txBox = slide2.shapes.add_textbox(Inches(0.5), Inches(0.2), Inches(12.333), Inches(0.7))
tf = txBox.text_frame
tf.word_wrap = True
p = tf.paragraphs[0]
p.text = 'PROGRESS SO FAR'
p.font.size = Pt(36)
p.font.bold = True
p.font.color.rgb = WHITE
p.font.name = 'Calibri'
p.alignment = PP_ALIGN.LEFT
sh = slide2.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.5), Inches(0.9), Inches(3), Inches(0.06))
sh.fill.solid()
sh.fill.fore_color.rgb = ACCENT_GOLD
sh.line.fill.background()
shape = slide2.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(10.5), Inches(0.2), Inches(2.5), Inches(0.7))
shape.fill.solid()
shape.fill.fore_color.rgb = ACCENT_GOLD
shape.line.fill.background()
txBox = slide2.shapes.add_textbox(Inches(10.5), Inches(0.25), Inches(2.5), Inches(0.7))
tf = txBox.text_frame
tf.word_wrap = True
p = tf.paragraphs[0]
p.text = '75% COMPLETE'
p.font.size = Pt(24)
p.font.bold = True
p.font.color.rgb = DARK_BLUE
p.font.name = 'Calibri'
p.alignment = PP_ALIGN.CENTER

lit_box = slide2.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.5), Inches(1.4), Inches(5.9), Inches(5.5))
lit_box.fill.solid()
lit_box.fill.fore_color.rgb = LIGHT_GRAY
lit_box.line.color.rgb = MEDIUM_BLUE
lit_box.line.width = Pt(1.5)
txBox = slide2.shapes.add_textbox(Inches(0.7), Inches(1.5), Inches(5.5), Inches(0.5))
tf = txBox.text_frame
tf.word_wrap = True
p = tf.paragraphs[0]
p.text = 'LITERATURE REVIEW'
p.font.size = Pt(22)
p.font.bold = True
p.font.color.rgb = DARK_BLUE
p.font.name = 'Calibri'

lit_items = [
    '✓  LMS Net (Zhang et al., 2025) - Lightweight Multi-Scale Network for riverbank detection (98.07% accuracy, 1/10th U-Net params)',
    '✓  Morphometric Analysis of Sutlej River (Kaur et al., 2025) - 23-year time series, channel width variation, bank shift 8.6m, erosion 2,263 ha',
    '✓  GIS Flood Vulnerability + AHP/ML (Nair et al., 2025) - 8 conditioning parameters, AUC-ROC >0.93',
    '✓  India-Specific Sandbank Detection (IIT Kharagpur) - Spectral indices NDVI, NDWI, NDBI, NDSI for sandbank detection',
    '✓  20+ papers reviewed across CV, GIS, Hydrology domains',
    '✓  Research gap identified: No integrated detection + risk prioritization system for Indian rivers'
]
y_pos = 2.1
for item in lit_items:
    txBox = slide2.shapes.add_textbox(Inches(0.8), Inches(y_pos), Inches(5.5), Inches(0.5))
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = item
    p.font.size = Pt(12)
    p.font.color.rgb = DARK_GRAY
    p.font.name = 'Calibri'
    y_pos += 0.45

code_box = slide2.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(6.8), Inches(1.4), Inches(6), Inches(5.5))
code_box.fill.solid()
code_box.fill.fore_color.rgb = LIGHT_GRAY
code_box.line.color.rgb = ACCENT_GOLD
code_box.line.width = Pt(1.5)
txBox = slide2.shapes.add_textbox(Inches(7), Inches(1.5), Inches(5.5), Inches(0.5))
tf = txBox.text_frame
tf.word_wrap = True
p = tf.paragraphs[0]
p.text = 'CODING & IMPLEMENTATION'
p.font.size = Pt(22)
p.font.bold = True
p.font.color.rgb = DARK_BLUE
p.font.name = 'Calibri'

code_items = [
    '✓  Data Pipeline: Sentinel-2 (10m, 14-band), Sentinel-1 SAR, Landsat-8 thermal -> 29 composites (2018-2024)',
    '✓  Centerline Extraction: Sentinel-1 VV Otsu thresholding -> 50.21 km centerline (Palla->Jaitpur)',
    '✓  Transect Generation: 51 perpendicular transects @ 1km spacing, 3km length each',
    '✓  Chip Extraction: 42 chips (256x256, 14-band) from 2023 Q2 Sentinel-2 composite',
    '✓  Multi-temporal Extraction: 6 quarters (2023 Q1-Q4, 2024 Q1-Q2) -> 252 S2 + 252 S1 chips',
    '✓  Index Verification: 5-check validation (band layout, recompute vs stored, CSV means, distribution, visual)',
    '✓  Band Mapping Diagnostic: Root cause found - band order bug (B8 at pos 4 instead of 7)',
    '✓  MERN Stack: React frontend, Node/Express backend, MongoDB for labeling metadata',
    '✓  Labeling Pipeline: 42 chips -> manifest, guidelines (MINING/NOT MINING/UNSURE), agreement log'
]
y_pos = 2.1
for item in code_items:
    txBox = slide2.shapes.add_textbox(Inches(7.1), Inches(y_pos), Inches(5.7), Inches(0.45))
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = item
    p.font.size = Pt(11)
    p.font.color.rgb = DARK_GRAY
    p.font.name = 'Calibri'
    y_pos += 0.42

shape = slide2.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.5), Inches(7.1), Inches(12.333), Inches(0.15))
shape.fill.solid()
shape.fill.fore_color.rgb = MEDIUM_BLUE
shape.line.fill.background()
txBox = slide2.shapes.add_textbox(Inches(0.5), Inches(7.1), Inches(12.333), Inches(0.4))
tf = txBox.text_frame
tf.word_wrap = True
p = tf.paragraphs[0]
p.text = 'OVERALL PROGRESS: 75%  |  Data Pipeline: 100%  |  CV Pipeline: 60%  |  MERN Dashboard: 40%  |  Labeling: 30%'
p.font.size = Pt(14)
p.font.bold = True
p.font.color.rgb = WHITE
p.font.name = 'Calibri'
p.alignment = PP_ALIGN.CENTER

# SLIDE 3
slide3 = prs.slides.add_slide(prs.slide_layouts[6])
bg = slide3.background
bg.fill.solid()
bg.fill.fore_color.rgb = WHITE
sh = slide3.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(1.1))
sh.fill.solid()
sh.fill.fore_color.rgb = DARK_BLUE
sh.line.fill.background()
txBox = slide3.shapes.add_textbox(Inches(0.5), Inches(0.2), Inches(12.333), Inches(0.7))
tf = txBox.text_frame
tf.word_wrap = True
p = tf.paragraphs[0]
p.text = 'TASKS LEFT TO BE DONE'
p.font.size = Pt(36)
p.font.bold = True
p.font.color.rgb = WHITE
p.font.name = 'Calibri'
p.alignment = PP_ALIGN.LEFT
sh = slide3.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.5), Inches(0.9), Inches(3), Inches(0.06))
sh.fill.solid()
sh.fill.fore_color.rgb = ACCENT_GOLD
sh.line.fill.background()

cols = [
    ('IMMEDIATE (Weeks 1-3)', ACCENT_GOLD, [
        '1. Re-download Sentinel-2 zip files (~45 GB)',
        '2. Fix S2_SPECTRAL_BANDS order in extract_yamuna_data.py (Line 99)',
        '3. Rebuild all Sentinel-2 composites (6 quarters x 2 years = 12 composites)',
        '4. Re-run index verification (script 08)',
        '5. Verify band order: B2,B3,B4,B5,B6,B7,B8,B8A,B11,B12'
    ]),
    ('SHORT-TERM (Weeks 4-6)', MEDIUM_BLUE, [
        '1. Manual labeling: 42 chips x 2 reviewers -> MINING/NOT MINING/UNSURE',
        '2. Inter-rater agreement analysis',
        '3. Resolve disagreements -> supervisor sign-off',
        '4. Train baseline models: RF/XGBoost on 14-band chips',
        '5. Build S2+S1 paired dataset'
    ]),
    ('MEDIUM-TERM (Weeks 7-10)', LIGHT_BLUE, [
        '1. Temporal change detection: 2018 vs 2024 annual composites',
        '2. Multi-temporal model: 6-quarter temporal stack',
        '3. S2+S1 fusion model: SAR-optical late fusion',
        '4. Temporal change maps for 6 quarters',
        '5. MERN Dashboard: Risk map visualization, chip browser, labeling interface'
    ])
]

for i, (title, color, tasks) in enumerate(cols):
    x_pos = Inches(0.5) + i * (Inches(4) + Inches(0.3))
    header_box = slide3.shapes.add_shape(MSO_SHAPE.RECTANGLE, x_pos, Inches(1.4), Inches(4), Inches(0.6))
    header_box.fill.solid()
    header_box.fill.fore_color.rgb = color
    header_box.line.fill.background()
    txBox = slide3.shapes.add_textbox(x_pos, Inches(1.45), Inches(4), Inches(0.5))
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = title
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = WHITE
    p.font.name = 'Calibri'
    p.alignment = PP_ALIGN.CENTER
    y_pos = 2.2
    for task in tasks:
        txBox = slide3.shapes.add_textbox(x_pos + Inches(0.2), Inches(y_pos), Inches(4) - Inches(0.4), Inches(0.7))
        tf = txBox.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = task
        p.font.size = Pt(12)
        p.font.color.rgb = DARK_GRAY
        p.font.name = 'Calibri'
        y_pos += 0.55

shape = slide3.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.5), Inches(5.2), Inches(12.333), Inches(1.8))
shape.fill.solid()
shape.fill.fore_color.rgb = LIGHT_GRAY
shape.line.fill.background()
txBox = slide3.shapes.add_textbox(Inches(0.7), Inches(5.3), Inches(12), Inches(0.4))
tf = txBox.text_frame
tf.word_wrap = True
p = tf.paragraphs[0]
p.text = 'CROSS-CUTTING / ONGOING'
p.font.size = Pt(20)
p.font.bold = True
p.font.color.rgb = DARK_BLUE
p.font.name = 'Calibri'

cross_items = [
    '□  Bi-weekly supervisor meetings & progress documentation in PROJECT_LOG.md',
    '□  Weekly code commits with descriptive messages (GitHub)',
    '□  Monthly model performance benchmarking (F1, IoU, precision/recall per class)',
    '□  Draft conference paper (target: ICVGIP / CVPR-W / Remote Sensing journal)',
    '□  Ethical clearance for field validation (if ground truth collection needed)',
    '□  Final thesis writing & defense preparation (weeks 11-12)'
]
y_pos = 5.8
for item in cross_items:
    txBox = slide3.shapes.add_textbox(Inches(0.8), Inches(y_pos), Inches(12), Inches(0.35))
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = item
    p.font.size = Pt(12)
    p.font.color.rgb = DARK_GRAY
    p.font.name = 'Calibri'
    y_pos += 0.3

# SLIDE 4
slide4 = prs.slides.add_slide(prs.slide_layouts[6])
bg = slide4.background
bg.fill.solid()
bg.fill.fore_color.rgb = WHITE
sh = slide4.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(1.1))
sh.fill.solid()
sh.fill.fore_color.rgb = DARK_BLUE
sh.line.fill.background()
txBox = slide4.shapes.add_textbox(Inches(0.5), Inches(0.2), Inches(12.333), Inches(0.7))
tf = txBox.text_frame
tf.word_wrap = True
p = tf.paragraphs[0]
p.text = 'EXPECTED TIMELINE OF PROJECT COMPLETION'
p.font.size = Pt(36)
p.font.bold = True
p.font.color.rgb = WHITE
p.font.name = 'Calibri'
p.alignment = PP_ALIGN.LEFT
sh = slide4.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.5), Inches(0.9), Inches(3), Inches(0.06))
sh.fill.solid()
sh.fill.fore_color.rgb = ACCENT_GOLD
sh.line.fill.background()

weeks = [
    ('Week 1-2', 'Rebuild Composites', 'Re-download zips, fix band order, rebuild 12 composites, verify', ACCENT_GOLD),
    ('Week 3-4', 'Labeling Sprint', 'Manual labeling (42 chips x 2 reviewers), agreement analysis, supervisor sign-off', ACCENT_GOLD),
    ('Week 5-6', 'Baseline Models', 'RF/XGBoost on 14-band chips, spatial split, train/eval, metrics', MEDIUM_BLUE),
    ('Week 5-6', 'S2+S1 Paired Data', 'Pair S2+S1 chips at same transect points, create fusion dataset', MEDIUM_BLUE),
    ('Week 7-8', 'Change Detection', '2018 vs 2024 annual diff maps, 6-quarter temporal stack, change maps', MEDIUM_BLUE),
    ('Week 8-9', 'Fusion Models', 'S2+S1 late fusion, temporal change head, U-Net segmentation', LIGHT_BLUE),
    ('Week 9-10', 'MERN Dashboard', 'React frontend, Node/Express API, chip browser, risk map viz', LIGHT_BLUE),
    ('Week 10-11', 'Integration & Testing', 'End-to-end pipeline, risk scoring, stress testing', RGBColor(0x6A, 0xA5, 0x4A)),
    ('Week 11-12', 'Thesis & Defense', 'Final report, conference paper draft, defense prep', RGBColor(0x6A, 0xA5, 0x4A)),
]

for i, (period, task, desc, color) in enumerate(weeks):
    y = 1.5 + i * 0.55
    shape = slide4.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.5), Inches(y), Inches(1.8), Inches(0.45))
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    shape.line.fill.background()
    txBox = slide4.shapes.add_textbox(Inches(0.5), Inches(y + 0.05), Inches(1.8), Inches(0.4))
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = period
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = WHITE
    p.font.name = 'Calibri'
    p.alignment = PP_ALIGN.CENTER
    txBox = slide4.shapes.add_textbox(Inches(2.5), Inches(y + 0.05), Inches(2.5), Inches(0.4))
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = task
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = color
    p.font.name = 'Calibri'
    txBox = slide4.shapes.add_textbox(Inches(5.2), Inches(y + 0.05), Inches(7.5), Inches(0.4))
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = desc
    p.font.size = Pt(11)
    p.font.color.rgb = DARK_GRAY
    p.font.name = 'Calibri'
    shape = slide4.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(5.2), Inches(y + 0.25), Inches(7.5), Inches(0.15))
    shape.fill.solid()
    shape.fill.fore_color.rgb = LIGHT_GRAY
    shape.line.fill.background()
    progress_widths = [0.15, 0.05, 0.1, 0.1, 0.05, 0.0, 0.0, 0.0, 0.0]
    if i < len(progress_widths):
        pw = progress_widths[i]
        if pw > 0:
            shape = slide4.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(5.2), Inches(y + 0.25), Inches(7.5 * pw), Inches(0.15))
            shape.fill.solid()
            shape.fill.fore_color.rgb = color
            shape.line.fill.background()

milestones = [
    (Inches(0.5), Inches(1.4), 'TODAY'),
    (Inches(0.5), Inches(1.4 + 2*0.55), 'COMPOSITES READY'),
    (Inches(0.5), Inches(1.4 + 4*0.55), 'LABELING DONE'),
    (Inches(0.5), Inches(1.4 + 6*0.55), 'BASELINE READY'),
    (Inches(0.5), Inches(1.4 + 8*0.55), 'DASHBOARD MVP'),
    (Inches(0.5), Inches(1.4 + 9*0.55), 'DEFENSE READY'),
]
for x, y, label in milestones:
    txBox = slide4.shapes.add_textbox(x, y, Inches(1.8), Inches(0.3))
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = label
    p.font.size = Pt(9)
    p.font.bold = True
    p.font.color.rgb = ACCENT_GOLD
    p.font.name = 'Calibri'
    p.alignment = PP_ALIGN.CENTER

shape = slide4.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(7.0), Inches(13.333), Inches(0.5))
shape.fill.solid()
shape.fill.fore_color.rgb = DARK_BLUE
shape.line.fill.background()
txBox = slide4.shapes.add_textbox(Inches(0.5), Inches(7.05), Inches(12.333), Inches(0.4))
tf = txBox.text_frame
tf.word_wrap = True
p = tf.paragraphs[0]
p.text = 'TOTAL: 12 WEEKS  |  START: WEEK 1 (REBUILD)  ->  END: WEEK 12 (THESIS DEFENSE)  |  MILESTONES: 6 MAJOR CHECKPOINTS'
p.font.size = Pt(14)
p.font.bold = True
p.font.color.rgb = WHITE
p.font.name = 'Calibri'
p.alignment = PP_ALIGN.CENTER

output_path = r'C:\Btech Project Important Files\Timeline\Project_Progress_Presentation.pptx'
os.makedirs(os.path.dirname(output_path), exist_ok=True)
prs.save(output_path)
print('PPT saved to: ' + output_path)
print('Done!')

