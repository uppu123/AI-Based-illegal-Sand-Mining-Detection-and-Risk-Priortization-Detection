#!/usr/bin/env python3
"""


03_generate_transects.py

Generate perpendicular transects every 1000 m along the Yamuna centerline.
Uses oriented centerline (north-to-south).
Outputs: transect points, lines, table, and map.
"""
# --- central configuration (no hard-coded paths in pipeline scripts) ---
from pathlib import Path as _Path
import sys as _sys
_sys.path.insert(0, str(_Path(__file__).resolve().parents[2]))
from config import project_config as _cfg


import argparse
import sys
from pathlib import Path
import geopandas as gpd
from shapely.geometry import LineString, Point
from shapely.ops import transform as shapely_transform
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import contextily as ctx
import pyproj
from pyproj import Transformer


# ============================================================
# CONFIGURATION
# ============================================================
CENTERLINE_PATH = _cfg.CENTERLINE_ORIENTED
OUTPUT_DIR = _cfg.TRANSECT_DIR
TRANSECT_SPACING_M = 1000  # 1 km
TRANSECT_HALF_LENGTH_M = 1500  # 1.5 km each side = 3 km total
TARGET_CRS = "EPSG:4326"
UTM_CRS = "EPSG:32643"  # UTM 43N
AOI_BOUNDS = _cfg.AOI_BOUNDS  # west, south, east, north
AOI_BUFFER_DEG = 0.01


# ============================================================
# HELPER FUNCTIONS
# ============================================================
def load_centerline():
    """Load oriented centerline."""
    if not CENTERLINE_PATH.exists():
        # Fallback to original
        fallback = _cfg.CENTERLINE_PATH
        if fallback.exists():
            print(f"Warning: Oriented centerline not found, using fallback: {fallback}")
            return gpd.read_file(fallback)
        else:
            raise FileNotFoundError("No centerline file found")
    return gpd.read_file(CENTERLINE_PATH)


def reproject_to_utm(geom):
    """Reproject geometry to UTM 43N for metric calculations."""
    gdf = gpd.GeoSeries([geom], crs=TARGET_CRS)
    return gdf.to_crs(UTM_CRS).iloc[0]


def reproject_to_wgs84(geom):
    """Reproject geometry from UTM 43N to WGS84."""
    gdf = gpd.GeoSeries([geom], crs=UTM_CRS)
    return gdf.to_crs(TARGET_CRS).iloc[0]


def get_line_direction(point_before, point_after):
    """Calculate bearing from point_before to point_after in degrees."""
    dx = point_after.x - point_before.x
    dy = point_after.y - point_before.y
    bearing = np.degrees(np.arctan2(dx, dy))  # arctan2(dx, dy) for bearing from north
    return (bearing + 360) % 360


def create_transect(center_pt, bearing_deg, half_length_m):
    """Create perpendicular transect line centered at center_pt."""
    # Perpendicular bearing (bearing + 90 and bearing - 90)
    perp1 = (bearing_deg + 90) % 360
    perp2 = (bearing_deg - 90) % 360
    
    # Convert bearing to radians
    # Bearing: 0=N, 90=E, 180=S, 270=W
    # In UTM: x=easting, y=northing
    # dx = sin(bearing) * dist, dy = cos(bearing) * dist
    rad1 = np.radians(perp1)
    rad2 = np.radians(perp2)
    
    x, y = center_pt.x, center_pt.y
    
    # End points
    x1 = x + np.sin(rad1) * half_length_m
    y1 = y + np.cos(rad1) * half_length_m
    x2 = x + np.sin(rad2) * half_length_m
    y2 = y + np.cos(rad2) * half_length_m
    
    return LineString([(x1, y1), (x2, y2)])


def check_transect_in_aoi(transect_line, aoi_bounds):
    """Check if transect extends outside AOI."""
    b = transect_line.bounds
    west, south, east, north = aoi_bounds
    outside = b[0] < west - AOI_BUFFER_DEG or b[2] > east + AOI_BUFFER_DEG or \
              b[1] < south - AOI_BUFFER_DEG or b[3] > north + AOI_BUFFER_DEG
    return outside


