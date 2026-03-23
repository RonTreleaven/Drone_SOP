from pathlib import Path

file_path = Path(r"C:\Users\Ron Treleaven\Drone_SOP\v3NotamMap.html")
text = file_path.read_text(encoding="utf-8")
original = text

old_enrich_block = '''  // Enrich airport markers with distance from pilot
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

new_enrich_block = '''  // Enrich airport markers with distance from pilot
  function enrichAirportMarkersWithDistance(pLat, pLon) {
      if (!airportLayerIndex) return;

      function asHtmlString(content) {
          if (!content) return '';
          if (typeof content === 'string') return content;
          if (content.outerHTML) return content.outerHTML;
          if (content.innerHTML) return content.innerHTML;
          return String(content);
      }

      function walkLayer(layer, visitor) {
          if (!layer) return;
          if (layer.getLatLng && layer.getPopup) {
              visitor(layer);
              return;
          }
          if (typeof layer.eachLayer === 'function') {
              layer.eachLayer(function(child) {
                  walkLayer(child, visitor);
              });
              return;
          }
          if (typeof layer.getLayers === 'function') {
              layer.getLayers().forEach(function(child) {
                  walkLayer(child, visitor);
              });
          }
      }

      function buildDistanceHtml(markerLatLng) {
          var distKm = haversineKm(pLat, pLon, markerLatLng.lat, markerLatLng.lng);
          var distNm = distKm / 1.852;
          return '<div class="airport-distance-meta" style="margin-top:8px; padding-top:8px; border-top:1px solid #ddd; font-size:0.9em;">' +
              '<div><strong>Distance:</strong> ' + distKm.toFixed(2) + ' km / ' + distNm.toFixed(2) + ' nm</div>' +
              '<div style="margin-top:4px;"><strong>Airport (DD):</strong> ' + markerLatLng.lat.toFixed(6) + ', ' + markerLatLng.lng.toFixed(6) + '</div>' +
              '<div style="margin-top:4px;"><strong>Pilot (DD):</strong> ' + pLat.toFixed(6) + ', ' + pLon.toFixed(6) + '</div>' +
              '</div>';
      }

      function buildTooltipHtml(baseHtml, markerLatLng) {
          var distKm = haversineKm(pLat, pLon, markerLatLng.lat, markerLatLng.lng);
          var distNm = distKm / 1.852;
          return '<div>' +
              baseHtml + '<br>' +
              'Dist: ' + distKm.toFixed(2) + ' km / ' + distNm.toFixed(2) + ' nm<br>' +
              'DD: ' + markerLatLng.lat.toFixed(6) + ', ' + markerLatLng.lng.toFixed(6) +
              '</div>';
      }

      Object.keys(airportLayerIndex).forEach(function(provinceCode) {
          var typeMap = airportLayerIndex[provinceCode];
          Object.keys(typeMap).forEach(function(typeName) {
              walkLayer(typeMap[typeName], function(markerLayer) {
                  var markerLatLng = markerLayer.getLatLng();
                  var popup = markerLayer.getPopup ? markerLayer.getPopup() : null;
                  var tooltip = markerLayer.getTooltip ? markerLayer.getTooltip() : null;

                  if (popup) {
                      if (!markerLayer._baseAirportPopupHtml) {
                          markerLayer._baseAirportPopupHtml = asHtmlString(popup.getContent());
                      }
                      if (markerLayer._baseAirportPopupHtml.indexOf('Open NOTAM focus') > -1) {
                          markerLayer.setPopupContent(markerLayer._baseAirportPopupHtml + buildDistanceHtml(markerLatLng));
                      }
                  }

                  if (tooltip) {
                      if (!markerLayer._baseAirportTooltipHtml) {
                          markerLayer._baseAirportTooltipHtml = asHtmlString(tooltip.getContent());
                      }
                      markerLayer.setTooltipContent(buildTooltipHtml(markerLayer._baseAirportTooltipHtml, markerLatLng));
                  }
              });
          });
      });
  }
