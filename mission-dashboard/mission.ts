export type Point = { lat: number; lon: number };
export type Route = { name: string; parts: Point[][]; warnings: string[]; sample?: boolean };
export type Forecast = { key: string; target: Point; valid: string; fetched: string; altitude: number; lower: number; upper: number; speed: number; direction: number; gust: number | null; visibility: number | null; temperature: number | null; precipitation: number | null };
export type Check = { status: "pending" | "reviewed" | "restriction" | "na"; note: string; at: string };
export type Mission = {
  name: string; route: Route | null; drone: string; mode: string; speed: string; operation: string;
  altitude: string; time: string; lat: string; lon: string; target: string;
  weatherMode: string; wind: string; direction: string; gust: string; visibility: string; weatherNote: string;
  forecast: Forecast | null; checks: Record<string, Check>; notes: string;
};

export const drones: Record<string, { label: string; speeds: number[]; link?: string }> = {
  mini5: { label: "DJI Mini 5 Pro", speeds: [5, 10, 18.5], link: "https://dl.djicdn.com/downloads/DJI_Mini_5_Pro/UM/2025/DJI_Mini_5_Pro_User_Manual_en.pdf" },
  mini4: { label: "DJI Mini 4 Pro", speeds: [5, 10, 16], link: "https://www.dji.com/mini-4-pro/specs" },
  mini3: { label: "DJI Mini 3", speeds: [5, 10, 16], link: "https://www.dji.com/mini-3/specs" },
  mavic2: { label: "DJI Mavic 2 Pro", speeds: [3, 10, 20], link: "https://www.dji.com/mavic-2/info" },
  custom: { label: "Custom aircraft", speeds: [5, 10, 15] },
};
export const modes = ["Cine / Tripod", "Normal", "Sport"];
export const operations = ["Unspecified", "Microdrone (<250 g)", "Basic VLOS", "Advanced VLOS", "Advanced EVLOS", "Other / SFOC"];
export const heights = [10, 80, 120, 180];
const car = (section: string) => "https://laws-lois.justice.gc.ca/eng/regulations/SOR-96-433/section-" + section + ".html";
export const refs = {
  cars: "https://laws-lois.justice.gc.ca/eng/regulations/SOR-96-433/",
  nav: "https://www.navcanada.ca/en/flight-planning/drone-flight-planning.aspx",
  notam: "https://plan.navcanada.ca/wxrecall/",
  aip: "https://www.navcanada.ca/en/aeronautical-information/aip-canada.aspx",
  tc: "https://tc.canada.ca/en/aviation/drone-safety/learn-rules-you-fly-your-drone",
  advanced: "https://tc.canada.ca/en/aviation/drone-safety/learn-rules-you-fly-your-drone/drone-operation-categories-pilot-certificates/advanced-operations",
  event: "https://tc.canada.ca/en/aviation/drone-safety/drone-pilot-licensing/get-permission-special-drone-operations/flying-your-drone-advertised-event",
  weather: "https://open-meteo.com/en/docs",
};

export const checklist: { id: string; title: string; detail: string; links: [string, string][] }[] = [
  { id: "airspace", title: "Airspace and authorization", detail: "Check the full operational volume, including vertical limits, Class F and controlling agency conditions. Record required authorization or restrictions.", links: [["NAV Drone", refs.nav], ["AIP Canada", refs.aip], ["CAR 901.71", car("901.71")]] },
  { id: "notam", title: "NOTAMs and temporary restrictions", detail: "Review relevant FIR and aerodrome notices in CFPS. Check effective dates, schedules, lateral and vertical limits, and the full notice text.", links: [["CFPS", refs.notam], ["CAR 901.27", car("901.27")]] },
  { id: "aerodrome", title: "Aerodromes and local procedures", detail: "Check airport, heliport, other aerodrome and DND proximity. Review published procedures, traffic patterns and any separate permissions.", links: [["CAR 901.47", car("901.47")], ["CAR 901.73", car("901.73")], ["AIP Canada", refs.aip]] },
  { id: "survey", title: "Site survey and people", detail: "Review terrain, obstacles, launch and recovery, bystanders, separation, land access, park rules and advertised events.", links: [["CAR 901.24", car("901.24")], ["CAR 901.27", car("901.27")], ["TC advertised events", refs.event]] },
  { id: "crew", title: "Operation category, aircraft and crew", detail: "Verify configured takeoff weight, category, pilot and observer qualifications, aircraft registration and any applicable declaration. Check altitude and sightline requirements.", links: [["Transport Canada", refs.tc], ["Advanced / EVLOS", refs.advanced], ["CAR 901.25", car("901.25")]] },
  { id: "weather", title: "Weather and aircraft limits", detail: "Check current aviation weather and onsite conditions, including visibility, gusts, local terrain effects and aircraft limitations throughout the mission.", links: [["NAV CANADA flight planning", "https://www.navcanada.ca/en/flight-planning.aspx"], ["CAR 901.27", car("901.27")]] },
  { id: "procedures", title: "Normal and emergency procedures", detail: "Confirm aircraft condition, reserve and recovery, lost link and return-to-home settings, abort criteria, crew communications and emergency contacts.", links: [["CAR 901.23", car("901.23")], ["CAR 901.29", car("901.29")]] },
];

