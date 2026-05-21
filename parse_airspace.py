import json
import re
import os

files = [
    "data/airspace/Control_ca_asp.geojson",
    "data/airspace/ca_asp_restricted.geojson",
    "data/ca_asp.geojson"
]

target_bbox = [-78.6, 43.5, -76.6, 44.8] # min_lon, min_lat, max_lon, max_lat
name_pattern = re.compile(r"mountain|view|cfd|cytr|trenton", re.IGNORECASE)

def get_bbox(geometry):
    if not geometry: return None
    t = geometry.get("type")
    coords = geometry.get("coordinates")
    if not coords: return None
    
    lons = []
    lats = []
    
    def extract_coords(c_list):
        for item in c_list:
            if isinstance(item[0], (int, float)):
                lons.append(item[0])
                lats.append(item[1])
            else:
                extract_coords(item)

    if t in ["Polygon", "MultiPolygon"]:
        extract_coords(coords)
    else:
        return None
    
    if not lons: return None
    return [min(lons), min(lats), max(lons), max(lats)]

def intersects(bbox1, bbox2):
    return not (bbox1[2] < bbox2[0] or bbox1[0] > bbox2[2] or bbox1[3] < bbox2[1] or bbox1[1] > bbox2[3])

def get_val(p, keys):
    for k in keys:
        if k in p: return p[k]
    return "N/A"

results = []
name_matches = []
icao_counts = {}

print("Starting processing...")

for filepath in files:
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        continue
    filename = os.path.basename(filepath)
    print(f"Processing {filename}...")
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            features = data.get("features", [])
            print(f"Found {len(features)} features in {filename}")
            for feature in features:
                props = feature.get("properties", {})
                geom = feature.get("geometry")
                
                name = str(get_val(props, ["name", "NAME"]))
                if name_pattern.search(name):
                    name_matches.append((filename, props))

                bbox = get_bbox(geom)
                if bbox and intersects(bbox, target_bbox):
                    icao = str(get_val(props, ["icaoClass", "CLASS", "class"]))
                    results.append({
                        "file": filename,
                        "id": get_val(props, ["_id", "IDENT", "id", "ID"]),
                        "name": name,
                        "type": get_val(props, ["type", "TYPE"]),
                        "icao": icao,
                        "lower": get_val(props, ["lowerLimit", "LOWER_VAL"]),
                        "upper": get_val(props, ["upperLimit", "UPPER_VAL"])
                    })
                    icao_counts[icao] = icao_counts.get(icao, 0) + 1
    except Exception as e:
        print(f"Error processing {filename}: {e}")

print(f"\n{'FILE':<25} {'ID':<15} {'NAME':<30} {'TYPE':<10} {'CLASS':<5} {'LOWER':<10} {'UPPER':<10}")
print("-" * 115)
for r in results:
    print(f"{r['file']:<25} {str(r['id'])[:14]:<15} {str(r['name'])[:28]:<30} {str(r['type'])[:10]:<10} {str(r['icao']):<5} {str(r['lower'])[:8]:<10} {str(r['upper'])[:8]:<10}")

print("\nCounts by icaoClass (Trenton area):")
for icao, count in sorted(icao_counts.items()):
    print(f"{icao}: {count}")

print("\nFeatures matching pattern (mountain|view|cfd|cytr|trenton):")
seen_matches = set()
for fname, props in name_matches:
    uid = str(get_val(props, ["_id", "IDENT", "name", "NAME"]))
    if uid not in seen_matches:
        print(f"File: {fname} | ID: {get_val(props, ['_id', 'IDENT'])} | Name: {get_val(props, ['name', 'NAME'])}")
        seen_matches.add(uid)
