# Airport NOTAM map (repo-driven)
# Rewritten to load NOTAMs from GitHub repo clone data/notams/All_CA.json

import html
import json
from pathlib import Path

import pandas as pd
import geopandas as gpd
import folium
from folium.plugins import FeatureGroupSubGroup, GroupedLayerControl, MarkerCluster

# ==============================
# GLOBAL CONFIG
# ==============================
DEFAULT_ZOOM = 10
NM_TO_M = 1852
NOTAM_RADIUS_KM = 10
NOTAM_RADIUS_M = NOTAM_RADIUS_KM * 1000

# Point this to your local GitHub repo clone root
REPO_ROOT = Path(r"C:\Users\Ron Treleaven\Drone_SOP")
NOTAMS_PATH = REPO_ROOT / "data" / "notams" / "All_CA.json"
META_PATH = REPO_ROOT / "data" / "notams" / "All_CA.meta.json"

ICON_STYLE = {
    "heliport": {"icon": "helicopter", "color": "green"},
    "seaplane_base": {"icon": "ship", "color": "cadetblue"},
    "small_airport": {"icon": "circle", "color": "gray"},
    "medium_airport": {"icon": "plane", "color": "blue"},
    "large_airport": {"icon": "plane", "color": "darkblue"},
    "default": {"icon": "map-marker", "color": "lightgray"},
}


def get_pilot_location():
    fetch_location = input(
        "Would you like to fetch your current location? (y/n): "
    ).strip().lower()

    if fetch_location == "y":
        try:
            import geocoder

            print("Fetching your current location...")
            g = geocoder.ip("me")

            if g.ok and g.latlng and len(g.latlng) == 2:
                pilot_lat, pilot_lon = g.latlng
                print(f"Detected: {pilot_lat}, {pilot_lon}")

                confirm = input("Use this location? (y/n): ").strip().lower()
                if confirm == "y":
                    return float(pilot_lat), float(pilot_lon)

            print("Falling back to manual entry.")
        except ImportError:
            print("geocoder package not installed.")
            print("Falling back to manual entry.")
        except Exception as exc:
            print(f"Unable to auto-detect location: {exc}")
            print("Falling back to manual entry.")

    while True:
        try:
            lat = float(input("Pilot latitude (decimal degrees): ").strip())
            lon = float(input("Pilot longitude (decimal degrees): ").strip())
            return lat, lon
        except ValueError:
            print("Numeric lat/lon required.")


def load_notams_from_repo():
    if not NOTAMS_PATH.exists():
        raise SystemExit(f"NOTAM file not found: {NOTAMS_PATH}")

    with NOTAMS_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise SystemExit("All_CA.json is not a JSON array.")

    generated_at = None
    if META_PATH.exists():
        try:
            with META_PATH.open("r", encoding="utf-8") as f:
                meta = json.load(f)
            generated_at = meta.get("generatedAt")
        except Exception:
            generated_at = None

    return data, generated_at


def build_map(pilot_lat, pilot_lon, notams_data, generated_at=None):
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

    c100 = folium.Circle(
        [pilot_lat, pilot_lon],
        radius=NOTAM_RADIUS_M,
        color="red",
        weight=2,
        dash_array="8,6",
        fill=False,
        popup=f"{NOTAM_RADIUS_KM} km NOTAM filter radius",
    ).add_to(m)
    c100_js = c100.get_name()

    # 5) Obstacles layer from repo JSON
    obstacle_layer = folium.FeatureGroup(name=f"Obstacles <= {NOTAM_RADIUS_KM} km")
    shown = 0
    for notam in notams_data:
        coords = notam.get("coordinates_dd") or []
        raw = (notam.get("raw") or "").strip()
        if not coords or not raw:
            continue

        safe_raw = html.escape(raw).replace("\n", "<br>")
        start_val = html.escape(str(notam.get("startValidity") or "N/A"))
        end_val = html.escape(str(notam.get("endValidity") or "N/A"))

        for coord in coords:
            try:
                lat, lon = map(float, coord.split(","))
            except Exception:
                continue
            popup_content = (
                "<b>Obstacle Alert</b><br>"
                f"<b>Start:</b> {start_val}<br>"
                f"<b>End:</b> {end_val}<hr style='margin:6px 0'>"
                f"{safe_raw}"
            )
            folium.Marker(
                [lat, lon],
                tooltip="Obstacle",
                popup=folium.Popup(popup_content, max_width=420, parse_html=True),
                icon=folium.Icon(color="red", icon="exclamation-triangle", prefix="fa"),
            ).add_to(obstacle_layer)
            shown += 1

    obstacle_layer.add_to(m)
    layers_dict["Obstacles"] = [obstacle_layer]

    # 6) Layer control + style
    GroupedLayerControl(groups=layers_dict, exclusive_groups=[], collapsed=False).add_to(m)
    m.get_root().html.add_child(
        folium.Element(
            "<style>.leaflet-control-layers-list{max-height:300px;overflow-y:auto;}.pilot-input{z-index:1200;}</style>"
        )
    )

    # 7) Inject widget for pilot drag/manual update and dynamic 100 km filter
    widget_js = f"""
<script>
window.onload = function() {{
  var map = {m.get_name()};
  var marker = {pm_js};
  var c1 = {c1_js};
  var c3 = {c3_js};
  var c100 = {c100_js};

  marker.dragging.enable();
  marker.on('dragend', function(e) {{
      var ll = e.target.getLatLng();
      c1.setLatLng(ll); c3.setLatLng(ll); c100.setLatLng(ll);
      marker.setPopupContent("Pilot<br>Lat: " + ll.lat.toFixed(6) + "<br>Lon: " + ll.lng.toFixed(6));
  }});

  var ctl = L.control({{position:'bottomleft'}});
  ctl.onAdd = function() {{
      var d = L.DomUtil.create('div','pilot-input');
      L.DomEvent.disableClickPropagation(d);
      d.style.background='white'; d.style.padding='6px'; d.style.fontSize='14px';
      d.style.boxShadow='0 0 4px rgba(0,0,0,0.3)';
      d.innerHTML = 'Lat <input id="pLat" size="9"> Lon <input id="pLon" size="9"> <button id="upd">Update</button>';
      return d;
  }};
  ctl.addTo(map);

  document.getElementById('upd').onclick = function() {{
      var lat=parseFloat(document.getElementById('pLat').value);
      var lon=parseFloat(document.getElementById('pLon').value);
      if(isNaN(lat)||isNaN(lon)) {{ alert("Enter numeric lat & lon"); return; }}
      var ll=L.latLng(lat,lon);
      marker.setLatLng(ll).openPopup();
      c1.setLatLng(ll); c3.setLatLng(ll); c100.setLatLng(ll);
      map.setView(ll, {DEFAULT_ZOOM});
  }};
}};
</script>
"""
    m.get_root().html.add_child(folium.Element(widget_js))

    print(f"Loaded NOTAMs from: {NOTAMS_PATH}")
    if generated_at:
        print(f"NOTAM data generatedAt: {generated_at}")
    print(f"Obstacle markers plotted: {shown}")

    return m


def main():
    pilot_lat, pilot_lon = get_pilot_location()
    print(f"Using pilot location: {pilot_lat}, {pilot_lon}")

    notams_data, generated_at = load_notams_from_repo()
    m = build_map(pilot_lat, pilot_lon, notams_data, generated_at)

    out_name = "2026_NOTAMS Map.html"
    m.save(out_name)
    print(f"Map saved as -> {out_name}")


if __name__ == "__main__":
    main()
