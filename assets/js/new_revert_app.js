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
    localStorage.removeItem('selectedSections');
    sections.forEach(s => localStorage.removeItem(`responses_${s.id}`));
    localStorage.removeItem('flightLog');
    localStorage.setItem('selectedSections', JSON.stringify(list));
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
  // Get the current section ID from the filename
  const pathParts = window.location.pathname.split('/');
  const filename = pathParts[pathParts.length - 1];
  const sopId = filename.replace('.html', '');

  const section = sections.find(s => s.id === sopId);
  if (!section) {
    document.getElementById('checklist-container').innerHTML = '<em>Section not found.</em>';
    return;
  }

  const container = document.getElementById('checklist-container');
  container.innerHTML = '';

  // Load progress
  const sopProgress = JSON.parse(localStorage.getItem('droneSOPProgress') || '{}');
  const sectionProgress = sopProgress.progress && sopProgress.progress[sopId] ? sopProgress.progress[sopId] : { data: {}, status: "not-started" };

  // Render the first item as a "Mark as Completed" checkbox
  const completedDiv = document.createElement('div');
  completedDiv.className = 'completed-checkbox';
  const completedLabel = document.createElement('label');
  completedLabel.innerHTML = `<input type="checkbox" id="section-completed"> ${section.items[0]}`;
  completedDiv.appendChild(completedLabel);
  container.appendChild(completedDiv);

  // Set checkbox state from progress
  document.getElementById('section-completed').checked = sectionProgress.status === "completed";

  // Render the rest of the checklist items as normal checkboxes
  section.items.slice(1).forEach((item, idx) => {
    const itemDiv = document.createElement('div');
    itemDiv.className = 'checklist-item';
    const itemLabel = document.createElement('label');
    const itemId = `item-${idx + 1}`;
    itemLabel.innerHTML = `<input type="checkbox" id="${itemId}"> ${item}`;
    itemDiv.appendChild(itemLabel);
    container.appendChild(itemDiv);

    // Restore checked state if previously saved
    if (sectionProgress.data && sectionProgress.data[itemId]) {
      document.getElementById(itemId).checked = true;
    }
  });

  // Save button
  const saveBtn = document.createElement('button');
  saveBtn.textContent = 'Save Progress';
  saveBtn.style.marginTop = '1em';
  container.appendChild(saveBtn);

  saveBtn.addEventListener('click', function() {
    // Save checklist state
    const newProgress = { data: {}, status: "in-progress" };
    // Save each item state
    section.items.slice(1).forEach((item, idx) => {
      const itemId = `item-${idx + 1}`;
      newProgress.data[itemId] = document.getElementById(itemId).checked;
    });
    // Save completed status
    if (document.getElementById('section-completed').checked) {
      newProgress.status = "completed";
    }
    // Update localStorage
    sopProgress.progress = sopProgress.progress || {};
    sopProgress.progress[sopId] = newProgress;
    localStorage.setItem('droneSOPProgress', JSON.stringify(sopProgress));
    alert('Progress saved!');
  });

  // Find the list of selected SOPs from progress
  const selected = sopProgress.selectedSOPs || [];
  const currentIdx = selected.indexOf(sopId);

  const navDiv = document.createElement('div');
  navDiv.style.marginTop = '2em';

  // Prev button
  if (currentIdx > 0) {
    const prevBtn = document.createElement('button');
    prevBtn.textContent = 'Prev';
    prevBtn.onclick = () => {
      window.location.href = `./${selected[currentIdx - 1]}.html`;
    };
    navDiv.appendChild(prevBtn);
  }

  // Next button or Flight Log/Summary
  if (currentIdx < selected.length - 1) {
    const nextBtn = document.createElement('button');
    nextBtn.textContent = 'Next';
    nextBtn.style.marginLeft = '1em';
    nextBtn.onclick = () => {
      window.location.href = `./${selected[currentIdx + 1]}.html`;
    };
    navDiv.appendChild(nextBtn);
  } else {
    // Last SOP: show button to go to Flight Log or Summary
    const logBtn = document.createElement('button');
    logBtn.textContent = 'Flight Log';
    logBtn.style.marginLeft = '1em';
    logBtn.onclick = () => {
      window.location.href = '../flight-log.html';
    };
    navDiv.appendChild(logBtn);
  }

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

