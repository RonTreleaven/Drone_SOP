# Canadian Aerodromes Map (full version with filters + working pilot widget)
# All-ASCII source
import pandas as pd, geopandas as gpd, folium
from folium.plugins import FeatureGroupSubGroup, GroupedLayerControl, MarkerCluster
import json
from datetime import datetime
import glob
import os
import html 
from collections import defaultdict

# ===== 0. pilot input =====
try:
    pilot_lat_str = input("Pilot latitude (decimal degrees) [44.0]: ").strip()
    pilot_lon_str = input("Pilot longitude (decimal degrees) [-79.0]: ").strip()
    pilot_lat = float(pilot_lat_str) if pilot_lat_str else 44.0
    pilot_lon = float(pilot_lon_str) if pilot_lon_str else -79.0
except ValueError:
    raise SystemExit("numeric lat/lon required")
print(f"Pilot location set to: {pilot_lat:.6f}, {pilot_lon:.6f}")

nm_to_m   = 1852 #nautical mile to meters
zoom_init = 8  # initial zoom level for the map

# ===== 1. load airport csv =====
df = pd.read_csv("https://davidmegginson.github.io/ourairports-data/airports.csv")
df = df[df["iso_country"] == "CA"].copy()  # Only Canadian aerodromes
df.dropna(subset=["ident", "latitude_deg", "longitude_deg"], inplace=True)
gdf = gpd.GeoDataFrame(df,
        geometry=gpd.points_from_xy(df.longitude_deg, df.latitude_deg),
        crs="EPSG:4326")

# ===== 2. icon lookup =====
ICON_STYLE = {
    "heliport":       {"icon":"helicopter","color":"green"},
    "seaplane_base":  {"icon":"ship",      "color":"cadetblue"},
    "small_airport":  {"icon":"circle",    "color":"gray"},
    "medium_airport": {"icon":"plane",     "color":"blue"},
    "large_airport":  {"icon":"plane",     "color":"darkblue"},
    "default":        {"icon":"map-marker","color":"lightgray"},
}

# ===== 3. base map =====
m = folium.Map(location=[pilot_lat, pilot_lon], zoom_start=zoom_init, tiles="CartoDB positron")
 



# ===== 4. province/type layers =====
province_parents, layers_dict = {}, {}
province_names = sorted(gdf["iso_region"].unique())
airport_types = sorted(gdf["type"].unique())

for prov in province_names:
    fg = folium.FeatureGroup(name=prov, show=False).add_to(m)
    province_parents[prov] = fg
    layers_dict[prov] = []

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
        child.add_to(m)  # <-- This is critical!
        layers_dict[prov].append(child)

GroupedLayerControl(
    groups=layers_dict,
    exclusive_groups=[],  # or province_names for radio buttons
    collapsed=False
).add_to(m)

# ===== 5. pilot marker + rings =====
pm = folium.Marker([pilot_lat, pilot_lon],
        tooltip="Pilot location",
        popup=f"Pilot<br>Lat: {pilot_lat:.6f}<br>Lon: {pilot_lon:.6f}",
        icon=folium.Icon(color="purple", icon="user", prefix="fa")).add_to(m)
pm_js = pm.get_name()

c1 = folium.Circle([pilot_lat,pilot_lon], radius=nm_to_m,
        color="red", weight=4, fill=False,
        popup="1 NM (1.9 km) radius").add_to(m)
c1_js = c1.get_name()
c3 = folium.Circle([pilot_lat,pilot_lon], radius=3*nm_to_m,
        color="red", weight=2, dash_array="5,5",
        fill=False,
        popup="3 NM (5.6 km) radius").add_to(m)
c3_js = c3.get_name()

# ===== 5a. Obstacles Layer =====

# Find all NOTAM JSON files in the current directory
notam_files = sorted(glob.glob("*_NOTAMS_*.json"))

if not notam_files:
    print("No NOTAM files found in the current directory.")
    choice = input("Enter 'R' to refresh NOTAM data, or any other key to exit: ").strip().upper()
    if choice == 'R':
        os.system("python FIR_NOTAMS_Maps_v1.0.py")
    raise SystemExit("No NOTAM files available. Exiting.")

