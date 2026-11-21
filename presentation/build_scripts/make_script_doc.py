# -*- coding: utf-8 -*-
"""Builds the presentation script / reasoning document and injects speaker notes into the PPTX."""
import os
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.section import WD_SECTION
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

OUT_DOC = r"C:\Btech Project Important Files\Timeline\Presentation_Script_and_Reasoning.docx"
PPTX = r"C:\Btech Project Important Files\Timeline\Project_Progress_Presentation.pptx"

NAVY = RGBColor(0x0E, 0x2A, 0x47)
GOLD = RGBColor(0xB8, 0x86, 0x2B)
GREY = RGBColor(0x55, 0x5F, 0x6B)

doc = Document()

# ---------------------------------------------------------------- base styles
st = doc.styles["Normal"]
st.font.name = "Calibri"
st.font.size = Pt(11)
st.paragraph_format.space_after = Pt(6)
st.paragraph_format.line_spacing = 1.12

for nm, sz, col in (("Heading 1", 18, NAVY), ("Heading 2", 14, NAVY), ("Heading 3", 12, GOLD)):
    s = doc.styles[nm]
    s.font.name = "Calibri"
    s.font.size = Pt(sz)
    s.font.bold = True
    s.font.color.rgb = col
    s.paragraph_format.space_before = Pt(14 if nm == "Heading 1" else 10)
    s.paragraph_format.space_after = Pt(6)

sec = doc.sections[0]
sec.top_margin = Inches(0.8)
sec.bottom_margin = Inches(0.8)
sec.left_margin = Inches(0.9)
sec.right_margin = Inches(0.9)


# ---------------------------------------------------------------- helpers
def shade(par, hexfill):
    pPr = par._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hexfill)
    pPr.append(shd)


def h1(t):
    doc.add_heading(t, level=1)


def h2(t):
    doc.add_heading(t, level=2)


def h3(t):
    doc.add_heading(t, level=3)


def p(text, bold=False, italic=False, size=None, color=None, space_after=None):
    par = doc.add_paragraph()
    r = par.add_run(text)
    r.bold = bold
    r.italic = italic
    if size:
        r.font.size = Pt(size)
    if color:
        r.font.color.rgb = color
    if space_after is not None:
        par.paragraph_format.space_after = Pt(space_after)
    return par


def rich(parts, space_after=None):
    """parts = [(text, bold, italic), ...]"""
    par = doc.add_paragraph()
    for text, bold, italic in parts:
        r = par.add_run(text)
        r.bold = bold
        r.italic = italic
    if space_after is not None:
        par.paragraph_format.space_after = Pt(space_after)
    return par


def bullet(text, level=0):
    par = doc.add_paragraph(style="List Bullet")
    par.paragraph_format.left_indent = Inches(0.25 + 0.25 * level)
    par.paragraph_format.space_after = Pt(3)
    r = par.add_run(text)
    return par


def bullet_rich(lead, rest, level=0):
    par = doc.add_paragraph(style="List Bullet")
    par.paragraph_format.left_indent = Inches(0.25 + 0.25 * level)
    par.paragraph_format.space_after = Pt(3)
    r1 = par.add_run(lead)
    r1.bold = True
    par.add_run(rest)
    return par


def numbered(text):
    par = doc.add_paragraph(style="List Number")
    par.paragraph_format.space_after = Pt(3)
    par.add_run(text)
    return par


def script(text):
    """What to actually say - shaded block."""
    par = doc.add_paragraph()
    par.paragraph_format.left_indent = Inches(0.18)
    par.paragraph_format.right_indent = Inches(0.1)
    par.paragraph_format.space_before = Pt(4)
    par.paragraph_format.space_after = Pt(10)
    r = par.add_run(text)
    r.italic = True
    r.font.size = Pt(10.5)
    r.font.color.rgb = RGBColor(0x1A, 0x33, 0x4D)
    shade(par, "EEF3F8")
    return par


def callout(label, text):
    par = doc.add_paragraph()
    par.paragraph_format.left_indent = Inches(0.18)
    par.paragraph_format.space_before = Pt(4)
    par.paragraph_format.space_after = Pt(8)
    r1 = par.add_run(label + "  ")
    r1.bold = True
    r1.font.size = Pt(10)
    r1.font.color.rgb = GOLD
    r2 = par.add_run(text)
    r2.font.size = Pt(10)
    shade(par, "FDF6E6")
    return par


def table(headers, rows, widths=None, font=9):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    hdr = t.rows[0].cells
    for i, htxt in enumerate(headers):
        hdr[i].text = ""
        par = hdr[i].paragraphs[0]
        r = par.add_run(htxt)
        r.bold = True
        r.font.size = Pt(font)
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        sh = OxmlElement("w:shd")
        sh.set(qn("w:val"), "clear")
        sh.set(qn("w:fill"), "0E2A47")
        hdr[i]._tc.get_or_add_tcPr().append(sh)
    for row in rows:
        cells = t.add_row().cells
        for i, val in enumerate(row):
            cells[i].text = ""
            par = cells[i].paragraphs[0]
            r = par.add_run(str(val))
            r.font.size = Pt(font)
    if widths:
        for r_ in t.rows:
            for i, w in enumerate(widths):
                r_.cells[i].width = Inches(w)
    doc.add_paragraph().paragraph_format.space_after = Pt(4)
    return t


# ================================================================ COVER
tp = doc.add_paragraph()
tp.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = tp.add_run("PRESENTATION SCRIPT & TECHNICAL JUSTIFICATION")
r.bold = True
r.font.size = Pt(20)
r.font.color.rgb = NAVY

sp = doc.add_paragraph()
sp.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = sp.add_run("AI-Based Illegal Sand Mining Detection and Risk Prioritization System on Yamuna River")
r.font.size = Pt(12.5)
r.italic = True

