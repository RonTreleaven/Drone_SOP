import pandas as pd
import geopandas as gpd
import folium
from folium.plugins import FeatureGroupSubGroup, GroupedLayerControl, MarkerCluster

DEFAULT_LAT = 44.0
DEFAULT_LON = -79.0
DEFAULT_ZOOM = 8
DEFAULT_RADIUS_KM = 100
RADIUS_M = DEFAULT_RADIUS_KM * 1000

ICON_STYLE = {
    "heliport": {"icon": "helicopter", "color": "green"},
    "seaplane_base": {"icon": "ship", "color": "cadetblue"},
    "small_airport": {"icon": "circle", "color": "gray"},
    "medium_airport": {"icon": "plane", "color": "blue"},
    "large_airport": {"icon": "plane", "color": "darkblue"},
    "default": {"icon": "map-marker", "color": "lightgray"},
}


def get_pilot_location():
    try:
        lat_str = input(f"Pilot latitude (decimal degrees) [{DEFAULT_LAT}]: ").strip()
        lon_str = input(f"Pilot longitude (decimal degrees) [{DEFAULT_LON}]: ").strip()
        lat = float(lat_str) if lat_str else DEFAULT_LAT
        lon = float(lon_str) if lon_str else DEFAULT_LON
        return lat, lon
    except ValueError:
        raise SystemExit("Numeric lat/lon required.")


