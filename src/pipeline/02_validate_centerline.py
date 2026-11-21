#!/usr/bin/env python3
"""
02_validate_centerline.py

Validate the digitized Yamuna centerline GeoJSON.
Checks: CRS, geometry type, length, vertex positions, direction, segment lengths,
self-intersections. Produces validation report and visualization map.
"""

import argparse
import sys
import json
from pathlib import Path
import geopandas as gpd
from shapely.geometry import LineString, MultiLineString, Point, box
from shapely.ops import linemerge, unary_union
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import contextily as ctx


# ============================================================
# CONFIGURATION
# ============================================================
CENTERLINE_PATH = Path(r"C:\New folder\yamuna_work\centerline\yamuna_centerline.geojson")
ORIENTED_PATH = Path(r"C:\New folder\yamuna_work\centerline\yamuna_centerline_oriented.geojson")
VALIDATION_TXT = Path(r"C:\New folder\yamuna_work\centerline\centerline_validation.txt")
VALIDATION_PNG = Path(r"C:\New folder\yamuna_work\centerline\centerline_check.png")

AOI_BOUNDS = (77.15, 28.54, 77.32, 28.76)  # west, south, east, north
AOI_BUFFER_DEG = 0.01
EXPECTED_LENGTH_KM_MIN = 45
EXPECTED_LENGTH_KM_MAX = 60
MAX_SEGMENT_M = 1000
TARGET_CRS = "EPSG:4326"
UTM_CRS = "EPSG:32643"  # UTM 43N for length calculation


# ============================================================
# HELPER FUNCTIONS
# ============================================================
def write_validation(txt_path, lines):
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Written: {txt_path}")


def check_file_exists():
    """Check 2a: Centerline file exists."""
    if not CENTERLINE_PATH.exists():
        return False, "Centerline file does not exist"
    return True, ""


def load_centerline():
    """Load centerline GeoJSON."""
    gdf = gpd.read_file(CENTERLINE_PATH)
    return gdf


def check_crs(gdf):
    """Check 1: CRS must be EPSG:4326."""
    if gdf.crs is None:
        return False, "CRS is missing", None
    if gdf.crs.to_epsg() != 4326:
        # Reproject
        gdf = gdf.to_crs(TARGET_CRS)
        return True, f"CRS was {gdf.crs}, reprojected to EPSG:4326", gdf
    return True, "CRS is EPSG:4326", gdf


def check_geometry_type(gdf):
    """Check 2: Only LineString or MultiLineString."""
    valid_types = {"LineString", "MultiLineString"}
    geom_types = set(gdf.geometry.type.unique())
    invalid = geom_types - valid_types
    if invalid:
        return False, f"Invalid geometry types: {invalid}", None
    return True, f"Geometry types: {geom_types}", gdf


def merge_geometries(gdf):
    """Check 3: Merge all features into one geometry."""
    merged = unary_union(gdf.geometry.tolist())
    if isinstance(merged, MultiLineString):
        # Try to merge into single LineString
        merged = linemerge(merged)
    feature_count = len(gdf)
    return merged, feature_count


def check_multiline_gaps(geom):
    """Check 4: If MultiLineString with gaps, report gap distances."""
    if isinstance(geom, LineString):
        return True, "Single LineString (no gaps)", []
    elif isinstance(geom, MultiLineString):
        gaps = []
        lines = list(geom.geoms)
        for i in range(len(lines) - 1):
            gap = lines[i].distance(lines[i + 1])
            if gap > 0:
                # Convert to metres (approximate at this latitude)
                gap_m = gap * 111320 * np.cos(np.radians(28.65))
                gaps.append((i, i + 1, gap_m))
        if gaps:
            return True, f"MultiLineString with {len(gaps)} gaps", gaps
        else:
            return True, "MultiLineString (connected)", []
    return True, "Unknown geometry type", []


