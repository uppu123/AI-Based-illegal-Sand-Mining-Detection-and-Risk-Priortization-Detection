# Presentation artifacts

## Final files (for the review)

| File | Purpose |
|---|---|
| `Project_Progress_Presentation.pptx` | 4-slide deck, navy/gold theme, 55% loader, DTU logo, speaker notes on all slides |
| `Project_Progress_Presentation.pdf` | PDF export of the same 4 slides |
| `Presentation_Script_and_Reasoning.docx` / `.pdf` | 13-page verbatim speaking script, reasoning per slide, 4 paper justifications, 12 Q&A, numbers cheat-sheet |
| `Project_Synopsis_Final.docx` / `.pdf` | Submitted synopsis |
| `dtu_logo.png` | Logo used on every slide |

## Builders (source code)

| Script | Generates |
|---|---|
| `build_progress_deck.py` | The 4-slide `.pptx` — **canonical builder** |
| `build_script_document.py` | The script `.docx` and the speaker-notes dictionary |
| `build_documentation_pack.py` | The 7 PDFs in `docs/documentation_pdfs/` |
| `export_all_pdfs.ps1` | DOCX/PPTX to PDF via Word/PowerPoint COM |
| `helpers/` | Inspection and note-injection utilities |
| `archive/` | Superseded deck iterations — do not use, kept only for traceability |

All output paths are relative to the repository, so the builders work after the repo is moved.
