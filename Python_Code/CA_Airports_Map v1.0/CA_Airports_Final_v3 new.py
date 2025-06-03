# Canadian Aerodromes Map (full version with filters + working pilot widget)
# All-ASCII source
###  May 31, 2025 updates

import pandas as pd, geopandas as gpd, folium
from folium.plugins import FeatureGroupSubGroup, GroupedLayerControl, MarkerCluster
import json
from geopy.distance import geodesic
import os

# ===== 0. pilot input with memory =====
pilot_file = "last_pilot_location.json"
default_lat, default_lon = "", ""

if os.path.exists(pilot_file):
    try:
        with open(pilot_file, "r") as f:
            data = json.load(f)
            default_lat = str(data.get("lat", ""))
            default_lon = str(data.get("lon", ""))
    except Exception:
        pass

def prompt_with_default(prompt, default):
    if default:
        val = input(f"{prompt} [{default}]: ").strip()
        return val if val else default
    else:
        return input(f"{prompt}: ").strip()

while True:
    try:
        pilot_lat = float(prompt_with_default("Pilot latitude (decimal degrees)", default_lat))
        pilot_lon = float(prompt_with_default("Pilot longitude (decimal degrees)", default_lon))
        break
    except ValueError:
        print("DD lat/lon input required")

# Save for next time
with open(pilot_file, "w") as f:
    json.dump({"lat": pilot_lat, "lon": pilot_lon}, f)

nm_to_m   = 1852
zoom_init = 11

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
##  ToDo: the "Closed" type icon or we just filter out  "Closed" airports?
ICON_STYLE = {
    "heliport":       {"icon":"helicopter","color":"green"},
    "seaplane_base":  {"icon":"ship",      "color":"cadetblue"},
    "small_airport":  {"icon":"circle",    "color":"gray"},
    "medium_airport": {"icon":"plane",     "color":"blue"},
    "large_airport":  {"icon":"plane",     "color":"darkblue"},
    "default":        {"icon":"map-marker","color":"lightgray"},
}

# ===== 3. base map =====
m = folium.Map(location=[pilot_lat, pilot_lon], zoom_start=zoom_init, tiles=None)
folium.TileLayer('CartoDB positron', name='CartoDB positron', control=False).add_to(m)

# ===== 4. type layers (one per type) =====
type_groups = {}
type_group_js = {}
for atype in sorted(gdf['type'].unique()):
    fg = folium.FeatureGroup(name=atype, show=True)
    fg.add_to(m)
    type_groups[atype] = fg
    type_group_js[atype] = fg.get_name()

import json
type_group_js_json = json.dumps(type_group_js)

# ===== 5. function to add markers for a province =====
def add_province_markers(province):
    # Clear all type groups
    for fg in type_groups.values():
        fg._children.clear()
    # Add markers for the selected province within 10 NM of pilot
    prov_df = gdf[gdf['region_name'] == province]
    for atype, sub in prov_df.groupby("type"):
        fg = type_groups[atype]
        for _, row in sub.iterrows():
            lat, lon = row.geometry.y, row.geometry.x
            # Calculate distance from pilot
            dist_m = geodesic((pilot_lat, pilot_lon), (lat, lon)).meters
            if dist_m <= 18520:  # 10 NM in meters
                folium.Marker(
                    [lat, lon],
                    tooltip=f"{row['icao']} • {row['name']}",
                    popup=f"{row['icao']} – {row['name']}<br>Lat: {lat:.6f}<br>Lon: {lon:.6f}<br>Distance: {dist_m/1852:.2f} NM",
                    icon=folium.Icon(color=ICON_STYLE.get(atype, ICON_STYLE["default"])["color"],
                                     icon=ICON_STYLE.get(atype, ICON_STYLE["default"])["icon"], prefix="fa")
                ).add_to(fg)

# ===== 6. initial province =====
default_province = sorted(gdf['region_name'].unique(), key=lambda x: (x != "Ontario", x))[0]
add_province_markers(default_province)

# ===== 7. LayerControl for types only =====
folium.LayerControl(collapsed=False).add_to(m)

# ===== 8. Province selector widget =====
# province_widget = f"""
# <script>
# window.addEventListener('load', function() {{\

#     var selDiv = document.createElement('div');
#     selDiv.style.position = 'absolute';
#     selDiv.style.top = '10px';
#     selDiv.style.left = '50px';
#     selDiv.style.zIndex = 1200;
#     selDiv.style.background = 'white';
#     selDiv.style.padding = '6px';
#     selDiv.style.boxShadow = '0 0 4px rgba(0,0,0,0.3)';
#     selDiv.innerHTML = `
#         <label for="provSel">Province:</label>
#         <select id="provSel">{province_options}</select>
#     `;
#     document.body.appendChild(selDiv);