sp = doc.add_paragraph()
sp.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = sp.add_run("Group 162  |  Department of Information Technology, Delhi Technological University")
r.font.size = Pt(10)
r.font.color.rgb = GREY

table(
    ["Item", "Detail"],
    [
        ["Presenters", "Upendra Kumar (23/IT/165), Somya Tripathi (23/IT/162)"],
        ["Supervisor", "Dr. Anita Thakur"],
        ["Deck", "Project_Progress_Presentation.pptx (4 slides)"],
        ["Speaking time", "9-10 minutes + 3-4 minutes Q&A"],
        ["Hard constraint", "45 days remaining"],
        ["Status claimed", "55% complete"],
    ],
    widths=[1.5, 4.9],
)

callout("HOW TO USE THIS",
        "Each slide has three parts: (1) the exact words to say, (2) the reasoning behind every claim on the "
        "slide so you can defend it, (3) the questions you will most likely get. Read the script once, then "
        "present from the reasoning - never memorise the script word for word.")

# ================================================================ 0 TIMING
h1("0.  Timing plan")

table(
    ["Slide", "Content", "Time", "What the panel must walk away believing"],
    [
        ["1", "Title, team, supervisor", "1:00", "You know the problem and why it matters."],
        ["2", "Progress: literature + code + 55%", "4:00", "The hard work is already done and it is verifiable."],
        ["3", "Tasks left", "2:30", "You know exactly what remains and why in that order."],
        ["4", "45-day timeline", "1:30", "The plan fits the deadline and you understand the risk."],
    ],
    widths=[0.55, 2.5, 0.6, 2.8],
)

p("Rule of thumb for the review: they care about three things - is the data real, is the reasoning sound, "
  "and will it finish in time. Slide 2 answers the first two, slide 4 answers the third.")

# ================================================================ SLIDE 1
h1("1.  Slide 1 - Title")

h2("1.1  What to say")
script(
    "Good morning. I am Upendra Kumar, and this is Somya Tripathi. We are Group 162 from the Department of "
    "Information Technology, and our project is supervised by Dr. Anita Thakur.\n\n"
    "Our project is the AI-Based Illegal Sand Mining Detection and Risk Prioritization System on the Yamuna River.\n\n"
    "Let me start with why this problem is worth a final-year project. Sand is the most consumed solid material "
    "on earth after water. The Yamuna's 52-kilometre Delhi stretch is under a complete legal ban - Supreme Court "
    "and National Green Tribunal orders - and yet extraction continues, because enforcement runs on manual "
    "patrols over a stretch that cannot be physically watched every day.\n\n"
    "Satellite imagery already covers that stretch every five days and it is free. What does not exist is the "
    "layer that converts those pixels into an enforcement decision: which segment, how severe, and in what order "
    "to act. That conversion layer is our project.\n\n"
    "Today I will cover three things: what we have completed, what remains, and how the remaining 45 days are planned."
)

h2("1.2  Why each element is on the slide")
bullet_rich("Department of Information Technology - ", "state it once, correctly; it is the only place the panel checks identity.")
bullet_rich("Two team members with roll numbers - ", "lets the panel map effort to people; a two-person team is why slide 4 relies on parallel tracks.")
bullet_rich("Supervisor name only, no designation - ", "the panel already knows the designation; including it looks like padding.")
bullet_rich("Title exactly as in the synopsis - ", "any drift in the title reads as a scope change, which invites questions you do not want.")
bullet_rich("Group 162 - ", "administrative requirement; wrong number invalidates the submission record.")

h2("1.3  Why the opening mentions 'enforcement decision'")
p("This single phrase sets up the entire architecture. If the problem were only detection, a segmentation model "
  "would be enough and the project would be half its size. Because the problem is prioritization, the project "
  "needs a risk score, which needs morphology change metrics, which is why two of the four papers are about "
  "change and risk rather than about segmentation. Say it early so slides 2 and 3 feel inevitable.")

# ================================================================ SLIDE 2
h1("2.  Slide 2 - Progress so far")

h2("2.1  What to say")
script(
    "We are reporting 55 percent completion. I want to justify that number rather than assert it, because it is "
    "the one number the panel will challenge.\n\n"
    "We split the project into five blocks: data engineering, label set, models, dashboard and reporting. We "
    "weighted them by expected effort - 55, 30, 10 and 5 percent - because in any remote-sensing machine-learning "
    "project, acquisition and preparation dominate. The first block is finished end to end, the other three have "
    "not started in earnest. So the honest number is the weight of the block we closed: 55 percent.\n\n"
    "'Finished end to end' means concretely: twenty-nine analysis-ready composites spanning 2018 to 2024, a "
    "50.21-kilometre river centreline extracted from Sentinel-1, fifty-one sampling transects, forty-two "
    "validated 14-band chips, a 252-chip multi-temporal stack across six quarters, four spectral index rasters, "
    "a five-check verification suite, and a labeling protocol with a manifest ready for review.\n\n"
    "On the left is the literature that shaped the design. On the right is the code that produced those numbers."
)

p("Then walk the panel through the two columns quickly - do not read every line. Point at three papers and two "
  "scripts, and let the slide carry the rest.", italic=True)

# ---- 2.2 the 55%
h2("2.2  How the 55% is justified (be ready to defend it)")
p("If asked 'why 55 and not 40 or 70', give this reasoning - it is auditable, which is what matters:")
table(
    ["Block", "Weight", "Status", "Concrete evidence"],
    [
        ["Data engineering + label set", "55%", "COMPLETE",
         "29 composites, 50.21 km centreline, 51 transects, 42 chips, 252-chip stack, 4 index rasters, verification suite passing"],
        ["Detection & risk models", "30%", "Not started",
         "Depends on final labels - Task 01 on slide 3"],
        ["MERN dashboard", "10%", "Not started",
         "Can start from mock data once the API contract is fixed"],
        ["Reporting & defense", "5%", "Not started", "Paper draft, thesis, defense"],
    ],
    widths=[2.2, 0.7, 1.0, 2.6],
)
callout("SAY THIS IF PRESSED",
        "The weighting is not arbitrary - acquisition, cloud masking, mosaicking, georeferencing, tiling and "
        "quality checking are typically two-thirds of the work in a remote-sensing ML project. We finished that "
        "and we deliberately did not claim credit for planning the models.")

