#!/usr/bin/env python3
"""


legacy_centerline_from_ndwi.py

Automatically extract Yamuna river centerline from Sentinel-2 NDWI.
Uses S2_2023_Q2_composite.tif (band 12 = NDWI).
Outputs: centerline/yamuna_centerline.geojson (EPSG:4326)
"""
# --- central configuration (no hard-coded paths in pipeline scripts) ---
from pathlib import Path as _Path
import sys as _sys
_sys.path.insert(0, str(_Path(__file__).resolve().parents[2]))
from config import project_config as _cfg


import argparse
import sys
from pathlib import Path
import rasterio
from rasterio.windows import Window
import numpy as np
import geopandas as gpd
from shapely.geometry import LineString, MultiLineString, box
from shapely.ops import linemerge, unary_union
from scipy import ndimage
from skimage import morphology, measure
import warnings
warnings.filterwarnings("ignore")


# ============================================================
# CONFIGURATION
# ============================================================
S2_PATH = _cfg.S2_Q2_COMPOSITE
OUTPUT_PATH = _cfg.CENTERLINE_PATH
AOI_BOUNDS = _cfg.AOI_BOUNDS  # west, south, east, north

# NDWI band index (1-indexed in file)
NDWI_BAND = 12  # NDWI is band 12 in the 14-band composite

# Water threshold on NDWI (decoded: raw/5000 - 1)
# NDWI > 0 typically indicates water, but Yamuna may have lower values
WATER_THRESHOLD = -0.2  # Very sensitive for dry-season narrow river

# Morphological parameters
MIN_RIVER_WIDTH_PX = 1      # minimum river width in pixels
SMALL_OBJECTS_SIZE = 100    # remove objects smaller than this (px)
CLOSING_RADIUS = 5          # aggressive closing to connect fragments
DILATION_RADIUS = 3         # dilate to thicken before skeletonizing


def decode_ndwi(raw):
    """Decode uint16 NDWI: value = (index + 1) * 5000."""
    return raw.astype(np.float32) / 5000.0 - 1.0


def extract_water_mask(ndwi_decoded):
    """Create binary water mask from decoded NDWI."""
    water = ndwi_decoded > WATER_THRESHOLD
    # Remove small noise
    water = morphology.remove_small_objects(water, min_size=SMALL_OBJECTS_SIZE)
    # Close small gaps aggressively
    water = morphology.binary_closing(water, morphology.disk(CLOSING_RADIUS))
    # Dilate to thicken river
    water = morphology.binary_dilation(water, morphology.disk(DILATION_RADIUS))
    # Keep only large connected components (river)
    labeled = measure.label(water)
    props = measure.regionprops(labeled)
    if not props:
        return water
    # Keep only the largest component (main river)
    largest = max(props, key=lambda p: p.area)
    water = (labeled == largest.label)
    return water


def skeletonize_river(water_mask):
    """Skeletonize water mask to get centerline."""
    skeleton = morphology.skeletonize(water_mask)
    # Remove small spurs
    skeleton = morphology.remove_small_objects(skeleton, min_size=50)
    return skeleton


def skeleton_to_linestring(skeleton, transform, crs):
    """Convert skeleton pixels to LineString(s) in geographic coordinates."""
    # Get skeleton pixel coordinates (row, col)
    rows, cols = np.where(skeleton)
    if len(rows) == 0:
        return None

    # Convert to geographic coordinates
    # rasterio transform: x = c + a*col + b*row, y = f + d*col + e*row
    xs, ys = rasterio.transform.xy(transform, rows, cols, offset='center')
    coords = list(zip(xs, ys))

    # Group into connected components using scipy
    labeled = measure.label(skeleton, connectivity=2)
    lines = []
    for region in measure.regionprops(labeled):
        r_coords = region.coords
        if len(r_coords) < 10:  # skip tiny fragments
            continue
        # Order coordinates along the skeleton
        # Simple approach: start from one end, walk to other
        line_coords = order_skeleton_coords(r_coords, transform)
        if len(line_coords) >= 2:
            lines.append(LineString(line_coords))

    if not lines:
        return None
    elif len(lines) == 1:
        return lines[0]
    else:
        # Merge if they connect
        merged = linemerge(lines)
        return merged