#     document.getElementById('provSel').addEventListener('change', function(e) {{
#         // Reload the page with the selected province as a query param, or
#         // (advanced) use AJAX or a JS function to update markers dynamically.
#         alert('To fully implement dynamic province switching, you would need to use a backend or advanced JS to update markers. For now, reload with the new province.');
#     }});
# }});
# </script>
# """
# m.get_root().html.add_child(folium.Element(province_widget))

# ===== 9. Layer control title =====
# <script>
# window.addEventListener('load', function() {
#     var controls = document.getElementsByClassName('leaflet-control-layers-list');
#     if (controls.length > 0) {
#         var title = document.createElement('div');
#         title.innerHTML = "<b>Airport Type</b>";
#         title.style.padding = "4px 8px";
#         controls[0].insertBefore(title, controls[0].firstChild);
#     }
# });
# </script>
# """
# m.get_root().html.add_child(folium.Element(layercontrol_title))

# Add pilot marker and radius
pilot_marker = folium.Marker(
    [pilot_lat, pilot_lon],
    tooltip="Pilot Location",
    popup=f"Pilot<br>Lat: {pilot_lat:.6f}<br>Lon: {pilot_lon:.6f}",
    icon=folium.Icon(color="red", icon="user", prefix="fa")
).add_to(m)
pm_js = pilot_marker.get_name()

c1 = folium.Circle([pilot_lat, pilot_lon], radius=nm_to_m,
        color="red", weight=2, fill=False,
        popup="1 NM (1.9 km) radius").add_to(m)
c1_js = c1.get_name()
c3 = folium.Circle([pilot_lat, pilot_lon], radius=3*nm_to_m,
        color="red", weight=1, dash_array="5,5",
        fill=False,
        popup="3 NM (5.6 km) radius").add_to(m)
c3_js = c3.get_name()

# ===== 10. Inject pilot widget JS BEFORE saving =====
widget_js = f"""
<script>
window.onload = function() {{
  var map    = {m.get_name()};
  var marker = {pm_js};
  var c1     = {c1_js};
  var c3     = {c3_js};

  marker.dragging.enable();
  marker.on('drag', function(e) {{
      var ll = e.target.getLatLng();
      c1.setLatLng(ll); c3.setLatLng(ll);
      document.getElementById('pLat').value = ll.lat.toFixed(6);
      document.getElementById('pLon').value = ll.lng.toFixed(6);
  }});
  marker.on('dragend', function(e) {{
      var ll = e.target.getLatLng();
      c1.setLatLng(ll); c3.setLatLng(ll);
      marker.setPopupContent("Pilot<br>Lat: "+ll.lat.toFixed(6)+"<br>Lon: "+ll.lng.toFixed(6));
      document.getElementById('pLat').value = ll.lat.toFixed(6);
      document.getElementById('pLon').value = ll.lng.toFixed(6);
  }});

  var ctl = L.control({{position:'bottomleft'}});
  ctl.onAdd = function() {{
      var d=L.DomUtil.create('div','pilot-input');
      L.DomEvent.disableClickPropagation(d);
      d.style.background='white'; d.style.padding='6px'; d.style.fontSize='14px';
      d.style.boxShadow='0 0 4px rgba(0,0,0,0.3)';
      d.innerHTML = 'Lat <input id="pLat" size="9" value="'+marker.getLatLng().lat.toFixed(6)+'"> Lon <input id="pLon" size="9" value="'+marker.getLatLng().lng.toFixed(6)+'"> \
<button id="upd">Update</button>';
      return d;
  }};
  ctl.addTo(map);

  document.getElementById('upd').onclick = function() {{
      var lat = document.getElementById('pLat').value;
      var lon = document.getElementById('pLon').value;
      alert("To update the map, re-run the Python script and enter:\\nLat: " + lat + "\\nLon: " + lon);
  }};
</script>
"""

# ===== Province and type options for sidebar =====
province_list = sorted(gdf['region_name'].unique())
province_options = "".join([f'<option value="{p}">{p}</option>' for p in province_list])

type_list = sorted(gdf['type'].unique())
type_options = "".join([f'<option value="{t}">{t}</option>' for t in type_list])

