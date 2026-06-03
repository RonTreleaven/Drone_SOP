#!/usr/bin/env python3
"""
Parse a DAH/OpenAir-style .air file into filtered GeoJSON.

Focus filters:
- Class D
- Class F
- Restricted CYR designators

Example:
  "C:/Program Files/Python312/python.exe" scripts/parse_dah_openair.py \
    --input data/airspace/canadian_airspace.air \
    --output data/airspace/dah_gold_airspace.geojson
"""

from __future__ import annotations

import argparse
import json
import math
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

EARTH_RADIUS_M = 6371008.8
COORD_RE = re.compile(r"(\d{1,3}):(\d{1,2}):(\d{1,2}(?:\.\d+)?)\s*([NSEW])", re.IGNORECASE)
CYR_RE = re.compile(r"\b(CYR\d{3}[A-Z]?)\b", re.IGNORECASE)
CYD_RE = re.compile(r"\b(CYD\d{3}[A-Z]?)\b", re.IGNORECASE)
CYA_RE = re.compile(r"\b(CYA\d{3}[A-Z]?)\b", re.IGNORECASE)


@dataclass
class Block:
    ac: str = ""
    an: str = ""
    al: str = ""
    ah: str = ""
    comments: list[str] = field(default_factory=list)
    geom_commands: list[tuple[str, Any]] = field(default_factory=list)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Parse DAH/OpenAir .air into filtered GeoJSON")
    parser.add_argument("--input", required=True, help="Path to .air file")
    parser.add_argument("--output", required=True, help="Path to output GeoJSON")
    parser.add_argument("--metadata-output", default="", help="Optional metadata JSON output path")
    parser.add_argument(
        "--include-classes",
        default="D,F",
        help="Comma-separated class filter (default: D,F)",
    )
    parser.add_argument(
        "--include-cyr",
        action="store_true",
        default=True,
        help="Include CYR restricted entries regardless of class (default: true)",
    )
    parser.add_argument(
        "--include-cyd-cya",
        action="store_true",
        default=True,
        help="Include CYD/CYA entries regardless of class (default: true)",
    )
    parser.add_argument(
        "--include-zone-types",
        default="CONTROL_ZONE,TRANSITION_AREA,TERMINAL_CONTROL_AREA,RESTRICTED,DANGER,ADVISORY,MOA,ADIZ",
        help="Comma-separated zone types to include regardless of class.",
    )
    parser.add_argument(
        "--diff-against",
        default="",
        help="Optional previous cycle GeoJSON path for diff.",
    )
    parser.add_argument(
        "--diff-output",
        default="",
        help="Optional output JSON for cycle diff results.",
    )
    parser.add_argument(
        "--discover-latest-dah-url",
        action="store_true",
        help="Discover latest Nav Canada DAH URL by testing AIRAC cadence URLs.",
    )
    parser.add_argument(
        "--dah-base-url",
        default="https://www.navcanada.ca/en",
        help="Base URL for DAH PDF discovery.",
    )
    parser.add_argument(
        "--dah-url-template",
        default="dah{date}.pdf",
        help="Template for DAH PDF filename where {date}=YYYYMMDD.",
    )
    parser.add_argument(
        "--airac-anchor",
        default="20260514",
        help="Known DAH publication date (YYYYMMDD) used as AIRAC cadence anchor.",
    )
    parser.add_argument(
        "--airac-step-days",
        type=int,
        default=56,
        help="Days between DAH cycles (default: 56).",
    )
    return parser.parse_args()


def parse_coord(token: str) -> tuple[float, float] | None:
    parts = COORD_RE.findall(token)
    if len(parts) < 2:
        return None

    def to_dd(p: tuple[str, str, str, str]) -> float:
        deg, minute, sec, hemi = p
        value = float(deg) + float(minute) / 60.0 + float(sec) / 3600.0
        if hemi.upper() in {"S", "W"}:
            value = -value
        return value

    lat = to_dd(parts[0])
    lon = to_dd(parts[1])
    return (lat, lon)


