#!/usr/bin/env python3
"""
01_verify_inventory.py

Verify all 29 expected GeoTIFF files in the yamuna_data directory.
Checks: existence, readability, band count, dtype, CRS, resolution, nodata,
bounds overlap with AOI, band descriptions, index sanity (S2), thermal sanity (L8),
and cross-file consistency.

Outputs:
- metadata/inventory_check.csv
- Console summary with PASS/FAIL
"""

import argparse
import sys
from pathlib import Path
import rasterio
from rasterio.crs import CRS
from rasterio.windows import Window
import numpy as np
import pandas as pd
from datetime import datetime
import math


# ============================================================
# CONFIGURATION
# ============================================================
BASE_DATA = Path(r"C:\New folder\yamuna_data")
OUTPUT_DIR = Path(r"C:\New folder\yamuna_work\metadata")
LOG_DIR = Path(r"C:\New folder\yamuna_work\logs")

AOI_WEST = 77.15
AOI_SOUTH = 28.54
AOI_EAST = 77.32
AOI_NORTH = 28.76
AOI_TOL = 0.01  # degrees

# Expected band descriptions
S2_BANDS = ["B2", "B3", "B4", "B5", "B6", "B7", "B8", "B8A", "B11", "B12",
            "NDVI", "NDWI", "NDBI", "NDSI"]
L8_BANDS = ["thermal_K", "red_B4", "nir_B5"]

# Resolution tolerances
S2_EXPECTED_RES = 10.0
S1_EXPECTED_RES = 10.0
L8_EXPECTED_RES = 30.0
RES_TOL_S2_S1 = 0.5
RES_TOL_L8 = 1.0

# Centre latitude for degree-to-metre conversion
CENTRE_LAT = (AOI_NORTH + AOI_SOUTH) / 2.0
CENTRE_LAT_RAD = math.radians(CENTRE_LAT)
DEG_TO_M_X = 111320 * math.cos(CENTRE_LAT_RAD)
DEG_TO_M_Y = 110574


# ============================================================
# HELPER FUNCTIONS
# ============================================================
def setup_logging():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LOG_DIR / f"01_verify_inventory_{timestamp}.log"
    return log_file


def log_message(log_file, msg):
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(msg + "\n")
    print(msg)


def generate_expected_files():
    """Generate list of expected file paths relative to BASE_DATA."""
    expected = []

    # Sentinel-2: 5 annual (2018-2022) - in year subdirectories
    for year in range(2018, 2023):
        expected.append((f"sentinel2/{year}", f"S2_{year}_composite.tif", "S2", 14))

    # Sentinel-2: 6 quarterly (2023 Q1-Q4, 2024 Q1-Q2) - in 2023_2024 subdirectory
    for year, quarters in [(2023, [1, 2, 3, 4]), (2024, [1, 2])]:
        for q in quarters:
            expected.append(("sentinel2/2023_2024", f"S2_{year}_Q{q}_composite.tif", "S2", 14))

    # Sentinel-1: 12 files (2023 Q1-Q4, 2024 Q1-Q2) x VV/VH
    for year, quarters in [(2023, [1, 2, 3, 4]), (2024, [1, 2])]:
        for q in quarters:
            for pol in ["VV", "VH"]:
                expected.append(("sentinel1/2023_2024", f"S1_{year}_Q{q}_{pol}.tif", "S1", 1))

    # Landsat-8: 6 quarterly (2023 Q1-Q4, 2024 Q1-Q2) - named with _thermal suffix
    for year, quarters in [(2023, [1, 2, 3, 4]), (2024, [1, 2])]:
        for q in quarters:
            expected.append(("landsat8/2023_2024", f"L8_{year}_Q{q}_thermal.tif", "L8", 3))

    return expected


def check_file_exists_size(filepath):
    """Check 1: File exists and size > 0."""
    if not filepath.exists():
        return False, "File does not exist"
    if filepath.stat().st_size == 0:
        return False, "File size is 0 bytes"
    return True, ""


def check_rasterio_open(filepath):
    """Check 1 (cont'd): Opens with rasterio and band 1 readable."""
    try:
        with rasterio.open(filepath) as src:
            _ = src.read(1)
        return True, ""
    except Exception as e:
        return False, f"Rasterio open/read failed: {e}"