def main():
    parser = argparse.ArgumentParser(description="Generate transects along Yamuna centerline")
    parser.add_argument("--spacing", type=int, default=TRANSECT_SPACING_M, help="Transect spacing in metres")
    parser.add_argument("--half-length", type=int, default=TRANSECT_HALF_LENGTH_M, help="Half transect length in metres")
    args = parser.parse_args()

    spacing = args.spacing
    half_length = args.half_length

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading centerline...")
    gdf = load_centerline()
    print(f"  Loaded: {len(gdf)} feature(s), CRS: {gdf.crs}")

    # Merge if MultiLineString
    if len(gdf) > 1 or gdf.iloc[0].geometry.geom_type == 'MultiLineString':
        merged = gpd.GeoSeries([gdf.geometry.unary_union], crs=gdf.crs).iloc[0]
        print(f"  Merged into single geometry: {merged.geom_type}")
    else:
        merged = gdf.iloc[0].geometry

    # Reproject to UTM for metric operations
    print("Reprojecting to UTM 43N...")
    line_utm = reproject_to_utm(merged)
    print(f"  UTM geometry: {line_utm.geom_type}, length: {line_utm.length/1000:.2f} km")

    # Generate points every `spacing` metres along the line
    total_length = line_utm.length
    distances = np.arange(0, total_length, spacing)
    print(f"  Total length: {total_length/1000:.2f} km, Transects: {len(distances)}")

    transect_data = []
    transect_lines_utm = []
    transect_points_utm = []

    for i, dist in enumerate(distances):
        # Get point at distance
        pt = line_utm.interpolate(dist)
        
        # Get bearing from points 50m before and after
        d_before = max(0, dist - 50)
        d_after = min(total_length, dist + 50)
        pt_before = line_utm.interpolate(d_before)
        pt_after = line_utm.interpolate(d_after)
        
        bearing = get_line_direction(pt_before, pt_after)
        
        # Create perpendicular transect
        transect_utm = create_transect(pt, bearing, half_length)
        
        # Convert back to WGS84
        pt_wgs = reproject_to_wgs84(pt)
        transect_wgs = reproject_to_wgs84(transect_utm)
        
        # Check AOI
        outside_aoi = check_transect_in_aoi(transect_wgs, AOI_BOUNDS)
        
        # Distance from centerline (should be 0)
        centerline_dist = pt.distance(line_utm)
        
        transect_id = f"T{i+1:03d}"
        chainage_km = dist / 1000
        
        transect_data.append({
            "transect_id": transect_id,
            "chainage_km": round(chainage_km, 3),
            "lon": round(pt_wgs.x, 6),
            "lat": round(pt_wgs.y, 6),
            "bearing_deg": round(bearing, 2),
            "outside_aoi": outside_aoi,
            "centerline_dist_m": round(centerline_dist, 2)
        })
        
        transect_points_utm.append({
            "geometry": pt_wgs,
            "transect_id": transect_id,
            "chainage_km": round(chainage_km, 3),
            "bearing_deg": round(bearing, 2)
        })
        
        transect_lines_utm.append({
            "geometry": transect_wgs,
            "transect_id": transect_id,
            "chainage_km": round(chainage_km, 3),
            "bearing_deg": round(bearing, 2),
            "length_m": 2 * half_length
        })
        
        if (i + 1) % 10 == 0:
            print(f"  Processed {i+1}/{len(distances)} transects...")

    # Create GeoDataFrames
    points_gdf = gpd.GeoDataFrame(transect_points_utm, crs=TARGET_CRS)
    lines_gdf = gpd.GeoDataFrame(transect_lines_utm, crs=TARGET_CRS)
    df = pd.DataFrame(transect_data)

    # Validation: any center point > 5m from centerline?
    max_dist = df["centerline_dist_m"].max()
    if max_dist > 5:
        print(f"WARNING: Max centerline distance = {max_dist:.2f} m (expected <= 5 m)")

    # AOI warnings
    outside_count = df["outside_aoi"].sum()
    if outside_count > 0:
        outside_ids = df[df["outside_aoi"]]["transect_id"].tolist()
        print(f"WARNING: {outside_count} transects extend outside AOI: {outside_ids[:10]}{'...' if len(outside_ids) > 10 else ''}")

    # Save outputs
    points_path = OUTPUT_DIR / "transect_points.geojson"
    lines_path = OUTPUT_DIR / "transect_lines.geojson"
    table_path = OUTPUT_DIR / "transect_table.csv"
    map_path = OUTPUT_DIR / "transect_map.png"

    points_gdf.to_file(points_path, driver="GeoJSON")
    lines_gdf.to_file(lines_path, driver="GeoJSON")
    df.to_csv(table_path, index=False)

    print(f"\nSaved:")
    print(f"  {points_path}")
    print(f"  {lines_path}")
    print(f"  {table_path}")

    # Create map
    print("Creating transect map...")
    fig, ax = plt.subplots(1, 1, figsize=(12, 10))
    
    # Plot centerline (handle MultiLineString)
    centerline_wgs = reproject_to_wgs84(line_utm)
    if centerline_wgs.geom_type == 'MultiLineString':
        for line in centerline_wgs.geoms:
            x, y = line.xy
            ax.plot(x, y, 'b-', linewidth=2)
        # Use first line for start/end markers
        first_line = list(centerline_wgs.geoms)[0]
        last_line = list(centerline_wgs.geoms)[-1]
        x0, y0 = first_line.coords[0]
        x1, y1 = last_line.coords[-1]
    else:
        x, y = centerline_wgs.xy
        ax.plot(x, y, 'b-', linewidth=2, label='Centerline')
        x0, y0 = x[0], y[0]
        x1, y1 = x[-1], y[-1]
    
    # Plot transects
    for _, row in lines_gdf.iterrows():
        tx, ty = row.geometry.xy
        color = 'red' if row.get('outside_aoi', False) else 'gray'
        alpha = 0.7 if row.get('outside_aoi', False) else 0.4
        ax.plot(tx, ty, color=color, linewidth=0.8, alpha=alpha)
    
    # Plot transect points
    px = points_gdf.geometry.x
    py = points_gdf.geometry.y
    ax.scatter(px, py, c='blue', s=10, zorder=5, label='Transect Points')
    
    # Mark Palla and Jaitpur
    ax.plot(x0, y0, 'go', markersize=12, label='Palla (Start)')
    ax.plot(x1, y1, 'ro', markersize=12, label='Jaitpur (End)')
    
    # AOI rectangle
    west, south, east, north = AOI_BOUNDS
    rect = Rectangle((west, south), east - west, north - south,
                     linewidth=2, edgecolor='red', facecolor='none', linestyle='--',
                     label='AOI')
    ax.add_patch(rect)
    
    # Basemap
    try:
        ctx.add_basemap(ax, crs=TARGET_CRS, source=ctx.providers.Esri.WorldImagery, zoom=11)
    except Exception:
        pass
    
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    ax.set_title(f'Yamuna Transects (Spacing: {spacing/1000:.1f} km, Length: {2*half_length/1000:.1f} km)')
    ax.legend()
    ax.set_aspect('equal')
    
    plt.tight_layout()
    plt.savefig(map_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  {map_path}")

    # Summary
    print(f"\n=== SUMMARY ===")
    print(f"Total transects: {len(df)}")
    print(f"Total length: {total_length/1000:.2f} km")
    print(f"Transect spacing: {spacing/1000:.1f} km")
    print(f"Transect length: {2*half_length/1000:.1f} km")
    print(f"Outside AOI: {outside_count}")

    # Check for any centerline distance > 5m
    if max_dist > 5:
        print(f"FAIL: Max centerline distance {max_dist:.2f} m > 5 m")
        sys.exit(1)

    print("SUCCESS: All checks passed")
    sys.exit(0)


if __name__ == "__main__":
    main()