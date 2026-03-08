// assets/js/app.js
// RLT May 2025 – Final step always goes to Flight Log

const FLIGHT_RUN_STORAGE_KEYS = [
  'flightLog',
  'flightDate',
  'flightPilot',
  'flightObservers',
  'flightStart',
  'flightEnd',
  'flightLocation'
];

function safeParseJSON(key, fallback = {}) {
  try {
    return JSON.parse(localStorage.getItem(key) || JSON.stringify(fallback));
  } catch (_err) {
    return fallback;
  }
}

function clearFlightRunData() {
  FLIGHT_RUN_STORAGE_KEYS.forEach(key => localStorage.removeItem(key));
}

function parseLatLonText(value) {
  if (!value || typeof value !== 'string') return null;
  const m = value.trim().match(/^\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*$/);
  if (!m) return null;
  const lat = Number(m[1]);
  const lon = Number(m[2]);
  if (!Number.isFinite(lat) || !Number.isFinite(lon)) return null;
  if (lat < -90 || lat > 90 || lon < -180 || lon > 180) return null;
  return { lat, lon };
}

function toDMS(deg, isLat) {
  const abs = Math.abs(deg);
  const d = Math.floor(abs);
  const mFloat = (abs - d) * 60;
  const m = Math.floor(mFloat);
  const s = ((mFloat - m) * 60).toFixed(1);
  const dir = isLat
    ? (deg >= 0 ? 'N' : 'S')
    : (deg >= 0 ? 'E' : 'W');
  return `${d}\u00B0${m}'${s}"${dir}`;
}

function savePilotLocation(lat, lon, source = 'manual') {
  const latShort = Number(lat).toFixed(6);
  const lonShort = Number(lon).toFixed(6);
  const latDMS = toDMS(Number(lat), true);
  const lonDMS = toDMS(Number(lon), false);

  localStorage.setItem('pilotLocationDD', `${latShort}, ${lonShort}`);
  localStorage.setItem('pilotLocationDMS', `${latDMS}, ${lonDMS}`);
  localStorage.setItem('pilotLatitude', latShort);
  localStorage.setItem('pilotLongitude', lonShort);
  localStorage.setItem('pilotLocationSource', source);

  return { latShort, lonShort, latDMS, lonDMS };
}

document.addEventListener('DOMContentLoaded', () => {
  // Flight Log page does not require sections.json; initialize immediately.
  if (document.getElementById('flight-log-form')) {
    renderFlightLog();
    return;
  }

  const jsonPath = window.location.pathname.includes('/sections/')
    ? '../data/sections.json'
    : './data/sections.json';

  fetch(jsonPath)
    .then(res => {
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return res.json();
    })
    .then(sections => initApp(sections))
    .catch(err => {
      console.error('Could not load sections.json', err);
      const sel = document.getElementById('section-selector');
      if (sel) sel.textContent = 'Error loading sections — check console';
    });
});

function initApp(sections) {
  if (document.getElementById('section-selector')) {
    renderIndex(sections);
  } else if (document.getElementById('checklist-container')) {
    renderSectionPage(sections);
  } else if (document.getElementById('summary-container')) {
    renderSummary(sections);
  }
}

// ─── INDEX ────────────────────────────────────────────────────────────────────
function renderIndex(sections) {
  const container = document.getElementById('section-selector');
  const btn       = document.getElementById('begin-btn');
  const chosen    = new Set();

  sections.forEach(sec => {
    const label = document.createElement('label');
    label.style.cursor = 'pointer';
    const cb = document.createElement('input');
    cb.type  = 'checkbox';
    cb.value = sec.id;
    cb.addEventListener('change', () => {
      if (cb.checked) chosen.add(cb.value);
      else chosen.delete(cb.value);
      btn.disabled = chosen.size === 0;
    });
    label.append(cb, ' ', sec.title);
    container.append(label);
  });

  btn.addEventListener('click', () => {
    const list = Array.from(chosen);
    if (!list.length) return;
    // Clear prior run data so summary/export only reflect the current run.
    localStorage.removeItem('droneSOPProgress');
    clearFlightRunData();
    // Initialize new progress structure
    const progress = {};
    list.forEach(id => {
      progress[id] = { status: 'not-started', data: {} };
    });
    const sopProgress = { selectedSOPs: list, progress };
    localStorage.setItem('droneSOPProgress', JSON.stringify(sopProgress));
    // Go to first section
    window.location.href = `sections/${list[0]}.html`;
  });

  setupIndexLocationCard();
}

