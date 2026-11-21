# -*- coding: utf-8 -*-
"""Dump slide 2 of the deck: every shape, its box and its text - top to bottom, left to right."""
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from pptx import Presentation
from pptx.util import Emu

P = r"C:\Btech Project Important Files\Timeline\Project_Progress_Presentation.pptx"
prs = Presentation(P)
emu2in = 914400.0

s = prs.slides[1]
print("slide size: %.3f x %.3f in" % (prs.slide_width / emu2in, prs.slide_height / emu2in))
print("shapes:", len(s.shapes))
print()

items = []
for sh in s.shapes:
    txt = ""
    if sh.has_text_frame:
        txt = "\n".join(p.text for p in sh.text_frame.paragraphs if p.text.strip())
    if not txt and sh.has_table:
        rows = []
        for r in sh.table.rows:
            rows.append(" | ".join(c.text.replace("\n", " / ") for c in r.cells))
        txt = "\n".join(rows)
    items.append((sh.top, sh.left, sh.name, sh.width, sh.height, txt))

for top, left, name, w, h, txt in sorted(items):
    print("=" * 100)
    print("[%s]  x=%.2f y=%.2f  w=%.2f h=%.2f" % (name, left / emu2in, top / emu2in, w / emu2in, h / emu2in))
    if txt:
        for line in txt.splitlines():
            print("    " + line)
    else:
        print("    (no text - graphic/shape)")