export function blankMission(): Mission {
  return { name: "", route: null, drone: "mini5", mode: "1", speed: "10", operation: "Unspecified",
    altitude: "100", time: "", lat: "", lon: "", target: "route", weatherMode: "manual", wind: "",
    direction: "", gust: "", visibility: "", weatherNote: "", forecast: null, checks: {}, notes: "" };
}
export function sampleMission(): Mission {
  return { ...blankMission(), name: "Durham Ridge · Training sample", wind: "10", direction: "310",
    gust: "16", visibility: "16", weatherNote: "Illustrative inputs only",
    route: { name: "durham-ridge-sample.kml", sample: true, warnings: [], parts: [[
      { lat: 44.0236, lon: -79.0747 }, { lat: 44.0258, lon: -79.0728 }, { lat: 44.0277, lon: -79.0683 },
      { lat: 44.0315, lon: -79.0637 }, { lat: 44.0322, lon: -79.0592 }, { lat: 44.0297, lon: -79.0570 },
      { lat: 44.0272, lon: -79.0594 }, { lat: 44.0264, lon: -79.0641 }, { lat: 44.0239, lon: -79.0687 },
    ]] } };
}

export function validPoint(point: Point) {
  return Number.isFinite(point.lat) && Math.abs(point.lat) <= 90 && Number.isFinite(point.lon) && Math.abs(point.lon) <= 180;
}
export function number(value: string) {
  return value.trim() ? Number(value) : NaN;
}
export function pilot(m: Mission) {
  const point = { lat: number(m.lat), lon: number(m.lon) };
  return validPoint(point) ? point : null;
}
const rad = (value: number) => value * Math.PI / 180;
const deg = (value: number) => value * 180 / Math.PI;
export const longitudeDelta = (from: number, to: number) => ((to - from + 540) % 360) - 180;
export function leg(a: Point, b: Point) {
  const lat1 = rad(a.lat), lat2 = rad(b.lat), dx = rad(longitudeDelta(a.lon, b.lon)), dy = lat2 - lat1;
  const h = Math.sin(dy / 2) ** 2 + Math.cos(lat1) * Math.cos(lat2) * Math.sin(dx / 2) ** 2;
  return {
    metres: 12742000 * Math.asin(Math.min(1, Math.sqrt(h))),
    bearing: Math.atan2(Math.sin(dx) * Math.cos(lat2), Math.cos(lat1) * Math.sin(lat2) - Math.sin(lat1) * Math.cos(lat2) * Math.cos(dx)),
    start: a, end: b,
  };
}
export function routeInfo(route: Route | null) {
  const legs = route?.parts.flatMap(part => part.slice(1).map((point, i) => leg(part[i], point))).filter(l => l.metres > 0) ?? [];
  const metres = legs.reduce((sum, l) => sum + l.metres, 0);
  let remaining = metres / 2;
  let centre: Point | null = null;
  for (const l of legs) {
    if (remaining <= l.metres) {
      const d = remaining / 6371000, lat = rad(l.start.lat), lon = rad(l.start.lon);
      const centreLat = Math.asin(Math.sin(lat) * Math.cos(d) + Math.cos(lat) * Math.sin(d) * Math.cos(l.bearing));
      const centreLon = lon + Math.atan2(Math.sin(l.bearing) * Math.sin(d) * Math.cos(lat), Math.cos(d) - Math.sin(lat) * Math.sin(centreLat));
      centre = { lat: deg(centreLat), lon: longitudeDelta(0, deg(centreLon)) };
      break;
    }
    remaining -= l.metres;
  }
  const points = route?.parts.reduce((count, part) => count + part.length, 0) ?? 0;
  return { legs, metres, centre, points };
}

