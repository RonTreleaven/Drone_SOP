// assets/js/app.js
// RLT May 2025 – Final step always goes to Flight Log

const FLIGHT_RUN_STORAGE_KEYS = [
  'flightLog',
  'flightLogLatest',
  'flightDate',
  'flightPilot',
  'flightObservers',
  'flightStart',
  'flightEnd',
  'flightLocation'
];

const WEATHER_CHECK_STORAGE_KEYS = [
  'dwCheckLatest',
  'dwCheckDraft',
  'dwCheckDraftPending',
  'dwCheckCompleted',
  'dwCheckCompletedAt'
];

const SESSION_PROGRESS_KEYS = [
  'droneSOPProgress',
  'selectedSections'
];

const PILOT_LOCATION_KEYS = [
  'pilotLocationDD',
  'pilotLocationDMS',
  'pilotLatitude',
  'pilotLongitude',
  'pilotLocationSource'
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

function clearWeatherCheckData() {
  WEATHER_CHECK_STORAGE_KEYS.forEach(key => localStorage.removeItem(key));
}

function clearSessionProgressData() {
  SESSION_PROGRESS_KEYS.forEach(key => localStorage.removeItem(key));
  Object.keys(localStorage).forEach(key => {
    if (key.startsWith('responses_')) localStorage.removeItem(key);
  });
}

function clearPilotLocationData() {
  PILOT_LOCATION_KEYS.forEach(key => localStorage.removeItem(key));
}

function clearSessionStateAfterSummarySave() {
  clearFlightRunData();
  clearWeatherCheckData();
  clearSessionProgressData();
  clearPilotLocationData();
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

function isPilotLocationUndefined(lat, lon) {
  return Math.abs(Number(lat)) < 0.000001 && Math.abs(Number(lon)) < 0.000001;
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

function normalizePilotLocationState() {
  const dd = parseLatLonText(localStorage.getItem('pilotLocationDD') || '');
  const lat = Number(localStorage.getItem('pilotLatitude'));
  const lon = Number(localStorage.getItem('pilotLongitude'));
  const fromLatLon = Number.isFinite(lat) && Number.isFinite(lon)
    ? { lat, lon }
    : null;
  const best = dd || fromLatLon;

  if (best) {
    savePilotLocation(best.lat, best.lon, localStorage.getItem('pilotLocationSource') || 'normalized');
    return;
  }

  const anyLocationKey = PILOT_LOCATION_KEYS.some(key => !!localStorage.getItem(key));
  if (anyLocationKey) clearPilotLocationData();
}

function parseJSONRaw(raw) {
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

function normalizeWeatherState() {
  const latestRaw = localStorage.getItem('dwCheckLatest');
  const draftRaw = localStorage.getItem('dwCheckDraft');
  const latest = parseJSONRaw(latestRaw);
  const draft = parseJSONRaw(draftRaw);
  const pending = localStorage.getItem('dwCheckDraftPending') === 'true';

  if (latestRaw && !latest) {
    localStorage.removeItem('dwCheckLatest');
    localStorage.removeItem('dwCheckCompleted');
    localStorage.removeItem('dwCheckCompletedAt');
  }

  if (draftRaw && !draft) {
    localStorage.removeItem('dwCheckDraft');
    localStorage.setItem('dwCheckDraftPending', 'false');
  }

  if (latest) {
    const stamp =
      localStorage.getItem('dwCheckCompletedAt') ||
      latest.committedAt ||
      latest.timestamp ||
      '';

    localStorage.setItem('dwCheckCompleted', 'true');
    if (stamp) localStorage.setItem('dwCheckCompletedAt', stamp);

    if (!draft) {
      localStorage.setItem('dwCheckDraftPending', 'false');
    }
  } else {
    localStorage.removeItem('dwCheckCompleted');
    localStorage.removeItem('dwCheckCompletedAt');
    if (!draft && pending) localStorage.setItem('dwCheckDraftPending', 'false');
  }

  if (draft && !pending) {
    localStorage.setItem('dwCheckDraftPending', 'true');
  }
}

function normalizeSessionProgressState() {
  const selected = safeParseJSON('selectedSections', []);
  const sopProgress = safeParseJSON('droneSOPProgress', {});
  const hasSelected = Array.isArray(selected) && selected.length > 0;
  const hasSopSelected = Array.isArray(sopProgress.selectedSOPs) && sopProgress.selectedSOPs.length > 0;
  const hasProgressMap = sopProgress.progress && typeof sopProgress.progress === 'object';

  if (hasSopSelected) {
    localStorage.setItem('selectedSections', JSON.stringify(sopProgress.selectedSOPs));
    return;
  }

  if (hasSelected) {
    const progress = {};
    selected.forEach(id => {
      progress[id] = { status: 'not-started', data: {} };
    });
    localStorage.setItem('droneSOPProgress', JSON.stringify({ selectedSOPs: selected, progress }));
    return;
  }

  if (hasProgressMap) {
    const inferred = Object.keys(sopProgress.progress);
    if (inferred.length) {
      localStorage.setItem('selectedSections', JSON.stringify(inferred));
      localStorage.setItem('droneSOPProgress', JSON.stringify({ selectedSOPs: inferred, progress: sopProgress.progress }));
      return;
    }
  }

  localStorage.removeItem('selectedSections');
}

function validateAndHealSessionState() {
  normalizePilotLocationState();
  normalizeWeatherState();
  normalizeSessionProgressState();
}

function goBackWithFallback(fallbackHref = 'index.html') {
  if (window.history.length > 1) {
    window.history.back();
  } else {
    window.location.href = fallbackHref;
  }
}

function ensureTopNavBackLink() {
  const nav = document.querySelector('.top-nav');
  if (!nav) return;

  const existingBack = Array.from(nav.querySelectorAll('a')).find(a =>
    (a.dataset && a.dataset.backLink === 'true') || /back/i.test((a.textContent || '').trim())
  );
  if (existingBack) return;

  const fallbackHref = window.location.pathname.includes('/sections/')
    ? '../Sections.html'
    : 'index.html';

  const back = document.createElement('a');
  back.href = '#';
  back.className = 'back-link';
  back.dataset.backLink = 'true';
  const icon = document.createElement('span');
  icon.className = 'back-icon';
  icon.setAttribute('aria-hidden', 'true');
  icon.innerHTML = '&#8592;';
  back.appendChild(icon);
  back.appendChild(document.createTextNode('BACK'));
  back.addEventListener('click', event => {
    event.preventDefault();
    goBackWithFallback(fallbackHref);
  });

  const sep = document.createTextNode(' | ');
  nav.insertBefore(sep, nav.firstChild);
  nav.insertBefore(back, sep);
}

function ensureSectionHeaderBranding() {
  if (!window.location.pathname.includes('/sections/')) return;

  const titleEl = document.getElementById('section-title');
  if (!titleEl) return;
  if (titleEl.closest('.site-header')) return;

  const header = document.createElement('header');
  header.className = 'site-header';

  const logo = document.createElement('img');
  logo.src = '../assets/img/logo_25.svg';
  logo.alt = 'Logo';
  logo.className = 'site-logo';

  titleEl.classList.add('page-title');
  titleEl.parentNode.insertBefore(header, titleEl);
  header.appendChild(logo);
  header.appendChild(titleEl);
}

document.addEventListener('DOMContentLoaded', () => {
  // Heal stale or partial localStorage state before rendering any page UI.
  validateAndHealSessionState();
  ensureTopNavBackLink();
  ensureSectionHeaderBranding();

  // Flight Log page does not require sections.json; initialize immediately.
  if (document.getElementById('flight-log-form')) {
    renderFlightLog();
    return;
  }

  const needsSectionsData =
    !!document.getElementById('section-selector') ||
    !!document.getElementById('checklist-container') ||
    !!document.getElementById('summary-container');
  if (!needsSectionsData) return;

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
  const checkboxById = new Map();
  let activePresetIds = null;

  const presets = {
    micro: ['1_0_Micro_Pre-Flight', '2_0_Takeoff_Procedures', '3_0_Landing_Procedures'],
    basic: ['1_1_Basic_Pre-Flight', '2_0_Takeoff_Procedures', '3_0_Landing_Procedures', '5_1_Basic_Rules'],
    advanced: ['1_2_Advanced_Pre-Flight', '2_0_Takeoff_Procedures', '3_0_Landing_Procedures', '5_2_Advanced_Rules']
  };

  const intro = document.createElement('div');
  intro.style.marginBottom = '1rem';
  intro.innerHTML = '<strong>Choose a profile:</strong> Micro, Basic, or Advanced. Then accept defaults or add more sections.';

  const presetWrap = document.createElement('div');
  presetWrap.style.display = 'flex';
  presetWrap.style.gap = '0.5rem';
  presetWrap.style.flexWrap = 'wrap';
  presetWrap.style.marginBottom = '0.8rem';

  const microBtn = document.createElement('button');
  microBtn.type = 'button';
  microBtn.textContent = 'MICRO';

  const basicBtn = document.createElement('button');
  basicBtn.type = 'button';
  basicBtn.textContent = 'BASIC';

  const advBtn = document.createElement('button');
  advBtn.type = 'button';
  advBtn.textContent = 'ADVANCED';

  presetWrap.append(microBtn, basicBtn, advBtn);

  const promptLine = document.createElement('p');
  promptLine.className = 'subtle';
  promptLine.style.margin = '0.4rem 0 0.8rem';
  promptLine.textContent = 'Select a profile to preload default SOP sections.';

  const decisionWrap = document.createElement('div');
  decisionWrap.style.display = 'flex';
  decisionWrap.style.gap = '0.5rem';
  decisionWrap.style.flexWrap = 'wrap';
  decisionWrap.style.marginBottom = '0.9rem';

  const acceptDefaultsBtn = document.createElement('button');
  acceptDefaultsBtn.type = 'button';
  acceptDefaultsBtn.textContent = 'Accept Defaults and Start';
  acceptDefaultsBtn.disabled = true;

  const addMoreBtn = document.createElement('button');
  addMoreBtn.type = 'button';
  addMoreBtn.textContent = 'Add or Remove Sections';
  addMoreBtn.disabled = true;

  decisionWrap.append(acceptDefaultsBtn, addMoreBtn);

  container.before(intro, presetWrap, promptLine, decisionWrap);

  function getPersistedSelection() {
    const progress = safeParseJSON('droneSOPProgress', {});
    if (Array.isArray(progress.selectedSOPs) && progress.selectedSOPs.length) {
      return progress.selectedSOPs;
    }

    const selected = safeParseJSON('selectedSections', []);
    if (Array.isArray(selected) && selected.length) {
      return selected;
    }

    return [];
  }

  function getChosenInSectionOrder() {
    return sections.filter(sec => chosen.has(sec.id)).map(sec => sec.id);
  }

  function updateBeginButtonState() {
    btn.disabled = chosen.size === 0;
    btn.textContent = chosen.size ? 'Start With Selected Sections' : 'Start Review';
    updateStartActionHighlights();
  }

  function toggleActionHighlight(button, isOn) {
    if (!button) return;
    if (isOn) {
      button.style.boxShadow = '0 0 0 3px rgba(47, 158, 68, 0.45)';
      button.style.background = '#2f9e44';
      button.style.color = '#ffffff';
      return;
    }

    button.style.boxShadow = '';
    button.style.background = '';
    button.style.color = '';
  }

  function updateStartActionHighlights() {
    const hasSelection = chosen.size > 0;
    const hasPreset = Array.isArray(activePresetIds) && activePresetIds.length > 0;
    const hasPresetDelta = hasPreset && (
      chosen.size !== activePresetIds.length ||
      activePresetIds.some(id => !chosen.has(id))
    );

    const highlightAcceptDefaults = hasSelection && hasPreset && !hasPresetDelta && !acceptDefaultsBtn.disabled;
    const highlightStartSelected = hasSelection && (!hasPreset || hasPresetDelta) && !btn.disabled;

    toggleActionHighlight(acceptDefaultsBtn, highlightAcceptDefaults);
    toggleActionHighlight(btn, highlightStartSelected);
  }

  function syncCheckboxesFromChosen() {
    checkboxById.forEach((cb, id) => {
      cb.checked = chosen.has(id);
    });
    updateBeginButtonState();
  }

  function applyPreset(profileKey) {
    chosen.clear();
    activePresetIds = (presets[profileKey] || []).filter(id => checkboxById.has(id));
    activePresetIds.forEach(id => {
      if (checkboxById.has(id)) chosen.add(id);
    });

    syncCheckboxesFromChosen();
    acceptDefaultsBtn.disabled = chosen.size === 0;
    addMoreBtn.disabled = chosen.size === 0;
    promptLine.textContent = 'Defaults loaded. Accept defaults to start now, or add/remove sections before starting.';
    updateStartActionHighlights();
  }

  function hydrateSelectionsFromSession() {
    const restored = getPersistedSelection();
    if (!restored.length) return;

    restored.forEach(id => {
      if (checkboxById.has(id)) chosen.add(id);
    });

    syncCheckboxesFromChosen();
    acceptDefaultsBtn.disabled = chosen.size === 0;
    addMoreBtn.disabled = chosen.size === 0;
    if (chosen.size) {
      promptLine.textContent = 'Previous session selections restored. You can start now or modify sections.';
    }

    const selectedList = getChosenInSectionOrder();
    const matchingPreset = Object.values(presets).find(profileIds =>
      profileIds.length === selectedList.length && profileIds.every(id => selectedList.includes(id))
    );
    activePresetIds = matchingPreset ? [...matchingPreset] : null;
    updateStartActionHighlights();
  }

  sections.forEach(sec => {
    const label = document.createElement('label');
    label.style.cursor = 'pointer';
    const cb = document.createElement('input');
    cb.type = 'checkbox';
    cb.value = sec.id;
    cb.addEventListener('change', () => {
      if (cb.checked) chosen.add(cb.value);
      else chosen.delete(cb.value);
      updateBeginButtonState();
    });
    checkboxById.set(sec.id, cb);
    label.append(cb, ' ', sec.title);
    container.append(label);
  });

  function beginWithSelection() {
    const list = getChosenInSectionOrder();
    if (!list.length) return;
    // Clear prior run data so summary/export only reflect the current run.
    localStorage.removeItem('droneSOPProgress');
    // Preserve flight log state when updating SOP selections.
    // Initialize new progress structure
    const progress = {};
    list.forEach(id => {
      progress[id] = { status: 'not-started', data: {} };
    });
    const sopProgress = { selectedSOPs: list, progress };
    localStorage.setItem('droneSOPProgress', JSON.stringify(sopProgress));
    localStorage.setItem('selectedSections', JSON.stringify(list));
    // Go to first section
    window.location.href = `sections/${list[0]}.html`;
  }

  microBtn.addEventListener('click', () => applyPreset('micro'));
  basicBtn.addEventListener('click', () => applyPreset('basic'));
  advBtn.addEventListener('click', () => applyPreset('advanced'));

  acceptDefaultsBtn.addEventListener('click', () => beginWithSelection());
  addMoreBtn.addEventListener('click', () => {
    container.scrollIntoView({ behavior: 'smooth', block: 'start' });
    promptLine.textContent = 'Adjust selections below, then click Start With Selected Sections.';
  });

  btn.addEventListener('click', () => beginWithSelection());
  updateBeginButtonState();
  hydrateSelectionsFromSession();

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
  const weatherStatus = document.getElementById('flight-weather-status');
  const weatherRefreshBtn = document.getElementById('flight-weather-refresh');
  const submitBtn = form ? form.querySelector('button[type="submit"]') : null;

  const RECENT_PILOTS_KEY = 'flightRecentPilots';
  const RECENT_OBSERVERS_KEY = 'flightRecentObservers';

  const parseList = key => {
    const parsed = safeParseJSON(key, []);
    return Array.isArray(parsed) ? parsed.filter(v => typeof v === 'string' && v.trim()) : [];
  };

  const saveRecentValue = (key, value) => {
    const clean = String(value || '').trim();
    if (!clean) return;
    const existing = parseList(key).filter(v => v.toLowerCase() !== clean.toLowerCase());
    const next = [clean, ...existing].slice(0, 3);
    localStorage.setItem(key, JSON.stringify(next));
  };

  const attachRecentList = (inputEl, key, datalistId) => {
    if (!inputEl) return;
    const list = parseList(key);
    const dl = document.createElement('datalist');
    dl.id = datalistId;
    list.forEach(name => {
      const opt = document.createElement('option');
      opt.value = name;
      dl.appendChild(opt);
    });
    document.body.appendChild(dl);
    inputEl.setAttribute('list', datalistId);
  };

  const formatTimeHHMM = d => {
    const h = String(d.getHours()).padStart(2, '0');
    const m = String(d.getMinutes()).padStart(2, '0');
    return `${h}:${m}`;
  };

  const now = new Date();
  const plus30 = new Date(now.getTime() + 30 * 60000);

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
    updateFlightLogLocationButtonLabel();
  };

  const updateFlightLogLocationButtonLabel = () => {
    if (!btn) return;
    const ddStored = localStorage.getItem('pilotLocationDD') || '';
    const parsedFromDD = parseLatLonText(ddStored);
    const parsedFromInput = parseLatLonText((loc && loc.value) ? loc.value : '');
    const active = parsedFromDD || parsedFromInput;
    const hasDefinedLocation = !!(active && !isPilotLocationUndefined(active.lat, active.lon));
    btn.textContent = hasDefinedLocation ? 'Refresh Pilot Location' : 'Get Pilot Location';
  };

  const renderFlightWeatherStatus = () => {
    if (!weatherStatus) return;

    const completedAt = localStorage.getItem('dwCheckCompletedAt');
    const latest = safeParseJSON('dwCheckLatest', null);
    const stamp = completedAt || (latest && latest.committedAt) || (latest && latest.timestamp) || '';

    if (!stamp) {
      weatherStatus.textContent = 'Last Weather Check: not saved yet.';
      if (weatherRefreshBtn) weatherRefreshBtn.textContent = 'Run Drone Risk and Weather Survey';
      return;
    }

    const whenMs = new Date(stamp).getTime();
    if (!Number.isFinite(whenMs)) {
      weatherStatus.textContent = 'Last Weather Check: saved (time unavailable).';
      return;
    }

    const hours = Math.max(0, (Date.now() - whenMs) / 3600000);
    const elapsedText = hours < 1
      ? `${Math.round(hours * 60)} min since saved`
      : `${hours.toFixed(1)} hr since saved`;
    weatherStatus.textContent = `Last Weather Check: ${elapsedText}.`;
    if (weatherRefreshBtn) weatherRefreshBtn.textContent = 'Refresh Weather Assessment';
  };

  const saved = safeParseJSON('flightLog', {});
  const savedAt = localStorage.getItem('flightLogSavedAt') || '';
  const recentPilots = parseList(RECENT_PILOTS_KEY);
  const recentObservers = parseList(RECENT_OBSERVERS_KEY);

  dateIn.value = saved.date || localStorage.getItem('flightDate') || new Date().toISOString().split('T')[0];
  pilot.value  = saved.pilot || localStorage.getItem('flightPilot') || recentPilots[0] || '';
  obs.value    = saved.observers || localStorage.getItem('flightObservers') || recentObservers[0] || '';
  start.value  = saved.start || localStorage.getItem('flightStart') || formatTimeHHMM(now);
  end.value    = saved.end || localStorage.getItem('flightEnd') || formatTimeHHMM(plus30);
  loc.value    = saved.location || localStorage.getItem('flightLocation') || '';

  attachRecentList(pilot, RECENT_PILOTS_KEY, 'pilot-names-list');
  attachRecentList(obs, RECENT_OBSERVERS_KEY, 'observer-names-list');

  let flightLogStatus = document.getElementById('flight-log-status');
  if (!flightLogStatus && form) {
    flightLogStatus = document.createElement('p');
    flightLogStatus.id = 'flight-log-status';
    flightLogStatus.className = 'subtle';
    form.parentNode.insertBefore(flightLogStatus, form.nextSibling);
  }

  let summaryQuickLink = document.getElementById('flight-log-summary-link');
  if (!summaryQuickLink && form) {
    summaryQuickLink = document.createElement('a');
    summaryQuickLink.id = 'flight-log-summary-link';
    summaryQuickLink.href = 'summary.html';
    summaryQuickLink.textContent = 'Proceed to Summary';
    summaryQuickLink.style.display = 'none';
    summaryQuickLink.style.marginLeft = '12px';
    summaryQuickLink.style.padding = '6px 10px';
    summaryQuickLink.style.borderRadius = '999px';
    summaryQuickLink.style.background = '#2f9e44';
    summaryQuickLink.style.color = '#ffffff';
    summaryQuickLink.style.textDecoration = 'none';
    summaryQuickLink.style.fontWeight = '600';
    form.appendChild(summaryQuickLink);
  }

  if (saved && (saved.date || saved.pilot || saved.location)) {
    if (submitBtn) submitBtn.textContent = 'Update Flight Log';
    if (flightLogStatus) {
      flightLogStatus.textContent = savedAt
        ? `Flight Log saved in this session at ${new Date(savedAt).toLocaleString()}. You can edit and update.`
        : 'Flight Log already saved in this session. You can edit and update.';
    }
    if (summaryQuickLink) summaryQuickLink.style.display = 'inline-block';
  }

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

  updateFlightLogLocationButtonLabel();
  renderFlightWeatherStatus();

  window.addEventListener('pageshow', () => {
    updateFlightLogLocationButtonLabel();
    renderFlightWeatherStatus();
  });

  if (weatherRefreshBtn) {
    weatherRefreshBtn.addEventListener('click', () => {
      // Launch the same tool referenced in Tools -> Drone Risk and Weather Survey.
      window.location.href = 'DWCheck.html?from=flight-log';
    });
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
          updateFlightLogLocationButtonLabel();
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
    localStorage.setItem('flightLogLatest', JSON.stringify(flightLog));
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
      updateFlightLogLocationButtonLabel();
    }

    const saveTs = new Date().toISOString();
    localStorage.setItem('flightLogSavedAt', saveTs);
    saveRecentValue(RECENT_PILOTS_KEY, flightLog.pilot);
    saveRecentValue(RECENT_OBSERVERS_KEY, flightLog.observers);

    if (submitBtn) submitBtn.textContent = 'Update Flight Log';
    if (flightLogStatus) {
      flightLogStatus.textContent = `Flight Log saved at ${new Date(saveTs).toLocaleString()}. You can edit and update, or continue to Summary.`;
    }
    if (summaryQuickLink) summaryQuickLink.style.display = 'inline-block';

    alert('✅ Flight log saved.');
  });
}

// ─── SECTION PAGES ─────────────────────────────────────────────────────────────
function renderSectionPage(sections) {
  const id = window.location.pathname.split('/').pop().replace('.html', '');
  const current = sections.find(s => s.id === id);
  if (!current) return console.error('Unknown section:', id);
  const params = new URLSearchParams(window.location.search);
  const fromSummary = params.get('from') === 'summary';
  let nextHighlightTimer = null;
  let saveNeedsAttention = true;

  const sopProgress = safeParseJSON('droneSOPProgress', {});
  const selected = sopProgress.selectedSOPs || [];
  const currentProgress = (sopProgress.progress && sopProgress.progress[current.id])
    ? sopProgress.progress[current.id]
    : { status: 'not-started', data: {} };

  document.getElementById('section-title').textContent = current.title;
  const container = document.getElementById('checklist-container');
  container.innerHTML = ''; // Clear "Loading..."

  // Render checklist items
  let responses = safeParseJSON(`responses_${current.id}`, []);
  if (responses.length !== current.items.length) {
    responses = current.items.map(() => false);
  }
  const itemCheckboxes = [];

  const persistResponses = () => {
    localStorage.setItem(`responses_${current.id}`, JSON.stringify(responses));
  };

  const setAllChecklistItems = (checked) => {
    responses = responses.map(() => checked);
    itemCheckboxes.forEach(cb => {
      cb.checked = checked;
    });
    persistResponses();
    syncSectionStatusFromUI();
    updateSaveProgressHighlight(true);
  };

  const syncSectionStatusFromUI = () => {
    const completedToggleEl = document.getElementById('section-completed');
    const isCompleted = !!(completedToggleEl && completedToggleEl.checked);
    const hasAnyChecks = responses.some(Boolean);

    let sopProgress = safeParseJSON('droneSOPProgress', {});
    sopProgress.progress = sopProgress.progress || {};
    sopProgress.progress[current.id] = sopProgress.progress[current.id] || { data: {} };
    sopProgress.progress[current.id].status = isCompleted
      ? 'completed'
      : (hasAnyChecks ? 'in-progress' : 'not-started');
    localStorage.setItem('droneSOPProgress', JSON.stringify(sopProgress));
  };

  const firstItemText = String(current.items[0] || '');
  const firstItemMeansChecklistComplete = /checklist\s+completed/i.test(firstItemText);

  current.items.forEach((item, idx) => {
    const div = document.createElement('div');
    div.className = 'check-item';
    const cb = document.createElement('input');
    cb.type    = 'checkbox';
    cb.checked = responses[idx];
    cb.addEventListener('change', () => {
      responses[idx] = cb.checked;
      if (idx === 0 && cb.checked && firstItemMeansChecklistComplete) {
        setAllChecklistItems(true);
        return;
      }
      persistResponses();
      syncSectionStatusFromUI();
      updateSaveProgressHighlight(true);
    });
    itemCheckboxes.push(cb);
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

  const completedToggle = completeDiv.querySelector('#section-completed');
  if (completedToggle) {
    completedToggle.checked = currentProgress.status === 'completed';
    completedToggle.addEventListener('change', () => {
      syncSectionStatusFromUI();
      updateSaveProgressHighlight(true);
    });
  }

  const completeHint = document.createElement('span');
  completeHint.className = 'subtle';
  completeHint.style.marginLeft = '1em';
  completeHint.textContent = 'Status updates automatically. Mark completed when finished.';
  completeDiv.appendChild(completeHint);

  const selectAllBtn = document.createElement('button');
  selectAllBtn.textContent = 'Select All Items';
  selectAllBtn.style.marginLeft = '1em';
  selectAllBtn.type = 'button';
  selectAllBtn.addEventListener('click', () => {
    setAllChecklistItems(true);
  });
  completeDiv.appendChild(selectAllBtn);

  const saveBtn = document.createElement('button');
  saveBtn.textContent = 'Save Progress';
  saveBtn.style.marginLeft = '1em';
  saveBtn.type = 'button';

  const updateSaveProgressHighlight = (needsSave) => {
    saveNeedsAttention = !!needsSave;
    if (saveNeedsAttention) {
      saveBtn.style.boxShadow = '0 0 0 3px rgba(47, 158, 68, 0.45)';
      saveBtn.style.background = '#2f9e44';
      saveBtn.style.color = '#ffffff';
      return;
    }

    saveBtn.style.boxShadow = '';
    saveBtn.style.background = '';
    saveBtn.style.color = '';
  };

  const saveStatus = document.createElement('span');
  saveStatus.className = 'subtle';
  saveStatus.style.marginLeft = '0.75em';
  let saveStatusTimer = null;
  saveBtn.addEventListener('click', () => {
    persistResponses();
    syncSectionStatusFromUI();
    saveStatus.textContent = 'Progress saved.';
    if (saveStatusTimer) clearTimeout(saveStatusTimer);
    saveStatusTimer = setTimeout(() => {
      saveStatus.textContent = '';
    }, 3000);

    const nextActionBtn = document.getElementById('section-next-btn');
    if (nextActionBtn) {
      nextActionBtn.style.boxShadow = '0 0 0 3px rgba(47, 158, 68, 0.45)';
      nextActionBtn.style.background = '#2f9e44';
      nextActionBtn.style.color = '#ffffff';
      if (nextHighlightTimer) clearTimeout(nextHighlightTimer);
      nextHighlightTimer = setTimeout(() => {
        nextActionBtn.style.boxShadow = '';
        nextActionBtn.style.background = '';
        nextActionBtn.style.color = '';
      }, 3000);
    }

    updateSaveProgressHighlight(false);
  });
  completeDiv.appendChild(saveBtn);
  completeDiv.appendChild(saveStatus);

  syncSectionStatusFromUI();
  updateSaveProgressHighlight(true);

  // Use droneSOPProgress for navigation
  const idx = selected.indexOf(current.id);
  const allowBackwardNav = selected.length > 1 || fromSummary;

  // Create navigation buttons
  const navDiv = document.createElement('div');
  navDiv.style.marginTop = '2em';

  if (allowBackwardNav) {
    const homeBtn = document.createElement('button');
    homeBtn.textContent = fromSummary ? 'Return to Summary' : 'Return to Checklists';
    homeBtn.onclick = () => {
      window.location.href = fromSummary ? '../summary.html' : '../Sections.html';
    };
    navDiv.appendChild(homeBtn);
  }

  // Prev button
  const prevBtn = document.createElement('button');
  prevBtn.textContent = '< Previous';
  prevBtn.style.marginLeft = allowBackwardNav ? '1em' : '0';
  prevBtn.onclick = () => {
    if (idx > 0) {
      window.location.href = `../sections/${selected[idx-1]}.html`;
    }
  };
  prevBtn.disabled = !allowBackwardNav || idx <= 0;
  if (allowBackwardNav) {
    navDiv.appendChild(prevBtn);
  }

  // Next or Flight Log button
  const nextBtn = document.createElement('button');
  nextBtn.id = 'section-next-btn';
  nextBtn.style.marginLeft = '1em';
  if (idx < selected.length - 1) {
    nextBtn.textContent = 'Next >';
    nextBtn.onclick = () => {
      window.location.href = `../sections/${selected[idx+1]}.html`;
    };
  } else {
    if (fromSummary) {
      nextBtn.textContent = 'Return to Summary';
      nextBtn.onclick = () => {
        window.location.href = '../summary.html';
      };
    } else {
      nextBtn.textContent = 'Save Selections for Flight Log Report';
      nextBtn.onclick = () => {
        // Keep section selections in session and continue to tools workflow.
        localStorage.setItem('selectedSections', JSON.stringify(selected));
        window.location.href = '../tools.html';
      };
    }
  }
  navDiv.appendChild(nextBtn);

  container.appendChild(navDiv);
}

// ─── SUMMARY PAGE ──────────────────────────────────────────────────────────────
function renderSummary(sections) {
  const container = document.getElementById('summary-container');
  if (!container) return;

  const flightLog = safeParseJSON('flightLog', {});
  const flightLogFallback = safeParseJSON('flightLogLatest', {});
  const activeFlightLog = (flightLog && (flightLog.date || flightLog.pilot || flightLog.observers || flightLog.start || flightLog.end || flightLog.location))
    ? flightLog
    : flightLogFallback;
  const hasFlightLogData = !!(activeFlightLog && (activeFlightLog.date || activeFlightLog.pilot || activeFlightLog.observers || activeFlightLog.start || activeFlightLog.end || activeFlightLog.location));
  const flightLogSavedAt = localStorage.getItem('flightLogSavedAt') || '';
  const flightLogSavedMs = flightLogSavedAt ? new Date(flightLogSavedAt).getTime() : NaN;
  const flightLogAgeHr = Number.isFinite(flightLogSavedMs) ? (Date.now() - flightLogSavedMs) / 3600000 : null;
  const flightLogFresh = flightLogAgeHr != null && flightLogAgeHr < 1;
  const flightLogCtaLabel = (hasFlightLogData && flightLogFresh)
    ? `Log Saved @ ${new Date(flightLogSavedAt).toLocaleString()}`
    : 'Complete Flight Log';
  const flightLogCtaClass = (hasFlightLogData && flightLogFresh) ? 'summary-cta-green' : 'summary-cta-red';
  const wrapper   = document.createElement('div');
  wrapper.className = 'flight-log-wrapper';
  wrapper.innerHTML = `
    <div class="summary-header">
      <h2>Flight Log Information</h2>
      <a href="flight-log.html" class="summary-cta ${flightLogCtaClass}">${flightLogCtaLabel}</a>
    </div>
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
          <td>${activeFlightLog.date || '—'}</td>
          <td>${activeFlightLog.pilot || '—'} / ${activeFlightLog.observers || '—'}</td>
          <td>${activeFlightLog.start || '—'}</td>
          <td>${activeFlightLog.end || '—'}</td>
          <td>${activeFlightLog.location || '—'}</td>
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
    const weatherStamp = weatherCompleteAt || weather.committedAt || weather.timestamp;
    const stampMs = new Date(weatherStamp).getTime();
    const weatherAgeHr = Number.isFinite(stampMs) ? (Date.now() - stampMs) / 3600000 : null;
    const isFresh = weatherAgeHr != null && weatherAgeHr < 1;
    const weatherCtaLabel = isFresh ? 'Weather Survey <1 hr old' : 'Refresh Weather Survey';
    const weatherCtaClass = isFresh ? 'summary-cta-green' : 'summary-cta-red';
    const weatherCta = `<a href="DWCheck.html" class="summary-cta ${weatherCtaClass}">${weatherCtaLabel}</a>`;

    weatherDiv.innerHTML = `
      <div class="summary-header">
        <h2>Drone Risk and Weather Survey</h2>
        ${weatherCta}
      </div>
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
      <div class="summary-header">
        <h2>Drone Risk and Weather Survey</h2>
        <a href="DWCheck.html" class="summary-cta summary-cta-red">Refresh Weather Survey</a>
      </div>
      <p><em>No weather check artifact saved for this session.</em></p>
    `;
  }

  container.append(weatherDiv);

  // Prefer the current key; keep legacy fallback for older saved sessions.
  const sopProgress = safeParseJSON('droneSOPProgress', {});
  const selected = sopProgress.selectedSOPs || safeParseJSON('selectedSections', []);

  const sopSummary = document.createElement('div');
  sopSummary.className = 'section-block';
  const sopProgressMap = sopProgress.progress || {};
  const allCompleted = selected.length
    ? selected.every(secId => (sopProgressMap[secId] && sopProgressMap[secId].status === 'completed'))
    : false;
  const sopCta = document.createElement('a');
  sopCta.href = 'Sections.html';
  sopCta.className = 'summary-cta';

  if (!selected.length) {
    sopSummary.innerHTML = '<div class="summary-header"><h2>SOP Procedures</h2></div><p><em>No SOP procedures were selected for this run.</em></p>';
    sopCta.classList.add('summary-cta-red');
    sopCta.textContent = 'Select SOP Sections';
  } else if (!allCompleted) {
    const firstIncomplete = selected.find(secId => !(sopProgressMap[secId] && sopProgressMap[secId].status === 'completed'));
    sopSummary.innerHTML = '<div class="summary-header"><h2>SOP Procedures</h2></div><p><em>Some SOP checks are still incomplete.</em></p>';
    sopCta.classList.add('summary-cta-yellow');
    sopCta.textContent = 'Complete SOP Checks';
    if (firstIncomplete) {
      sopCta.href = `sections/${firstIncomplete}.html?from=summary`;
    }
  } else {
    sopSummary.innerHTML = '<div class="summary-header"><h2>SOP Procedures</h2></div><p><em>All selected SOP checks are complete.</em></p>';
    sopCta.classList.add('summary-cta-green');
    sopCta.textContent = 'SOP Completed';
  }

  const sopHeader = sopSummary.querySelector('.summary-header');
  if (sopHeader) sopHeader.appendChild(sopCta);
  else sopSummary.appendChild(sopCta);
  container.append(sopSummary);
  selected.forEach(secId => {
    const section   = sections.find(s => s.id === secId);
    const responses = safeParseJSON(`responses_${secId}`, []);
    const secStatus = (sopProgress.progress && sopProgress.progress[secId] && sopProgress.progress[secId].status)
      ? sopProgress.progress[secId].status
      : 'not-started';
    const block     = document.createElement('div');
    block.className = 'section-block';
    block.innerHTML = `<h2>${section.title}</h2>` +
      `<p><strong>Status:</strong> ${secStatus.replace('-', ' ')}</p>` +
      `<ul>${section.items.map((item,i) =>
        `<li>${responses[i] ? '✔' : '◻'} ${item}</li>`
      ).join('')}</ul>`;

    const revisitBtn = document.createElement('button');
    revisitBtn.textContent = secStatus === 'completed' ? 'Review/Edit' : 'Continue';
    revisitBtn.addEventListener('click', () => {
      window.location.href = `sections/${secId}.html?from=summary`;
    });
    block.appendChild(revisitBtn);

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

  function csvEscape(value) {
    const text = String(value ?? '');
    if (/[",\n]/.test(text)) return `"${text.replace(/"/g, '""')}"`;
    return text;
  }

  function inferChecklistProfile(selectedIds) {
    if (!Array.isArray(selectedIds) || !selectedIds.length) return 'Custom';

    const micro = ['1_0_Micro_Pre-Flight', '2_0_Takeoff_Procedures', '3_0_Landing_Procedures'];
    const basic = ['1_1_Basic_Pre-Flight', '2_0_Takeoff_Procedures', '3_0_Landing_Procedures', '5_1_Basic_Rules'];
    const advanced = ['1_2_Advanced_Pre-Flight', '2_0_Takeoff_Procedures', '3_0_Landing_Procedures', '5_2_Advanced_Rules'];

    const hasAll = profile => profile.every(id => selectedIds.includes(id));
    const exact = profile => selectedIds.length === profile.length && hasAll(profile);

    if (exact(micro)) return 'Micro';
    if (exact(basic)) return 'Basic';
    if (exact(advanced)) return 'Advanced';
    if (hasAll(micro)) return 'Micro + Custom';
    if (hasAll(basic)) return 'Basic + Custom';
    if (hasAll(advanced)) return 'Advanced + Custom';
    return 'Custom';
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
    const weather = safeParseJSON('dwCheckLatest', null);
    const weatherComplete = localStorage.getItem('dwCheckCompleted') === 'true';
    const weatherCompleteAt = localStorage.getItem('dwCheckCompletedAt');
    const nearestStations = (weather && Array.isArray(weather.nearestStations))
      ? weather.nearestStations.map(s => `${s.icaoId} (${Number(s.distanceKm || 0).toFixed(1)} km)`).join('; ')
      : '';

    let csv = 'Field,Value\n'
      + `Date,${csvEscape(flightLog.date || '')}\n`
      + `Pilot(s),${csvEscape(flightLog.pilot || '')}\n`
      + `Observer(s),${csvEscape(flightLog.observers || '')}\n`
      + `Start,${csvEscape(flightLog.start || '')}\n`
      + `End,${csvEscape(flightLog.end || '')}\n`
      + `Location,${csvEscape(flightLog.location || '')}\n`
      + `Checklist Profile,${csvEscape(inferChecklistProfile(selected))}\n`;

    if (weather && weather.timestamp) {
      csv += `Weather Checked At,${csvEscape(new Date(weather.timestamp).toLocaleString())}\n`
        + `Weather Completed,${csvEscape(weatherComplete ? 'Yes' : 'No')}\n`
        + `Weather Completed At,${csvEscape(weatherCompleteAt ? new Date(weatherCompleteAt).toLocaleString() : '')}\n`
        + `Weather ICAO,${csvEscape(weather.icao || '')}\n`
        + `Weather Risk Label,${csvEscape(weather.riskLabel || '')}\n`
        + `Weather Risk Score,${csvEscape(weather.riskScore ?? '')}\n`
        + `Weather KP Index,${csvEscape(weather.kpIndex ?? '')}\n`
        + `Weather KP Condition,${csvEscape(weather.kpCondition || '')}\n`
        + `Weather Wind kt,${csvEscape(weather.windKt ?? '')}\n`
        + `Weather Gust kt,${csvEscape(weather.gustKt ?? '')}\n`
        + `Weather Visibility SM,${csvEscape(weather.visibilitySm ?? '')}\n`
        + `Weather Ceiling ft,${csvEscape(weather.ceilingFt ?? '')}\n`
        + `Weather Nearest Stations,${csvEscape(nearestStations)}\n`;
    } else {
      csv += 'Weather Check Saved,No\n';
    }

    csv += '\nSOP Section,Status\n';
    selected.forEach(secId => {
      const section = sections.find(s => s.id === secId);
      const secStatus = (sopProgress.progress && sopProgress.progress[secId] && sopProgress.progress[secId].status)
        ? sopProgress.progress[secId].status
        : 'not-started';
      csv += `${csvEscape(section ? section.title : secId)},${csvEscape(secStatus)}\n`;
    });

    csv += '\nSection,Item,Checked\n';
    selected.forEach(secId => {
      const section   = sections.find(s => s.id === secId);
      const responses = safeParseJSON(`responses_${secId}`, []);
      const firstItem = section && Array.isArray(section.items) && section.items.length
        ? section.items[0]
        : 'Checklist completed';
      const firstChecked = Array.isArray(responses) && responses.length ? !!responses[0] : false;
      csv += `${csvEscape(section ? section.title : secId)},${csvEscape(firstItem)},${csvEscape(firstChecked ? 'Yes' : 'No')}\n`;
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

  const saveSummaryBtn = document.getElementById('save-summary');
  const clearDataBtn = document.getElementById('clear-data');
  let summarySnapshotSaved = false;

  function buildSummarySnapshot() {
    const weatherLatest = safeParseJSON('dwCheckLatest', null);
    const weatherCompleted = localStorage.getItem('dwCheckCompleted') === 'true';
    const weatherCompletedAt = localStorage.getItem('dwCheckCompletedAt') || null;
    const sopLatest = safeParseJSON('droneSOPProgress', {});
    const selectedIds = Array.isArray(sopLatest.selectedSOPs)
      ? sopLatest.selectedSOPs
      : safeParseJSON('selectedSections', []);

    const selectedSections = selectedIds.map(secId => {
      const section = sections.find(s => s.id === secId);
      const responses = safeParseJSON(`responses_${secId}`, []);
      const status = (sopLatest.progress && sopLatest.progress[secId] && sopLatest.progress[secId].status)
        ? sopLatest.progress[secId].status
        : 'not-started';

      return {
        id: secId,
        title: section ? section.title : secId,
        status,
        checklistItems: section
          ? section.items.map((item, idx) => ({ item, checked: !!responses[idx] }))
          : []
      };
    });

    const createdAt = new Date().toISOString();

    return {
      createdAt,
      flightLog,
      weather: {
        completed: weatherCompleted,
        completedAt: weatherCompletedAt,
        latest: weatherLatest
      },
      selectedSections
    };
  }

  function saveSummarySnapshot() {
    const snapshot = buildSummarySnapshot();
    localStorage.setItem('flightSummaryLatest', JSON.stringify(snapshot));

    const history = safeParseJSON('flightSummaryHistory', []);
    const list = Array.isArray(history) ? history : [];
    list.unshift(snapshot);
    const trimmed = list.slice(0, 25);
    localStorage.setItem('flightSummaryHistory', JSON.stringify(trimmed));

    return snapshot;
  }

  function promptSummaryExportChoice() {
    const answer = prompt(
      'Summary snapshot saved. Export now? Type: csv, pdf, or skip',
      'csv'
    );

    if (answer === null) return 'cancelled';
    const choice = String(answer).trim().toLowerCase();
    if (!choice || choice === 'skip' || choice === 'none') return 'skip';
    if (choice === 'csv') return 'csv';
    if (choice === 'pdf') return 'pdf';
    return 'invalid';
  }

  function setSummaryButtonsDisabled(isDisabled) {
    if (saveSummaryBtn) saveSummaryBtn.disabled = isDisabled;
    if (clearDataBtn) clearDataBtn.disabled = isDisabled;
  }

  function clearInputsAndRestartHome() {
    setSummaryButtonsDisabled(true);
    setExportStatus('Clearing session inputs...');

    localStorage.removeItem('flightSummaryLatest');
    localStorage.removeItem('flightSummaryHistory');
    clearSessionStateAfterSummarySave();

    setExportStatus('All inputs cleared. Returning Home...');
    setTimeout(() => {
      window.location.href = 'index.html';
    }, 350);
  }

  function promoteSaveButtonToClearAction() {
    if (!saveSummaryBtn) return;

    summarySnapshotSaved = true;
    saveSummaryBtn.textContent = 'Clear Previous Inputs/Data';
    saveSummaryBtn.style.background = '#2f9e44';
    saveSummaryBtn.style.boxShadow = '0 0 0 3px rgba(47, 158, 68, 0.35)';

    if (clearDataBtn) {
      clearDataBtn.style.display = 'none';
      clearDataBtn.disabled = true;
    }
  }

  if (clearDataBtn) {
    clearDataBtn.addEventListener('click', () => {
      if (!confirm('Are you sure you want to wipe/clear all data? This cannot be undone.')) {
        setExportStatus('Clear inputs cancelled.');
        return;
      }

      clearInputsAndRestartHome();
    });
  }

  if (saveSummaryBtn) {
    saveSummaryBtn.addEventListener('click', () => {
      if (summarySnapshotSaved) {
        if (!confirm('Clear previous inputs/data and restart at Home?')) {
          setExportStatus('Clear inputs cancelled.');
          return;
        }
        clearInputsAndRestartHome();
        return;
      }

      setSummaryButtonsDisabled(true);

      const snapshot = saveSummarySnapshot();
      const savedAt = new Date(snapshot.createdAt).toLocaleString();
      setExportStatus(`Summary snapshot saved at ${savedAt}.`);

      const choice = promptSummaryExportChoice();
      if (choice === 'csv') {
        document.getElementById('export-csv').click();
      } else if (choice === 'pdf') {
        document.getElementById('export-pdf').click();
      } else if (choice === 'invalid') {
        setExportStatus('Unknown choice. Snapshot saved; export skipped.', true);
      } else if (choice === 'skip') {
        setExportStatus(`Summary snapshot saved at ${savedAt}. Export skipped.`);
      }

      promoteSaveButtonToClearAction();
      setExportStatus('Summary saved. Next step: Clear Previous Inputs/Data to start a new run from Home.');
      setSummaryButtonsDisabled(false);
    });
  }

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
