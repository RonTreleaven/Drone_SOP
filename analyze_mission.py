import os
import xml.etree.ElementTree as ET
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from datetime import datetime
import math

def get_haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
    return 2 * R * math.asin(math.sqrt(a))

def get_exif_data(image_path):
    try:
        img = Image.open(image_path)
        exif = img._getexif()
        if not exif: return None, None
        timestamp = None
        lat = None
        lon = None
        for tag, value in exif.items():
            decoded = TAGS.get(tag, tag)
            if decoded == 'DateTimeOriginal' or decoded == 'DateTime':
                try: timestamp = datetime.strptime(value, '%Y:%m:%d %H:%M:%S')
                except: pass
            if decoded == 'GPSInfo':
                gps_data = {GPSTAGS.get(t, t): value[t] for t in value}
                def get_decimal(res):
                    return float(res[0]) + (float(res[1]) / 60.0) + (float(res[2]) / 3600.0)
                if 'GPSLatitude' in gps_data and 'GPSLongitude' in gps_data:
                    lat = get_decimal(gps_data['GPSLatitude'])
                    if gps_data.get('GPSLatitudeRef', 'N') == 'S': lat = -lat
                    lon = get_decimal(gps_data['GPSLongitude'])
                    if gps_data.get('GPSLongitudeRef', 'E') == 'W': lon = -lon
        return timestamp, (lat, lon) if lat is not None else None
    except: return None, None

folder = r'G:\DJI_Mini_Flights\New folder'
wpml_path = os.path.join(folder, 'waylines.wpml')
waypoints = []
try:
    tree = ET.parse(wpml_path)
    root = tree.getroot()
    # The XML uses namespaces but also tags like <Placemark> directly or with wpml prefix
    # From inspection: xmlns="http://www.opengis.net/kml/2.2" (default) and xmlns:wpml="http://www.uav.com/wpmz/1.0.2"
    ns = {'k': 'http://www.opengis.net/kml/2.2', 'w': 'http://www.uav.com/wpmz/1.0.2'}
    for pm in root.findall('.//k:Placemark', ns):
        idx_el = pm.find('w:index', ns)
        coords_el = pm.find('.//k:coordinates', ns)
        if idx_el is not None and coords_el is not None:
            lon, lat = map(float, coords_el.text.split(',')[:2])
            waypoints.append({'idx': int(idx_el.text), 'lat': lat, 'lon': lon})
    waypoints.sort(key=lambda x: x['idx'])
except Exception as e: print(f'WPML Error: {e}')

photos = []
for f in os.listdir(folder):
    if f.lower().endswith(('.jpg', '.jpeg')):
        ts, gps = get_exif_data(os.path.join(folder, f))
        if ts: photos.append({'name': f, 'ts': ts, 'gps': gps})
photos.sort(key=lambda x: x['ts'])
valid_photos = [p for p in photos if p['gps']]

if waypoints and valid_photos:
    for p in valid_photos:
        best = min(waypoints, key=lambda w: get_haversine(p['gps'][0], p['gps'][1], w['lat'], w['lon']))
        p['wp'] = best['idx']
        p['dist'] = get_haversine(p['gps'][0], p['gps'][1], best['lat'], best['lon'])

    wp_indices = [p['wp'] for p in valid_photos]
    from collections import Counter
    unique_wps = sorted(list(set(wp_indices)))
    hc = unique_wps[0]
    for i in range(len(unique_wps)-1):
        if unique_wps[i+1] == unique_wps[i]+1: hc = unique_wps[i+1]
        else: break
    print(f'Photos: {len(valid_photos)}/{len(photos)}')
    print(f'A) Time: {valid_photos[0]["ts"]} to {valid_photos[-1]["ts"]}')
    print(f'B) WP Range: {min(wp_indices)}-{max(wp_indices)}, Freq: {Counter(wp_indices).most_common(1)[0][0]}')
    print(f'C) Contig WP: {hc}')
    print('D) Top 15 Highest WP:')
    for p in sorted(valid_photos, key=lambda x: x['wp'], reverse=True)[:15]:
        print(f" {p['name']} | {p['ts'].time()} | WP{p['wp']} | {p['dist']:.1f}m")
    cb = 0
    for p in valid_photos:
        if p['wp'] <= 3 and p['dist'] > 60: cb += 1
        else: break
    print(f'E) Before Prox: {cb}')
    print(f'F) Elapsed: {valid_photos[-1]["ts"] - valid_photos[0]["ts"]}')

if len(waypoints) > 1:
    td = sum(get_haversine(waypoints[i]['lat'], waypoints[i]['lon'], waypoints[i+1]['lat'], waypoints[i+1]['lon']) for i in range(len(waypoints)-1))
    et = td/4.0 + (len(waypoints)*2)
    print(f'Route: {td:.0f}m | Est Time: {et/60:.1f}m | Battery: {"OK" if et < 1200 else "Tight"}')
    print(f'Restart: {max(wp_indices)+1 if valid_photos else 0}')
    print(f'Split: {waypoints[len(waypoints)//2]["idx"]}')
elif not waypoints:
    print('No waypoints found in WPML.')
