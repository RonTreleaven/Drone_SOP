// assets/js/app.js
// RLT May 2025 – Final step always goes to Flight Log

document.addEventListener('DOMContentLoaded', () => {
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
  } else if (document.getElementById('flight-log-form')) {
    renderFlightLog();
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
    // Clear old progress
    localStorage.removeItem('droneSOPProgress');
    localStorage.removeItem('flightLog');
    // Initialize new progress structure
    const progress = {};
    list.forEach(id => {
      progress[id] = { status: "not-started", data: {} };
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

  const saved = JSON.parse(localStorage.getItem('flightLog') || '{}');
  dateIn.value = saved.date      || new Date().toISOString().split('T')[0];
  pilot.value  = saved.pilot     || '';
  obs.value    = saved.observers || '';
  start.value  = saved.start     || '';
  end.value    = saved.end       || '';
  loc.value    = saved.location  || '';

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
    alert('✅ Flight log saved.');
  });
}

// ─── SECTION PAGES ─────────────────────────────────────────────────────────────
function renderSectionPage(sections) {
    const id = window.location.pathname.split('/').pop().replace('.html','');
  const current = sections.find(s => s.id === id);
  if (!current) return console.error('Unknown section:', id);

  document.getElementById('section-title').textContent = current.title;
  const container = document.getElementById('checklist-container');
  container.innerHTML = ''; // Clear "Loading..."

  // Render checklist items
  let responses = JSON.parse(localStorage.getItem(`responses_${current.id}`) || '[]');
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

  // // Restore checkbox state if previously completed *** crashed the loading of the Section.json
  
  // const sopProgress = JSON.parse(localStorage.getItem('droneSOPProgress') || '{}');
  // if (sopProgress.progress && sopProgress.progress[current.id]) {
  //   document.getElementById('section-completed').checked = sopProgress.progress[current.id].status === "completed";
  // }

  // Save Progress button
  const saveBtn = document.createElement('button');
  saveBtn.textContent = 'Save Progress';
  saveBtn.style.marginLeft = '1em';
  completeDiv.appendChild(saveBtn);

  saveBtn.addEventListener('click', function() {
    // Save checklist state (your existing logic)
    // ...

    // Save completed status
    let sopProgress = JSON.parse(localStorage.getItem('droneSOPProgress') || '{}');
    sopProgress.progress = sopProgress.progress || {};
    sopProgress.progress[current.id] = sopProgress.progress[current.id] || { data: {} };
    sopProgress.progress[current.id].status = document.getElementById('section-completed').checked ? "completed" : "in-progress";
    localStorage.setItem('droneSOPProgress', JSON.stringify(sopProgress));
    alert('Progress saved!');
  });

  // Use droneSOPProgress for navigation
  const sopProgress = JSON.parse(localStorage.getItem('droneSOPProgress') || '{}');
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

  const flightLog = JSON.parse(localStorage.getItem('flightLog') || '{}');
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

  const selected = JSON.parse(localStorage.getItem('selectedSections') || '[]');
  selected.forEach(secId => {
    const section   = sections.find(s => s.id === secId);
    const responses = JSON.parse(localStorage.getItem(`responses_${secId}`) || '[]');
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
    return { today, count: next };
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
      const responses = JSON.parse(localStorage.getItem(`responses_${secId}`) || '[]');
      section.items.forEach((item, idx) => {
        csv += `"${section.title}","${item.replace(/"/g,'""')}","${responses[idx] ? 'Yes' : 'No'}"\n`;
      });
    });
    const { today, count } = bumpCount('csvExport');
    const suffix = count > 1 ? ` (${count})` : '';
    const filename = `Flight Summary ${today}${suffix}.csv`;
    const blob = new Blob([csv], { type: 'text/csv' });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    a.href     = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  });

  document.getElementById('export-pdf').addEventListener('click', () => {
    const { today, count } = bumpCount('pdfExport');
    const suffix = count > 1 ? ` (${count})` : '';
    const filename = `Flight Summary ${today}${suffix}`;
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

// ─── COLLAPSIBLE CARDS FOR emerge3.html ───────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.card h2').forEach(header => {
    header.addEventListener('click', () => {
      header.parentElement.classList.toggle('collapsed');
    });
  });
});

document.addEventListener('DOMContentLoaded', function() {
  const btn = document.getElementById('getLocation');
  const output = document.getElementById('output');
  const locInput = document.getElementById('flight-location');

  // Restore from localStorage if available
  const dd = localStorage.getItem('pilotLocationDD');
  const dms = localStorage.getItem('pilotLocationDMS');
  if (dd && dms) {
    if (output) {
      output.innerHTML =
        `DD: ${dd}<br>` +
        `DMS: ${dms}<br>` +
        `<a href="https://maps.google.com/?q=${dd.replace(/ /g, '')}" target="_blank" rel="noopener">View on Google Maps</a>`;
    }
    if (locInput) {
      locInput.value = dd;
    }
  }

  if (!btn) return;
  btn.addEventListener('click', () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const latitude = position.coords.latitude;
          const longitude = position.coords.longitude;
          // Round to 6 decimal places
          const latShort = latitude.toFixed(6);
          const lonShort = longitude.toFixed(6);
          // Convert to DMS
          const latDMS = toDMS(latitude, true);
          const lonDMS = toDMS(longitude, false);
          output.innerHTML =
            `DD: ${latShort}, ${lonShort}<br>` +
            `DMS: ${latDMS}, ${lonDMS}<br>` +
            `<a href="https://maps.google.com/?q=${latShort},${lonShort}" target="_blank" rel="noopener">View on Google Maps</a>`;
          // Autofill the Pilot Location field
          if (locInput) {
            locInput.value = `${latShort}, ${lonShort}`;
          }
          // Store in localStorage
          localStorage.setItem('pilotLocationDD', `${latShort}, ${lonShort}`);
          localStorage.setItem('pilotLocationDMS', `${latDMS}, ${lonDMS}`);
        },
        (error) => {
          switch (error.code) {
            case error.PERMISSION_DENIED:
              output.textContent = "User denied the request for Geolocation.";
              break;
            case error.POSITION_UNAVAILABLE:
              output.textContent = "Location information is unavailable.";
              break;
            case error.TIMEOUT:
              output.textContent = "The request to get user location timed out.";
              break;
            default:
              output.textContent = "An unknown error occurred.";
              break;
          }
        }
      );
    } else {
      output.textContent = "Geolocation is not supported by this browser.";
    }
  });
});