function setupIndexLocationCard() {
  const locBtn = document.getElementById('index-get-location');
  const out = document.getElementById('index-location-output');
  if (!locBtn || !out) return;

  const renderOutput = (ddText, dmsText) => {
    out.innerHTML =
      `DD: ${ddText}<br>` +
      `DMS: ${dmsText}<br>` +
      `<a href="https://maps.google.com/?q=${ddText.replace(/\s/g, '')}" target="_blank" rel="noopener">View on Google Maps</a>`;
  };

  const dd = localStorage.getItem('pilotLocationDD') || '';
  const parsed = parseLatLonText(dd);
  if (parsed) {
    const saved = savePilotLocation(parsed.lat, parsed.lon, localStorage.getItem('pilotLocationSource') || 'restored');
    renderOutput(`${saved.latShort}, ${saved.lonShort}`, `${saved.latDMS}, ${saved.lonDMS}`);
  }

  locBtn.addEventListener('click', () => {
    if (!navigator.geolocation) {
      out.textContent = 'Geolocation is not supported by this browser.';
      return;
    }

    navigator.geolocation.getCurrentPosition(
      position => {
        const saved = savePilotLocation(position.coords.latitude, position.coords.longitude, 'index');
        renderOutput(`${saved.latShort}, ${saved.lonShort}`, `${saved.latDMS}, ${saved.lonDMS}`);
      },
      error => {
        switch (error.code) {
          case error.PERMISSION_DENIED:
            out.textContent = 'User denied the request for Geolocation.';
            break;
          case error.POSITION_UNAVAILABLE:
            out.textContent = 'Location information is unavailable.';
            break;
          case error.TIMEOUT:
            out.textContent = 'The request to get user location timed out.';
            break;
          default:
            out.textContent = 'An unknown error occurred.';
            break;
        }
      },
      { enableHighAccuracy: true, timeout: 12000, maximumAge: 300000 }
    );
  });
}