# ---- 2.3 papers
h2("2.3  The four papers - what each says, why we chose it, what we took")

h3("Paper 1  -  Zhang, Liu & Liu (2025), Remote Sensing 17(2):227  |  LMS-Net")
bullet_rich("What it does: ", "a lightweight multi-scale segmentation network for riverbank sand mining areas in "
            "satellite images. Reports 98.07% accuracy with roughly one-tenth the parameters of U-Net.")
bullet_rich("Why we chose it: ", "three reasons, in order of importance. First, its label definition is identical "
            "to ours - 'riverbank sand mining area', not generic land cover - so its evaluation protocol is "
            "directly reusable. Second, our problem statement explicitly demands a model that is lightweight and "
            "deployable on standard devices; this paper is the current state of the art built for exactly that "
            "constraint. Third, its multi-scale design addresses the real difficulty in our data: mining patches "
            "range from small pits to kilometre-long bars, so a single receptive field will miss one end of that range.")
bullet_rich("What we take from it: ", "the multi-scale backbone idea, and the accuracy-versus-parameters "
            "trade-off as our benchmark target. If our model lands near 98% at a fraction of U-Net parameters, "
            "we can say we reproduced a published result on a new river.")
bullet_rich("What we do not take: ", "their trained weights. Different sensor, different river, different "
            "season. We reuse the architecture and the evaluation method, not the model.")

h3("Paper 2  -  Kaur, Gani, Pathak & Tiwari (2025), Env. Geochemistry & Health 47(11):459  |  Sutlej morphometry")
bullet_rich("What it does: ", "a 23-year multi-temporal morphometric analysis of mining-induced change on the "
            "Sutlej - channel width variation, lateral bank shift of 8.6 m, erosion of 2,263 ha against "
            "deposition of 1,562 ha.")
bullet_rich("Why we chose it: ", "because our project has two halves and this paper supplies the second one. "
            "Detection alone gives a probability; risk needs a physical quantity. This paper defines those "
            "quantities - bank shift, width change, erosion and deposition area - and shows how to measure them "
            "from a satellite time series without fieldwork. The second reason is geographic: the Sutlej is a "
            "Himalayan-fed, monsoonal, sand-bed river like the Yamuna. Sediment regime, bar behaviour and "
            "seasonal exposure all transfer. A study on the Amazon or the Mississippi would give us methods but "
            "not comparable numbers.")
bullet_rich("What we take from it: ", "the change-metric definitions and the annual-composite comparison design, "
            "plus its published magnitudes as a sanity band for our own outputs.")
bullet_rich("What we do not take: ", "its discharge-based calibration - we have no gauge data for the Delhi "
            "stretch, so our change metrics are image-derived only, and we say so as a limitation.")

h3("Paper 3  -  Nair et al. (2025), Geocarto International 40(1):2551261  |  AHP + ML risk mapping")
bullet_rich("What it does: ", "combines Analytical Hierarchy Process weighting with eight machine-learning "
            "algorithms over eight conditioning parameters - rainfall, elevation, slope, drainage density, "
            "distance from river, topographic wetness index, land use, soil type - reaching AUC-ROC above 0.93.")
bullet_rich("Why we chose it: ", "this is our prioritization blueprint, and we would rather adapt a validated "
            "method than invent one. Three specific fits. All eight parameters are derivable from free and open "
            "data, which matters because we have no survey budget. The paper reports that the AHP-plus-ML hybrid "
            "outperforms either component alone, which is precisely the justification for our hybrid design - "
            "expert weights for interpretability, learned calibration for accuracy. And an AUC above 0.93 sets a "
            "defensible target for our own risk model.")
bullet_rich("What we take from it: ", "the parameter set, the AHP weighting procedure and the hybrid evaluation "
            "approach.")
bullet_rich("What we do not take: ", "its target variable. It predicts flood vulnerability; we predict mining "
            "intensity and change severity. The scoring machinery transfers, the label does not.")

h3("Paper 4  -  India-specific multispectral sandbank detection study (JIIT Noida)")
bullet_rich("What it does: ", "develops India-calibrated spectral indices - NDVI, NDWI, NDBI, NDSI - for "
            "separating riverbank sand from water, vegetation and built-up surface.")
bullet_rich("Why we chose it: ", "two reasons, and the second is the one that matters for our schedule. First, "
            "index thresholds are sensor- and atmosphere-dependent. Global thresholds taken from non-Indian "
            "studies misclassify Indian river sand because sediment mineralogy, surface moisture and atmospheric "
            "path differ. This paper gives us India-calibrated starting ranges. Second, and more important: we "
            "have 42 chips and no ground truth. Without a principled labeling rule, 'manual labeling' means two "
            "people eyeballing chips with no rubric - slow, inconsistent and impossible to defend. This paper "
            "converts labeling into a semi-automatic, reproducible step: compute four physically meaningful "
            "indices, threshold them, generate candidate labels, then have a human verify. That is exactly Task "
            "01 on the next slide, and it is why we can still finish in 45 days.")
bullet_rich("What we take from it: ", "the index family, the sand-versus-water-versus-vegetation separability "
            "logic, and the threshold ranges as our starting point.")
bullet_rich("What we do not take: ", "its thresholds as final. Our sensor, season and stretch differ, so we "
            "recalibrate on our own 42 chips and record the final thresholds.")

