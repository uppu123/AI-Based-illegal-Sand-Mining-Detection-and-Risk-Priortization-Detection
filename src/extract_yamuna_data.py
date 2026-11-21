#!/usr/bin/env python3
"""
================================================================================
Yamuna River Sand Mining Detection - Direct Download System
================================================================================
Downloads Sentinel-2, Sentinel-1 and Landsat-8 imagery DIRECTLY to your computer
(from Copernicus Data Space Ecosystem + USGS Earth Explorer) and builds the
deliverable GeoTIFF products (composites, indices, thermal).

WHY NOT sentinelsat / Google Earth Engine?
  * sentinelsat talks to the old Copernicus Open Access Hub (SciHub), which has
    been DECOMMISSIONED. The current archive is the "Data Space Ecosystem" with
    a modern OData API. We use that API directly (still free, same credentials).
  * Earth Engine requires a cloud project + (for commercial) metered billing.
    Direct downloads avoid all of that and give you the raw data on disk.

Study area: Yamuna River, Palla to Jaitpur, Delhi
AOI (WGS84): lon 77.15 -> 77.32 | lat 28.54 -> 28.76

Usage:
  python extract_yamuna_data.py                # interactive
  python extract_yamuna_data.py --dry-run      # search but do not download
  python extract_yamuna_data.py --sources sentinel2 --workers 2
  python extract_yamuna_data.py --no-process   # download only, skip processing

Requires Python 3.8+. No GPU. Just disk space (~250 GB) + internet.
================================================================================
"""

import os
import sys
import csv
import json
import math
import time
import shutil
import getpass
import logging
import argparse
import traceback
import threading
from datetime import datetime, timezone, timedelta
from pathlib import Path

import requests
from concurrent.futures import ThreadPoolExecutor

# Optional (heavy) dependencies - imported lazily inside the functions that need
# them so the script still runs if only downloaded raw data is wanted.
#   rasterio, numpy  -> needed for GeoTIFF processing (--no-process disables)
#   tqdm             -> progress bars (falls back to plain prints)
#   landsatxplore    -> needed for the Landsat-8 part only

# ==============================================================================
# 1. CONSTANTS / CONFIGURATION
# ==============================================================================

STUDY_AREA_WKT = (
    "POLYGON((77.15 28.54, 77.32 28.54, 77.32 28.76, 77.15 28.76, 77.15 28.54))"
)
# [west, south, east, north]
STUDY_AREA = [77.15, 28.54, 77.32, 28.76]
AOI_WKT_SRID = f"SRID=4326;{STUDY_AREA_WKT}"

# Quarterly windows: name -> (start_month, start_day, end_month, end_day)
QUARTERS = {
    "Q1": (1, 1, 3, 31),
    "Q2": (4, 1, 6, 30),
    "Q3": (8, 1, 9, 30),   # monsoon window (Aug-Sep)
    "Q4": (10, 1, 12, 31),
}

# Sentinel-2 annual years: pull the single LOWEST-cloud scene for the year.
S2_ANNUAL_YEARS = [2018, 2019, 2020, 2021, 2022]

# Sentinel-2 quarterly years (download ALL scenes with < 15% cloud per quarter).
S2_QUARTERLY = {2023: ["Q1", "Q2", "Q3", "Q4"], 2024: ["Q1", "Q2"]}

# Sentinel-1 + Landsat-8 quarterly years.
S1_L8_YEARS = {2023: ["Q1", "Q2", "Q3", "Q4"], 2024: ["Q1", "Q2"]}

S2_CLOUD_MAX = 15     # percent, strict
L8_CLOUD_MAX = 10     # percent

# -----------------------------------------------------------------------------
# "Trim to fit" limits (your disk has ~153 GB free). Instead of downloading the
# full archive per quarter (which needs ~210 GB), cap how many of the cleanest
# scenes we pull for each quarterly composite. A few good scenes are enough to
# build a clean median composite and keep the total ~15-25 GB.
# -----------------------------------------------------------------------------
S2_MAX_SCENES_PER_QUARTER = 6     # ~6 GB/quarter  (was: all scenes ~20 GB)
S1_MAX_SCENES_PER_QUARTER = 8     # ~4 GB/quarter  (was: all scenes ~12 GB)
# Annual S2 years keep just the single best scene (unchanged, small).
USE_SCENE_CAPS = True             # set False to download everything (needs ~210 GB)

# Sentinel-2 spectral bands delivered as GeoTIFF (10 m + 20 m native bands).
S2_10M_BANDS = ["B2", "B3", "B4", "B8"]
S2_20M_BANDS = ["B5", "B6", "B7", "B8A", "B11", "B12"]
S2_SPECTRAL_BANDS = ["B2", "B3", "B4", "B5", "B6", "B7", "B8", "B8A", "B11", "B12"]  # 10 bands, correct wavelength order
S2_INDEX_BANDS = ["NDVI", "NDWI", "NDBI", "NDSI"]        # 4 indices
S2_FULL_BANDS = S2_SPECTRAL_BANDS + S2_INDEX_BANDS       # 14 total

# Copernicus Data Space Ecosystem endpoints
CDSE_CATALOGUE = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products"
CDSE_DOWNLOAD = "https://download.dataspace.copernicus.eu/odata/v1/Products({})/$value"
CDSE_TOKEN_URL = (
    "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/"
    "openid-connect/token"
)
CDSE_CLIENT_ID = "cdse-public"

# USGS M2M API (used via landsatxplore)
USGS_DATASET = "landsat_ot_c2_l2"

DOWNLOAD_TIMEOUT = 600      # seconds per single file stream
RETRY_ATTEMPTS = 3
HTTP_CHUNK = 1 << 20        # 1 MB chunks

# Shared mutable state for parallel download worker count (set via CLI --workers)
workers_pool = {"n": 4}

# ==============================================================================
# 2. LOGGING
# ==============================================================================

def setup_logging(base_path, verbose=False):
    """File + console logging. Log goes to metadata/download_log.txt."""
    log_dir = os.path.join(base_path, "metadata")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "download_log.txt")

    level = logging.DEBUG if verbose else logging.INFO
    fmt = "%(asctime)s [%(levelname)s] %(message)s"

    fh = logging.FileHandler(log_file, mode="a", encoding="utf-8")
    fh.setFormatter(logging.Formatter(fmt))

    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(logging.Formatter(fmt))

    logger = logging.getLogger("yamuna_downloader")
    logger.setLevel(level)
    # Avoid duplicate handlers if setup_logging is called more than once.
    if not logger.handlers:
        logger.addHandler(fh)
        logger.addHandler(ch)
    return logger


# ==============================================================================
# 3. CREDENTIALS (never hardcoded)
# ==============================================================================

def _mask(s):
    if not s:
        return "(empty)"
    if len(s) <= 2:
        return "*" * len(s)
    return s[0] + "*" * (len(s) - 2) + s[-1]


def get_credentials(env_only=False, base_path=None, sources=None):
    """
    Ask the user for Copernicus + USGS login. Falls back to environment
    variables CDSE_USER / CDSE_PASS / USGS_USER / USGS_PASS when available.
    Credentials are never written to disk.
    """
    env_creds = {
        "cdse_user": os.environ.get("CDSE_USER", ""),
        "cdse_pass": os.environ.get("CDSE_PASS", ""),
        "usgs_user": os.environ.get("USGS_USER", ""),
        "usgs_pass": os.environ.get("USGS_PASS", ""),
    }

    print("\n" + "=" * 60)
    print("LOGIN CREDENTIALS")
    print("=" * 60)
    print("Free accounts - create one if you don't have:")
    print("  Copernicus Data Space: https://dataspace.copernicus.eu/")
    print("  USGS Earth Explorer  : https://ers.cr.usgs.gov/register/")
    print("(You can set env vars CDSE_USER/CDSE_PASS/USGS_USER/USGS_PASS to\n"
          " skip these prompts next time.)")
    print()
    if not sources or "landsat8" in sources:
        print("  NOTE: For USGS, you need an M2M Application Token (not your password).")
        print("  Create one at: https://ers.cr.usgs.gov/ -> Access Request -> Machine -> Token")
    print()

    creds = {}
    if env_creds["cdse_user"]:
        print(f"  Using CDSE user from env: {_mask(env_creds['cdse_user'])}")
        creds["cdse_user"] = env_creds["cdse_user"]
        creds["cdse_pass"] = env_creds["cdse_pass"]
    else:
        creds["cdse_user"] = input("  Copernicus Data Space username/email: ").strip()
        creds["cdse_pass"] = getpass.getpass("  Copernicus Data Space password: ")

    needs_usgs = not sources or "landsat8" in sources
    if needs_usgs:
        if env_creds["usgs_user"]:
            print(f"  Using USGS user from env: {_mask(env_creds['usgs_user'])}")
            creds["usgs_user"] = env_creds["usgs_user"]
            creds["usgs_pass"] = env_creds["usgs_pass"]
        else:
            creds["usgs_user"] = input("  USGS Earth Explorer username: ").strip()
            creds["usgs_pass"] = getpass.getpass("  USGS M2M Application Token (not your password): ")
    else:
        print("  USGS not requested - skipping USGS credentials.")

    if not creds["cdse_user"] or not creds["cdse_pass"]:
        sys.exit("ERROR: Copernicus credentials are required (Sentinel-2/1).")

    return creds


def test_cdse_login(creds, logger):
    """Fetch a token to confirm CDSE credentials work."""
    print("\nVerifying Copernicus Data Space credentials...")
    try:
        client = CdseClient(creds)
        token = client.get_token()
        if token:
            print("  Copernicus login: OK")
            return True
    except Exception as e:
        logger.error(f"  Copernicus login FAILED: {e}")
        print("  Check your username/password at https://dataspace.copernicus.eu/")
        return False
    print("  Copernicus login: FAILED (no token returned)")
    return False