def build_map(pilot_lat, pilot_lon):
    df = pd.read_csv("https://davidmegginson.github.io/ourairports-data/airports.csv")
    df = df[df["iso_country"] == "CA"].copy()
    df.dropna(subset=["ident", "latitude_deg", "longitude_deg"], inplace=True)

    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df.longitude_deg, df.latitude_deg),
        crs="EPSG:4326",
    )

    m = folium.Map(location=[pilot_lat, pilot_lon], zoom_start=DEFAULT_ZOOM, tiles="CartoDB positron")

    province_parents = {}
    layers_dict = {}

    for prov in sorted(gdf["iso_region"].unique()):
        fg = folium.FeatureGroup(name=prov, show=False).add_to(m)
        province_parents[prov] = fg
        layers_dict[prov] = []

    for prov, prov_df in gdf.groupby("iso_region"):
        for atype, sub in prov_df.groupby("type"):
            child = FeatureGroupSubGroup(province_parents[prov], atype, show=False, overlay=True)
            cluster = MarkerCluster().add_to(child)
            style = ICON_STYLE.get(atype, ICON_STYLE["default"])
            for _, row in sub.iterrows():
                lat = row.geometry.y
                lon = row.geometry.x
                folium.Marker(
                    [lat, lon],
                    tooltip=f"{row['ident']} | {row['name']}",
                    popup=f"{row['ident']} - {row['name']}<br>Lat: {lat:.6f}<br>Lon: {lon:.6f}",
                    icon=folium.Icon(color=style["color"], icon=style["icon"], prefix="fa"),
                ).add_to(cluster)
            child.add_to(m)
            layers_dict[prov].append(child)

    pilot_marker = folium.Marker(
        [pilot_lat, pilot_lon],
        tooltip="Pilot location",
        popup=f"Pilot<br>Lat: {pilot_lat:.6f}<br>Lon: {pilot_lon:.6f}",
        icon=folium.Icon(color="green", icon="user", prefix="fa"),
    ).add_to(m)

    radius_circle = folium.Circle(
        [pilot_lat, pilot_lon],
        radius=RADIUS_M,
        color="red",
        weight=2,
        dash_array="6,6",
        fill=False,
        popup=f"{DEFAULT_RADIUS_KM} km radius",
    ).add_to(m)

    obstacles_layer = folium.FeatureGroup(name="Obstacles <= 100 km", show=True).add_to(m)
    layers_dict["NOTAM"] = [obstacles_layer]

    GroupedLayerControl(groups=layers_dict, exclusive_groups=[], collapsed=False).add_to(m)

    m.get_root().html.add_child(
        folium.Element(
            """
<style>
.leaflet-control-layers-list { max-height: 320px; overflow-y: auto; }
.pilot-input { z-index: 1200; }
.notam-status { z-index: 1200; }
</style>
"""
        )
    )

    widget_js = """
<script>
window.addEventListener('load', function() {
  var map = __MAP_NAME__;
  var pilotMarker = __PILOT_MARKER__;
  var radiusCircle = __RADIUS_CIRCLE__;
  var obstaclesLayer = __OBST_LAYER__;

  var NOTAM_URL = './data/notams/All_CA.json';
  var META_URL = './data/notams/All_CA.meta.json';
  var RADIUS_KM = __RADIUS_KM__;
  var allNotams = [];

  function escapeHtml(text) {
    var div = document.createElement('div');
    div.textContent = text == null ? '' : String(text);
    return div.innerHTML;
  }

  function parseCoord(text) {
    if (!text || typeof text !== 'string') return null;
    var parts = text.split(',');
    if (parts.length < 2) return null;
    var lat = parseFloat(parts[0].trim());
    var lon = parseFloat(parts[1].trim());
    if (Number.isNaN(lat) || Number.isNaN(lon)) return null;
    return [lat, lon];
  }

  function haversineKm(lat1, lon1, lat2, lon2) {
    var toRad = Math.PI / 180;
    var dLat = (lat2 - lat1) * toRad;
    var dLon = (lon2 - lon1) * toRad;
    var a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
            Math.cos(lat1 * toRad) * Math.cos(lat2 * toRad) *
            Math.sin(dLon / 2) * Math.sin(dLon / 2);
    var c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return 6371 * c;
  }

  function isActiveNow(notam) {
    if (!notam || !notam.endValidity) return true;
    var endMs = Date.parse(notam.endValidity);
    if (Number.isNaN(endMs)) return true;
    return endMs >= Date.now();
  }

  function formatTs(ts) {
    if (!ts) return 'N/A';
    var d = new Date(ts);
    if (Number.isNaN(d.getTime())) return ts;
    return d.toLocaleString();
  }

  var statusCtl = L.control({ position: 'topright' });
  statusCtl.onAdd = function() {
    var d = L.DomUtil.create('div', 'notam-status');
    L.DomEvent.disableClickPropagation(d);
    d.style.background = 'white';
    d.style.padding = '8px';
    d.style.fontSize = '12px';
    d.style.boxShadow = '0 0 4px rgba(0,0,0,0.3)';
    d.style.minWidth = '240px';
    d.id = 'notamStatusBox';
    d.innerHTML = 'Loading NOTAM data...';
    return d;
  };
  statusCtl.addTo(map);

  function setStatus(html) {
    var box = document.getElementById('notamStatusBox');
    if (box) box.innerHTML = html;
  }

  function renderNearbyObstacles() {
    obstaclesLayer.clearLayers();
    var ll = pilotMarker.getLatLng();
    var shown = 0;
    var activeWithCoords = 0;

    for (var i = 0; i < allNotams.length; i++) {
      var n = allNotams[i];
      if (!isActiveNow(n)) continue;
      if (!Array.isArray(n.coordinates_dd) || n.coordinates_dd.length === 0) continue;

      activeWithCoords++;
      for (var j = 0; j < n.coordinates_dd.length; j++) {
        var c = parseCoord(n.coordinates_dd[j]);
        if (!c) continue;

        var km = haversineKm(ll.lat, ll.lng, c[0], c[1]);
        if (km > RADIUS_KM) continue;

        var rawSafe = escapeHtml(n.raw || '').replace(/\n/g, '<br>');
        var popupHtml =
          '<b>Obstacle Alert</b><br>' +
          '<b>Distance:</b> ' + km.toFixed(1) + ' km<br>' +
          '<b>Start:</b> ' + escapeHtml(formatTs(n.startValidity)) + '<br>' +
          '<b>End:</b> ' + escapeHtml(formatTs(n.endValidity)) + '<hr style="margin:6px 0">' +
          rawSafe;

        L.marker([c[0], c[1]], {
          icon: L.AwesomeMarkers.icon({
            icon: 'exclamation-triangle',
            prefix: 'fa',
            markerColor: 'red'
          })
        })
          .bindTooltip('Obstacle')
          .bindPopup(popupHtml, { maxWidth: 420 })
          .addTo(obstaclesLayer);

        shown++;
      }
    }

    setStatus(
      '<b>Nearby Obstacles:</b> ' + shown + '<br>' +
      '<b>Radius:</b> ' + RADIUS_KM + ' km<br>' +
      '<b>Active NOTAMs with coords:</b> ' + activeWithCoords + '<br>' +
      '<b>Pilot:</b> ' + ll.lat.toFixed(5) + ', ' + ll.lng.toFixed(5)
    );
  }

  function refreshPilotDisplay() {
    var ll = pilotMarker.getLatLng();
    radiusCircle.setLatLng(ll);
    pilotMarker.setPopupContent('Pilot<br>Lat: ' + ll.lat.toFixed(6) + '<br>Lon: ' + ll.lng.toFixed(6));
    renderNearbyObstacles();
  }

  function installPilotControl() {
    var ctl = L.control({ position: 'bottomleft' });
    ctl.onAdd = function() {
      var d = L.DomUtil.create('div', 'pilot-input');
      L.DomEvent.disableClickPropagation(d);
      d.style.background = 'white';
      d.style.padding = '8px';
      d.style.fontSize = '13px';
      d.style.boxShadow = '0 0 4px rgba(0,0,0,0.3)';
      d.innerHTML =
        'Lat <input id="pLat" size="10" value="' + pilotMarker.getLatLng().lat.toFixed(6) + '"> ' +
        'Lon <input id="pLon" size="10" value="' + pilotMarker.getLatLng().lng.toFixed(6) + '"> ' +
        '<button id="updPilot">Update</button>';
      return d;
    };
    ctl.addTo(map);

    document.getElementById('updPilot').onclick = function() {
      var lat = parseFloat(document.getElementById('pLat').value);
      var lon = parseFloat(document.getElementById('pLon').value);
      if (Number.isNaN(lat) || Number.isNaN(lon)) {
        alert('Enter numeric lat/lon.');
        return;
      }
      var ll = L.latLng(lat, lon);
      pilotMarker.setLatLng(ll).openPopup();
      map.setView(ll, map.getZoom());
      refreshPilotDisplay();
    };
  }

  pilotMarker.dragging.enable();
  pilotMarker.on('dragend', function() {
    var ll = pilotMarker.getLatLng();
    var latIn = document.getElementById('pLat');
    var lonIn = document.getElementById('pLon');
    if (latIn) latIn.value = ll.lat.toFixed(6);
    if (lonIn) lonIn.value = ll.lng.toFixed(6);
    refreshPilotDisplay();
  });

  installPilotControl();

  fetch(NOTAM_URL)
    .then(function(resp) {
      if (!resp.ok) throw new Error('HTTP ' + resp.status);
      return resp.json();
    })
    .then(function(data) {
      if (!Array.isArray(data)) throw new Error('All_CA.json must be a JSON array');
      allNotams = data;
      return fetch(META_URL)
        .then(function(metaResp) {
          if (!metaResp.ok) return null;
          return metaResp.json();
        })
        .catch(function() { return null; });
    })
    .then(function(meta) {
      if (meta && meta.generatedAt) {
        var box = document.getElementById('notamStatusBox');
        if (box) {
          box.innerHTML = 'NOTAM data loaded.<br><b>Generated:</b> ' + escapeHtml(formatTs(meta.generatedAt));
        }
      }
      refreshPilotDisplay();
    })
    .catch(function(err) {
      setStatus('<b>NOTAM load failed:</b> ' + escapeHtml(err.message));
      console.error('NOTAM load failed', err);
    });
});
</script>
"""

    widget_js = (
        widget_js.replace("__MAP_NAME__", m.get_name())
        .replace("__PILOT_MARKER__", pilot_marker.get_name())
        .replace("__RADIUS_CIRCLE__", radius_circle.get_name())
        .replace("__OBST_LAYER__", obstacles_layer.get_name())
        .replace("__RADIUS_KM__", str(DEFAULT_RADIUS_KM))
    )

    m.get_root().html.add_child(folium.Element(widget_js))
    return m


def main():
    pilot_lat, pilot_lon = get_pilot_location()
    print(f"Pilot location: {pilot_lat:.6f}, {pilot_lon:.6f}")

    m = build_map(pilot_lat, pilot_lon)
    out_path = "2026_airports_notams_map.html"
    m.save(out_path)
    print(f"Map saved: {out_path}")


if __name__ == "__main__":
    main()
