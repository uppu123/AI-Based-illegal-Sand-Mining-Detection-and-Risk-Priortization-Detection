from pptx import Presentation
from pptx.util import Emu

P = r"C:\Btech Project Important Files\Timeline\Project_Progress_Presentation.pptx"
prs = Presentation(P)
SW = prs.slide_width / 914400.0
SH = prs.slide_height / 914400.0
print("slide size: %.2f x %.2f in" % (SW, SH))

def est_lines(text, width_in, size_pt, bold=False):
    # avg char width ~ 0.50 * font size for Calibri, 0.60 for Consolas
    cw = size_pt * (0.58 if bold else 0.50) / 72.0
    per_line = max(1, int(width_in / cw))
    n = 0
    for ln in text.split("\n"):
        n += max(1, -(-len(ln) // per_line))
    return n

for idx, slide in enumerate(prs.slides, 1):
    print("\n=== SLIDE %d ===" % idx)
    warn = []
    for sh in slide.shapes:
        L = sh.left / 914400.0
        T = sh.top / 914400.0
        W = sh.width / 914400.0
        H = sh.height / 914400.0
        # bounds check
        if L < -0.01 or T < -0.01 or L + W > SW + 0.02 or T + H > SH + 0.02:
            warn.append("OUT-OF-BOUNDS %-22s L=%.2f T=%.2f R=%.2f B=%.2f" %
                        (sh.shape_type, L, T, L + W, T + H))
        if not sh.has_text_frame:
            continue
        txt = sh.text_frame.text
        if not txt.strip():
            continue
        sizes = []
        bolds = []
        for p in sh.text_frame.paragraphs:
            for r in p.runs:
                if r.font.size:
                    sizes.append(r.font.size.pt)
                bolds.append(bool(r.font.bold))
        if not sizes:
            continue
        size = max(sizes)
        bold = any(bolds)
        lines = est_lines(txt, W, size, bold)
        need = lines * size * 1.32 / 72.0
        if need > H + 0.03:
            warn.append("TEXT-OVERFLOW %-28s box %.2fx%.2f need h=%.2f (lines=%d size=%.0f) :: %s"
                        % (sh.name[:28], W, H, need, lines, size, txt[:52].replace("\n", " / ")))
    if warn:
        for w in warn:
            print("  !", w)
    else:
        print("  ok")

