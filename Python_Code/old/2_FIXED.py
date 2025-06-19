# Updated script with sidebar filters
# Original imports and data loading remain unchanged
import pandas as pd, geopandas as gpd, folium
from folium.plugins import FeatureGroupSubGroup, MarkerCluster
import json, glob, os, html
from datetime import datetime

# === Pilot input ===
try:
    pilot_lat = float(input("Pilot latitude [44.0]: ") or 44.0)
    pilot_lon = float(input("Pilot longitude [-79.0]: ") or -79.0)
except ValueError:
    raise SystemExit("numeric lat/lon required")
print(f"Pilot location: {pilot_lat}, {pilot_lon}")

nm_to_m = 1852
zoom_init = 8

# === Load airports ===
df = pd.read_csv("https://davidmegginson.github.io/ourairports-data/airports.csv")
df = df[df["iso_country"] == "CA"].dropna(subset=["ident", "latitude_deg", "longitude_deg"])
gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.longitude_deg, df.latitude_deg), crs="EPSG:4326")

# === Icon styles ===
ICON_STYLE = {
    "heliport":       {"icon": "helicopter", "color": "green"},
    "seaplane_base":  {"icon": "ship", "color": "cadetblue"},
    "small_airport":  {"icon": "circle", "color": "gray"},
    "medium_airport": {"icon": "plane", "color": "blue"},
    "large_airport":  {"icon": "plane", "color": "darkblue"},
    "default":        {"icon": "map-marker", "color": "lightgray"},
}

# === Base map ===
m = folium.Map(location=[pilot_lat, pilot_lon], zoom_start=zoom_init, tiles="CartoDB positron")

# === Build layers ===
province_parents, layers_dict = {}, {}
province_names = sorted(gdf["iso_region"].unique())
airport_types = sorted(gdf["type"].unique())

for prov in province_names:
    fg = folium.FeatureGroup(name=prov, show=False)
    province_parents[prov] = fg
    layers_dict[prov] = []
    fg.add_to(m)

for prov, prov_df in gdf.groupby("iso_region"):
    for atype, sub in prov_df.groupby("type"):
        child = FeatureGroupSubGroup(province_parents[prov], atype, show=False, overlay=True)
        cluster = MarkerCluster().add_to(child)
        style = ICON_STYLE.get(atype, ICON_STYLE["default"])
        for _, row in sub.iterrows():
            lat, lon = row.geometry.y, row.geometry.x
            folium.Marker(
                [lat, lon],
                tooltip=f"{row['ident']} • {row['name']}",
                popup=f"{row['ident']} – {row['name']}<br>Lat: {lat:.6f}<br>Lon: {lon:.6f}",
                icon=folium.Icon(color=style["color"], icon=style["icon"], prefix="fa")
            ).add_to(cluster)
        child.add_to(m)
        layers_dict[prov].append(child)
        layer_id = f"{prov}:{atype}"
        js = (
            '<script>' +
            'if (!window._all_layers) window._all_layers = {};' +
            'if (!window._map) window._map = ' + m.get_name() + ';' +
            'window._all_layers["' + layer_id + '"] = ' + child.get_name() + ';' +
            '</script>'
        )
        m.get_root().html.add_child(folium.Element(js))
        layers_dict[prov].append(child)

# === Pilot marker + rings ===
folium.Marker([pilot_lat, pilot_lon], tooltip="Pilot", popup="Pilot Location", icon=folium.Icon(color="purple", icon="user", prefix="fa")).add_to(m)
folium.Circle([pilot_lat, pilot_lon], radius=nm_to_m, color="red", weight=4, fill=False, popup="1 NM").add_to(m)
folium.Circle([pilot_lat, pilot_lon], radius=3*nm_to_m, color="red", weight=2, dash_array="5,5", fill=False, popup="3 NM").add_to(m)

# === NOTAM obstacles ===
notam_files = sorted(glob.glob("*_NOTAMS_*.json"))
if not notam_files:
    raise SystemExit("No NOTAM files available")
latest_file = notam_files[-1]
with open(latest_file) as f:
    notams_data = json.load(f)
obstacle_layer = folium.FeatureGroup(name="Obstacles", show=False)
for notam in notams_data:
    if "coordinates_dd" not in notam: continue
    for coord in notam["coordinates_dd"]:
        lat, lon = map(float, coord.split(","))
        safe_raw = html.escape(notam["raw"]).replace("\n", "<br>")
        popup_html = "<b>Obstacle Alert</b><br>{}".format(safe_raw)
        folium.Marker([lat, lon], tooltip="Obstacle", popup=folium.Popup(popup_html), icon=folium.Icon(color="orange", icon="exclamation-triangle", prefix="fa")).add_to(obstacle_layer)
obstacle_layer.add_to(m)

# === NOTAM obstacles ===
notam_files = sorted(glob.glob("*_NOTAMS_*.json"))
if not notam_files:
    print("No NOTAM files found in directory.")
    notams_data = []
else:
    latest_file = notam_files[-1]
    with open(latest_file) as f:
        notams_data = json.load(f)
obstacle_layer = folium.FeatureGroup(name="Obstacles", show=False)
for notam in notams_data:
    if "coordinates_dd" not in notam: continue
    for coord in notam["coordinates_dd"]:
        lat, lon = map(float, coord.split(","))
        safe_raw = html.escape(notam["raw"]).replace("\n", "<br>")
        popup_html = "<b>Obstacle Alert</b><br>{}".format(safe_raw)
        folium.Marker([lat, lon], tooltip="Obstacle", popup=folium.Popup(popup_html),
            icon=folium.Icon(color="orange", icon="exclamation-triangle", prefix="fa")
        ).add_to(obstacle_layer)
obstacle_layer.add_to(m)
js_obs = (
    '<script>' +
    'if (!window._all_layers) window._all_layers = {};' +
    'window._all_layers["NOTAMS"] = ' + obstacle_layer.get_name() + ';' +
    '</script>'
)
m.get_root().html.add_child(folium.Element(js_obs))

# === Sidebar filter ===
prov_options = ''.join('<option value="{}">{}</option>'.format(p, p) for p in province_names)
type_options = ''.join('<option value="{}">{}</option>'.format(t, t) for t in airport_types)

sidebar_html = '''
<div id="sidebar" style="position:fixed;top:10px;left:10px;z-index:9999;background:white;padding:10px;border:1px solid #ccc;max-height:90%;overflow:auto">
  <h4>Filters</h4>
  <label>Province:</label><br>
  <select id="provSelect" multiple size="5">{prov_options}</select><br><br>
  <label>Airport Types:</label><br>
  <select id="typeSelect" multiple size="5">{type_options}</select><br><br>
  <button onclick="applyFilter()">Apply Filter</button>
</div>
<script>
function applyFilter() {{
  var provs = Array.from(document.getElementById('provSelect').selectedOptions).map(o=>o.value);
  var types = Array.from(document.getElementById('typeSelect').selectedOptions).map(o=>o.value);
  var layers = window._all_layers;
  for (let id in layers) {{
    let obj = layers[id];
    if (!obj || !obj.options || !obj.options.pane) continue;
    let name = obj.options.pane;
    let [prov, type] = name.split(':');
    if (provs.includes(prov) && types.includes(type)) obj.addTo(window._map);
    else obj.remove();
  }}
}}
</script>
'''.format(prov_options=prov_options, type_options=type_options)

m.get_root().html.add_child(folium.Element(sidebar_html))

# === Export map ===
m.save("Airports_NOTAMS.html")
print("Map saved -> Airports_NOTAMS.html")