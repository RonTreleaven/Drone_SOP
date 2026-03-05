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


def build_map(pilot_lat, pilot_lon, notams_filtered, notams_raw, generated_at=None):
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
        tiles="CartoDB positron",
        zoom_control=False,
    )

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
    filtered_points = prepare_obstacle_points(notams_filtered)
    raw_points = prepare_obstacle_points(notams_raw)

    shown = 0
    for point in filtered_points:
        if haversine_km(pilot_lat, pilot_lon, point["lat"], point["lon"]) <= NOTAM_RADIUS_KM:
            shown += 1

    obstacle_layer.add_to(m)
    layers_dict["Obstacles"] = [obstacle_layer]

    # 6) Layer control + style
    control_groups = {"Obstacles": layers_dict["Obstacles"]}
    for group_name, group_layers in layers_dict.items():
        if group_name != "Obstacles":
            control_groups[group_name] = group_layers

    GroupedLayerControl(groups=control_groups, exclusive_groups=[], collapsed=True).add_to(m)
    m.get_root().html.add_child(
        folium.Element(
            "<style>"
            ".leaflet-control-layers{min-width:220px;max-width:320px;font-size:13px;}"
            ".leaflet-control-layers-expanded{padding:7px 9px;}"
            ".leaflet-control-layers-group-name{font-weight:700;color:#1f3b63;margin-top:6px;}"
            ".leaflet-control-layers-list{max-height:56vh;overflow-y:auto;padding-right:4px;}"
            ".leaflet-control-layers-group-label{cursor:pointer;display:block;position:relative;padding-right:14px;}"
            ".leaflet-control-layers-group-label:after{content:'▾';position:absolute;right:2px;top:0;color:#1f3b63;font-size:11px;}"
            ".leaflet-control-layers-group.province-collapsed>.leaflet-control-layers-group-label:after{content:'▸';}"
            ".leaflet-control-layers-group.province-collapsed>label:not(.leaflet-control-layers-group-label){display:none;}"
            ".leaflet-control-layers-group.province-collapsed>.leaflet-control-layers-group-label{display:inline-block;max-width:170px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}"
            "@media (max-width:600px){.leaflet-control-layers{min-width:176px;max-width:220px;font-size:12px;}.leaflet-control-layers-expanded{padding:6px 8px;}.leaflet-control-layers-group.province-collapsed>.leaflet-control-layers-group-label{max-width:146px;}}"
            ".pilot-input{z-index:1200;}"
            ".pilot-flyout{position:relative;width:272px;background:#fff;border:1px solid #d8e2ee;border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,0.2);padding:7px;transition:transform .2s ease;overflow:visible;box-sizing:border-box;}"
            ".pilot-flyout.collapsed{transform:translateX(-100%);}" 
            ".pilot-flyout-toggle{position:absolute;right:-24px;top:10px;width:24px;height:52px;border:1px solid #d8e2ee;border-left:none;border-radius:0 6px 6px 0;background:#fff;color:#1f3b63;cursor:pointer;font-weight:700;line-height:1;}"
            ".pilot-flyout .controls-row{display:flex;flex-wrap:wrap;gap:3px;align-items:center;}"
            ".pilot-flyout input{max-width:102px;font-size:12px;}"
            ".pilot-flyout .action-grid{display:grid;grid-template-columns:1fr 1fr;gap:4px;margin-top:5px;}"
            ".pilot-flyout .action-grid button{width:100%;height:24px;margin:0;padding:2px 4px;font-size:10px;line-height:1.05;text-align:center;}"
            ".pilot-flyout .controls-meta{font-size:11px;margin-top:3px;line-height:1.25;}"
            ".pilot-flyout .status-line{font-weight:600;color:#1f3b63;}"
            ".pilot-flyout .dd-hint{color:#666;margin-top:2px;}"
            ".home-logo-control{background:#fff;border:1px solid #d8e2ee;border-radius:8px;padding:4px 6px;box-shadow:0 2px 6px rgba(0,0,0,0.2);}"
            ".home-logo-control img{display:block;height:64px;width:auto;}"
            ".notam-popup{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;font-size:13px;line-height:1.35;color:#333;}"
            ".notam-title{font-weight:700;color:#007acc;margin-bottom:4px;}"
            ".notam-label{font-weight:600;color:#1f3b63;}"
            ".notam-raw{max-height:220px;overflow:auto;white-space:normal;}"
            "</style>"
        )
    )

    # 7) Inject widget for pilot drag/manual update and dynamic NOTAM source/filter
    widget_js = f"""
<script>
window.onload = function() {{
  var map = {m.get_name()};
  var marker = {pm_js};
  var c1 = {c1_js};
  var c3 = {c3_js};
  var c100 = {c100_js};
  var obstacleLayer = {obstacle_layer_js};
    var radiusKm = {NOTAM_RADIUS_KM};
    var filteredNotams = {json.dumps(filtered_points)};
    var rawNotams = {json.dumps(raw_points)};
    var activeSource = 'RAW';
    var currentZoom = map.getZoom();

    L.control.zoom({{position:'bottomleft'}}).addTo(map);

  function formatCoord(v) {{
      return Number(v).toFixed({COORD_DECIMALS});
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
      refreshObstacles(marker.getLatLng());
  }}

  function initProvinceGroupCollapse() {{
      var groups = document.querySelectorAll('.leaflet-control-layers-group');
      for (var i = 0; i < groups.length; i++) {{
          var group = groups[i];
          var nameEl = group.querySelector('.leaflet-control-layers-group-name');
          var labelEl = group.querySelector('.leaflet-control-layers-group-label');
          if (!nameEl || !labelEl) {{
              continue;
          }}

          if (labelEl.dataset.collapseBound === '1') {{
              continue;
          }}

          var groupName = (nameEl.textContent || '').trim().toLowerCase();
          var isObstacles = groupName.indexOf('obstacle') !== -1;
          if (!isObstacles) {{
              group.classList.add('province-collapsed');
          }}

          labelEl.dataset.collapseBound = '1';
          labelEl.addEventListener('click', function(ev) {{
              ev.stopPropagation();
              var parent = ev.currentTarget.parentElement;
              if (parent) {{
                  parent.classList.toggle('province-collapsed');
              }}
          }});
      }}
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
      return activeSource === 'RAW' ? rawNotams : filteredNotams;
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
      if (sourceText) {{
          sourceText.textContent = 'NOTAM Src: ' + activeSource;
          sourceText.style.color = activeSource === 'RAW' ? 'green' : 'red';
      }}
      if (sourceBtn) {{
          sourceBtn.textContent = 'Switch Filter Group';
      }}
  }}

  function refreshObstacles(ll) {{
      obstacleLayer.clearLayers();
      var activeNotams = getActiveNotams();
      var shownCount = 0;

      for (var i = 0; i < activeNotams.length; i++) {{
          var item = activeNotams[i];
          var km = haversineKm(ll.lat, ll.lng, item.lat, item.lon);
          if (km > radiusKm) {{
              continue;
          }}

          shownCount += 1;
          L.marker([item.lat, item.lon], {{
              icon: L.AwesomeMarkers.icon({{
                  icon: 'exclamation-triangle',
                  prefix: 'fa',
                  markerColor: 'red'
              }})
          }})
          .bindTooltip('Obstacle')
          .bindPopup(buildObstaclePopupHtml(item), {{ maxWidth: 420 }})
          .addTo(obstacleLayer);
      }}

      var countText = document.getElementById('obstacleCountText');
      if (countText) {{
          countText.textContent = 'Obstacles (' + radiusLabel() + ' km): ' + shownCount;
      }}
  }}

  function applyPilotLocation(ll, shouldCenter) {{
      marker.setLatLng(ll).openPopup();
      c1.setLatLng(ll); c3.setLatLng(ll); c100.setLatLng(ll);
      c1Touch.setLatLng(ll); c3Touch.setLatLng(ll); c100Touch.setLatLng(ll);
      marker.setPopupContent("Pilot<br>Lat: " + ll.lat.toFixed(6) + "<br>Lon: " + ll.lng.toFixed(6));
      if (shouldCenter) {{
          map.setView(ll, currentZoom);
      }}
      refreshObstacles(ll);
      updatePilotDisplay(ll);
  }}

  function createCircleTouchTarget(circle, popupText) {{
      var target = L.circle(circle.getLatLng(), {{
          radius: circle.getRadius(),
          color: '#000',
          opacity: 0,
          weight: 28,
          fill: false,
          interactive: true,
          bubblingMouseEvents: false
      }}).addTo(map);

      target.bindPopup(popupText);
      target.on('mouseover', function() {{
          target.openPopup();
      }});
      target.on('mouseout', function() {{
          target.closePopup();
      }});
      target.on('click', function() {{
          target.openPopup();
      }});
      target.on('touchend', function() {{
          setTimeout(function() {{ target.closePopup(); }}, 1200);
      }});
      return target;
  }}

  var c1Touch = createCircleTouchTarget(c1, '1 NM (1.9 km) radius');
  var c3Touch = createCircleTouchTarget(c3, '3 NM (5.6 km) radius');
  var c100Touch = createCircleTouchTarget(c100, radiusLabel() + ' km NOTAM filter radius');

    map.on('click', function() {{
            c1Touch.closePopup();
            c3Touch.closePopup();
            c100Touch.closePopup();
    }});

  map.on('zoomend', function() {{
      currentZoom = map.getZoom();
  }});

  marker.dragging.enable();
  marker.on('dragend', function(e) {{
      var ll = e.target.getLatLng();
      applyPilotLocation(ll, false);
  }});

  var homeCtl = L.control({{position:'topleft'}});
  homeCtl.onAdd = function() {{
      var d = L.DomUtil.create('div', 'home-logo-control');
      L.DomEvent.disableClickPropagation(d);
      d.innerHTML = '<a href="tools.html" title="Tools Menu"><img src="assets/img/logo.png" alt="Tools"></a>';
      return d;
  }};
  homeCtl.addTo(map);

  var ctl = L.control({{position:'topleft'}});
  ctl.onAdd = function() {{
      var d = L.DomUtil.create('div','pilot-input');
      L.DomEvent.disableClickPropagation(d);
      d.style.marginTop = '88px';
        d.innerHTML = '<div id="pilotFlyout" class="pilot-flyout"><button id="pilotFlyoutToggle" class="pilot-flyout-toggle" title="Pilot controls"><</button><div class="controls-row">Lat <input id="pLat" size="10" maxlength="12" placeholder="43.000000"> Lon <input id="pLon" size="10" maxlength="13" placeholder="-79.000000"></div><div class="controls-meta dd-hint">DD: 43.653200, -79.383200</div><div class="action-grid"><button id="upd">Set Lat/Lon</button><button id="centerPilot">Center Map</button><button id="getPilotLoc">Get Location</button><button id="sourceBtn">Swith Filter Group</button></div><div class="controls-row" style="margin-top:5px;">Radius km <input id="radiusKmInput" size="6" maxlength="6" placeholder="10"> <button id="setRadiusBtn">Change NOTAM Radius</button></div><div id="currentPilotText" class="controls-meta status-line">Current Pilot: --, --</div><div id="notamSourceText" class="controls-meta status-line">NOTAM Src: RAW</div><div id="radiusInfoText" class="controls-meta status-line">NOTAM Radius: 10 km</div><div id="obstacleCountText" class="controls-meta status-line">Obstacles (10 km): --</div></div>';
      return d;
  }};
  ctl.addTo(map);

  document.getElementById('pilotFlyoutToggle').onclick = function() {{
      var flyout = document.getElementById('pilotFlyout');
      if (!flyout) {{
          return;
      }}
      flyout.classList.toggle('collapsed');
    this.textContent = flyout.classList.contains('collapsed') ? '>' : '<';
  }};

  document.getElementById('upd').onclick = function() {{
      var lat=parseFloat(document.getElementById('pLat').value);
      var lon=parseFloat(document.getElementById('pLon').value);
      if(isNaN(lat)||isNaN(lon)) {{ alert("Enter numeric lat & lon"); return; }}
      if(lat < -90 || lat > 90) {{ alert("Latitude must be between -90 and 90"); return; }}
      if(lon < -180 || lon > 180) {{ alert("Longitude must be between -180 and 180"); return; }}
      var ll=L.latLng(lat,lon);
      applyPilotLocation(ll, true);
  }};

  document.getElementById('centerPilot').onclick = function() {{
      map.setView(marker.getLatLng(), currentZoom);
  }};

    document.getElementById('sourceBtn').onclick = function() {{
          activeSource = activeSource === 'FILTERED' ? 'RAW' : 'FILTERED';
            updateSourceDisplay();
            refreshObstacles(marker.getLatLng());
    }};

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
                  var promptMsg = `Use current location?\n\nLat: ${{lat.toFixed({COORD_DECIMALS})}}\nLon: ${{lon.toFixed({COORD_DECIMALS})}}`;
                  if (!confirm(promptMsg)) {{
                      return;
                  }}
                  applyPilotLocation(L.latLng(lat, lon), true);
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
              {{ enableHighAccuracy: true, timeout: 12000, maximumAge: 0 }}
          );
      }};

    setTimeout(initProvinceGroupCollapse, 0);
  updatePilotDisplay(marker.getLatLng());
    updateSourceDisplay();
    updateRadiusDisplay();
  refreshObstacles(marker.getLatLng());
}};
</script>
"""
    m.get_root().html.add_child(folium.Element(widget_js))

    print(f"Loaded filtered NOTAMs from: {NOTAMS_FILTERED_PATH}")
    print(f"Loaded RAW NOTAMs from: {NOTAMS_RAW_PATH}")
    if generated_at:
        print(f"NOTAM data generatedAt: {generated_at}")
    print(f"Initial obstacle markers plotted (FILTERED): {shown}")

    return m


def main():
    pilot_lat, pilot_lon = get_pilot_location()
    print(f"Using pilot location: {pilot_lat}, {pilot_lon}")

    notams_filtered, notams_raw, generated_at = load_notams_from_repo()
    m = build_map(pilot_lat, pilot_lon, notams_filtered, notams_raw, generated_at)

    default_out_name = "Notam Map.html"
    out_name = input(
        f"Output HTML filename [{default_out_name}]: "
    ).strip()
    if not out_name:
        out_name = default_out_name
    elif not out_name.lower().endswith(".html"):
        out_name += ".html"

    m.save(out_name)
    print(f"Map saved as -> {out_name}")


if __name__ == "__main__":
    main()
