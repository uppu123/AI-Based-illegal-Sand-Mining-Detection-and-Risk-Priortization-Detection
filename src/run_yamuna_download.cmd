@echo off
set CDSE_USER=email4upendra@gmail.com
set CDSE_PASS=@Kvaratskhelia7
cd /d "C:\New folder"
python extract_yamuna_data.py --yes --sources sentinel2 sentinel1 --base-path "C:\New folder\yamuna_data"