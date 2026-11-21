# Source code (`src/`)

Seven small packages, ordered by their role in the pipeline. See `../ARCHITECTURE.md` for the data-flow diagram and `../docs/PIPELINE_GUIDE.md` for commands.

| Package | What lives here |
|---|---|
| `acquisition/` | `extract_yamuna_data.py` — CDSE OData + USGS M2M download, SCL-masked median composites, spectral indices |
| `geometry/` | `build_centerline_from_sar.py`, `03_generate_transects.py` |
| `processing/` | `04_extract_training_chips.py`, `extract_chips_all_quarters.py`, `extract_sar_chips.py` |
| `labeling/` | `05_prepare_labeling_set.py` |
| `verification/` | `01_verify_data_inventory.py`, `02_validate_river_centerline.py`, `08_verify_spectral_indices.py`, `09_diagnose_band_mapping.py` |
| `experiments/` | `legacy_centerline_from_ndwi.py` — failed approach, kept for transparency |
| `utilities/` | Read-only inspection helpers used while building the reports |

## Conventions

- A numbered prefix (`01_` … `09_`) means the script is a step in the main pipeline. The number tells you the order.
- A descriptive name without a number means a reusable variant (for example, "all quarters" instead of one demo quarter).
- Every script begins with a docstring: purpose, inputs and outputs.
- All paths come from `config/project_config.py`. No script contains a hard-coded `C:\...` path.
- Verification scripts never write into the imagery folders.

## Adding a new step

1. Put the script in the package that matches its role.
2. Give it a numbered or descriptive name in `snake_case`.
3. Import paths from `config.project_config` using the standard bootstrap at the top of existing scripts.
4. Add its command to `docs/PIPELINE_GUIDE.md` and its box to `ARCHITECTURE.md`.