export function parseKml(xml: string, name: string): Route {
  if (/<!DOCTYPE/i.test(xml)) throw new Error("KML document types are unsupported.");
  const document = new DOMParser().parseFromString(xml, "application/xml");
  if (document.getElementsByTagName("parsererror").length || document.documentElement.localName.toLowerCase() !== "kml")
    throw new Error("This file is not valid KML.");
  const elements = (root: Document | Element, local: string) => Array.from(root.getElementsByTagNameNS("*", local));
  const parts: Point[][] = [];
  const warnings: string[] = [];
  const read = (value: string, separator: RegExp) => {
    const tuple = value.trim().split(separator);
    const point = { lon: number(tuple[0] ?? ""), lat: number(tuple[1] ?? "") };
    if (tuple.length < 2 || !validPoint(point)) throw new Error("The KML contains an invalid route coordinate.");
    return point;
  };
  for (const geometry of Array.from(document.getElementsByTagName("*")).filter(node => ["LineString", "Track"].includes(node.localName))) {
    const tuples = geometry.localName === "Track"
      ? elements(geometry, "coord").map(node => node.textContent ?? "")
      : (elements(geometry, "coordinates")[0]?.textContent ?? "").trim().split(/\s+/).filter(Boolean);
    if (tuples.length < 2) throw new Error("Each LineString or Track needs at least two coordinates.");
    parts.push(tuples.map(value => read(value, geometry.localName === "Track" ? /\s+/ : /,/)));
  }
  if (!parts.length) throw new Error("No LineString or gx:Track route found. Point-only waypoint files and KMZ are unsupported.");
  if (parts.reduce((sum, part) => sum + part.length, 0) > 10000) throw new Error("Reduce the route to 10,000 points or fewer.");
  if (parts.length > 1) warnings.push("Separate KML tracks were measured independently. Transit between tracks is excluded.");
  if (elements(document, "NetworkLink").length || elements(document, "Polygon").length || elements(document, "Point").length)
    warnings.push("Only LineString and gx:Track geometry was used. KML points, polygons and network links are ignored.");
  const route = { name, parts, warnings };
  if (!routeInfo(route).metres) throw new Error("The KML route has no measurable distance.");
  return route;
}

export function mapUrl(point: Point) {
  return "https://www.google.com/maps/search/?api=1&query=" + encodeURIComponent(point.lat.toFixed(6) + "," + point.lon.toFixed(6));
}
export function coords(point: Point | null) {
  return point ? point.lat.toFixed(6) + ", " + point.lon.toFixed(6) : "Not set";
}
export const utc = (time: string) => time && Number.isFinite(Date.parse(time + "Z")) ? time + "Z" : "";
export const forecastKey = (m: Mission, point: Point | null) => JSON.stringify([m.target, coords(point), m.altitude, m.time]);
export const formatTime = (seconds: number | null) => seconds === null ? "—" : `${Math.floor(Math.round(seconds) / 60)}m ${String(Math.round(seconds) % 60).padStart(2, "0")}s`;

