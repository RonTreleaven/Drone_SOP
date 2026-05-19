import json
import math
import sys

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def is_point_in_poly(x, y, poly):
    num = len(poly)
    j = num - 1
    res = False
    for i in range(num):
        if (poly[i][1] > y) != (poly[j][1] > y):
            if x < (poly[j][0] - poly[i][0]) * (y - poly[i][1]) / (poly[j][1] - poly[i][1]) + poly[i][0]:
                res = not res
        j = i
    return res

def get_centroid(geometry):
    num_pts = 0
    t_lat = 0
    t_lon = 0
    if geometry['type'] == 'Polygon':
        for ring in geometry['coordinates']:
            for pt in ring:
                t_lon += pt[0]
                t_lat += pt[1]
                num_pts += 1
    elif geometry['type'] == 'MultiPolygon':
        for poly in geometry['coordinates']:
            for ring in poly:
                for pt in ring:
                    t_lon += pt[0]
                    t_lat += pt[1]
                    num_pts += 1
    else: return None
    if num_pts == 0: return None
    return t_lat/num_pts, t_lon/num_pts

path = 'data/airspace/ca_asp_restricted.geojson'
point_lat, point_lon = 43.868782, -78.717507

with open(path, 'r', encoding='utf-8') as f:
    data = json.load(f)

filtered = []
for f in data['features']:
    p = f.get('properties', {})
    if p.get('type') == 1 or p.get('icaoClass') == 8:
        filtered.append(f)

matches = []
for f in filtered:
    geom = f['geometry']
    in_poly = False
    if geom['type'] == 'Polygon':
        if is_point_in_poly(point_lon, point_lat, geom['coordinates'][0]): in_poly = True
    elif geom['type'] == 'MultiPolygon':
        for poly in geom['coordinates']:
            if is_point_in_poly(point_lon, point_lat, poly[0]):
                in_poly = True; break
    if in_poly: matches.append(f)

print('--- Matches ---')
for m in matches:
    p = m['properties']
    print('ID: {}, Name: {}, Type: {}, ICAO: {}'.format(p.get('id'), p.get('name'), p.get('type'), p.get('icaoClass')))

distances = []
for f in filtered:
    c = get_centroid(f['geometry'])
    if c:
        d = haversine(point_lat, point_lon, c[0], c[1])
        distances.append((d, f))
distances.sort(key=lambda x: x[0])

print('\n--- Nearest 10 Restricted ---')
for d, f in distances[:10]:
    p = f['properties']
    print('Dist: {:.2f}m, ID: {}, Name: {}, Type: {}, ICAO: {}'.format(d, p.get('id'), p.get('name'), p.get('type'), p.get('icaoClass')))
