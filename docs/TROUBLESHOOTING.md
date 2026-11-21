# TROUBLESHOOTING

## Installation Issues

**"rasterio" fails to install (Windows)**
rasterio depends on GDAL. Install pre-built wheels:
```bash
pip install rasterio --only-binary=rasterio
```
If that fails on Python 3.12, try: `pip install rasterio --only-binary=:all:`
or install from conda-forge: `conda install -c conda-forge rasterio`

**"landsatxplore" fails to import**
Ensure you have Python 3.8+ and run:
```bash
pip install landsatxplore>=0.14.0
```

---

## Login Errors

**"Copernicus login FAILED"**
- Double-check your username/password at https://dataspace.copernicus.eu/
- Reset your password if needed (use the same page's "Forgot password")
- The script uses the public OAuth2 token endpoint (no special API key needed)

**"USGS login FAILED"**
- Log in manually at https://earthexplorer.usgs.gov/ first to confirm your account is active
- Some USGS accounts take a few hours to activate after registration
- Ensure you are using your **USGS username**, not your email

---

## No Scenes Found

**Sentinel-2: "0 scenes found for XXXX-QX"**
This is normal for the monsoon quarters (Q3 = Aug–Sep). Cloud cover is high; few scenes pass the 15% filter. The script skips that period gracefully.

**Sentinel-1: "0 scenes found"**
Check the bounding box is correct. The AOI should overlap the Indian subcontinent in the Sentinel-1 archive. If the Copernicus API returns 0, it may be a token expiry issue — the script refreshes automatically on retry.

---

## Download Failures

**"retry 1/3" messages**
This is normal — it means a download is slow or the server paused. The script retries up to 3 times before marking a scene as failed.

**Download stalls for >5 minutes**
If the Copernicus server is slow, downloads may time out (600s). The script will retry automatically. You can also reduce parallelism:
```bash
python extract_yamuna_data.py --workers 2
```

**Resume after full crash**
Just run the same command again. The script reads `metadata/download_state.json` and skips already-downloaded files.

---

## Processing Errors

**"Processing: SCL-masked median composite failed"**
A corrupt .SAFE archive may be the cause. The script logs a warning and skips that product. You can manually re-download by removing the corresponding entry from `metadata/download_state.json`.

**rasterio cannot read a .SAFE band**
Try installing/upgrading rasterio and its GDAL dependency:
```bash
pip install --upgrade rasterio numpy
```

---

## Common CLI Flags

| Flag | What it does |
|---|---|
| `--dry-run` | Search + print plan only, no downloads |
| `--workers N` | Number of parallel downloads (1-6) |
| `--sources sentinel2` | Download only Sentinel-2 |
| `--no-process` | Download raw archives only, skip GeoTIFF processing |
| `--start-year 2021` | Skip years before 2021 |
| `--yes` | Skip the confirmation prompt |
| `--verbose` | Debug logging to console + metadata/download_log.txt |

---

## Still stuck?

1. Read `metadata/download_log.txt` — all errors are logged there with timestamps
2. Check `metadata/failed_downloads.csv` — lists every failed download with the suggested fix
3. Open a GitHub issue: https://github.com/your-team/yamuna-data/issues (or email your team lead)
