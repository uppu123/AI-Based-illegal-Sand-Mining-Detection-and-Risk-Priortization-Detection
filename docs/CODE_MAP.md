# Code map — slide 2 names vs. real files

Slide 2 of the current deck uses three convenient short names. Two of them were never real filenames, and spectral indices are computed inline rather than in a separate file. This map is the authoritative answer if the panel asks for a file by name.

| Name shown on slide 2 | Real file in this repository | Note |
|---|---|---|
| `extract_yamuna_data.py` | `src/acquisition/extract_yamuna_data.py` | Same filename, moved into the acquisition package |
| `build_centerline.py` | `src/geometry/build_centerline_from_sar.py` | The S1 VV + Otsu implementation actually used |
| `make_transects.py` | `src/geometry/03_generate_transects.py` | 51 transects at 1 km spacing |
| `extract_chips.py` | `src/processing/04_extract_training_chips.py` | One-quarter demo extractor; `extract_chips_all_quarters.py` and `extract_sar_chips.py` are the batch variants |
| `compute_indices.py` | inline in `src/acquisition/extract_yamuna_data.py` (spectral-index section) | NDVI/NDWI/NDBI/NDSI are computed by band name there; no separate file exists |
| `verify_indices.py` | `src/verification/08_verify_spectral_indices.py` and `09_diagnose_band_mapping.py` | One 5-check suite plus the root-cause diagnostic |

Planned fix (Phase E): update slide 2 to show the real filenames, so the deck matches the repository exactly.