def test_usgs_login(creds, logger):
    """Sanity check USGS credentials via M2M API."""
    if not creds.get("usgs_user") or not creds.get("usgs_pass"):
        return True
    print("Verifying USGS credentials...")
    try:
        api = UsgsM2m(creds["usgs_user"], creds["usgs_pass"])
        api.logout()
        print("  USGS login: OK")
        return True
    except Exception as e:
        logger.error(f"  USGS login FAILED: {e}")
        print("  Check your USGS credentials at https://earthexplorer.usgs.gov/")
        return False


# ==============================================================================
# 4. CDSE ODATA CLIENT (token + search)
# ==============================================================================

class CdseClient:
    """Minimal client for the Copernicus Data Space Ecosystem OData API."""

    def __init__(self, creds):
        self.creds = creds
        self.access_token = None
        self.token_expiry = datetime.now(timezone.utc)
        self._lock = threading.Lock()

    # -- authentication --------------------------------------------------------
    def get_token(self, force=False):
        """Return a valid bearer token, refreshing when it is about to expire."""
        with self._lock:
            now = datetime.now(timezone.utc)
            if not force and self.access_token and (self.token_expiry - now).total_seconds() > 60:
                return self.access_token
            data = {
                "grant_type": "password",
                "username": self.creds["cdse_user"],
                "password": self.creds["cdse_pass"],
                "client_id": CDSE_CLIENT_ID,
            }
            r = requests.post(CDSE_TOKEN_URL, data=data, timeout=60)
            r.raise_for_status()
            j = r.json()
            self.access_token = j["access_token"]
            self.token_expiry = now + timedelta(seconds=int(j.get("expires_in", 3600)))
            return self.access_token

    # -- search ----------------------------------------------------------------
    def search(self, collection, start_dt, end_dt, max_pages=25, page_size=200):
        """
        Search one collection within [start_dt, end_dt) intersecting the AOI.
        Returns raw product records (list of dicts with 'Id','Name','ContentDate',
        'Attributes'). Cloud cover is read from Attributes later.
        """
        start_s = start_dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        end_s = end_dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        token = self.get_token()

        # Geometry intersects filter (OData v4, CDSE-specific syntax).
        geom_filter = f"OData.CSC.Intersects(area=geography'{AOI_WKT_SRID}')"
        date_filter = (
            f"ContentDate/Start ge {start_s} and ContentDate/Start lt {end_s}"
        )
        filter_str = f"Collection/Name eq '{collection}' and {date_filter} and {geom_filter}"

        records = []
        skip = 0
        for _page in range(max_pages):
            params = {
                "$filter": filter_str,
                "$expand": "Attributes",
                "$top": page_size,
                "$skip": skip,
                "$count": True,
            }
            r = requests.get(
                CDSE_CATALOGUE, params=params,
                headers={"Authorization": f"Bearer {token}"}, timeout=90,
            )
            r.raise_for_status()
            j = r.json()
            page_recs = j.get("value", [])
            total = j.get("@odata.count", 0)
            records.extend(page_recs)

            if len(page_recs) < page_size:
                break
            skip += page_size
            if skip >= total or len(records) > 2500:
                break
        return records

    @staticmethod
    def attribute(record, name):
        """Read a named attribute value from a product record."""
        for a in record.get("Attributes", []):
            if a.get("Name") == name:
                return a.get("Value")
        return None

    @staticmethod
    def process_time(record):
        """Human date of the derived (sensed) image."""
        try:
            cd = record["ContentDate"]["Start"]
            return datetime.fromisoformat(cd.replace("Z", "+00:00"))
        except Exception:
            return None

    # -- download --------------------------------------------------------------
    def download_url(self, product_id):
        return CDSE_DOWNLOAD.format(product_id)


# ==============================================================================
# 5. PARALLEL DOWNLOAD ENGINE (resumable, retrying, progress-aware)
# ==============================================================================

class DownloadState:
    """
    Persistent state so a crashed/stopped run can be resumed:
      metadata/download_state.json
      { "<product-id>": {"dest": "...", "done": true} }
    """

    def __init__(self, state_file):
        self.state_file = state_file
        self.data = {}
        self._lock = threading.Lock()
        os.makedirs(os.path.dirname(state_file), exist_ok=True)
        if os.path.exists(state_file):
            try:
                with open(state_file, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
            except Exception:
                self.data = {}

    def is_done(self, key):
        with self._lock:
            return self.data.get(key, {}).get("done", False)

    def mark_done(self, key, dest):
        with self._lock:
            self.data[key] = {"dest": dest, "done": True}
            self._save()

    def _save(self):
        tmp = self.state_file + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=1)
        os.replace(tmp, self.state_file)


def _try_tqdm():
    """Return a tqdm progress-bar factory, or a plain fallback."""
    try:
        from tqdm import tqdm
        return tqdm
    except Exception:
        class _PlainBar:
            def __init__(self, *a, **k):
                pass
            def update(self, n):
                pass
            def close(self):
                pass
            def __enter__(self):
                return self
            def __exit__(self, *a):
                return False
        return _PlainBar


def stream_download(url, dest, headers=None, timeout=DOWNLOAD_TIMEOUT,
                    resume=True, progress=None, logger=None):
    """
    Stream `url` to `dest` supporting HTTP Range resume.
    Returns True on success. Raises on fatal error.
    """
    dest = str(dest)
    headers = dict(headers or {})

    existing = 0
    if resume and os.path.exists(dest):
        existing = os.path.getsize(dest)

    tmp = dest + ".part"
    # Always write fresh into .part (avoids corrupting an existing finished file).
    mode = "ab" if (resume and existing > 0 and os.path.exists(tmp)) else "wb"
    if mode == "ab":
        start = os.path.getsize(tmp)
    else:
        start = 0
    if start > 0:
        headers["Range"] = f"bytes={start}-"

    with requests.Session() as session:
        with session.get(url, headers=headers, stream=True, timeout=timeout) as resp:
            total = int(resp.headers.get("Content-Length", 0)) + start
            if resp.status_code == 416:  # Range not satisfiable => already complete
                if os.path.exists(tmp):
                    os.replace(tmp, dest)
                return True
            resp.raise_for_status()

            with open(tmp, mode) as f:
                with progress(total=total, unit="B", unit_scale=True,
                              leave=False, desc=os.path.basename(dest)[:34]) as bar:
                    for chunk in resp.iter_content(chunk_size=HTTP_CHUNK):
                        if not chunk:
                            continue
                        f.write(chunk)
                        bar.update(len(chunk))

    # Verify size when the server gave us something to compare against.
    if existing_final := os.path.getsize(tmp):
        try:
            with requests.get(url, headers={"Range": "bytes=0-0"}, timeout=60) as r:
                cl = int(r.headers.get("Content-Range", "/-1").split("/")[-1])
                if cl > 0 and existing_final != cl:
                    raise IOError(
                        f"size mismatch after download: {existing_final} != {cl}")
        except (requests.RequestException, ValueError, IndexError):
            pass  # head-check impossible, accept file

    os.replace(tmp, dest)
    return True


def parallel_download(items, max_workers=4, state=None, logger=None, token=None, token_getter=None):
    """
    Download a list of (key, url, dest) triples in parallel.
      key  - unique id recorded in state for resume
      token - static CDSE bearer token (used if token_getter not given)
      token_getter - callable returning a fresh bearer token; re-fetched on
                     every attempt so long runs survive token expiry
    Returns (ok_list, failed_list).
    """
    if not items:
        return [], []

    bar_factory = _try_tqdm()
    ok, failed = [], []

    def headers_for():
        t = token_getter() if token_getter else token
        return {"Authorization": f"Bearer {t}"} if t else None

    headers = headers_for()

    def worker(item):
        key, url, dest = item
        if state and state.is_done(key):
            logger.info(f"    [resume] skipping {key} (already downloaded)")
            return ("ok", key, dest)
        last_err = None
        for attempt in range(1, RETRY_ATTEMPTS + 1):
            try:
                head = headers_for() if token_getter else headers
                bar = bar_factory
                stream_download(url, dest, headers=head, progress=bar, logger=logger)
                if state:
                    state.mark_done(key, dest)
                logger.info(f"    [ok] {key} -> {os.path.basename(dest)}")
                return ("ok", key, dest)
            except Exception as e:  # noqa: BLE001 - we want to retry everything
                last_err = e
                logger.warning(f"    [retry {attempt}/{RETRY_ATTEMPTS}] {key}: {e}")
                time.sleep(3 * attempt)
        return ("failed", key, dest, str(last_err))

    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = [ex.submit(worker, it) for it in items]
        for f in futures:
            try:
                r = f.result()
            except Exception as e:  # noqa: BLE001
                failed.append((items[0][1], "", str(e)))
                continue
            if r[0] == "ok":
                ok.append((r[1], r[2]))
            else:
                failed.append((r[1], r[2], r[3]))

    return ok, failed


# ==============================================================================
# 6. FOLDER STRUCTURE
# ==============================================================================