// ─── FLIGHT LOG ────────────────────────────────────────────────────────────────
function renderFlightLog() {
  const form   = document.getElementById('flight-log-form');
  const dateIn = document.getElementById('flight-date');
  const pilot  = document.getElementById('flight-pilot');
  const obs    = document.getElementById('flight-observers');
  const start  = document.getElementById('flight-start');
  const end    = document.getElementById('flight-end');
  const loc    = document.getElementById('flight-location');
  const btn    = document.getElementById('getLocation');
  const output = document.getElementById('output');

  const writePilotLocationToStorage = (lat, lon, source = 'manual') => {
    return savePilotLocation(lat, lon, source);
  };

  const renderPilotLocationOutput = (ddText, dmsText) => {
    if (!output) return;
    const mapQ = ddText.replace(/\s/g, '');
    output.innerHTML =
      `DD: ${ddText}<br>` +
      (dmsText ? `DMS: ${dmsText}<br>` : '') +
      `<a href="https://maps.google.com/?q=${mapQ}" target="_blank" rel="noopener">View on Google Maps</a>`;
  };

  const saved = safeParseJSON('flightLog', {});

  dateIn.value = saved.date || localStorage.getItem('flightDate') || new Date().toISOString().split('T')[0];
  pilot.value  = saved.pilot || localStorage.getItem('flightPilot') || '';
  obs.value    = saved.observers || localStorage.getItem('flightObservers') || '';
  start.value  = saved.start || localStorage.getItem('flightStart') || '';
  end.value    = saved.end || localStorage.getItem('flightEnd') || '';
  loc.value    = saved.location || localStorage.getItem('flightLocation') || '';

  const dd = localStorage.getItem('pilotLocationDD');
  const dms = localStorage.getItem('pilotLocationDMS');
  const parsedFromDD = parseLatLonText(dd || '');
  const parsedFromInput = parseLatLonText(loc.value || '');
  const restored = parsedFromDD || parsedFromInput;

  if (restored) {
    const stored = writePilotLocationToStorage(restored.lat, restored.lon, localStorage.getItem('pilotLocationSource') || 'restored');
    renderPilotLocationOutput(`${stored.latShort}, ${stored.lonShort}`, `${stored.latDMS}, ${stored.lonDMS}`);
    loc.value = `${stored.latShort}, ${stored.lonShort}`;
  }

  if (btn) {
    btn.addEventListener('click', () => {
      if (!navigator.geolocation) {
        if (output) output.textContent = 'Geolocation is not supported by this browser.';
        return;
      }

      navigator.geolocation.getCurrentPosition(
        (position) => {
          const latitude = position.coords.latitude;
          const longitude = position.coords.longitude;
          const latShort = latitude.toFixed(6);
          const lonShort = longitude.toFixed(6);
          const savedLoc = writePilotLocationToStorage(latitude, longitude, 'geolocation');

          renderPilotLocationOutput(`${latShort}, ${lonShort}`, `${savedLoc.latDMS}, ${savedLoc.lonDMS}`);

          loc.value = `${latShort}, ${lonShort}`;
        },
        (error) => {
          if (!output) return;
          switch (error.code) {
            case error.PERMISSION_DENIED:
              output.textContent = 'User denied the request for Geolocation.';
              break;
            case error.POSITION_UNAVAILABLE:
              output.textContent = 'Location information is unavailable.';
              break;
            case error.TIMEOUT:
              output.textContent = 'The request to get user location timed out.';
              break;
            default:
              output.textContent = 'An unknown error occurred.';
              break;
          }
        }
      );
    });
  }

  form.addEventListener('submit', e => {
    e.preventDefault();
    const flightLog = {
      date:      dateIn.value,
      pilot:     pilot.value.trim(),
      observers: obs.value.trim(),
      start:     start.value,
      end:       end.value,
      location:  loc.value.trim()
    };

    localStorage.setItem('flightLog', JSON.stringify(flightLog));
    localStorage.setItem('flightDate', flightLog.date || '');
    localStorage.setItem('flightPilot', flightLog.pilot || '');
    localStorage.setItem('flightObservers', flightLog.observers || '');
    localStorage.setItem('flightStart', flightLog.start || '');
    localStorage.setItem('flightEnd', flightLog.end || '');
    localStorage.setItem('flightLocation', flightLog.location || '');
    const parsed = parseLatLonText(flightLog.location);
    if (parsed) {
      const saved = writePilotLocationToStorage(parsed.lat, parsed.lon, 'flight-log');
      renderPilotLocationOutput(`${saved.latShort}, ${saved.lonShort}`, `${saved.latDMS}, ${saved.lonDMS}`);
    }

    alert('✅ Flight log saved.');
  });
}