def order_skeleton_coords(coords_rc, transform):
    """Order skeleton pixel coordinates from one end to another."""
    # coords_rc: array of (row, col)
    # Convert to xy
    rows, cols = coords_rc[:, 0], coords_rc[:, 1]
    xs, ys = rasterio.transform.xy(transform, rows, cols, offset='center')
    pts = list(zip(xs, ys))

    # Build adjacency (8-connected)
    n = len(pts)
    if n <= 2:
        return pts

    # Find endpoints (degree 1 in 8-neighborhood)
    endpoints = []
    for i, (r, c) in enumerate(coords_rc):
        neighbors = 0
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                nr, nc = r + dr, c + dc
                if any((coords_rc[:, 0] == nr) & (coords_rc[:, 1] == nc)):
                    neighbors += 1
        if neighbors == 1:
            endpoints.append(i)

    if len(endpoints) >= 2:
        start = endpoints[0]
    else:
        start = 0

    # Walk from start
    ordered = [pts[start]]
    visited = {start}
    current = start

    while len(ordered) < n:
        # Find nearest unvisited neighbor
        r, c = coords_rc[current]
        found = False
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                nr, nc = r + dr, c + dc
                matches = np.where((coords_rc[:, 0] == nr) & (coords_rc[:, 1] == nc))[0]
                if len(matches) > 0:
                    nxt = matches[0]
                    if nxt not in visited:
                        ordered.append(pts[nxt])
                        visited.add(nxt)
                        current = nxt
                        found = True
                        break
            if found:
                break
        if not found:
            # No unvisited neighbor, find any unvisited
            unvisited = [i for i in range(n) if i not in visited]
            if unvisited:
                current = unvisited[0]
                ordered.append(pts[current])
                visited.add(current)
            else:
                break

    return ordered


def clip_to_aoi(geom, aoi_bounds):
    """Clip geometry to AOI bounding box."""
    aoi_box = box(*aoi_bounds)
    return geom.intersection(aoi_box)


def ensure_north_to_south(geom):
    """Ensure LineString goes from north (higher lat) to south (lower lat)."""
    if isinstance(geom, LineString):
        coords = list(geom.coords)
        if coords[0][1] < coords[-1][1]:  # start lat < end lat (going north)
            return LineString(coords[::-1])
        return geom
    elif isinstance(geom, MultiLineString):
        lines = []
        for line in geom.geoms:
            coords = list(line.coords)
            if coords[0][1] < coords[-1][1]:
                lines.append(LineString(coords[::-1]))
            else:
                lines.append(line)
        # Sort lines by start latitude (descending = north to south)
        lines.sort(key=lambda l: list(l.coords)[0][1], reverse=True)
        return MultiLineString(lines)
    return geom


def validate_centerline(geom):
    """Basic validation of generated centerline."""
    issues = []
    if geom is None or geom.is_empty:
        issues.append("Empty geometry")
        return False, issues

    # Length check in UTM 43N
    gdf = gpd.GeoSeries([geom], crs="EPSG:4326").to_crs("EPSG:32643")
    length_km = gdf.length.iloc[0] / 1000
    if not (40 <= length_km <= 65):
        issues.append(f"Length {length_km:.1f} km outside expected 40-65 km")

    # Vertex count
    if isinstance(geom, LineString):
        n_vertices = len(geom.coords)
    else:
        n_vertices = sum(len(l.coords) for l in geom.geoms)
    if n_vertices < 20:
        issues.append(f"Only {n_vertices} vertices (too few)")

    # Bounds check
    b = geom.bounds
    if b[0] < AOI_BOUNDS[0] - 0.02 or b[2] > AOI_BOUNDS[2] + 0.02:
        issues.append(f"Bounds {b} exceed AOI significantly")

    return len(issues) == 0, issues