h3("Papers we reviewed and deliberately rejected")
table(
    ["Candidate approach", "Why rejected"],
    [
        ["Generic U-Net / DeepLab baselines", "No handling of the extreme scale range of mining patches; no domain prior."],
        ["Deep learning on commercial imagery (WorldView, Planet)", "Not free; kills reproducibility and the 'deployable on standard devices' claim."],
        ["Global water-mapping products (30-500 m)", "Far too coarse for pit-scale features; a single mining pit is a few pixels."],
        ["Earth-Engine-only pipelines", "We were ineligible for non-commercial GEE access, so the whole pipeline would be non-portable."],
    ],
    widths=[2.5, 3.9],
)

# ---- 2.4 sensors
h2("2.4  Why these three sensors")
bullet_rich("Sentinel-2 MSI (primary) - ", "10 m at the visible and NIR bands, 20 m at red-edge and SWIR, five-day "
            "revisit with two satellites, free and open, level-2A surface reflectance. Crucially it carries SWIR "
            "B11 and B12, which we need for NDBI and for separating dry sand from damp sand. Ten metres is the "
            "sweet spot: fine enough to resolve a mining cluster, coarse enough to keep the archive manageable.")
bullet_rich("Sentinel-1 C-band SAR (monsoon + centreline) - ", "all-weather and day-night. Delhi's monsoon runs "
            "June to September, which is exactly when optical imagery has gaps and also when mining pressure is "
            "highest. VV backscatter is sensitive to surface roughness and dielectric constant, so dry exposed "
            "sand and wet channel separate well. We also discovered it is the better centreline extractor - see 2.5.")
bullet_rich("Landsat-8 TIRS (corroboration) - ", "thermal band 10. Dry exposed sand heats and cools very "
            "differently from vegetated or wet ground, which gives an independent physical check that does not "
            "share failure modes with the optical indices. At 30 m it is corroboration, not the primary detector.")

# ---- 2.5 indices
h2("2.5  Why these four indices (say the formulas)")
table(
    ["Index", "Formula", "Source", "What it separates, and why we need it"],
    [
        ["NDVI", "(B8 - B4) / (B8 + B4)", "Rouse 1974",
         "Vegetation is the main confuser - a vegetated island looks like a sand bar in RGB. NDVI pushes vegetation high and sand near zero or negative."],
        ["NDWI", "(B3 - B8) / (B3 + B8)", "McFeeters 1996",
         "Open water versus dry bar. Water positive, sand low. This is our primary water mask."],
        ["NDBI", "(B11 - B8) / (B11 + B8)", "Zha 2003",
         "SWIR-NIR contrast highlights bare and built surfaces. Sand bars and stockpiles read high, and it also flags access roads and stock yards that accompany mining."],
        ["NDSI", "(B3 - B11) / (B3 + B11)", "Dozier 1989 / Xu 2006",
         "SWIR-inclusive variant. In our area of interest water is positive and sand is negative - the opposite of what people assume, and we corrected an earlier caption on exactly this sign."],
    ],
    widths=[0.6, 1.45, 1.25, 3.1],
)
callout("STRONG POINT",
        "Four indices are four independent physical measurements of the same pixel. A pixel that is low-NDVI, "
        "low-NDWI, high-NDBI and negative-NDSI is sand with high confidence. That conjunction is the entire basis "
        "of the auto-labeling model, and it is why we can label without ground truth.")

# ---- 2.6 pipeline
h2("2.6  Design decisions in the pipeline - and the reason for each")
table(
    ["Decision", "Value", "Reason"],
    [
        ["Study reach", "Palla to Jaitpur", "The administratively defined Delhi stretch, and it contains the known active clusters (Palla, Jaitpur-Kondli belt). A segment-level priority list is only useful if it matches the jurisdiction that has to act on it."],
        ["Centreline length", "50.21 km", "Extracted from the actual watercourse, so it is 3.4% shorter than the official 52 km figure - the official number follows the administrative boundary, not the channel. Worth stating: it shows we measured rather than assumed."],
        ["Transect spacing", "1 km, 51 transects", "One decision unit per river-kilometre, which is the granularity an enforcement team can act on. 51 = 50.21 km divided by 1 km, inclusive of both ends."],
        ["Transect length", "3 km", "Long enough to cross bank-bar-channel-bar-bank even where the river is unusually wide; guarantees every transect sees both banks."],
        ["Chip size", "256 x 256 at 10 m = 2.56 km square", "A mining cluster - pits plus access track plus stockpile - is typically 1-3 km across. 256 is also the standard CNN tile size, so no resampling before training."],
        ["Chips retained", "42 of 51", "Nine transects fell on barrage, bridge or fully urbanised bank with no floodplain to mine. Keeping them injects pure label noise."],
        ["Temporal sampling", "6 quarters (2023 Q1-Q4, 2024 Q1-Q2)", "Seasonal, not arbitrary. Mining visibility peaks in the dry pre-monsoon quarter when bars are exposed. One date cannot distinguish a permanent bar from an active pit; quarterly cadence gives seasonal contrast plus a persistence signal."],
        ["Bands", "10 spectral + 4 indices = 14", "Red-edge bands B5-B7 and B8A are included because they discriminate stressed vegetation on disturbed bars. The four indices are handed to the model as explicit physical features."],
        ["Compositing", "SCL cloud mask + median", "Median across scenes removes transient cloud and shadow far better than a mean, and produces a stable composite without phenology artefacts."],
    ],
    widths=[1.35, 1.75, 3.3],
)

h2("2.7  The centreline story - an honest engineering finding")
p("We first tried to extract the channel with NDWI on dry-season Sentinel-2. It failed. Between February and May "
  "the channel is mostly exposed sand with only narrow water threads, so NDWI fragments the river into pieces and "
  "the skeleton breaks. We switched to Sentinel-1 VV with Otsu thresholding: backscatter gives a clean bimodal "
  "land-water split regardless of season, and the largest connected component plus skeletonisation produced a "
  "single continuous 50.21 km polyline.")
