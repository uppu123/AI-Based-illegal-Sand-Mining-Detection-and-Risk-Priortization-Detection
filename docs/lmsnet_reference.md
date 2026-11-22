# LMS-Net Reference Check (Stage 7)

## Reference on disk
- **File**: `C:\Users\upend\Downloads\remotesensing-17-00227-v2.pdf`
- **Title**: *Lightweight Multi-Scale Network for Segmentation of Riverbank Sand Mining Area in Satellite Images*
- **Authors**: Hongyang Zhang, Shuo Liu, Huamei Liu
- **Venue**: Remote Sensing 2025, 17, 227
- **DOI**: 10.3390/rs17020227
- **Checked**: 2026-11-22 (text extracted with PyMuPDF)

## Why relevant
Directly targets riverbank sand mining area segmentation in satellite images. Proposes LMS-Net with lightweight multi-scale (LMS) blocks and channel attention; claims better efficiency than U-Net and better accuracy than lightweight baselines.

## Architecture facts extracted (paper Sections 3.2-3.4)

### Overall (Fig. 2, Sec 3.2)
- 5 levels, encoder-decoder.
- Level 1: `B1 = lms(A)`
- Levels 2-5: `Bi = lms(MaxPool(Bi-1))`, `i=2..5`
- Channel attention: `Ci = cam(Bi)`, `i=1..5`
- Decoder: `D4=[Up(C5),C4]` then `Di=[Up(lms(Di+1)),Ci]`; final `D1` through 3x3 conv + channel adjustment to output.

### LMS block (Fig. 3, Sec 3.3)
- Input goes through 5 parallel conv layers.
- First 4: 3x3, stride 1, dilation rates 1,2,3,5; each outputs 1/8 of output channels; concat to `F5` (1/2 output channels).
- 5th branch: depthwise conv on `F5` -> `F6` (same channels as `F5`).
- Output: `F0 = [F5, Depthwise(F5)]` (concat by channel = output channels).

### CAM (Fig. 4, Sec 3.4)
- Global max pool + avg pool -> two 1x1 vectors; each through shared MLP (C/8, C); add; sigmoid; multiply with input.

## Compliance status vs current repo

- `models/train_segmentation.py --lmsnet` is **NOT compliant** with this paper. It is a U-Net with ASPP-like multiscale bottleneck (dilations 1,2,4) and no LMS block/CAM/decoder structure from the paper.
- New implementation for Stage 7: `notebooks/stage7_lmsnet_kaggle.ipynb` (and local smoke) follows the paper structure, with explicit deviations below.

## Explicit deviations (must be reported)

1. **Input bands**: paper uses satellite RGB/NIR context in dataset description; our chips are 14-band Sentinel-2 composites (256x256). Model input adapted to `in_ch=14`.
2. **Task/output**: paper segments riverbank sand mining areas (2D satellite images). We use binary mining masks (1 output channel, sigmoid/BCE-Dice) on 256x256 chips.
3. **Channel schedule**: paper figure shows sizes but channel counts are not fully explicit in extracted text. Implementation uses explicit lightweight schedule `[32,64,128,256,512]` (configurable) and documents it.
4. **Training protocol**: we follow project Stage 7 gate, not paper training: 2023 mask chips GroupKFold-by-transect CV, 2024 held out report-only, flip/90° train-fold augmentation only, no leakage, sequential.
5. **Dataset**: paper uses its own benchmark dataset; we use Yamuna 28 human pixel masks / chips_fixed.
6. **Pre/post-processing**: paper-specific preprocessing/augmentation not adopted; we keep project normalization and no photometric augmentation on 14-band spectral chips.

## Gate decision
- Reference: **FOUND**.
- Old `--lmsnet` flag: **NON-COMPLIANT** for this paper.
- New paper-faithful implementation: **implemented for smoke/Kaggle verification**; Stage 7 LMS-Net gate remains BLOCKED until compliant run outputs are reviewed.