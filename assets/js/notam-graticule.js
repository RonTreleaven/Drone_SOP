function initNotamGraticule(map, pilotMarker) {

  var COLOR = '#4a0d36';
  var VNC_SCALE = 500000;
  var CSS_PX_M = 0.0254 / 96;
  var enabled = true;

  var gpane = map.createPane('graticulePane');
  gpane.style.zIndex = 450;
  gpane.style.pointerEvents = 'none';
  var canvas = L.DomUtil.create('canvas', 'gr-canvas', gpane);
  var ctx = canvas.getContext('2d');

  function fmt(valDeg, isLat) {
    var hemi = isLat ? (valDeg >= 0 ? 'N' : 'S') : (valDeg >= 0 ? 'E' : 'W');
    var totalMin = Math.round(Math.abs(valDeg) * 60);
    var d = Math.floor(totalMin / 60);
    var m = totalMin % 60;
    return d + '\u00B0' + (m < 10 ? '0' : '') + m + '\u2032' + hemi;
  }

  function tickLen(min) {
    if (min % 15 === 0) { return { len: 20, w: 2 }; }
    if (min % 10 === 0) { return { len: 15, w: 2 }; }
    if (min % 5 === 0) { return { len: 11, w: 1.75 }; }
    return { len: 6, w: 1.25 };
  }

  function lineStepMin(pxPer15) {
    if (pxPer15 >= 50) { return 15; }
    return pxPer15 * 2 >= 50 ? 30 : 60;
  }

  function label(text, x, y, align, base) {
    ctx.font = '600 11px Arial, Helvetica, sans-serif';
    ctx.textAlign = align;
    ctx.textBaseline = base;
    ctx.lineWidth = 3;
    ctx.strokeStyle = '#fff';
    ctx.strokeText(text, x, y);
    ctx.fillStyle = COLOR;
    ctx.fillText(text, x, y);
  }

  function drawGrid() {
    var size = map.getSize();
    L.DomUtil.setPosition(canvas, map.containerPointToLayerPoint([0, 0]));
    var dpr = window.devicePixelRatio || 1;
    canvas.width = size.x * dpr;
    canvas.height = size.y * dpr;
    canvas.style.width = size.x + 'px';
    canvas.style.height = size.y + 'px';
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, size.x, size.y);
    if (!enabled) { return; }

    var b = map.getBounds();
    var c = map.getCenter();
    var west = b.getWest(), east = b.getEast();
    var south = Math.max(b.getSouth(), -85), north = Math.min(b.getNorth(), 85);

    var pxLon1 = Math.abs(map.latLngToContainerPoint([c.lat, c.lng + 1 / 60]).x -
                          map.latLngToContainerPoint([c.lat, c.lng]).x);
    var pxLat1 = Math.abs(map.latLngToContainerPoint([c.lat + 1 / 60, c.lng]).y -
                          map.latLngToContainerPoint([c.lat, c.lng]).y);
    var tickMin = (Math.min(pxLon1, pxLat1) >= 4) ? 1 : (Math.min(pxLon1, pxLat1) * 5 >= 4 ? 5 : 15);
    var lineMin = lineStepMin(Math.min(pxLon1, pxLat1) * 15);

    ctx.strokeStyle = COLOR;

    // Full lines (every 15' when space allows)
    ctx.lineWidth = 1;
    ctx.globalAlpha = 0.9;
    ctx.beginPath();
    var latLine0 = Math.ceil(south * 60 / lineMin - 1e-9);
    for (var i = latLine0; i * lineMin / 60 <= north; i++) {
      var yl = map.latLngToContainerPoint([i * lineMin / 60, c.lng]).y;
      ctx.moveTo(0, yl); ctx.lineTo(size.x, yl);
    }
    var lonLine0 = Math.ceil(west * 60 / lineMin - 1e-9);
    for (var j = lonLine0; j * lineMin / 60 <= east; j++) {
      var xl = map.latLngToContainerPoint([c.lat, j * lineMin / 60]).x;
      ctx.moveTo(xl, 0); ctx.lineTo(xl, size.y);
    }
    ctx.stroke();
    ctx.globalAlpha = 1;

    var k, t, pt, minV, i2;

    // Ticks along every graticule line (skipping spots where the two line sets cross)
    var latLines = [], lonLines = [];
    for (i2 = latLine0; i2 * lineMin / 60 <= north; i2++) {
      latLines.push(map.latLngToContainerPoint([i2 * lineMin / 60, c.lng]).y);
    }
    for (i2 = lonLine0; i2 * lineMin / 60 <= east; i2++) {
      lonLines.push(map.latLngToContainerPoint([c.lat, i2 * lineMin / 60]).x);
    }

    var lonTickStart = Math.ceil(west * 60 / tickMin - 1e-9);
    for (k = lonTickStart; k * tickMin / 60 <= east; k++) {
      minV = k * tickMin;
      if (minV % lineMin === 0) { continue; }
      t = tickLen(minV);
      pt = map.latLngToContainerPoint([c.lat, minV / 60]).x;
      ctx.lineWidth = t.w;
      ctx.beginPath();
      for (i2 = 0; i2 < latLines.length; i2++) {
        ctx.moveTo(pt, latLines[i2] - t.len / 2);
        ctx.lineTo(pt, latLines[i2] + t.len / 2);
      }
      ctx.stroke();
    }
    var latTickStart = Math.ceil(south * 60 / tickMin - 1e-9);
    for (k = latTickStart; k * tickMin / 60 <= north; k++) {
      minV = k * tickMin;
      if (minV % lineMin === 0) { continue; }
      t = tickLen(minV);
      pt = map.latLngToContainerPoint([minV / 60, c.lng]).y;
      ctx.lineWidth = t.w;
      ctx.beginPath();
      for (i2 = 0; i2 < lonLines.length; i2++) {
        ctx.moveTo(lonLines[i2] - t.len / 2, pt);
        ctx.lineTo(lonLines[i2] + t.len / 2, pt);
      }
      ctx.stroke();
    }

    // Labels at the map edges for each graticule line
    for (i2 = 0; i2 < latLines.length; i2++) {
      if (latLines[i2] > 14 && latLines[i2] < size.y - 14) {
        label(fmt((latLine0 + i2) * lineMin / 60, true), size.x - 6, latLines[i2], 'right', 'middle');
      }
    }
    for (i2 = 0; i2 < lonLines.length; i2++) {
      if (lonLines[i2] > 40 && lonLines[i2] < size.x - 40) {
        label(fmt((lonLine0 + i2) * lineMin / 60, false), lonLines[i2], 6, 'center', 'top');
      }
    }
  }

  var PILOT_COLOR = '#ff2d95';
  var pilotLinesEnabled = true;

  function fmtDMS(valDeg, isLat) {
    var hemi = isLat ? (valDeg >= 0 ? 'N' : 'S') : (valDeg >= 0 ? 'E' : 'W');
    var totalSeconds = Math.round(Math.abs(valDeg) * 3600);
    var d = Math.floor(totalSeconds / 3600);
    var m = Math.floor((totalSeconds % 3600) / 60);
    var s = totalSeconds % 60;
    return d + '\u00B0 ' + (m < 10 ? '0' : '') + m + '\u2032 ' + (s < 10 ? '0' : '') + s + '\u2033 ' + hemi;
  }

  window.pilotPopupHtml = function (ll) {
    return '<div class="pilot-coordinates"><div class="pilot-heading">Pilot</div>' +
      '<div class="pilot-coordinate">Lat: ' + ll.lat.toFixed(6) + '</div>' +
      '<div class="pilot-coordinate">Lon: ' + ll.lng.toFixed(6) + '</div>' +
      '<div class="pilot-coordinate"><b>Lat: ' + fmtDMS(ll.lat, true) + '</b></div>' +
      '<div class="pilot-coordinate"><b>Lon: ' + fmtDMS(ll.lng, false) + '</b></div></div>';
  };

  function currentLineMin() {
    var c = map.getCenter();
    var px = Math.min(
      Math.abs(map.latLngToContainerPoint([c.lat, c.lng + 1 / 60]).x - map.latLngToContainerPoint([c.lat, c.lng]).x),
      Math.abs(map.latLngToContainerPoint([c.lat + 1 / 60, c.lng]).y - map.latLngToContainerPoint([c.lat, c.lng]).y));
    return lineStepMin(px * 15);
  }

  function drawPilotLines() {
    if (!pilotLinesEnabled || !pilotMarker) { return; }
    var ll = pilotMarker.getLatLng();
    var lineMin = currentLineMin();
    var latMin = ll.lat * 60, lonMin = ll.lng * 60;
    var nLat = Math.round(latMin / lineMin) * lineMin;
    var nLon = Math.round(lonMin / lineMin) * lineMin;
    var p = map.latLngToContainerPoint(ll);
    var pLat = map.latLngToContainerPoint([nLat / 60, ll.lng]);
    var pLon = map.latLngToContainerPoint([ll.lat, nLon / 60]);

    ctx.save();
    ctx.strokeStyle = PILOT_COLOR;
    ctx.lineWidth = 2.5;
    ctx.setLineDash([6, 4]);
    ctx.beginPath();
    ctx.moveTo(p.x, p.y); ctx.lineTo(pLat.x, pLat.y);
    ctx.moveTo(p.x, p.y); ctx.lineTo(pLon.x, pLon.y);
    ctx.stroke();
    ctx.setLineDash([]);

    function tag(text, x, y) {
      ctx.font = '700 11px Arial, Helvetica, sans-serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.lineWidth = 3;
      ctx.strokeStyle = '#fff';
      ctx.strokeText(text, x, y);
      ctx.fillStyle = PILOT_COLOR;
      ctx.fillText(text, x, y);
    }
    var dLat = Math.abs(latMin - nLat), dLon = Math.abs(lonMin - nLon);
    tag(dLat.toFixed(3) + '\u2032', p.x + 28, (p.y + pLat.y) / 2);
    tag(dLon.toFixed(3) + '\u2032', (p.x + pLon.x) / 2, p.y - 12);
    ctx.restore();
  }

  function draw() {
    drawGrid();
    drawPilotLines();
  }

  function zoomForScale(lat, scale) {
    var mPerPx = scale * CSS_PX_M;
    return Math.log(156543.03392 * Math.cos(lat * Math.PI / 180) / mPerPx) / Math.LN2;
  }

  var ctl = L.control({ position: 'topright' });
  ctl.onAdd = function () {
    var div = L.DomUtil.create('div', 'leaflet-bar gr-ctl');
    div.innerHTML =
      '<a href="#" class="gr-toggle gr-on" title="Toggle lat/lon graticule" role="button" aria-label="Toggle lat/lon graticule">' +
      '<svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true">' +
      '<circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" stroke-width="1.6"/>' +
      '<polygon points="12,3.5 15,12 12,10.5 9,12" fill="currentColor"/>' +
      '<polygon points="12,20.5 15,12 12,13.5 9,12" fill="none" stroke="currentColor" stroke-width="1.2"/>' +
      '</svg></a>' +
      '<a href="#" class="gr-pilot gr-on" title="Toggle pilot-to-graticule lines" role="button" aria-label="Toggle pilot-to-graticule lines">' +
      '<svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true">' +
      '<circle cx="12" cy="12" r="3" fill="currentColor"/>' +
      '<path d="M12 2v6M12 16v6M2 12h6M16 12h6" stroke="currentColor" stroke-width="1.8" fill="none" stroke-dasharray="2 1.5"/>' +
      '</svg></a>' +
      '<a href="#" class="gr-scale" title="Zoom to 1:500,000 (VNC scale)" role="button">1:500k</a>';
    L.DomEvent.disableClickPropagation(div);
    var pilotBtn = div.querySelector('.gr-pilot');
    L.DomEvent.on(pilotBtn, 'click', function (e) {
      L.DomEvent.preventDefault(e);
      pilotLinesEnabled = !pilotLinesEnabled;
      pilotBtn.classList.toggle('gr-on', pilotLinesEnabled);
      draw();
    });
    var toggle = div.querySelector('.gr-toggle');
    L.DomEvent.on(toggle, 'click', function (e) {
      L.DomEvent.preventDefault(e);
      enabled = !enabled;
      toggle.classList.toggle('gr-on', enabled);
      draw();
    });
    L.DomEvent.on(div.querySelector('.gr-scale'), 'click', function (e) {
      L.DomEvent.preventDefault(e);
      map.options.zoomSnap = 0;
      map.setZoom(zoomForScale(map.getCenter().lat, VNC_SCALE));
    });
    return div;
  };

  ctl.addTo(map);
  map.on('move zoom resize', draw);
  if (pilotMarker) {
    pilotMarker.getPopup().options.minWidth = 180;
    pilotMarker.getPopup().options.maxWidth = 260;
    pilotMarker.on('move', draw);
    pilotMarker.setPopupContent(window.pilotPopupHtml(pilotMarker.getLatLng()));
  }
  draw();
  window.__graticule = { draw: draw };
}