def check_length(geom):
    """Check 5: Length in EPSG:32643 (UTM 43N)."""
    gdf_utm = gpd.GeoSeries([geom], crs=TARGET_CRS).to_crs(UTM_CRS)
    length_m = gdf_utm.length.iloc[0]
    length_km = length_m / 1000
    if EXPECTED_LENGTH_KM_MIN <= length_km <= EXPECTED_LENGTH_KM_MAX:
        return True, f"Length: {length_km:.2f} km (within {EXPECTED_LENGTH_KM_MIN}-{EXPECTED_LENGTH_KM_MAX} km)", length_km
    else:
        return False, f"Length: {length_km:.2f} km (OUTSIDE {EXPECTED_LENGTH_KM_MIN}-{EXPECTED_LENGTH_KM_MAX} km)", length_km


def check_vertices_in_aoi(geom):
    """Check 6: Every vertex inside AOI with buffer."""
    if isinstance(geom, LineString):
        coords = list(geom.coords)
    elif isinstance(geom, MultiLineString):
        coords = []
        for line in geom.geoms:
            coords.extend(list(line.coords))
    else:
        return False, "Cannot extract vertices", 0

    aoi_box = box(AOI_BOUNDS[0] - AOI_BUFFER_DEG, AOI_BOUNDS[1] - AOI_BUFFER_DEG,
                  AOI_BOUNDS[2] + AOI_BUFFER_DEG, AOI_BOUNDS[3] + AOI_BUFFER_DEG)

    outside = []
    for i, (x, y) in enumerate(coords):
        pt = Point(x, y)
        if not aoi_box.contains(pt):
            outside.append((i, x, y))

    if outside:
        return False, f"{len(outside)} vertices outside AOI buffer", outside
    return True, f"All {len(coords)} vertices inside AOI buffer", []


def check_direction(geom):
    """Check 7: Start should be north (higher latitude) of end."""
    if isinstance(geom, LineString):
        coords = list(geom.coords)
    elif isinstance(geom, MultiLineString):
        # Use first point of first line and last point of last line
        first_line = list(geom.geoms)[0]
        last_line = list(geom.geoms)[-1]
        coords = [list(first_line.coords)[0], list(last_line.coords)[-1]]
    else:
        return False, "Cannot determine direction", None

    start_lat = coords[0][1]
    end_lat = coords[-1][1]

    if start_lat > end_lat:
        return True, "Direction OK: start (north) to end (south)", False
    else:
        return True, "Direction REVERSED: start is south of end", True


def check_segment_lengths(geom):
    """Check 8: Any vertex-to-vertex segment > 1000 m."""
    if isinstance(geom, LineString):
        coords = list(geom.coords)
    elif isinstance(geom, MultiLineString):
        coords = []
        for line in geom.geoms:
            coords.extend(list(line.coords))
    else:
        return True, "Cannot check segments", []

    long_segments = []
    for i in range(len(coords) - 1):
        x1, y1 = coords[i]
        x2, y2 = coords[i + 1]
        # Approximate distance in metres
        dx = (x2 - x1) * 111320 * np.cos(np.radians((y1 + y2) / 2))
        dy = (y2 - y1) * 110574
        dist_m = np.sqrt(dx**2 + dy**2)
        if dist_m > MAX_SEGMENT_M:
            long_segments.append((i, dist_m, (x1, y1), (x2, y2)))

    if long_segments:
        return True, f"{len(long_segments)} segments > {MAX_SEGMENT_M} m", long_segments
    return True, f"No segments > {MAX_SEGMENT_M} m", []


def check_self_intersection(geom):
    """Check 9: Self-intersection."""
    if isinstance(geom, LineString):
        if not geom.is_simple:
            # Find intersection points
            return False, "LineString is not simple (self-intersects)", []
        return True, "No self-intersection", []
    elif isinstance(geom, MultiLineString):
        # Check each line and cross-line intersections
        lines = list(geom.geoms)
        for i, line in enumerate(lines):
            if not line.is_simple:
                return False, f"Line {i} self-intersects", []
        # Check cross intersections
        for i in range(len(lines)):
            for j in range(i + 1, len(lines)):
                if lines[i].crosses(lines[j]):
                    return False, f"Lines {i} and {j} cross", []
        return True, "No self-intersections", []
    return True, "Unknown geometry", []


