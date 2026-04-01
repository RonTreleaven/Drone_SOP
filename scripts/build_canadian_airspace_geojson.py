#!/usr/bin/env python3
"""
Build data/canadian_airspace.geojson from a source GeoJSON export.

Usage:
  python scripts/build_canadian_airspace_geojson.py \
    --input path/to/source.geojson \
    --output data/canadian_airspace.geojson

Optional:
  --classes C,D,E,F
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import urlparse
from urllib.request import Request, urlopen


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build Canadian airspace GeoJSON")
    parser.add_argument("--input", required=True, help="Path to source GeoJSON FeatureCollection")
    parser.add_argument("--output", required=True, help="Path to output GeoJSON")
    parser.add_argument(
        "--classes",
        default="",
        help="Optional comma-separated class allowlist, e.g. C,D,E,F",
    )
    parser.add_argument(
        "--max-lower-agl-ft",
        type=float,
        default=400.0,
        help="Keep only features with lower limit <= this AGL value in feet (default: 400). Use a negative value to disable.",
    )
    parser.add_argument(
        "--include-airways",
        action="store_true",
        help="Include airway records (excluded by default for low-altitude mission planning).",
    )
    return parser.parse_args()


def get_prop(props: Dict[str, Any], keys: Iterable[str]) -> Optional[Any]:
    for key in keys:
        if key in props and props[key] not in (None, ""):
            return props[key]
    return None


def is_canadian(props: Dict[str, Any]) -> bool:
    country = get_prop(props, ["country", "iso_country", "country_code", "countryCode"])
    if isinstance(country, str) and country.strip().upper() in {"CA", "CAN", "CANADA"}:
        return True

    # Fallback heuristic: many records include ICAO-style identifiers.
    ident = get_prop(props, ["id", "identifier", "icao", "name"])
    if isinstance(ident, str) and "C" in ident.upper():
        # Keep heuristic conservative by not auto-including everything.
        return False

    return False


def extract_class(props: Dict[str, Any]) -> str:
    raw = get_prop(props, ["class", "airspace_class", "airspaceClass", "classification", "icaoClass", "type"])
    if raw is None:
        return ""

    # openAIP may encode ICAO class as numeric enum.
    if isinstance(raw, (int, float)):
        numeric = int(raw)
        numeric_map = {0: "A", 1: "B", 2: "C", 3: "D", 4: "E", 5: "F", 6: "G"}
        return numeric_map.get(numeric, "")

    text = str(raw).strip().upper()
    if len(text) == 1 and text in {"A", "B", "C", "D", "E", "F", "G"}:
        return text
    for c in ["A", "B", "C", "D", "E", "F", "G"]:
        if f"CLASS {c}" in text or text == c:
            return c
    return text


def valid_geometry(geom: Dict[str, Any]) -> bool:
    if not isinstance(geom, dict):
        return False
    gtype = geom.get("type")
    return gtype in {"Polygon", "MultiPolygon"} and isinstance(geom.get("coordinates"), list)


def load_features(input_spec: str) -> List[Dict[str, Any]]:
    text = read_input_text(input_spec).strip()
    if not text:
        return []

    # First try standard GeoJSON FeatureCollection / Feature.
    try:
        obj = json.loads(text)
        if isinstance(obj, dict) and obj.get("type") == "FeatureCollection" and isinstance(obj.get("features"), list):
            return obj["features"]
        if isinstance(obj, dict) and obj.get("type") == "Feature":
            return [obj]

        # openAIP object-array format: [{..., geometry:{...}, ...}, ...]
        if isinstance(obj, list):
            converted: List[Dict[str, Any]] = []
            for item in obj:
                if not isinstance(item, dict):
                    continue
                geom = item.get("geometry")
                if not isinstance(geom, dict):
                    continue
                props = {k: v for k, v in item.items() if k != "geometry"}
                converted.append({"type": "Feature", "properties": props, "geometry": geom})
            return converted
    except json.JSONDecodeError:
        pass

    # Fallback: ND-GeoJSON (one Feature JSON per line).
    features: List[Dict[str, Any]] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict) and obj.get("type") == "Feature":
            features.append(obj)
    return features


def read_input_text(input_spec: str) -> str:
    if is_url(input_spec):
        req = Request(input_spec, headers={"User-Agent": "Drone-SOP-Airspace-Builder"})
        with urlopen(req, timeout=120) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            return response.read().decode(charset, errors="replace")

    return Path(input_spec).read_text(encoding="utf-8")


def is_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def main() -> None:
    args = parse_args()
    input_spec = args.input
    output_path = Path(args.output)

    class_allowlist = {c.strip().upper() for c in args.classes.split(",") if c.strip()}
    floor_filter_enabled = args.max_lower_agl_ft is not None and args.max_lower_agl_ft >= 0

    source_features = load_features(input_spec)
    if not source_features:
        raise SystemExit("No features found. Input must be GeoJSON FeatureCollection, Feature, or ND-GeoJSON.")

    output_features: List[Dict[str, Any]] = []

    dropped_non_polygon = 0
    dropped_non_canadian = 0
    dropped_by_class = 0
    dropped_airway = 0
    dropped_by_floor = 0

    for feature in source_features:
        if not isinstance(feature, dict):
            continue

        props = feature.get("properties") or {}
        geom = feature.get("geometry") or {}

        if not valid_geometry(geom):
            dropped_non_polygon += 1
            continue
        if not is_canadian(props):
            dropped_non_canadian += 1
            continue

        airspace_class = extract_class(props)
        if class_allowlist and airspace_class not in class_allowlist:
            dropped_by_class += 1
            continue

        name = get_prop(props, ["name", "title", "label", "id", "identifier"]) or "Unnamed Airspace"

        if not args.include_airways and "AIRWAY" in str(name).upper():
            dropped_airway += 1
            continue

        lower_agl_ft = extract_lower_agl_ft(props)
        if floor_filter_enabled and (lower_agl_ft is None or lower_agl_ft > args.max_lower_agl_ft):
            dropped_by_floor += 1
            continue

        output_features.append(
            {
                "type": "Feature",
                "properties": {
                    "name": str(name),
                    "class": airspace_class,
                    "lower_agl_ft": lower_agl_ft,
                    "source": "source import",
                },
                "geometry": geom,
            }
        )

    result = {
        "type": "FeatureCollection",
        "name": "canadian_airspace",
        "metadata": {
            "source": str(input_spec),
            "input_feature_count": len(source_features),
            "feature_count": len(output_features),
            "dropped_non_polygon": dropped_non_polygon,
            "dropped_non_canadian": dropped_non_canadian,
            "dropped_by_class": dropped_by_class,
            "dropped_airway": dropped_airway,
            "dropped_by_floor": dropped_by_floor,
            "class_filter": sorted(class_allowlist),
            "max_lower_agl_ft": args.max_lower_agl_ft,
        },
        "features": output_features,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"Wrote {len(output_features)} features to {output_path}")
    if len(output_features) == 0 and dropped_non_polygon > 0:
        print("Hint: input appears to be point/line data (e.g., obstacles), not airspace polygons.")


def extract_lower_agl_ft(props: Dict[str, Any]) -> Optional[float]:
    lower = props.get("lowerLimit")
    if not isinstance(lower, dict):
        return None

    value = lower.get("value")
    unit = lower.get("unit")
    datum = lower.get("referenceDatum")

    if value is None:
        return None

    # Heuristic: openAIP commonly encodes 0=AGL, 1=MSL for referenceDatum.
    # We only keep AGL floors for drone low-altitude filtering.
    if datum not in (0, "0", "AGL", "GND", "SFC"):
        return None

    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None

    # Heuristic unit handling: 1=ft, 0=m. Fallback to feet for unknown unit.
    if unit in (0, "0", "M", "m"):
        return numeric * 3.28084
    return numeric


if __name__ == "__main__":
    main()