def get_sensor_from_filename(filename):
    """Check 2: Sensor from filename prefix."""
    if filename.startswith("S2_"):
        return "S2"
    elif filename.startswith("S1_"):
        return "S1"
    elif filename.startswith("L8_"):
        return "L8"
    return "UNKNOWN"


def check_band_count(src, expected, sensor):
    """Check 3: Band count matches expected."""
    actual = src.count
    if actual != expected:
        return False, f"Band count mismatch: expected {expected}, got {actual}"
    return True, ""


def check_dtype(src):
    """Check 4: dtype should be uint16."""
    if src.dtypes[0] != "uint16":
        return False, f"dtype is {src.dtypes[0]}, expected uint16"
    return True, ""


def check_crs(src):
    """Check 5: CRS should be EPSG:4326."""
    if src.crs is None:
        return False, "CRS is None"
    try:
        crs_epsg = src.crs.to_epsg()
        if crs_epsg != 4326:
            return False, f"CRS is EPSG:{crs_epsg}, expected EPSG:4326"
    except Exception:
        return False, f"CRS could not be parsed: {src.crs}"
    return True, ""


def check_resolution(src):
    """Check 6: Resolution in metres (approximate for geographic CRS)."""
    res_x = abs(src.transform.a)
    res_y = abs(src.transform.e)
    res_x_m = res_x * DEG_TO_M_X
    res_y_m = res_y * DEG_TO_M_Y
    return res_x_m, res_y_m


def check_resolution_tolerance(res_x_m, res_y_m, sensor):
    """Check 6 (cont'd): Resolution within tolerance."""
    if sensor in ("S2", "S1"):
        expected = S2_EXPECTED_RES if sensor == "S2" else S1_EXPECTED_RES
        tol = RES_TOL_S2_S1
    else:
        expected = L8_EXPECTED_RES
        tol = RES_TOL_L8

    ok_x = abs(res_x_m - expected) <= tol
    ok_y = abs(res_y_m - expected) <= tol
    if not (ok_x and ok_y):
        return False, f"Resolution {res_x_m:.2f} x {res_y_m:.2f} m, expected ~{expected} m (tol {tol} m)"
    return True, ""


def check_nodata(src):
    """Check 7: Nodata not set."""
    if src.nodata is None:
        return False, "Nodata not set"
    return True, ""


def check_bounds_overlap(src):
    """Check 8: Bounds overlap AOI with tolerance."""
    b = src.bounds
    west, south, east, north = b.left, b.bottom, b.right, b.top

    overlap = not (east < AOI_WEST - AOI_TOL or west > AOI_EAST + AOI_TOL or
                   north < AOI_SOUTH - AOI_TOL or south > AOI_NORTH + AOI_TOL)

    if not overlap:
        return False, f"Bounds {west:.4f},{south:.4f},{east:.4f},{north:.4f} do not overlap AOI"
    return True, ""


def check_band_descriptions(src, sensor):
    """Check 9: Band descriptions match expected."""
    expected = S2_BANDS if sensor == "S2" else (L8_BANDS if sensor == "L8" else None)
    if sensor == "S1":
        # S1: VV or VH from filename
        return True, "", ["VV"] if "VV" in str(src.name).upper() else ["VH"]

    if expected is None:
        return True, "", []

    actual = list(src.descriptions) if src.descriptions else []
    if not actual or all(d is None or d == "" for d in actual):
        return True, "Band descriptions empty; using expected order as fallback", expected

    # Compare (case-insensitive, allow minor variations)
    mismatch = False
    notes = []
    for i, (exp, act) in enumerate(zip(expected, actual)):
        if act is None or act == "":
            notes.append(f"Band {i+1}: empty, using '{exp}'")
            mismatch = True
        elif exp.lower() != act.lower():
            notes.append(f"Band {i+1}: expected '{exp}', got '{act}'")
            mismatch = True

    if mismatch:
        return True, "; ".join(notes), actual

    return True, "", actual


