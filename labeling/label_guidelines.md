# Labeling Guidelines: Yamuna Sand Mining Detection

## Objective
Label each 256×256 chip (2023 Q2 Sentinel-2) for presence of **sand mining activity**.

## Classes

### MINING
**Evidence of active or recent sand extraction:**
- Exposed bare sand bars / riverbed sediment (bright in NDSI, low NDVI)
- Excavated pits or depressions in river channel
- Spoil heaps / stockpiles along banks
- Equipment: excavators, loaders, trucks (small bright specs)
- Barges / boats on river (elongated shapes in water)
- Tracks / haul roads on riverbed or banks (linear features)
- Sudden river channel widening or braiding

### NOT MINING
**Natural or non-mining features:**
- Open water (dark in true colour, blue in NDSI)
- Vegetated floodplain / agriculture (green in true colour, high NDVI)
- Natural vegetated river banks
- Built-up areas / settlements away from active channel
- Dry sand bars with no equipment/activity (context: seasonal)
- Clouds / haze / artefacts

### UNSURE
**Use when you cannot confidently decide:**
- Ambiguous features (could be natural or mining)
- Heavy haze/cloud obscuring >30% of chip
- Edge chips with partial coverage
- Low contrast / poor visibility
- **Count separately — do not guess.**

---

## Decision Process

1. **Open truecolour PNG** — assess overall scene
2. **Check NDSI PNG** — sand = red, water = blue, vegetation = green
3. **Look for mining signatures** (see MINING above)
4. **Assign label:** MINING / NOT MINING / UNSURE
5. **If unsure → UNSURE** (don't force a decision)

---

## Disagreements and Agreed Rules
*(Filled during agreement check between Reviewer A and Reviewer B)*

| Chip ID | Reviewer A | Reviewer B | Agreed Rule / Resolution |
|---------|------------|------------|--------------------------|
|         |            |            |                          |
|         |            |            |                          |

---

## Approved by Supervisor
**Name:** ________________________  
**Date:** ________________________