def create_folder_structure(base_path, sources):
    """Create all output directories. Returns the paths dict."""
    p = {
        "base": base_path,
        "metadata": os.path.join(base_path, "metadata"),
        "s2_delivery": os.path.join(base_path, "sentinel2"),
        "s1_delivery": os.path.join(base_path, "sentinel1"),
        "l8_delivery": os.path.join(base_path, "landsat8"),
        "dl_s2": os.path.join(base_path, "downloaded_scenes", "sentinel2"),
        "dl_s1": os.path.join(base_path, "downloaded_scenes", "sentinel1"),
        "dl_l8": os.path.join(base_path, "downloaded_scenes", "landsat8"),
    }
    dirs = [p["metadata"]]

    if "sentinel2" in sources:
        dirs += [p["s2_delivery"]]
        for y in S2_ANNUAL_YEARS:
            dirs.append(os.path.join(p["s2_delivery"], str(y)))
        dirs.append(os.path.join(p["s2_delivery"], "2023_2024"))
        dirs.append(p["dl_s2"])

    if "sentinel1" in sources:
        dirs += [p["s1_delivery"], os.path.join(p["s1_delivery"], "2023_2024"), p["dl_s1"]]

    if "landsat8" in sources:
        dirs += [p["l8_delivery"], os.path.join(p["l8_delivery"], "2023_2024"), p["dl_l8"]]

    for d in dirs:
        os.makedirs(d, exist_ok=True)
    return p


def disk_space_warning(base_path, need_gb, logger):
    """Warn if there is not enough free disk space."""
    try:
        usage = shutil.disk_usage(base_path)
        free_gb = usage.free / (1024 ** 3)
        logger.info(f"  Free disk space: {free_gb:.1f} GB | estimated need: {need_gb:.1f} GB")
        if need_gb * 0.95 > free_gb:
            logger.warning("  NOT ENOUGH DISK SPACE! Free some space before downloading.")
    except Exception as e:
        logger.warning(f"  Could not check disk space: {e}")

# ==============================================================================
# 7. SEARCH + DOWNLOAD: SENTINEL-2 (Copernicus)
# ==============================================================================

def detect_s2_delivery(record):
    """S2L2A cloud cover attribute (float) or None."""
    try:
        val = CdseClient.attribute(record, "cloudCover")
        if val is None:
            val = CdseClient.attribute(record, "cloudCoverage")
        return float(val) if val is not None else None
    except (TypeError, ValueError):
        return None


def product_dt(record):
    """Derived sensing start time -> naive-UTC datetime (fallback parse from name)."""
    t = CdseClient.process_time(record)
    if t:
        return t.replace(tzinfo=None)
    # fall back to parsing from the product name, e.g. S2A_MSIL2A_20180615T052441_...
    try:
        token = record["Name"].split("_")[2]
        return datetime.strptime(token, "%Y%m%dT%H%M%S")
    except Exception:
        return datetime(2000, 1, 1)


def model_s2_period(client, start_dt, end_dt, max_cloud=None):
    """
    Search Sentinel-2 L2A scenes for a period. Returns sorted list of
    (record, cloud_pct, sensed_dt). sorted ascending by sensing time.
    """
    raw = client.search("SENTINEL-2", start_dt, end_dt)
    out = []
    for rec in raw:
        name = rec.get("Name", "")
        if "MSIL2A" not in name and "MSIL2B" not in name:
            # also accept L2A naming without platform letter check
            if name.count("_") < 4 or "L2A" not in name:
                continue
        cloud = detect_s2_delivery(rec)
        if max_cloud is not None and (cloud is None or cloud > max_cloud):
            continue
        out.append((rec, cloud if cloud is not None else 100.0, product_dt(rec)))

    # products avoid dedup: CDSE can list both 'MSI_L2A' tile and original L2A
    seen = set()
    dedup = []
    for item in out:
        key = item[2].strftime("%Y%m%dT%H%M%S")
        if key in seen:
            continue
        seen.add(key)
        dedup.append(item)
    # newest first is nicer for picking "any" scenes
    dedup.sort(key=lambda x: x[2], reverse=True)
    return dedup


def choose_s2_scene(records, logger):
    """Pick a single 'best' scene (lowest cloud). records from model_s2_period."""
    if not records:
        return None
    best = min(records, key=lambda x: (x[1] if x[1] is not None else 100.0))
    return best


# ==============================================================================
# 8. SEARCH + DOWNLOAD: SENTINEL-1 (Copernicus)
# ==============================================================================

def model_s1_period(client, start_dt, end_dt):
    """
    Search Sentinel-1 GRD IW scenes (ascending, prefer dual VV+VH).
    Returns list of (record, mode) where mode in ('DV','VV').
    """
    raw = client.search("SENTINEL-1", start_dt, end_dt)
    out = []
    for rec in raw:
        name = rec.get("Name", "")
        if "GRDH" not in name:
            continue  # only Ground Range Detected High
        orbit = (CdseClient.attribute(rec, "orbitDirection") or "").upper()
        if orbit and orbit != "ASCENDING":
            continue
        pol = CdseClient.attribute(rec, "polarisationMode") or name
        if "1SDV" in name or "VV VH" in pol:
            mode = "DV"
        elif "1SSV" in name or pol == "VV":
            mode = "VV"
        else:
            continue  # 1SDH (HV only) or 1SSH (HH only) - not needed
        out.append((rec, mode, product_dt(rec)))
    out.sort(key=lambda x: x[2], reverse=True)
    return out


# ==============================================================================
# 9. SEARCH + DOWNLOAD: LANDSAT-8 (USGS direct M2M API)
# ==============================================================================
#
# landsatxplore 0.14.0 is broken on Python 3.12 (shapely dep) and its
# endpoints are stale.  We call the USGS Machine-to-Machine REST API
# directly with `requests` — same auth, same downloads, zero extra deps.
#
# M2M base: https://m2m.cr.usgs.gov/api/api/json/stable/
# Docs     : https://m2m.cr.usgs.gov/

USGS_M2M = "https://m2m.cr.usgs.gov/api/api/json/stable/"


class UsgsM2m:
    """Minimal USGS Machine-to-Machine API client."""

    def __init__(self, username, password):
        self.api_key = None
        self.s = requests.Session()
        self.s.headers.update({"Content-Type": "application/json"})
        self._login(username, password)

    def _call(self, endpoint, payload, timeout=240):
        last = None
        for attempt in range(3):
            try:
                r = self.s.post(USGS_M2M + endpoint, json=payload, timeout=timeout)
                r.raise_for_status()
                data = r.json()
                if isinstance(data, dict) and data.get("errorMessage"):
                    raise RuntimeError(f"M2M error: {data['errorMessage']}")
                return data
            except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectTimeout) as e:
                last = e
                time.sleep(5 * (attempt + 1))
        raise RuntimeError(f"M2M call {endpoint} timed out: {last}")

    def _login(self, username, password):
        # USGS deprecated /login (password) in Feb 2025; use /login-token.
        # The `password` param is actually the M2M Application Token.
        data = self._call("login-token", {"username": username, "token": password})
        self.api_key = data.get("data")
        if not self.api_key:
            raise RuntimeError("USGS M2M login returned no API key")
        self.s.headers["X-Auth-Token"] = self.api_key

    def logout(self):
        try:
            self._call("logout", {"apiKey": self.api_key})
        except Exception:
            pass

    # -- search ----------------------------------------------------------------
    def search_scenes(self, dataset, bbox, start, end, max_cloud=None):
        """
        Search a USGS dataset.  bbox = (west, south, east, north).
        Returns list of dicts with entity_id, display_id, date, cloud.
        """
        spatial = {
            "filterType": "mbr",
            "lowerLeft": {"latitude": bbox[1], "longitude": bbox[0]},
            "upperRight": {"latitude": bbox[3], "longitude": bbox[2]},
        }
        acquisition = {
            "start": start.strftime("%Y-%m-%d"),
            "end": end.strftime("%Y-%m-%d"),
        }
        scene_filter = {"spatialFilter": spatial, "acquisitionFilter": acquisition}
        if max_cloud is not None:
            scene_filter["cloudCoverFilter"] = {"min": 0, "max": max_cloud}
        payload = {
            "datasetName": dataset,
            "maxResults": 250,
            "sceneFilter": scene_filter,
        }
        data = self._call("scene-search", payload)
        hits = data.get("data", []) or []
        if isinstance(hits, dict):
            hits = hits.get("results", []) or []
        results = []
        for h in hits:
            results.append({
                "entity_id": str(h.get("entityId", "")),
                "display_id": h.get("displayId", ""),
                "date": h.get("acquisitionDate", ""),
                "cloud": h.get("cloudCover", 0),
            })
        return results

    # -- download-url ----------------------------------------------------------
    def get_download_urls(self, dataset, entity_ids):
        """
        Request download URLs for a batch of scenes (current M2M API).
        Returns dict {entity_id: url_string}.
        """
        urls = {}
        for eid in entity_ids:
            try:
                op_data = self._call("download-options", {
                    "datasetName": dataset, "entityIds": [eid]})
                options = op_data.get("data", []) or []
                if not options:
                    continue
                opt = next((o for o in options
                            if "Level-2 Product Bundle" in (o.get("productName") or "")),
                           options[0])
                pid = opt.get("id")
                req_data = self._call("download-request", {
                    "downloads": [{"entityId": eid, "productId": pid}],
                    "label": "yamuna_l8", "returnAvailable": True,
                })
                req = req_data.get("data", {}) or {}
                for item in (req.get("availableDownloads", []) or []):
                    if item.get("entityId") == eid and item.get("url"):
                        urls[eid] = item["url"]
                        break
                if eid not in urls and opt.get("url"):
                    urls[eid] = opt["url"]
            except Exception as e:
                print("get_download_urls err:", e)
        return urls

    def download_file(self, url, dest):
        """Stream-download a file from a USGS URL."""
        with self.s.get(url, stream=True, timeout=DOWNLOAD_TIMEOUT) as resp:
            resp.raise_for_status()
            total = int(resp.headers.get("Content-Length", 0))
            tmp = dest + ".part"
            mode = "ab" if os.path.exists(tmp) else "wb"
            existing = os.path.getsize(tmp) if mode == "ab" else 0
            with open(tmp, mode) as f:
                for chunk in resp.iter_content(chunk_size=HTTP_CHUNK):
                    if chunk:
                        f.write(chunk)
            if existing or os.path.getsize(tmp) >= total * 0.98:
                os.replace(tmp, dest)
                return True
        return False


