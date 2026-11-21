#!/usr/bin/env python3
"""
generate_centerline_s1.py

Extract Yamuna river centerline from Sentinel-1 VV backscatter.
S1 shows water as very low backscatter (dark) year-round.
Much more reliable than dry-season S2 NDWI.
"""

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
from skimage import morphology, measure, filters
import warnings
warnings.filterwarnings("ignore")


# ============================================================
# CONFIGURATION
# ============================================================
# Use S1 quarterly composite - Q2 (pre-monsoon) should show river well
S1_PATH = Path(r"C:\New folder\yamuna_data\sentinel1\2023_2024\S1_2023_Q2_VV.tif")
OUTPUT_PATH = Path(r"C:\New folder\yamuna_work\centerline\yamuna_centerline.geojson")
AOI_BOUNDS = (77.15, 28.54, 77.32, 28.76)  # west, south, east, north

# S1 VV: water has very low backscatter (dark)
# Values are uint16 sigma0 * 100 (or similar scaling)
# We'll use Otsu thresholding on the VV band

# Morphological parameters
SMALL_OBJECTS_SIZE = 500
CLOSING_RADIUS = 3
DILATION_RADIUS = 2


def extract_water_mask_s1(vv_band):
    """Create water mask from S1 VV backscatter."""
    # VV is uint16, water = very low values
    # Use adaptive approach: Otsu threshold on valid pixels
    valid = vv_band > 0
    if np.sum(valid) < 1000:
        return np.zeros_like(vv_band, dtype=bool)
    
    # Otsu threshold on valid pixels
    try:
        thresh = filters.threshold_otsu(vv_band[valid])
        water = (vv_band < thresh) & valid
    except Exception:
        # Fallback: fixed low threshold
        water = (vv_band < 1000) & valid
    
    # Morphological cleanup
    water = morphology.remove_small_objects(water, min_size=SMALL_OBJECTS_SIZE)
    water = morphology.binary_closing(water, morphology.disk(CLOSING_RADIUS))
    water = morphology.binary_dilation(water, morphology.disk(DILATION_RADIUS))
    
    # Keep largest connected component (main river)
    labeled = measure.label(water)
    props = measure.regionprops(labeled)
    if not props:
        return water
    largest = max(props, key=lambda p: p.area)
    water = (labeled == largest.label)
    
    return water


def skeletonize_river(water_mask):
    """Skeletonize water mask to get centerline."""
    skeleton = morphology.skeletonize(water_mask)
    skeleton = morphology.remove_small_objects(skeleton, min_size=100)
    return skeleton


def skeleton_to_linestring(skeleton, transform):
    """Convert skeleton pixels to ordered LineString(s)."""
    rows, cols = np.where(skeleton)
    if len(rows) < 10:
        return None

    # Label connected components
    labeled = measure.label(skeleton, connectivity=2)
    lines = []
    
    for region in measure.regionprops(labeled):
        r_coords = region.coords
        if len(r_coords) < 20:
            continue
        
        # Order coordinates
        line_coords = order_skeleton_coords(r_coords, transform)
        if len(line_coords) >= 2:
            lines.append(LineString(line_coords))
    
    if not lines:
        return None
    elif len(lines) == 1:
        return lines[0]
    else:
        merged = linemerge(lines)
        return merged


def order_skeleton_coords(coords_rc, transform):
    """Order skeleton pixel coordinates from one end to another."""
    rows, cols = coords_rc[:, 0], coords_rc[:, 1]
    xs, ys = rasterio.transform.xy(transform, rows, cols, offset='center')
    pts = list(zip(xs, ys))
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
        lines.sort(key=lambda l: list(l.coords)[0][1], reverse=True)
        return MultiLineString(lines)
    return geom