print("Available NOTAM files:")
for idx, fname in enumerate(notam_files, 1):
    print(f"{idx}: {fname}")

# Prompt user to pick a file or refresh
while True:
    file_choice = input(f"Select NOTAM file [1-{len(notam_files)}] or 'R' to refresh: ").strip()
    if file_choice.upper() == 'R':
        os.system("python FIR_NOTAMS_Maps_v1.0.py")
        raise SystemExit("Refreshed NOTAM data. Please rerun this script.")
    try:
        file_choice = int(file_choice)
        if 1 <= file_choice <= len(notam_files):
            latest_file = notam_files[file_choice - 1]
            break
        else:
            print("Invalid selection.")
    except ValueError:
        print("Please enter a number or 'R'.")

with open(latest_file, "r") as f:
    notams_data = json.load(f)

obstacle_layer = folium.FeatureGroup(name="Obstacles", show=False)
for notam in notams_data:
    # Skip if coordinates_dd is missing or empty
    if "coordinates_dd" not in notam or not notam["coordinates_dd"]:
        continue
    # Skip if raw field is missing or empty
    if "raw" not in notam or not notam["raw"]:
        continue
    for coord in notam["coordinates_dd"]:
        lat, lon = map(float, coord.split(","))
        safe_raw = html.escape(notam['raw']).replace('\n', '<br>')
        popup_html = f"<b>Obstacle Alert</b><br>{safe_raw}"
        popup = folium.Popup(popup_html, max_width=400, parse_html=True)
        folium.Marker(
            [lat, lon],
            tooltip="Obstacle",
            popup=popup,
            icon=folium.Icon(color="orange", icon="exclamation-triangle", prefix="fa")
        ).add_to(obstacle_layer)
obstacle_layer.add_to(m)
layers_dict["Obstacles"] = [obstacle_layer]
# 
# ===== 6. legend =====
# GroupedLayerControl(groups=layers_dict, exclusive_groups=[], collapsed=False).add_to(m)
# m.get_root().html.add_child(folium.Element(
    # '<style>.leaflet-control-layers-list{max-height:300px;overflow-y:auto;}\
# .pilot-input{z-index:1200;}</style>'
# ))

# ===== 7. widget injected after load =====
widget_js = f"""
<script>
window.onload = function() {{
  var map    = {m.get_name()};
  var marker = {pm_js};
  var c1     = {c1_js};
  var c3     = {c3_js};

  marker.dragging.enable();
  marker.on('dragend', function(e) {{
      var ll = e.target.getLatLng();
      c1.setLatLng(ll); c3.setLatLng(ll);
      marker.setPopupContent("Pilot<br>Lat: "+ll.lat.toFixed(6)+"<br>Lon: "+ll.lng.toFixed(6));
  }});

  var ctl = L.control({{position:'bottomleft'}});
  ctl.onAdd = function() {{
      var d=L.DomUtil.create('div','pilot-input');
      L.DomEvent.disableClickPropagation(d);
      d.style.background='white'; d.style.padding='6px'; d.style.fontSize='14px';
      d.style.boxShadow='0 0 4px rgba(0,0,0,0.3)';
      d.innerHTML = 'Lat <input id="pLat" size="9"> Lon <input id="pLon" size="9"> \
<button id="upd">Update</button>';
      return d;
  }};
  ctl.addTo(map);

  document.getElementById('upd').onclick = function() {{
      var lat=parseFloat(document.getElementById('pLat').value);
      var lon=parseFloat(document.getElementById('pLon').value);
      if(isNaN(lat)||isNaN(lon)) {{ alert("Enter numeric lat & lon"); return; }}
      var ll=L.latLng(lat,lon);
      marker.setLatLng(ll).openPopup();
      c1.setLatLng(ll); c3.setLatLng(ll);
      map.setView(ll, {zoom_init});
  }};
}};
</script>
"""
m.get_root().html.add_child(folium.Element(widget_js))

# ===== 8. save =====
m.save("GPT_Airports_NOTAMS.html")
print("Map saved -> GPT_Airports_NOTAMS.html")
