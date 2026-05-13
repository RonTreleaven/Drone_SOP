import re
import hashlib
import difflib
import os

files = ["NotamsMap.html", "NotamsMap_regen_test.html"]
results = {}

def get_sha256(fname):
    with open(fname, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

def normalize(text):
    # Folium IDs
    text = re.sub(r"(map|marker|circle|feature_group_sub_group|feature_group|tile_layer|layer_control|html|popup|tooltip)_[0-9a-f]{32}", r"\1_ID", text)
    # Collapse spaces
    text = re.sub(r"[ \t]+", " ", text)
    return text

contracts = [
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
    "map-layers-close-btn"
]

print("--- FILE STATS ---")
norm_texts = []
for f in files:
    if not os.path.exists(f):
        print(f"Error: {f} not found")
        exit(1)
    size = os.path.getsize(f)
    sha = get_sha256(f)
    print(f"{f}: Size={size}, SHA256={sha}")
    with open(f, "r", encoding="utf-8") as fh:
        raw = fh.read()
        norm_texts.append(normalize(raw))

print("\n--- CONTRACT CHECK ---")
contract_results = []
drift_indicators = []
for c in contracts:
    c_status = []
    lines_found = []
    for i, f in enumerate(files):
        with open(f, "r", encoding="utf-8") as fh:
            lines = fh.readlines()
            found_line = -1
            for l_idx, line in enumerate(lines):
                if c in line:
                    found_line = l_idx + 1
                    break
            c_status.append(found_line != -1)
            lines_found.append(found_line)
    
    status_str = "PASS" if all(c_status) else "FAIL"
    print(f"{status_str:4} | {c[:40]:40} | File1: {lines_found[0]:6} | File2: {lines_found[1]:6}")
    
    if c_status[0] and not c_status[1]:
        drift_indicators.append(f"Manual Addition (Current only): {c}")
    elif not c_status[0] and c_status[1]:
        drift_indicators.append(f"Missing from Manual (Regen only): {c}")

print("\n--- DIFF ANALYSIS ---")
n1 = norm_texts[0].splitlines()
n2 = norm_texts[1].splitlines()
diff = list(difflib.unified_diff(n1, n2, fromfile=files[0], tofile=files[1], n=0))
changed_lines = len([l for l in diff if l.startswith("+") or l.startswith("-")]) - 2 # subtract header
if changed_lines < 0: changed_lines = 0
change_pct = (changed_lines / max(len(n1), 1)) * 100

print(f"Total normalized lines: {len(n1)}")
print(f"Estimated changed lines: {changed_lines}")
print(f"Change percentage: {change_pct:.2f}%")

print("\n--- DIFF SNIPPET (MAX 80 LINES) ---")
for line in diff[:80]:
    print(line)

print("\n--- VERDICT ---")
all_contracts_pass = all([all([c in norm_texts[i] for c in contracts]) for i in range(2)])
reasons = []
if not all_contracts_pass: reasons.append("One or more contracts failed to appear in both files.")
if change_pct > 5.0: reasons.append(f"Change percentage {change_pct:.2f}% exceeds 5% threshold.")

if not reasons:
    print("FINAL VERDICT: PASS")
else:
    print("FINAL VERDICT: WARN")
    for r in reasons:
        print(f" - REASON: {r}")

if drift_indicators:
    print("\n--- LIKELY MANUAL DRIFT INDICATORS ---")
    for d in drift_indicators:
        print(f" - {d}")
