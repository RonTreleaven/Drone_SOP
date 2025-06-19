import requests
import json
import re
from datetime import datetime

# Define FIRs and their ICAO codes

firs = {
    "1": ("Edmonton", "CZEG"),
    "2": ("Gander", "CZQX"),
    "3": ("Moncton", "CZQM"),
    "4": ("Montreal", "CZUL"),
    "5": ("Toronto", "CZYZ"),
    "6": ("Vancouver", "CZVR"),
    "7": ("Winnipeg", "CZWG")
}

# Display FIR options
print("Select a FIR by number or enter an ICAO code (e.g., CYOO for Oshawa Executive Airport):")
for num, (name, icao_code) in firs.items():
    print(f"{num}: {name} ({icao_code})")

# Get user input
user_input = input("Enter the number of the FIR or an ICAO code: ").strip().upper()

if user_input in firs:
    icao = firs[user_input][1]
    print(f"Selected FIR: {firs[user_input][0]} ({icao})")
else:
    icao = user_input
    print(f"No FIR selected. Using ICAO code: {icao}")

# Define the API endpoint using the selected ICAO code
url = f"https://plan.navcanada.ca/weather/api/alpha/?site={icao}&alpha=notam&notam_choice=default"

# Fetch the data with error handling
response = requests.get(url)
print(f"HTTP status code: {response.status_code}")  # Always print the status code

if response.status_code != 200:
    print(f"Failed to fetch data for ICAO code '{icao}'.")
    print(f"Response content: {response.text}")  # Print the response content for debugging
    exit(1)

data = response.json()

# Check for error or empty data
if not data.get("data"):
    print(f"No NOTAMs found or invalid ICAO code '{icao}'.")
    # Optionally print the full response for debugging
    print("API response:", data)
    print(" JSON file will not be created.")
    exit(1)

# Count total NOTAMs received
total_notams = len(data.get("data", []))
print(f"Total NOTAMs received from API: {total_notams}")

# Keywords to filter for obstacle-type events
KEYWORDS = ["PARAJUMP", "PARACHUTE", "ADVISORY", "CRANE", "GPS", "RESTRICTED", "OBST", "TFR", "Danger"]

# Helper function to extract DMS coordinates from text
def extract_dms(text):
    pattern = r'(\d{6}[NS])\s*(\d{7}[EW])'
    matches = re.findall(pattern, text)
    return matches

# Convert DMS to Decimal Degrees
def dms_to_dd(dms_lat, dms_lon):
    lat_deg = int(dms_lat[:2])
    lat_min = int(dms_lat[2:4])
    lat_sec = int(dms_lat[4:6])
    lat_dir = dms_lat[-1]
    lat_dd = lat_deg + lat_min / 60 + lat_sec / 3600
    if lat_dir == 'S':
        lat_dd = -lat_dd

    lon_deg = int(dms_lon[:3])
    lon_min = int(dms_lon[3:5])
    lon_sec = int(dms_lon[5:7])
    lon_dir = dms_lon[-1]
    lon_dd = lon_deg + lon_min / 60 + lon_sec / 3600
    if lon_dir == 'W':
        lon_dd = -lon_dd

    return round(lat_dd, 6), round(lon_dd, 6)

# Process NOTAMs
notams_list = []

for item in data.get("data", []):
    raw_text = json.loads(item.get("text", "{}")).get("raw", "")
    if raw_text and any(keyword in raw_text.upper() for keyword in KEYWORDS):
        start_time = item.get("startValidity")
        end_time = item.get("endValidity")
        
        matches = extract_dms(raw_text)
        coords_dd = []
        for match in matches:
            lat_dd, lon_dd = dms_to_dd(match[0], match[1])
            coords_dd.append(f"{lat_dd:.6f}, {lon_dd:.6f}")

        notams_list.append({
            "raw": raw_text,
            "startValidity": start_time,
            "endValidity": end_time,
            "coordinates_dd": coords_dd
        })

# Save to JSON file
date_str = datetime.now().strftime("%d_%m_%y")
output_filename = f"{date_str}_NOTAMS_{icao}.json"
log_filename = f"{date_str}_NOTAMS_{icao}_log.txt"

with open(output_filename, "w") as f:
    json.dump(notams_list, f, indent=2)

# Prepare log content

# log_lines = [
#     f"FIR/ICAO: {icao}",
#     f"Total NOTAMs received: {total_notams}",
#     f"Filtered NOTAMs saved to: {output_filename}",
#     f"Filtered Saved Count:
#     "Filtered NOTAMs:",
log_lines = [
    f"FIR/ICAO: {icao}",
    f"Total NOTAMs received from API: {total_notams}",
    f"Saved {len(notams_list)} filtered NOTAMs to {output_filename}"
]

with open(log_filename, "w") as logf:
    for line in log_lines:
        print(line)
        logf.write(line + "\n")
        

print(f"Total NOTAMs received: {total_notams}")
print(f"Saved {len(notams_list)} filtered NOTAMs to {output_filename}")
