# Canadian Aerodromes Map (full version with filters + working pilot widget)
# All-ASCII source
import pandas as pd, geopandas as gpd, folium
from folium.plugins import FeatureGroupSubGroup, GroupedLayerControl, MarkerCluster

# ===== 0. pilot input =====
try:
    pilot_lat = float(input("Pilot latitude (decimal degrees): ").strip())
    pilot_lon = float(input("Pilot longitude (decimal degrees): ").strip())
except ValueError:
    raise SystemExit("numeric lat/lon required")

nm_to_m   = 1852
zoom_init = 10

# ===== 1. load airport csv =====
df = pd.read_csv("ca-airports.csv")
df.rename(columns={"ident": "icao"}, inplace=True)
df["latitude_deg"]  = pd.to_numeric(df["latitude_deg"],  errors="coerce")
df["longitude_deg"] = pd.to_numeric(df["longitude_deg"], errors="coerce")
df.dropna(subset=["icao", "latitude_deg", "longitude_deg"], inplace=True)
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
m = folium.Map(location=[pilot_lat, pilot_lon], zoom_start=zoom_init,
               tiles="CartoDB positron")

# ===== 4. province/type layers =====
province_parents, layers_dict = {}, {}
for prov in sorted(gdf["region_name"].unique(), key=lambda x:(x!="Ontario",x)):
    fg = folium.FeatureGroup(name=prov).add_to(m)
    province_parents[prov] = fg
    layers_dict[prov] = []

for prov, prov_df in gdf.groupby("region_name"):
    for atype, sub in prov_df.groupby("type"):
        child = FeatureGroupSubGroup(province_parents[prov], atype,
                                     show=False, overlay=True)
        cluster = MarkerCluster().add_to(child)
        style   = ICON_STYLE.get(atype, ICON_STYLE["default"])
        for _, row in sub.iterrows():
            lat, lon = row.geometry.y, row.geometry.x
            folium.Marker([lat, lon],
                tooltip=f"{row['icao']} • {row['name']}",
                popup=f"{row['icao']} – {row['name']}<br>Lat: {lat:.6f}<br>Lon: {lon:.6f}",
                icon=folium.Icon(color=style["color"], icon=style["icon"], prefix="fa")
            ).add_to(cluster)
        child.add_to(m)
        layers_dict[prov].append(child)

# ===== 5. pilot marker + rings =====
pm = folium.Marker([pilot_lat, pilot_lon],
        tooltip="Pilot location",
        popup=f"Pilot<br>Lat: {pilot_lat:.6f}<br>Lon: {pilot_lon:.6f}",
        icon=folium.Icon(color="red", icon="user", prefix="fa")).add_to(m)
pm_js = pm.get_name()

c1 = folium.Circle([pilot_lat,pilot_lon], radius=nm_to_m,
        color="red", weight=2, fill=False,
        popup="1 NM (1.9 km) radius").add_to(m)
c1_js = c1.get_name()
c3 = folium.Circle([pilot_lat,pilot_lon], radius=3*nm_to_m,
        color="red", weight=1, dash_array="5,5",
        fill=False,
        popup="3 NM (5.6 km) radius").add_to(m)
c3_js = c3.get_name()

# ===== 6. legend =====
GroupedLayerControl(groups=layers_dict, exclusive_groups=[], collapsed=False).add_to(m)
m.get_root().html.add_child(folium.Element(
    '<style>.leaflet-control-layers-list{max-height:300px;overflow-y:auto;}\
.pilot-input{z-index:1200;}</style>'
))

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

# ===== 8. sidebar =====
sidebar_html = """
<style>
#sidebar {
  position: absolute;
  top: 60px;
  left: 10px;
  width: 240px;
  background: white;
  border-radius: 6px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.2);
  z-index: 1202;
  padding: 10px;
  font-size: 15px;
  max-height: 80vh;
  overflow-y: auto;
}
#sidebar h3 { margin: 0 0 10px 0; font-size: 18px; }
.sidebar-group { margin-bottom: 10px; }
.sidebar-group label { font-weight: bold; cursor: pointer; display: block; }
.sidebar-types { margin-left: 15px; display: none; }
.sidebar-group.open .sidebar-types { display: block; }
</style>
<div id="sidebar">
  <h3>Filter Airports</h3>
  <!-- Province/Type checkboxes will be injected here -->
  <div id="sidebar-content"></div>
</div>
"""
m.get_root().html.add_child(folium.Element(sidebar_html))

# ===== 9. save =====
m.save("CA_Airports_Final_V1.html")
print("Map saved as -> CA_Airports_Final_V1.html.html")
