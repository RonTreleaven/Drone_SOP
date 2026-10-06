'use strict';
// Prototype mission distance / time / battery estimator. Pure functions, no DOM, no dependencies.
// Used by GGcode.html (window.MissionEstimate) and by Dev/mission_estimate tests (require).

const EARTH_R = 6371008.8;

// Mini 5 Pro planning assumptions. Verify against DJI specs before relying on them.
const DRONE_PROFILES = {
  mini5pro: {
    label: 'DJI Mini 5 Pro',
    maxHorizSpeedMs: 18,
    ascentMs: 5,
    descentMs: 5,
    landingFinalMs: 1.5,
    landingFinalFromM: 10,
    accelMs2: 2,
    maxWindMs: 12,
    batteries: { standard: 21, plus: 33 } // typical flight minutes, not maximum
  }
};

const DEFAULTS = {
  droneKey: 'mini5pro',
  battery: 'standard',
  speedMs: 5,
  heightM: 30,
  finishAction: 'goHome',
  rthSpeedMs: 12,
  rthAltM: null, // null: stay at last waypoint height
  startupSec: 10,
  hoverDefaultSec: 0,
  orthoPrecise: false,
  stopTurnThresholdDeg: 55,
  windMs: 0,
  contingencyMin: 0, // safety reserve in minutes (RTH buffer); compared against remaining battery, not added to use
  reservePct: 25,
  cautionPct: 70,
  orbitLaps: 1,
  home: null // {lat,lng}; null: centroid of the route
};

const toRad = (d) => (d * Math.PI) / 180;

function haversineM(a, b) {
  const dLat = toRad(b.lat - a.lat);
  const dLng = toRad(b.lng - a.lng);
  const s = Math.sin(dLat / 2) ** 2 + Math.cos(toRad(a.lat)) * Math.cos(toRad(b.lat)) * Math.sin(dLng / 2) ** 2;
  return 2 * EARTH_R * Math.asin(Math.min(1, Math.sqrt(s)));
}

function bearingDeg(a, b) {
  const y = Math.sin(toRad(b.lng - a.lng)) * Math.cos(toRad(b.lat));
  const x = Math.cos(toRad(a.lat)) * Math.sin(toRad(b.lat)) -
    Math.sin(toRad(a.lat)) * Math.cos(toRad(b.lat)) * Math.cos(toRad(b.lng - a.lng));
  return (Math.atan2(y, x) * 180 / Math.PI + 360) % 360;
}

function turnAngleDeg(prev, cur, next) {
  const d = Math.abs(bearingDeg(cur, next) - bearingDeg(prev, cur)) % 360;
  return d > 180 ? 360 - d : d;
}

function centroid(input) {
  const closed = input.length > 2 && haversineM(input[0], input[input.length - 1]) < 1;
  const points = closed ? input.slice(0, -1) : input;
  const n = points.length;
  return {
    lat: points.reduce((s, p) => s + p.lat, 0) / n,
    lng: points.reduce((s, p) => s + p.lng, 0) / n
  };
}

// Detects a closed, roughly circular route. Returns null if not an orbit.
function detectOrbit(points, tolerance = 0.03) {
  if (!Array.isArray(points) || points.length < 6) return null;
  const first = points[0];
  const last = points[points.length - 1];
  const closed = haversineM(first, last) < 1;
  const ring = closed ? points.slice(0, -1) : points;
  if (ring.length < 6) return null;
  const c = centroid(ring);
  const radii = ring.map((p) => haversineM(c, p));
  const mean = radii.reduce((s, r) => s + r, 0) / radii.length;
  if (mean < 5) return null;
  const maxDev = Math.max(...radii.map((r) => Math.abs(r - mean) / mean));
  if (maxDev > tolerance) return null;
  return { center: c, radiusM: mean, closed, vertices: ring.length };
}

function polylineHorizontalM(points) {
  let t = 0;
  for (let i = 1; i < points.length; i++) t += haversineM(points[i - 1], points[i]);
  return t;
}

function windFactor(windMs, maxWindMs) {
  const r = Math.max(0, windMs) / maxWindMs;
  return 1 + 0.5 * r * r; // heuristic energy multiplier, not a measured curve
}

