import json
from shapely.geometry import shape, Point
import re

geojson_path = "data/airspace/dah_gold_airspace.geojson"
point = Point(-76.5960, 44.2253)  # lon, lat

with open(geojson_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

matches = []
class_counts = {}
keyword_matches = []
keyword_pattern = re.compile(r'CYGK|KINGSTON', re.IGNORECASE)

for feature in data['features']:
    props = feature['properties']
    geom = shape(feature['geometry'])
    
    # Matching records for spatial containment
    if geom.contains(point):
        matches.append({
            'id': props.get('id'),
            'name': props.get('name'),
            'class': props.get('class'),
            'zone_type': props.get('zone_type'),
            'lower': props.get('lower'),
            'upper': props.get('upper')
        })
    
    # Counts by class
    cls = props.get('class', 'Unknown')
    class_counts[cls] = class_counts.get(cls, 0) + 1
    
    # Keyword matches
    name = props.get('name', '')
    if keyword_pattern.search(name):
        keyword_matches.append(name)

print("--- Spatial Matches at lat 44.2253 lon -76.5960 ---")
for m in matches:
    print(f"ID: {m['id']}, Name: {m['name']}, Class: {m['class']}, Type: {m['zone_type']}, Lower: {m['lower']}, Upper: {m['upper']}")

print("\n--- Counts by Class ---")
for cls, count in sorted(class_counts.items()):
    print(f"{cls}: {count}")

print("\n--- CYGK/KINGSTON Keyword Matches ---")
for name in sorted(set(keyword_matches)):
    print(name)

