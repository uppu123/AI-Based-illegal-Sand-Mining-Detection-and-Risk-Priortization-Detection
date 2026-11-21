# Stacking Order Check - Sentinel-2 Band Order Analysis

**Date:** 2026-10-28
**Script analyzed:** `C:\New folder\extract_yamuna_data.py`
**Function:** `process_sentinel2_products()` (lines 875-1052)

---

## 1. Band File Listing and Stacking Order

### Lines that build the band list and stacking order:

**Line 99 (constants):**
```python
S2_10M_BANDS = ["B2", "B3", "B4", "B8"]
S2_20M_BANDS = ["B5", "B6", "B7", "B8A", "B11", "B12"]
S2_SPECTRAL_BANDS = S2_10M_BANDS + S2_20M_BANDS          # 10 bands
```

**Lines 990-998 (band loading loop):**
```python
for band in S2_SPECTRAL_BANDS:
    resn = "R10m" if band in S2_10M_BANDS else "R20m"
    data = load_band(safe, band, resn, Resampling.bilinear)
    if data is None:
        continue
    if valid is not None:
        data = data.copy()
        data[~valid] = np.nan
    bands_arrays.setdefault(band, []).append(data)
```

**Lines 1007-1011 (median composite per band):**
```python
for band, arrs in bands_arrays.items():
    stack = np.stack(arrs, axis=0)          # (n, H, W) float32
    med = np.nanmedian(stack, axis=0)       # float64
    med[~np.isfinite(med)] = 0
    medians[band] = med
```

**Lines 1030-1040 (output writing):**
```python
out_bands = []
for b in S2_SPECTRAL_BANDS:
    arr = medians.get(b)
    if arr is None:
        logger.warning(f"  missing band {b} in composite")
        arr = np.zeros((height, width), dtype=np.float32)
    out_bands.append(np.clip(np.round(arr * 10000), 0, 65535).astype(np.uint16))
for name in S2_INDEX_BANDS:
    arr = indices.get(name)
    if arr is None:
        arr = np.zeros((height, width), dtype=np.float32)
    out_bands.append(np.clip(np.round((arr + 1) * 5000), 0, 65535).astype(np.uint16))
```

**Lines 1048-1050 (writing):**
```python
with rasterio.open(out_tif, "w", **profile) as dst:
    for i, band_arr in enumerate(out_bands, start=1):
        dst.write(band_arr, i)
```

**Order source:** Hard-coded list `S2_SPECTRAL_BANDS = S2_10M_BANDS + S2_20M_BANDS`. No `sorted()` is used. The order comes from concatenating two hard-coded lists: 10m bands first, then 20m bands.

---

## 2. Sorted Order of Band Names

If `sorted()` were applied to the 10 band names as plain strings:

```python
bands = ["B2", "B3", "B4", "B5", "B6", "B7", "B8", "B8A", "B11", "B12"]
sorted(bands)
```

**Result:**
```
['B11', 'B12', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B8A']
```

**Note:** `B8A` comes **last** (lexicographically after `B8` because 'A' > '' in string comparison). This is **not** the wavelength order.

---

## 3. Position vs. Band Name Mapping

### Stacking Order (from `S2_SPECTRAL_BANDS = S2_10M_BANDS + S2_20M_BANDS`):

| File Position (1-based) | Band Written | Band Actually Stored |
|-------------------------|--------------|----------------------|
| 1 | B2 | B2 |
| 2 | B3 | B3 |
| 3 | B4 | B4 |
| **4** | **B8** | **B5** |
| **5** | **B5** | **B6** |
| 6 | B6 | B7 |
| 7 | B7 | B8 |
| 8 | B8A | B8A |
| 9 | B11 | B11 |
| 10 | B12 | B12 |

### Index Computation (lines 1014-1026) - uses dictionary keys (CORRECT):