// waypoints: [{lat, lng, heightM, speedMs, hoverSec}]
function estimateMission(waypoints, options = {}) {
  const o = { ...DEFAULTS, ...options };
  const drone = DRONE_PROFILES[o.droneKey];
  if (!drone) throw new Error(`Unknown drone profile: ${o.droneKey}`);
  if (!Array.isArray(waypoints) || waypoints.length < 2) throw new Error('Need at least 2 waypoints');

  const wps = waypoints.map((w) => ({
    lat: Number(w.lat),
    lng: Number(w.lng),
    heightM: Number.isFinite(w.heightM) ? w.heightM : o.heightM,
    speedMs: Number.isFinite(w.speedMs) && w.speedMs > 0 ? w.speedMs : o.speedMs,
    hoverSec: Number.isFinite(w.hoverSec) && w.hoverSec > 0 ? w.hoverSec : o.hoverDefaultSec
  }));

  const warnings = [];
  const home = o.home || centroid(wps);
  const a = drone.accelMs2;
  const parts = []; // {key,label,distM,sec}
  const add = (key, label, distM, sec) => parts.push({ key, label, distM, sec });

  add('startup', 'Pre-takeoff / spin-up', 0, o.startupSec);

  const first = wps[0];
  add('climb', 'Climb to first waypoint height', first.heightM, first.heightM / drone.ascentMs);

  const transitM = haversineM(home, first);
  add('transit', 'Transit takeoff point to waypoint 1', transitM, transitM / first.speedMs + first.speedMs / (2 * a));

  // Waypoint legs (3D, vertical rate limited)
  let legHorizM = 0;
  let legDistM = 0;
  let legSec = 0;
  for (let i = 1; i < wps.length; i++) {
    const h = haversineM(wps[i - 1], wps[i]);
    const dz = wps[i].heightM - wps[i - 1].heightM;
    const v = wps[i].speedMs;
    const vertLimit = dz >= 0 ? drone.ascentMs : drone.descentMs;
    legHorizM += h;
    legDistM += Math.hypot(h, dz);
    legSec += Math.max(h / v, Math.abs(dz) / vertLimit);
  }
  add('legs', 'Waypoint legs', legDistM, legSec);

  // Orbit: aircraft rounds corners on a curved path, so use the true circle length
  const orbit = detectOrbit(wps);
  let orbitInfo = null;
  if (orbit) {
    const circleM = 2 * Math.PI * orbit.radiusM * o.orbitLaps;
    const polyM = legHorizM * o.orbitLaps;
    const curveM = (2 * Math.PI * orbit.radiusM - legHorizM) * o.orbitLaps;
    const avgV = wps.reduce((s, w) => s + w.speedMs, 0) / wps.length;
    if (o.orbitLaps > 1) {
      add('extraLaps', `Additional laps (${o.orbitLaps - 1})`, legDistM * (o.orbitLaps - 1), legSec * (o.orbitLaps - 1));
    }
    add('orbitCurve', 'Orbit curvature (true circle vs polygon)', curveM, curveM / avgV);
    orbitInfo = {
      radiusM: orbit.radiusM,
      vertices: orbit.vertices,
      polygonLengthM: polyM,
      circleLengthM: circleM,
      laps: o.orbitLaps
    };
  }

  const hoverSec = wps.reduce((s, w) => s + w.hoverSec, 0);
  if (hoverSec > 0) add('hover', 'Hover / photo pauses', 0, hoverSec);

  // Stop-and-turn penalty only in Ortho-Precise mode
  if (o.orthoPrecise) {
    let n = 0;
    let sec = 0;
    for (let i = 1; i < wps.length - 1; i++) {
      if (turnAngleDeg(wps[i - 1], wps[i], wps[i + 1]) >= o.stopTurnThresholdDeg) {
        n++;
        sec += wps[i].speedMs / a;
      }
    }
    if (n) add('stopTurns', `Stop-and-turn (${n} vertices)`, 0, sec);
  }

  // Finish action
  const last = wps[wps.length - 1];
  const fin = o.finishAction;
  const landSec = (alt) => {
    const lowM = Math.min(alt, drone.landingFinalFromM);
    return Math.max(0, alt - lowM) / drone.descentMs + lowM / drone.landingFinalMs;
  };
  if (fin === 'goHome') {
    const rthAlt = Number.isFinite(o.rthAltM) ? o.rthAltM : last.heightM;
    const dz = rthAlt - last.heightM;
    const rthM = haversineM(last, home);
    const climbSec = dz > 0 ? dz / drone.ascentMs : 0;
    add('rth', 'Return to home leg', rthM + Math.abs(dz), climbSec + rthM / o.rthSpeedMs + o.rthSpeedMs / (2 * a));
    add('landing', 'Descent and landing', rthAlt, landSec(rthAlt));
  } else if (fin === 'autoLand') {
    add('landing', 'Descent and landing at last waypoint', last.heightM, landSec(last.heightM));
  } else if (fin === 'goToFirstWaypoint') {
    const m = haversineM(last, first);
    add('toFirst', 'Return to first waypoint', m, m / first.speedMs);
  } else if (fin !== 'noAction') {
    warnings.push(`Unknown finish action "${fin}"; no finish leg counted.`);
  }

  const totalSec = parts.reduce((s, p) => s + p.sec, 0);
  const totalM = parts.reduce((s, p) => s + p.distM, 0);

  // Battery
  const capMin = drone.batteries[o.battery];
  const wf = windFactor(o.windMs, drone.maxWindMs);
  // Flight energy only. The RTH buffer is a safety reserve held back, not energy used (the return leg is already in totalSec).
  const energySec = totalSec * wf;
  const usedPct = (energySec / (capMin * 60)) * 100;
  const flightPct = (totalSec / (capMin * 60)) * 100;
  const windPct = usedPct - flightPct;
  const bufferPct = (Math.max(0, o.contingencyMin) * 60 / (capMin * 60)) * 100;
  const requiredReservePct = Math.max(o.reservePct, bufferPct);
  const maxSpeedMs = Math.max(...wps.map((w) => w.speedMs));
  if (usedPct > 100 - requiredReservePct) warnings.push(`Battery use ${usedPct.toFixed(0)}% leaves less than the ${requiredReservePct.toFixed(0)}% reserve (greater of reserve setting and RTH buffer).`);
  else if (usedPct > o.cautionPct) warnings.push(`Battery use ${usedPct.toFixed(0)}% is above the ${o.cautionPct}% caution level.`);
  if (o.windMs > 0.7 * drone.maxWindMs) warnings.push(`Wind ${o.windMs} m/s is above 70% of the ${drone.maxWindMs} m/s rated limit.`);
  if (maxSpeedMs + o.windMs > drone.maxHorizSpeedMs) warnings.push('Mission speed plus wind may exceed the aircraft maximum speed (cannot hold ground speed into a headwind).');
  if (maxSpeedMs > drone.maxHorizSpeedMs) warnings.push('Mission speed exceeds aircraft maximum.');
  if (o.finishAction === 'goHome' && !o.home) warnings.push('Takeoff point assumed at route centroid; set it to the pilot position for accurate transit and return legs.');

  return {
    drone: drone.label,
    parts,
    totalDistanceM: totalM,
    totalSec,
    pathOnly: { horizontalM: legHorizM, speedMs: wps[1].speedMs, sec: legHorizM / wps[1].speedMs },
    orbit: orbitInfo,
    battery: {
      type: o.battery,
      capacityMin: capMin,
      windFactor: wf,
      energyMin: energySec / 60,
      usedPct,
      flightPct,
      windPct,
      bufferPct,
      requiredReservePct,
      remainingPct: 100 - usedPct
    },
    warnings
  };
}