def search_landsat8_period(usgs_creds, start_dt, end_dt, max_cloud, scenes_by_id, logger):
    """
    Search Landsat-8 (OLI/TIRS, Collection 2 Level 2) via USGS M2M API.
    """
    try:
        api = UsgsM2m(usgs_creds["usgs_user"], usgs_creds["usgs_pass"])
    except Exception as e:
        logger.error("  USGS login failed: %s", e)
        return []
    try:
        hits = api.search_scenes(
            dataset=USGS_DATASET,
            bbox=(STUDY_AREA[0], STUDY_AREA[1], STUDY_AREA[2], STUDY_AREA[3]),
            start=start_dt, end=end_dt, max_cloud=max_cloud,
        )
        return hits
    except Exception as e:
        logger.error("  USGS search failed: %s", e)
        return []
    finally:
        api.logout()


def download_landsat8_scene(usgs_creds, scene, out_dir, logger):
    """
    Download a single Landsat-8 C2 L2 product to out_dir.
    Returns destination path or None.
    """
    try:
        api = UsgsM2m(usgs_creds["usgs_user"], usgs_creds["usgs_pass"])
    except Exception as e:
        logger.error("  USGS login for download failed: %s", e)
        return None
    try:
        eid = scene["entity_id"]
        did = scene["display_id"]
        urls = api.get_download_urls(USGS_DATASET, [eid])
        url = urls.get(eid)
        if not url:
            logger.error("  No download URL for %s", did or eid)
            return None
        dest = os.path.join(out_dir, (did or eid) + ".tar")
        logger.info("  Downloading %s ...", did or eid)
        api.download_file(url, dest)
        if os.path.exists(dest):
            return dest
        # check if it's a .tar.gz that was saved with extension
        for f in os.listdir(out_dir):
            if (did or eid) in f and f.endswith((".tar", ".tar.gz", ".gz")):
                return os.path.join(out_dir, f)
        return None
    except Exception as e:
        logger.error("  USGS download failed: %s", e)
        return None
    finally:
        api.logout()


# ==============================================================================
# 10. PROCESSING: SENTINEL-2 -> 14-band cloud-masked GeoTIFF
# ==============================================================================

def _two_letter(band):
    """B2 -> '', B8A -> '8A' etc, for file matching."""
    return band.replace("B", "", 1)


def process_sentinel2_products(safe_dirs, out_tif, period_label, res=10.0, logger=None):
    """
    Build a single cloud-masked median GeoTIFF from a list of S2 L2A .SAFE dirs.
    Bands: 10 spectral (10/20 m, all resampled to `res` m) + 4 indices.
    CRS: EPSG:4326. Dtype: uint16 (reflectance scaled x100 / indices scaled).
    """
    import numpy as np
    import rasterio
    from rasterio.transform import from_bounds
    from rasterio.warp import reproject, Resampling, transform_bounds, calculate_default_transform
    from pathlib import Path

    logger = logger or logging.getLogger("yamuna_downloader")

    # Build the output grid over the AOI in EPSG:4326 at `res` metres.
    west, south, east, north = STUDY_AREA
    mid_lat = math.radians((south + north) / 2)
    deg_per_m_y = 1.0 / 111320.0
    deg_per_m_x = 1.0 / (111320.0 * math.cos(mid_lat))
    px = res * deg_per_m_x          # degrees per pixel in x
    py = res * deg_per_m_y          # degrees per pixel in y
    width = int(math.ceil((east - west) / px))
    height = int(math.ceil((north - south) / py))
    dst_transform = from_bounds(west, south, east, north, width, height)
    dst_crs = "EPSG:4326"

    def band_filepath(safe, band, res_txt):
        gran = os.path.join(safe, "GRANULE")
        if not os.path.isdir(gran):
            return None
        gdirs = os.listdir(gran)
        for g in gdirs:
            img_data = os.path.join(gran, g, "IMG_DATA", res_txt)
            if not os.path.isdir(img_data):
                continue
            match_res = res_txt.replace("R", "")   # S2 files use "10m"/"20m"
            band_alt = ("B0" + band[1:]) if (len(band) == 2 and band[:1] == "B"
                                             and band[1:].isdigit()) else band
            for f in os.listdir(img_data):
                cands = (f"_{band}_{res_txt}.jp2", f"_{band}_{res_txt}.tif",
                         f"_{band}_{match_res}.jp2", f"_{band}_{match_res}.tif",
                         f"_{band_alt}_{res_txt}.jp2", f"_{band_alt}_{res_txt}.tif",
                         f"_{band_alt}_{match_res}.jp2", f"_{band_alt}_{match_res}.tif")
                if any(f.endswith(c) for c in cands):
                    return os.path.join(img_data, f)
        return None

    def load_band(safe, band, res_txt, resampling):
        """Read one band of one SAFE to the 4326 grid. Returns float32 or None."""
        fp = band_filepath(safe, band, res_txt)
        if not fp or not os.path.exists(fp):
            return None
        with rasterio.open(fp) as src:
            src_transform = src.transform
            src_crs = src.crs
            # AOI bounds in the source CRS
            try:
                xmin, ymin, xmax, ymax = transform_bounds(
                    dst_crs, src_crs, west, south, east, north)
            except Exception:
                logger.warning(f"  reproject of AOI failed for {os.path.basename(safe)}")
                return None
            # window covering those bounds
            from rasterio.windows import from_bounds as w_from_bounds
            w = w_from_bounds(xmin, ymin, xmax, ymax, src_transform)
            w = w.round_lengths(op="floor", pixel_precision=3)
            arr = src.read(1, window=w)
            win_transform = src.window_transform(w)
            src_crs = src.crs.to_string() if hasattr(src.crs, "to_string") else "EPSG:32643"
            out = np.empty((height, width), dtype=np.float32)
            _ = reproject(
                source=arr,
                destination=out,
                src_transform=win_transform,
                src_crs=src.crs,
                dst_transform=dst_transform,
                dst_crs=dst_crs,
                src_nodata=0,
                dst_nodata=-9999.0,
                resampling=resampling,
            )
        out[out == -9999.0] = np.nan
        # scale: L2A reflectance stored as int16 with 1/10000 factor
        return out / 10000.0

    valid_count = 0
    bands_arrays = {}   # band -> list of 2D float arrays
    for safe in safe_dirs:
        # Quick microscope: integrity check for required bands
        ok = all(band_filepath(safe, b, "R10m" if b in S2_10M_BANDS else "R20m")
                 for b in S2_SPECTRAL_BANDS)
        if not ok:
            logger.warning(f"  Skipping incomplete product {Path(safe).name}")
            continue
        valid_count += 1

        # cloud mask from SCL (20 m), resampled to target grid (nearest)
        scl_fp = band_filepath(safe, "SCL", "R20m")
        scl = None
        if scl_fp and os.path.exists(scl_fp):
            with rasterio.open(scl_fp) as src:
                xmin, ymin, xmax, ymax = transform_bounds(dst_crs, src.crs, west, south, east, north)
                from rasterio.windows import from_bounds as w_from_bounds
                w = w_from_bounds(xmin, ymin, xmax, ymax, src.transform)
                scl_src = src.read(1, window=w)
                scl_out = np.empty((height, width), dtype=np.float32)
                _ = reproject(
                    source=scl_src, destination=scl_out,
                    src_transform=src.window_transform(w), src_crs=src.crs,
                    dst_transform=dst_transform, dst_crs=dst_crs,
                    src_nodata=0, dst_nodata=0, resampling=Resampling.nearest)
            valid = np.isin(scl_out, [2, 3, 4, 5, 6, 7])   # keep shadow/veg/bare/water/low-cl
        else:
            valid = None

        for band in S2_SPECTRAL_BANDS:
            resn = "R10m" if band in S2_10M_BANDS else "R20m"
            data = load_band(safe, band, resn, Resampling.bilinear)
            if data is None:
                continue
            if valid is not None:
                data = data.copy()
                data[~valid] = np.nan
            bands_arrays.setdefault(band, []).append(data)

    if valid_count == 0 or not bands_arrays:
        logger.warning(f"  No valid S2 products processed for {period_label}")
        return False

    # median composite per band
    logger.info(f"  Compositing {valid_count} products -> median ...")
    medians = {}
    for band, arrs in bands_arrays.items():
        stack = np.stack(arrs, axis=0)          # (n, H, W) float32
        med = np.nanmedian(stack, axis=0)       # float64
        med[~np.isfinite(med)] = 0
        medians[band] = med

    # indices from composites
    b8 = medians.get("B8"); b4 = medians.get("B4"); b3 = medians.get("B3")
    b11 = medians.get("B11")
    all_ok = all(m is not None for m in (b8, b4, b3, b11))
    indices = {}
    if all_ok:
        denom = np.where(np.abs(b8 + b4) < 1e-9, np.nan, b8 + b4)
        indices["NDVI"] = (b8 - b4) / denom
        denom2 = np.where(np.abs(b3 + b8) < 1e-9, np.nan, b3 + b8)
        indices["NDWI"] = (b3 - b8) / denom2
        denom3 = np.where(np.abs(b11 + b8) < 1e-9, np.nan, b11 + b8)
        indices["NDBI"] = (b11 - b8) / denom3
        denom4 = np.where(np.abs(b3 + b11) < 1e-9, np.nan, b3 + b11)
        indices["NDSI"] = (b3 - b11) / denom4

    # write GeoTIFF (uint16, LZW). reflectance: round(v*10000). index: round((v+1)*5000)
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

    profile = {
        "driver": "GTiff", "count": len(out_bands), "dtype": "uint16", "compress": "lzw",
        "height": height, "width": width, "crs": dst_crs, "transform": dst_transform,
        "nodata": 0,
    }
    os.makedirs(os.path.dirname(out_tif), exist_ok=True)
    with rasterio.open(out_tif, "w", **profile) as dst:
        for i, band_arr in enumerate(out_bands, start=1):
            dst.write(band_arr, i)
    logger.info(f"  Wrote {os.path.basename(out_tif)} ({len(out_bands)} bands)")
    return True