'''

if old_enrich_block in text:
    text = text.replace(old_enrich_block, new_enrich_block, 1)
elif 'function enrichAirportMarkersWithDistance(pLat, pLon)' in text and 'airport-distance-meta' not in text:
    start = text.index('  // Enrich airport markers with distance from pilot')
    end = text.index('\n\n  function getActiveNotams() {', start)
    text = text[:start] + new_enrich_block + text[end:]

circle_anchor = '\n    updatePilotDisplay(startupPilotLocation);'
if 'Airport Circle Layers' not in text and circle_anchor in text:
    circle_block = '''

    // Airspace circles + legend toggles by airport type
    (function buildAirportCircles() {
        var NM_TO_M = 1852;
        var circleTypes = ['large_airport', 'medium_airport', 'small_airport', 'heliport', 'seaplane_base'];
        var circleConfig = {
            large_airport:  { label: 'Large Airport', radiusNm: 5, color: '#e53935', fillOpacity: 0.08 },
            medium_airport: { label: 'Medium Airport', radiusNm: 3, color: '#fb8c00', fillOpacity: 0.10 },
            small_airport:  { label: 'Small Airport', radiusNm: 1, color: '#8e24aa', fillOpacity: 0.10 },
            heliport:       { label: 'Heliport', radiusNm: 1, color: '#00897b', fillOpacity: 0.10 },
            seaplane_base:  { label: 'Seaplane Base', radiusNm: 1, color: '#0288d1', fillOpacity: 0.10 }
        };
        var circleLayersByType = {};
        var circleEnabledByType = {};
        var rowsByType = {};

        function walkLayer(layer, visitor) {
            if (!layer) return;
            if (layer.getLatLng) {
                visitor(layer);
                return;
            }
            if (typeof layer.eachLayer === 'function') {
                layer.eachLayer(function(child) {
                    walkLayer(child, visitor);
                });
                return;
            }
            if (typeof layer.getLayers === 'function') {
                layer.getLayers().forEach(function(child) {
                    walkLayer(child, visitor);
                });
            }
        }

        function setCircleOnly(type, enabled) {
            var layer = circleLayersByType[type];
            if (!layer) return;
            circleEnabledByType[type] = !!enabled;
            if (enabled) {
                if (!map.hasLayer(layer)) layer.addTo(map);
            } else if (map.hasLayer(layer)) {
                map.removeLayer(layer);
            }
            var row = rowsByType[type];
            if (row) {
                row.style.opacity = enabled ? '1' : '0.55';
                var status = row.querySelector('[data-role="status"]');
                if (status) status.textContent = enabled ? 'On' : 'Off';
            }
        }

        function setTypeVisibilityBoth(type, enabled) {
            setCircleOnly(type, enabled);
            Object.keys(airportLayerIndex).forEach(function(provinceCode) {
                var group = airportLayerIndex[provinceCode][type];
                if (!group) return;
                if (enabled) {
                    if (!map.hasLayer(group)) group.addTo(map);
                } else if (map.hasLayer(group)) {
                    map.removeLayer(group);
                }
            });
        }

        circleTypes.forEach(function(type) {
            circleLayersByType[type] = L.layerGroup().addTo(map);
            circleEnabledByType[type] = true;
        });

        Object.keys(airportLayerIndex).forEach(function(provinceCode) {
            var types = airportLayerIndex[provinceCode];
            circleTypes.forEach(function(aptType) {
                var cfg = circleConfig[aptType];
                var subGroup = types[aptType];
                if (!cfg || !subGroup) return;
                walkLayer(subGroup, function(markerLayer) {
                    if (!markerLayer.getLatLng) return;
                    L.circle(markerLayer.getLatLng(), {
                        radius: cfg.radiusNm * NM_TO_M,
                        color: cfg.color,
                        weight: 1.5,
                        fill: true,
                        fillColor: cfg.color,
                        fillOpacity: cfg.fillOpacity,
                        interactive: false
                    }).addTo(circleLayersByType[aptType]);
                });
            });
        });

        var circleLegendControl = L.control({ position: 'bottomleft' });
        circleLegendControl.onAdd = function() {
            var container = L.DomUtil.create('div');
            container.style.background = 'rgba(255, 255, 255, 0.96)';
            container.style.border = '1px solid #d8e2ee';
            container.style.borderRadius = '8px';
            container.style.boxShadow = '0 2px 6px rgba(0,0,0,0.18)';
            container.style.padding = '8px 8px 6px';
            container.style.minWidth = '220px';
            container.style.fontSize = '12px';
            container.style.lineHeight = '1.25';

            var title = document.createElement('div');
            title.textContent = 'Airport Circle Layers';
            title.style.fontWeight = '700';
            title.style.color = '#1f3b63';
            title.style.marginBottom = '6px';
            container.appendChild(title);

            circleTypes.forEach(function(type) {
                var cfg = circleConfig[type];
                var row = document.createElement('button');
                row.type = 'button';
                row.style.display = 'flex';
                row.style.alignItems = 'center';
                row.style.width = '100%';
                row.style.gap = '8px';
                row.style.padding = '4px 2px';
                row.style.border = 'none';
                row.style.background = 'transparent';
                row.style.cursor = 'pointer';
                row.style.textAlign = 'left';

                var swatch = document.createElement('span');
                swatch.style.width = '12px';
                swatch.style.height = '12px';
                swatch.style.borderRadius = '50%';
                swatch.style.background = cfg.color;
                swatch.style.border = '1px solid rgba(0,0,0,0.2)';

                var label = document.createElement('span');
                label.textContent = cfg.label + ' (' + cfg.radiusNm + ' NM)';
                label.style.flex = '1';
                label.style.color = '#1f3b63';

                var status = document.createElement('span');
                status.setAttribute('data-role', 'status');
                status.style.fontWeight = '700';
                status.style.color = '#4a5568';
                status.textContent = 'On';

                row.appendChild(swatch);
                row.appendChild(label);
                row.appendChild(status);
                row.addEventListener('click', function() {
                    setTypeVisibilityBoth(type, !circleEnabledByType[type]);
                });

                rowsByType[type] = row;
                container.appendChild(row);
            });

            var hint = document.createElement('div');
            hint.textContent = 'Click a row to toggle';
            hint.style.marginTop = '4px';
            hint.style.fontSize = '11px';
            hint.style.color = '#6b7280';
            container.appendChild(hint);

            L.DomEvent.disableClickPropagation(container);
            L.DomEvent.disableScrollPropagation(container);
            return container;
        };

        circleLegendControl.addTo(map);

        var layerToTypeMap = {};
        Object.keys(airportLayerIndex).forEach(function(provinceCode) {
            var types = airportLayerIndex[provinceCode];
            circleTypes.forEach(function(type) {
                var group = types[type];
                if (group && group._leaflet_id) {
                    layerToTypeMap[group._leaflet_id] = type;
                }
            });
        });

        map.on('overlayadd', function(e) {
            if (!e || !e.layer || !e.layer._leaflet_id) return;
            var type = layerToTypeMap[e.layer._leaflet_id];
            if (type) setCircleOnly(type, true);
        });

        map.on('overlayremove', function(e) {
            if (!e || !e.layer || !e.layer._leaflet_id) return;
            var type = layerToTypeMap[e.layer._leaflet_id];
            if (type) setCircleOnly(type, false);
        });

        window._airportCircleLayersByType = circleLayersByType;
        window._airportCircleEnabledByType = circleEnabledByType;
        window._airportCircleLegendControl = circleLegendControl;
    })();
    // End airspace circles + legend
'''
    text = text.replace(circle_anchor, circle_block + circle_anchor, 1)

if text != original:
    file_path.write_text(text, encoding="utf-8")
    print("Updated v3NotamMap.html")
else:
    print("No changes applied")