callout("WHY TELL THIS",
        "A method that failed and was replaced is stronger evidence of competence than a method that just worked. "
        "It shows you tested your assumption against the actual data and changed course.")

h2("2.8  The band-order bug - why we mention it on the slide")
p("We built a five-check verification suite: band layout against metadata, recompute indices from stored bands "
  "versus stored index rasters, compare CSV means, compare histogram distributions, and a visual panel check. "
  "NDSI passed all five; NDVI, NDWI and NDBI failed checks two to five.")
p("Root cause: our band list concatenated the 10 m bands first and then the 20 m bands, so B8 landed at position "
  "four instead of position seven. The channel order written to disk did not match the wavelength order we had "
  "documented.")
callout("THE NUANCE THAT MATTERS",
        "The stored index rasters and all CSV statistics were correct, because those were computed by band-name "
        "lookup, not by position. Only the band order written to the output file was wrong. So no scientific "
        "conclusion changed. But any model reading channels positionally would have trained on mislabelled inputs "
        "and would have silently capped its own accuracy - and we would never have known why.")
p("That is the argument for the verification gate: without it, this bug would have surfaced as an unexplained "
  "plateau in accuracy three weeks from now. The fix is already committed in the extraction script, and the "
  "rebuild is the first item on the next slide.")

h2("2.9  Code walkthrough - what to actually show")
table(
    ["Script", "What it does", "What to show / say"],
    [
        ["extract_yamuna_data.py", "CDSE OData client with OAuth2, search, parallel download with resume and retry; SCL-masked median mosaic to 14-band LZW GeoTIFF; USGS M2M client for Landsat-8", "Scroll the download and mosaic functions. Say: 29 products, 2018-2024, fully automated and restartable."],
        ["build_centerline.py", "Sentinel-1 VV, Otsu threshold, largest connected component, skeleton to polyline", "State the NDWI failure and the switch to SAR."],
        ["make_transects.py", "1 km spacing, perpendicular to the local tangent, 3 km length, clipped", "Point out that perpendicularity is computed from the local tangent, not a global angle."],
        ["extract_chips.py", "Windowed read around each transect midpoint, 256 square, 14-band stack, no-data rejection", "Mention the 42-of-51 filter and why."],
        ["compute_indices.py", "The four indices, computed by band-name lookup", "Say explicitly: by name, not by position - this is why the statistics survived the bug."],
        ["verify_indices.py", "The five checks that caught the bug", "Best live demo. Run it, or show verify_indices output."],
    ],
    widths=[1.5, 2.6, 2.3],
)
callout("LIVE DEMO - 60 SECONDS MAX",
        "Open verify_indices output, then band_mapping_report.md, then one chip render as an RGB plus NDVI "
        "side-by-side panel, then label_manifest.csv. Four artefacts, four sentences. Do not open an editor and "
        "scroll code - it burns time and invites nitpicking.")

h2("2.10  One honesty note to keep you safe")
p("The 42 candidate labels currently in the manifest - 16 mining, 14 not-mining, 12 unsure - are "
  "auto-generated from the index thresholds, not ground truth. Always describe them as 'candidate labels pending "
  "human verification'. If a panel member later discovers they were presented as ground truth, every number on "
  "the slide loses credibility. The 12 unsure chips are the honest and useful part: they are exactly the "
  "ambiguous cases the human-review step exists to resolve.")

# ================================================================ SLIDE 3
h1("3.  Slide 3 - Tasks left to be done")

h2("3.1  What to say")
script(
    "The largest single block - collecting the satellite data and producing a label set - is finished. What "
    "remains is three things, and I want to explain why they are in this order.\n\n"
    "First, the index model and auto-labeling, seven days. Everything downstream depends on labels, so nothing "
    "can start before this. We compute NDVI, NDWI, NDBI and NDSI per the JIIT Noida study, calibrate the "
    "thresholds on our own 42 chips, let the model assign candidate labels, and then a human reviews - "
    "concentrating on the twelve that come back unsure.\n\n"
    "Second, the detection and risk models, thirty days. A random forest or XGBoost baseline first, because it "
    "is cheap and tells us how much signal the indices actually carry. Then U-Net or LMS-Net segmentation, "
    "evaluated with spatial cross-validation rather than random splits. Then Sentinel-2 plus Sentinel-1 late "
    "fusion for the monsoon months. Then the risk score itself.\n\n"
    "Third, the MERN dashboard and delivery, twenty days. React front end with the risk map and pixel overlay, "
    "Node and Express for the API, MongoDB for the label store.\n\n"
    "The important point is the parallelism: the dashboard only needs the API contract, not a trained model, so "
    "it starts at day twelve while training is still running."
)

h2("3.2  Why this order and not another order")
bullet_rich("Labels before models - ", "a model trained on unverified labels produces metrics you cannot explain. "
            "Seven days spent here protects twenty-five days of training.")
bullet_rich("Baseline before deep learning - ", "a random forest on 14 features costs an afternoon. If it lands "
            "close to the network, the network is over-engineered and you have saved three weeks. It also gives "
            "you feature importances, which is direct evidence in your paper that the four indices carry real signal.")
bullet_rich("Segmentation, not classification - ", "the deliverable is a map with a pixel-level overlay. A "
            "chip-level label throws away spatial extent, and extent is what feeds area-based risk. Also, the "
            "reference paper is a segmentation paper.")
bullet_rich("Spatial cross-validation - ", "neighbouring chips overlap in geography. A random split leaks "
            "information across the train-test boundary and inflates accuracy. Leave-one-transect-cluster-out "
            "gives the honest number. Saying this out loud pre-empts the most common methodology objection.")
bullet_rich("Fusion after segmentation - ", "you need a working optical model before you can fuse. Fusing two "
            "half-built models produces a result you cannot attribute to either sensor.")
