#!/usr/bin/env python3
"""Analyze geotagged mission photos against DJI waylines.wpml waypoints.

Usage:
  python scripts/analyze_photo_coverage_vs_waylines.py --dir "G:/DJI_Mini_Flights/New folder"
  python scripts/analyze_photo_coverage_vs_waylines.py --dir "G:/..." --wpml "G:/.../waylines.wpml"
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import html
import json
import math
import re
import statistics
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from PIL import Image, ExifTags

KML_NS = "http://www.opengis.net/kml/2.2"
WPML_NS = "http://www.uav.com/wpmz/1.0.2"
NS = {"kml": KML_NS, "wpml": WPML_NS}


@dataclass
class Waypoint:
    index: int
    lat: float
    lon: float


@dataclass
class PhotoPoint:
    name: str
    ts: Optional[dt.datetime]
    lat: Optional[float]
    lon: Optional[float]


@dataclass
class Match:
    photo: PhotoPoint
    nearest_wp: int
    distance_m: float


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Compare geotagged JPGs to waylines.wpml")
    p.add_argument("--dir", required=True, help="Folder containing mission JPGs and waylines.wpml")
    p.add_argument("--wpml", default=None, help="Optional explicit path to waylines.wpml")
    p.add_argument("--speed", type=float, default=4.0, help="Planned speed m/s")
    p.add_argument("--turn-penalty", type=float, default=0.2, help="Seconds per turn (segments-1)")
    p.add_argument("--csv-out", default=None, help="Optional CSV output path (default: <dir>/photo_wp_matches.csv)")
    p.add_argument("--geojson-out", default=None, help="Optional GeoJSON output path (default: <dir>/photo_wp_overview.geojson)")
    p.add_argument("--kml-out", default=None, help="Optional KML output path (default: <dir>/photo_wp_overview.kml)")
    p.add_argument("--geojson-photo-step", type=int, default=5, help="Include every Nth photo point in GeoJSON (default: 5)")
    return p.parse_args()


def _to_deg(value: Tuple[Tuple[int, int], Tuple[int, int], Tuple[int, int]], ref: str) -> float:
    d = value[0][0] / value[0][1]
    m = value[1][0] / value[1][1]
    s = value[2][0] / value[2][1]
    deg = d + (m / 60.0) + (s / 3600.0)
    if ref in ("S", "W"):
        deg = -deg
    return deg


def _extract_xmp_gps(path: Path) -> Tuple[Optional[float], Optional[float]]:
    try:
        raw = path.read_bytes()
    except Exception:
        return None, None

    # DJI often stores geotags in XMP packet attributes.
    m_lat = re.search(rb"drone-dji:GpsLatitude=\"([^\"]+)\"", raw)
    m_lon = re.search(rb"drone-dji:GpsLongitude=\"([^\"]+)\"", raw)
    if m_lat and m_lon:
        try:
            lat = float(m_lat.group(1).decode("utf-8", errors="ignore"))
            lon = float(m_lon.group(1).decode("utf-8", errors="ignore"))
            return lat, lon
        except Exception:
            pass

    # Some files use plain GPSLatitude/GPSLongitude keys.
    m_lat2 = re.search(rb"GPSLatitude=\"([^\"]+)\"", raw)
    m_lon2 = re.search(rb"GPSLongitude=\"([^\"]+)\"", raw)
    if m_lat2 and m_lon2:
        try:
            lat = float(m_lat2.group(1).decode("utf-8", errors="ignore"))
            lon = float(m_lon2.group(1).decode("utf-8", errors="ignore"))
            return lat, lon
        except Exception:
            pass

    return None, None


def read_photos(folder: Path) -> List[PhotoPoint]:
    discovered = [
        *folder.glob("*.jpg"),
        *folder.glob("*.JPG"),
        *folder.glob("*.jpeg"),
        *folder.glob("*.JPEG"),
    ]
    # On Windows, globbing different letter cases can return the same file twice.
    unique: Dict[str, Path] = {}
    for p in discovered:
        unique[str(p).lower()] = p
    jpgs = sorted(unique.values(), key=lambda p: p.name.lower())
    exif_map = {v: k for k, v in ExifTags.TAGS.items()}
    gps_map = ExifTags.GPSTAGS

    photos: List[PhotoPoint] = []
    for path in jpgs:
        ts: Optional[dt.datetime] = None
        lat: Optional[float] = None
        lon: Optional[float] = None

        try:
            with Image.open(path) as img:
                exif = img.getexif()
                if exif:
                    dt_orig = exif.get(exif_map.get("DateTimeOriginal")) or exif.get(exif_map.get("DateTime"))
                    if isinstance(dt_orig, str):
                        try:
                            ts = dt.datetime.strptime(dt_orig, "%Y:%m:%d %H:%M:%S")
                        except ValueError:
                            ts = None

                    gps_info = exif.get(exif_map.get("GPSInfo"))
                    if gps_info:
                        gps: Dict[str, object] = {}
                        for key, val in gps_info.items():
                            name = gps_map.get(key, key)
                            gps[name] = val
                        if all(k in gps for k in ("GPSLatitude", "GPSLatitudeRef", "GPSLongitude", "GPSLongitudeRef")):
                            lat = _to_deg(gps["GPSLatitude"], str(gps["GPSLatitudeRef"]))
                            lon = _to_deg(gps["GPSLongitude"], str(gps["GPSLongitudeRef"]))
        except Exception:
            pass

        if lat is None or lon is None:
            x_lat, x_lon = _extract_xmp_gps(path)
            if x_lat is not None and x_lon is not None:
                lat, lon = x_lat, x_lon

        photos.append(PhotoPoint(name=path.name, ts=ts, lat=lat, lon=lon))

    photos.sort(key=lambda p: (p.ts is None, p.ts or dt.datetime.max, p.name))
    return photos


def read_waypoints(wpml_path: Path) -> List[Waypoint]:
    root = ET.parse(wpml_path).getroot()
    points: List[Waypoint] = []
    for pm in root.findall(".//kml:Placemark", NS):
        idx_el = pm.find("wpml:index", NS)
        coord_el = pm.find("./kml:Point/kml:coordinates", NS)
        if idx_el is None or coord_el is None or not coord_el.text:
            continue
        idx = int(idx_el.text.strip())
        lon_s, lat_s = coord_el.text.strip().split(",")[:2]
        points.append(Waypoint(index=idx, lat=float(lat_s), lon=float(lon_s)))
    points.sort(key=lambda w: w.index)
    return points


def haversine_m(a_lat: float, a_lon: float, b_lat: float, b_lon: float) -> float:
    r = 6371000.0
    dlat = math.radians(b_lat - a_lat)
    dlon = math.radians(b_lon - a_lon)
    s1 = math.sin(dlat / 2.0)
    s2 = math.sin(dlon / 2.0)
    aa = s1 * s1 + math.cos(math.radians(a_lat)) * math.cos(math.radians(b_lat)) * s2 * s2
    return 2 * r * math.atan2(math.sqrt(aa), math.sqrt(1 - aa))


def nearest_waypoint(lat: float, lon: float, waypoints: Sequence[Waypoint]) -> Tuple[int, float]:
    best_idx = -1
    best_d = float("inf")
    for w in waypoints:
        d = haversine_m(lat, lon, w.lat, w.lon)
        if d < best_d:
            best_idx = w.index
            best_d = d
    return best_idx, best_d


def rolling_median(values: Sequence[int], window: int = 7) -> List[float]:
    out: List[float] = []
    half = window // 2
    for i in range(len(values)):
        lo = max(0, i - half)
        hi = min(len(values), i + half + 1)
        out.append(statistics.median(values[lo:hi]))
    return out


def compute_contiguous(matches: Sequence[Match], threshold: float) -> int:
    reached = {m.nearest_wp for m in matches if m.distance_m <= threshold}
    if not reached:
        return -1
    c = 0
    while c in reached:
        c += 1
    return c - 1


def planned_distance_m(waypoints: Sequence[Waypoint]) -> float:
    total = 0.0
    for a, b in zip(waypoints, waypoints[1:]):
        total += haversine_m(a.lat, a.lon, b.lat, b.lon)
    return total


def fmt_dur(seconds: float) -> str:
    seconds = max(0, int(round(seconds)))
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    if h:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def write_csv(matches: Sequence[Match], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["photo_name", "timestamp", "lat", "lon", "nearest_wp", "distance_m"])
        for m in matches:
            w.writerow([
                m.photo.name,
                m.photo.ts.isoformat(sep=" ") if m.photo.ts else "",
                f"{m.photo.lat:.9f}" if m.photo.lat is not None else "",
                f"{m.photo.lon:.9f}" if m.photo.lon is not None else "",
                m.nearest_wp,
                f"{m.distance_m:.3f}",
            ])


def write_geojson(
    waypoints: Sequence[Waypoint],
    matches: Sequence[Match],
    out_path: Path,
    photo_step: int,
    conservative_restart: int,
    aggressive_restart: int,
    split_idx: int,
) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    step = max(1, int(photo_step))

    features: List[Dict[str, object]] = []

    planned_coords = [[w.lon, w.lat] for w in waypoints]
    features.append({
        "type": "Feature",
        "properties": {"layer": "planned_wayline", "waypoint_count": len(waypoints)},
        "geometry": {"type": "LineString", "coordinates": planned_coords},
    })

    flown_coords = [[m.photo.lon, m.photo.lat] for m in matches if m.photo.lon is not None and m.photo.lat is not None]
    if len(flown_coords) >= 2:
        features.append({
            "type": "Feature",
            "properties": {"layer": "flown_photo_track", "photo_count": len(flown_coords)},
            "geometry": {"type": "LineString", "coordinates": flown_coords},
        })

    for w in waypoints:
        role = "normal"
        if w.index == conservative_restart:
            role = "restart_conservative"
        elif w.index == aggressive_restart:
            role = "restart_aggressive"
        elif w.index == split_idx:
            role = "split_candidate"
        features.append({
            "type": "Feature",
            "properties": {"layer": "waypoint", "wp": w.index, "role": role},
            "geometry": {"type": "Point", "coordinates": [w.lon, w.lat]},
        })

    for i, m in enumerate(matches):
        if i % step != 0 and i != len(matches) - 1:
            continue
        if m.photo.lon is None or m.photo.lat is None:
            continue
        features.append({
            "type": "Feature",
            "properties": {
                "layer": "photo_sample",
                "photo": m.photo.name,
                "time": m.photo.ts.isoformat(sep=" ") if m.photo.ts else "",
                "nearest_wp": m.nearest_wp,
                "distance_m": round(m.distance_m, 3),
            },
            "geometry": {"type": "Point", "coordinates": [m.photo.lon, m.photo.lat]},
        })

    fc = {"type": "FeatureCollection", "features": features}
    out_path.write_text(json.dumps(fc, indent=2), encoding="utf-8")


def write_kml(
        waypoints: Sequence[Waypoint],
        matches: Sequence[Match],
        out_path: Path,
        photo_step: int,
        conservative_restart: int,
        aggressive_restart: int,
        split_idx: int,
) -> None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        step = max(1, int(photo_step))

        planned_coords = " ".join(f"{w.lon:.9f},{w.lat:.9f},0" for w in waypoints)
        flown_coords = " ".join(
                f"{m.photo.lon:.9f},{m.photo.lat:.9f},0"
                for m in matches
                if m.photo.lon is not None and m.photo.lat is not None
        )

        waypoint_placemarks: List[str] = []
        for w in waypoints:
                role = "normal"
                if w.index == conservative_restart:
                        role = "restart_conservative"
                elif w.index == aggressive_restart:
                        role = "restart_aggressive"
                elif w.index == split_idx:
                        role = "split_candidate"
                waypoint_placemarks.append(
                        f"""
            <Placemark>
                <name>WP {w.index}</name>
                <description>{html.escape(role)}</description>
                <Point><coordinates>{w.lon:.9f},{w.lat:.9f},0</coordinates></Point>
            </Placemark>"""
                )

        photo_placemarks: List[str] = []
        for i, m in enumerate(matches):
                if i % step != 0 and i != len(matches) - 1:
                        continue
                if m.photo.lon is None or m.photo.lat is None:
                        continue
                ts = m.photo.ts.isoformat(sep=" ") if m.photo.ts else ""
                desc = (
                        f"photo={html.escape(m.photo.name)}\n"
                        f"time={html.escape(ts)}\n"
                        f"nearest_wp={m.nearest_wp}\n"
                        f"distance_m={m.distance_m:.3f}"
                )
                photo_placemarks.append(
                        f"""
            <Placemark>
                <name>{html.escape(m.photo.name)}</name>
                <description>{html.escape(desc)}</description>
                <Point><coordinates>{m.photo.lon:.9f},{m.photo.lat:.9f},0</coordinates></Point>
            </Placemark>"""
                )

        kml = f"""<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<kml xmlns=\"http://www.opengis.net/kml/2.2\">
    <Document>
        <name>photo_wp_overview</name>
        <Placemark>
            <name>planned_wayline</name>
            <LineString>
                <tessellate>1</tessellate>
                <coordinates>{planned_coords}</coordinates>
            </LineString>
        </Placemark>
        <Placemark>
            <name>flown_photo_track</name>
            <LineString>
                <tessellate>1</tessellate>
                <coordinates>{flown_coords}</coordinates>
            </LineString>
        </Placemark>
        <Folder>
            <name>waypoints</name>
            {''.join(waypoint_placemarks)}
        </Folder>
        <Folder>
            <name>photo_samples</name>
            {''.join(photo_placemarks)}
        </Folder>
    </Document>