def validate_centerline(geom):
    """Basic validation."""
    issues = []
    if geom is None or geom.is_empty:
        issues.append("Empty geometry")
        return False, issues

    gdf = gpd.GeoSeries([geom], crs="EPSG:4326").to_crs("EPSG:32643")
    length_km = gdf.length.iloc[0] / 1000
    if not (40 <= length_km <= 65):
        issues.append(f"Length {length_km:.1f} km outside expected 40-65 km")

    if isinstance(geom, LineString):
        n_vertices = len(geom.coords)
    else:
        n_vertices = sum(len(l.coords) for l in geom.geoms)
    if n_vertices < 30:
        issues.append(f"Only {n_vertices} vertices (too few)")

    b = geom.bounds
    if b[0] < AOI_BOUNDS[0] - 0.02 or b[2] > AOI_BOUNDS[2] + 0.02:
        issues.append(f"Bounds {b} exceed AOI significantly")

    return len(issues) == 0, issues


def main():
    parser = argparse.ArgumentParser(description="Generate Yamuna centerline from S1 VV")
    parser.add_argument("--s1", default=str(S1_PATH), help="Path to S1 VV composite")
    parser.add_argument("--out", default=str(OUTPUT_PATH), help="Output GeoJSON path")
    args = parser.parse_args()

    s1_path = Path(args.s1)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Loading: {s1_path}")
    if not s1_path.exists():
        print(f"ERROR: File not found: {s1_path}")
        sys.exit(1)

    with rasterio.open(s1_path) as src:
        print(f"  CRS: {src.crs}")
        print(f"  Shape: {src.height} x {src.width}")
        print(f"  Bands: {src.count}")
        vv = src.read(1)
        transform = src.transform
        crs = src.crs
        nodata = src.nodata

    print(f"  VV range: {np.min(vv[vv>0])} to {np.max(vv)} (nodata={nodata})")

    # Extract water mask
    print("  Extracting water mask from S1 VV...")
    water = extract_water_mask_s1(vv)
    print(f"  Water pixels: {np.sum(water)} / {water.size} ({100*np.sum(water)/water.size:.1f}%)")

    # Debug: save water mask
    debug_mask = out_path.parent / "debug_s1_water_mask.tif"
    with rasterio.open(s1_path) as src:
        profile = src.profile
        profile.update(count=1, dtype='uint8', nodata=0)
        with rasterio.open(debug_mask, 'w', **profile) as dst:
            dst.write(water.astype(np.uint8), 1)
    print(f"  Debug water mask saved: {debug_mask}")

    # Skeletonize
    print("  Skeletonizing...")
    skeleton = skeletonize_river(water)
    print(f"  Skeleton pixels: {np.sum(skeleton)}")

    # Debug skeleton
    debug_skel = out_path.parent / "debug_s1_skeleton.tif"
    with rasterio.open(s1_path) as src:
        profile = src.profile
        profile.update(count=1, dtype='uint8', nodata=0)
        with rasterio.open(debug_skel, 'w', **profile) as dst:
            dst.write(skeleton.astype(np.uint8), 1)
    print(f"  Debug skeleton saved: {debug_skel}")

    # Convert to LineString
    print("  Converting to vector...")
    geom = skeleton_to_linestring(skeleton, transform)

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

    # Save (use temp name if locked)
    temp_path = out_path.with_name(out_path.stem + "_new.geojson")
    gdf_out = gpd.GeoDataFrame(geometry=[geom], crs="EPSG:4326")
    gdf_out.to_file(temp_path, driver="GeoJSON")
    print(f"Saved to: {temp_path}")
    print(f"Replace {out_path} with this file when QGIS is closed")
    print(f"\nSaved: {out_path}")
    print(f"Geometry type: {geom.geom_type}")
    vcount = len(geom.coords) if isinstance(geom, LineString) else sum(len(l.coords) for l in geom.geoms)
    print(f"Vertex count: {vcount}")

    gdf_utm = gdf_out.to_crs("EPSG:32643")
    length_km = gdf_utm.length.iloc[0] / 1000
    print(f"Length: {length_km:.2f} km")


if __name__ == "__main__":
    main()