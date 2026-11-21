import io
import sys
from pptx import Presentation

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

p = Presentation(r"C:\Btech Project Important Files\Timeline\Project_Progress_Presentation.pptx")
for i, s in enumerate(p.slides, 1):
    if i < 3:
        continue
    print("================ SLIDE %d ================" % i)
    for sh in s.shapes:
        if sh.has_text_frame and sh.text_frame.text.strip():
            t = sh.text_frame.text.replace("\n", " | ")
            if len(t) < 130:
                print("  %-58s  L=%.2f T=%.2f" % (t, sh.left / 914400.0, sh.top / 914400.0))