export function evaluate(m: Mission, now = Date.now()) {
  const route = routeInfo(m.route);
  const location = pilot(m);
  const target = m.target === "pilot" ? location : route.centre;
  const time = utc(m.time);
  const altitude = number(m.altitude);
  const key = forecastKey(m, target);
  const forecast = m.weatherMode === "forecast" && m.forecast?.key === key ? m.forecast : null;
  const warnings = [...(m.route?.warnings ?? [])];
  if (m.route?.sample) warnings.push("Training sample with illustrative inputs. Import your own route before operational use.");
  if (!route.metres) warnings.push("Import a KML route to calculate distance and transit time.");
  if (!location) warnings.push(m.lat || m.lon ? "Pilot coordinates are incomplete or invalid. Enter latitude −90 to 90 and longitude −180 to 180." : "Pilot location is unconfirmed. Enter verified coordinates separately from the route centre.");
  if (!time) warnings.push("Set the intended mission time in UTC.");
  else if (Date.parse(time) < now - 3600000) warnings.push("The mission time has passed. Recheck dates, weather and NOTAMs before reuse.");
  if (m.operation === "Unspecified") warnings.push("Confirm the operating category using the aircraft’s configured takeoff weight and intended operation.");
  if (!Number.isFinite(altitude) || altitude < 0) warnings.push("Enter a valid planned altitude in metres AGL.");
  if (altitude > 121.92) warnings.push("Planned altitude exceeds 400 ft AGL. Check the applicable CARs, exceptions and airspace limits.");
  if (m.operation === "Advanced EVLOS") warnings.push("Verify uncontrolled airspace, observer qualifications and positioning, separation, and all EVLOS conditions.");
  if (m.operation === "Other / SFOC") warnings.push("Verify the applicable operating authority and any SFOC conditions.");
  if (m.weatherMode === "forecast" && !forecast) warnings.push("Fetch a forecast for the selected reference, altitude and UTC time, or use manual weather.");
  if (forecast) {
    warnings.push("Model forecast is tentative. Gust and visibility values are near-surface. Verify against aviation weather and onsite conditions.");
    if (now - Date.parse(forecast.fetched) > 3 * 3600000) warnings.push("Forecast retrieval is over 3 hours old. Refresh and compare with current conditions.");
  }
  const wind = forecast ? forecast.speed : m.weatherMode === "manual" ? number(m.wind) : NaN;
  const from = forecast ? forecast.direction : number(m.direction);
  const gust = forecast ? forecast.gust : m.weatherMode === "manual" ? number(m.gust) : NaN;
  const visibility = forecast ? (forecast.visibility === null ? NaN : forecast.visibility / 1000) : m.weatherMode === "manual" ? number(m.visibility) : NaN;
  const air = number(m.speed);
  const hasSpeed = Number.isFinite(air) && air > 0;
  const hasWind = Number.isFinite(wind) && wind >= 0 && (wind === 0 || (Number.isFinite(from) && from >= 0 && from <= 360));
  if (m.mode === "2") warnings.push("Sport mode may disable obstacle avoidance. Verify the aircraft manual and operating limits.");
  if (hasWind && m.weatherMode === "manual" && !m.weatherNote.trim()) warnings.push("Record the source and observation time for manually entered weather.");
  if (!hasSpeed) warnings.push("Enter a positive planning speed in m/s.");
  if (!hasWind && m.weatherMode === "manual") warnings.push("Enter wind speed and true direction (0–360°), or enter 0 kt if calm.");
  if (m.gust && m.weatherMode === "manual" && (!Number.isFinite(gust) || Number(gust) < 0)) warnings.push("Enter non-negative gusts in knots.");
  if (m.visibility && m.weatherMode === "manual" && (!Number.isFinite(visibility) || visibility < 0)) warnings.push("Enter non-negative visibility in km.");
  if (gust !== null && Number.isFinite(gust) && hasWind && Number(gust) < wind && !forecast) warnings.push("Entered gust is below the sustained wind. Verify both inputs.");
  const calm = hasSpeed && route.metres > 0 ? route.metres / air : null;
  let adjusted: number | null = calm === null || !hasWind ? null : 0;
  let minGround: number | null = null;
  if (adjusted !== null) {
    const windMs = wind * 1852 / 3600;
    for (const l of route.legs) {
      const angle = rad(wind === 0 ? 0 : from) - l.bearing;
      const cross = windMs * Math.sin(angle);
      const along = -windMs * Math.cos(angle);
      const ground = Math.sqrt(Math.max(0, air ** 2 - cross ** 2)) + along;
      if (Math.abs(cross) > air || ground <= 0.01) {
        adjusted = null;
        minGround = null;
        warnings.push("The wind model cannot hold track or make positive progress on at least one leg. No adjusted time is available.");
        break;
      }
      adjusted += l.metres / ground;
      minGround = minGround === null ? ground : Math.min(minGround, ground);
    }
  }
  const completed = checklist.filter(item => {
    const check = m.checks[item.id];
    return (check?.status === "reviewed" || check?.status === "na") && check.note.trim();
  }).length;
  const flagged = checklist.filter(item => m.checks[item.id]?.status === "restriction").length;
  const lackingEvidence = checklist.some(item => m.checks[item.id]?.status !== undefined && m.checks[item.id].status !== "pending" && !m.checks[item.id].note.trim());
  if (lackingEvidence) warnings.push("Add a reference or note to each check marked reviewed, flagged or not applicable.");
  if (flagged) warnings.push(`${flagged} check${flagged === 1 ? " has" : "s have"} a flagged restriction. Review before proceeding.`);
  return { route, location, target, time, altitude, forecast, warnings, wind, from, gust, visibility, hasWind, calm, adjusted, minGround, completed, flagged };
}
