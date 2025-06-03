import requests
import json
import re
from datetime import datetime

# Define the API endpoint
url = "https://plan.navcanada.ca/weather/api/alpha/?site=CZYZ&alpha=notam&notam_choice=default"

# Fetch the data
response = requests.get(url)
data = response.json()

# Helper function to extract DMS coordinates from text
def extract_dms(text):
    pattern = r'(\d{6}[NS])\s*(\d{7}[EW])'
    matches = re.findall(pattern, text)
    return matches

# Convert DMS to Decimal Degrees
def dms_to_dd(dms_lat, dms_lon):
    # Latitude
    lat_deg = int(dms_lat[:2])
    lat_min = int(dms_lat[2:4])
    lat_sec = int(dms_lat[4:6])
    lat_dir = dms_lat[-1]
    lat_dd = lat_deg + lat_min / 60 + lat_sec / 3600
    if lat_dir == 'S':
        lat_dd = -lat_dd
    
    # Longitude
    lon_deg = int(dms_lon[:3])
    lon_min = int(dms_lon[3:5])
    lon_sec = int(dms_lon[5:7])
    lon_dir = dms_lon[-1]
    lon_dd = lon_deg + lon_min / 60 + lon_sec / 3600
    if lon_dir == 'W':
        lon_dd = -lon_dd
    
    return round(lat_dd, 6), round(lon_dd, 6)

############  Notams List
notams_list = []

for item in data.get("data", []):
    raw_text = json.loads(item.get("text", "{}")).get("raw", "")
    if raw_text:
        start_time = item.get("startValidity")
        end_time = item.get("endValidity")
        
        # Try to extract coordinates (if any)
        matches = extract_dms(raw_text)
        coords = []
        for match in matches:
            lat_dd, lon_dd = dms_to_dd(match[0], match[1])
            coords.append({"latitude": lat_dd, "longitude": lon_dd})
        
        notams_list.append({
            "raw": raw_text,
            "startValidity": start_time,
            "endValidity": end_time,
            "coordinates": coords
        })


# Save to JSON file
output_filename = "notams_parsed.json"

with open(output_filename, "w") as f:
    json.dump(notams_list, f, indent=2)

print(f"Saved {len(notams_list)} NOTAMs to {output_filename}")