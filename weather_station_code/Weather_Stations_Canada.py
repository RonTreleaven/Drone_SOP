import requests, json, csv

base = "https://api.weather.gc.ca/collections/climate-stations/items/"
params = {"limit": 1000, "offset": 0, "f": "json"}
all_items = []

while True:
    r = requests.get(base, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    items = data.get("features") or data.get("items") or data.get("features", [])
    if not items:
        break
    all_items.extend(items)
    # progress
    print("Fetched:", len(all_items))
    # stop if fewer than limit returned
    if len(items) < params["limit"]:
        break
    params["offset"] += params["limit"]

# Save combined JSON (GeoJSON-style with features)
out = {"type": "FeatureCollection", "features": all_items}
with open("climate_stations_full.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)

print("Total stations saved:", len(all_items))

# Save as CSV (properties only — LATITUDE/LONGITUDE are already included in properties)
csv_filename = "climate_stations_full.csv"
if all_items:
    fieldnames = list(all_items[0]["properties"].keys())
    with open(csv_filename, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for feature in all_items:
            writer.writerow(feature["properties"])
    print(f"CSV saved to {csv_filename}")