def normalize_name(an: str) -> tuple[str, str, str]:
    raw = (an or "").strip()
    ident = ""
    designation = "Other"
    name = raw

    cyr_match = CYR_RE.search(raw)
    cyd_match = CYD_RE.search(raw)
    cya_match = CYA_RE.search(raw)
    if cyr_match:
        ident = cyr_match.group(1).upper()
        designation = "Restricted"
        name = re.sub(CYR_RE, "", raw).strip(" ,-")
    elif cyd_match:
        ident = cyd_match.group(1).upper()
        designation = "Danger"
        name = re.sub(CYD_RE, "", raw).strip(" ,-")
    elif cya_match:
        ident = cya_match.group(1).upper()
        designation = "Advisory"
        name = re.sub(CYA_RE, "", raw).strip(" ,-")
    else:
        head = raw.split(" ", 1)
        if head and re.fullmatch(r"[A-Z]\d{2,4}", head[0] or ""):
            ident = head[0]
        if "CTR" in raw.upper() or "CONTROL" in raw.upper():
            designation = "Control"

    if not name:
        name = raw
    return ident, designation, name


def parse_active(comments: list[str]) -> str:
    for c in comments:
        m = re.search(r"Time of Designation\s*-\s*(.+)$", c, re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return "Unknown"


def parse_section(comments: list[str]) -> str:
    for c in comments:
        m = re.search(r"CDAH\s+section\s*:\s*(.+)$", c, re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return ""


def classify_zone_type(block: Block, designation: str) -> str:
    text = f"{block.an} {' '.join(block.comments)}".upper()
    if designation == "Restricted":
        return "RESTRICTED"
    if designation == "Danger":
        return "DANGER"
    if designation == "Advisory":
        return "ADVISORY"
    if "CONTROL ZONE" in text or "CTR" in text or " CZ" in text:
        return "CONTROL_ZONE"
    if "TERMINAL CONTROL AREA" in text or " TCA" in text:
        return "TERMINAL_CONTROL_AREA"
    if "TRANSITION AREA" in text or "[TA]" in text or " TA" in text:
        return "TRANSITION_AREA"
    if "MOA" in text:
        return "MOA"
    if "ADIZ" in text:
        return "ADIZ"
    return "OTHER"


def normalize_altitude(alt: str) -> dict[str, Any]:
    raw = (alt or "").strip().upper()
    result: dict[str, Any] = {
        "raw": raw,
        "unit": "",
        "reference": "",
        "value": None,
    }
    if not raw:
        return result
    if raw == "SFC":
        result["unit"] = "FT"
        result["reference"] = "SFC"
        result["value"] = 0
        return result

    fl_match = re.match(r"FL\s*(\d+)", raw)
    if fl_match:
        result["unit"] = "FL"
        result["reference"] = "STD"
        result["value"] = int(fl_match.group(1))
        return result

    num_match = re.match(r"(\d+(?:\.\d+)?)\s*(AGL|ASL|MSL|AMSL)?", raw)
    if num_match:
        result["unit"] = "FT"
        result["reference"] = num_match.group(2) or "UNKNOWN"
        n = float(num_match.group(1))
        result["value"] = int(n) if n.is_integer() else n
    return result


def bearing_deg(center: tuple[float, float], point: tuple[float, float]) -> float:
    lat1 = math.radians(center[0])
    lon1 = math.radians(center[1])
    lat2 = math.radians(point[0])
    lon2 = math.radians(point[1])
    dlon = lon2 - lon1
    y = math.sin(dlon) * math.cos(lat2)
    x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
    brng = math.degrees(math.atan2(y, x))
    return (brng + 360.0) % 360.0


def haversine_m(a: tuple[float, float], b: tuple[float, float]) -> float:
    lat1, lon1 = map(math.radians, a)
    lat2, lon2 = map(math.radians, b)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    s = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(min(1.0, math.sqrt(s)))


def destination_point(center: tuple[float, float], bearing_deg_value: float, distance_m: float) -> tuple[float, float]:
    lat1 = math.radians(center[0])
    lon1 = math.radians(center[1])
    brng = math.radians(bearing_deg_value)
    ang = distance_m / EARTH_RADIUS_M

    lat2 = math.asin(
        math.sin(lat1) * math.cos(ang) + math.cos(lat1) * math.sin(ang) * math.cos(brng)
    )
    lon2 = lon1 + math.atan2(
        math.sin(brng) * math.sin(ang) * math.cos(lat1),
        math.cos(ang) - math.sin(lat1) * math.sin(lat2),
    )

    return (math.degrees(lat2), ((math.degrees(lon2) + 540.0) % 360.0) - 180.0)


def build_arc(
    center: tuple[float, float],
    start: tuple[float, float],
    end: tuple[float, float],
    direction: str,
) -> list[tuple[float, float]]:
    start_b = bearing_deg(center, start)
    end_b = bearing_deg(center, end)
    radius_m = haversine_m(center, start)

    clockwise = direction == "+"
    if clockwise:
        if end_b <= start_b:
            end_b += 360.0
        angles = [start_b + i for i in range(0, int(end_b - start_b) + 1, 4)]
        if angles[-1] != end_b:
            angles.append(end_b)
    else:
        if end_b >= start_b:
            end_b -= 360.0
        angles = [start_b - i for i in range(0, int(start_b - end_b) + 1, 4)]
        if angles[-1] != end_b:
            angles.append(end_b)

    return [destination_point(center, a, radius_m) for a in angles]


def build_circle(center: tuple[float, float], radius_nm: float) -> list[tuple[float, float]]:
    radius_m = radius_nm * 1852.0
    pts = [destination_point(center, ang, radius_m) for ang in range(0, 360, 4)]
    if pts and pts[0] != pts[-1]:
        pts.append(pts[0])
    return pts


def parse_blocks(text: str) -> tuple[list[Block], dict[str, str]]:
    lines = text.splitlines()
    blocks: list[Block] = []
    header: dict[str, str] = {}
    current = Block()

    for raw in lines:
        line = raw.strip()
        if not line:
            continue

        if line.startswith("*"):
            clean = line.lstrip("* ").strip()
            if clean.lower().startswith("valid:"):
                header["valid"] = clean.split(":", 1)[1].strip()
            if clean.lower().startswith("issue:"):
                header["issue"] = clean.split(":", 1)[1].strip()
            current.comments.append(clean)
            continue

        if line.startswith("AC "):
            if current.ac:
                blocks.append(current)
                current = Block()
            current.ac = line[3:].strip().upper()
            continue

        if line.startswith("AN "):
            current.an = line[3:].strip()
            continue

        if line.startswith("AL "):
            current.al = line[3:].strip().upper()
            continue

        if line.startswith("AH "):
            current.ah = line[3:].strip().upper()
            continue

        if line.startswith("V D="):
            current.geom_commands.append(("DIR", line.split("=", 1)[1].strip()))
            continue

        if line.startswith("V X="):
            coord = parse_coord(line)
            if coord:
                current.geom_commands.append(("CENTER", coord))
            continue

        if line.startswith("DP "):
            coord = parse_coord(line)
            if coord:
                current.geom_commands.append(("POINT", coord))
            continue

        if line.startswith("DC "):
            try:
                radius_nm = float(line[3:].strip())
                current.geom_commands.append(("CIRCLE", radius_nm))
            except ValueError:
                pass
            continue

        if line.startswith("DB "):
            payload = line[3:].strip()
            parts = [p.strip() for p in payload.split(",")]
            if len(parts) >= 2:
                p1 = parse_coord(parts[0])
                p2 = parse_coord(parts[1])
                if p1 and p2:
                    current.geom_commands.append(("ARC", (p1, p2)))
            continue

    if current.ac:
        blocks.append(current)

    return blocks, header


def looks_like_geojson(text: str) -> bool:
    sample = text.lstrip()[:2000]
    if not sample:
        return False
    return (
        '"type"' in sample and (
            '"FeatureCollection"' in sample
            or '"Feature"' in sample
            or '"features"' in sample
            or '"geometry"' in sample
        )
    )


def commands_to_polygon(block: Block) -> list[list[float]] | None:
    points: list[tuple[float, float]] = []
    center: tuple[float, float] | None = None
    direction = "+"

    for kind, value in block.geom_commands:
        if kind == "DIR":
            direction = str(value).strip()[:1] if str(value).strip() else "+"
        elif kind == "CENTER":
            center = value
        elif kind == "POINT":
            points.append(value)
        elif kind == "CIRCLE":
            if center is not None:
                points.extend(build_circle(center, float(value)))
        elif kind == "ARC":
            if center is not None:
                start, end = value
                arc_pts = build_arc(center, start, end, direction)
                points.extend(arc_pts)

    # Keep only polygons; most of the target airspace in this feed is polygonal.
    if len(points) < 3:
        return None

    if points[0] != points[-1]:
        points.append(points[0])

    return [[lon, lat] for lat, lon in points]


def should_keep(
    block: Block,
    allowed_classes: set[str],
    include_cyr: bool,
    include_cyd_cya: bool,
    include_zone_types: set[str],
) -> bool:
    an_upper = block.an.upper()
    is_cyr = bool(CYR_RE.search(an_upper))
    is_cyd = bool(CYD_RE.search(an_upper))
    is_cya = bool(CYA_RE.search(an_upper))
    if include_cyr and is_cyr:
        return True
    if include_cyd_cya and (is_cyd or is_cya):
        return True
    ident, designation, _ = normalize_name(block.an)
    zone_type = classify_zone_type(block, designation)
    if zone_type in include_zone_types:
        return True
    return block.ac in allowed_classes


def block_to_feature(block: Block) -> dict[str, Any] | None:
    ring = commands_to_polygon(block)
    if not ring:
        return None

    ident, designation, base_name = normalize_name(block.an)
    zone_type = classify_zone_type(block, designation)
    section = parse_section(block.comments)
    lower_norm = normalize_altitude(block.al)
    upper_norm = normalize_altitude(block.ah)
    props = {
        "id": ident or block.an.split(" ", 1)[0].strip(),
        "class": block.ac,
        "designation": designation,
        "zone_type": zone_type,
        "name": base_name,
        "lower": block.al or "",
        "upper": block.ah or "",
        "lower_norm": lower_norm,
        "upper_norm": upper_norm,
        "active": parse_active(block.comments),
        "section": section,
        "source": "Transport Canada DAH",
    }

    return {
        "type": "Feature",
        "properties": props,
        "geometry": {
            "type": "Polygon",
            "coordinates": [ring],
        },
    }


def probe_url_exists(url: str) -> bool:
    try:
        req = Request(url, method="HEAD")
        with urlopen(req, timeout=12) as resp:
            return 200 <= getattr(resp, "status", 200) < 400
    except (HTTPError, URLError, TimeoutError, ValueError):
        return False


def discover_latest_dah_url(
    base_url: str,
    url_template: str,
    anchor_yyyymmdd: str,
    step_days: int,
) -> tuple[str, str] | tuple[None, None]:
    anchor = datetime.strptime(anchor_yyyymmdd, "%Y%m%d").replace(tzinfo=UTC)
    now = datetime.now(UTC)
    # Check cycles around current date with a small forward margin.
    candidates: list[datetime] = []

    dt = anchor
    while dt <= now + timedelta(days=step_days):
        candidates.append(dt)
        dt += timedelta(days=step_days)

    for cycle_dt in reversed(candidates):
        date_token = cycle_dt.strftime("%Y%m%d")
        filename = url_template.format(date=date_token)
        url = f"{base_url.rstrip('/')}/{filename.lstrip('/')}"
        if probe_url_exists(url):
            return url, date_token
    return None, None


def build_diff(current: list[dict[str, Any]], previous: list[dict[str, Any]]) -> dict[str, Any]:
    def key_of(f: dict[str, Any]) -> str:
        p = f.get("properties", {})
        return str(p.get("id") or p.get("name") or "")

    current_map = {key_of(f): f for f in current if key_of(f)}
    prev_map = {key_of(f): f for f in previous if key_of(f)}

    current_keys = set(current_map.keys())
    prev_keys = set(prev_map.keys())

    added = sorted(current_keys - prev_keys)
    removed = sorted(prev_keys - current_keys)

    changed: list[str] = []
    for k in sorted(current_keys & prev_keys):
        c_sig = json.dumps(current_map[k].get("properties", {}), sort_keys=True)
        p_sig = json.dumps(prev_map[k].get("properties", {}), sort_keys=True)
        if c_sig != p_sig:
            changed.append(k)

    return {
        "added": added,
        "removed": removed,
        "changed": changed,
        "counts": {
            "added": len(added),
            "removed": len(removed),
            "changed": len(changed),
        },
    }


def main() -> None:
    args = parse_args()
    allowed_classes = {c.strip().upper() for c in args.include_classes.split(",") if c.strip()}
    include_zone_types = {t.strip().upper() for t in args.include_zone_types.split(",") if t.strip()}

    input_path = Path(args.input)
    output_path = Path(args.output)
    text = input_path.read_text(encoding="utf-8", errors="replace")

    if looks_like_geojson(text):
        raise SystemExit(
            "Input appears to be GeoJSON. parse_dah_openair.py expects OpenAir .air text "
            "(AC/AN/AL/AH/DP/DB/V X lines), not GeoJSON. "
            "Use scripts/build_canadian_airspace_geojson.py for ca_asp.geojson inputs."
        )

    blocks, header = parse_blocks(text)

    features: list[dict[str, Any]] = []
    for block in blocks:
        if not should_keep(
            block,
            allowed_classes,
            args.include_cyr,
            args.include_cyd_cya,
            include_zone_types,
        ):
            continue
        feat = block_to_feature(block)
        if feat is not None:
            features.append(feat)

    dah_url = ""
    dah_publication_date = ""
    if args.discover_latest_dah_url:
        found_url, found_date = discover_latest_dah_url(
            args.dah_base_url,
            args.dah_url_template,
            args.airac_anchor,
            args.airac_step_days,
        )
        if found_url:
            dah_url = found_url
            dah_publication_date = found_date

    collection = {
        "type": "FeatureCollection",
        "name": "dah_gold_airspace",
        "metadata": {
            "source_file": str(input_path),
            "source_url": dah_url,
            "publication_date": dah_publication_date,
            "issue": header.get("issue", ""),
            "valid": header.get("valid", ""),
            "feature_count": len(features),
            "filters": {
                "classes": sorted(allowed_classes),
                "include_cyr": bool(args.include_cyr),
                "include_cyd_cya": bool(args.include_cyd_cya),
                "include_zone_types": sorted(include_zone_types),
            },
        },
        "features": features,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(collection, indent=2), encoding="utf-8")
    print(f"Wrote {len(features)} features to {output_path}")

    if args.metadata_output:
        metadata_path = Path(args.metadata_output)
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        metadata_path.write_text(json.dumps(collection["metadata"], indent=2), encoding="utf-8")
        print(f"Wrote metadata to {metadata_path}")

    if args.diff_against:
        prev_path = Path(args.diff_against)
        if prev_path.exists():
            prev_data = json.loads(prev_path.read_text(encoding="utf-8", errors="replace"))
            prev_features = prev_data.get("features", []) if isinstance(prev_data, dict) else []
            diff = build_diff(features, prev_features)
            print(
                "Diff counts -> "
                f"added: {diff['counts']['added']}, "
                f"removed: {diff['counts']['removed']}, "
                f"changed: {diff['counts']['changed']}"
            )
            if args.diff_output:
                diff_path = Path(args.diff_output)
                diff_path.parent.mkdir(parents=True, exist_ok=True)
                diff_path.write_text(json.dumps(diff, indent=2), encoding="utf-8")
                print(f"Wrote diff to {diff_path}")


if __name__ == "__main__":
    main()