| Index | Formula | Bands Used | Correct? |
|-------|---------|------------|----------|
| NDVI | `(b8 - b4) / (b8 + b4)` | B8, B4 | ✅ Uses `medians["B8"]`, `medians["B4"]` |
| NDWI | `(b3 - b8) / (b3 + b8)` | B3, B8 | ✅ Uses `medians["B3"]`, `medians["B8"]` |
| NDBI | `(b11 - b8) / (b11 + b8)` | B11, B8 | ✅ Uses `medians["B11"]`, `medians["B8"]` |
| NDSI | `(b3 - b11) / (b3 + b11)` | B3, B11 | ✅ Uses `medians["B3"]`, `medians["B11"]` |

**The index computation is CORRECT** because it uses dictionary keys (`medians["B8"]`, etc.).

### Output Writing (lines 1030-1050) - WRONG ORDER:

The `out_bands` list is built by iterating `S2_SPECTRAL_BANDS` in the WRONG order, so the file positions are wrong:

| Output Position | Band Written | Should Be |
|-----------------|--------------|-----------|
| 1 | B2 | B2 ✅ |
| 2 | B3 | B3 ✅ |
| 3 | B4 | B4 ✅ |
| **4** | **B8** | **B5** ❌ |
| **5** | **B5** | **B6** ❌ |
| 6 | B6 | B7 ❌ |
| 7 | B7 | B8 ❌ |
| 8 | B8A | B8A ✅ |
| 9 | B11 | B11 ✅ |
| 10 | B12 | B12 ✅ |
| 11 | NDVI | NDVI ✅ |
| 12 | NDWI | NDWI ✅ |
| 13 | NDBI | NDBI ✅ |
| 14 | NDSI | NDSI ✅ |

---

## 4. NIR/SWIR Assignments for Indices

| Index | NIR Band | SWIR Band | Correct Under Stacking Order? |
|-------|----------|-----------|-------------------------------|
| NDVI | B8 (position 4) | B4 (position 3) | ❌ Position 4 actually has B5 data |
| NDWI | B8 (position 4) | B3 (position 2) | ❌ Position 4 has B5 data |
| NDBI | B8 (position 4) | B11 (position 9) | ❌ Position 4 has B5 data |
| NDSI | N/A | B3 (pos 2), B11 (pos 9) | ✅ Both positions correct |

**The NIR assignments are INCORRECT under the stacking order** because position 4 contains B5 (Red Edge 1) data, not B8 (NIR).

However, **the index computation itself is correct** because it accesses `medians["B8"]` by dictionary key. The error is only in the output file layout.

---

## 5. Can Bands Be Relabelled In Place?

**No, the bands cannot be reliably relabelled in place without re-reading the source data.**

**Reason:** The file has B8 data at position 4 and B5 data at position 5, but we cannot distinguish which is which from the file alone because:
1. Both are 10m resolution bands
2. Both have similar value ranges (1000-15000)
3. No metadata in the file records the band name (band descriptions are all `None`)
4. The spectral response functions overlap (Red Edge 1 ~705nm, NIR ~842nm)

**Missing information:**
- Band descriptions/metadata in the GeoTIFF tags (currently all `None`)
- The original SAFE directories with their IMG_DATA folder structure
- A mapping file that was not written during processing

**What would be needed:**
- The original SAFE directories to re-extract with correct order, OR
- A band mapping file written during processing (not created), OR
- External reference data to identify bands by spectral signature

---

## 6. Summary

| Aspect | Status |
|--------|--------|
| Band loading order | Hard-coded concatenation: `S2_10M_BANDS + S2_20M_BANDS` |
| Band stacking order | B2, B3, B4, B8, B5, B6, B7, B8A, B11, B12 |
| Correct wavelength order | B2, B3, B4, B5, B6, B7, B8, B8A, B11, B12 |
| Index computation | **CORRECT** (uses dict keys) |
| Output file band order | **WRONG** - B8 at position 4, B5 at position 5 |
| NIR in output | **WRONG** - B8 data at position 4 (should be position 7) |
| NDSI | Works (doesn't use NIR) |
| Relabel in place | **NOT POSSIBLE** - no band metadata, B5/B8 indistinguishable |
| Fix required | Rebuild composites with correct `S2_SPECTRAL_BANDS` order |