# ===== 10b. Inject sidebar controls JS =====
sidebar_js = f"""
<script>
window.addEventListener('load', function() {{
    // Sidebar container
    var sidebar = document.createElement('div');
    sidebar.id = "customSidebar";
    sidebar.style.position = "absolute";
    sidebar.style.top = "20px";
    sidebar.style.right = "20px";
    sidebar.style.left = "auto";
    sidebar.style.width = "260px";
    sidebar.style.background = "white";
    sidebar.style.padding = "16px";
    sidebar.style.boxShadow = "0 0 8px rgba(0,0,0,0.2)";
    sidebar.style.zIndex = 1200;
    sidebar.style.borderRadius = "8px";
    sidebar.style.transition = "right 0.3s";
    sidebar.style.fontSize = "15px";
    sidebar.style.cursor = "move";

    // Sidebar content
    sidebar.innerHTML = `
        <div id="sidebarHeader" style="display:flex;justify-content:space-between;align-items:center;cursor:move;">
            <b>Controls</b>
            <button id="hideSidebarBtn" style="font-size:16px;padding:2px 8px;">&times;</button>
        </div>
        <hr>
        <label for="provSel"><b>Province:</b></label>
        <select id="provSel" style="width:100%;margin-bottom:12px;">{province_options}</select>
        <label for="typeSel"><b>Airport Types:</b></label>
        <select id="typeSel" multiple size="6" style="width:100%;margin-bottom:12px;">
            {type_options}
        </select>
        <button id="clearTypesBtn" style="width:100%;margin-bottom:8px;">Clear All Types</button>
        <button id="selectAllTypesBtn" style="width:100%;margin-bottom:8px;">Select All Types</button>
    `;

    document.body.appendChild(sidebar);

    // Attach event handlers for type buttons
    function attachTypeHandlers() {{
        var clearBtn = document.getElementById('clearTypesBtn');
        var selectBtn = document.getElementById('selectAllTypesBtn');
        var typeSel = document.getElementById('typeSel');
        if (clearBtn && typeSel) {{
            clearBtn.onclick = function() {{
                for (var i=0; i<typeSel.options.length; i++) {{
                    typeSel.options[i].selected = false;
                }}
            }};
        }}
        if (selectBtn && typeSel) {{
            selectBtn.onclick = function() {{
                for (var i=0; i<typeSel.options.length; i++) {{
                    typeSel.options[i].selected = true;
                }}
            }};
        }}
    }}

    attachTypeHandlers();

    // Toggle button (to show sidebar)
    var toggleBtn = document.createElement('button');
    toggleBtn.id = "showSidebarBtn";
    toggleBtn.innerHTML = "☰ Controls";
    toggleBtn.style.position = "absolute";
    toggleBtn.style.bottom = "70px";
    toggleBtn.style.left = "20px";
    toggleBtn.style.right = "auto";
    toggleBtn.style.zIndex = 1201;
    toggleBtn.style.padding = "6px 14px";
    toggleBtn.style.background = "#fff";
    toggleBtn.style.border = "1px solid #888";
    toggleBtn.style.borderRadius = "6px";
    toggleBtn.style.cursor = "pointer";
    toggleBtn.style.display = "none";
    document.body.appendChild(toggleBtn);

    // Hide sidebar
    document.getElementById('hideSidebarBtn').onclick = function() {{
        sidebar.style.transition = "right 0.3s, left 0.3s, top 0.3s";
        sidebar.style.right = "-300px";
        sidebar.style.left = "auto";
        toggleBtn.style.display = "block";
    }};
    // Show sidebar
    toggleBtn.onclick = function() {{
        sidebar.style.transition = "right 0.3s, left 0.3s, top 0.3s";
        sidebar.style.top = "20px";
        sidebar.style.right = "20px";
        sidebar.style.left = "auto";
        toggleBtn.style.display = "none";
        attachTypeHandlers(); // Re-attach handlers in case DOM changed
    }};

    // Drag functionality
    var isDragging = false, dragOffsetX = 0, dragOffsetY = 0;
    var header = document.getElementById('sidebarHeader');
    header.onmousedown = function(e) {{
        isDragging = true;
        dragOffsetX = e.clientX - sidebar.getBoundingClientRect().left;
        dragOffsetY = e.clientY - sidebar.getBoundingClientRect().top;
        document.body.style.userSelect = "none";
    }};
    document.onmousemove = function(e) {{
        if (isDragging) {{
            sidebar.style.left = "auto";
            sidebar.style.right = "auto";
            sidebar.style.top = (e.clientY - dragOffsetY) + "px";
            sidebar.style.left = (e.clientX - dragOffsetX) + "px";
        }}
    }};
    document.onmouseup = function(e) {{
        isDragging = false;
        document.body.style.userSelect = "";
    }};

    // Set province selector to match the default province
    document.getElementById('provSel').value = "{default_province}";

    // Province selector event (customize as needed)
    document.getElementById('provSel').addEventListener('change', function(e) {{
        alert('Province change: implement your province switching logic here.');
    }});

    // Listen for changes to the type selector and update marker layers
    document.getElementById('typeSel').addEventListener('change', function() {{
        var selected = Array.from(this.selectedOptions).map(function(opt) {{ return opt.value; }});
        var typeGroups = {type_group_js_json};
        for (var t in typeGroups) {{
            var layerName = typeGroups[t];
            var layer = map._layers;
            for (var key in layer) {{
                var obj = layer[key];
                if (obj && obj.options && obj.options.name === t) {{
                    if (selected.includes(t)) {{
                        map.addLayer(obj);
                    }} else {{
                        map.removeLayer(obj);
                    }}
                }}
            }}
        }}
    }});
}});
</script>
"""

m.get_root().html.add_child(folium.Element(widget_js))
m.get_root().html.add_child(folium.Element(sidebar_js))
m.save("Airport_Survey_v3.html")
print("Map saved -> Airport_Survey_v3.html")

