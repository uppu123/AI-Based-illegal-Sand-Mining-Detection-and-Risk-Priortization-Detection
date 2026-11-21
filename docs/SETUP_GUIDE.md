# Setup Guide — Yamuna River Data Collection

## 1. Create Free Accounts

### Copernicus Data Space Ecosystem (Sentinel-2 + Sentinel-1)
1. Go to https://dataspace.copernicus.eu/
2. Click **Register** (top right)
3. Fill in the form, confirm your email
4. Your **username/email + password** will be used by the script

### USGS Earth Explorer (Landsat-8)
1. Go to https://ers.cr.usgs.gov/register/
2. Click **Register** and complete the form
3. Confirm your email
4. **Create an M2M Application Token** (required since Feb 2025):
   - Sign in at https://ers.cr.usgs.gov/
   - Go to **Access Request** → **Request Access**
   - Select access type: **Machine**
   - Fill the form → submit → you'll get a **token** (long alphanumeric string)
   - Save this token — it's what the script uses (NOT your USGS password)

## 2. Install Python Dependencies

```bash
cd "C:\New folder"
pip install -r requirements.txt
```

This installs: `requests`, `tqdm`, `rasterio`, `numpy`, `landsatxplore`, `geopandas`.

## 3. Run the Script

### Preview first (recommended)
```bash
python extract_yamuna_data.py --dry-run --yes
```
This searches both APIs and prints the full download plan (sizes, scene counts) without downloading anything.

### Run the download
```bash
python extract_yamuna_data.py --base-path "C:\New folder\yamuna_data"
```

You will be prompted for:
- Copernicus username + password (hidden input)
- USGS username + password (hidden input)
- Confirmation before download starts

### Download only (skip GeoTIFF processing)
```bash
python extract_yamuna_data.py --no-process
```

### Resume after a crash
Just run the same command again — the script automatically skips already-downloaded files.

### Force restart from a specific year
```bash
python extract_yamuna_data.py --start-year 2020
```

## 4. Environment Variables (optional, skip prompts)

Set these in your terminal or a `.env` file before running:

```
set CDSE_USER=your@email.com
set CDSE_PASS=your_password
set USGS_USER=your_usgs_name
set USGS_PASS=your_usgs_password
```

## 5. Disk Space

The trimmed plan uses **~15-25 GB** total. Check your free space first:

```powershell
# PowerShell
Get-PSDrive C | Select-Object @{N='FreeGB';E={[math]::Round($_.Free/1GB)}}
```

## Troubleshooting

See `TROUBLESHOOTING.md` in the same folder.
