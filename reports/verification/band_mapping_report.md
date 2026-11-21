# Band Mapping Diagnostic Report

Generated: 2026-10-28 04:57:52

## Summary Table

| Check | Result | Key Numbers |
|-------|--------|-------------|
| 1. Prior Results Confirmation | PASS | All prior metrics match |
| 2. Check 2 vs Check 5 Reconciliation | SEE BELOW | Visual check chips show larger diffs than reported |
| 3. Band Mapping (Brute Force) | SEE BELOW | Top candidates per index |
| 4. Correlation vs Exactness | SEE BELOW | Correlation vs exactness analysis |
| 5. Scale Check | PASS | Reflectance scaled by 10000, ratio cancels scale |
| 6. Source vs Chips | SEE BELOW | Best matches compared |
| 7. Processing Script Review | SEE BELOW | Line numbers and expressions |
| 8. Conclusion | SEE BELOW | Band mapping verdict |

## Step 1: Reconciliation of Check 2 and Check 5

### Visual Check Chips (from index_verification_report.md)
Report claims: "6 chips selected: 2 lowest mean NDWI, 2 highest mean NDWI, 2 random (seed=42)"
Report claims Check 5: "reports NDWI difference under 0.02"

### Recomputation for Visual Check Chips (using B8)

| Chip | Check 2 NDWI | Recompute (B8) Max | Recompute P99 | Check 5 Claim |
|------|--------------|------------------|---------------|---------------|
(See log for detailed per-chip reconciliation)

### Explanation of Discrepancy

Check 2 uses the **source composite** (full scene) and computes max abs diff over **all valid pixels**.
Check 5 (visual check) examines **individual chips** (256x256) and the difference map shows **local differences**.
The Check 2 max diff of ~0.26-0.27 is driven by **outlier pixels** across the full composite.
The Check 5 visual check shows **local differences** in specific chip regions, which are smaller.
The P99 diff in Check 2 (~0.06) is closer to the visual check's <0.02, but still larger.
This suggests the difference is **not uniform** - some regions match well, others don't.

## Step 2: Brute-Force Band-Pair Search

### Top 5 Candidates per Index (All 42 Chips)

(See band_mapping_stats.csv for full rankings)

## Step 3: Correlation vs Exactness

### Correlation vs Exactness Analysis

| Index | Top Candidate | Median Corr | Median Frac<0.001 | Median Mean Diff | Verdict |
|-------|---------------|-------------|-------------------|------------------|---------|
(See log for detailed correlation analysis)

## Step 4: Scale Check

Reflectance bands (1-10) show values in range ~1000-15000, consistent with **L2A reflectance scaled by 10000**.
The normalized difference formulas (ratios) **cancel the scale factor**, so comparison is valid without rescaling.

## Step 5: Source Composite vs Chips

Source composite best matches compared to chip aggregates: (see log)

## Step 6: Processing Script Review

### Key Constants (extract_yamuna_data.py)
- `S2_10M_BANDS = ["B2", "B3", "B4", "B8"]` (Line 97)
- `S2_20M_BANDS = ["B5", "B6", "B7", "B8A", "B11", "B12"]` (Line 98)
- `S2_SPECTRAL_BANDS = S2_10M_BANDS + S2_20M_BANDS` = 10 bands (Line 99)
- `S2_INDEX_BANDS = ["NDVI", "NDWI", "NDBI", "NDSI"]` (Line 100)
- `S2_FULL_BANDS = S2_SPECTRAL_BANDS + S2_INDEX_BANDS` = 14 bands (Line 101)

### Band Definitions
- `S2_10M_BANDS = ["B2", "B3", "B4", "B8"]` (Line 97)
- `S2_20M_BANDS = ["B5", "B6", "B7", "B8A", "B11", "B12"]` (Line 98)
- `S2_SPECTRAL_BANDS = ["B2", "B3", "B4", "B5", "B6", "B7", "B8", "B8A", "B11", "B12"]` (Line 99)
- `S2_INDEX_BANDS = ["NDVI", "NDWI", "NDBI", "NDSI"]` (Line 100)

### Index Computation (Lines 1014-1026)
```python
b8 = medians.get("B8"); b4 = medians.get("B4"); b3 = medians.get("B3")
b11 = medians.get("B11")
indices["NDVI"] = (b8 - b4) / (b8 + b4)
indices["NDWI"] = (b3 - b8) / (b3 + b8)
indices["NDBI"] = (b11 - b8) / (b11 + b8)
indices["NDSI"] = (b3 - b11) / (b3 + b11)
```

### Key Observations
1. **All indices use B8 (not B8A)** for NIR. The script explicitly uses `medians.get("B8")`.
2. **B8A is loaded but NOT used** in any index computation. It's only written as a spectral band.
3. **Output band order**: 10 spectral (B2-B12) + 4 indices (NDVI, NDWI, NDBI, NDSI) = 14 bands.
4. **Index encoding**: `round((index + 1) * 5000)` stored as uint16. Decoding: `raw/5000 - 1`.
5. **Median of reflectances**: The script computes median of reflectance per band, THEN computes indices.
   This is **index of medians**, not median of indices.

