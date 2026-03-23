from pathlib import Path

file_path = Path(r"C:\Users\Ron Treleaven\Drone_SOP\v3NotamMap.html")
text = file_path.read_text(encoding="utf-8")
original = text

anchor = "      function buildTooltipHtml(baseHtml, markerLatLng) {"
insert_block = '''      function extractAirportCode(html) {
          if (!html) return null;
          var plain = String(html).replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim();
          var m = plain.match(/^([A-Z0-9-]{3,10})\s*[\-|]/);
          return m ? m[1] : null;
      }

      function buildExternalLinkPopupHtml(code) {
          if (!code) return '<div style="font-size:0.95em;">Airport link unavailable</div>';
          var isIcao = /^[A-Z0-9]{4}$/.test(code);
          var label = isIcao ? 'Skyvector' : 'OurAirports';
          var url = isIcao
              ? ('https://skyvector.com/airport/' + encodeURIComponent(code))
              : ('https://ourairports.com/airports/' + encodeURIComponent(code));
          return '<div style="font-size:0.95em;">' +
              '<a href="' + url + '" target="_blank" rel="noopener noreferrer">' + code + ' ' + label + '</a>' +
              '</div>';
      }

'''

if insert_block not in text and anchor in text:
    text = text.replace(anchor, insert_block + anchor, 1)

old_popup_logic = '''                  if (popup) {
                      if (!markerLayer._baseAirportPopupHtml) {
                          markerLayer._baseAirportPopupHtml = asHtmlString(popup.getContent());
                      }
                      if (markerLayer._baseAirportPopupHtml.indexOf('Open NOTAM focus') > -1) {
                          markerLayer.setPopupContent(markerLayer._baseAirportPopupHtml + buildDistanceHtml(markerLatLng));
                      }
                  }
'''

new_popup_logic = '''                  if (popup) {
                      if (!markerLayer._baseAirportPopupHtml) {
                          markerLayer._baseAirportPopupHtml = asHtmlString(popup.getContent());
                      }
                      var codeFromPopup = extractAirportCode(markerLayer._baseAirportPopupHtml);
                      var codeFromTooltip = markerLayer._baseAirportTooltipHtml
                          ? extractAirportCode(markerLayer._baseAirportTooltipHtml)
                          : null;
                      var airportCode = codeFromPopup || codeFromTooltip;
                      markerLayer.setPopupContent(buildExternalLinkPopupHtml(airportCode));
                  }
'''

if old_popup_logic in text:
    text = text.replace(old_popup_logic, new_popup_logic, 1)

if text != original:
    file_path.write_text(text, encoding="utf-8")
    print("Updated popup link mode in v3NotamMap.html")
else:
    print("No changes applied")