// // Load SOP sections from sections.json and initialize UI
// fetch('data/sections.json')
//   .then(res => res.json())
//   .then(sections => {
//     let sopProgress = loadSOPProgress();
//     if (!sopProgress) {
//       // First visit: let user select SOPs
//       renderSOPSelector(sections);
//     } else {
//       // Already started: render progress dashboard
//       renderSections(sections, sopProgress);
//     }
//   });

function renderSOPSelector(sections) {
  const sectionSelector = document.getElementById('section-selector');
  sectionSelector.innerHTML = '';
  sections.forEach(sec => {
    const label = document.createElement('label');
    label.innerHTML = `<input type="checkbox" value="${sec.id}"> ${sec.title}`;
    sectionSelector.appendChild(label);
    sectionSelector.appendChild(document.createElement('br'));
  });
  const beginBtn = document.getElementById('begin-btn');
  beginBtn.disabled = false;
  beginBtn.onclick = function() {
    const selected = Array.from(sectionSelector.querySelectorAll('input[type=checkbox]:checked')).map(cb => cb.value);
    const progress = {};
    selected.forEach(id => {
      progress[id] = { status: "not-started", data: {} };
    });
    saveSOPProgress({ selectedSOPs: selected, progress });
    renderSections(sections, { selectedSOPs: selected, progress });
  };
}

function renderSections(sections, sopData) {
  const sectionSelector = document.getElementById('section-selector');
  sectionSelector.innerHTML = '';
  sopData.selectedSOPs.forEach(sopId => {
    const sec = sections.find(s => s.id === sopId);
    const sop = sopData.progress[sopId];
    const div = document.createElement('div');
    div.className = 'sop-section';

    const title = document.createElement('h2');
    title.textContent = sec ? sec.title : sopId;
    div.appendChild(title);

    const status = document.createElement('p');
    status.textContent = `Status: ${sop.status.replace('-', ' ')}`;
    div.appendChild(status);

    const openBtn = document.createElement('button');
    openBtn.textContent = sop.status === "completed" ? "Review/Edit" : "Continue";
    openBtn.onclick = function() {
      openSOP(sopId);
    };
    div.appendChild(openBtn);

    if (sop.status !== "completed") {
      const completeBtn = document.createElement('button');
      completeBtn.textContent = "Mark as Completed";
      completeBtn.onclick = function() {
        completeSOP(sopId, sop.data);
        renderSections(sections, loadSOPProgress());
      };
      div.appendChild(completeBtn);
    }

    sectionSelector.appendChild(div);
  });
}

function saveSOPProgress(progressObj) {
  localStorage.setItem('droneSOPProgress', JSON.stringify(progressObj));
}

function loadSOPProgress() {
  const data = localStorage.getItem('droneSOPProgress');
  return data ? JSON.parse(data) : null;
}

function clearSOPProgress() {
  localStorage.removeItem('droneSOPProgress');
}

function openSOP(sopId) {
  let sopProgress = loadSOPProgress();
  if (sopProgress.progress[sopId].status === "not-started") {
    sopProgress.progress[sopId].status = "in-progress";
    saveSOPProgress(sopProgress);
  }
  // Redirect or load the SOP form here, e.g.:
  // window.location.href = `sop.html?id=${encodeURIComponent(sopId)}`;
}

function completeSOP(sopId, formData) {
  let sopProgress = loadSOPProgress();
  sopProgress.progress[sopId].status = "completed";
  sopProgress.progress[sopId].data = formData;
  saveSOPProgress(sopProgress);
}