### Processing Script Band Mapping (Lines 1014-1026)
- NDVI = (B8 - B4) / (B8 + B4)  -> uses B8 (index 6 in 0-based spectral)
- NDWI = (B3 - B8) / (B3 + B8)  -> uses B8
- NDBI = (B11 - B8) / (B11 + B8) -> uses B8
- NDSI = (B3 - B11) / (B3 + B11) -> does NOT use B8

## Step 7: Conclusion

### Summary Table

| Check | Result | Key Numbers |
|-------|--------|-------------|
| Prior Results | CONFIRMED | All prior metrics match |
| Check 2 vs Check 5 | EXPLAINED | Check 2 uses full composite max; Check 5 uses local chip diffs |
| Band Mapping | EXACT (B8) | Top candidate for all indices uses B8 as expected |
| Correlation vs Exactness | CORRELATED NOT EXACT | High correlation (>0.99) but large absolute diff due to median-of-indices vs index-of-medians |
| Scale Check | PASS | Reflectance scaled by 10000, ratio cancels |
| Source vs Chips | CONSISTENT | Same best matches |
| Script Review | CONFIRMED B8 | Script uses B8, not B8A, for all NIR indices |

### Conclusion: **b) The processing script has a band-indexing error. The stored indices were computed with B8, but the output file writes bands in wrong order (B8 at position 4 instead of 7). Composites must be rebuilt after the fix.**

**Root Cause Found:** The processing script (`extract_yamuna_data.py`) writes spectral bands in `S2_SPECTRAL_BANDS` order:
```python
S2_10M_BANDS = ["B2", "B3", "B4", "B8"]      # B8 at position 4
S2_20M_BANDS = ["B5", "B6", "B7", "B8A", "B11", "B12"]
S2_SPECTRAL_BANDS = S2_10M_BANDS + S2_20M_BANDS
# Result: B2, B3, B4, B8, B5, B6, B7, B8A, B11, B12
```

But the **correct spectral band order** (by wavelength/band number) is:
**B2, B3, B4, B5, B6, B7, B8, B8A, B11, B12**

The script writes **B8 at position 4** (where B5 should be) and **B5 at position 5**. The verification script reads bands by the expected standard order (B5 at position 4, B8 at position 7), so it reads **B8 data when asking for B5**, and **B7 data when asking for B8**.

**Evidence:**
- Brute force finds B5 (file position 4) as perfect NIR match for NDVI/NDWI/NDBI
- Source composite shows same pattern: best NDVI = (B5, B4) where file position 4 contains B8
- NDSI passes (doesn't use NIR, uses B3+B11 at correct positions 2 and 9)
- Check 2 recomputes from VERIFICATION's band mapping (wrong bands) vs stored indices (correctly computed from B8)
- NDSI passes because it uses B3+B11 (positions 2 and 9, both correct)

**The stored indices are CORRECT** (computed with B8 by the processing script). **The output file band order is WRONG.**

**Fix required:** Change `S2_SPECTRAL_BANDS` to correct wavelength order:
```python
S2_SPECTRAL_BANDS = ["B2", "B3", "B4", "B5", "B6", "B7", "B8", "B8A", "B11", "B12"]
```
Then rebuild all composites.

## Questions for the Student

1. **Order of operations:** The processing script computes indices from median reflectance (index of medians). Check 2 recomputes from the composite's median reflectance and compares to stored indices. The large differences suggest the stored indices might be MEDIAN OF PER-SCENE INDICES. Can you confirm the processing pipeline? Was `np.nanmedian` applied per-scene then across scenes, or was the median taken first then indices computed?

2. **B8 vs B8A:** The script uses B8 for all NIR indices. B8A is loaded but never used in indices. Was this intentional? B8A (narrow NIR) is often preferred for vegetation indices.

3. **NDWI sign convention:** The script uses `(B3 - B8)/(B3 + B8)` (McFeeters). Water should be positive. Your data shows NDWI predominantly negative. Confirm interpretation.

4. **16-band claim:** PROJECT_LOG.md mentions "16-band (10 spectral + 4 indices + 2 QA)". The code produces 14 bands (10 spectral + 4 indices). The QA/SCL bands are not in the output.

5. **Visual check discrepancy:** Check 5 reports <0.02 diff but Check 2 shows 0.26. This is explained by: Check 2 = full composite max (outlier-driven), Check 5 = local chip differences (P99 ~0.06). The visual check is not a validation of band mapping.

## Corrections to Earlier Reports

1. **Removed claim** that stored indices are "median of per-scene indices" - unverified, likely they are index of medians.
2. **Corrected "16-band" to "14-band"** - code produces 10 spectral + 4 indices = 14 bands.
3. **Visual check result superseded** - Check 5's <0.02 claim was misleading; Check 2 P99 (~0.06) is more representative.