# ==============================================================================
# 11. PROCESSING: SENTINEL-1 -> VV / VH GeoTIFF
# ==============================================================================

def process_sentinel1_products(safe_dirs, out_prefix, period_label, res=10.0, logger=None):
    """
    Mosaic the IW1/2/3 sub-swath measurements of each GRD product into a
    single EPSG:4326 GeoTIFF clipped to the AOI. Outputs:
      <out_prefix>_VV.tif and <out_prefix>_VH.tif  (uint16 amplitude)
    For quantitativuse (sigma0 dB) run processing in SNAP / pyroSAR.
    """
    import numpy as np
    import rasterio
    from rasterio.transform import from_bounds
    from rasterio.warp import reproject, Resampling, transform_bounds
    from pathlib import Path

    logger = logger or logging.getLogger("yamuna_downloader")
    west, south, east, north = STUDY_AREA
    mid_lat = math.radians((south + north) / 2)
    px = res / (111320.0 * math.cos(mid_lat))
    py = res / 111320.0
    width = int(math.ceil((east - west) / px))
    height = int(math.ceil((north - south) / py))
    dst_transform = from_bounds(west, south, east, north, width, height)
    dst_crs = "EPSG:4326"

    def meas_tiffs(safe, pol):
        """Return list of measurement .tif paths for a polarization (vv/vh)."""
        mdir = os.path.join(safe, "measurement")
        if not os.path.isdir(mdir):
            return []
        out = []
        for f in sorted(os.listdir(mdir)):
            if f.lower().endswith((".tif", ".tiff")) and f"-{pol}-" in f.lower():
                out.append(os.path.join(mdir, f))
        return out

    def mosaic_pol(safe, pol):
        outs = []
        for fp in meas_tiffs(safe, pol):
            if not os.path.exists(fp):
                continue
            with rasterio.open(fp) as src:
                xmin, ymin, xmax, ymax = transform_bounds(dst_crs, src.crs, west, south, east, north)
                from rasterio.windows import from_bounds as w_from_bounds
                w = w_from_bounds(xmin, ymin, xmax, ymax, src.transform)
                arr = src.read(1, window=w).astype(np.float32)
                add = np.zeros((height, width), dtype=np.float32)
                _ = reproject(
                    source=arr,
                    destination=add,
                    src_transform=src.window_transform(w),
                    src_crs=src.crs,
                    dst_transform=dst_transform,
                    dst_crs=dst_crs,
                    src_nodata=0, dst_nodata=0,
                    resampling=Resampling.bilinear,
                )
                outs.append(add)
        if not outs:
            return None
        stack = np.stack(outs, axis=0)
        return np.max(stack, axis=0)   # max-fuse swath overlap

    # Median across products (same geometry), then scale to uint16.
    vv_stack = []
    vh_stack = []
    for safe in safe_dirs:
        _vv = mosaic_pol(safe, "vv")
        _vh = mosaic_pol(safe, "vh")
        if _vv is not None:
            vv_stack.append(_vv)
        if _vh is not None:
            vh_stack.append(_vh)

    for pol, stack, name in (("VV", vv_stack, "VV"), ("VH", vh_stack, "VH")):
        if not stack:
            logger.warning(f"  No S1 {name} imagery for {period_label}")
            continue
        med = np.nanmedian(np.stack(stack, 0), axis=0)
        med[~np.isfinite(med)] = 0
        # amplitude DN : stretch using the 99.9th percentile
        p99 = float(np.percentile(med[med > 0], 99.9)) if (med > 0).any() else 1.0
        scaled = np.clip((med / (p99 + 1e-6)) * 60000.0, 0, 65535).astype(np.uint16)
        profile = {
            "driver": "GTiff", "count": 1, "dtype": "uint16", "compress": "lzw",
            "height": height, "width": width, "crs": dst_crs,
            "transform": dst_transform, "nodata": 0,
        }
        out_tif = f"{out_prefix}_{name}.tif"
        os.makedirs(os.path.dirname(out_tif), exist_ok=True)
        with rasterio.open(out_tif, "w", **profile) as dst:
            dst.write(scaled, 1)
        logger.info(f"  Wrote {os.path.basename(out_tif)}")
    return True


# ==============================================================================
# 12. PROCESSING: LANDSAT-8 -> thermal (K) + red + NIR GeoTIFF
# ==============================================================================

def process_landsat8_product(product_dir, out_tif, period_label, logger=None):
    """
    From an extracted USGS C2 L2 product build a 3-band GeoTIFF:
      band1 Thermal surface temperature [Kelvin] (float32)
      band2 Red reflectance x10000 (uint16)
      band3 NIR reflectance x10000 (uint16)
    Reads directly inside the .tar archive via GDAL /vsitar when possible.
    """
    import numpy as np
    import rasterio
    from rasterio.transform import from_bounds
    from rasterio.warp import reproject, Resampling, transform_bounds
    from pathlib import Path

    logger = logger or logging.getLogger("yamuna_downloader")
    west, south, east, north = STUDY_AREA
    mid_lat = math.radians((south + north) / 2)
    res = 30.0
    px = res / (111320.0 * math.cos(mid_lat))
    py = res / 111320.0
    width = int(math.ceil((east - west) / px))
    height = int(math.ceil((north - south) / py))
    dst_transform = from_bounds(west, south, east, north, width, height)
    dst_crs = "EPSG:4326"

    def find_tiff(base, suffix):
        """Locate a *_suffix.TIF either in extracted dir or inside the tar."""
        if os.path.isdir(base):
            for root, _, files in os.walk(base):
                for f in files:
                    if f.endswith(f"_{suffix}.TIF") or f.endswith(f"_{suffix}.tif"):
                        return os.path.join(root, f)
        if os.path.isfile(base):
            if base.endswith((".tar", ".tar.gz", ".gz")):
                vs = f"/vsitar/{base}/{suffix}.TIF"
                try:
                    with rasterio.open(vs) as _:
                        return vs
                except Exception:
                    pass
            # fallback: extract the archive once, then walk the extracted dir
            import tarfile
            outdir = os.path.join(os.path.dirname(base),
                                  os.path.basename(base) + "_x")
            if not os.path.isdir(outdir):
                os.makedirs(outdir, exist_ok=True)
                with tarfile.open(base, "r:*") as tf:
                    for member in tf.getmembers():
                        if not (member.name.startswith("/") or ".." in member.name):
                            tf.extract(member, outdir)
            for root, _, files in os.walk(outdir):
                for f in files:
                    if f.endswith(f"_{suffix}.TIF") or f.endswith(f"_{suffix}.tif"):
                        return os.path.join(root, f)
        return None

    def read_single(name):
        fp = find_tiff(product_dir, name)
        if not fp or not os.path.exists(fp) and not fp.startswith("/vsitar"):
            return None
        try:
            with rasterio.open(fp) as src:
                xmin, ymin, xmax, ymax = transform_bounds(dst_crs, src.crs, west, south, east, north)
                from rasterio.windows import from_bounds as w_from_bounds
                w = w_from_bounds(xmin, ymin, xmax, ymax, src.transform)
                arr = src.read(1, window=w).astype(np.float32)
                add = np.zeros((height, width), dtype=np.float32)
                _ = reproject(
                    source=arr, destination=add,
                    src_transform=src.window_transform(w), src_crs=src.crs,
                    dst_transform=dst_transform, dst_crs=dst_crs,
                    src_nodata=0, dst_nodata=0, resampling=Resampling.bilinear)
                return add
        except Exception as e:
            logger.warning(f"  read {name} failed: {e}")
            return None

    thermal = read_single("ST_B10")
    red = read_single("SR_B4")
    nir = read_single("SR_B5")
    if thermal is None:
        logger.warning(f"  No thermal band for {period_label}")
        return False

    h, w = height, width
    ones = np.zeros((h, w), dtype=np.float32)
    kelvin = np.where(thermal != 0, thermal * 0.00341802 + 149.0, np.nan)
    red_arr = (np.where(red is not None, red, ones) * 0.0000275 - 0.2)
    nir_arr = (np.where(nir is not None, nir, ones) * 0.0000275 - 0.2)

    k16 = np.zeros((h, w), dtype=np.float32)
    k16[:] = kelvin
    r16 = np.clip(np.round(np.where(np.isfinite(red_arr), red_arr * 10000, 0)), 0, 65535).astype(np.uint16)
    n16 = np.clip(np.round(np.where(np.isfinite(nir_arr), nir_arr * 10000, 0)), 0, 65535).astype(np.uint16)

    out_tif = os.path.abspath(out_tif)
    os.makedirs(os.path.dirname(out_tif), exist_ok=True)
    with rasterio.open(
        out_tif, "w",
        driver="GTiff", count=3, compress="lzw",
        dtype="float32", height=h, width=w, crs=dst_crs, transform=dst_transform,
        nodata=np.nan,
    ) as dst:
        dst.write(k16, 1)
        dst.write(r16.astype(np.float32), 2)
        dst.write(n16.astype(np.float32), 3)
    logger.info(f"  Wrote {os.path.basename(out_tif)} (thermal=K, red, nir)")
    return True