bullet_rich("Risk score last - ", "it consumes detection output plus change metrics; both must exist first.")
bullet_rich("Dashboard in parallel - ", "it is the only block that does not depend on model accuracy, only on the "
            "shape of the API. That is the whole basis of the 45-day plan on the next slide.")

h2("3.3  Why the labeling model is the linchpin")
p("If the auto-labeling step slips, everything slips. That is why it gets the first seven days and the most "
  "care. Two safeguards:")
numbered("Human spot-check with a written rubric, and two reviewers on the unsure cases, so we can report an "
         "agreement statistic rather than a bare assertion.")
numbered("Fixed, recorded thresholds committed alongside the labels, so the labeling is reproducible - anyone can "
         "re-derive the 42 labels from the four index rasters.")

h2("3.4  Day estimates - the reasoning behind each number")
table(
    ["Block", "Estimate", "Why that number"],
    [
        ["01  Index model + auto-labeling", "7 days",
         "Four indices are already computed, so this is threshold calibration plus review of 42 chips. Two people, roughly three days each with a day of reconciliation."],
        ["02  Detection & risk models", "30 days",
         "Baseline 4 d, segmentation training and tuning 12 d, spatial CV and error analysis 5 d, S2+S1 fusion 6 d, risk score 3 d. It is the critical path."],
        ["03  MERN dashboard + delivery", "20 days",
         "API + schema 5 d, map and overlay 7 d, chip browser and labeling UI 4 d, integration and testing 4 d. Runs in parallel from day 12."],
    ],
    widths=[2.3, 0.8, 3.3],
)

# ================================================================ SLIDE 4
h1("4.  Slide 4 - Expected timeline")

h2("4.1  What to say")
script(
    "We have 45 days. The plan is built backwards from that date, and the milestones are placed proportionally "
    "on a day axis rather than spaced evenly, so the drawing does not lie about the gaps.\n\n"
    "Day zero is today, at 55 percent. Day seven, the index model is done and the label set is verified. Day "
    "sixteen, baseline models are in and we know whether the indices carry signal. Day twenty-six, segmentation "
    "is trained and spatially validated. Day thirty-four, Sentinel-1 fusion and the risk score are in place. "
    "Day forty, the dashboard is live. Day forty-five, paper, thesis and defense.\n\n"
    "One thing I want to be explicit about: the effort numbers - thirty days of models, twenty of dashboard, "
    "seven of reporting - add up to fifty-seven, which is more than forty-five. That is not an error; it is the "
    "plan. Two of us run two tracks from day twelve. If we tried to do this serially it would not fit, and I "
    "would rather say that now than discover it in week four."
)

h2("4.2  The parallelism, stated plainly")
table(
    ["Track", "Owner", "Runs", "Content"],
    [
        ["A  -  Models (critical path)", "Upendra", "Day 0 - 34", "Index model, labels, baseline, segmentation, S2+S1 fusion, risk score"],
        ["B  -  Product", "Somya", "Day 12 - 40", "API contract from day 12, dashboard, map and overlay, chip browser, labeling UI"],
        ["Joint", "Both", "Day 34 - 45", "Integration, end-to-end testing, paper, thesis, defense rehearsal"],
    ],
    widths=[2.2, 0.8, 1.1, 3.3],
)
callout("THE ARGUMENT IN ONE LINE",
        "The dashboard is deliberately off the critical path - it needs the API contract, not a trained model. "
        "That is what buys the schedule.")

h2("4.3  Why each milestone sits where it sits")
bullet_rich("Day 7 - ", "labels verified. Nothing else can start, so it is front-loaded and it has a hard gate.")
bullet_rich("Day 16 - ", "baseline in. This is the go/no-go decision point. If a random forest on the four indices "
            "already separates mining from non-mining well, the deep model becomes a confirmation rather than a "
            "gamble. If it does not, we know at day 16 and not at day 40.")
bullet_rich("Day 26 - ", "segmentation validated. Placed at the midpoint because training plus error analysis is "
            "the single most variable block; it is the one that can overrun.")
bullet_rich("Day 34 - ", "fusion and risk score. Deliberately before the dashboard so integration has a stable API.")
bullet_rich("Day 40 - ", "dashboard live. Five days of slack before the deadline; if it slips it eats buffer, not scope.")
bullet_rich("Day 45 - ", "paper, thesis, defense. Reporting is seven days of writing, not seven days of analysis - "
            "that distinction is why it is last and small.")

h2("4.4  Risks and the mitigation for each")
table(
    ["Risk", "Impact", "Mitigation"],
    [
        ["Sentinel-2 re-download for the rebuild is slow or blocked", "Delays Day 7", "The 78 extracted SAFE directories are still on disk, so the rebuild is local if zips are restored; Sentinel-1 already covers the monsoon gap."],
        ["Reviewers disagree on labels", "Delays Day 7", "Third-party tie-break, and report the agreement statistic honestly instead of forcing consensus."],
        ["Segmentation underperforms", "Threatens Day 26", "Fall back to the index plus random-forest pipeline. It is a weaker but fully working product - the project does not fail, the ceiling drops."],
        ["Dashboard scope creep", "Threatens Day 40", "Fixed MVP feature list agreed before day 12: risk map, overlay, chip browser, labeling UI. Nothing else enters."],
        ["Report writing squeezed at the end", "Threatens Day 45", "PROJECT_LOG.md has been maintained throughout, so the thesis is assembly, not archaeology."],
    ],
    widths=[2.3, 1.1, 3.2],
)
callout("OFFER THIS BEFORE THEY ASK",
        "Ask for the internal target to be day 42, not day 45, leaving three days of genuine slack for review "
        "comments and submission logistics. Panels respond well to a plan that already contains its own buffer.")

# ================================================================ Q&A
h1("5.  Questions you will be asked - and the answer")

