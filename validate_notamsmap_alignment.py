import argparse
import difflib
import hashlib
import os
import re
import sys
from pathlib import Path


DEFAULT_CONTRACTS = [
    "navcan-proxy.rontreleaven.workers.dev",
    "airportsToggleCtl",
    "refreshFirCacheBtn",
    "openLiveFetch",
    "sourceBtn",
    "ourairports.com/airports/",
    "skyvector.com/airport/",
    "data/notams/All_CA.json",
    "data/notams/All_CA_raw.json",
    "detectProvinceCodeForLocation",
    "applyAirportDefaultsFromLocation",
    "Linked Live View",
    "map-layers-close-btn",
]


def sha256_for_file(path: Path) -> str:
    with path.open("rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def normalize_html(text: str) -> str:
    # Normalize Folium-generated random IDs to reduce false positives in diff.
    text = re.sub(
        r"(map|marker|circle|feature_group_sub_group|feature_group|tile_layer|layer_control|html|popup|tooltip)_[0-9a-f]{32}",
        r"\1_ID",
        text,
    )
    text = re.sub(r"[ \t]+", " ", text)
    return text


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def contract_line_numbers(path: Path, contracts: list[str]) -> dict[str, int]:
    line_map = {c: -1 for c in contracts}
    with path.open("r", encoding="utf-8") as f:
        lines = f.readlines()

    for c in contracts:
        for idx, line in enumerate(lines, start=1):
            if c in line:
                line_map[c] = idx
                break
    return line_map


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate generated NotamsMap candidate against current map using contracts and normalized diff."
    )
    parser.add_argument("--current", default="NotamsMap.html", help="Current production map HTML")
    parser.add_argument("--candidate", required=True, help="Candidate generated map HTML")
    parser.add_argument(
        "--warn-threshold",
        type=float,
        default=5.0,
        help="Warn if normalized change percentage is above this value",
    )
    parser.add_argument(
        "--fail-on-warn",
        action="store_true",
        help="Return non-zero exit code when verdict is WARN",
    )
    args = parser.parse_args()

    current_path = Path(args.current)
    candidate_path = Path(args.candidate)

    for p in [current_path, candidate_path]:
        if not p.exists():
            print(f"ERROR: File not found: {p}")
            return 2

    print("--- FILE STATS ---")
    paths = [current_path, candidate_path]
    norm_lines = []
    for path in paths:
        size = os.path.getsize(path)
        sha = sha256_for_file(path)
        print(f"{path.name}: Size={size}, SHA256={sha}")
        norm_text = normalize_html(load_text(path))
        norm_lines.append(norm_text.splitlines())

    print("\n--- CONTRACT CHECK ---")
    current_contract_lines = contract_line_numbers(current_path, DEFAULT_CONTRACTS)
    candidate_contract_lines = contract_line_numbers(candidate_path, DEFAULT_CONTRACTS)
    missing_contracts = []

    for c in DEFAULT_CONTRACTS:
        c_ok_current = current_contract_lines[c] != -1
        c_ok_candidate = candidate_contract_lines[c] != -1
        status = "PASS" if c_ok_current and c_ok_candidate else "FAIL"
        print(
            f"{status:4} | {c[:40]:40} | "
            f"Current: {current_contract_lines[c]:6} | Candidate: {candidate_contract_lines[c]:6}"
        )
        if not (c_ok_current and c_ok_candidate):
            missing_contracts.append(c)

    print("\n--- DIFF ANALYSIS ---")
    diff = list(
        difflib.unified_diff(
            norm_lines[0],
            norm_lines[1],
            fromfile=current_path.name,
            tofile=candidate_path.name,
            n=0,
        )
    )
    changed_lines = len([d for d in diff if d.startswith("+") or d.startswith("-")]) - 2
    changed_lines = max(changed_lines, 0)
    total_lines = max(len(norm_lines[0]), 1)
    change_pct = (changed_lines / total_lines) * 100

    print(f"Total normalized lines: {total_lines}")
    print(f"Estimated changed lines: {changed_lines}")
    print(f"Change percentage: {change_pct:.2f}%")

    print("\n--- DIFF SNIPPET (MAX 80 LINES) ---")
    for line in diff[:80]:
        print(line)

    reasons = []
    if missing_contracts:
        reasons.append("One or more contracts were missing in current/candidate files.")
    if change_pct > args.warn_threshold:
        reasons.append(
            f"Change percentage {change_pct:.2f}% exceeds threshold {args.warn_threshold:.2f}%."
        )

    print("\n--- VERDICT ---")
    if reasons:
        print("FINAL VERDICT: WARN")
        for reason in reasons:
            print(f" - REASON: {reason}")
        if args.fail_on_warn:
            return 1
        return 0

    print("FINAL VERDICT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