# ==============================================================================
# 13. PRODUCT ORGANISATION + EXTRACTION HELPERS
# ==============================================================================

def content_length(record):
    """Product size in bytes from the OData record (may be None)."""
    try:
        return int(record.get("ContentLength") or 0)
    except (TypeError, ValueError):
        return 0


def extract_product_archive(archive_path, scratch_root, logger=None):
    """
    Extract a downloaded product (zip of a .SAFE for S2/S1) into scratch_root.
    Returns the final .SAFE folder path, or None if nothing usable.
    """
    import zipfile
    logger = logger or logging.getLogger("yamuna_downloader")
    os.makedirs(scratch_root, exist_ok=True)

    if os.path.isdir(archive_path):
        return archive_path   # already an extracted folder

    name = os.path.basename(archive_path)
    extract_to = os.path.join(scratch_root, name.replace(".zip", "").replace(".SAFE", ""))
    os.makedirs(extract_to, exist_ok=True)

    if archive_path.lower().endswith(".zip"):
        try:
            with zipfile.ZipFile(archive_path) as zf:
                zf.extractall(extract_to)
        except zipfile.BadZipFile as e:
            logger.error(f"  Bad zip for {name}: {e}")
            return None
    else:
        # single-file product (should not happen for S2/S1) - copy through
        shutil.copy(archive_path, extract_to)

    # find the .SAFE dir (may be nested one level deep)
    for root, dirs, _ in os.walk(extract_to):
        for d in dirs:
            if d.endswith(".SAFE") or d in ("GRANULE", "measurement"):
                return os.path.join(root, d)
    # some S2 archives unpack to a folder whose structure starts at GRANULE/
    for root, dirs, _ in os.walk(extract_to):
        if "GRANULE" in dirs and "measurement" in dirs:
            return root
    if os.path.isdir(extract_to):
        # fallback: the extracted root itself
        for root, dirs, _ in os.walk(extract_to):
            if "GRANULE" in dirs or "measurement" in dirs:
                return root
    return extract_to


# ==============================================================================
# 14. METADATA GENERATION
# ==============================================================================

def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)


