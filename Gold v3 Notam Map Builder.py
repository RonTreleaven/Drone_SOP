# Airport NOTAM map (repo-driven gathering of NOTAMS daily)
# Rewritten to load NOTAMs from GitHub repo clone data/notams/All_CA.json

#########################################################################
# This creates the base "Notam Map.html" or user defined name for one-off runs
# Notam Map.html is the basemap, and will pull NOTAM data for /data/Notams/*.json files
#

import html
import json
import math
import re
from pathlib import Path

import nest_asyncio
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
COORD_DECIMALS = 6

# Point this to your local GitHub repo clone root
REPO_ROOT = Path(r"C:\Users\Ron Treleaven\Drone_SOP")
NOTAMS_FILTERED_PATH = REPO_ROOT / "data" / "notams" / "All_CA.json"
NOTAMS_RAW_PATH = REPO_ROOT / "data" / "notams" / "All_CA_raw.json"
META_PATH = REPO_ROOT / "data" / "notams" / "All_CA.meta.json"

ICON_STYLE = {
    "heliport": {"icon": "helicopter", "color": "green"},
    "seaplane_base": {"icon": "ship", "color": "cadetblue"},
    "small_airport": {"icon": "circle", "color": "gray"},
    "medium_airport": {"icon": "plane", "color": "blue"},
    "large_airport": {"icon": "plane", "color": "darkblue"},
    "default": {"icon": "map-marker", "color": "lightgray"},
}

PROVINCE_NAMES = {
    "CA-AB": "Alberta",
    "CA-BC": "British Columbia",
    "CA-MB": "Manitoba",
    "CA-NB": "New Brunswick",
    "CA-NL": "Newfoundland and Labrador",
    "CA-NS": "Nova Scotia",
    "CA-NT": "Northwest Territories",
    "CA-NU": "Nunavut",
    "CA-ON": "Ontario",
    "CA-PE": "Prince Edward Island",
    "CA-QC": "Quebec",
    "CA-SK": "Saskatchewan",
    "CA-YT": "Yukon",
}


def province_label(iso_region: str) -> str:
    name = PROVINCE_NAMES.get(iso_region)
    return f"{iso_region} ({name})" if name else iso_region

DEFAULT_BASEMAP_KEY = "cartodb_positron"
BASEMAP_OPTIONS = {
    "cartodb_positron": {
        "name": "CartoDB Positron",
        "tiles": "CartoDB positron",
    },
    "cartodb_voyager": {
        "name": "CartoDB Voyager",
        "tiles": "CartoDB Voyager",
    },
    "openstreetmap": {
        "name": "OpenStreetMap",
        "tiles": "OpenStreetMap",
    },
    "opentopomap": {
        "name": "OpenTopoMap",
        "tiles": "https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png",
        "attr": "Map data (c) OpenStreetMap contributors, SRTM | style (c) OpenTopoMap",
    },
    "esri_world_imagery": {
        "name": "Esri World Imagery",
        "tiles": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        "attr": "Tiles (c) Esri and contributors",
    },
    "google_roadmap": {
        "name": "Google Roadmap",
        "tiles": "https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}",
        "attr": "Map data (c) Google",
    },
    "google_satellite": {
        "name": "Google Satellite",
        "tiles": "https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
        "attr": "Imagery (c) Google",
    },
    "google_hybrid": {
        "name": "Google Hybrid",
        "tiles": "https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}",
        "attr": "Imagery and labels (c) Google",
    },
    "google_terrain": {
        "name": "Google Terrain",
        "tiles": "https://mt1.google.com/vt/lyrs=p&x={x}&y={y}&z={z}",
        "attr": "Terrain (c) Google",
    },
}

nest_asyncio.apply()


def haversine_km(lat1, lon1, lat2, lon2):
    r_km = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(d_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    )
    return 2 * r_km * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def format_notam_raw_for_popup(raw_text):
    compact = re.sub(r"\s+", " ", (raw_text or "")).strip()
    if not compact:
        return ""

    section_split = r"(?=\b(?:Q|A|B|C|D|E|F|G|X)\))"
    parts = [part.strip() for part in re.split(section_split, compact) if part.strip()]
    return "<br>".join(html.escape(part) for part in parts)


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
                timeout=timeout,
            )

            lat = pos.coordinate.point.position.latitude
            lon = pos.coordinate.point.position.longitude
            acc = pos.coordinate.accuracy
            return lat, lon, acc

        return asyncio.run(_locate())
    except Exception:
        return None


def get_pilot_location():
    print("Pilot coordinate format: Decimal Degrees (DD)")
    print("Example latitude: 43.653200")
    print("Example longitude: -79.383200")

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
                return float(lat), float(lon)

        print("Auto-location unavailable. Falling back to manual entry.")

    while True:
        try:
            lat = float(
                input("Pilot latitude DD (e.g., 43.653200, range -90 to 90): ").strip()
            )
            lon = float(
                input("Pilot longitude DD (e.g., -79.383200, range -180 to 180): ").strip()
            )
            if not (-90 <= lat <= 90):
                print("Latitude out of range. Use -90 to 90.")
                continue
            if not (-180 <= lon <= 180):
                print("Longitude out of range. Use -180 to 180.")
                continue
            return lat, lon
        except ValueError:
            print("Numeric DD lat/lon required (example: 43.653200 and -79.383200).")


def choose_basemap_key():
    print("\nBasemap options:")
    keys = list(BASEMAP_OPTIONS.keys())
    for idx, key in enumerate(keys, start=1):
        print(f"{idx}. {BASEMAP_OPTIONS[key]['name']} [{key}]")

    choice = input(
        f"Choose basemap by number or key [{DEFAULT_BASEMAP_KEY}]: "
    ).strip().lower()

    if not choice:
        return DEFAULT_BASEMAP_KEY

    if choice.isdigit():
        num = int(choice)
        if 1 <= num <= len(keys):
            return keys[num - 1]

    if choice in BASEMAP_OPTIONS:
        return choice

    print(f"Unknown basemap '{choice}'. Falling back to {DEFAULT_BASEMAP_KEY}.")
    return DEFAULT_BASEMAP_KEY


