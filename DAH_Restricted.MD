# DAH Restricted Layer - Recreate Process

This file documents how to rebuild:

- data/airspace/RestrictedDAH.geoJson

from the Transport Canada Designated Airspace Handbook (DAH).

## Source Used (Current Build)

- Publication: Transport Canada Designated Airspace Handbook (DAH)
- Effective window shown in handbook pages used: 0901Z 22 JAN 2026 to 0901Z 19 MAR 2026
- Pages used for this build: 197 to 201
- Key reference requested in this update: section 6.2.0-2 (Darlington Nuclear Generating Station, ON)

## Scope of Data Included

The current RestrictedDAH layer contains point centers plus radius-based circles for DAH restricted entries provided from:

- 6.1.x (Vancouver FIR entries in the supplied extract)
- 6.2.x (Toronto FIR entries in the supplied extract)
- 6.3.x (Montreal FIR entries in the supplied extract)
- 6.4.x (Moncton FIR entries in the supplied extract)

## Coordinate and Unit Rules

1. Convert DAH DMS coordinates to decimal degrees.
2. Longitude west values are negative.
3. Radius is stored in nautical miles as radius_nm.
4. Map rendering uses radius_nm * 1852 (meters).
5. Designated altitude "Surface to X" is stored as:
   - lower_ft: 0
   - upper_ft: X

## File Format

RestrictedDAH.geoJson is a GeoJSON FeatureCollection of Point features.
Each feature includes at minimum:

- section
- name
- fir
- province
- radius_nm
- lower_ft
- upper_ft
- time_designation
- user_agency

## Rebuild Steps

1. Open the current DAH and copy the restricted entries you want to publish.
2. For each entry, capture:
   - section number
   - site name
   - FIR
   - province
   - center coordinate (DMS)
   - radius (NM)
   - altitude top (ft)
   - time of designation
   - user agency contact
3. Convert all DMS coordinates to decimal degrees.
4. Update or regenerate:
   - data/airspace/RestrictedDAH.geoJson
5. Save with UTF-8 encoding.
6. Validate JSON syntax.
7. Reload map page and verify circles and popups.

## Quick Validation Checklist

- FeatureCollection parses correctly
- Every feature geometry is Point
- Coordinates are [lon, lat]
- radius_nm present and numeric
- lower_ft and upper_ft present
- 6.2.0-2 exists and matches:
  - N43°52'12.00" W078°43'15.00"
  - radius 1 NM
  - Surface to 1300 ft
  - User Agency: OPG Senior Manager Of Investigations (905) 839-6746 Ext 4000

## Optional Helper Script Pattern

Use a temporary Python helper to convert DMS to decimal degrees and print rows, then paste output into RestrictedDAH.geoJson.

Example conversion logic:

- dd = degrees + minutes/60 + seconds/3600
- if hemisphere is S or W, dd = -dd

## Notes

- This DAH layer is separate from data/airspace/ca_asp_restricted.geojson.
- Maintain RestrictedDAH.geoJson as the handbook-derived restricted source for these fixed-designation circles.
