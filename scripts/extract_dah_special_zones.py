#!/usr/bin/env python3
"""
Extract ADIZ/MOA polygons from DAH PDF text and write GeoJSON.

Current extraction targets in DAH:
- ADIZ (North/East + West)
- Algonquin MOA
- Elk MOA
- Shearwater MOA sectors 1-4

This extractor uses coordinate chains present in DAH text. Arc statements are
approximated using listed boundary vertices (center-point-only lines are ignored).
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Iterable

from pypdf import PdfReader

COORD_PAIR_RE = re.compile(
    r"([NS])(\d{2,3})°(\d{2})'(\d{2}(?:\.\d+)?)\"?\s+([EW])(\d{2,3})°(\d{2})'(\d{2}(?:\.\d+)?)\"?",
    re.IGNORECASE,
)
CENTERED_ON_RE = re.compile(r"CENT(?:ER|RE)D\s+ON", re.IGNORECASE)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Extract ADIZ/MOA polygons from DAH PDF")
    p.add_argument("--pdf", required=True, help="Path to DAH PDF")
    p.add_argument("--output", required=True, help="Path to output GeoJSON")
    return p.parse_args()


def page_lines(reader: PdfReader, page_no: int) -> list[str]:
    text = reader.pages[page_no - 1].extract_text() or ""
    return [ln.strip() for ln in text.splitlines() if ln.strip()]


def dms_to_dd(hemi: str, deg: str, minute: str, sec: str) -> float:
    v = float(deg) + float(minute) / 60.0 + float(sec) / 3600.0
    if hemi.upper() in {"S", "W"}:
        v = -v
    return v


def parse_coords(text: str) -> list[tuple[float, float]]:
    out: list[tuple[float, float]] = []
    for m in COORD_PAIR_RE.finditer(text):
        lat = dms_to_dd(m.group(1), m.group(2), m.group(3), m.group(4))
        lon = dms_to_dd(m.group(5), m.group(6), m.group(7), m.group(8))
        out.append((lat, lon))
    return out


def coords_from_line(line: str, pending_center_skip: bool) -> tuple[list[tuple[float, float]], bool]:
    coords: list[tuple[float, float]]
    pending = pending_center_skip

    centered_match = CENTERED_ON_RE.search(line)
    if centered_match:
        before = line[: centered_match.start()]
        after = line[centered_match.end() :]
        coords_before = parse_coords(before)
        coords_after = parse_coords(after)

        if pending and coords_before:
            coords_before = coords_before[1:]
            pending = False

        if coords_after:
            # First coordinate after "centered on" is arc center, not boundary vertex.
            coords_after = coords_after[1:]
        else:
            pending = True

        coords = coords_before + coords_after
        return coords, pending

    coords = parse_coords(line)
    if pending and coords:
        # Previous line announced "centered on" with no coordinate; skip this center point.
        coords = coords[1:]
        pending = False
    return coords, pending


def dedupe_consecutive(points: Iterable[tuple[float, float]]) -> list[tuple[float, float]]:
    out: list[tuple[float, float]] = []
    for p in points:
        if not out or out[-1] != p:
            out.append(p)
    return out


def close_ring(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    if not points:
        return points
    if points[0] != points[-1]:
        points.append(points[0])
    return points


def extract_block(lines: list[str], start_marker: str) -> list[tuple[float, float]]:
    start_idx = -1
    start_upper = start_marker.upper()
    for i, line in enumerate(lines):
        if start_upper in line.upper():
            start_idx = i
            break
    if start_idx < 0:
        return []

    points: list[tuple[float, float]] = []
    pending_center_skip = False
    for line in lines[start_idx:]:
        line_points, pending_center_skip = coords_from_line(line, pending_center_skip)
        points.extend(line_points)
        if "POINT OF BEGINNING" in line.upper():
            break

    points = dedupe_consecutive(points)
    points = close_ring(points)
    return points


def to_feature(fid: str, name: str, zone_type: str, points: list[tuple[float, float]]) -> dict:
    if len(points) < 4:
        raise ValueError(f"Not enough points for polygon: {fid}")

    ring = [[lon, lat] for lat, lon in points]
    return {
        "type": "Feature",
        "properties": {
            "id": fid,
            "name": name,
            "class": "F",
            "designation": "Other",
            "zone_type": zone_type,
            "lower": "SFC",
            "upper": "",
            "active": "Unknown",
            "section": "DAH PDF",
            "source": "Transport Canada DAH PDF",
        },
        "geometry": {
            "type": "Polygon",
            "coordinates": [ring],
        },
    }


def main() -> None:
    args = parse_args()
    pdf_path = Path(args.pdf)
    out_path = Path(args.output)

    if not pdf_path.exists():
        raise SystemExit(f"Missing DAH PDF: {pdf_path}")

    reader = PdfReader(str(pdf_path))

    # ADIZ text spans M6 pages 210-211 in the current DAH layout.
    adiz_lines = page_lines(reader, 210) + page_lines(reader, 211)

    # MOA glossary text spans pages 15-17 in current DAH layout.
    moa_lines = page_lines(reader, 15) + page_lines(reader, 16) + page_lines(reader, 17)

    blocks = [
        ("ADIZ-NE", "Air Defence Identification Zone (North and East)", "ADIZ", adiz_lines, "a) North and East"),
        ("ADIZ-W", "Air Defence Identification Zone (West)", "ADIZ", adiz_lines, "b) West"),
        ("MOA-ALGONQUIN", "Algonquin Military Operational Area", "MOA", moa_lines, "a) ALGONQUIN MOA"),
        ("MOA-ELK", "Elk Military Operational Area", "MOA", moa_lines, "b) ELK MOA"),
        ("MOA-SHEARWATER-S1", "Shearwater MOA DIP Sector 1", "MOA", moa_lines, "i)  Shearwater DIP Sector 1"),
        ("MOA-SHEARWATER-S2", "Shearwater MOA DIP Sector 2", "MOA", moa_lines, "ii) Shearwater DIP Sector 2"),
        ("MOA-SHEARWATER-S3", "Shearwater MOA DIP Sector 3", "MOA", moa_lines, "iii) Shearwater DIP Sector 3"),
        ("MOA-SHEARWATER-S4", "Shearwater MOA DIP Sector 4", "MOA", moa_lines, "iv) Shearwater DIP Sector 4"),
    ]

    features: list[dict] = []
    for fid, name, zone_type, lines, marker in blocks:
        pts = extract_block(lines, marker)
        if not pts:
            print(f"Warning: no points extracted for {fid} ({marker})")
            continue
        try:
            features.append(to_feature(fid, name, zone_type, pts))
        except ValueError as exc:
            print(f"Warning: {exc}")

    collection = {
        "type": "FeatureCollection",
        "name": "dah_special_zones",
        "metadata": {
            "source_pdf": str(pdf_path),
            "feature_count": len(features),
            "zone_types": sorted({f["properties"]["zone_type"] for f in features}),
        },
        "features": features,
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(collection, indent=2), encoding="utf-8")
    print(f"Wrote {len(features)} special zones to {out_path}")


if __name__ == "__main__":
    main()
