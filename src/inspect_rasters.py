# -*- coding: utf-8 -*-
"""Read-only: report raster metadata + band tables for the Yamuna products and chips."""
import io, sys, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import rasterio

BASE = r"C:\New folder\yamuna_data"
CH = r"C:\New folder\yamuna_work\chips"
S1CH = r"C:\New folder\yamuna_work\chips_s1"

TARGETS = [
    (os.path.join(BASE, r"sentinel2\2023_2024\S2_2023_Q2_composite.tif"), "SENTINEL-2 QUARTERLY COMPOSITE"),
    (os.path.join(BASE, r"sentinel2\2018\S2_2018_composite.tif"), "SENTINEL-2 ANNUAL COMPOSITE"),
    (os.path.join(BASE, r"sentinel1\2023_2024\S1_2023_Q2_VV.tif"), "SENTINEL-1 VV"),
    (os.path.join(BASE, r"landsat8\2023_2024\L8_2023_Q2_thermal.tif"), "LANDSAT-8 THERMAL"),
]


def report(path, label):
    print("=" * 100)
    if not os.path.exists(path):
        print("MISSING:", path)
        return
    mb = os.path.getsize(path) / 1024.0 / 1024.0
    with rasterio.open(path) as d:
        print("%s  (%.1f MB)" % (label, mb))
        print("  file      :", os.path.basename(path))
        print("  size      : %d x %d px" % (d.width, d.height))
        print("  bands     : %d   dtype: %s   nodata: %s" % (d.count, d.dtypes[0], d.nodata))
        print("  crs       :", d.crs)
        print("  resolution: %.1f x %.1f m" % (d.res[0], d.res[1]))
        b = d.bounds
        print("  bounds    : lon %.3f-%.3f  lat %.3f-%.3f" % (b.left, b.right, b.bottom, b.top))
        print("  footprint : %.1f x %.1f km" % ((b.right - b.left) * 111 * 0.88, (b.top - b.bottom) * 111))
        print("  --- bands ---")
        for i in range(1, d.count + 1):
            desc = (d.descriptions[i - 1] or "").strip()
            print("   %2d  %-28s" % (i, desc if desc else "<no description>"))


for p, l in TARGETS:
    report(p, l)

for d_, name in ((CH, "SENTINEL-2 CHIP"), (S1CH, "SENTINEL-1 CHIP")):
    sample = None
    for q in sorted(os.listdir(d_)):
        qp = os.path.join(d_, q)
        if os.path.isdir(qp):
            tifs = [f for f in os.listdir(qp) if f.lower().endswith(".tif")]
            if tifs:
                sample = os.path.join(qp, sorted(tifs)[0])
                break
    if sample:
        report(sample, name + " (sample)")