// ─── SECTION PAGES ─────────────────────────────────────────────────────────────
function renderSectionPage(sections) {
  const id = window.location.pathname.split('/').pop().replace('.html', '');
  const current = sections.find(s => s.id === id);
  if (!current) return console.error('Unknown section:', id);

  document.getElementById('section-title').textContent = current.title;
  const container = document.getElementById('checklist-container');
  container.innerHTML = ''; // Clear "Loading..."

  // Render checklist items
  let responses = safeParseJSON(`responses_${current.id}`, []);
  if (responses.length !== current.items.length) {
    responses = current.items.map(() => false);
  }
  current.items.forEach((item, idx) => {
    const div = document.createElement('div');
    div.className = 'check-item';
    const cb = document.createElement('input');
    cb.type    = 'checkbox';
    cb.checked = responses[idx];
    cb.addEventListener('change', () => {
      responses[idx] = cb.checked;
      localStorage.setItem(`responses_${current.id}`, JSON.stringify(responses));
    });
    const lbl = document.createElement('label');
    lbl.textContent = item;
    div.append(cb, ' ', lbl);
    container.append(div);
  });

  // Add "Mark as Completed" checkbox
  const completeDiv = document.createElement('div');
  completeDiv.style.marginTop = '1em';
  const completeLabel = document.createElement('label');
  completeLabel.innerHTML = `<input type="checkbox" id="section-completed"> Mark this section as completed`;
  completeDiv.appendChild(completeLabel);
  container.appendChild(completeDiv);

  // Save Progress button
  const saveBtn = document.createElement('button');
  saveBtn.textContent = 'Save Progress';
  saveBtn.style.marginLeft = '1em';
  completeDiv.appendChild(saveBtn);

  saveBtn.addEventListener('click', function() {
    // Save checklist state (your existing logic)
    // ...

    // Save completed status
    let sopProgress = safeParseJSON('droneSOPProgress', {});
    sopProgress.progress = sopProgress.progress || {};
    sopProgress.progress[current.id] = sopProgress.progress[current.id] || { data: {} };
    sopProgress.progress[current.id].status = document.getElementById('section-completed').checked ? 'completed' : 'in-progress';
    localStorage.setItem('droneSOPProgress', JSON.stringify(sopProgress));
    alert('Progress saved!');
  });

  // Use droneSOPProgress for navigation
  const sopProgress = safeParseJSON('droneSOPProgress', {});
  const selected = sopProgress.selectedSOPs || [];
  const idx = selected.indexOf(current.id);

  // Create navigation buttons
  const navDiv = document.createElement('div');
  navDiv.style.marginTop = '2em';

  // Prev button
  const prevBtn = document.createElement('button');
  prevBtn.textContent = idx > 0 ? '< Previous' : '< Back to Index';
  prevBtn.onclick = () => {
    if (idx > 0) {
      window.location.href = `../sections/${selected[idx-1]}.html`;
    } else {
      window.location.href = '../index.html';
    }
  };
  navDiv.appendChild(prevBtn);

  // Next or Flight Log button
  const nextBtn = document.createElement('button');
  nextBtn.style.marginLeft = '1em';
  if (idx < selected.length - 1) {
    nextBtn.textContent = 'Next >';
    nextBtn.onclick = () => {
      window.location.href = `../sections/${selected[idx+1]}.html`;
    };
  } else {
    nextBtn.textContent = 'Flight Log';
    nextBtn.onclick = () => {
      window.location.href = '../flight-log.html';
    };
  }
  navDiv.appendChild(nextBtn);

  container.appendChild(navDiv);
}

