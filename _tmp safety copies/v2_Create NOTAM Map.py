# Airport NOTAM map (dynamic NOTAM loading)
# v2 baseline: keeps airport layers static, loads NOTAM obstacles at page launch.

import json
from pathlib import Path

import nest_asyncio
import pandas as pd
import geopandas as gpd
import folium
from folium.plugins import FeatureGroupSubGroup, GroupedLayerControl, MarkerCluster

# ==============================
# GLOBAL CONFIG
# ==============================
DEFAULT_ZOOM = 12
NM_TO_M = 1852
NOTAM_RADIUS_KM = 10
NOTAM_RADIUS_M = NOTAM_RADIUS_KM * 1000
NOTAMS_URL = "./data/notams/All_CA.json"

ICON_STYLE = {
    "heliport": {"icon": "helicopter", "color": "green"},
    "seaplane_base": {"icon": "ship", "color": "cadetblue"},
    "small_airport": {"icon": "circle", "color": "gray"},
    "medium_airport": {"icon": "plane", "color": "blue"},
    "large_airport": {"icon": "plane", "color": "darkblue"},
    "default": {"icon": "map-marker", "color": "lightgray"},
}

nest_asyncio.apply()


def get_windows_location(timeout=5, desired_accuracy=25):
    """
    Returns (lat, lon, accuracy_m) using Windows Location Services
    or None if unavailable / denied / timeout exceeded.
    """
    try:
        import asyncio
        from winsdk.windows.devices.geolocation import Geolocator

        async def _locate():
            locator = Geolocator()
            locator.desired_accuracy_in_meters = desired_accuracy

            pos = await asyncio.wait_for(
                locator.get_geoposition_async(),
                timeout=timeout
            )

            lat = pos.coordinate.point.position.latitude
            lon = pos.coordinate.point.position.longitude
            acc = pos.coordinate.accuracy
            return lat, lon, acc

        return asyncio.run(_locate())
    except Exception:
        return None


def get_pilot_location():
    use_auto = input(
        "Fetch pilot location from Windows Location Services if available? (y/n): "
    ).strip().lower()

    if use_auto == "y":
        result = get_windows_location()
        if result:
            lat, lon, acc = result
            print("\nDetected:")
            print(f"Lat: {lat}")
            print(f"Lon: {lon}")
            print(f"Accuracy: +/-{round(acc, 1)} m")
            confirm = input("Use this location? (y/n): ").strip().lower()
            if confirm == "y":
                return lat, lon

        print("Auto-location unavailable. Falling back to manual.")

    while True:
        try:
            lat = float(input("Pilot latitude (decimal degrees): ").strip())
            lon = float(input("Pilot longitude (decimal degrees): ").strip())
            return lat, lon
        except ValueError:
            print("Numeric lat/lon required.")