def delivery_metadata_json(out_tif, scene_info, out_path, extra=None):
    """Write the JSON next to a delivered GeoTIFF."""
    meta = {
        "filename": os.path.basename(out_tif),
        "path": out_tif,
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    meta.update(scene_info)
    if extra:
        meta.update(extra)
    stem = os.path.basename(out_tif).replace(".tif", "").replace(".TIF", "")
    write_json(os.path.join(out_path, stem + "_metadata.json"), meta)


def write_inventory_csv(rows, output_path):
    """rows: list of dicts. CSV with fixed header + dynamic extras."""
    if not rows:
        return
    fieldnames = ["product", "sensor", "period", "scene_type", "sensing_date",
                  "cloud_cover_pct", "size_mb", "status", "error", "dest"]
    for r in rows:
        for k in r:
            if k not in fieldnames:
                fieldnames.append(k)
    path = os.path.join(output_path, "complete_inventory.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def write_quality_report(rows, output_path):
    """Summarise download/processing results per sensor & period."""
    path = os.path.join(output_path, "quality_report.txt")
    lines = ["=" * 70,
             "YAMUNA DATA COLLECTION - QUALITY REPORT",
             f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
             "=" * 70, ""]
    sensors = {}
    for r in rows:
        sensors.setdefault(r.get("sensor", "Unknown"), []).append(r)
    for sensor, items in sensors.items():
        ok = [i for i in items if i.get("status") == "ok"]
        fail = [i for i in items if i.get("status") != "ok"]
        lines.append(f"--- {sensor} ---")
        lines.append(f"  Scenes attempted : {len(items)}")
        lines.append(f"  Successful       : {len(ok)}")
        lines.append(f"  Failed           : {len(fail)}")
        clouds = [float(i["cloud_cover_pct"]) for i in ok
                  if str(i.get("cloud_cover_pct", "")).replace(".", "", 1).isdigit()]
        if clouds:
            lines.append(f"  Cloud cover range: {min(clouds):.1f}% - {max(clouds):.1f}% "
                         f"(avg {sum(clouds)/len(clouds):.1f}%)")
        lines.append("")
    total = len(rows)
    okn = sum(1 for r in rows if r.get("status") == "ok")
    lines += ["", "TOTAL: {:d} rows | {:d} ok | {:d} failed".format(total, okn, total - okn)]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def write_failed_csv(failed_rows, output_path):
    path = os.path.join(output_path, "failed_downloads.csv")
    fieldnames = ["product", "sensor", "period", "url_or_id", "error", "suggested_action"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in failed_rows:
            w.writerow(r)


# ==============================================================================
# 15. ORCHESTRATOR: SENTINEL-2 periods
# ==============================================================================

def _fi_mb(path):
    try:
        return round(os.path.getsize(path) / (1024 ** 2), 1)
    except OSError:
        return 0.0


def _s2_dest_dir(paths, label, scene_mode):
    if scene_mode == "best":
        return os.path.join(paths["s2_delivery"], label.split("_")[0])
    return os.path.join(paths["s2_delivery"], "2023_2024")


def run_s2_period(client, start_dt, end_dt, label, scene_mode, paths, state,
                  logger, dry_run, do_process, all_rows, all_failed):
    """Scene_mode: 'best' (single lowest-cloud, annual) or 'all' (every scene)."""
    records = model_s2_period(client, start_dt, end_dt, max_cloud=None)
    eligible = [r for r in records if (r[1] is not None and r[1] <= S2_CLOUD_MAX)]

    if scene_mode == "all" and USE_SCENE_CAPS and len(eligible) > S2_MAX_SCENES_PER_QUARTER:
        # "trim to fit": keep only the cleanest N scenes for the median composite
        eligible = sorted(eligible, key=lambda x: x[1])[:S2_MAX_SCENES_PER_QUARTER]
        logger.info("  %s: trimmed to %d cleanest scenes "
                    "(disk limit, full archive needs ~210 GB)",
                    label, len(eligible))

    logger.info("  %s: found %d L2A scenes, %d with cloud <= %d%%",
                label, len(records), len(eligible), S2_CLOUD_MAX)

    if scene_mode == "best":
        if not eligible:
            logger.warning("  %s: no eligible scene, skipping", label)
            return 0
        chosen = [min(eligible, key=lambda x: x[1])]
        logger.info("  %s: best scene %s (%.1f%% cloud)",
                    label, chosen[0][0]["Name"], chosen[0][1])
    else:
        chosen = eligible
        logger.info("  %s: downloading all %d eligible scenes", label, len(chosen))

    if dry_run:
        for rec, cloud, dt in chosen:
            all_rows.append({
                "product": rec["Name"], "sensor": "Sentinel-2 L2A", "period": label,
                "scene_type": "best" if scene_mode == "best" else "quarterly",
                "sensing_date": dt.strftime("%Y-%m-%d"), "cloud_cover_pct": cloud,
                "size_mb": round(content_length(rec) / 2 ** 20, 1),
                "status": "planned",
            })
        return len(chosen)

    dest_dir = paths["dl_s2"]
    items, meta_list = [], []
    for rec, cloud, dt in chosen:
        pid = rec["Id"]
        dest = os.path.join(dest_dir, rec["Name"] + ".zip")
        items.append((pid, client.download_url(pid), dest))
        meta_list.append({"record": rec, "cloud": cloud, "dt": dt})

    n_done = sum(1 for pid, _, _ in items if state.is_done(pid))
    logger.info("  %s: downloading %d products (%d already present)",
                label, len(items), n_done)

    ok, failed = parallel_download(items, max_workers=workers_pool["n"],
                                   state=state, logger=logger,
                                   token_getter=client.get_token)
    ok_ids = {pid for pid, _ in ok}
    for pid, dest in ok:
        rec = next(m["record"] for m in meta_list if m["record"]["Id"] == pid)
        all_rows.append({
            "product": rec["Name"], "sensor": "Sentinel-2 L2A", "period": label,
            "scene_type": "best" if scene_mode == "best" else "quarterly",
            "sensing_date": product_dt(rec).strftime("%Y-%m-%d"),
            "cloud_cover_pct": detect_s2_delivery(rec),
            "size_mb": round(content_length(rec) / 2 ** 20, 1),
            "status": "ok", "dest": dest,
        })
    for pid, dest, err in failed:
        rec = next((m["record"] for m in meta_list if m["record"]["Id"] == pid), None)
        name = rec["Name"] if rec else pid
        all_rows.append({
            "product": name, "sensor": "Sentinel-2 L2A", "period": label,
            "scene_type": "best" if scene_mode == "best" else "quarterly",
            "sensing_date": "", "cloud_cover_pct": "", "status": "failed",
            "error": err, "dest": dest,
        })
        all_failed.append({
            "product": name, "sensor": "Sentinel-2 L2A", "period": label,
            "url_or_id": pid, "error": err, "suggested_action": "re-run script (resume)",
        })

    # ---- processing ---------------------------------------------------------
    if do_process:
        safe_paths = [extract_product_archive(d, os.path.join(paths["dl_s2"], "_extract"), logger)
                      for _, d in ok]
        safe_paths = [p for p in safe_paths if p]
        out_dir = _s2_dest_dir(paths, label, scene_mode)
        out_tif = os.path.join(out_dir, f"S2_{label}_composite.tif")
        scene_type = "annual_best_scene" if scene_mode == "best" else "quarterly_median"
        if safe_paths:
            okp = process_sentinel2_products(safe_paths, out_tif, label, logger=logger)
            if okp:
                delivery_metadata_json(out_tif, {
                    "sensor": "Sentinel-2 L2A", "period": label, "scene_type": scene_type,
                    "source_scenes": len(safe_paths), "bands": S2_FULL_BANDS,
                    "crs": "EPSG:4326", "resolution_m": 10,
                    "cloud_cover_max_pct": S2_CLOUD_MAX,
                    "processing": "SCL-masked median composite; LZW uint16",
                }, out_dir, extra={"file_size_mb": _fi_mb(out_tif)})
                for d in safe_paths:
                    shutil.rmtree(d, ignore_errors=True)
    return len(ok)


# ==============================================================================
# 16. ORCHESTRATOR: SENTINEL-1 periods
# ==============================================================================

def run_s1_period(client, start_dt, end_dt, label, paths, state, logger,
                  dry_run, do_process, all_rows, all_failed):
    records = model_s1_period(client, start_dt, end_dt)

    if USE_SCENE_CAPS and len(records) > S1_MAX_SCENES_PER_QUARTER:
        # "trim to fit": pick scenes spread across the quarter so the median
        # composite stays representative while keeping the disk light.
        records = sorted(records, key=lambda x: x[2])
        step = len(records) / S1_MAX_SCENES_PER_QUARTER
        idxs = sorted({int(i * step) for i in range(S1_MAX_SCENES_PER_QUARTER)})
        records = [records[i] for i in idxs if i < len(records)]
        logger.info("  %s: trimmed to %d scenes spread across the quarter",
                    label, len(records))

    logger.info("  %s: found %d GRD IW ascending scenes", label, len(records))

    if dry_run:
        for rec, mode, dt in records:
            all_rows.append({
                "product": rec["Name"], "sensor": "Sentinel-1 GRD", "period": label,
                "scene_type": "quarterly", "sensing_date": dt.strftime("%Y-%m-%d"),
                "cloud_cover_pct": "N/A (SAR)",
                "size_mb": round(content_length(rec) / 2 ** 20, 1),
                "status": "planned",
            })
        return len(records)

    dest_dir = paths["dl_s1"]
    items = []
    for rec, mode, dt in records:
        pid = rec["Id"]
        items.append((pid, client.download_url(pid),
                      os.path.join(dest_dir, rec["Name"] + ".zip")))
    n_done = sum(1 for a, _, _ in items if state.is_done(a))
    logger.info("  %s: downloading %d products (%d already present)",
                label, len(items), n_done)

    ok, failed = parallel_download(items, max_workers=workers_pool["n"],
                                   state=state, logger=logger,
                                   token_getter=client.get_token)
    ok_ids = {pid for pid, _ in ok}
    for rec, mode, dt in records:
        status = "ok" if rec["Id"] in ok_ids else "queued"
        all_rows.append({
            "product": rec["Name"], "sensor": "Sentinel-1 GRD", "period": label,
            "scene_type": "quarterly", "sensing_date": dt.strftime("%Y-%m-%d"),
            "cloud_cover_pct": "N/A (SAR)",
            "size_mb": round(content_length(rec) / 2 ** 20, 1),
            "status": status,
        })
    for pid, dest, err in failed:
        all_failed.append({
            "product": pid, "sensor": "Sentinel-1 GRD", "period": label,
            "url_or_id": pid, "error": err, "suggested_action": "re-run script (resume)",
        })

    if do_process:
        safe_paths = [extract_product_archive(d, os.path.join(paths["dl_s1"], "_extract"), logger)
                      for pid, d in ok]
        safe_paths = [p for p in safe_paths if p]
        out_dir = os.path.join(paths["s1_delivery"], "2023_2024")
        out_pre = os.path.join(out_dir, f"S1_{label}")
        if safe_paths:
            okp = process_sentinel1_products(safe_paths, out_pre, label, logger=logger)
            if okp:
                for pol in ("VV", "VH"):
                    tif = f"{out_pre}_{pol}.tif"
                    if os.path.exists(tif):
                        delivery_metadata_json(tif, {
                            "sensor": "Sentinel-1 GRD IW", "period": label,
                            "scene_type": "quarterly_median",
                            "source_scenes": len(safe_paths),
                            "polarization": pol, "crs": "EPSG:4326",
                            "resolution_m": 10,
                            "processing": "swath mosaic max-fuse; median across products; uint16",
                        }, out_dir, extra={"file_size_mb": _fi_mb(tif)})
                for d in safe_paths:
                    shutil.rmtree(d, ignore_errors=True)
    return len(ok)


# ==============================================================================
# 17. ORCHESTRATOR: LANDSAT-8 periods
# ==============================================================================

def run_l8_period(usgs_creds, start_dt, end_dt, label, paths, state, logger,
                  dry_run, do_process, all_rows, all_failed):
    scenes = search_landsat8_period(usgs_creds, start_dt, end_dt, L8_CLOUD_MAX,
                                    {"dataset": USGS_DATASET}, logger)
    logger.info("  %s: found %d C2 L2 scenes (cloud <= %d%%)",
                label, len(scenes), L8_CLOUD_MAX)
    if not scenes:
        return 0
    best = min(scenes, key=lambda s: float(s.get("cloud") or 100))
    sid = best["display_id"] or best["entity_id"]
    logger.info("  %s: best scene %s (%s%% cloud)",
                label, sid, best.get("cloud"))

    if dry_run:
        for s in scenes:
            all_rows.append({
                "product": s["display_id"] or s["entity_id"], "sensor": "Landsat-8 C2 L2",
                "period": label,
                "scene_type": "quarterly_best" if s is best else "quarterly_candidate",
                "sensing_date": str(s.get("date", "")), "cloud_cover_pct": s.get("cloud"),
                "size_mb": 1000, "status": "planned",
            })
        return 1

    import glob
    dest_dir = paths["dl_l8"]
    existing = glob.glob(os.path.join(dest_dir, (sid.split("_")[0] or "LC") + "*_*.tar*"))
    if existing:
        logger.info("  %s: already have product, skipping download", label)
        dest_path = existing[0]
        state.mark_done(sid, dest_path)
    else:
        downloaded = download_landsat8_scene(usgs_creds, best, dest_dir, logger)
        if not downloaded:
            all_rows.append({"product": sid, "sensor": "Landsat-8 C2 L2", "period": label,
                             "sensing_date": str(best.get("date", "")),
                             "cloud_cover_pct": best.get("cloud"), "status": "failed",
                             "error": "download failed"})
            all_failed.append({"product": sid, "sensor": "Landsat-8 C2 L2", "period": label,
                               "url_or_id": sid, "error": "download failed",
                               "suggested_action": "re-run script (resume)"})
            return 0
        dest_path = downloaded
        state.mark_done(sid, dest_path)

    all_rows.append({"product": sid, "sensor": "Landsat-8 C2 L2", "period": label,
                     "scene_type": "quarterly_best",
                     "sensing_date": str(best.get("date", "")),
                     "cloud_cover_pct": best.get("cloud"),
                     "size_mb": round(os.path.getsize(dest_path) / 2 ** 20, 1),
                     "status": "ok", "dest": dest_path})

    if do_process:
        out_dir = os.path.join(paths["l8_delivery"], "2023_2024")
        out_tif = os.path.join(out_dir, f"L8_{label}_thermal.tif")
        okp = process_landsat8_product(dest_path, out_tif, label, logger=logger)
        if okp:
            delivery_metadata_json(out_tif, {
                "sensor": "Landsat-8 C2 L2 (OLI/TIRS)", "period": label,
                "scene_type": "quarterly_best", "display_id": sid,
                "bands": ["Thermal_K", "Red", "NIR"], "crs": "EPSG:4326",
                "resolution_m": 30, "thermal_scale": "K (Kelvin)",
                "processing": "3-band GeoTIFF, LZW",
            }, out_dir, extra={"file_size_mb": _fi_mb(out_tif)})
    return 1


# ==============================================================================
# 18. DRY RUN PLANNER (search everything, print the plan, no downloads)
# ==============================================================================

def generate_plan(client, usgs_creds, sources, logger):
    """Search all periods and return plan rows. No files are downloaded."""
    rows = []
    if "sentinel2" in sources:
        for y in S2_ANNUAL_YEARS:
            run_s2_period(client, datetime(y, 1, 1), datetime(y, 12, 31, 23, 59),
                          str(y), "best", None, None, logger, True, False, rows, [])
        for y, qs in S2_QUARTERLY.items():
            for q in qs:
                sm, sd, em, ed = QUARTERS[q]
                run_s2_period(client, datetime(y, sm, sd), datetime(y, em, ed, 23, 59),
                              f"{y}_{q}", "all", None, None, logger, True, False, rows, [])
    if "sentinel1" in sources:
        for y, qs in S1_L8_YEARS.items():
            for q in qs:
                sm, sd, em, ed = QUARTERS[q]
                run_s1_period(client, datetime(y, sm, sd), datetime(y, em, ed, 23, 59),
                              f"{y}_{q}", None, None, logger, True, False, rows, [])
    if "landsat8" in sources:
        for y, qs in S1_L8_YEARS.items():
            for q in qs:
                sm, sd, em, ed = QUARTERS[q]
                run_l8_period(usgs_creds, datetime(y, sm, sd), datetime(y, em, ed, 23, 59),
                              f"{y}_{q}", None, None, logger, True, False, rows, [])
    return rows


def print_plan(rows, sources):
    print("\n" + "=" * 70)
    print("COPERNICUS + USGS DIRECT DOWNLOAD - DRY RUN (trimmed to disk)")
    print("=" * 70)
    print(f"AOI: Yamuna River Palla-Jaitpur, Delhi  {STUDY_AREA}")
    print()
    tallies = {}
    for src, tag in (("Sentinel-2 L2A", "SENTINEL-2"), ("Sentinel-1 GRD", "SENTINEL-1"),
                     ("Landsat-8 C2 L2", "LANDSAT-8")):
        items = [r for r in rows if r["sensor"] == src]
        if not items:
            continue
        print(f"-- {tag} --")
        by_p = {}
        for r in items:
            by_p.setdefault(r["period"], []).append(r)
        for period in sorted(by_p):
            it = by_p[period]
            n = len(it)
            sz_mb = sum(r.get("size_mb") or 0 for r in it)
            cvals = [r["cloud_cover_pct"] for r in it
                     if isinstance(r.get("cloud_cover_pct"), (int, float))]
            ctxt = f"cloud {min(cvals):.0f}-{max(cvals):.0f}%" if cvals else "SAR (no cloud)"
            print(f"  {period:8s}: {n:3d} products | {sz_mb/1024:6.1f} GB | {ctxt}")
        ntot, sztot = len(items), sum(r.get("size_mb") or 0 for r in items) / 1024
        tallies[src] = (ntot, sztot)
        print(f"  TOTAL {tag}: {ntot} products | {sztot:.1f} GB")
        print()
    gb_all = sum(r.get("size_mb") or 0 for r in rows) / 1024
    print(f"GRAND TOTAL: {len(rows)} products | {gb_all:.1f} GB")
    print(f"Recommended free disk: {gb_all * 1.25 + 5:.0f} GB")
    return len(rows), gb_all


# ==============================================================================
# 19. MAIN ORCHESTRATOR
# ==============================================================================

def run_partial(base_path, paths, state, client, creds, sources, logger,
                do_process, all_rows, all_failed, start_year):
    """Execute downloads + processing for all selected sources."""
    t0 = time.time()

    if "sentinel2" in sources:
        print("\n" + "-" * 70)
        print("SENTINEL-2 L2A  (2018-2024)  [trimmed to fit disk]")
        print("-" * 70)
        for y in S2_ANNUAL_YEARS:
            if start_year and y < start_year:
                continue
            print(f"\n  Processing {y} ...")
            run_s2_period(client, datetime(y, 1, 1), datetime(y, 12, 31, 23, 59),
                          str(y), "best", paths, state, logger, False, do_process,
                          all_rows, all_failed)
        for y, qs in S2_QUARTERLY.items():
            if start_year and y < start_year:
                continue
            for q in qs:
                sm, sd, em, ed = QUARTERS[q]
                print(f"\n  Processing {y}-{q} ...")
                run_s2_period(client, datetime(y, sm, sd), datetime(y, em, ed, 23, 59),
                              f"{y}_{q}", "all", paths, state, logger, False, do_process,
                              all_rows, all_failed)

    if "sentinel1" in sources:
        print("\n" + "-" * 70)
        print("SENTINEL-1 GRD  (2023-2024 quarterly)")
        print("-" * 70)
        for y, qs in S1_L8_YEARS.items():
            if start_year and y < start_year:
                continue
            for q in qs:
                sm, sd, em, ed = QUARTERS[q]
                print(f"\n  Processing {y}-{q} ...")
                run_s1_period(client, datetime(y, sm, sd), datetime(y, em, ed, 23, 59),
                              f"{y}_{q}", paths, state, logger, False, do_process,
                              all_rows, all_failed)

    if "landsat8" in sources:
        print("\n" + "-" * 70)
        print("LANDSAT-8 C2 L2 THERMAL  (2023-2024 quarterly)")
        print("-" * 70)
        for y, qs in S1_L8_YEARS.items():
            if start_year and y < start_year:
                continue
            for q in qs:
                sm, sd, em, ed = QUARTERS[q]
                print(f"\n  Processing {y}-{q} ...")
                run_l8_period(creds, datetime(y, sm, sd), datetime(y, em, ed, 23, 59),
                              f"{y}_{q}", paths, state, logger, False, do_process,
                              all_rows, all_failed)

    # ---- metadata + summary --------------------------------------------------
    write_inventory_csv(all_rows, paths["metadata"])
    write_quality_report(all_rows, paths["metadata"])
    write_failed_csv(all_failed, paths["metadata"])

    elapsed = time.time() - t0
    ok_n = sum(1 for r in all_rows if r.get("status") == "ok")
    fail_n = sum(1 for r in all_rows if r.get("status") == "failed") + len(all_failed)
    gb = sum((r.get("size_mb") or 0) for r in all_rows) / 1024

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"  Products handled : {len(all_rows)}")
    print(f"  Downloaded OK    : {ok_n}")
    print(f"  Failed           : {fail_n}")
    print(f"  Total size       : {gb:.1f} GB")
    print(f"  Elapsed          : {int(elapsed//3600)}h {int((elapsed%3600)//60)}m")
    print(f"  Metadata written : metadata/complete_inventory.csv, quality_report.txt,")
    print(f"                     download_log.txt, failed_downloads.csv")
    print()
    print(f"  Resume any time  : python extract_yamuna_data.py --base-path"
          f" \"{base_path}\" --sources {' '.join(sources)}")
    if fail_n:
        print("\n  WARNING - failed items are listed in metadata/failed_downloads.csv")
        print("  Re-run the script to retry them (resume mode skips done files).")
    print()
    return 0


def run_main(args):
    global workers_pool
    workers_pool["n"] = max(1, min(args.workers, 6))

    print("=" * 70)
    print("Yamuna River Sand Mining - Data Collection (Copernicus + USGS direct)")
    print("=" * 70)

    base_path = args.base_path
    if not base_path:
        print("\nEnter the base output folder path (Enter = default):")
        cand = input("  Path: ").strip()
        default = os.path.join(os.path.dirname(os.path.abspath(__file__)), "yamuna_data")
        base_path = cand if cand else default
    base_path = os.path.abspath(base_path)
    os.makedirs(base_path, exist_ok=True)

    logger = setup_logging(base_path, args.verbose)
    logger.info("Starting Yamuna data collection (Copernicus + USGS)")

    sources = args.sources or ["sentinel2", "sentinel1", "landsat8"]
    if "sentinel2" not in sources:
        logger.warning("Note: Sentinel-2 is the primary data source - highly recommended.")

    creds = get_credentials(sources=sources)
    client = CdseClient(creds) if "sentinel2" in sources or "sentinel1" in sources else None

    if client and not test_cdse_login(creds, logger):
        sys.exit("Copernicus login failed - aborting.")
    if "landsat8" in sources and not test_usgs_login(creds, logger):
        sys.exit("USGS login failed - aborting.")

    paths = create_folder_structure(base_path, sources)
    print(f"\nFolder structure ready at: {base_path}")

    # Disk space warning
    try:
        usage = shutil.disk_usage(base_path)
        free_gb = usage.free / (1024 ** 3)
        print(f"  Free disk space: {free_gb:.0f} GB")
    except OSError:
        pass

    # -- dry-run / plan ---------------------------------------------------------
    if args.dry_run:
        print("\nSearching Copernicus + USGS (no downloads) ...")
        rows = generate_plan(client, creds, sources, logger)
        n_all, gb_all = print_plan(rows, sources)
        print("\nMetadata targets:")
        print("  - complete_inventory.csv, quality_report.txt, download_log.txt")
        print("  - failed_downloads.csv, JSON per delivered GeoTIFF")
        print()
        if not args.yes:
            ans = input("Proceed with actual download? (yes/no): ").strip().lower()
            if ans not in ("y", "yes"):
                print("Aborted - nothing was downloaded.")
                return 0

    # -- execution --------------------------------------------------------------
    state = DownloadState(os.path.join(paths["metadata"], "download_state.json"))
    all_rows, all_failed = [], []

    run_partial(base_path, paths, state, client, creds, sources, logger,
                not args.no_process, all_rows, all_failed, args.start_year)
    return 0


# ==============================================================================
# 20. CLI
# ==============================================================================

def parse_args():
    p = argparse.ArgumentParser(
        description="Download Sentinel-2 / Sentinel-1 (Copernicus) and "
                    "Landsat-8 (USGS) for the Yamuna River sand-mining study.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python extract_yamuna_data.py                         interactive
  python extract_yamuna_data.py --dry-run               plan only (no downloads)
  python extract_yamuna_data.py --sources sentinel2     only Sentinel-2
  python extract_yamuna_data.py --workers 2             slower / gentler network
  python extract_yamuna_data.py --no-process            download only, no GeoTIFFs
  python extract_yamuna_data.py --start-year 2020       resume from 2020 onward
        """)
    p.add_argument("--base-path", default=None, help="output root folder (Enter = default)")
    p.add_argument("--dry-run", action="store_true", help="search and plan, don't download")
    p.add_argument("--yes", action="store_true", help="skip confirmation prompts")
    p.add_argument("--sources", nargs="+",
                   choices=["sentinel2", "sentinel1", "landsat8"],
                   default=None, help="data sources (default: all three)")
    p.add_argument("--workers", type=int, default=4, help="parallel downloads (1-6, default 4)")
    p.add_argument("--start-year", type=int, default=None, help="skip years before this")
    p.add_argument("--no-process", action="store_true", help="download raw products only")
    p.add_argument("--verbose", action="store_true", help="debug logging")
    return p.parse_args()


if __name__ == "__main__":
    sys.exit(run_main(parse_args()))