// ─── SUMMARY PAGE ──────────────────────────────────────────────────────────────
function renderSummary(sections) {
  const container = document.getElementById('summary-container');
  if (!container) return;

  const flightLog = safeParseJSON('flightLog', {});
  const wrapper   = document.createElement('div');
  wrapper.className = 'flight-log-wrapper';
  wrapper.innerHTML = `
    <h2>Flight Log Information</h2>
    <table class="flight-log-table">
      <thead>
        <tr>
          <th>Date</th>
          <th>Pilot(s) / Observer(s)</th>
          <th>Start Time</th>
          <th>End Time</th>
          <th>Location</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>${flightLog.date || '—'}</td>
          <td>${flightLog.pilot || '—'} / ${flightLog.observers || '—'}</td>
          <td>${flightLog.start || '—'}</td>
          <td>${flightLog.end || '—'}</td>
          <td>${flightLog.location || '—'}</td>
        </tr>
      </tbody>
    </table>
  `;
  container.append(wrapper);

  const weather = safeParseJSON('dwCheckLatest', null);
  const weatherComplete = localStorage.getItem('dwCheckCompleted') === 'true';
  const weatherCompleteAt = localStorage.getItem('dwCheckCompletedAt');
  const weatherDiv = document.createElement('div');
  weatherDiv.className = 'section-block';

  if (weather && weather.timestamp) {
    const nearest = Array.isArray(weather.nearestStations)
      ? weather.nearestStations.map(s => `${s.icaoId} (${Number(s.distanceKm || 0).toFixed(1)} km)`).join(', ')
      : '';
    const when = new Date(weather.timestamp).toLocaleString();
    const completedText = weatherComplete
      ? `Yes (${weatherCompleteAt ? new Date(weatherCompleteAt).toLocaleString() : 'time unavailable'})`
      : 'No';

    weatherDiv.innerHTML = `
      <h2>Weather Sanity Check</h2>
      <ul>
        <li>Checked At: ${when}</li>
        <li>Completed: ${completedText}</li>
        <li>ICAO: ${weather.icao || '—'}</li>
        <li>Risk: ${weather.riskLabel || '—'} (score ${weather.riskScore ?? '—'})</li>
        <li>Kp: ${weather.kpIndex ?? '—'} (${weather.kpCondition || 'Unavailable'})</li>
        <li>Wind/Gust: ${weather.windKt ?? '—'} / ${weather.gustKt ?? '—'} kt</li>
        <li>Visibility/Ceiling: ${weather.visibilitySm ?? '—'} SM / ${weather.ceilingFt ?? '—'} ft</li>
        <li>Nearest Stations: ${nearest || '—'}</li>
      </ul>
    `;
  } else {
    weatherDiv.innerHTML = `
      <h2>Weather Sanity Check</h2>
      <p><em>No weather check artifact saved for this session.</em></p>
    `;
  }

  container.append(weatherDiv);

  // Prefer the current key; keep legacy fallback for older saved sessions.
  const sopProgress = safeParseJSON('droneSOPProgress', {});
  const selected = sopProgress.selectedSOPs || safeParseJSON('selectedSections', []);
  selected.forEach(secId => {
    const section   = sections.find(s => s.id === secId);
    const responses = safeParseJSON(`responses_${secId}`, []);
    const block     = document.createElement('div');
    block.className = 'section-block';
    block.innerHTML = `<h2>${section.title}</h2>` +
      `<ul>${section.items.map((item,i) =>
        `<li>${responses[i] ? '✔' : '◻'} ${item}</li>`
      ).join('')}</ul>`;
    container.append(block);
  });

  // Filename utilities...
  function getDateStr() {
    const d = new Date(), p = n => String(n).padStart(2,'0');
    return `${p(d.getDate())}-${p(d.getMonth()+1)}-${String(d.getFullYear()).slice(-2)}`;
  }
  function bumpCount(key) {
    const today = getDateStr(), sk = `${key}_${today}`;
    const prev  = parseInt(localStorage.getItem(sk) || '0', 10);
    const next  = prev + 1;
    localStorage.setItem(sk, String(next));
  }

  function getIsoDateStr() {
    return new Date().toISOString().slice(0, 10);
  }

  function getNextLogExportMeta(ext = 'csv') {
    const date = getIsoDateStr();
    const key = `logExportIteration_${date}`;
    const prev = parseInt(localStorage.getItem(key) || '0', 10);
    const next = prev + 1;
    return {
      key,
      next,
      filename: `LOG_${date}_${next}.${ext}`
    };
  }

  function commitLogExportIteration(meta) {
    if (!meta || !meta.key || !Number.isFinite(meta.next)) return;
    const prev = parseInt(localStorage.getItem(meta.key) || '0', 10);
    if (meta.next > prev) localStorage.setItem(meta.key, String(meta.next));
  }

  function sanitizeFilenameBase(input) {
    return String(input || '')
      .replace(/[<>:"/\\|?*\x00-\x1F]/g, '_')
      .replace(/\s+/g, '_')
      .replace(/_+/g, '_')
      .replace(/^_+|_+$/g, '');
  }

  function promptForFilename(defaultFilename, ext) {
    const expectedExt = `.${ext}`;
    const defaultBase = defaultFilename.toLowerCase().endsWith(expectedExt)
      ? defaultFilename.slice(0, -expectedExt.length)
      : defaultFilename;

    const userInput = prompt(`Enter ${ext.toUpperCase()} file name:`, defaultBase);
    if (userInput === null) return null;

    const cleanBase = sanitizeFilenameBase(userInput);
    if (!cleanBase) {
      alert('Invalid file name. Export cancelled.');
      return null;
    }

    return `${cleanBase}${expectedExt}`;
  }

  function getExportStatusElement() {
    let el = document.getElementById('export-status');
    if (el) return el;

    el = document.createElement('p');
    el.id = 'export-status';
    el.style.marginTop = '10px';
    el.style.fontSize = '0.95em';
    el.style.color = '#2f3b52';

    const pdfBtn = document.getElementById('export-pdf');
    if (pdfBtn && pdfBtn.parentNode) {
      pdfBtn.parentNode.insertBefore(el, pdfBtn.nextSibling);
    } else {
      container.appendChild(el);
    }

    return el;
  }

  function setExportStatus(message, isError = false) {
    const el = getExportStatusElement();
    el.textContent = message;
    el.style.color = isError ? '#8a1f1f' : '#2f3b52';
  }

  async function saveTextFileWithPicker(content, filename, mimeType) {
    if (!window.showSaveFilePicker) return false;

    const ext = filename.split('.').pop() || 'txt';
    const handle = await window.showSaveFilePicker({
      suggestedName: filename,
      types: [{
        description: `${ext.toUpperCase()} file`,
        accept: { [mimeType]: [`.${ext}`] }
      }]
    });

    const writable = await handle.createWritable();
    await writable.write(content);
    await writable.close();
    return true;
  }

  document.getElementById('export-csv').addEventListener('click', async () => {
    let csv = 'Field,Value\n'
      + `Date,${flightLog.date||''}\n`
      + `Pilot(s),${flightLog.pilot||''}\n`
      + `Observer(s),${flightLog.observers||''}\n`
      + `Start,${flightLog.start||''}\n`
      + `End,${flightLog.end||''}\n`
      + `Location,${flightLog.location||''}\n\n`
      + 'Section,Item,Checked\n';
    selected.forEach(secId => {
      const section   = sections.find(s => s.id === secId);
      const responses = safeParseJSON(`responses_${secId}`, []);
      section.items.forEach((item, idx) => {
        csv += `"${section.title}","${item.replace(/"/g,'""')}","${responses[idx] ? 'Yes' : 'No'}"\n`;
      });
    });
    const exportMeta = getNextLogExportMeta('csv');
    const filename = promptForFilename(exportMeta.filename, 'csv');
    if (!filename) {
      setExportStatus('CSV export cancelled.');
      return;
    }

    try {
      const usedPicker = await saveTextFileWithPicker(csv, filename, 'text/csv');
      if (usedPicker) {
        commitLogExportIteration(exportMeta);
        bumpCount('csvExport');
        setExportStatus(`CSV saved: ${filename}`);
        return;
      }
    } catch (err) {
      if (err && err.name === 'AbortError') {
        setExportStatus('CSV export cancelled.');
        return;
      }
      console.warn('Save file picker unavailable or cancelled, falling back to browser download.', err);
    }

    const blob = new Blob([csv], { type: 'text/csv' });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    a.href     = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
    commitLogExportIteration(exportMeta);
    bumpCount('csvExport');
    setExportStatus(`CSV download started: ${filename}`);
  });

  document.getElementById('export-pdf').addEventListener('click', () => {
    const exportMeta = getNextLogExportMeta('pdf');
    const chosen = promptForFilename(exportMeta.filename, 'pdf');
    if (!chosen) {
      setExportStatus('PDF export cancelled.');
      return;
    }
    const filename = chosen.replace('.pdf',''); // window.print() uses document.title
    const origTitle = document.title;
    document.title  = filename;
    alert('Use the print dialog to choose Save as PDF and select the destination folder.');
    window.print();
    document.title  = origTitle;
    commitLogExportIteration(exportMeta);
    bumpCount('pdfExport');
    setExportStatus(`PDF print/save dialog opened for: ${chosen}`);
  });

  document.getElementById('return-home').addEventListener('click', () =>
    window.location.href = 'index.html'
  );

  // Pilot Location (DD/DMS)
  const dd = localStorage.getItem('pilotLocationDD');
  const dms = localStorage.getItem('pilotLocationDMS');
  const pilotLocDiv = document.getElementById('pilot-location-summary');
  if (pilotLocDiv) {
    if (dd && dms) {
      pilotLocDiv.innerHTML =
        `<strong>Pilot Location:</strong><br>DD: ${dd}<br>DMS: ${dms}`;
    } else {
      pilotLocDiv.innerHTML = "<em>Pilot location not recorded in this session.</em>";
    }
  }
}

// Collapsible cards for emergencies.html
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.card h2').forEach(header => {
    header.addEventListener('click', () => {
      header.parentElement.classList.toggle('collapsed');
    });
  });
});