def check_s2_index_sanity(src):
    """Check 10: S2 index bands (last 4) sanity check."""
    # Indices stored as uint16: value = (index + 1) * 5000
    # So index = raw / 5000 - 1
    # Valid range: [-1.05, 1.05]
    try:
        height, width = src.height, src.width
        # Centre 256x256 window
        win = Window(max(0, (width - 256) // 2), max(0, (height - 256) // 2), 256, 256)
        # Read last 4 bands
        indices_data = src.read([11, 12, 13, 14], window=win)  # 1-indexed
        if indices_data.size == 0:
            return False, "Could not read index bands"

        # Decode
        decoded = indices_data.astype(np.float32) / 5000.0 - 1.0

        # Check for all zeros (fail)
        if np.all(decoded == 0):
            return False, "All index bands are zero"

        # Check range
        min_val = np.nanmin(decoded)
        max_val = np.nanmax(decoded)
        if min_val < -1.05 or max_val > 1.05:
            return True, f"Index range [{min_val:.3f}, {max_val:.3f}] outside [-1.05, 1.05]"

        return True, ""
    except Exception as e:
        return True, f"Index sanity check error: {e}"


def check_l8_thermal_sanity(src):
    """Check 11: L8 thermal band sanity (Kelvin range 240-340 K)."""
    try:
        height, width = src.height, src.width
        win = Window(max(0, (width - 256) // 2), max(0, (height - 256) // 2), 256, 256)
        thermal = src.read(1, window=win).astype(np.float32)
        if thermal.size == 0:
            return True, "Could not read thermal band"

        median_val = np.nanmedian(thermal)
        if 240 <= median_val <= 340:
            return True, f"Thermal median {median_val:.1f} K (looks like Kelvin)"
        else:
            return True, f"Thermal median {median_val:.1f} - outside Kelvin range 240-340 (may be raw DN)"
    except Exception as e:
        return True, f"Thermal sanity check error: {e}"


def check_cross_file_consistency(results, sensor):
    """Cross-file checks for same sensor."""
    sensor_results = [r for r in results if r["sensor"] == sensor and r["status"] != "FAIL"]
    if len(sensor_results) < 2:
        return

    # All should share CRS, resolution, width, height, transform
    first = sensor_results[0]
    for r in sensor_results[1:]:
        mismatches = []
        if r["crs"] != first["crs"]:
            mismatches.append("CRS")
        if abs(r["res_x_m"] - first["res_x_m"]) > 0.01 or abs(r["res_y_m"] - first["res_y_m"]) > 0.01:
            mismatches.append("resolution")
        if r["width"] != first["width"] or r["height"] != first["height"]:
            mismatches.append("dimensions")
        if r["transform"] != first["transform"]:
            mismatches.append("transform")

        if mismatches:
            r["status"] = "FAIL"
            r["notes"] += f"; Cross-file mismatch: {', '.join(mismatches)}"


def find_extra_files():
    """Find unexpected files in yamuna_data."""
    extra = []
    for ext in [".part", ".zip"]:
        extra.extend(BASE_DATA.rglob(f"*{ext}"))
    # Unexpected .json files (not in metadata/)
    for json_file in BASE_DATA.rglob("*.json"):
        if "metadata" not in json_file.parts:
            extra.append(json_file)
    return [str(f.relative_to(BASE_DATA)) for f in extra]


def main():
    parser = argparse.ArgumentParser(description="Verify Yamuna data inventory")
    parser.add_argument("--base", default=str(BASE_DATA), help="Base data directory")
    parser.add_argument("--output", default=str(OUTPUT_DIR), help="Output directory")
    args = parser.parse_args()

    base = Path(args.base)
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)

    log_file = setup_logging()
    log_message(log_file, f"=== 01_verify_inventory started at {datetime.now()} ===")
    log_message(log_file, f"Base data: {base}")
    log_message(log_file, f"Output dir: {output}")

    expected = generate_expected_files()
    log_message(log_file, f"Expected files: {len(expected)}")

    results = []
    fail_count = 0
    warn_count = 0
    ok_count = 0

    for rel_dir, filename, sensor, expected_bands in expected:
        filepath = base / rel_dir / filename
        log_message(log_file, f"\nChecking: {rel_dir}/{filename}")

        row = {
            "file": f"{rel_dir}/{filename}",
            "sensor": sensor,
            "n_bands": None,
            "dtype": None,
            "crs": None,
            "res_x_m": None,
            "res_y_m": None,
            "nodata": None,
            "west": None,
            "south": None,
            "east": None,
            "north": None,
            "width": None,
            "height": None,
            "band_names": "",
            "status": "OK",
            "notes": ""
        }

        # Check 1: Exists and size
        ok, note = check_file_exists_size(filepath)
        if not ok:
            row["status"] = "FAIL"
            row["notes"] = note
            fail_count += 1
            results.append(row)
            log_message(log_file, f"  FAIL: {note}")
            continue

        # Check 1 cont'd: Rasterio open
        ok, note = check_rasterio_open(filepath)
        if not ok:
            row["status"] = "FAIL"
            row["notes"] = note
            fail_count += 1
            results.append(row)
            log_message(log_file, f"  FAIL: {note}")
            continue

        # Open for detailed checks
        try:
            with rasterio.open(filepath) as src:
                row["n_bands"] = src.count
                row["dtype"] = src.dtypes[0]
                row["crs"] = str(src.crs) if src.crs else "None"
                row["width"] = src.width
                row["height"] = src.height
                row["transform"] = str(src.transform)
                row["nodata"] = src.nodata

                # Bounds
                b = src.bounds
                row["west"] = b.left
                row["south"] = b.bottom
                row["east"] = b.right
                row["north"] = b.top

                # Check 2: Sensor from filename
                detected_sensor = get_sensor_from_filename(filename)
                if detected_sensor != sensor:
                    row["status"] = "FAIL"
                    row["notes"] += f"Sensor mismatch: filename says {detected_sensor}, expected {sensor}; "
                    fail_count += 1

                # Check 3: Band count
                ok, note = check_band_count(src, expected_bands, sensor)
                if not ok:
                    row["status"] = "FAIL"
                    row["notes"] += note + "; "
                    fail_count += 1
                else:
                    log_message(log_file, f"  Band count: {src.count} (OK)")

                # Check 4: dtype
                ok, note = check_dtype(src)
                if not ok:
                    if row["status"] == "OK":
                        row["status"] = "WARN"
                    row["notes"] += note + "; "
                    warn_count += 1
                else:
                    log_message(log_file, f"  dtype: {src.dtypes[0]} (OK)")

                # Check 5: CRS
                ok, note = check_crs(src)
                if not ok:
                    row["status"] = "FAIL"
                    row["notes"] += note + "; "
                    fail_count += 1
                else:
                    log_message(log_file, f"  CRS: {src.crs} (OK)")

                # Check 6: Resolution
                res_x_m, res_y_m = check_resolution(src)
                row["res_x_m"] = round(res_x_m, 2)
                row["res_y_m"] = round(res_y_m, 2)
                ok, note = check_resolution_tolerance(res_x_m, res_y_m, sensor)
                if not ok:
                    if row["status"] == "OK":
                        row["status"] = "WARN"
                    row["notes"] += note + "; "
                    warn_count += 1
                else:
                    log_message(log_file, f"  Resolution: {res_x_m:.2f} x {res_y_m:.2f} m (OK)")

                # Check 7: Nodata
                ok, note = check_nodata(src)
                if not ok:
                    if row["status"] == "OK":
                        row["status"] = "WARN"
                    row["notes"] += note + "; "
                    warn_count += 1
                else:
                    log_message(log_file, f"  Nodata: {src.nodata} (OK)")

                # Check 8: Bounds overlap AOI
                ok, note = check_bounds_overlap(src)
                if not ok:
                    row["status"] = "FAIL"
                    row["notes"] += note + "; "
                    fail_count += 1
                else:
                    log_message(log_file, f"  Bounds overlap AOI: OK")

                # Check 9: Band descriptions
                ok, note, band_names = check_band_descriptions(src, sensor)
                row["band_names"] = ",".join(band_names) if band_names else ""
                if note:
                    if row["status"] == "OK":
                        row["status"] = "WARN"
                    row["notes"] += note + "; "
                    warn_count += 1

                # Check 10: S2 index sanity
                if sensor == "S2":
                    ok, note = check_s2_index_sanity(src)
                    if not ok:
                        row["status"] = "FAIL"
                        row["notes"] += note + "; "
                        fail_count += 1
                    elif note:
                        if row["status"] == "OK":
                            row["status"] = "WARN"
                        row["notes"] += note + "; "
                        warn_count += 1

                # Check 11: L8 thermal sanity
                if sensor == "L8":
                    ok, note = check_l8_thermal_sanity(src)
                    if note and "outside Kelvin range" in note:
                        if row["status"] == "OK":
                            row["status"] = "WARN"
                        row["notes"] += note + "; "
                        warn_count += 1
                    elif note:
                        log_message(log_file, f"  {note}")

        except Exception as e:
            row["status"] = "FAIL"
            row["notes"] += f"Unexpected error: {e}; "
            fail_count += 1
            log_message(log_file, f"  FAIL: Unexpected error: {e}")

        results.append(row)

        if row["status"] == "OK":
            ok_count += 1
        elif row["status"] == "WARN":
            pass  # already counted
        # FAIL already counted

        log_message(log_file, f"  Status: {row['status']}")

    # Cross-file consistency checks
    log_message(log_file, "\n--- Cross-file consistency checks ---")
    for sensor in ["S2", "S1", "L8"]:
        check_cross_file_consistency(results, sensor)

    # Re-count after cross-file checks
    ok_count = sum(1 for r in results if r["status"] == "OK")
    warn_count = sum(1 for r in results if r["status"] == "WARN")
    fail_count = sum(1 for r in results if r["status"] == "FAIL")

    # Extra files check
    extra_files = find_extra_files()
    if extra_files:
        warn_count += 1
        log_message(log_file, f"\nExtra/unexpected files found ({len(extra_files)}):")
        for f in extra_files:
            log_message(log_file, f"  {f}")
        # Add to first row notes
        if results:
            results[0]["notes"] += f" Extra files: {len(extra_files)}; "
            if results[0]["status"] == "OK":
                results[0]["status"] = "WARN"

    # Check for missing expected files
    existing_files = set()
    for rel_dir, filename, sensor, expected_bands in expected:
        filepath = base / rel_dir / filename
        if filepath.exists():
            existing_files.add(f"{rel_dir}/{filename}")

    for rel_dir, filename, sensor, expected_bands in expected:
        key = f"{rel_dir}/{filename}"
        if key not in existing_files:
            fail_count += 1
            row = {
                "file": key,
                "sensor": sensor,
                "n_bands": None,
                "dtype": None,
                "crs": None,
                "res_x_m": None,
                "res_y_m": None,
                "nodata": None,
                "west": None,
                "south": None,
                "east": None,
                "north": None,
                "width": None,
                "height": None,
                "band_names": "",
                "status": "FAIL",
                "notes": "Missing expected file"
            }
            results.append(row)
            log_message(log_file, f"MISSING: {key}")

    # Write inventory CSV
    df = pd.DataFrame(results)
    csv_path = output / "inventory_check.csv"
    df.to_csv(csv_path, index=False)
    log_message(log_file, f"\nWritten: {csv_path}")

    # Console summary
    log_message(log_file, f"\n=== SUMMARY ===")
    log_message(log_file, f"Total files checked: {len(results)}")
    log_message(log_file, f"OK: {ok_count}")
    log_message(log_file, f"WARN: {warn_count}")
    log_message(log_file, f"FAIL: {fail_count}")

    if fail_count == 0:
        log_message(log_file, "\n>>> PASS: All checks passed (zero FAIL)")
        print("\n>>> PASS: All checks passed (zero FAIL)")
        sys.exit(0)
    else:
        log_message(log_file, "\n>>> FAIL: One or more files failed checks")
        print("\n>>> FAIL: One or more files failed checks")
        for r in results:
            if r["status"] == "FAIL":
                print(f"  FAIL: {r['file']} - {r['notes']}")
        sys.exit(1)


if __name__ == "__main__":
    main()