// ---- Parsing ----

function parseNameTokens(name) {
  const out = {};
  const base = String(name || '').replace(/\.[a-z0-9]+$/i, '');
  const agl = base.match(/AGL(\d+(?:p\d+)?)/i);
  const spd = base.match(/_S(\d+(?:p\d+)?)(?:_|$)/i);
  const orb = base.match(/_O(\d+)/i);
  if (agl) out.heightM = Number(agl[1].replace('p', '.'));
  if (spd) out.speedMs = Number(spd[1].replace('p', '.'));
  if (orb) out.orbitRadiusM = Number(orb[1]);
  return out;
}

function tag(xml, name) {
  const m = xml.match(new RegExp(`<(?:wpml:)?${name}>\\s*([^<]*?)\\s*</(?:wpml:)?${name}>`));
  return m ? m[1] : null;
}

// Accepts a plain KML LineString or a DJI waylines.wpml. Returns {waypoints, mission}.
function parseMissionXml(xml) {
  const placemarks = xml.split(/<Placemark>/).slice(1);
  const mission = {
    finishAction: tag(xml, 'finishAction'),
    speedMs: Number(tag(xml, 'autoFlightSpeed')) || Number(tag(xml, 'globalTransitionalSpeed')) || null
  };
  const waypoints = [];
  const nameTag = xml.match(/<name>([^<]*)<\/name>/);
  mission.name = nameTag ? nameTag[1] : '';

  const wpmlPlacemarks = placemarks.filter((p) => /<wpml:index>/.test(p));
  if (wpmlPlacemarks.length) {
    for (const p of wpmlPlacemarks) {
      const c = (p.match(/<Point>\s*<coordinates>\s*([^<]+?)\s*<\/coordinates>/) || [])[1];
      if (!c) continue;
      const [lng, lat] = c.split(',').map(Number);
      let hover = 0;
      const re = /<wpml:action>[\s\S]*?<\/wpml:action>/g;
      for (const act of p.match(re) || []) {
        if (/<wpml:actionActuatorFunc>hover<\/wpml:actionActuatorFunc>/.test(act)) {
          hover += Number(tag(act, 'hoverTime')) || 0;
        }
      }
      waypoints.push({
        lat, lng,
        heightM: Number(tag(p, 'executeHeight')),
        speedMs: Number(tag(p, 'waypointSpeed')),
        hoverSec: hover
      });
    }
    return { waypoints, mission };
  }

  for (const p of placemarks) {
    const ls = p.match(/<LineString>[\s\S]*?<coordinates>([\s\S]*?)<\/coordinates>/);
    if (!ls) continue;
    for (const tri of ls[1].trim().split(/\s+/)) {
      const [lng, lat] = tri.split(',').map(Number);
      if (Number.isFinite(lat) && Number.isFinite(lng)) waypoints.push({ lat, lng });
    }
  }
  return { waypoints, mission };
}