def load_notams_file(path, label):
    if not path.exists():
        raise SystemExit(f"NOTAM file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise SystemExit(f"{label} is not a JSON array.")

    return data


def load_notams_from_repo():
    filtered_data = load_notams_file(NOTAMS_FILTERED_PATH, "All_CA.json")
    raw_data = load_notams_file(NOTAMS_RAW_PATH, "All_CA_raw.json")

    generated_at = None
    if META_PATH.exists():
        try:
            with META_PATH.open("r", encoding="utf-8") as f:
                meta = json.load(f)
            generated_at = meta.get("generatedAt")
        except Exception:
            generated_at = None

    return filtered_data, raw_data, generated_at


def prepare_obstacle_points(notams_data):
    points = []
    for notam in notams_data:
        coords = notam.get("coordinates_dd") or []
        raw = (notam.get("raw") or "").strip()
        if not coords or not raw:
            continue

        start_val = str(notam.get("startValidity") or "N/A")
        end_val = str(notam.get("endValidity") or "N/A")
        safe_raw = format_notam_raw_for_popup(raw)

        for coord in coords:
            try:
                lat, lon = map(float, coord.split(","))
            except Exception:
                continue
            points.append(
                {
                    "lat": lat,
                    "lon": lon,
                    "start": start_val,
                    "end": end_val,
                    "rawHtml": safe_raw,
                }
            )

    return points


def build_map(
    pilot_lat,
    pilot_lon,
    notams_filtered,
    notams_raw,
    generated_at=None,
    basemap_key=DEFAULT_BASEMAP_KEY,
):
    # 1) Airports
    df = pd.read_csv("https://davidmegginson.github.io/ourairports-data/airports.csv")
    df = df[df["iso_country"] == "CA"].copy()

    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df.longitude_deg, df.latitude_deg),
        crs="EPSG:4326",
    )

    # 2) Base map
    m = folium.Map(
        location=[pilot_lat, pilot_lon],
        zoom_start=DEFAULT_ZOOM,
        tiles=None,
        zoom_control=False,
    )
    basemap = BASEMAP_OPTIONS.get(basemap_key, BASEMAP_OPTIONS[DEFAULT_BASEMAP_KEY])
    basemap_layers = {}
    for key, opt in BASEMAP_OPTIONS.items():
        layer = folium.TileLayer(
            tiles=opt["tiles"],
            attr=opt.get("attr"),
            name=opt["name"],
            overlay=False,
            control=False,
            show=(key == basemap_key),
        ).add_to(m)
        basemap_layers[opt["name"]] = layer.get_name()

    basemap_layers_js = "{\n" + ",\n".join(
        f"      {json.dumps(name)}: {js_var}"
        for name, js_var in basemap_layers.items()
    ) + "\n    }"

    # 3) Province/type layers
    province_parents, layers_dict = {}, {}
    province_group_labels = {}
    airport_layer_vars = []
    airport_layer_index = {}
    for prov in sorted(gdf["iso_region"].dropna().unique(), key=lambda x: (x != "CA-ON", x)):
        fg = folium.FeatureGroup(name=prov).add_to(m)
        province_parents[prov] = fg
        display_label = province_label(prov)
        province_group_labels[prov] = display_label
        layers_dict[display_label] = []

    for prov, prov_df in gdf.groupby("iso_region"):
        for atype, sub in prov_df.groupby("type"):
            child = FeatureGroupSubGroup(province_parents[prov], atype, show=False, overlay=True)
            cluster = MarkerCluster().add_to(child)
            style = ICON_STYLE.get(atype, ICON_STYLE["default"])
            for _, row in sub.iterrows():
                lat, lon = row.geometry.y, row.geometry.x
                ident = row.get("ident") or row.get("icao_code") or "UNK"
                name = row.get("name") or "Unnamed"
                dd_str = f"{lat:.6f}, {lon:.6f}"
                focus_url = f"NotamsMap.html?lat={lat:.6f}&lon={lon:.6f}&focus=1&src=qfilter"
                folium.Marker(
                    [lat, lon],
                    tooltip=f"{ident} | {name}",
                    popup=(
                        f"{ident} - {name}"
                        f"<br><a href='{focus_url}'>Open NOTAM focus: {dd_str}</a>"
                    ),
                    icon=folium.Icon(color=style["color"], icon=style["icon"], prefix="fa"),
                ).add_to(cluster)
            child.add_to(m)
            layers_dict[province_group_labels[prov]].append(child)
            airport_layer_vars.append(child.get_name())
            airport_layer_index.setdefault(prov, {})[atype] = child.get_name()

    airport_layers_js = "[" + ", ".join(airport_layer_vars) + "]"
    airport_layer_index_js = (
        "{\n"
        + ",\n".join(
            "      "
            + json.dumps(prov)
            + ": {"
            + ", ".join(
                f"{json.dumps(atype)}: {layer_var}"
                for atype, layer_var in sorted(type_map.items())
            )
            + "}"
            for prov, type_map in sorted(airport_layer_index.items())
        )
        + "\n    }"
    )

    # 4) Pilot marker + rings
    pm = folium.Marker(
        [pilot_lat, pilot_lon],
        tooltip="Pilot location",
        popup=f"Pilot<br>Lat: {pilot_lat:.6f}<br>Lon: {pilot_lon:.6f}",
        icon=folium.Icon(color="purple", icon="user", prefix="fa"),
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
    obstacle_layer_js = obstacle_layer.get_name()
    obstacle_layer.add_to(m)

    # 6) Layer control + style
    control_groups = {}
    for group_name, group_layers in layers_dict.items():
        control_groups[group_name] = group_layers

    GroupedLayerControl(groups=control_groups, exclusive_groups=[], collapsed=True).add_to(m)
    m.get_root().html.add_child(
        folium.Element(
            "<style>"
            ".leaflet-control-layers{font-size:13px;}"
            ".leaflet-control-layers.leaflet-control-layers-expanded{min-width:220px;max-width:320px;padding:7px 9px;}"
            ".leaflet-control-layers-group-name{font-weight:700;color:#1f3b63;margin-top:6px;}"
            ".leaflet-control-layers-list{max-height:56vh;overflow-y:auto;padding-right:4px;}"
            ".leaflet-control-layers-group-label{display:block;}"
            "@media (max-width:600px){.leaflet-control-layers{min-width:176px;max-width:220px;font-size:12px;}.leaflet-control-layers-expanded{padding:6px 8px;}}"
            ".pilot-input{z-index:1200;}"
            ".pilot-flyout{position:relative;width:272px;background:#fff;border:1px solid #d8e2ee;border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,0.2);padding:7px;transition:transform .2s ease;overflow:visible;box-sizing:border-box;}"
            ".pilot-flyout.collapsed{transform:translateX(-100%);}" 
            ".pilot-flyout-toggle{position:absolute;right:-30px;top:10px;width:30px;height:34px;border:1px solid #d8e2ee;border-left:none;border-radius:0 8px 8px 0;background:#fff;color:#1f3b63;cursor:pointer;font-size:14px;display:flex;align-items:center;justify-content:center;}"
            ".pilot-flyout .controls-row{display:flex;flex-wrap:wrap;gap:3px;align-items:center;}"
            ".pilot-flyout input{max-width:102px;font-size:12px;}"
            ".pilot-flyout .action-grid{display:grid;grid-template-columns:1fr 1fr;gap:4px;margin-top:5px;}"
            ".pilot-flyout .action-grid button{width:100%;height:24px;margin:0;padding:2px 4px;font-size:10px;line-height:1.05;text-align:center;}"
            ".pilot-flyout .controls-meta{font-size:11px;margin-top:3px;line-height:1.25;}"
            ".pilot-flyout .status-line{font-weight:600;color:#1f3b63;}"
            ".pilot-flyout .dd-hint{color:#666;margin-top:2px;}"
            ".home-logo-control{background:#fff;border:1px solid #d8e2ee;border-radius:8px;padding:4px 6px;box-shadow:0 2px 6px rgba(0,0,0,0.2);}"
            ".home-logo-control img{display:block;height:64px;width:auto;}"
            ".map-layers-control .leaflet-control-layers-toggle{background-image:none!important;width:34px;height:34px;position:relative;border-radius:8px;background:linear-gradient(145deg,#e7f3ff,#d5e8ff);border:1px solid #c2d6ef;}"
            ".map-layers-control .leaflet-control-layers-toggle:before{content:'\\f0ac';font-family:'Font Awesome 6 Free';font-weight:900;font-size:16px;line-height:34px;display:block;text-align:center;color:#12406d;}"
            ".left-mini-toggle-control{background:#fff;border:1px solid #d8e2ee;border-radius:8px;box-shadow:0 2px 6px rgba(0,0,0,0.2);}"
            ".left-mini-toggle-btn{width:34px;height:34px;display:flex;align-items:center;justify-content:center;color:#1f3b63;text-decoration:none;font-size:16px;}"
            ".left-mini-toggle-control.inactive .left-mini-toggle-btn{color:#8b97a7;background:#f4f6f9;}"
            ".center-map-control{background:#fff;border:1px solid #d8e2ee;border-radius:8px;box-shadow:0 2px 6px rgba(0,0,0,0.2);}"
            ".center-map-btn{width:34px;height:34px;display:flex;align-items:center;justify-content:center;color:#1f3b63;text-decoration:none;font-size:16px;}"
            ".leaflet-control-zoom.leaflet-bar{border:1px solid #d8e2ee;border-radius:8px;box-shadow:0 2px 6px rgba(0,0,0,0.2);overflow:hidden;}"
            ".leaflet-control-zoom.leaflet-bar a{width:34px;height:34px;line-height:34px;font-size:18px;color:#1f3b63;}"
            ".leaflet-control-zoom.leaflet-bar a:first-child{border-top-left-radius:8px;border-top-right-radius:8px;}"
            ".leaflet-control-zoom.leaflet-bar a:last-child{border-bottom-left-radius:8px;border-bottom-right-radius:8px;}"
            ".notam-popup{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;font-size:13px;line-height:1.35;color:#333;}"
            ".notam-title{font-weight:700;color:#007acc;margin-bottom:4px;}"
            ".notam-label{font-weight:600;color:#1f3b63;}"
            ".notam-raw{max-height:220px;overflow:auto;white-space:normal;}"
            "</style>"
        )
    )
    m.get_root().html.add_child(
        folium.Element(
            """
<style>
  .map-layers-control.leaflet-control-layers {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
  }
  .map-layers-control.leaflet-control-layers-expanded {
    background: #ffffff !important;
    border: 1px solid #d8e2ee !important;
    box-shadow: 0 2px 6px rgba(0,0,0,0.2) !important;
    border-radius: 8px;
  }
  .map-layers-control .leaflet-control-layers-list {
    max-height: 56vh;
    overflow-y: auto;
    touch-action: pan-y;
    overscroll-behavior: contain;
  }
  .map-layers-control .map-layers-close-btn {
    display: none;
    margin-top: 8px;
    width: 100%;
    border: 1px solid #d8e2ee;
    border-radius: 6px;
    background: #f7fafc;
    color: #1f3b63;
    font-size: 12px;
    font-weight: 700;
    padding: 6px 8px;
    cursor: pointer;
  }
  .map-layers-control.leaflet-control-layers-expanded .map-layers-close-btn {
    display: block;
  }

  #getPilotLoc.needs-location {
    background: #2e7d32;
    border: 1px solid #1b5e20;
    color: #ffffff;
    font-weight: 700;
  }
  #getPilotLoc.needs-location:hover {
    background: #276a2b;
  }
  .pilot-marker-wrap {
    background: transparent;
    border: none;
  }
  .pilot-marker-wrap .pilot-marker-glow {
    position: absolute;
    left: 50%;
    top: 52%;
    width: 34px;
    height: 34px;
    transform: translate(-50%, -50%);
    border-radius: 50%;
    background: rgba(255, 215, 0, 0.34);
    box-shadow: 0 0 12px 6px rgba(255, 215, 0, 0.56);
    pointer-events: none;
  }
  .pilot-marker-wrap .pilot-marker-pin {
    position: absolute;
    left: 50%;
    top: 2px;
    width: 30px;
    height: 30px;
    transform: translateX(-50%) rotate(-45deg);
    border-radius: 50% 50% 50% 0;
    background: #4a148c;
    border: 2px solid #ffffff;
    box-shadow: 0 2px 6px rgba(0,0,0,0.35);
  }
  .pilot-marker-wrap .pilot-marker-pin i {
    position: absolute;
    left: 50%;
    top: 50%;
    transform: translate(-50%, -50%) rotate(45deg);
    color: #ffffff;
    font-size: 14px;
    line-height: 1;
  }
</style>
<style>
  @media (max-width: 768px) {
    #backToQFilterBtn {
      width: 32px;
      height: 32px;
      font-size: 14px;
    }
    .home-logo-control {
      display: block;
      padding: 2px 4px;
    }
    .home-logo-control img {
      height: 32px;
      width: auto;
    }
    .pilot-flyout {
      width: 236px;
      max-width: calc(100vw - 56px);
    }
    .pilot-flyout .action-grid button {
      height: 28px;
      font-size: 11px;
    }
  }
</style>
<style>
  .pilot-input {
    pointer-events: none;
  }
  .pilot-input .pilot-flyout {
    pointer-events: auto;
  }
  .pilot-input .pilot-flyout.collapsed {
    pointer-events: none;
  }
  .pilot-input .pilot-flyout.collapsed .pilot-flyout-toggle {
    pointer-events: auto;
  }
  /* Obstacles toggle hint state (off + nearby NOTAMS) */
  .left-mini-toggle-control.notams-hint .left-mini-toggle-btn {
    color: #b85c00;
    background: #fff3cd;
  }
  /* Uniform 34px sizing for all left-column controls */
  .left-mini-toggle-control,
  .center-map-control {
    border-radius: 8px;
  }
</style>
"""
        )
    )

    # 7) Inject widget for pilot drag/manual update and dynamic NOTAM source/filter
    widget_js = f"""
<script>
window.onload = function() {{
    try {{
        console.info('[NOTAM MAP] widget init start');
  var launchParams = new URLSearchParams(window.location.search || '');
  var launchedFromQFilter = (launchParams.get('src') || '').toLowerCase() === 'qfilter';
  var linkedFocusRequested = /^(1|true|yes|on)$/i.test((launchParams.get('focus') || '').trim());

  window.closeMapTab = function() {{
      if (window.opener && !window.opener.closed) {{
          try {{
              window.opener.focus();
              window.close();
              return;
          }} catch (e) {{
              console.warn('[NOTAM MAP] opener focus/close failed', e);
          }}
      }}

      if (launchedFromQFilter) {{
          window.location.href = 'Notam Q Filter.html';
          return;
      }}

      if (window.history.length > 1) {{
          window.history.back();
          return;
      }}

      if (document.referrer) {{
          window.location.href = document.referrer;
          return;
      }}

      window.location.href = 'Notam Q Filter.html';
  }};
  var map = {m.get_name()};
  var marker = {pm_js};
  var c1 = {c1_js};
  var c3 = {c3_js};
  var c100 = {c100_js};
    var obstacleLayer = {obstacle_layer_js};
        var airportLayers = {airport_layers_js};
        var airportLayerIndex = {airport_layer_index_js};
        var selectedAirportLayers = [];
        var notamsVisible = true;
    var radiusKm = {NOTAM_RADIUS_KM};
    var filteredNotams = [];
    var rawNotams = [];
    var activeSource = 'RAW';
    var linkedRealtimeNotams = [];
    var linkedRealtimeMode = false;
    var linkedRealtimeIntent = 'none';
    var linkedRealtimePayloadSource = '';
    var linkedRealtimePayloadCreatedAt = 0;
    var linkedRealtimePayloadFir = '';
    var linkedObstacleLocation = null;
    var linkedObstacleBatch = [];
    var linkedObstacleAutoOpenPending = false;
    var linkedObstacleMarker = null;
    var linkedObstacleBatchLayer = L.layerGroup().addTo(map);
    var linkedObstacleGlow = null;
    var pilotToObstacleLine = null;
    var notamDataReady = false;
    var notamDataError = '';
    var currentZoom = map.getZoom();
    var provinceCodeCache = Object.create(null);
    var refreshQueued = false;
    var pendingRefreshLatLng = null;
    var obstacleMarkers = [];
    var lastObstacleTapKey = '';
    var lastObstacleTapIndex = 0;
    var obstacleIcon = L.AwesomeMarkers.icon({{
        icon: 'exclamation-triangle',
        prefix: 'fa',
        markerColor: 'red'
    }});
    var isCompactTouchLayout = window.matchMedia && window.matchMedia('(max-width: 768px)').matches && (('ontouchstart' in window) || navigator.maxTouchPoints > 0);
        var basemapLayers = {basemap_layers_js};
    var basemapStorageKey = 'notam-map.basemap';
    var livePayloadStoragePrefix = 'fetchnotams:map:payload:';
    var liveUnfilteredPayloadStorageKey = 'fetchnotams:map:live:latest';
    var livePayloadTtlMs = 2 * 60 * 60 * 1000;
    var defaultBasemapName = {json.dumps(basemap['name'])};
    var currentBasemapName = defaultBasemapName;

    // Dial in finer zoom increments for smoother manual zooming.
    map.options.zoomSnap = 0.25;
    map.options.zoomDelta = 0.25;
    map.options.wheelPxPerZoomLevel = 140;
    if (map.scrollWheelZoom && map.scrollWheelZoom.setWheelPxPerZoomLevel) {{
        map.scrollWheelZoom.setWheelPxPerZoomLevel(140);
    }}
    if (typeof map.options.tapTolerance === 'number' && map.options.tapTolerance < 22) {{
        map.options.tapTolerance = 22;
    }}

        var zoomControl = L.control.zoom({{position:'topleft'}});
        var basemapControl = L.control.layers(basemapLayers, null, {{ position: 'topleft', collapsed: true }});
  function applyPilotMarkerVisual() {{
      var pilotIcon = L.divIcon({{
          className: 'pilot-marker-wrap',
          html: '<div class="pilot-marker-glow"></div><div class="pilot-marker-pin"><i class="fa-solid fa-user"></i></div>',
          iconSize: [36, 44],
          iconAnchor: [18, 42],
          popupAnchor: [0, -36],
          tooltipAnchor: [14, -22]
      }});
      marker.setIcon(pilotIcon);
  }}

  applyPilotMarkerVisual();

  function formatCoord(v) {{
      return Number(v).toFixed({COORD_DECIMALS});
  }}

  function toDms(deg, isLat) {{
      var abs = Math.abs(Number(deg));
      var d = Math.floor(abs);
      var mFloat = (abs - d) * 60;
      var m = Math.floor(mFloat);
      var s = ((mFloat - m) * 60).toFixed(1);
      var dir = isLat ? (deg >= 0 ? 'N' : 'S') : (deg >= 0 ? 'E' : 'W');
      return d + '\u00B0' + m + "'" + s + '"' + dir;
  }}

  function parseLatLonText(value) {{
      if (!value || typeof value !== 'string') {{
          return null;
      }}
    var m = value.trim().match(/^\\s*(-?\\d+(?:\\.\\d+)?)\\s*,\\s*(-?\\d+(?:\\.\\d+)?)\\s*$/);
      if (!m) {{
          return null;
      }}
      var lat = Number(m[1]);
      var lon = Number(m[2]);
      if (!isFinite(lat) || !isFinite(lon)) {{
          return null;
      }}
      if (lat < -90 || lat > 90 || lon < -180 || lon > 180) {{
          return null;
      }}
      return L.latLng(lat, lon);
  }}

  function isValidPilotLocation(ll) {{
      return !!(ll &&
          isFinite(ll.lat) && isFinite(ll.lng) &&
          ll.lat >= -90 && ll.lat <= 90 &&
          ll.lng >= -180 && ll.lng <= 180);
  }}

  function isZeroPilotLocation(ll) {{
      if (!isValidPilotLocation(ll)) {{
          return false;
      }}
      return Math.abs(Number(ll.lat)) < 0.000001 && Math.abs(Number(ll.lng)) < 0.000001;
  }}

  function hasUsablePilotLocation(ll) {{
      return isValidPilotLocation(ll) && !isZeroPilotLocation(ll);
  }}

  function getLinkedObstacleFromQuery() {{
      try {{
          var params = new URLSearchParams(window.location.search || '');
          var latRaw = params.get('lat') || params.get('latitude');
          var lonRaw = params.get('lon') || params.get('lng') || params.get('longitude');
          if (latRaw == null || lonRaw == null) {{
              return null;
          }}
          var lat = Number(latRaw);
          var lon = Number(lonRaw);
          if (!isFinite(lat) || !isFinite(lon)) {{
              return null;
          }}
          if (lat < -90 || lat > 90 || lon < -180 || lon > 180) {{
              return null;
          }}
          return L.latLng(lat, lon);
      }} catch (err) {{
          return null;
      }}
  }}

  function parseLinkedObstacleBatchFromQuery() {{
      try {{
          var params = new URLSearchParams(window.location.search || '');
          var values = [];
          var keys = ['markers', 'marker', 'm'];
          for (var ki = 0; ki < keys.length; ki++) {{
              var key = keys[ki];
              var list = params.getAll(key) || [];
              for (var vi = 0; vi < list.length; vi++) {{
                  if (list[vi]) {{
                      values.push(list[vi]);
                  }}
              }}
          }}

          var seen = Object.create(null);
          var out = [];

          for (var i = 0; i < values.length; i++) {{
              var chunks = String(values[i]).split(/[|;]/);
              for (var ci = 0; ci < chunks.length; ci++) {{
                  var pair = splitCoordinatePair(chunks[ci]);
                  if (!pair) {{
                      continue;
                  }}
                  var lat = Number(pair.lat);
                  var lon = Number(pair.lon);
                  if (!isFinite(lat) || !isFinite(lon)) {{
                      continue;
                  }}
                  if (lat < -90 || lat > 90 || lon < -180 || lon > 180) {{
                      continue;
                  }}
                  var keyText = lat.toFixed(6) + ',' + lon.toFixed(6);
                  if (seen[keyText]) {{
                      continue;
                  }}
                  seen[keyText] = true;
                  out.push(L.latLng(lat, lon));
              }}
          }}

          return out;
      }} catch (err) {{
          return [];
      }}
  }}

  function getLinkedRealtimeNotamsFromQuery() {{
      var params = new URLSearchParams(window.location.search || '');
      var payloadKey = (params.get('payload_key') || '').trim();
      var src = (params.get('src') || '').trim().toLowerCase();
      if (payloadKey) {{
          linkedRealtimeIntent = 'linked';
          linkedRealtimePayloadSource = 'query';
          return readLivePayloadRecords(payloadKey);
      }}
      if (src === 'fetchnotams') {{
          var latestKey = findLatestLivePayloadKey();
          if (latestKey) {{
              linkedRealtimeIntent = 'linked';
              linkedRealtimePayloadSource = 'cache';
              return readLivePayloadRecords(latestKey);
          }}
      }}
      linkedRealtimeIntent = 'none';
      linkedRealtimePayloadSource = '';
      linkedRealtimePayloadCreatedAt = 0;
      linkedRealtimePayloadFir = '';
      return [];
  }}

  function getLivePayloadMeta(payloadKey) {{
      if (!payloadKey) {{
          return {{ createdAt: 0, fir: '', ageMinutes: null }};
      }}
      try {{
          var raw = localStorage.getItem(payloadKey);
          if (!raw) {{
              return {{ createdAt: 0, fir: '', ageMinutes: null }};
          }}
          var parsed = JSON.parse(raw);
          var createdAt = Number(parsed && parsed.createdAt) || 0;
          var fir = String(parsed && parsed.fir || '').trim().toUpperCase();
          var ageMinutes = createdAt ? Math.max(0, Math.round((Date.now() - createdAt) / 60000)) : null;
          return {{
              createdAt: createdAt,
              fir: fir,
              ageMinutes: ageMinutes
          }};
      }} catch (err) {{
          return {{ createdAt: 0, fir: '', ageMinutes: null }};
      }}
  }}

  function formatLivePayloadMeta(meta) {{
      var firText = (meta && meta.fir) ? meta.fir : 'FIR n/a';
      var ageText = (meta && Number.isFinite(meta.ageMinutes)) ? (meta.ageMinutes + ' min old') : 'age n/a';
      return firText + ', ' + ageText;
  }}

  function findStartupLivePayloadKey() {{
      try {{
          var raw = localStorage.getItem(liveUnfilteredPayloadStorageKey);
          if (!raw) {{
              return '';
          }}
          var parsed = JSON.parse(raw);
          var createdAt = Number(parsed && parsed.createdAt) || 0;
          var records = Array.isArray(parsed && parsed.records) ? parsed.records : [];
          if (!records.length || !createdAt) {{
              return '';
          }}
          if (livePayloadTtlMs > 0 && (Date.now() - createdAt) > livePayloadTtlMs) {{
              return '';
          }}
          return liveUnfilteredPayloadStorageKey;
      }} catch (err) {{
          return '';
      }}
  }}

  function getStartupLiveNotamsFromCache() {{
      var startupKey = findStartupLivePayloadKey();
      if (!startupKey) {{
          return [];
      }}
      linkedRealtimeIntent = 'startup-live';
      linkedRealtimePayloadSource = 'startup';
      return readLivePayloadRecords(startupKey);
  }}

  function readLivePayloadRecords(payloadKey) {{
      linkedRealtimePayloadCreatedAt = 0;
      linkedRealtimePayloadFir = '';
      if (!payloadKey) {{
          return [];
      }}
      try {{
          var raw = localStorage.getItem(payloadKey);
          if (!raw) {{
              return [];
          }}
          var parsed = JSON.parse(raw);
          linkedRealtimePayloadCreatedAt = Number(parsed && parsed.createdAt) || 0;
          linkedRealtimePayloadFir = String(parsed && parsed.fir || '').trim().toUpperCase();
          var records = Array.isArray(parsed && parsed.records) ? parsed.records : [];
          return normalizeNotamRecords(records);
      }} catch (err) {{
          return [];
      }}
  }}

  // --- Inline FIR cache refresh ---
  var mapFetchApiBase = 'https://plan.navcanada.ca/weather/api/alpha/';
  var mapFetchProxyUrl = 'https://navcan-proxy.rontreleaven.workers.dev/?url=';
  var mapFetchProxyTimeout = 14000;
  var mapFetchLastFirKey = 'fetchnotams:lastFir';

  function mapNormalizeCode(str) {{
      return String(str || '').trim().toUpperCase().slice(0, 4);
  }}

  function mapDmsToDecimal(token, isLat) {{
      var clean = String(token || '').toUpperCase().trim();
      var dir = clean.slice(-1);
      var body = clean.slice(0, -1);
      if (isLat && !/[NS]/.test(dir)) return null;
      if (!isLat && !/[EW]/.test(dir)) return null;
      var degDigits = isLat ? 2 : 3;
      if (!/^\\d+$/.test(body)) return null;
      if (body.length !== degDigits + 2 && body.length !== degDigits + 4) return null;
      var deg = Number(body.slice(0, degDigits));
      var min = Number(body.slice(degDigits, degDigits + 2));
      var sec = body.length === degDigits + 4 ? Number(body.slice(degDigits + 2, degDigits + 4)) : 0;
      if (min >= 60 || sec >= 60) return null;
      var dd = deg + (min / 60) + (sec / 3600);
      if (dir === 'S' || dir === 'W') dd = -dd;
      return dd;
  }}

  function mapExtractCoordsFromText(text) {{
      var value = String(text || '');
      var pairRegex = /(\\d{{4,6}}[NS])\\s*(\\d{{5,7}}[EW])/gi;
      var found = [];
      var match;
      while ((match = pairRegex.exec(value)) !== null) {{
          var lat = mapDmsToDecimal((match[1] || '').toUpperCase(), true);
          var lon = mapDmsToDecimal((match[2] || '').toUpperCase(), false);
          if (lat == null || lon == null) continue;
          if (lat < -90 || lat > 90 || lon < -180 || lon > 180) continue;
          found.push({{ lat: lat, lon: lon }});
      }}
      return found;
  }}

  function mapExtractPrimaryCoord(rawText) {{
      var value = String(rawText || '');
      if (!value) return null;
      var eMatch = value.match(/E\\)\\s*([\\s\\S]*?)(?=(?:\\n|\\r\\n?)[A-Z]\\)|$)/);
      var eSection = eMatch ? String(eMatch[0] || '') : '';
      var eCoords = mapExtractCoordsFromText(eSection);
      if (eCoords.length > 0) return eCoords[0];
      var anyCoords = mapExtractCoordsFromText(value);
      return anyCoords.length > 0 ? anyCoords[0] : null;
  }}

  function mapParseTextBlock(value) {{
      if (typeof value !== 'string') return '';
      try {{
          var parsed = JSON.parse(value);
          if (parsed && typeof parsed === 'object') {{
              return parsed.raw || parsed.english || parsed.french || '';
          }}
      }} catch (e) {{ return value; }}
      return '';
  }}

  function mapParseApiResponse(payload) {{
      var arr = Array.isArray(payload && payload.data) ? payload.data : [];
      var records = [];
      for (var i = 0; i < arr.length; i++) {{
          var item = arr[i];
          if (!item || item.type !== 'notam') continue;
          var raw = mapParseTextBlock(item.text);
          if (!raw) continue;
          var coord = mapExtractPrimaryCoord(raw);
          if (!coord) continue;
          records.push({{
              lat: Number(coord.lat.toFixed(6)),
              lon: Number(coord.lon.toFixed(6)),
              start: item.startValidity || null,
              end: item.endValidity || null,
              raw: raw
          }});
      }}
      return records;
  }}

  async function mapFetchFir(firCode) {{
      var params = new URLSearchParams();
      params.append('site', firCode);
      params.append('alpha', 'notam');
      params.append('notam_choice', 'default');
      params.append('_', String(Date.now()));
      var targetUrl = mapFetchApiBase + '?' + params.toString();
      var proxiedUrl = mapFetchProxyUrl + encodeURIComponent(targetUrl);
      var controller = new AbortController();
      var timer = setTimeout(function() {{ controller.abort(); }}, mapFetchProxyTimeout);
      try {{
          var res = await fetch(proxiedUrl, {{ method: 'GET', signal: controller.signal, cache: 'no-store', credentials: 'omit' }});
          clearTimeout(timer);
          if (!res.ok) throw new Error('HTTP ' + res.status);
          return await res.json();
      }} catch (err) {{
          clearTimeout(timer);
          throw err;
      }}
  }}

  async function refreshFirCache(firCode) {{
      var statusEl = document.getElementById('refreshFirStatus');
      var fetchBtn = document.getElementById('refreshFirFetchBtn');
      firCode = mapNormalizeCode(firCode);
      if (!firCode || firCode.length < 3) {{
          if (statusEl) statusEl.textContent = 'Enter a valid FIR code (e.g. CZYZ).';
          return;
      }}
      if (fetchBtn) fetchBtn.disabled = true;
      if (statusEl) {{ statusEl.textContent = 'Fetching ' + firCode + '...'; statusEl.style.color = '#555'; }}
      try {{
          var payload = await mapFetchFir(firCode);
          var records = mapParseApiResponse(payload);
          if (!records.length) {{
              if (statusEl) {{ statusEl.textContent = 'No mappable NOTAMs found for ' + firCode + '.'; statusEl.style.color = '#b07d00'; }}
              if (fetchBtn) fetchBtn.disabled = false;
              return;
          }}
          var livePayload = {{ createdAt: Date.now(), records: records, scope: 'live-unfiltered', fir: firCode }};
          localStorage.setItem(liveUnfilteredPayloadStorageKey, JSON.stringify(livePayload));
          localStorage.setItem(mapFetchLastFirKey, firCode);
          if (statusEl) {{ statusEl.textContent = '\\u2713 ' + records.length + ' NOTAMs from ' + firCode + '. Applying...'; statusEl.style.color = '#2d6a2d'; }}
          setTimeout(function() {{
              linkedRealtimeNotams = getStartupLiveNotamsFromCache();
              linkedRealtimeMode = linkedRealtimeNotams.length > 0;
              updateSourceDisplay();
              scheduleRefreshObstacles(marker.getLatLng());
              hideRefreshFirPanel();
          }}, 700);
      }} catch (err) {{
          if (statusEl) {{ statusEl.textContent = 'Fetch failed: ' + (err && err.message ? err.message : 'unknown'); statusEl.style.color = '#c0392b'; }}
          if (fetchBtn) fetchBtn.disabled = false;
      }}
  }}

  function showRefreshFirPanel() {{
      var panel = document.getElementById('refreshFirPanel');
      if (!panel) return;
      var lastFir = localStorage.getItem(mapFetchLastFirKey) || 'CZYZ';
      var input = document.getElementById('refreshFirInput');
      if (input && !input.value) input.value = lastFir;
      panel.style.display = 'block';
      var statusEl = document.getElementById('refreshFirStatus');
      if (statusEl) statusEl.textContent = '';
      var fetchBtn = document.getElementById('refreshFirFetchBtn');
      if (fetchBtn) fetchBtn.disabled = false;
      if (input) setTimeout(function() {{ input.focus(); }}, 50);
  }}

  function hideRefreshFirPanel() {{
      var panel = document.getElementById('refreshFirPanel');
      if (panel) panel.style.display = 'none';
  }}

  function findLatestLivePayloadKey() {{
      try {{
          var now = Date.now();
          var latestKey = '';
          var latestTs = 0;
          for (var i = 0; i < localStorage.length; i++) {{
              var key = localStorage.key(i);
              if (!key || key.indexOf(livePayloadStoragePrefix) !== 0) {{
                  continue;
              }}
              var raw = localStorage.getItem(key);
              if (!raw) {{
                  continue;
              }}
              var parsed = null;
              try {{
                  parsed = JSON.parse(raw);
              }} catch (_err) {{
                  continue;
              }}
              var createdAt = Number(parsed && parsed.createdAt) || 0;
              var records = Array.isArray(parsed && parsed.records) ? parsed.records : [];
              if (!records.length) {{
                  continue;
              }}
              if (!createdAt) {{
                  continue;
              }}
              if (livePayloadTtlMs > 0 && now - createdAt > livePayloadTtlMs) {{
                  continue;
              }}
              if (createdAt > latestTs) {{
                  latestTs = createdAt;
                  latestKey = key;
              }}
          }}
          return latestKey;
      }} catch (err) {{
          return '';
      }}
  }}

  function renderLinkedObstacleBatchMarkers() {{
      if (!linkedObstacleBatchLayer) {{
          return;
      }}

      linkedObstacleBatchLayer.clearLayers();
      if (!linkedObstacleBatch.length) {{
          return;
      }}

      for (var i = 0; i < linkedObstacleBatch.length; i++) {{
          var ll = linkedObstacleBatch[i];
          if (linkedObstacleLocation &&
              Math.abs(ll.lat - linkedObstacleLocation.lat) < 0.0000005 &&
              Math.abs(ll.lng - linkedObstacleLocation.lng) < 0.0000005) {{
              continue;
          }}

          var mk = L.circleMarker([ll.lat, ll.lng], {{
              radius: 7,
              color: '#ff7a00',
              weight: 2,
              fillColor: '#ffb74d',
              fillOpacity: 0.88
          }}).addTo(linkedObstacleBatchLayer);

          var idx = i + 1;
          mk.bindTooltip('Obstacle Alert ' + idx, {{ direction: 'top' }});
          mk.bindPopup(
              "<div class='notam-popup'>" +
              "<div class='notam-title'>Obstacle Alert " + idx + "</div>" +
              "<div><span class='notam-label'>Position:</span> " + formatCoord(ll.lat) + ', ' + formatCoord(ll.lng) + "</div>" +
              "</div>",
              {{ maxWidth: 320 }}
          );
      }}
  }}

  function fitMapToLinkedObstacleBatch() {{
      if (!linkedObstacleBatch.length) {{
          return;
      }}

      var bounds = L.latLngBounds(linkedObstacleBatch.map(function(ll) {{
          return [ll.lat, ll.lng];
      }}));

      if (!bounds.isValid()) {{
          return;
      }}

      map.fitBounds(bounds.pad(0.15), {{ padding: [34, 34], maxZoom: 11 }});
  }}

  function appendLinkedSetToCountText() {{
      var countText = document.getElementById('obstacleCountText');
      if (!countText) {{
          return;
      }}

      var base = countText.textContent || '';
      base = base.replace(/\\s*\\|\\s*Linked set:\\s*\\d+\\s*$/i, '');
      if (linkedObstacleBatch.length > 1) {{
          countText.textContent = base + ' | Linked set: ' + linkedObstacleBatch.length;
      }} else {{
          countText.textContent = base;
      }}
  }}

  function updatePilotObstacleContext(pilotLL) {{
      if (!linkedObstacleLocation || !pilotLL) {{
          if (linkedObstacleGlow && map.hasLayer(linkedObstacleGlow)) {{
              map.removeLayer(linkedObstacleGlow);
          }}
          if (linkedObstacleMarker && map.hasLayer(linkedObstacleMarker)) {{
              map.removeLayer(linkedObstacleMarker);
          }}
          if (pilotToObstacleLine && map.hasLayer(pilotToObstacleLine)) {{
              map.removeLayer(pilotToObstacleLine);
          }}
          appendLinkedSetToCountText();
          return;
      }}

      if (!linkedObstacleGlow) {{
          linkedObstacleGlow = L.circleMarker([linkedObstacleLocation.lat, linkedObstacleLocation.lng], {{
              radius: 20,
              color: '#ff9800',
              weight: 2,
              fillColor: '#ff9800',
              fillOpacity: 0.20,
              interactive: false
          }});
      }} else {{
          linkedObstacleGlow.setLatLng(linkedObstacleLocation);
      }}
      if (!map.hasLayer(linkedObstacleGlow)) {{
          linkedObstacleGlow.addTo(map);
      }}

      if (!linkedObstacleMarker) {{
          linkedObstacleMarker = L.marker([linkedObstacleLocation.lat, linkedObstacleLocation.lng], {{
              icon: L.AwesomeMarkers.icon({{
                  icon: 'triangle-exclamation',
                  prefix: 'fa',
                  markerColor: 'orange'
              }}),
              zIndexOffset: 1950
          }});
      }} else {{
          linkedObstacleMarker.setLatLng(linkedObstacleLocation);
      }}
      if (!map.hasLayer(linkedObstacleMarker)) {{
          linkedObstacleMarker.addTo(map);
      }}
      linkedObstacleMarker.bindTooltip('Obstacle Alert', {{ direction: 'top' }});

      var path = [[pilotLL.lat, pilotLL.lng], [linkedObstacleLocation.lat, linkedObstacleLocation.lng]];
      if (!pilotToObstacleLine) {{
          pilotToObstacleLine = L.polyline(path, {{
              color: '#ff7a00',
              weight: 4,
              opacity: 0.95,
              dashArray: '8,7'
          }});
      }} else {{
          pilotToObstacleLine.setLatLngs(path);
      }}
      if (!map.hasLayer(pilotToObstacleLine)) {{
          pilotToObstacleLine.addTo(map);
      }}

      var km = haversineKm(pilotLL.lat, pilotLL.lng, linkedObstacleLocation.lat, linkedObstacleLocation.lng);
      var nm = km / 1.852;
      var distanceBadge = '<span style="background:rgba(198,40,40,0.95);color:#fff;padding:3px 8px;border-radius:12px;font-weight:700;font-size:11px;box-shadow:0 0 10px rgba(198,40,40,0.55);">' + km.toFixed(1) + ' km</span>';
      if (!pilotToObstacleLine.getTooltip()) {{
          pilotToObstacleLine.bindTooltip(distanceBadge, {{ permanent: true, direction: 'center', opacity: 1 }});
      }} else {{
          pilotToObstacleLine.setTooltipContent(distanceBadge);
      }}

      // Try to find the matching NOTAM item for full detail popup
      var matchedItem = null;
      var searchPool = getActiveNotams ? getActiveNotams() : [];
      for (var si = 0; si < searchPool.length; si++) {{
          var sp = searchPool[si];
          if (Math.abs(sp.lat - linkedObstacleLocation.lat) < 0.0002 &&
              Math.abs(sp.lon - linkedObstacleLocation.lng) < 0.0002) {{
              matchedItem = sp;
              break;
          }}
      }}
      var distHeader = '<div class="notam-popup"><div class="notam-title">Obstacle Alert</div>' +
          '<div><span class="notam-label">Distance from Pilot:</span> ' + km.toFixed(1) + ' km (' + nm.toFixed(1) + ' NM)</div>' +
          '<hr style="margin:6px 0">';
      var popupBody = matchedItem
          ? buildObstaclePopupHtml(matchedItem).replace('<div class="notam-popup">', '').replace('</div>\\n</div>', '').replace(/<\\/div>$/, '')
          : '<div><span class="notam-label">Position:</span> ' + formatCoord(linkedObstacleLocation.lat) + ', ' + formatCoord(linkedObstacleLocation.lng) + '</div>';
      var linkedPopupWasOpen = !!(linkedObstacleMarker.isPopupOpen && linkedObstacleMarker.isPopupOpen());
      linkedObstacleMarker.bindPopup(distHeader + popupBody + '</div>', {{
          maxWidth: 420,
          autoClose: false,
          closeOnClick: false
      }});
      if (linkedPopupWasOpen) {{
          linkedObstacleMarker.openPopup();
      }}
      if (linkedObstacleAutoOpenPending && (notamDataReady || !!notamDataError)) {{
          linkedObstacleMarker.openPopup();
          linkedObstacleAutoOpenPending = false;
      }}

      var countText = document.getElementById('obstacleCountText');
      if (countText) {{
          var base = countText.textContent || '';
          base = base.replace(/\\s*\\|\\s*Focus:\\s*[0-9.]+\\s*km\\s*\\([0-9.]+\\s*NM\\)\\s*$/i, '');
          base = base.replace(/\\s*\\|\\s*Target:\\s*[0-9.]+\\s*km\\s*\\([0-9.]+\\s*NM\\)\\s*$/i, '');
          countText.textContent = base + ' | Focus: ' + km.toFixed(1) + ' km (' + nm.toFixed(1) + ' NM)';
      }}
  }}

  function getStoredPilotLocation() {{
      try {{
          var dd = localStorage.getItem('pilotLocationDD') || '';
          var parsedDd = parseLatLonText(dd);
          if (hasUsablePilotLocation(parsedDd)) {{
              return parsedDd;
          }}

          var lat = Number(localStorage.getItem('pilotLatitude'));
          var lon = Number(localStorage.getItem('pilotLongitude'));
          if (isFinite(lat) && isFinite(lon) && lat >= -90 && lat <= 90 && lon >= -180 && lon <= 180) {{
              var storedLl = L.latLng(lat, lon);
              if (hasUsablePilotLocation(storedLl)) {{
                  return storedLl;
              }}
          }}
      }} catch (err) {{
          console.warn('[NOTAM MAP] unable to read pilot location from localStorage', err);
      }}
      return null;
  }}

  function savePilotLocationToStorage(ll, source) {{
      try {{
          var lat = Number(ll.lat);
          var lon = Number(ll.lng);
          var latShort = lat.toFixed({COORD_DECIMALS});
          var lonShort = lon.toFixed({COORD_DECIMALS});
          localStorage.setItem('pilotLocationDD', latShort + ', ' + lonShort);
          localStorage.setItem('pilotLocationDMS', toDms(lat, true) + ', ' + toDms(lon, false));
          localStorage.setItem('pilotLatitude', latShort);
          localStorage.setItem('pilotLongitude', lonShort);
          localStorage.setItem('pilotLocationSource', source || 'notams-map');
      }} catch (err) {{
          console.warn('[NOTAM MAP] unable to write pilot location to localStorage', err);
      }}
  }}

  function updatePilotDisplay(ll) {{
      var latInput = document.getElementById('pLat');
      var lonInput = document.getElementById('pLon');
      var pilotText = document.getElementById('currentPilotText');
      if (latInput && lonInput) {{
          latInput.value = formatCoord(ll.lat);
          lonInput.value = formatCoord(ll.lng);
      }}
      if (pilotText) {{
          pilotText.textContent = 'Current Pilot Location: ' + formatCoord(ll.lat) + ', ' + formatCoord(ll.lng);
      }}
  }}

  function updateBasemapDisplay() {{
      var basemapText = document.getElementById('currentBasemapText');
      if (basemapText) {{
          basemapText.textContent = 'Basemap: ' + (currentBasemapName || 'Unknown');
      }}
  }}

  function anySelectedAirportLayerVisible() {{
      for (var i = 0; i < selectedAirportLayers.length; i++) {{
          if (map.hasLayer(selectedAirportLayers[i])) {{
              return true;
          }}
      }}
      return false;
  }}

  function setAllAirportLayersVisible(visible) {{
      for (var i = 0; i < airportLayers.length; i++) {{
          var lyr = airportLayers[i];
          if (!lyr) {{
              continue;
          }}
          if (visible) {{
              if (!map.hasLayer(lyr)) {{
                  map.addLayer(lyr);
              }}
          }} else if (map.hasLayer(lyr)) {{
              map.removeLayer(lyr);
          }}
      }}
  }}

  function setSelectedAirportLayersVisible(visible) {{
      if (visible) {{
          for (var i = 0; i < selectedAirportLayers.length; i++) {{
              var lyr = selectedAirportLayers[i];
              if (lyr && !map.hasLayer(lyr)) {{
                  map.addLayer(lyr);
              }}
          }}
      }} else {{
          setAllAirportLayersVisible(false);
      }}
  }}

  function normalizeProvinceCode(candidate) {{
      if (!candidate) {{
          return null;
      }}
      var text = String(candidate).trim();
      if (!text) {{
          return null;
      }}
      if (/^CA-[A-Z]{{2}}$/.test(text.toUpperCase())) {{
          return text.toUpperCase();
      }}
      if (/^[A-Z]{{2}}$/.test(text.toUpperCase())) {{
          return 'CA-' + text.toUpperCase();
      }}

      var byName = {{
          'alberta': 'CA-AB',
          'british columbia': 'CA-BC',
          'manitoba': 'CA-MB',
          'new brunswick': 'CA-NB',
          'newfoundland and labrador': 'CA-NL',
          'nova scotia': 'CA-NS',
          'northwest territories': 'CA-NT',
          'nunavut': 'CA-NU',
          'ontario': 'CA-ON',
          'prince edward island': 'CA-PE',
          'quebec': 'CA-QC',
          'saskatchewan': 'CA-SK',
          'yukon': 'CA-YT'
      }};
      return byName[text.toLowerCase()] || null;
  }}

  function applyAirportDefaultsForProvince(provinceCode) {{
      var code = normalizeProvinceCode(provinceCode);
      var typeMap = code ? airportLayerIndex[code] : null;
      selectedAirportLayers = [];

      if (typeMap) {{
          for (var atype in typeMap) {{
              if (!Object.prototype.hasOwnProperty.call(typeMap, atype)) {{
                  continue;
              }}
              if (String(atype).toLowerCase() === 'closed') {{
                  continue;
              }}
              selectedAirportLayers.push(typeMap[atype]);
          }}
      }}

      setAllAirportLayersVisible(false);
      setSelectedAirportLayersVisible(true);
      updateAirportsToggleLabel();
  }}

  async function detectProvinceCodeForLocation(ll) {{
      try {{
          var url = 'https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=' + encodeURIComponent(ll.lat) + '&lon=' + encodeURIComponent(ll.lng) + '&zoom=5&addressdetails=1';
          var resp = await fetch(url, {{ cache: 'no-store' }});
          if (!resp.ok) {{
              return null;
          }}
          var payload = await resp.json();
          var addr = (payload && payload.address) ? payload.address : {{}};
          return (
              normalizeProvinceCode(addr['ISO3166-2-lvl4']) ||
              normalizeProvinceCode(addr['ISO3166-2-lvl3']) ||
              normalizeProvinceCode(addr.state_code) ||
              normalizeProvinceCode(addr.state) ||
              normalizeProvinceCode(addr.province) ||
              normalizeProvinceCode(addr.region)
          );
      }} catch (err) {{
          console.warn('[NOTAM MAP] province detection failed', err);
          return null;
      }}
  }}

  async function applyAirportDefaultsFromLocation(ll) {{
      var code = await detectProvinceCodeForLocation(ll);
      if (code && airportLayerIndex[code]) {{
          applyAirportDefaultsForProvince(code);
          return;
      }}

      if (airportLayerIndex['CA-ON']) {{
          applyAirportDefaultsForProvince('CA-ON');
          return;
      }}

      for (var fallbackCode in airportLayerIndex) {{
          if (Object.prototype.hasOwnProperty.call(airportLayerIndex, fallbackCode)) {{
              applyAirportDefaultsForProvince(fallbackCode);
              return;
          }}
      }}
  }}

  function updateAirportsToggleLabel() {{
      var txt = document.getElementById('airportsToggleText');
      var ctl = document.getElementById('airportsToggleCtl');
      var active = anySelectedAirportLayerVisible();

      if (txt) {{
          txt.textContent = active ? 'Hide Airports Layer' : 'Show Airports Layer';
      }}

      if (ctl) {{
          ctl.classList.toggle('inactive', !active);
          ctl.title = active ? 'Hide Airports Layer' : 'Show Airports Layer';
      }}
  }}

  function setNotamsVisible(visible) {{
      notamsVisible = !!visible;
      if (notamsVisible) {{
          if (!map.hasLayer(obstacleLayer)) {{
              map.addLayer(obstacleLayer);
          }}
      }} else if (map.hasLayer(obstacleLayer)) {{
          map.removeLayer(obstacleLayer);
      }}
      updateNotamsToggleVisual();
  }}

  function updateNotamsToggleVisual() {{
      var ctl = document.getElementById('notamsToggleCtl');
      if (!ctl) return;
      var count = window._notamObstacleCount || 0;
      ctl.classList.remove('inactive', 'notams-hint');
      if (!notamsVisible && count > 0) {{
          ctl.classList.add('notams-hint'); // amber: obstacles exist while toggle is off
      }} else if (!notamsVisible) {{
          ctl.classList.add('inactive'); // grey: toggle off and no nearby obstacles
      }}
      // when toggle is on, keep the same normal look as Airports toggle
  }}

  function applyBasemapByName(name) {{
      if (!name || !basemapLayers[name]) {{
          return false;
      }}

      for (var layerName in basemapLayers) {{
          if (!Object.prototype.hasOwnProperty.call(basemapLayers, layerName)) {{
              continue;
          }}
          var layer = basemapLayers[layerName];
          if (map.hasLayer(layer)) {{
              map.removeLayer(layer);
          }}
      }}

      map.addLayer(basemapLayers[name]);
      currentBasemapName = name;
      updateBasemapDisplay();
      return true;
  }}

  function getStoredBasemapName() {{
      try {{
          return localStorage.getItem(basemapStorageKey);
      }} catch (err) {{
          console.warn('[NOTAM MAP] unable to read basemap from localStorage', err);
          return null;
      }}
  }}

  function setStoredBasemapName(name) {{
      try {{
          localStorage.setItem(basemapStorageKey, name);
      }} catch (err) {{
          console.warn('[NOTAM MAP] unable to write basemap to localStorage', err);
      }}
  }}

  function splitCoordinatePair(value) {{
      if (typeof value !== 'string') {{
          return null;
      }}
      var parts = value.split(',');
      if (parts.length < 2) {{
          return null;
      }}
      var lat = parseFloat(parts[0]);
      var lon = parseFloat(parts[1]);
      if (!isFinite(lat) || !isFinite(lon)) {{
          return null;
      }}
      return {{ lat: lat, lon: lon }};
  }}

  function normalizeNotamRecords(records) {{
      if (!Array.isArray(records)) {{
          return [];
      }}

      var normalized = [];
      for (var i = 0; i < records.length; i++) {{
          var rec = records[i] || {{}};
          var start = rec.start || rec.startValidity || null;
          var end = rec.end || rec.endValidity || null;
          var rawHtml = rec.rawHtml || '';

          if (!rawHtml && rec.raw) {{
              rawHtml = escapeHtml(rec.raw).replace(/\\n/g, '<br>');
          }}

          if (isFinite(rec.lat) && isFinite(rec.lon)) {{
              normalized.push({{
                  lat: Number(rec.lat),
                  lon: Number(rec.lon),
                  start: start,
                  end: end,
                  rawHtml: rawHtml
              }});
              continue;
          }}

          var coords = Array.isArray(rec.coordinates_dd) ? rec.coordinates_dd : [];
          for (var c = 0; c < coords.length; c++) {{
              var pair = splitCoordinatePair(coords[c]);
              if (!pair) {{
                  continue;
              }}
              normalized.push({{
                  lat: pair.lat,
                  lon: pair.lon,
                  start: start,
                  end: end,
                  rawHtml: rawHtml
              }});
          }}
      }}
      return normalized;
  }}

  async function fetchNotamJson(path) {{
      var res = await fetch(path, {{ cache: 'no-store' }});
      if (!res.ok) {{
          throw new Error('HTTP ' + res.status + ' for ' + path);
      }}
      return res.json();
  }}

  async function loadNotamData() {{
      try {{
          var results = await Promise.all([
              fetchNotamJson('data/notams/All_CA.json'),
              fetchNotamJson('data/notams/All_CA_raw.json')
          ]);

          filteredNotams = normalizeNotamRecords(results[0]);
          rawNotams = normalizeNotamRecords(results[1]);
          notamDataReady = true;
          notamDataError = '';
      }} catch (err) {{
          notamDataReady = false;
          notamDataError = (err && err.message) ? err.message : 'Unknown NOTAM load error';
          filteredNotams = [];
          rawNotams = [];
      }}
  }}

  function radiusLabel() {{
      var rounded = Math.round(radiusKm * 10) / 10;
      return Number.isInteger(rounded) ? String(rounded) : String(rounded);
  }}

  function updateRadiusDisplay() {{
      var radiusInput = document.getElementById('radiusKmInput');
      var radiusInfo = document.getElementById('radiusInfoText');
      if (radiusInput) {{
          radiusInput.value = radiusLabel();
      }}
      if (radiusInfo) {{
          radiusInfo.textContent = 'NOTAM Radius: ' + radiusLabel() + ' km';
      }}
  }}

  function applyNotamRadius(nextRadiusKm) {{
      radiusKm = nextRadiusKm;
      c100.setRadius(radiusKm * 1000);
      if (c100.getPopup && c100.getPopup()) {{
          c100.setPopupContent(radiusLabel() + ' km NOTAM filter radius');
      }}
      c100Touch.setRadius(radiusKm * 1000);
      c100Touch.bindPopup(radiusLabel() + ' km NOTAM filter radius');
      updateRadiusDisplay();
      scheduleRefreshObstacles(marker.getLatLng());
  }}

  function centerMapToPilotRadius() {{
      var bounds = c100.getBounds ? c100.getBounds() : null;
      if (!bounds) {{
          map.setView(marker.getLatLng(), currentZoom);
          return;
      }}
      map.fitBounds(bounds, {{ padding: [30, 30] }});
  }}

  function escapeHtml(txt) {{
      var d = document.createElement('div');
      d.textContent = txt == null ? '' : String(txt);
      return d.innerHTML;
  }}

  function haversineKm(lat1, lon1, lat2, lon2) {{
      var toRad = function(v) {{ return v * Math.PI / 180; }};
      var dLat = toRad(lat2 - lat1);
      var dLon = toRad(lon2 - lon1);
      var p1 = toRad(lat1);
      var p2 = toRad(lat2);
      var a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
              Math.cos(p1) * Math.cos(p2) * Math.sin(dLon / 2) * Math.sin(dLon / 2);
      return 2 * 6371.0 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  }}

  function getActiveNotams() {{
      if (linkedRealtimeMode && linkedRealtimeNotams.length) {{
          return linkedRealtimeNotams;
      }}
      return activeSource === 'RAW' ? rawNotams : filteredNotams;
  }}

  function scheduleRefreshObstacles(ll) {{
      pendingRefreshLatLng = ll;
      if (refreshQueued) {{
          return;
      }}
      refreshQueued = true;
      requestAnimationFrame(function() {{
          refreshQueued = false;
          var target = pendingRefreshLatLng || marker.getLatLng();
          pendingRefreshLatLng = null;
          refreshObstacles(target);
      }});
  }}

  function getLikelyNotamCandidates(allNotams, ll, kmRadius) {{
      var latPad = kmRadius / 110.574;
      var lonDivisor = Math.max(0.25, Math.cos(ll.lat * Math.PI / 180) * 111.320);
      var lonPad = kmRadius / lonDivisor;
      var minLat = ll.lat - latPad;
      var maxLat = ll.lat + latPad;
      var minLon = ll.lng - lonPad;
      var maxLon = ll.lng + lonPad;
      var candidates = [];

      for (var i = 0; i < allNotams.length; i++) {{
          var item = allNotams[i];
          if (item.lat < minLat || item.lat > maxLat || item.lon < minLon || item.lon > maxLon) {{
              continue;
          }}
          candidates.push(item);
      }}
      return candidates;
  }}

  function buildObstaclePopupHtml(item) {{
      return "<div class='notam-popup'>" +
          "<div class='notam-title'>Obstacle Alert</div>" +
          "<div><span class='notam-label'>Start:</span> " + escapeHtml(item.start || 'N/A') + "</div>" +
          "<div><span class='notam-label'>End:</span> " + escapeHtml(item.end || 'N/A') + "</div>" +
          "<hr style='margin:6px 0'>" +
          "<div class='notam-raw'>" + (item.rawHtml || '') + "</div>" +
          "</div>";
  }}

  function updateSourceDisplay() {{
      var sourceText = document.getElementById('notamSourceText');
      var sourceBtn = document.getElementById('sourceBtn');
      var liveText = document.getElementById('livePayloadText');
      if (sourceText) {{
          if (linkedRealtimeMode && linkedRealtimeNotams.length) {{
              var liveLabel = 'LIVE (payload)';
              if (linkedRealtimeIntent === 'startup-live') {{
                  liveLabel = 'LIVE (startup)';
              }} else if (linkedRealtimePayloadSource === 'cache') {{
                  liveLabel = 'LIVE (cached)';
              }}
              sourceText.textContent = 'NOTAM Src: ' + liveLabel;
              sourceText.style.color = '#0b5ea8';
          }} else {{
              sourceText.textContent = 'NOTAM Src: JSON (' + activeSource + ')';
              sourceText.style.color = activeSource === 'RAW' ? 'green' : 'red';
          }}
      }}
      if (liveText) {{
          if (linkedRealtimeMode && linkedRealtimeNotams.length) {{
              var activeMeta = {{
                  fir: linkedRealtimePayloadFir,
                  ageMinutes: linkedRealtimePayloadCreatedAt ? Math.max(0, Math.round((Date.now() - linkedRealtimePayloadCreatedAt) / 60000)) : null
              }};
              liveText.textContent = linkedRealtimeIntent === 'startup-live'
                  ? ('Live payload: active (startup cache) | ' + formatLivePayloadMeta(activeMeta))
                  : ('Live payload: active (linked) | ' + formatLivePayloadMeta(activeMeta));
              liveText.style.color = '#0b5ea8';
          }} else {{
              var startupKey = findStartupLivePayloadKey();
              if (startupKey) {{
                  var startupMeta = getLivePayloadMeta(startupKey);
                  liveText.textContent = 'Live payload: available (open live) | ' + formatLivePayloadMeta(startupMeta);
                  liveText.style.color = '#8a6d3b';
              }} else {{
                  liveText.textContent = 'Live payload: none (open FetchNotams)';
                  liveText.style.color = '#6c757d';
              }}
          }}
      }}
      if (sourceBtn) {{
          sourceBtn.disabled = !!(linkedRealtimeMode && linkedRealtimeNotams.length);
          sourceBtn.textContent = sourceBtn.disabled ? 'Linked Live View' : 'Switch Filter Group';
      }}
  }}

  function refreshObstacles(ll) {{
      obstacleLayer.clearLayers();
      obstacleMarkers = [];
      lastObstacleTapKey = '';
      lastObstacleTapIndex = 0;
      var countText = document.getElementById('obstacleCountText');

      var usingLinkedRealtime = !!(linkedRealtimeMode && linkedRealtimeNotams.length);
      var bypassRadius = usingLinkedRealtime && linkedRealtimeIntent === 'linked';
      if (!usingLinkedRealtime && !notamDataReady) {{
          if (countText) {{
              countText.textContent = notamDataError ? ('NOTAM load failed: ' + notamDataError) : 'Loading NOTAM data...';
          }}
          return;
      }}

      var activeNotams = getActiveNotams();
      var candidates = bypassRadius ? activeNotams : getLikelyNotamCandidates(activeNotams, ll, radiusKm);
      var shownCount = 0;

      for (var i = 0; i < candidates.length; i++) {{
          var item = candidates[i];
          if (!bypassRadius) {{
              var km = haversineKm(ll.lat, ll.lng, item.lat, item.lon);
              if (km > radiusKm) {{
                  continue;
              }}
          }}

          shownCount += 1;
          var obstacleMarker = L.marker([item.lat, item.lon], {{
              icon: obstacleIcon,
              riseOnHover: true,
              keyboard: false
          }})
          .bindTooltip('Obstacle')
          .bindPopup(buildObstaclePopupHtml(item), {{ maxWidth: 420 }})
          .addTo(obstacleLayer);

          obstacleMarker.on('click touchstart', function(ev) {{
              this.setZIndexOffset(4000);
              this.openPopup();
              if (ev) {{
                  if (ev.originalEvent) {{
                      ev.originalEvent.preventDefault();
                      ev.originalEvent.stopPropagation();
                  }}
              }}
          }});
          obstacleMarkers.push(obstacleMarker);
      }}

      if (countText) {{
          countText.textContent = bypassRadius
              ? ('Obstacle Alerts (linked): ' + shownCount)
              : ('Obstacles (' + radiusLabel() + ' km): ' + shownCount);
      }}
      window._notamObstacleCount = shownCount;
      updateNotamsToggleVisual();
      updatePilotObstacleContext(ll);
      appendLinkedSetToCountText();
  }}

  function applyPilotLocation(ll, shouldCenter) {{
      marker.setLatLng(ll).openPopup();
      c1.setLatLng(ll); c3.setLatLng(ll); c100.setLatLng(ll);
      c1Touch.setLatLng(ll); c3Touch.setLatLng(ll); c100Touch.setLatLng(ll);
      marker.setPopupContent("Pilot<br>Lat: " + ll.lat.toFixed({COORD_DECIMALS}) + "<br>Lon: " + ll.lng.toFixed({COORD_DECIMALS}));
      savePilotLocationToStorage(ll, 'notams-map');
      if (shouldCenter) {{
          centerMapToPilotRadius();
      }}
      scheduleRefreshObstacles(ll);
      updatePilotDisplay(ll);
      updatePilotLocationPromptState(ll);
      updatePilotObstacleContext(ll);
  }}

  function closeRingPopups() {{
      c1Touch.closePopup();
      c3Touch.closePopup();
      c100Touch.closePopup();
  }}

  function disableBaseCircleInteractions(circle) {{
      // Disable Leaflet-level interactivity (works for both canvas and SVG renderers)
      circle.options.interactive = false;
      if (circle.unbindPopup) {{
          circle.unbindPopup();
      }}
      if (circle.off) {{
          circle.off();
      }}
      // For SVG renderer: suppress browser-level pointer events on the path element
      if (circle._path) {{
          circle._path.style.pointerEvents = 'none';
      }}
  }}

  function createCircleTouchTarget(circle, popupText, strokeWeight) {{
      var target = L.circle(circle.getLatLng(), {{
          radius: circle.getRadius(),
          color: '#000',
          opacity: 0,
          weight: strokeWeight,
          fill: false,
          interactive: true,
          bubblingMouseEvents: false
      }}).addTo(map);

      target.bindPopup(popupText, {{ autoClose: false, closeOnClick: false }});
      target.on('mouseover', function() {{
          target.openPopup();
      }});
      target.on('mouseout', function() {{
          target.closePopup();
      }});
      target.on('click touchstart', function(ev) {{
          if (ev && ev.originalEvent) {{
              ev.originalEvent.preventDefault();
              ev.originalEvent.stopPropagation();
          }}
          closeRingPopups();
          target.openPopup();
      }});
      target.on('touchend', function(ev) {{
          if (ev && ev.originalEvent) {{
              ev.originalEvent.preventDefault();
              ev.originalEvent.stopPropagation();
          }}
      }});
      return target;
  }}

  function openNearbyObstaclePopup(containerPoint) {{
      if (!containerPoint || !obstacleMarkers.length) {{
          return false;
      }}
      var candidates = [];
      var pixelThreshold = isCompactTouchLayout ? 28 : 18;

      for (var i = 0; i < obstacleMarkers.length; i++) {{
          var obstacleMarker = obstacleMarkers[i];
          var point = map.latLngToContainerPoint(obstacleMarker.getLatLng());
          var dx = point.x - containerPoint.x;
          var dy = point.y - containerPoint.y;
          var distance = Math.sqrt(dx * dx + dy * dy);
          if (distance <= pixelThreshold) {{
              candidates.push({{ marker: obstacleMarker, distance: distance }});
          }}
      }}

      if (!candidates.length) {{
          lastObstacleTapKey = '';
          lastObstacleTapIndex = 0;
          return false;
      }}

      candidates.sort(function(a, b) {{
          return a.distance - b.distance;
      }});

      var tapKey = candidates.map(function(entry) {{
          var ll = entry.marker.getLatLng();
          return ll.lat.toFixed(6) + ',' + ll.lng.toFixed(6);
      }}).join('|');

      if (tapKey !== lastObstacleTapKey) {{
          lastObstacleTapKey = tapKey;
          lastObstacleTapIndex = 0;
      }} else {{
          lastObstacleTapIndex = (lastObstacleTapIndex + 1) % candidates.length;
      }}

      var chosenMarker = candidates[lastObstacleTapIndex].marker;
      chosenMarker.setZIndexOffset(4000);
      chosenMarker.openPopup();
      return true;
  }}

  var c1Touch = createCircleTouchTarget(c1, '1 NM (1.9 km) radius', 34);
  var c3Touch = createCircleTouchTarget(c3, '3 NM (5.6 km) radius', 34);
  var c100Touch = createCircleTouchTarget(c100, radiusLabel() + ' km NOTAM filter radius', 18);
  disableBaseCircleInteractions(c1);
  disableBaseCircleInteractions(c3);
  disableBaseCircleInteractions(c100);

    map.on('click touchend', function(e) {{
            closeRingPopups();
            if (e && e.containerPoint) {{
                openNearbyObstaclePopup(e.containerPoint);
            }}
    }});

  map.on('zoomend', function() {{
      currentZoom = map.getZoom();
  }});

  marker.setZIndexOffset(2000);
  marker.dragging.enable();
  marker.on('dragend', function(e) {{
      var ll = e.target.getLatLng();
      applyPilotLocation(ll, false);
  }});

  var homeCtl = L.control({{position:'bottomright'}});
  homeCtl.onAdd = function() {{
      var d = L.DomUtil.create('div', 'home-logo-control');
      L.DomEvent.disableClickPropagation(d);
      d.innerHTML = '<a href="index.html" title="Home"><picture><source srcset="assets/img/logo_25.svg" type="image/svg+xml"><img src="assets/img/logo.png" alt="Home"></picture></a>';
      return d;
  }};
  homeCtl.addTo(map);

  var centerMapCtl = L.control({{position:'topleft'}});
  centerMapCtl.onAdd = function() {{
      var d = L.DomUtil.create('div', 'center-map-control');
      var btn = L.DomUtil.create('a', 'center-map-btn', d);
      btn.href = '#';
      btn.title = 'Center Map on Pilot';
      btn.setAttribute('aria-label', 'Center Map on Pilot');
      btn.innerHTML = '<i class="fa-solid fa-crosshairs"></i>';
      L.DomEvent.disableClickPropagation(d);
      L.DomEvent.on(btn, 'click', function(ev) {{
          L.DomEvent.stop(ev);
          centerMapToPilotRadius();
      }});
      return d;
  }};
  centerMapCtl.addTo(map);

  var airportsToggleCtl = L.control({{position:'topleft'}});
  airportsToggleCtl.onAdd = function() {{
      var d = L.DomUtil.create('div', 'left-mini-toggle-control');
      d.id = 'airportsToggleCtl';
      var btn = L.DomUtil.create('a', 'left-mini-toggle-btn', d);
      btn.href = '#';
      btn.title = 'Toggle airport types by province';
      btn.setAttribute('aria-label', 'Toggle Airports Layer');
      btn.innerHTML = '<i class="fa-solid fa-plane-departure"></i><span id="airportsToggleText" style="display:none">Toggle Airports Layer</span>';
      L.DomEvent.disableClickPropagation(d);
      L.DomEvent.on(btn, 'click', function(ev) {{
          L.DomEvent.stop(ev);
          setSelectedAirportLayersVisible(!anySelectedAirportLayerVisible());
          updateAirportsToggleLabel();
      }});
      return d;
  }};
  airportsToggleCtl.addTo(map);

  var notamsToggleCtl = L.control({{position:'topleft'}});
  notamsToggleCtl.onAdd = function() {{
      var d = L.DomUtil.create('div', 'left-mini-toggle-control');
      d.id = 'notamsToggleCtl';
      var btn = L.DomUtil.create('a', 'left-mini-toggle-btn', d);
      btn.href = '#';
      btn.title = 'Toggle NOTAM obstacles';
      btn.setAttribute('aria-label', 'Toggle NOTAMs');
      btn.innerHTML = '<i class="fa-solid fa-triangle-exclamation"></i>';
      L.DomEvent.disableClickPropagation(d);
      L.DomEvent.on(btn, 'click', function(ev) {{
          L.DomEvent.stop(ev);
          setNotamsVisible(!notamsVisible);
      }});
      return d;
  }};
  notamsToggleCtl.addTo(map);

  basemapControl.addTo(map);
  var basemapCtlContainer = basemapControl.getContainer ? basemapControl.getContainer() : null;
  if (basemapCtlContainer) {{
      basemapCtlContainer.classList.add('map-layers-control');
      basemapCtlContainer.title = 'Map Layers';
      L.DomEvent.disableClickPropagation(basemapCtlContainer);
      L.DomEvent.disableScrollPropagation(basemapCtlContainer);
      var baseToggle = basemapCtlContainer.querySelector('.leaflet-control-layers-toggle');
      if (baseToggle) {{
          baseToggle.title = 'Map Layers';
          baseToggle.setAttribute('aria-label', 'Map Layers');
      }}
      var layersList = basemapCtlContainer.querySelector('.leaflet-control-layers-list');
      if (layersList) {{
          L.DomEvent.on(layersList, 'touchstart', L.DomEvent.stopPropagation);
          L.DomEvent.on(layersList, 'touchmove', L.DomEvent.stopPropagation);
      }}
      if (!basemapCtlContainer.querySelector('.map-layers-close-btn')) {{
          var closeBtn = L.DomUtil.create('button', 'map-layers-close-btn', basemapCtlContainer);
          closeBtn.type = 'button';
          closeBtn.textContent = 'Close';
          closeBtn.setAttribute('aria-label', 'Close map layers panel');
          closeBtn.title = 'Close';
          L.DomEvent.on(closeBtn, 'click', function(ev) {{
              L.DomEvent.stop(ev);
              if (basemapControl && basemapControl.collapse) {{
                  basemapControl.collapse();
              }}
          }});
      }}
  }}

    zoomControl.addTo(map);

  var ctl = L.control({{position:'topleft'}});
  ctl.onAdd = function() {{
      var d = L.DomUtil.create('div','pilot-input');
      L.DomEvent.disableClickPropagation(d);
      d.style.marginTop = '88px';
                d.innerHTML = '<div id="pilotFlyout" class="pilot-flyout"><button id="pilotFlyoutToggle" class="pilot-flyout-toggle" title="Pilot controls"><i class="fa-solid fa-bars"></i></button><div class="controls-row">Lat <input id="pLat" size="10" maxlength="12" placeholder="43.000000"> Lon <input id="pLon" size="10" maxlength="13" placeholder="-79.000000"></div><div class="controls-meta dd-hint">DD: 43.653200, -79.383200</div><div class="action-grid"><button id="upd">Set Lat/Lon</button><button id="centerPilot">Center Map</button><button id="getPilotLoc">Get Location</button><button id="sourceBtn">Switch Filter Group</button><button id="openLiveFetch">Open FetchNotams</button><button id="refreshFirCacheBtn">Refresh FIR</button></div><div class="controls-row" style="margin-top:5px;">Radius km <input id="radiusKmInput" size="6" maxlength="6" placeholder="10"> <button id="setRadiusBtn">Change NOTAM Radius</button></div><div id="currentPilotText" class="controls-meta status-line">Current Pilot: --, --</div><div id="notamSourceText" class="controls-meta status-line">NOTAM Src: RAW</div><div id="livePayloadText" class="controls-meta status-line">Live payload: --</div><div id="currentBasemapText" class="controls-meta status-line">Basemap: --</div><div id="radiusInfoText" class="controls-meta status-line">NOTAM Radius: 10 km</div><div id="obstacleCountText" class="controls-meta status-line">Obstacles (10 km): --</div><div id="refreshFirPanel" style="display:none;padding:5px 2px 2px 2px;border-top:1px solid #ccc;margin-top:5px;"><div style="font-size:0.82em;font-weight:600;margin-bottom:3px;color:#555;">Refresh NOTAMs Cache</div><div style="display:flex;gap:4px;align-items:center;"><span style="font-size:0.8em;">FIR:</span><input id="refreshFirInput" size="5" maxlength="4" placeholder="CZYZ" style="width:50px;font-size:0.8em;padding:2px 3px;border:1px solid #aaa;border-radius:3px;"><button id="refreshFirFetchBtn" style="font-size:0.8em;padding:2px 7px;background:#2d6a2d;color:#fff;border:none;border-radius:3px;cursor:pointer;">Fetch</button><button id="refreshFirCancelBtn" style="font-size:0.8em;padding:2px 6px;background:#888;color:#fff;border:none;border-radius:3px;cursor:pointer;">&#x2715;</button></div><div id="refreshFirStatus" style="font-size:0.78em;margin-top:4px;color:#555;min-height:1.1em;"></div></div></div>';
      return d;
  }};
  ctl.addTo(map);

  // Enforce visual order in the left control column
  (function() {{
      var col = document.querySelector('.leaflet-top.leaflet-left');
      if (!col) return;
      var order = [
          '.leaflet-control-zoom',
          '.map-layers-control',
          '#notamsToggleCtl',
          '#airportsToggleCtl',
          '.center-map-control',
          '.pilot-input'
      ];
      order.reverse().forEach(function(sel) {{
          var el = col.querySelector(sel);
          if (el) col.insertBefore(el, col.firstChild);
      }});
  }})();

  map.on('baselayerchange', function(e) {{
      if (e && e.name) {{
          currentBasemapName = e.name;
          setStoredBasemapName(currentBasemapName);
          updateBasemapDisplay();
      }}
  }});

      map.on('overlayadd', function() {{
          updateAirportsToggleLabel();
          updateNotamsToggleVisual();
      }});

      map.on('overlayremove', function() {{
          updateAirportsToggleLabel();
          updateNotamsToggleVisual();
      }});

  function setPilotFlyoutCollapsed(collapsed) {{
      var flyout = document.getElementById('pilotFlyout');
      var toggle = document.getElementById('pilotFlyoutToggle');
      if (!flyout || !toggle) {{
          return;
      }}
      flyout.classList.toggle('collapsed', !!collapsed);
      toggle.setAttribute('aria-expanded', String(!flyout.classList.contains('collapsed')));
      toggle.innerHTML = flyout.classList.contains('collapsed')
          ? '<i class="fa-solid fa-bars"></i>'
          : '<i class="fa-solid fa-xmark"></i>';
  }}


  function updatePilotLocationPromptState(ll) {{
      var getPilotLocBtn = document.getElementById('getPilotLoc');
      if (!getPilotLocBtn) {{
          return;
      }}

      var needsLocation = !hasUsablePilotLocation(ll);
      getPilotLocBtn.classList.toggle('needs-location', needsLocation);
      getPilotLocBtn.title = needsLocation
          ? 'Pilot location required. Click to use device location.'
          : 'Get Location';

      if (needsLocation) {{
          setPilotFlyoutCollapsed(false);
      }}
  }}

  function collapsePilotFlyoutIfIdle() {{
      var flyout = document.getElementById('pilotFlyout');
      if (!flyout) {{
          return;
      }}
      if (flyout.contains(document.activeElement)) {{
          return;
      }}
      setPilotFlyoutCollapsed(true);
  }}

  (function wirePilotFlyoutBehavior() {{
      var flyout = document.getElementById('pilotFlyout');
      var toggle = document.getElementById('pilotFlyoutToggle');
      if (!flyout || !toggle) {{
          return;
      }}

      // Match neighboring map control button size and improve tap target.
      toggle.style.width = '34px';
      toggle.style.height = '34px';
      toggle.style.right = '-34px';
      toggle.style.fontSize = '16px';

      toggle.onclick = function(ev) {{
          if (ev) {{
              ev.preventDefault();
          }}
          setPilotFlyoutCollapsed(!flyout.classList.contains('collapsed'));
      }};

      // Start collapsed; expand/collapse only on hamburger click/tap.
      setPilotFlyoutCollapsed(true);
  }})();

  function stabilizeViewportLayout() {{
      window.scrollTo(0, 0);
      if (map && map.invalidateSize) {{
          map.invalidateSize(false);
      }}
  }}

  window.addEventListener('resize', stabilizeViewportLayout);
  window.addEventListener('orientationchange', stabilizeViewportLayout);
  if (window.visualViewport) {{
      window.visualViewport.addEventListener('resize', stabilizeViewportLayout);
      window.visualViewport.addEventListener('scroll', stabilizeViewportLayout);
  }}

  function preventBrowserZoomGestures(ev) {{
      if (ev) {{
          ev.preventDefault();
      }}
  }}

  document.addEventListener('gesturestart', preventBrowserZoomGestures, {{ passive: false }});
  document.addEventListener('gesturechange', preventBrowserZoomGestures, {{ passive: false }});
  document.addEventListener('gestureend', preventBrowserZoomGestures, {{ passive: false }});
  window.addEventListener('wheel', function(ev) {{
      if (ev && ev.ctrlKey) {{
          ev.preventDefault();
      }}
  }}, {{ passive: false }});

  document.getElementById('upd').onclick = function() {{
      var lat=parseFloat(document.getElementById('pLat').value);
      var lon=parseFloat(document.getElementById('pLon').value);
      if(isNaN(lat)||isNaN(lon)) {{ alert("Enter numeric lat & lon"); return; }}
      if(lat < -90 || lat > 90) {{ alert("Latitude must be between -90 and 90"); return; }}
      if(lon < -180 || lon > 180) {{ alert("Longitude must be between -180 and 180"); return; }}
      var ll=L.latLng(lat,lon);
      applyPilotLocation(ll, true);
      applyAirportDefaultsFromLocation(ll);
  }};

  document.getElementById('centerPilot').onclick = function() {{
      centerMapToPilotRadius();
  }};

    document.getElementById('sourceBtn').onclick = function() {{
          if (linkedRealtimeMode && linkedRealtimeNotams.length) {{
              return;
          }}
          activeSource = activeSource === 'FILTERED' ? 'RAW' : 'FILTERED';
            updateSourceDisplay();
            refreshObstacles(marker.getLatLng());
    }};

      document.getElementById('openLiveFetch').onclick = function() {{
          var popup = window.open('FetchNotams.html', '_blank');
          if (popup) {{
              popup.focus();
          }}
      }};

      document.getElementById('refreshFirCacheBtn').onclick = function() {{
          showRefreshFirPanel();
      }};
      document.getElementById('refreshFirCancelBtn').onclick = function() {{
          hideRefreshFirPanel();
      }};
      document.getElementById('refreshFirFetchBtn').onclick = async function() {{
          var input = document.getElementById('refreshFirInput');
          await refreshFirCache(input ? input.value : '');
      }};
      document.getElementById('refreshFirInput').addEventListener('keydown', function(ev) {{
          if (ev.key === 'Enter') {{ ev.preventDefault(); document.getElementById('refreshFirFetchBtn').click(); }}
      }});

      document.getElementById('setRadiusBtn').onclick = function() {{
          var val = parseFloat(document.getElementById('radiusKmInput').value);
          if (isNaN(val)) {{
              alert('Enter a numeric radius in km.');
              return;
          }}
          if (val <= 0 || val > 500) {{
              alert('Radius must be > 0 and <= 500 km.');
              return;
          }}
          applyNotamRadius(val);
      }};

      document.getElementById('radiusKmInput').addEventListener('keydown', function(ev) {{
          if (ev.key === 'Enter') {{
              ev.preventDefault();
              document.getElementById('setRadiusBtn').click();
          }}
      }});

      document.getElementById('getPilotLoc').onclick = function() {{
          if (!navigator.geolocation) {{
              alert('Geolocation is not supported by this browser/device.');
              return;
          }}

          navigator.geolocation.getCurrentPosition(
              function(pos) {{
                  var lat = pos.coords.latitude;
                  var lon = pos.coords.longitude;
                  var ll = L.latLng(lat, lon);
                  applyPilotLocation(ll, true);
                  applyAirportDefaultsFromLocation(ll);
              }},
              function(err) {{
                  var msg = 'Unable to retrieve location.';
                  if (err && typeof err.code !== 'undefined') {{
                      if (err.code === 1) {{
                          msg = 'Location permission was denied. Enable location access for this site/browser and try again.';
                      }} else if (err.code === 2) {{
                          msg = 'Location is currently unavailable. Check GPS/network and try again.';
                      }} else if (err.code === 3) {{
                          msg = 'Location request timed out. Try again in a stronger signal area.';
                      }}
                  }}
                  if (err && err.message) {{
                      msg += '\\n\\nDetails: ' + err.message;
                  }}
                  alert(msg);
              }},
              {{ enableHighAccuracy: !isCompactTouchLayout, timeout: 12000, maximumAge: isCompactTouchLayout ? 30000 : 5000 }}
          );
      }};

    var startupPilotLocation = marker.getLatLng();
    var restoredPilotLocation = getStoredPilotLocation();
    linkedRealtimeNotams = getLinkedRealtimeNotamsFromQuery();
        if (!linkedRealtimeNotams.length) {{
            linkedRealtimeNotams = getStartupLiveNotamsFromCache();
        }}
    linkedRealtimeMode = linkedRealtimeNotams.length > 0;

    if (restoredPilotLocation) {{
            startupPilotLocation = restoredPilotLocation;
    }}

    linkedObstacleBatch = parseLinkedObstacleBatchFromQuery();
    linkedObstacleLocation = getLinkedObstacleFromQuery();
    if (!linkedObstacleLocation && linkedObstacleBatch.length) {{
            linkedObstacleLocation = linkedObstacleBatch[0];
    }}

        if (linkedRealtimeMode && linkedRealtimeIntent === 'linked') {{
            linkedObstacleBatch = [];
            linkedObstacleLocation = null;
            linkedObstacleAutoOpenPending = false;
    }} else {{
            linkedObstacleAutoOpenPending = !!(linkedObstacleLocation && linkedFocusRequested);
    }}

    var startupLocationMissing = !hasUsablePilotLocation(startupPilotLocation);

    applyPilotLocation(startupPilotLocation, !startupLocationMissing);
    applyAirportDefaultsFromLocation(startupPilotLocation);
    if (!linkedRealtimeMode) {{
            renderLinkedObstacleBatchMarkers();
            if (linkedFocusRequested && linkedObstacleBatch.length > 1) {{
                    fitMapToLinkedObstacleBatch();
            }}
        }} else if (linkedRealtimeIntent === 'linked' && linkedFocusRequested && linkedRealtimeNotams.length > 1) {{
            var linkedRealtimeBounds = L.latLngBounds(linkedRealtimeNotams.map(function(item) {{
                    return [item.lat, item.lon];
            }}));
            if (linkedRealtimeBounds.isValid()) {{
                    map.fitBounds(linkedRealtimeBounds.pad(0.15), {{ padding: [34, 34], maxZoom: 11 }});
            }}
    }}

    updatePilotDisplay(startupPilotLocation);
    updateSourceDisplay();
        setAllAirportLayersVisible(false);
        updateAirportsToggleLabel();
        applyAirportDefaultsFromLocation(startupPilotLocation);
        applyBasemapByName(getStoredBasemapName()) || applyBasemapByName(defaultBasemapName);
        updateBasemapDisplay();
    updateNotamsToggleVisual();
    updateRadiusDisplay();
    scheduleRefreshObstacles(startupPilotLocation);
    loadNotamData().then(function() {{
                        if (!linkedRealtimeMode) {{
                                scheduleRefreshObstacles(marker.getLatLng());
                        }}
                        console.info('[NOTAM MAP] NOTAM data loaded and obstacle layer refreshed');
        }}).catch(function(err) {{
                        console.error('[NOTAM MAP] loadNotamData failed', err);
    }});
        console.info('[NOTAM MAP] widget init complete');
    }} catch (err) {{
        console.error('[NOTAM MAP] widget init failed', err);
    }}
}};
</script>
"""
    m.get_root().html.add_child(folium.Element(widget_js))
    m.get_root().html.add_child(
        folium.Element(
            """
<style>
.leaflet-top.leaflet-left {
    margin-top: calc(40px + env(safe-area-inset-top, 0px));
}

#backToQFilterBtn {
    position: fixed;
    left: calc(10px + env(safe-area-inset-left, 0px));
    top: calc(10px + env(safe-area-inset-top, 0px));
    z-index: 2600;
    width: 34px;
    height: 34px;
    border-radius: 8px;
    border: 1px solid #8e1b1b;
    background: #c62828;
    color: #ffffff;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 0;
    font-size: 16px;
    line-height: 1;
    cursor: pointer;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.35);
}
#backToQFilterBtn:hover {
    background: #b71c1c;
}
</style>

<button id="backToQFilterBtn" type="button" onclick="closeMapTab()" aria-label="Back" title="Back to previous page"><i class="fa-solid fa-arrow-left"></i></button>
"""
        )
    )

    print(f"Loaded filtered NOTAMs from: {NOTAMS_FILTERED_PATH}")
    print(f"Loaded RAW NOTAMs from: {NOTAMS_RAW_PATH}")
    print(f"Basemap: {basemap['name']} [{basemap_key}]")
    if generated_at:
        print(f"NOTAM data generatedAt: {generated_at}")
    print("Obstacle markers are now loaded dynamically in-browser from data/notams/*.json")

    return m


def normalize_output_html_head(output_path: Path) -> None:
    try:
        text = output_path.read_text(encoding="utf-8")
    except Exception as err:
        print(f"Warning: could not read generated HTML for head normalization: {err}")
        return

    original = text

    if "<html>" in text:
        text = text.replace("<html>", "<html lang=\"en\">", 1)

    text = text.replace(
        '<meta http-equiv="content-type" content="text/html; charset=UTF-8" />',
        '<meta charset="utf-8" />\n    <title>NOTAM Map</title>\n    <meta name="viewport" content="width=device-width, initial-scale=1.0" />',
        1,
    )

    text = re.sub(
        r"\s*<meta\s+name=\"viewport\"\s+content=\"width=device-width,\s*initial-scale=1\.0,\s*maximum-scale=1\.0,\s*user-scalable=no\"\s*/>",
        "",
        text,
        count=1,
        flags=re.IGNORECASE,
    )

    mojibake_replacements = {
        "Â°": "°",
        "â€™": "'",
        "â€˜": "'",
        "â€œ": '"',
        "â€�": '"',
        "â€“": "-",
        "â€”": "-",
        "Ã€": "À",
        "Ã‡": "Ç",
        "Ãˆ": "È",
        "Ã‰": "É",
        "ÃŠ": "Ê",
        "Ã‹": "Ë",
        "ÃŽ": "Î",
        "Ã”": "Ô",
        "Ã›": "Û",
        "Ãœ": "Ü",
        "Ã ": "à",
        "Ã¢": "â",
        "Ã¤": "ä",
        "Ã§": "ç",
        "Ã¨": "è",
        "Ã©": "é",
        "Ãª": "ê",
        "Ã«": "ë",
        "Ã¬": "ì",
        "Ã®": "î",
        "Ã¯": "ï",
        "Ã´": "ô",
        "Ã¶": "ö",
        "Ã¹": "ù",
        "Ã»": "û",
        "Ã¼": "ü",
        "Ã¿": "ÿ",
        "Å’": "Œ",
        "Å“": "œ",
    }
    for bad, good in mojibake_replacements.items():
        text = text.replace(bad, good)

    if text != original:
        try:
            output_path.write_text(text, encoding="utf-8")
            print(f"Normalized HTML metadata in -> {output_path.name}")
        except Exception as err:
            print(f"Warning: could not write head-normalized HTML: {err}")


def main():
    basemap_key = choose_basemap_key()
    if basemap_key.startswith("google_"):
        print(
            "Note: Google tile use may require API keys/licensing terms for production usage."
        )

    pilot_lat, pilot_lon = get_pilot_location()
    print(f"Using pilot location: {pilot_lat}, {pilot_lon}")

    notams_filtered, notams_raw, generated_at = load_notams_from_repo()
    m = build_map(
        pilot_lat,
        pilot_lon,
        notams_filtered,
        notams_raw,
        generated_at,
        basemap_key=basemap_key,
    )

    default_out_name = "Notam Map.html"
    out_name = input(
        f"Output HTML filename [{default_out_name}]: "
    ).strip()
    if not out_name:
        out_name = default_out_name
    elif not out_name.lower().endswith(".html"):
        out_name += ".html"

    m.save(out_name)
    normalize_output_html_head(Path(out_name))
    print(f"Map saved as -> {out_name}")


if __name__ == "__main__":
    main()