def main():
    parser = argparse.ArgumentParser(description="Generate Yamuna centerline from S2 NDWI")
    parser.add_argument("--s2", default=str(S2_PATH), help="Path to S2 composite")
    parser.add_argument("--out", default=str(OUTPUT_PATH), help="Output GeoJSON path")
    args = parser.parse_args()

    s2_path = Path(args.s2)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Loading: {s2_path}")
    if not s2_path.exists():
        print(f"ERROR: File not found: {s2_path}")
        sys.exit(1)

    with rasterio.open(s2_path) as src:
        print(f"  CRS: {src.crs}")
        print(f"  Shape: {src.height} x {src.width}")
        print(f"  Bands: {src.count}")

        # Read NDWI band (band 12)
        ndwi_raw = src.read(NDWI_BAND)
        transform = src.transform
        crs = src.crs

        print(f"  Reading NDWI band {NDWI_BAND}...")

    # Decode NDWI
    ndwi = decode_ndwi(ndwi_raw)
    print(f"  NDWI range: {np.nanmin(ndwi):.3f} to {np.nanmax(ndwi):.3f}")

    # Extract water mask
    print("  Extracting water mask...")
    water = extract_water_mask(ndwi)
    print(f"  Water pixels: {np.sum(water)} / {water.size} ({100*np.sum(water)/water.size:.1f}%)")

    # Debug: save water mask as raster for inspection
    debug_mask = out_path.parent / "debug_water_mask.tif"
    with rasterio.open(s2_path) as src:
        profile = src.profile
        profile.update(count=1, dtype='uint8', nodata=0)
        with rasterio.open(debug_mask, 'w', **profile) as dst:
            dst.write(water.astype(np.uint8), 1)
    print(f"  Debug water mask saved: {debug_mask}")

    # Skeletonize
    print("  Skeletonizing...")
    skeleton = skeletonize_river(water)
    print(f"  Skeleton pixels: {np.sum(skeleton)}")

    # Debug: save skeleton
    debug_skel = out_path.parent / "debug_skeleton.tif"
    with rasterio.open(s2_path) as src:
        profile = src.profile
        profile.update(count=1, dtype='uint8', nodata=0)
        with rasterio.open(debug_skel, 'w', **profile) as dst:
            dst.write(skeleton.astype(np.uint8), 1)
    print(f"  Debug skeleton saved: {debug_skel}")

    # Convert to LineString
    print("  Converting to vector...")
    geom = skeleton_to_linestring(skeleton, transform, crs)

    if geom is None:
        print("ERROR: Failed to generate centerline")
        sys.exit(1)

    # Clip to AOI
    print("  Clipping to AOI...")
    geom = clip_to_aoi(geom, AOI_BOUNDS)

    # Ensure north-to-south orientation
    geom = ensure_north_to_south(geom)

    # Validate
    ok, issues = validate_centerline(geom)
    if issues:
        print("  Validation issues:")
        for issue in issues:
            print(f"    - {issue}")
    else:
        print("  Validation: PASS")

    # Save
    gdf_out = gpd.GeoDataFrame(geometry=[geom], crs="EPSG:4326")
    gdf_out.to_file(out_path, driver="GeoJSON")
    print(f"\nSaved: {out_path}")
    print(f"Geometry type: {geom.geom_type}")
    print(f"Vertex count: {len(geom.coords) if isinstance(geom, LineString) else sum(len(l.coords) for l in geom.geoms)}")

    # Print length
    gdf_utm = gdf_out.to_crs("EPSG:32643")
    length_km = gdf_utm.length.iloc[0] / 1000
    print(f"Length: {length_km:.2f} km")


if __name__ == "__main__":
    main()