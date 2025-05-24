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
  const id      = window.location.pathname
                    .split('/')
                    .pop()
                    .replace('.html','');
  const current = sections.find(s => s.id === id);
  if (!current) return console.error('Unknown section:', id);

  document.getElementById('section-title').textContent = current.title;
  const key     = `responses_${current.id}`;
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

  // Prev button
  if (idx > 0) {
    prevBtn.disabled = false;
    prevBtn.addEventListener('click', () =>
      window.location.href = `../sections/${selected[idx-1]}.html`
    );
  } else {
    prevBtn.disabled = true;
  }

  // Next or Flight Log
  if (idx < selected.length - 1) {
    nextBtn.textContent = 'Next ›';
    nextBtn.disabled   = false;
    nextBtn.addEventListener('click', () =>
      window.location.href = `../sections/${selected[idx+1]}.html`
    );
  } else {
    // Last section: always enabled and goes to flight-log.html
    nextBtn.textContent = 'Flight Log';
    nextBtn.disabled   = false;
    nextBtn.addEventListener('click', () =>
      window.location.href = '../flight-log.html'
    );
  }
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
}