def save_oriented(geom, reversed_flag):
    """Save oriented centerline if reversed."""
    if reversed_flag:
        if isinstance(geom, LineString):
            oriented = LineString(list(geom.coords)[::-1])
        elif isinstance(geom, MultiLineString):
            lines = [LineString(list(line.coords)[::-1]) for line in geom.geoms]
            oriented = MultiLineString(lines[::-1])
        else:
            return False

        gdf_out = gpd.GeoDataFrame(geometry=[oriented], crs=TARGET_CRS)
        gdf_out.to_file(ORIENTED_PATH, driver="GeoJSON")
        return True
    return False


def create_validation_map(geom, aoi_bounds, output_path, reversed_flag=False):
    """Create validation visualization map."""
    fig, ax = plt.subplots(1, 1, figsize=(10, 10))

    # Plot centerline
    if isinstance(geom, LineString):
        x, y = geom.xy
        ax.plot(x, y, 'b-', linewidth=2, label='Centerline')
        ax.plot(x[0], y[0], 'go', markersize=10, label='Start (Palla)')
        ax.plot(x[-1], y[-1], 'ro', markersize=10, label='End (Jaitpur)')
    elif isinstance(geom, MultiLineString):
        for i, line in enumerate(geom.geoms):
            x, y = line.xy
            if i == 0:
                ax.plot(x, y, 'b-', linewidth=2, label='Centerline')
            else:
                ax.plot(x, y, 'b-', linewidth=2)
        # Start of first, end of last
        first = list(geom.geoms)[0]
        last = list(geom.geoms)[-1]
        fx, fy = list(first.coords)[0]
        lx, ly = list(last.coords)[-1]
        ax.plot(fx, fy, 'go', markersize=10, label='Start (Palla)')
        ax.plot(lx, ly, 'ro', markersize=10, label='End (Jaitpur)')

    # Plot AOI rectangle
    west, south, east, north = aoi_bounds
    rect = Rectangle((west, south), east - west, north - south,
                     linewidth=2, edgecolor='red', facecolor='none', linestyle='--',
                     label='AOI')
    ax.add_patch(rect)

    # Add basemap
    try:
        ctx.add_basemap(ax, crs=TARGET_CRS, source=ctx.providers.OpenStreetMap.Mapnik, zoom=11)
    except Exception:
        pass  # Basemap optional

    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    ax.set_title('Yamuna Centerline Validation')
    ax.legend()
    ax.set_aspect('equal')

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Written: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Validate Yamuna centerline")
    parser.add_argument("--continue", dest="force_continue", action="store_true",
                        help="Continue even if centerline missing (for testing)")
    args = parser.parse_args()

    validation_lines = []
    validation_lines.append("=" * 60)
    validation_lines.append("YAMUNA CENTERLINE VALIDATION REPORT")
    validation_lines.append("=" * 60)
    validation_lines.append("")

    # Check 2a: File exists
    ok, msg = check_file_exists()
    validation_lines.append(f"[CHECK 2a] File exists: {'PASS' if ok else 'FAIL'} - {msg}")
    if not ok:
        validation_lines.append("")
        validation_lines.append("BLOCKED: Centerline file not found.")
        validation_lines.append("Digitise the Yamuna centreline in QGIS as a LineString")
        validation_lines.append("in EPSG:4326 from Palla (north, upstream) to Jaitpur")
        validation_lines.append("(south, downstream), follow the main channel, and")
        validation_lines.append("export as GeoJSON to:")
        validation_lines.append(f"  {CENTERLINE_PATH}")
        validation_lines.append("Then tell OpenCode to continue.")
        write_validation(VALIDATION_TXT, validation_lines)
        print("\n" + "\n".join(validation_lines))
        print("\nDigitise the Yamuna centreline in QGIS as a LineString in EPSG:4326")
        print("from Palla (north, upstream) to Jaitpur (south, downstream),")
        print("follow the main channel, and export as GeoJSON to the path above.")
        print("Then tell OpenCode to continue.")
        sys.exit(1)

    # Load centerline
    gdf = load_centerline()
    validation_lines.append(f"[INFO] Loaded {len(gdf)} feature(s)")

    # Check 1: CRS
    ok, msg, gdf = check_crs(gdf)
    validation_lines.append(f"[CHECK 1] CRS: {'PASS' if ok else 'FAIL'} - {msg}")
    if not ok:
        write_validation(VALIDATION_TXT, validation_lines)
        sys.exit(1)

    # Check 2: Geometry type
    ok, msg, gdf = check_geometry_type(gdf)
    validation_lines.append(f"[CHECK 2] Geometry type: {'PASS' if ok else 'FAIL'} - {msg}")
    if not ok:
        write_validation(VALIDATION_TXT, validation_lines)
        sys.exit(1)

    # Check 3: Merge geometries
    merged_geom, feat_count = merge_geometries(gdf)
    validation_lines.append(f"[CHECK 3] Merged {feat_count} feature(s) into {type(merged_geom).__name__}")

    # Check 4: MultiLineString gaps
    ok, msg, gaps = check_multiline_gaps(merged_geom)
    validation_lines.append(f"[CHECK 4] Gaps: {'WARN' if gaps else 'PASS'} - {msg}")
    if gaps:
        for i, j, dist in gaps:
            validation_lines.append(f"  Gap between lines {i}-{j}: {dist:.1f} m")

    # Check 5: Length
    ok, msg, length_km = check_length(merged_geom)
    validation_lines.append(f"[CHECK 5] Length: {'PASS' if ok else 'FAIL'} - {msg}")
    if not ok:
        write_validation(VALIDATION_TXT, validation_lines)
        sys.exit(1)

    # Check 6: Vertices in AOI
    ok, msg, outside = check_vertices_in_aoi(merged_geom)
    validation_lines.append(f"[CHECK 6] Vertices in AOI: {'PASS' if ok else 'FAIL'} - {msg}")
    if not ok:
        for idx, x, y in outside[:10]:
            validation_lines.append(f"  Vertex {idx}: ({x:.6f}, {y:.6f})")
        if len(outside) > 10:
            validation_lines.append(f"  ... and {len(outside) - 10} more")
        write_validation(VALIDATION_TXT, validation_lines)
        sys.exit(1)

    # Check 7: Direction
    ok, msg, reversed_flag = check_direction(merged_geom)
    validation_lines.append(f"[CHECK 7] Direction: {'WARN' if reversed_flag else 'PASS'} - {msg}")
    if reversed_flag:
        saved = save_oriented(merged_geom, reversed_flag)
        if saved:
            validation_lines.append(f"  Saved oriented version to: {ORIENTED_PATH}")

    # Check 8: Segment lengths
    ok, msg, long_segs = check_segment_lengths(merged_geom)
    validation_lines.append(f"[CHECK 8] Segment lengths: {'WARN' if long_segs else 'PASS'} - {msg}")
    if long_segs:
        for idx, dist, p1, p2 in long_segs[:10]:
            validation_lines.append(f"  Segment {idx}: {dist:.1f} m, {p1} -> {p2}")
        if len(long_segs) > 10:
            validation_lines.append(f"  ... and {len(long_segs) - 10} more")

    # Check 9: Self-intersection
    ok, msg, _ = check_self_intersection(merged_geom)
    validation_lines.append(f"[CHECK 9] Self-intersection: {'PASS' if ok else 'FAIL'} - {msg}")
    if not ok:
        write_validation(VALIDATION_TXT, validation_lines)
        sys.exit(1)

    # Create validation map
    create_validation_map(merged_geom, AOI_BOUNDS, VALIDATION_PNG, reversed_flag)

    validation_lines.append("")
    validation_lines.append("=" * 60)
    validation_lines.append("OVERALL: PASS")
    validation_lines.append("=" * 60)
    validation_lines.append("")
    validation_lines.append("Open centerline_check.png and confirm the line follows")
    validation_lines.append("the river. Note any braided or ambiguous sections.")
    validation_lines.append("Then tell OpenCode to continue.")

    write_validation(VALIDATION_TXT, validation_lines)
    print("\n" + "\n".join(validation_lines))
    print("\nOpen centerline_check.png and confirm the line follows the river.")
    print("Note any braided or ambiguous sections. Then tell OpenCode to continue.")
    sys.exit(0)


if __name__ == "__main__":
    main()