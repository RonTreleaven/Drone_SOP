# Canadian Airspace GeoJSON - Source and Build Notes

This folder documents how to populate `data/canadian_airspace.geojson` for `gcode.html` airspace checks.

## What `gcode.html` needs

`gcode.html` expects one file to exist and remain current:

- `data/canadian_airspace.geojson`

If this file is missing, invalid, or empty, the page will still work for geocoding but the Airspace panel will show a warning state instead of a lookup result.

## Current build source

Current practical source:

- OpenAIP Canada airspace export
- Example source filenames used in this repo:
  - `ca_asp.geojson`
  - `ca_asp.json`

Important:

- Validate license terms for your intended use.

- OpenAIP data is published under CC BY-NC 4.0 unless otherwise stated.

- Signed download URLs expire. Do not hardcode them permanently in code or docs.

  

## Builder script

Script:

- `scripts/build_canadian_airspace_geojson.py`

The builder accepts:

- local GeoJSON files
- local OpenAIP object-array JSON files
- ND-GeoJSON files
- remote `http/https` URLs

![OpenAIP Logo](openaip_logo.svg)

[OpenAIP - Data Exports](https://www.openaip.net/data/exports?page=1&limit=50&sortBy=createdAt&sortDesc=true&format=geojson&contentType=airspace&country=CA) (short cut) CA GeoJSON download.  ca_asp.geojson



## Standard build commands

Preferred local files workflow:

data/airspace/ca_asp.geojson  (input)

data/airspace/canadian_airspace.geojson (output)

```powershell
python scripts/build_canadian_airspace_geojson.py --input ca_asp.geojson --output data/canadian_airspace.geojson --classes B,C,D,E,F
```

```python scripts/build_canadian_airspace_geojson.py --input data/airspace/ca_asp.geojson --output data/airspace/canadian_airspace.geojson --classes B,C,D,E,F 
\Drone_SOP\python scripts/build_canadian_airspace_geojson.py --input data/airspace/ca_asp.geojson --output data/airspace/canadian_airspace.geojson --classes B,C,D,E,F
```







Alternative local JSON workflow:

```powershell
python scripts/build_canadian_airspace_geojson.py --input ca_asp.json --output data/canadian_airspace.geojson --classes B,C,D,E,F
```

Remote signed URL workflow:

```powershell
python scripts/build_canadian_airspace_geojson.py --input "<signed-openaip-url>" --output data/canadian_airspace.geojson --classes B,C,D,E,F
```

## What the builder keeps

The current filter is tuned for drone mission pre-screening:

- Country: Canada only
- Classes: `B,C,D,E,F`
- Lower limit: `<= 400 ft AGL`
- Airways: excluded by default

This is intended to answer a practical question for mission planning:

- Is this point inside low-altitude controlled or restricted airspace that matters to a typical sub-400 ft operation?

## Output contract

`gcode.html` supports GeoJSON `FeatureCollection` with `Polygon` and `MultiPolygon` geometries.

Expected properties per feature:

- `name`: airspace name
- `class`: class letter when available
- `lower_agl_ft`: filtered lower floor value used by the builder

Example feature:

```json
{
  "type": "Feature",
  "properties": {
    "name": "Toronto Terminal Control Area",
    "class": "C",
    "lower_agl_ft": 0,
    "source": "source import"
  },
  "geometry": {
    "type": "Polygon",
    "coordinates": [[[-79.9, 43.3], [-79.2, 43.3], [-79.2, 44.0], [-79.9, 44.0], [-79.9, 43.3]]]
  }
}
```

## Refresh cadence

Minimum acceptable maintenance for this page:

- Refresh airspace data every 6 months

Recommended maintenance for better operational confidence:

- Refresh monthly, or whenever you intentionally refresh other aviation data sources
- Rebuild immediately if source schema changes or if airspace results look wrong in a spot check

Operationally conservative rule:

- Treat 6 months as the outer limit, not the ideal target
- Always verify final status in NAV CANADA DSST before flight

## Validation after rebuild

After rebuilding `data/canadian_airspace.geojson`:

1. Open `gcode.html`
2. Test a known controlled location and a known uncontrolled location
3. Confirm the Airspace panel shows a reasonable class/name
4. Cross-check those same points in NAV CANADA DSST

## Operational note

Use this lookup as pre-screening only. Confirm final status in NAV CANADA DSST before flight.
