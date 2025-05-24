// assets/js/app.js
// RLT May 22, 2025
// assets/js/app.js
// RLT May 21, 2025

document.addEventListener('DOMContentLoaded', () => {
  // Only pages under /sections/ need ../data/, everything else uses ./data/
  const jsonPath = window.location.pathname.includes('/sections/')
    ? '../data/sections.json'
    : './data/sections.json';

  console.log('⏳ Fetching sections.json from:', jsonPath);
  fetch(jsonPath)
    .then(res => {
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return res.json();
    })
    .then(sections => initApp(sections))
    .catch(err => {
      console.error('❌ Could not load sections.json', err);
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
      cb.checked ? chosen.add(cb.value) : chosen.delete(cb.value);
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

  const saved = JSON.parse(localStorage.getItem('flightLog') || '{}');
  dateIn.value = saved.date      || new Date().toISOString().split('T')[0];
  pilot.value  = saved.pilot     || '';
  obs.value    = saved.observers || '';
  start.value  = saved.start     || '';
  end.value    = saved.end       || '';

  form.addEventListener('submit', e => {
    e.preventDefault();
    const flightLog = {
      date:      dateIn.value,
      pilot:     pilot.value.trim(),
      observers: obs.value.trim(),
      start:     start.value,
      end:       end.value
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
  const key = `responses_${current.id}`;
  let responses = JSON.parse(localStorage.getItem(key) || '[]');
  if (responses.length !== current.items.length) {
    responses = current.items.map(() => false);
  }

  const container = document.getElementById('checklist-container');
  current.items.forEach((item, idx) => {
    const div = document.createElement('div');
    div.className = 'check-item';
    const cb = document.createElement('input');
    cb.type    = 'checkbox';
    cb.checked = responses[idx];
    cb.addEventListener('change', () => {
      responses[idx] = cb.checked;
      localStorage.setItem(key, JSON.stringify(responses));
    });
    const lbl = document.createElement('label');
    lbl.textContent = item;
    div.append(cb, ' ', lbl);
    container.append(div);
  });

  const selected = JSON.parse(localStorage.getItem('selectedSections') || '[]');
  const idx      = selected.indexOf(current.id);
  const prevBtn  = document.getElementById('prev-btn');
  const nextBtn  = document.getElementById('next-btn');

  if (idx > 0) {
    prevBtn.addEventListener('click', () =>
      window.location.href = `../sections/${selected[idx-1]}.html`
    );
  } else prevBtn.disabled = true;

  if (idx < selected.length - 1) {
    nextBtn.textContent = 'Next ›';
    nextBtn.addEventListener('click', () =>
      window.location.href = `../sections/${selected[idx+1]}.html`
    );
  } else {
    nextBtn.textContent = 'Summary';
    nextBtn.addEventListener('click', () =>
      window.location.href = `../summary.html`
    );
  }
}

// ─── SUMMARY PAGE ──────────────────────────────────────────────────────────────
function renderSummary(sections) {
  const container = document.getElementById('summary-container');
  if (!container) return;

  // Flight Log block
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
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>${flightLog.date || '—'}</td>
          <td>${flightLog.pilot || '—'} / ${flightLog.observers || '—'}</td>
          <td>${flightLog.start || '—'}</td>
          <td>${flightLog.end || '—'}</td>
        </tr>
      </tbody>
    </table>
  `;
  container.append(wrapper);

  // Checklist sections
  const selected = JSON.parse(localStorage.getItem('selectedSections') || '[]');
  selected.forEach(secId => {
    const section   = sections.find(s => s.id === secId);
    const responses = JSON.parse(localStorage.getItem(`responses_${secId}`) || '[]');

    const sectionBlock = document.createElement('div');
    sectionBlock.className = 'section-block';

    const h2 = document.createElement('h2');
    h2.textContent = section.title;
    sectionBlock.append(h2);

    const ul = document.createElement('ul');
    section.items.forEach((item, idx) => {
      const li = document.createElement('li');
      li.textContent = `${responses[idx] ? '✔' : '◻'} ${item}`;
      ul.append(li);
    });
    sectionBlock.append(ul);

    container.append(sectionBlock);
  });

  // Button wiring
  document.getElementById('export-csv').addEventListener('click', () => {
    let csv = 'Section,Item,Checked\n';
    selected.forEach(secId => {
      const section   = sections.find(s => s.id === secId);
      const responses = JSON.parse(localStorage.getItem(`responses_${secId}`) || '[]');
      section.items.forEach((item, idx) => {
        csv += `"${section.title}","${item.replace(/"/g,'""')}","${responses[idx] ? 'Yes' : 'No'}"\n`;
      });
    });
    const blob = new Blob([csv], { type: 'text/csv' });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    a.href     = url;
    a.download = 'Flight_Summary.csv';
    a.click();
    URL.revokeObjectURL(url);
  });

  document.getElementById('export-pdf').addEventListener('click', () => {
    window.print();
  });

  document.getElementById('return-home').addEventListener('click', () => {
    window.location.href = 'index.html';
  });
}