qa = [
    ("Why not just use Google Earth Engine?",
     "We were ineligible for non-commercial GEE access. Rather than build something we could not run or share, we "
     "went directly to Copernicus and USGS APIs. The side benefit is that the pipeline is portable - it runs on a "
     "laptop, which is exactly what our problem statement demands."),
    ("How do you validate without ground truth?",
     "Three layers: index-based candidate labels grounded in a published India-specific method, two-reviewer "
     "human verification with a reported agreement statistic, and sanity checks against published morphometric "
     "magnitudes from the Sutlej study. We are explicit that field validation is future work, not a claim."),
    ("Why is 55% not 70%?",
     "Because seventy would include work we have only planned. Fifty-five is the measured weight of the block we "
     "closed: data engineering and the label set, complete end to end and verified."),
    ("Why 10-metre imagery and not sub-metre?",
     "Sub-metre is commercial and would break both reproducibility and the lightweight deployment claim. Ten "
     "metres resolves a mining cluster of one to three kilometres comfortably. The limiting factor is temporal "
     "revisit, not ground sampling distance - and Sentinel-2 gives five days for free."),
    ("Why is NDSI negative for sand? You have it backwards.",
     "In our formulation - B3 minus B11 over B3 plus B11 - water is positive and sand negative. We had this "
     "caption wrong in an earlier draft and corrected it during verification. It is exactly the kind of sign "
     "error the five-check suite exists to catch."),
    ("What happens in monsoon when there is no optical imagery?",
     "That is why Sentinel-1 is in the design, not bolted on. Late fusion means the optical model still works "
     "standalone when SAR is missing, and SAR carries the monsoon months when optical has gaps."),
    ("How is the risk score actually computed?",
     "A weighted combination of detected mining area, temporal persistence across quarters, proximity to roads "
     "and settlements, and the magnitude of morphological change - AHP weights from the Nair framework, "
     "calibrated against the labels with a learned model."),
    ("Is this not just thresholding? Where is the AI?",
     "Thresholding produces labels; the AI is the segmentation network that learns spatial context the indices "
     "cannot express, and the fusion model that combines optical and SAR. The indices are features and a "
     "labeling prior, not the final detector."),
    ("Can this scale to other rivers?",
     "That is the point of the design. The only river-specific artefact is the centreline, which is extracted "
     "automatically. Swap the reach, rerun three scripts. We state this as a scalability claim, not a result."),
    ("What if the model does not reach the published 98%?",
     "98.07% is a benchmark, not a promise. Our commitment is a defensible evaluation - spatial cross-validation, "
     "per-class precision and recall, IoU - and an honest comparison. A well-diagnosed 88% is worth more than an "
     "unsourced 98%."),
    ("Why two team members for this scope?",
     "Which is exactly why slide 4 is built on parallel tracks and why the dashboard is off the critical path. "
     "The scope was cut to fit two people: one river, one season pair, one MVP dashboard."),
    ("What is the single biggest threat to finishing?",
     "The segmentation block, because it is the most variable in duration. That is why the baseline at day 16 is "
     "a go/no-go gate - it tells us early whether we are on the fast path or the fallback path."),
]
for q, a in qa:
    h3("Q:  " + q)
    p("A:  " + a)

# ================================================================ CHECKLIST
h1("6.  Check before you present")
for item in [
    "Group number 162, both names, both roll numbers, supervisor spelling - read them off the slide once, out loud, before the panel does.",
    "Confirm the affiliation string for the spectral-index paper against the actual PDF before you say it aloud in the room.",
    "Say 'candidate labels pending human verification', never 'ground truth'.",
    "Do not claim the composites are final - the rebuild is on slide 3, and saying so is a strength.",
    "Have these four files open in separate windows: verify_indices output, band_mapping_report.md, one chip RGB+NDVI panel, label_manifest.csv.",
    "Memorise these seven numbers: 29, 51, 42, 50.21, 252, 14, 45.",
    "Rehearse the 55% justification until it is one breath, not three sentences of hedging.",
]:
    bullet(item)

# ================================================================ NUMBERS
h1("7.  Numbers cheat-sheet")

table(
    ["Number", "Meaning"],
    [
        ["52 km", "Official Delhi stretch under legal ban (administrative boundary)"],
        ["50.21 km", "Centreline we measured from Sentinel-1 - 3.4% shorter, because it follows the watercourse"],
        ["77.15-77.32 E, 28.54-28.76 N", "Area of interest, Palla to Jaitpur"],
        ["29", "Analysis-ready composites delivered (11 Sentinel-2, 12 Sentinel-1, 6 Landsat-8)"],
        ["14", "Bands per chip: 10 spectral (B2-B8, B8A, B11, B12) plus 4 indices"],
        ["10 m / 256 px", "Pixel size and tile size; one chip covers 2.56 km square"],
        ["51", "Transects at 1 km spacing, 3 km long"],
        ["42", "Chips retained after rejecting 9 with no floodplain"],
        ["6", "Quarters: 2023 Q1-Q4 and 2024 Q1-Q2"],
        ["252", "Multi-temporal Sentinel-2 chips (42 x 6), plus 252 Sentinel-1"],
        ["5", "Verification checks that caught the band-order bug"],
        ["16 / 14 / 12", "Candidate labels: mining / not mining / unsure - pending human review"],
        ["55%", "Completion: the full weight of the data and label block"],
        ["45 / 30 / 20 / 7", "Days left / models / dashboard / reporting"],
        ["4 + 20", "Core papers used, papers reviewed in total"],
    ],
    widths=[2.0, 4.5],
)