def build_map(pilot_lat, pilot_lon):
    # 1) Airports
    df = pd.read_csv("https://davidmegginson.github.io/ourairports-data/airports.csv")
    df = df[df["iso_country"] == "CA"].copy()
    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df.longitude_deg, df.latitude_deg),
        crs="EPSG:4326",
    )

    # 2) Base map
    m = folium.Map(location=[pilot_lat, pilot_lon], zoom_start=DEFAULT_ZOOM, tiles="CartoDB positron")

    # 3) Province/type layers
    province_parents, layers_dict = {}, {}
    for prov in sorted(gdf["iso_region"].dropna().unique(), key=lambda x: (x != "CA-ON", x)):
        fg = folium.FeatureGroup(name=prov).add_to(m)
        province_parents[prov] = fg
        layers_dict[prov] = []

    for prov, prov_df in gdf.groupby("iso_region"):
        for atype, sub in prov_df.groupby("type"):
            child = FeatureGroupSubGroup(province_parents[prov], atype, show=False, overlay=True)
            cluster = MarkerCluster().add_to(child)
            style = ICON_STYLE.get(atype, ICON_STYLE["default"])
            for _, row in sub.iterrows():
                lat, lon = row.geometry.y, row.geometry.x
                ident = row.get("ident") or row.get("icao_code") or "UNK"
                name = row.get("name") or "Unnamed"
                folium.Marker(
                    [lat, lon],
                    tooltip=f"{ident} | {name}",
                    popup=f"{ident} - {name}<br>Lat: {lat:.6f}<br>Lon: {lon:.6f}",
                    icon=folium.Icon(color=style["color"], icon=style["icon"], prefix="fa"),
                ).add_to(cluster)
            child.add_to(m)
            layers_dict[prov].append(child)

    # 4) Pilot marker + rings
    pm = folium.Marker(
        [pilot_lat, pilot_lon],
        tooltip="Pilot location",
        popup=f"Pilot<br>Lat: {pilot_lat:.6f}<br>Lon: {pilot_lon:.6f}",
        icon=folium.Icon(color="green", icon="user", prefix="fa"),
    ).add_to(m)
    pm_js = pm.get_name()

    c1 = folium.Circle(
        [pilot_lat, pilot_lon],
        radius=NM_TO_M,
        color="green",
        weight=2,
        fill=False,
        popup="1 NM (1.9 km) radius",
    ).add_to(m)
    c1_js = c1.get_name()

    c3 = folium.Circle(
        [pilot_lat, pilot_lon],
        radius=3 * NM_TO_M,
        color="green",
        weight=3,
        dash_array="5,5",
        fill=False,
        popup="3 NM (5.6 km) radius",
    ).add_to(m)
    c3_js = c3.get_name()

    c10 = folium.Circle(
        [pilot_lat, pilot_lon],
        radius=NOTAM_RADIUS_M,
        color="red",
        weight=2,
        dash_array="8,6",
        fill=False,
        popup=f"{NOTAM_RADIUS_KM} km NOTAM display ring",
    ).add_to(m)
    c10_js = c10.get_name()

    # 5) Empty obstacles layer - dynamically populated in browser
    obstacle_layer = folium.FeatureGroup(name=f"ACTIVE Obstacles ({NOTAM_RADIUS_KM} km ring)", show=True).add_to(m)
    layers_dict["Obstacles"] = [obstacle_layer]

    # 6) Layer control + style
    control_groups = {"Safety": layers_dict["Obstacles"]}
    for group_name, group_layers in layers_dict.items():
        if group_name != "Obstacles":
            control_groups[group_name] = group_layers

    GroupedLayerControl(groups=control_groups, exclusive_groups=[], collapsed=False).add_to(m)
    m.get_root().html.add_child(
        folium.Element(
            "<style>"
            ".leaflet-control-layers{min-width:280px;max-width:340px;font-size:13px;}"
            ".leaflet-control-layers-group-name{font-weight:700;color:#1f3b63;margin-top:6px;}"
            ".leaflet-control-layers-list{max-height:56vh;overflow-y:auto;padding-right:4px;}"
            ".pilot-input{z-index:1200;}"
            "</style>"
        )
    )

    # 7) JS widget + dynamic NOTAM loading
    widget_js = f"""
<script>
window.onload = function() {{
  var map = {m.get_name()};
  var marker = {pm_js};
  var c1 = {c1_js};
  var c3 = {c3_js};
  var c10 = {c10_js};
  var obstacleLayer = {obstacle_layer.get_name()};
  var notamsUrl = {json.dumps(NOTAMS_URL)};

  map.setView(marker.getLatLng(), {DEFAULT_ZOOM});

  function escapeHtml(txt) {{
    var d = document.createElement('div');
    d.textContent = txt == null ? '' : String(txt);
    return d.innerHTML;
  }}

  function parseCoord(coordText) {{
    if (!coordText || typeof coordText !== 'string') return null;
    var p = coordText.split(',');
    if (p.length < 2) return null;
    var lat = parseFloat(p[0].trim());
    var lon = parseFloat(p[1].trim());
    if (isNaN(lat) || isNaN(lon)) return null;
    return [lat, lon];
  }}

  function addObstacleMarker(lat, lon, notam) {{
    var startVal = escapeHtml(notam.startValidity || 'N/A');
    var endVal = escapeHtml(notam.endValidity || 'N/A');
    var rawSafe = escapeHtml(notam.raw || '').replace(/\\n/g, '<br>');
    var popupHtml =
      "<div style='font-family:Segoe UI,Arial,sans-serif;font-size:13px;line-height:1.35;'>" +
      "<div style='font-weight:700;color:#b00020;margin-bottom:4px;'>Obstacle Alert</div>" +
      "<div><span style='font-weight:600;'>Start:</span> " + startVal + "</div>" +
      "<div><span style='font-weight:600;'>End:</span> " + endVal + "</div>" +
      "<hr style='margin:6px 0'>" +
      "<div style='max-height:220px;overflow:auto;white-space:normal;'>" + rawSafe + "</div>" +
      "</div>";

    L.marker([lat, lon], {{
      icon: L.AwesomeMarkers.icon({{
        icon: 'exclamation-triangle',
        prefix: 'fa',
        markerColor: 'red'
      }})
    }})
      .bindTooltip("Obstacle")
      .bindPopup(popupHtml, {{ maxWidth: 500 }})
      .addTo(obstacleLayer);
  }}

  function loadNotams() {{
    fetch(notamsUrl)
      .then(function(resp) {{
        if (!resp.ok) throw new Error("HTTP " + resp.status);
        return resp.json();
      }})
      .then(function(data) {{
        if (!Array.isArray(data)) throw new Error("All_CA.json is not an array");
        var count = 0;
        obstacleLayer.clearLayers();
        data.forEach(function(notam) {{
          var coords = Array.isArray(notam.coordinates_dd) ? notam.coordinates_dd : [];
          coords.forEach(function(c) {{
            var pair = parseCoord(c);
            if (!pair) return;
            addObstacleMarker(pair[0], pair[1], notam);
            count += 1;
          }});
        }});
        console.log("Loaded obstacle markers:", count);
      }})
      .catch(function(err) {{
        console.error("Failed to load NOTAMs:", err);
      }});
  }}

  marker.dragging.enable();
  marker.on('dragend', function(e) {{
      var ll = e.target.getLatLng();
      c1.setLatLng(ll); c3.setLatLng(ll); c10.setLatLng(ll);
      marker.setPopupContent("Pilot<br>Lat: " + ll.lat.toFixed(6) + "<br>Lon: " + ll.lng.toFixed(6));
      var latInput = document.getElementById('pLat');
      var lonInput = document.getElementById('pLon');
      if (latInput) latInput.value = ll.lat.toFixed(6);
      if (lonInput) lonInput.value = ll.lng.toFixed(6);
  }});

  var ctl = L.control({{position:'bottomleft'}});
  ctl.onAdd = function() {{
      var d = L.DomUtil.create('div','pilot-input');
      L.DomEvent.disableClickPropagation(d);
      d.style.background='white'; d.style.padding='6px'; d.style.fontSize='14px';
      d.style.boxShadow='0 0 4px rgba(0,0,0,0.3)';
      d.innerHTML = 'Lat <input id="pLat" size="9" value="' + marker.getLatLng().lat.toFixed(6) + '"> Lon <input id="pLon" size="9" value="' + marker.getLatLng().lng.toFixed(6) + '"> <button id="upd">Update</button>';
      return d;
  }};
  ctl.addTo(map);

  document.getElementById('upd').onclick = function() {{
      var lat=parseFloat(document.getElementById('pLat').value);
      var lon=parseFloat(document.getElementById('pLon').value);
      if(isNaN(lat)||isNaN(lon)) {{ alert("Enter numeric lat & lon"); return; }}
      var ll=L.latLng(lat,lon);
      marker.setLatLng(ll).openPopup();
      c1.setLatLng(ll); c3.setLatLng(ll); c10.setLatLng(ll);
      map.setView(ll, {DEFAULT_ZOOM});
  }};

  loadNotams();
}};
</script>
"""
    m.get_root().html.add_child(folium.Element(widget_js))
    return m


def main():
    pilot_lat, pilot_lon = get_pilot_location()
    print(f"Using pilot location: {pilot_lat}, {pilot_lon}")

    m = build_map(pilot_lat, pilot_lon)

    out_name = "v2_Notam Map.html"
    m.save(out_name)
    print(f"Map saved as -> {out_name}")
    print(f"NOTAMs will load dynamically at page open from: {NOTAMS_URL}")


if __name__ == "__main__":
    main()
