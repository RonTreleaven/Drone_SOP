#!/usr/bin/env python3
"""Analyze DJI waylines.wpml or KMZ mission files.

Features:
- Accepts one or more files/folders (.wpml and .kmz)
- Extracts mission config fields (height mode, speed, finish/lost-link behavior)
- Counts waypoints and flags DJI 100-waypoint limit breaches
- Prints human-readable report and optional JSON output
"""

from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional

KML_NS = "http://www.opengis.net/kml/2.2"
WPML_NS = "http://www.uav.com/wpmz/1.0.2"
NS = {"kml": KML_NS, "wpml": WPML_NS}

DJI_WAYPOINT_LIMIT = 100
DEFAULT_DROP_DIR = Path(r"C:\Users\Ron Treleaven\RC2_Missions\Waylines_Testing_PY")
DEFAULT_WPML_NAME = "waylines.wpml"


@dataclass
class MissionReport:
    mission_label: str
    source_path: str
    source_type: str
    waypoint_count: int
    min_index: Optional[int]
    max_index: Optional[int]
    execute_height_mode: Optional[str]
    execute_heights: list[str]
    auto_flight_speed: Optional[str]
    waypoint_speeds: list[str]
    fly_to_wayline_mode: Optional[str]
    finish_action: Optional[str]
    exit_on_rc_lost: Optional[str]
    execute_rc_lost_action: Optional[str]
    global_transitional_speed: Optional[str]
    warnings: list[str]


def _text(node: Optional[ET.Element]) -> Optional[str]:
    if node is None or node.text is None:
        return None
    value = node.text.strip()
    return value if value else None


def _find_wpml(root: ET.Element, tag: str) -> Optional[str]:
    return _text(root.find(f".//wpml:{tag}", NS))


def _extract_wpml_from_kmz(kmz_path: Path) -> bytes:
    with zipfile.ZipFile(kmz_path, "r") as zf:
        candidates = [
            name
            for name in zf.namelist()
            if name.lower().endswith("waylines.wpml")
        ]
        if not candidates:
            raise ValueError("No waylines.wpml found in KMZ")
        preferred = next((n for n in candidates if n.lower() == "wpmz/waylines.wpml"), candidates[0])
        return zf.read(preferred)


def _parse_wpml_bytes(data: bytes) -> ET.Element:
    return ET.fromstring(data)


def _collect_files(paths: Iterable[Path]) -> list[Path]:
    collected: list[Path] = []
    for path in paths:
        if path.is_dir():
            for pattern in ("*.wpml", "*.kmz"):
                collected.extend(sorted(path.rglob(pattern)))
        elif path.is_file():
            collected.append(path)
    return collected


def analyze_file(file_path: Path, mission_label: str) -> MissionReport:
    suffix = file_path.suffix.lower()
    if suffix == ".wpml":
        root = ET.parse(file_path).getroot()
        source_type = "wpml"
    elif suffix == ".kmz":
        root = _parse_wpml_bytes(_extract_wpml_from_kmz(file_path))
        source_type = "kmz"
    else:
        raise ValueError(f"Unsupported file type: {file_path.suffix}")

    idx_nodes = root.findall(".//wpml:index", NS)
    indices = []
    for n in idx_nodes:
        txt = _text(n)
        if txt is None:
            continue
        try:
            indices.append(int(txt))
        except ValueError:
            pass

    height_nodes = root.findall(".//wpml:executeHeight", NS)
    speed_nodes = root.findall(".//wpml:waypointSpeed", NS)

    execute_heights = sorted({v for v in (_text(n) for n in height_nodes) if v is not None})
    waypoint_speeds = sorted({v for v in (_text(n) for n in speed_nodes) if v is not None})

    report = MissionReport(
        mission_label=mission_label,
        source_path=str(file_path),
        source_type=source_type,
        waypoint_count=len(indices),
        min_index=min(indices) if indices else None,
        max_index=max(indices) if indices else None,
        execute_height_mode=_find_wpml(root, "executeHeightMode"),
        execute_heights=execute_heights,
        auto_flight_speed=_find_wpml(root, "autoFlightSpeed"),
        waypoint_speeds=waypoint_speeds,
        fly_to_wayline_mode=_find_wpml(root, "flyToWaylineMode"),
        finish_action=_find_wpml(root, "finishAction"),
        exit_on_rc_lost=_find_wpml(root, "exitOnRCLost"),
        execute_rc_lost_action=_find_wpml(root, "executeRCLostAction"),
        global_transitional_speed=_find_wpml(root, "globalTransitionalSpeed"),
        warnings=[],
    )

    if report.waypoint_count > DJI_WAYPOINT_LIMIT:
        report.warnings.append(
            f"Waypoint count {report.waypoint_count} exceeds DJI limit of {DJI_WAYPOINT_LIMIT}."
        )
    if report.waypoint_count == 0:
        report.warnings.append("No waypoints detected; mission may be invalid.")
    if report.finish_action not in {None, "goHome", "autoLand", "goFirstWaypoint", "noAction"}:
        report.warnings.append(f"Unexpected finishAction value: {report.finish_action}")
    if report.exit_on_rc_lost is None:
        report.warnings.append("exitOnRCLost is missing.")
    if report.execute_rc_lost_action is None:
        report.warnings.append("executeRCLostAction is missing.")

    return report


