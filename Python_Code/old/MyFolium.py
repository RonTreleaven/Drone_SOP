import folium
import json
from folium.plugins import MarkerCluster  # This will ensure Leaflet is loaded

# Example data
airport_js_array = [
    {"lat": 43.7, "lon": -79.4, "popup": "Toronto Airport"},
    {"lat": 45.5, "lon": -73.6, "popup": "Montreal Airport"}
]
notam_js_array = [
    {"lat": 44.0, "lon": -79.0, "popup": "NOTAM: Obstacle 1"},
    {"lat": 46.0, "lon": -74.0, "popup": "NOTAM: Obstacle 2"}
]

# Create the map
m = folium.Map(location=[44.5, -78.5], zoom_start=6)
map_id = m.get_name()
# m.get_root().script.add_child(folium.Element(f"window._map = {map_id};"))
# 
# Expose the map object to JS
# m.get_root().script.add_child(folium.Element(f"window._map = {map_id};")# )

# Inject data arrays into JS
m.get_root().html.add_child(folium.Element(
    f"<script>window.AIRPORTS = {json.dumps(airport_js_array)};</script>"
))
m.get_root().html.add_child(folium.Element(
    f"<script>window.NOTAMS = {json.dumps(notam_js_array)};</script>"
))

# Add sidebar and JS for marker display

### RAW Section

sidebar_html = '''
<div id="sidebar" style="position:fixed;top:20px;left:20px;z-index:1000;background:#fff;padding:10px;border:1px solid #ccc;">
  <button onclick="applyFilter()">Show Markers</button>
</div>


{% raw %}
<script>
function waitForMapAndRun(fn) {
  if (window._map && typeof window._map.addLayer === "function") {
    fn();
  } else {
    setTimeout(() => waitForMapAndRun(fn), 100);
  }
}

function applyFilter() {
  console.log("applyFilter called");
  let airportMarkers = window.airportMarkers = window.airportMarkers || [];
  let notamMarkers = window.notamMarkers = window.notamMarkers || [];
  function clearMarkers(markerList) {
    markerList.forEach(m => window._map.removeLayer(m));
    markerList.length = 0;
  }
  clearMarkers(airportMarkers);
  clearMarkers(notamMarkers);
  if (window.AIRPORTS) {
    window.AIRPORTS.forEach(a => {
      console.log("Adding airport marker:", a);
      let marker = L.marker([a.lat, a.lon], {
        icon: (L.ExtraMarkers && L.ExtraMarkers.icon)
          ? L.ExtraMarkers.icon({
              icon: 'fa-plane',
              markerColor: 'blue',
              shape: 'square',
              prefix: 'fa'
            })
          : undefined
      }).bindPopup(a.popup).addTo(window._map);
      airportMarkers.push(marker);
    });
  }
  if (window.NOTAMS) {
    window.NOTAMS.forEach(n => {
      console.log("Adding NOTAM marker:", n);
      let marker = L.marker([n.lat, n.lon], {
        icon: (L.ExtraMarkers && L.ExtraMarkers.icon)
          ? L.ExtraMarkers.icon({
              icon: 'fa-exclamation-triangle',
              markerColor: 'orange',
              shape: 'circle',
              prefix: 'fa'
            })
          : undefined
      }).bindPopup(n.popup).addTo(window._map);
      notamMarkers.push(marker);
    });
  }
}

// Wait for map, then run applyFilter
document.addEventListener("DOMContentLoaded", function() {
  waitForMapAndRun(applyFilter);
  window.applyFilter = function() { waitForMapAndRun(applyFilter); };
});
</script>
{% endraw %}
'''


m.get_root().html.add_child(folium.Element(sidebar_html))

m.get_root().header.add_child(folium.Element(
    "<style>#map {height: 600px !important;}</style>"
))

# Add FontAwesome (for icons)
m.get_root().header.add_child(folium.Element(
    '<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css"/>'
))

m.get_root().html.add_child(folium.Element("""
{% raw %}
<script>
function loadExtraMarkers(callback) {
  if (window.L && !window.L.ExtraMarkers) {
    var link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = 'https://unpkg.com/leaflet-extra-markers@1.2.1/dist/css/leaflet.extra-markers.min.css';
    document.head.appendChild(link);

    var script = document.createElement('script');
    script.src = 'https://unpkg.com/leaflet-extra-markers@1.2.1/dist/js/leaflet.extra-markers.min.js';
    script.onload = callback;
    document.body.appendChild(script);
  } else if (window.L && window.L.ExtraMarkers) {
    callback();
  } else {
    setTimeout(function() { loadExtraMarkers(callback); }, 100);
  }
}

// Usage: load the plugin, then run your marker code
document.addEventListener("DOMContentLoaded", function() {
  loadExtraMarkers(function() {
    if (window.applyFilter) window.applyFilter();
  });
});
</script>
{% endraw %}
"""))

m.save("test2_map.html")