// ---- Formatting ----

function fmtTime(sec) {
  const total = Math.round(sec);
  const m = Math.floor(total / 60);
  const s = total - m * 60;
  return `${m}:${String(s).padStart(2, '0')} min`;
}

function formatReport(est) {
  const lines = [];
  lines.push(`Mission estimate (${est.drone})`);
  for (const p of est.parts) {
    lines.push(`  ${p.label.padEnd(46)} ${p.distM.toFixed(0).padStart(7)} m  ${fmtTime(p.sec).padStart(11)}`);
  }
  lines.push(`  ${'TOTAL'.padEnd(46)} ${est.totalDistanceM.toFixed(0).padStart(7)} m  ${fmtTime(est.totalSec).padStart(11)}`);
  const b = est.battery;
  lines.push(`  Battery (${b.type}, ${b.capacityMin} min typical): ${b.usedPct.toFixed(0)}% used, ${b.remainingPct.toFixed(0)}% remaining (flight ${b.flightPct.toFixed(0)}% + wind ${b.windPct.toFixed(0)}%; reserve held ${b.requiredReservePct.toFixed(0)}%; wind factor ${b.windFactor.toFixed(2)})`);
  if (est.orbit) {
    const o = est.orbit;
    lines.push(`  Orbit: R=${o.radiusM.toFixed(0)} m, ${o.vertices} vertices, polygon ${o.polygonLengthM.toFixed(0)} m vs circle ${o.circleLengthM.toFixed(0)} m`);
  }
  lines.push(`  Simple path-only estimate (current GGcode method): ${est.pathOnly.horizontalM.toFixed(0)} m, ${fmtTime(est.pathOnly.sec)}`);
  for (const w of est.warnings) lines.push(`  WARNING: ${w}`);
  return lines.join('\n');
}

const api = {
  DRONE_PROFILES, DEFAULTS, haversineM, bearingDeg, turnAngleDeg, centroid, detectOrbit,
  polylineHorizontalM, windFactor, estimateMission, parseNameTokens, parseMissionXml, fmtTime, formatReport
};
if (typeof module !== 'undefined' && module.exports) module.exports = api;
if (typeof window !== 'undefined') window.MissionEstimate = api;
