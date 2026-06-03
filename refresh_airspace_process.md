# Airspace Refresh Process

June 3, 2026 - created end to end refresh process.

This runbook defines the end-to-end process to refresh airspace data used by both map tools.

## Scope

- GGcode uses [data/canadian_airspace.geojson](data/canadian_airspace.geojson)
- DAHminimap uses [data/airspace/dah_gold_airspace.geojson](data/airspace/dah_gold_airspace.geojson)
- Canonical source folder is [data/airspace/_sources](data/airspace/_sources)

## Canonical source files

Store source files in one folder with one fixed name each:

1. [data/airspace/_sources/canadian_airspace.air](data/airspace/_sources/canadian_airspace.air)
2. [data/airspace/_sources/ca_asp.geojson](data/airspace/_sources/ca_asp.geojson)
3. [data/airspace/_sources/ca_apt.geojson](data/airspace/_sources/ca_apt.geojson)
4. [data/airspace/_sources/airports.csv](data/airspace/_sources/airports.csv)

Do not keep rotating names like Mayxx or delete-me variants in the refresh path.

## Source systems

1. OpenAir source for canadian_airspace.air
- URL: https://airspace.canadarasp.com/OpenAirFiles/canadian_airspace.air
- Note: DAH PDF is treated as the gold source for ADIZ/MOA polygon extraction.

2. GeoJSON source for ca_asp.geojson and ca_apt.geojson
- Use your designated provider URLs for these two files.
- Keep the canonical local names fixed in [data/airspace/_sources](data/airspace/_sources):
	- [data/airspace/_sources/ca_asp.geojson](data/airspace/_sources/ca_asp.geojson)
	- [data/airspace/_sources/ca_apt.geojson](data/airspace/_sources/ca_apt.geojson)
- If provider URLs are signed/expiring, refresh URL values before each pull.

## Scripts used

1. [scripts/refresh_airspace_data.py](scripts/refresh_airspace_data.py)
- Orchestrates both pipelines from canonical source paths.

2. [scripts/parse_dah_openair.py](scripts/parse_dah_openair.py)
- Input: OpenAir .air
- Output: DAH Gold GeoJSON

3. [scripts/extract_dah_special_zones.py](scripts/extract_dah_special_zones.py)
- Input: latest DAH PDF
- Output: [data/airspace/_derived/dah_special_zones.geojson](data/airspace/_derived/dah_special_zones.geojson)
- Extracts ADIZ and MOA polygons, merged into DAH Gold output during refresh

4. [scripts/build_canadian_airspace_geojson.py](scripts/build_canadian_airspace_geojson.py)
- Input: provider ca_asp.geojson
- Output: canadian_airspace.geojson

## End-to-end refresh steps

### Step 1: Pull or place source files

Option A: Let refresh script download sources for this run.

Run:

C:/Program Files/Python312/python.exe scripts/refresh_airspace_data.py --download-openair --download-ca-sources --ca-asp-url "PUT_CURRENT_CA_ASP_URL_HERE" --ca-apt-url "PUT_CURRENT_CA_APT_URL_HERE" --discover-latest-dah-url

To also refresh airports.csv in canonical sources during the same run:

C:/Program Files/Python312/python.exe scripts/refresh_airspace_data.py --download-openair --download-airports-csv --download-ca-sources --ca-asp-url "PUT_CURRENT_CA_ASP_URL_HERE" --ca-apt-url "PUT_CURRENT_CA_APT_URL_HERE" --discover-latest-dah-url

To include DAH PDF gold-source extraction (ADIZ/MOA) in the same run:

C:/Program Files/Python312/python.exe scripts/refresh_airspace_data.py --download-openair --download-airports-csv --download-ca-sources --ca-asp-url "PUT_CURRENT_CA_ASP_URL_HERE" --ca-apt-url "PUT_CURRENT_CA_APT_URL_HERE" --discover-latest-dah-url --download-dah-pdf --extract-dah-special-zones

Option B: Manually place source files in canonical folder, then run local-only build.

Place files at:

- [data/airspace/_sources/canadian_airspace.air](data/airspace/_sources/canadian_airspace.air)
- [data/airspace/_sources/ca_asp.geojson](data/airspace/_sources/ca_asp.geojson)
- [data/airspace/_sources/ca_apt.geojson](data/airspace/_sources/ca_apt.geojson)

Then run:

C:/Program Files/Python312/python.exe scripts/refresh_airspace_data.py --discover-latest-dah-url

### Step 2: Confirm outputs were rebuilt

Expected output files:

1. [data/airspace/dah_gold_airspace.geojson](data/airspace/dah_gold_airspace.geojson)
2. [data/airspace/_derived/dah_gold_airspace.metadata.json](data/airspace/_derived/dah_gold_airspace.metadata.json)
3. [data/canadian_airspace.geojson](data/canadian_airspace.geojson)
4. [data/airspace/_derived/dah_special_zones.geojson](data/airspace/_derived/dah_special_zones.geojson) when DAH special extraction is enabled

Optional mirror output if needed by other tools:

C:/Program Files/Python312/python.exe scripts/refresh_airspace_data.py --sync-canadian-to-airspace-folder

This also writes:

- [data/airspace/canadian_airspace.geojson](data/airspace/canadian_airspace.geojson)

### Step 3: Validate quickly

1. Open [GGcode.html](GGcode.html) and verify Airspace checks return expected results.
2. Open [DAHminimap.html](DAHminimap.html) and verify DAH polygons and airport overlays load.
3. Review metadata in [data/airspace/_derived/dah_gold_airspace.metadata.json](data/airspace/_derived/dah_gold_airspace.metadata.json) for source and cycle details.

## Monthly automation

Use Windows Task Scheduler with [scripts/monthly_refresh_airspace.ps1](scripts/monthly_refresh_airspace.ps1).

### What the monthly script does

1. Ensures [data/airspace/_sources](data/airspace/_sources) exists.
2. Downloads latest OpenAir file each run.
3. Downloads latest [data/airspace/_sources/airports.csv](data/airspace/_sources/airports.csv) each run.
4. Downloads latest DAH PDF from discovered cycle URL and extracts ADIZ/MOA polygons.
5. Runs [scripts/refresh_airspace_data.py](scripts/refresh_airspace_data.py) to rebuild outputs from canonical sources.
6. Writes logs to [data/airspace/reports](data/airspace/reports).

### Important automation note

Provider URLs may expire. That means full unattended GeoJSON download can fail unless you supply stable URL sources.

Recommended monthly model:

1. Keep OpenAir fully automated via script.
2. Refresh GeoJSON source URLs/files monthly into canonical names.
3. Let scheduled task run the build and validation logging automatically.

If you obtain stable GeoJSON source URLs, set them for [scripts/monthly_refresh_airspace.ps1](scripts/monthly_refresh_airspace.ps1) using OPENAIP_CA_ASP_URL and OPENAIP_CA_APT_URL (variable names can remain as-is, values can point to your provider).

## Task Scheduler setup example

Program:

powershell.exe

Arguments:

-NoProfile -ExecutionPolicy Bypass -File "C:/Users/Ron Treleaven/Drone_SOP/scripts/monthly_refresh_airspace.ps1"

Start in:

C:/Users/Ron Treleaven/Drone_SOP

Schedule:

Monthly, first day, 06:00 local time.

## Operational guardrails

1. Do not feed GeoJSON into [scripts/parse_dah_openair.py](scripts/parse_dah_openair.py).
2. Keep canonical source file names fixed in [data/airspace/_sources](data/airspace/_sources).
3. Keep source refresh and build logs for traceability.