# ================================================================ PITCH
h1("8.  The 60-second version")
p("If you get only one minute - or if the panel cuts you short - say this:")
script(
    "Illegal sand mining on the Yamuna's 52-kilometre Delhi stretch continues despite a total legal ban, because "
    "enforcement depends on patrols over a river nobody can watch daily. Satellite imagery already covers that "
    "stretch every five days for free; the missing piece is turning pixels into a ranked enforcement decision.\n\n"
    "We have finished the heaviest part - 29 analysis-ready composites from 2018 to 2024, a 50.21-kilometre "
    "centreline, 51 transects, 42 validated chips and a 252-chip multi-temporal stack, all with a verification "
    "suite that has already caught and fixed a real band-order defect. That is 55 percent of the project.\n\n"
    "What remains is a seven-day index-based labeling model drawn from an India-specific spectral study, thirty "
    "days of detection and risk models including Sentinel-1 fusion for the monsoon, and a twenty-day MERN "
    "dashboard running in parallel - done in 45 days with two people on two tracks."
)

doc.save(OUT_DOC)
print("DOC SAVED:", OUT_DOC)

# ================================================================ speaker notes
NOTES = {
    1: ("Opening - 60 sec\n"
        "- Introduce: Upendra Kumar (23/IT/165), Somya Tripathi (23/IT/162), Group 162, Dept. of IT, "
        "supervisor Dr. Anita Thakur.\n"
        "- Hook: sand is the most consumed solid material after water; 52 km Delhi stretch is under a total "
        "SC/NGT ban, yet mining continues because enforcement = manual patrols.\n"
        "- Frame the gap: imagery already covers it every 5 days, free. Missing piece = pixels -> ranked "
        "enforcement decision. That is our project.\n"
        "- Roadmap line: what is done, what remains, how 45 days are planned.\n"
        "- Do NOT read the slide. Say the title once, then move."),
    2: ("Progress - 4 min. Justify 55%, do not assert it.\n"
        "- 55% = weight of the completed block (data+labels 55 / models 30 / dashboard 10 / reporting 5).\n"
        "- Evidence: 29 composites (2018-2024), 50.21 km S1 centreline, 51 transects, 42 chips, 252-chip "
        "6-quarter stack, 4 index rasters, 5-check verification, labeling manifest ready.\n"
        "- Papers, one line each + WHY:\n"
        "  * LMS-Net (Zhang 2025): same label definition, 98.07% at 1/10 U-Net params - matches our "
        "'lightweight, laptop-deployable' constraint; multi-scale handles pit-to-kilometre patch range.\n"
        "  * Sutlej morphometry (Kaur 2025): supplies the PHYSICAL risk quantities - bank shift 8.6 m, "
        "erosion 2,263 ha vs deposition 1,562 ha; same Himalayan monsoonal sand-bed regime as Yamuna.\n"
        "  * AHP+ML (Nair 2025): our prioritization blueprint; all 8 parameters free-data derivable; "
        "hybrid > either alone (AUC>0.93) justifies expert weights + learned calibration.\n"
        "  * JIIT Noida index study: India-calibrated NDVI/NDWI/NDBI/NDSI. Critical because we have NO "
        "ground truth - it makes labeling semi-automatic and reproducible instead of 42 blind eyeballs.\n"
        "- Design reasons: 10 m/5-day free S2 (SWIR needed); S1 for monsoon + it beat NDWI on dry-season "
        "centreline; L8 thermal as an independent physical check.\n"
        "- Band-order bug: B8 at index 4 instead of 7. Stored indices/CSVs were CORRECT (computed by band "
        "name); only the written channel order was wrong. Would have silently capped any positional model.\n"
        "- Demo 60 sec max: verify_indices output -> band_mapping_report.md -> one RGB+NDVI panel -> "
        "label_manifest.csv.\n"
        "- HONESTY: call the 42 labels 'candidates pending human verification', never ground truth."),
    3: ("Tasks left - 2.5 min.\n"
        "- Lead with: the heaviest block (data + labels, ~55%) is DONE. Only models, dashboard, reporting remain.\n"
        "- 01 Index model + auto-labeling, 7 days: compute 4 indices per JIIT Noida, calibrate thresholds on "
        "our 42 chips, model assigns candidates, human reviews - focus on the 12 unsure. Everything "
        "downstream depends on this, so it is first and it is a hard gate.\n"
        "- 02 Detection & risk, 30 days: RF/XGB baseline (cheap go/no-go at day 16, gives feature "
        "importances) -> U-Net/LMS-Net segmentation with SPATIAL cross-validation (random splits leak "
        "between overlapping neighbouring chips) -> S2+S1 late fusion for monsoon -> risk score.\n"
        "- 03 MERN + delivery, 20 days: React map/overlay, Node/Express API, MongoDB label store, paper+thesis.\n"
        "- Key point: 01 and 03 run in PARALLEL with 02. The dashboard needs the API contract, not a trained "
        "model - that is what makes 45 days possible."),
    4: ("Timeline - 1.5 min.\n"
        "- 45 days, built backwards from the deadline. Milestones are placed PROPORTIONALLY on the day axis, "
        "not evenly - the drawing should not flatter the gaps.\n"
        "- Day 0 today 55% | 7 index model + verified labels | 16 baseline in (go/no-go) | 26 segmentation "
        "validated | 34 S2+S1 fusion + risk score | 40 dashboard live | 45 paper, thesis, defense.\n"
        "- Be explicit: 30+20+7 = 57 effort-days > 45 calendar days. Not an error - it is two tracks from "
        "day 12 (A: models, critical path; B: product). Serial would not fit; say so now, not in week four.\n"
        "- Biggest risk = segmentation duration; that is why day 16 is a gate. Fallback = index + random "
        "forest: weaker ceiling, still a working product.\n"
        "- Offer proactively: internal target day 42, leaving 3 days of real slack for review comments."),
}

try:
    from pptx import Presentation
    prs = Presentation(PPTX)
    for i, slide in enumerate(prs.slides, 1):
        if i in NOTES:
            slide.notes_slide.notes_text_frame.text = NOTES[i]
    prs.save(PPTX)
    print("SPEAKER NOTES injected into:", PPTX)
except Exception as e:
    print("Notes injection failed:", e)