def print_report(report: MissionReport) -> None:
    print(f"Mission: {report.mission_label}")
    print(f"Source: {report.source_path} ({report.source_type})")
    print(f"Waypoints: {report.waypoint_count} (index range: {report.min_index}..{report.max_index})")
    print(f"Height Mode: {report.execute_height_mode}")
    print(f"Execute Heights: {', '.join(report.execute_heights) if report.execute_heights else 'n/a'}")
    print(f"Auto Flight Speed: {report.auto_flight_speed}")
    print(f"Waypoint Speeds: {', '.join(report.waypoint_speeds) if report.waypoint_speeds else 'n/a'}")
    print(f"Fly To Wayline Mode: {report.fly_to_wayline_mode}")
    print(f"Finish Action (F): {report.finish_action}")
    print(f"RC Lost Exit (S): {report.exit_on_rc_lost}")
    print(f"RC Lost Action: {report.execute_rc_lost_action}")
    print(f"Global Transitional Speed: {report.global_transitional_speed}")

    if report.warnings:
        print("Warnings:")
        for w in report.warnings:
            print(f"- {w}")
    else:
        print("Warnings: none")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze DJI waylines WPML/KMZ files")
    parser.add_argument(
        "inputs",
        nargs="*",
        help="One or more .wpml/.kmz files or directories to scan recursively",
    )
    parser.add_argument(
        "--mission",
        default="Mission_B",
        help="Mission label to include in report output (default: Mission_B)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON report instead of human-readable text",
    )
    parser.add_argument(
        "--no-confirm",
        action="store_true",
        help="Skip confirmation prompt when default drop-folder waylines.wpml is found",
    )
    return parser.parse_args(argv)


def _choose_default_drop_file(no_confirm: bool) -> Optional[Path]:
    candidate = DEFAULT_DROP_DIR / DEFAULT_WPML_NAME
    if not candidate.exists() or not candidate.is_file():
        return None

    modified = datetime.fromtimestamp(candidate.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
    print("Found default test file:")
    print(f"- Path: {candidate}")
    print(f"- Modified: {modified}")

    if no_confirm:
        print("Using default test file (confirmation skipped via --no-confirm).")
        return candidate

    while True:
        answer = input("Use this file? [Y/n]: ").strip().lower()
        if answer in ("", "y", "yes"):
            return candidate
        if answer in ("n", "no"):
            return None
        print("Please answer 'y' or 'n'.")


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    input_paths: list[Path] = []

    default_file = _choose_default_drop_file(args.no_confirm)
    if default_file is not None:
        input_paths.append(default_file)
    else:
        input_paths = [Path(p).expanduser() for p in args.inputs]

    files = _collect_files(input_paths)

    if not files:
        print(
            f"No .wpml or .kmz files found. Place {DEFAULT_WPML_NAME} in {DEFAULT_DROP_DIR} "
            "or pass file/folder paths as arguments.",
            file=sys.stderr,
        )
        return 2

    reports: list[MissionReport] = []
    had_errors = False

    for file_path in files:
        try:
            reports.append(analyze_file(file_path, args.mission))
        except Exception as exc:  # noqa: BLE001
            had_errors = True
            print(f"ERROR: {file_path}: {exc}", file=sys.stderr)

    if args.json:
        print(json.dumps([asdict(r) for r in reports], indent=2))
    else:
        for i, report in enumerate(reports):
            if i:
                print("\n" + "=" * 60)
            print_report(report)

    return 1 if had_errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

#!/usr/bin/env python3
