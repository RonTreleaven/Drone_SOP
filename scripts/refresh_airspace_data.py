#!/usr/bin/env python3
"""
Refresh airspace datasets used by GGcode.html and DAHminimap.html.

Pipelines:
1) OpenAir -> DAH Gold
    input:  data/airspace/_sources/canadian_airspace.air
   output: data/airspace/dah_gold_airspace.geojson

2) OpenAIP GeoJSON -> Canadian mission lookup
    input:  data/airspace/_sources/ca_asp.geojson
   output: data/canadian_airspace.geojson

Optional URL downloads can refresh source files before build.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.request import Request, urlopen


DEFAULT_SOURCE_DIR = "data/airspace/_sources"
DEFAULT_OPENAIR_URL = "https://airspace.canadarasp.com/OpenAirFiles/canadian_airspace.air"
DEFAULT_AIRPORTS_CSV_URL = "https://raw.githubusercontent.com/davidmegginson/ourairports-data/main/airports.csv"

# ca_asp/ca_apt sources are intentionally provider-agnostic.
# Supply your authoritative provider URLs at runtime via --ca-asp-url / --ca-apt-url.


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Refresh airspace data files")

    p.add_argument("--skip-dah", action="store_true", help="Skip OpenAir -> DAH gold build")
    p.add_argument("--skip-canadian", action="store_true", help="Skip OpenAIP -> canadian_airspace build")

    p.add_argument(
        "--openair-url",
        default=DEFAULT_OPENAIR_URL,
        help="Source URL for canadian_airspace.air",
    )
    p.add_argument(
        "--source-dir",
        default=DEFAULT_SOURCE_DIR,
        help="Canonical source folder for downloaded/managed inputs.",
    )
    p.add_argument(
        "--openair-input",
        default="",
        help="Local .air input path for parse_dah_openair.py",
    )
    p.add_argument(
        "--download-openair",
        action="store_true",
        help="Download canadian_airspace.air from --openair-url before parsing",
    )
    p.add_argument(
        "--require-web-openair",
        action="store_true",
        help="Fail unless --download-openair is used so OpenAir source is freshly pulled.",
    )

    p.add_argument(
        "--dah-output",
        default="data/airspace/dah_gold_airspace.geojson",
        help="Output path for DAH Gold GeoJSON",
    )
    p.add_argument(
        "--dah-metadata-output",
        default="data/airspace/_derived/dah_gold_airspace.metadata.json",
        help="Output path for DAH metadata JSON",
    )
    p.add_argument(
        "--discover-latest-dah-url",
        action="store_true",
        help="Pass through to parse_dah_openair.py for metadata source_url/publication_date discovery",
    )
    p.add_argument(
        "--download-dah-pdf",
        action="store_true",
        help="Download the current DAH PDF into canonical _sources from discovered metadata source_url.",
    )
    p.add_argument(
        "--dah-pdf-url",
        default="",
        help="Optional DAH PDF URL override (used instead of discovered metadata source_url).",
    )
    p.add_argument(
        "--dah-pdf-input",
        default="",
        help="Optional local DAH PDF path for special zone extraction.",
    )
    p.add_argument(
        "--extract-dah-special-zones",
        action="store_true",
        help="Extract ADIZ/MOA zones from DAH PDF and merge into dah_gold_airspace.geojson.",
    )
    p.add_argument(
        "--dah-special-output",
        default="data/airspace/_derived/dah_special_zones.geojson",
        help="Output path for extracted DAH special zones GeoJSON.",
    )

    p.add_argument(
        "--airports-csv-url",
        default=DEFAULT_AIRPORTS_CSV_URL,
        help="Source URL for airports.csv (stored in canonical _sources directory).",
    )
    p.add_argument(
        "--download-airports-csv",
        action="store_true",
        help="Download airports.csv into canonical _sources before DAHminimap runtime use.",
    )

    p.add_argument(
        "--ca-asp-url",
        default="",
        help="Optional URL for ca_asp.geojson download from your chosen provider.",
    )
    p.add_argument(
        "--ca-apt-url",
        default="",
        help="Optional URL for ca_apt.geojson download from your chosen provider.",
    )
    p.add_argument(
        "--download-ca-sources",
        action="store_true",
        help="Download ca_asp.geojson and optional ca_apt.geojson from provided URLs before build.",
    )
    p.add_argument(
        "--require-web-ca-asp",
        action="store_true",
        help="Fail unless ca_asp.geojson is downloaded from --ca-asp-url in this run.",
    )
    p.add_argument(
        "--ca-asp-input",
        default="",
        help="Input path for build_canadian_airspace_geojson.py",
    )
    p.add_argument(
        "--ca-apt-output",
        default="",
        help="Local output path when --ca-apt-url is used",
    )
    p.add_argument(
        "--canadian-output",
        default="data/canadian_airspace.geojson",
        help="Output path for canadian_airspace.geojson",
    )
    p.add_argument(
        "--classes",
        default="B,C,D,E,F",
        help="Class allowlist for canadian_airspace build",
    )
    p.add_argument(
        "--max-lower-agl-ft",
        type=float,
        default=400.0,
        help="Lower AGL filter for canadian_airspace build",
    )
    p.add_argument(
        "--include-airways",
        action="store_true",
        help="Include airways in canadian_airspace build",
    )

    p.add_argument(
        "--sync-canadian-to-airspace-folder",
        action="store_true",
        help="Copy canadian output to data/airspace/canadian_airspace.geojson as a mirror",
    )

    return p.parse_args()


def download_to(url: str, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    req = Request(url, headers={"User-Agent": "Drone-SOP-Airspace-Refresh"})
    with urlopen(req, timeout=180) as resp:  # nosec: B310
        data = resp.read()
    out_path.write_bytes(data)
    print(f"Downloaded {url} -> {out_path}")


def run_cmd(args: list[str]) -> None:
    print("Running:", " ".join(args))
    subprocess.run(args, check=True)


def merge_special_zones(main_geojson: Path, special_geojson: Path) -> int:
    if not main_geojson.exists() or not special_geojson.exists():
        return 0

    main = json.loads(main_geojson.read_text(encoding="utf-8"))
    special = json.loads(special_geojson.read_text(encoding="utf-8"))

    main_features = list(main.get("features", []))
    special_features = list(special.get("features", []))

    existing_ids = set()
    for ft in main_features:
        props = ft.get("properties", {}) if isinstance(ft, dict) else {}
        fid = str(props.get("id") or "").strip()
        if fid:
            existing_ids.add(fid)

    added = 0
    for ft in special_features:
        props = ft.get("properties", {}) if isinstance(ft, dict) else {}
        fid = str(props.get("id") or "").strip()
        if fid and fid in existing_ids:
            continue
        main_features.append(ft)
        if fid:
            existing_ids.add(fid)
        added += 1

    main["features"] = main_features
    meta = main.get("metadata") if isinstance(main.get("metadata"), dict) else {}
    meta["feature_count"] = len(main_features)
    meta["special_zone_feature_count"] = len(special_features)
    main["metadata"] = meta

    main_geojson.write_text(json.dumps(main, indent=2), encoding="utf-8")
    return added


def main() -> None:
    args = parse_args()
    root = Path(__file__).resolve().parents[1]
    source_dir = root / args.source_dir
    source_dir.mkdir(parents=True, exist_ok=True)

    openair_input = root / args.openair_input if args.openair_input else source_dir / "canadian_airspace.air"
    dah_output = root / args.dah_output
    dah_meta = root / args.dah_metadata_output
    dah_special_output = root / args.dah_special_output

    ca_asp_input = root / args.ca_asp_input if args.ca_asp_input else source_dir / "ca_asp.geojson"
    canadian_output = root / args.canadian_output
    ca_apt_output = root / args.ca_apt_output if args.ca_apt_output else source_dir / "ca_apt.geojson"
    airports_csv_output = source_dir / "airports.csv"

    if args.require_web_openair and not args.download_openair and not args.skip_dah:
        raise SystemExit("--require-web-openair requires --download-openair.")

    if args.require_web_ca_asp and not args.download_ca_sources and not args.skip_canadian:
        raise SystemExit("--require-web-ca-asp requires --download-ca-sources.")

    if args.download_openair and not args.skip_dah:
        download_to(args.openair_url, openair_input)

    downloaded_ca_asp = False
    if args.download_ca_sources and not args.skip_canadian:
        if not args.ca_asp_url:
            raise SystemExit("--download-ca-sources requires --ca-asp-url.")
        download_to(args.ca_asp_url, ca_asp_input)
        downloaded_ca_asp = True

    if args.download_ca_sources and args.ca_apt_url:
        download_to(args.ca_apt_url, ca_apt_output)

    if args.download_airports_csv:
        download_to(args.airports_csv_url, airports_csv_output)

    if not args.skip_dah:
        if not openair_input.exists():
            raise SystemExit(f"Missing OpenAir input: {openair_input}")

        cmd = [
            sys.executable,
            str(root / "scripts" / "parse_dah_openair.py"),
            "--input",
            str(openair_input),
            "--output",
            str(dah_output),
            "--metadata-output",
            str(dah_meta),
        ]
        if args.discover_latest_dah_url:
            cmd.append("--discover-latest-dah-url")
        run_cmd(cmd)

        dah_pdf_path = root / args.dah_pdf_input if args.dah_pdf_input else None
        dah_pdf_url = args.dah_pdf_url.strip()
        publication_date = ""

        if dah_meta.exists():
            try:
                meta_obj = json.loads(dah_meta.read_text(encoding="utf-8"))
                publication_date = str(meta_obj.get("publication_date") or "").strip()
                if not dah_pdf_url:
                    dah_pdf_url = str(meta_obj.get("source_url") or "").strip()
            except json.JSONDecodeError:
                pass

        if args.download_dah_pdf:
            if not dah_pdf_url:
                raise SystemExit("--download-dah-pdf requested but no DAH PDF URL is available.")
            pdf_name = f"dah{publication_date}.pdf" if publication_date else "dah_latest.pdf"
            dah_pdf_path = source_dir / pdf_name
            download_to(dah_pdf_url, dah_pdf_path)

        if args.extract_dah_special_zones:
            if dah_pdf_path is None:
                if publication_date:
                    candidate = source_dir / f"dah{publication_date}.pdf"
                    if candidate.exists():
                        dah_pdf_path = candidate
            if dah_pdf_path is None or not dah_pdf_path.exists():
                raise SystemExit(
                    "DAH special zone extraction requested but no DAH PDF is available. "
                    "Use --download-dah-pdf or provide --dah-pdf-input."
                )

            extract_cmd = [
                sys.executable,
                str(root / "scripts" / "extract_dah_special_zones.py"),
                "--pdf",
                str(dah_pdf_path),
                "--output",
                str(dah_special_output),
            ]
            run_cmd(extract_cmd)

            added = merge_special_zones(dah_output, dah_special_output)
            print(f"Merged {added} DAH special zone feature(s) into {dah_output}")

    if not args.skip_canadian:
        if args.require_web_ca_asp and not downloaded_ca_asp:
            raise SystemExit("Web ca_asp download was required but not completed.")

        if not ca_asp_input.exists():
            raise SystemExit(
                "Missing canonical source input: "
                f"{ca_asp_input}. Download/update this file (use --ca-asp-url) and rerun."
            )

        cmd = [
            sys.executable,
            str(root / "scripts" / "build_canadian_airspace_geojson.py"),
            "--input",
            str(ca_asp_input),
            "--output",
            str(canadian_output),
            "--classes",
            args.classes,
            "--max-lower-agl-ft",
            str(args.max_lower_agl_ft),
        ]
        if args.include_airways:
            cmd.append("--include-airways")
        run_cmd(cmd)

        if args.sync_canadian_to_airspace_folder:
            mirror = root / "data" / "airspace" / "canadian_airspace.geojson"
            mirror.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(canadian_output, mirror)
            print(f"Mirrored {canadian_output} -> {mirror}")

    print("Refresh complete.")


if __name__ == "__main__":
    main()
