// assets/js/app.js
// RLT May 2025 – Final step always goes to Flight Log

const FLIGHT_RUN_STORAGE_KEYS = [
  'flightLog',
  'flightDate',
  'flightPilot',
  'flightObservers',
  'flightStart',
  'flightEnd',
  'flightLocation',
  'pilotLocationDD',
  'pilotLocationDMS'
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

  const toDMS = (deg, isLat) => {
    const abs = Math.abs(deg);
    const d = Math.floor(abs);
    const mFloat = (abs - d) * 60;
    const m = Math.floor(mFloat);
    const s = ((mFloat - m) * 60).toFixed(1);
    const dir = isLat
      ? (deg >= 0 ? 'N' : 'S')
      : (deg >= 0 ? 'E' : 'W');
    return `${d}\u00B0${m}'${s}"${dir}`;
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
  if (dd && dms) {
    if (output) {
      output.innerHTML =
        `DD: ${dd}<br>` +
        `DMS: ${dms}<br>` +
        `<a href="https://maps.google.com/?q=${dd.replace(/ /g, '')}" target="_blank" rel="noopener">View on Google Maps</a>`;
    }
    loc.value = dd;
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
          const latDMS = toDMS(latitude, true);
          const lonDMS = toDMS(longitude, false);

          if (output) {
            output.innerHTML =
              `DD: ${latShort}, ${lonShort}<br>` +
              `DMS: ${latDMS}, ${lonDMS}<br>` +
              `<a href="https://maps.google.com/?q=${latShort},${lonShort}" target="_blank" rel="noopener">View on Google Maps</a>`;
          }

          loc.value = `${latShort}, ${lonShort}`;
          localStorage.setItem('pilotLocationDD', `${latShort}, ${lonShort}`);
          localStorage.setItem('pilotLocationDMS', `${latDMS}, ${lonDMS}`);
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
    if (flightLog.location) {
      localStorage.setItem('pilotLocationDD', flightLog.location);
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

  // Utility: get export filename (CSV or PDF)
  function getExportFilename(ext = 'csv') {
    const currentFlightLog = safeParseJSON('flightLog', {});
    // Use flight date and pilot name if available, else fallback to today
    const date = currentFlightLog.date || new Date().toISOString().slice(0, 10);
    const pilot = currentFlightLog.pilot ? currentFlightLog.pilot.replace(/[^a-z0-9]/gi, '_') : 'UnknownPilot';
    return `FlightLog_${date}_${pilot}.${ext}`;
  }

  document.getElementById('export-csv').addEventListener('click', () => {
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
    bumpCount('csvExport');
    const filename = getExportFilename('csv');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    a.href     = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  });

  document.getElementById('export-pdf').addEventListener('click', () => {
    bumpCount('pdfExport');
    const filename = getExportFilename('pdf').replace('.pdf',''); // window.print() uses document.title
    const origTitle = document.title;
    document.title  = filename;
    window.print();
    document.title  = origTitle;
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
