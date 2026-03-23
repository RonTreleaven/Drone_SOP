#!/usr/bin/env python3
"""Add airport marker distance enrichment to v3NotamMap.html"""

import sys

file_path = r'C:\Users\Ron Treleaven\Drone_SOP\v3NotamMap.html'

# Read the entire file (Python can handle large text files better than PowerShell)
try:
    with open(file_path, 'r', encoding='utf-8') as src:
        original = src.read()
except Exception as e:
    print(f"Error reading: {e}", file=sys.stderr)
    sys.exit(1)

# Check if already added
if 'enrichAirportMarkersWithDistance' in original:
    print("Enrichment already added")
    sys.exit(0)

# Build the enrichment function
enrich_func = '''

  // Enrich airport markers with distance from pilot
  function enrichAirportMarkersWithDistance(pLat, pLon) {
      if (!map || !map.eachLayer) return;
      map.eachLayer(function(layer) {
          if (!layer._layers) return;
          for (var lid in layer._layers) {
              var marker = layer._layers[lid];
              if (!marker.getLatLng || !marker.getPopup) continue;
              var mll = marker.getLatLng(), popup = marker.getPopup();
              if (!popup) continue;
              var orig = popup.getContent();
              if (!orig || orig.indexOf('Open NOTAM') === -1) continue;
              var distKm = haversineKm(pLat, pLon, mll.lat, mll.lng);
              var distNm = (distKm / 1.852).toFixed(2);
              var add = '<div style="margin-top:8px; padding-top:8px; border-top:1px solid #ddd; font-size:0.9em;">' +
                  '<div><strong>Distance:</strong> ' + distKm.toFixed(2) + ' km / ' + distNm + ' nm</div>' +
                  '<div style="margin-top:4px;"><strong>Airport (DD):</strong> ' + mll.lat.toFixed(6) + ', ' + mll.lng.toFixed(6) + '</div>' +
                  '<div style="margin-top:4px;"><strong>Pilot (DD):</strong> ' + pLat.toFixed(6) + ', ' + pLon.toFixed(6) + '</div></div>';
              marker.setPopupContent(orig + add);
          }
      });
  }
'''

# Find insertion point: after getActiveNotams function starts, insert before it
insert_point = '  function getActiveNotams() {'
if insert_point not in original:
    print("Could not find insertion point", file=sys.stderr)
    sys.exit(1)

# Insert enrichment function
modified = original.replace(insert_point, enrich_func + '\n\n  function getActiveNotams() {')

# Also add the call in applyPilotLocation
call_point = '      updatePilotObstacleContext(ll);'
if call_point in modified:
    modified = modified.replace(call_point, call_point + '\n      enrichAirportMarkersWithDistance(ll.lat, ll.lng);')
else:
    print("Warning: Could not find call insertion point", file=sys.stderr)

# Write back
try:
    with open(file_path, 'w', encoding='utf-8') as dst:
        dst.write(modified)
    new_size = len(modified)
    old_size = len(original)
    print(f"Success! File size: {old_size} → {new_size} bytes (+{new_size - old_size})")
except Exception as e:
    print(f"Error writing: {e}", file=sys.stderr)
    sys.exit(1)