</kml>
"""
        out_path.write_text(kml, encoding="utf-8")


def main() -> int:
    args = parse_args()
    folder = Path(args.dir)
    wpml = Path(args.wpml) if args.wpml else folder / "waylines.wpml"

    if not folder.exists():
        raise SystemExit(f"Folder not found: {folder}")
    if not wpml.exists():
        raise SystemExit(f"waylines.wpml not found: {wpml}")

    waypoints = read_waypoints(wpml)
    photos = read_photos(folder)
    geotagged = [p for p in photos if p.lat is not None and p.lon is not None]

    matches: List[Match] = []
    for p in geotagged:
        idx, d = nearest_waypoint(p.lat, p.lon, waypoints)
        matches.append(Match(photo=p, nearest_wp=idx, distance_m=d))

    print("=== Mission Coverage Analysis ===")
    print(f"Folder: {folder}")
    print(f"WPML: {wpml}")
    print(f"Waypoints: {len(waypoints)} ({waypoints[0].index}..{waypoints[-1].index})")
    print(f"Photos total: {len(photos)}")
    print(f"Photos with GPS: {len(geotagged)}")

    timed = [p for p in photos if p.ts is not None]
    if timed:
        elapsed_s = (timed[-1].ts - timed[0].ts).total_seconds()
        print(f"Capture window: {timed[0].ts} -> {timed[-1].ts} ({fmt_dur(elapsed_s)})")

    if not matches:
        print("No geotagged photos found; cannot compare to waypoints.")
        return 0

    idxs = [m.nearest_wp for m in matches]
    dists = [m.distance_m for m in matches]
    print(f"Nearest waypoint index range: {min(idxs)}..{max(idxs)}")
    print(f"Median nearest distance: {statistics.median(dists):.1f} m")

    print("\nThreshold summary:")
    for t in (20, 30, 40, 60):
        max_wp = max((m.nearest_wp for m in matches if m.distance_m <= t), default=-1)
        cont = compute_contiguous(matches, t)
        print(f"  <= {t:>2} m: max={max_wp:>2}, contiguous={cont:>2}")

    med = rolling_median(idxs, window=7)
    last_sustained_i = 0
    for i in range(1, len(med)):
        if med[i] > med[last_sustained_i]:
            last_sustained_i = i
    last_sustained = matches[last_sustained_i]

    conservative_restart = max(0, compute_contiguous(matches, 30) - 1)
    aggressive_restart = max(0, max((m.nearest_wp for m in matches if m.distance_m <= 40), default=0) + 1)

    route_m = planned_distance_m(waypoints)
    segment_count = max(0, len(waypoints) - 1)
    ideal_time_s = route_m / max(0.1, args.speed)
    est_time_s = ideal_time_s + (segment_count * max(0, args.turn_penalty))

    half_dist = route_m / 2.0
    acc = 0.0
    split_idx = waypoints[0].index
    for a, b in zip(waypoints, waypoints[1:]):
        leg = haversine_m(a.lat, a.lon, b.lat, b.lon)
        if acc + leg >= half_dist:
            split_idx = b.index
            break
        acc += leg

    print("\nProgression signal:")
    print(
        f"  Last sustained rolling-median increase near WP {int(round(last_sustained.nearest_wp))} "
        f"at {last_sustained.photo.ts} (distance {last_sustained.distance_m:.1f} m)"
    )

    print("\nTop 15 highest-index matched photos:")
    top = sorted(matches, key=lambda m: (m.nearest_wp, -m.distance_m), reverse=True)[:15]
    for m in top:
        print(f"  {m.photo.name} | {m.photo.ts} | wp={m.nearest_wp} | d={m.distance_m:.1f} m")

    print("\nLast 25 photos:")
    for m in matches[-25:]:
        print(f"  {m.photo.name} | {m.photo.ts} | wp={m.nearest_wp} | d={m.distance_m:.1f} m")

    print("\nTime and split planning:")
    print(f"  Planned route distance: {route_m:.0f} m")
    print(f"  Ideal cruise @ {args.speed:.1f} m/s: {fmt_dur(ideal_time_s)}")
    print(f"  Estimated with turn penalty: {fmt_dur(est_time_s)}")
    print(f"  Half-distance split candidate waypoint: {split_idx}")

    print("\nRecommended restart range:")
    print(f"  Conservative restart waypoint: {conservative_restart}")
    print(f"  Aggressive restart waypoint: {aggressive_restart}")

    csv_out = Path(args.csv_out) if args.csv_out else folder / "photo_wp_matches.csv"
    geojson_out = Path(args.geojson_out) if args.geojson_out else folder / "photo_wp_overview.geojson"
    kml_out = Path(args.kml_out) if args.kml_out else folder / "photo_wp_overview.kml"
    write_csv(matches, csv_out)
    write_geojson(
        waypoints=waypoints,
        matches=matches,
        out_path=geojson_out,
        photo_step=args.geojson_photo_step,
        conservative_restart=conservative_restart,
        aggressive_restart=aggressive_restart,
        split_idx=split_idx,
    )
    write_kml(
        waypoints=waypoints,
        matches=matches,
        out_path=kml_out,
        photo_step=args.geojson_photo_step,
        conservative_restart=conservative_restart,
        aggressive_restart=aggressive_restart,
        split_idx=split_idx,
    )
    print("\nArtifacts:")
    print(f"  CSV: {csv_out}")
    print(f"  GeoJSON: {geojson_out}")
    print(f"  KML: {kml_out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
