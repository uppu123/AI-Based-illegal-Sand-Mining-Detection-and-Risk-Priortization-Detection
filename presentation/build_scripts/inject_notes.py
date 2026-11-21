# -*- coding: utf-8 -*-
"""Inject speaker notes into a copy of the deck, then try to replace the original."""
import shutil
import sys
from pptx import Presentation

SRC = r"C:\Btech Project Important Files\Timeline\Project_Progress_Presentation.pptx"
TMP = r"C:\Users\upend\AppData\Local\Temp\opencode\deck_with_notes.pptx"
ALT = r"C:\Btech Project Important Files\Timeline\Project_Progress_Presentation_with_notes.pptx"

sys.path.insert(0, r"C:\New folder")
from make_script_doc import NOTES  # noqa: E402  (reuses the same note text)


def inject(path):
    prs = Presentation(path)
    for i, slide in enumerate(prs.slides, 1):
        if i in NOTES:
            slide.notes_slide.notes_text_frame.text = NOTES[i]
    prs.save(path)
    return len(prs.slides)


shutil.copy2(SRC, TMP)
n = inject(TMP)
print("notes written into temp copy, slides =", n)

try:
    shutil.copy2(TMP, SRC)
    print("REPLACED ORIGINAL:", SRC)
    target = SRC
except PermissionError:
    shutil.copy2(TMP, ALT)
    print("ORIGINAL LOCKED - wrote instead:", ALT)
    target = ALT

# verify
prs = Presentation(target)
print("\nVERIFY", target)
for i, s in enumerate(prs.slides, 1):
    note = s.notes_slide.notes_text_frame.text.strip()
    print("  slide %d notes: %d chars | first line: %s"
          % (i, len(note), note.splitlines()[0][:70] if note else "<none>"))
