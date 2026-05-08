import os
import math
import xml.etree.ElementTree as ET
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from datetime import datetime

def get_exif_data(image):
    exif_data = {}
    info = image._getexif()
    if info:
        for tag, value in info.items():
            decoded = TAGS.get(tag, tag)
            if decoded == "GPSInfo":
                gps_data = {}
                for t in value:
                    sub_decoded = GPSTAGS.get(t, t)
                    gps_data[sub_decoded] = value[t]
                exif_data[decoded] = gps_data
            else:
                exif_data[decoded] = value
    return exif_data

def get_lat_lon(gps_info):
    def convert_to_degrees(value):
        d = float(value[0])
        m = float(value[1])
        s = float(value[2])
        return d + (m / 60.0) + (s / 3600.0)

    try:
        lat = convert_to_degrees(gps_info['GPSLatitude'])
        if gps_info['GPSLatitudeRef'] != 'N': lat = -lat
        lon = convert_to_degrees(gps_info['GPSLongitude'])
        if gps_info['GPSLongitudeRef'] != 'E': lon = -lon
        return lat, lon
    except:
        return None, None

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
    return 2 * R * math.asin(math.sqrt(a))

folder_path = r"G:\DJI_Mini_Flights\New folder"
wpml_path = os.path.join(folder_path, "waylines.wpml")

# Parse WPML
tree = ET.parse(wpml_path)
root = tree.getroot()
namespaces = {'wpml': 'http://www.uav.com/wpmz/1.0.2', 'kml': 'http://www.opengis.net/kml/2.2'}
waypoints = []
for placemark in root.findall('.//kml:Placemark', namespaces):
    idx = int(placemark.find('wpml:index', namespaces).text)
    coord_txt = placemark.find('.//kml:coordinates', namespaces).text
    lon, lat = map(float, coord_txt.split(','))
    waypoints.append({'index': idx, 'lat': lat, 'lon': lon})
waypoints.sort(key=lambda x: x['index'])

# Process Images
images_metadata = []
for filename in os.listdir(folder_path):
    if filename.lower().endswith(('.jpg', '.jpeg')):
        path = os.path.join(folder_path, filename)
        try:
            with Image.open(path) as img:
                exif = get_exif_data(img)
                lat, lon = get_lat_lon(exif.get('GPSInfo', {}))
                dt_str = exif.get('DateTimeOriginal') or exif.get('DateTime')
                dt = datetime.strptime(dt_str, '%Y:%m:%d %H:%M:%S') if dt_str else None
                if lat is not None and dt:
                    images_metadata.append({'filename': filename, 'time': dt, 'lat': lat, 'lon': lon})
        except:
            continue
images_metadata.sort(key=lambda x: x['time'])

# Compute nearest waypoint
results = []
for img in images_metadata:
    min_dist = float('inf')
    nearest_wp = -1
    for wp in waypoints:
        d = haversine(img['lat'], img['lon'], wp['lat'], wp['lon'])
        if d < min_dist:
            min_dist = d
            nearest_wp = wp['index']
    img['nearest_wp'] = nearest_wp
    img['dist'] = min_dist
    results.append(img)

# Stats for thresholds
thresholds = [20, 30, 40, 60]
print("--- Stats by Threshold ---")
for t in thresholds:
    max_wp = -1
    contiguous_up_to = -1
    wps_in_threshold = sorted(list(set(r['nearest_wp'] for r in results if r['dist'] <= t)))
    if wps_in_threshold:
        max_wp = max(wps_in_threshold)
        expected = 0
        for wp_idx in wps_in_threshold:
            if wp_idx == expected:
                contiguous_up_to = wp_idx
                expected += 1
            elif wp_idx > expected:
                break
    print(f"Threshold {t}m: Max WP reached: {max_wp}, Highest contiguous: {contiguous_up_to}")

# Progression analysis (Rolling Median)
import statistics
window_size = 7
rolling_medians = []
for i in range(len(results)):
    window = [r['nearest_wp'] for r in results[max(0, i - window_size // 2) : min(len(results), i + window_size // 2 + 1)]]
    rolling_medians.append(statistics.median(window))

last_sustained_idx = 0
last_sustained_wp = rolling_medians[0]
for i in range(1, len(rolling_medians)):
    # If the median increases, update potential "last sustained" if no significant drops follow
    # Or more simply: find the point after which the median mostly decreases or stays same
    pass

# Refined sustained forward progression:
# Last index where rolling_medians[i] > max(rolling_medians[:i]) and no significantly higher value (e.g. +5) appears much later?
# Let's keep it simple: index of the maximum rolling median value, and then the last time it was increasing to reach that or near that.
max_med = max(rolling_medians)
last_time_at_max = None
for i in range(len(rolling_medians)):
    if rolling_medians[i] >= max_med - 1: # allowing small fluctuations
        last_time_at_max = results[i]['time']
        sustained_wp = int(rolling_medians[i])

print(f"\nLast sustained forward progression detected around: {last_time_at_max} (Approx WP {sustained_wp})")

# Suggestions
c_up_30 = -1
wps_30 = sorted(list(set(r['nearest_wp'] for r in results if r['dist'] <= 30)))
expected = 0
for wp_idx in wps_30:
    if wp_idx == expected:
        c_up_30 = wp_idx
        expected += 1
    elif wp_idx > expected:
        break
max_40 = max([r['nearest_wp'] for r in results if r['dist'] <= 40] or [-1])

print(f"\n--- Restart Suggestions ---")
print(f"Conservative Restart (Contiguous @30m - 1): {max(0, c_up_30 - 1)}")
print(f"Aggressive Restart (Max @40m + 1): {max_40 + 1}")

# Table of last 25 photos
print(f"\n--- Last 25 Photos ---")
print(f"{'Filename':<25} | {'Time':<20} | {'WP':<5} | {'Dist(m)':<8}")
for r in results[-25:]:
    print(f"{r['filename']:<25} | {r['time'].strftime('%H:%M:%S'):<20} | {r['nearest_wp']:<5} | {r['dist']:<8.2f}")

