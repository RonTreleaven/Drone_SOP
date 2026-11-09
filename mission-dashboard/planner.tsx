import { fetchModelForecast } from "./forecast";
import { listMissions, readMission, saveRecord, removeRecord, type RecordRow } from "./storage";
import { useEffect, useRef, useState, type ChangeEvent, type ReactNode } from "react";
import { Activity, ArrowDownToLine, ArrowUpRight, Check, ChevronRight, CloudSun, Compass, Crosshair, FileText, FolderOpen, Gauge, MapPin, Plus, Route as RouteIcon, Save, ShieldAlert, SlidersHorizontal, TriangleAlert, Upload, Wind } from "lucide-react";
import { blankMission, checklist, coords, drones, evaluate, forecastKey, formatTime, longitudeDelta, mapUrl, modes, number, operations, parseKml, refs, sampleMission, type Check as CheckRecord, type Forecast, type Mission, type Point, type Route } from "./mission";

type Section = "overview" | "setup" | "weather" | "checks" | "report" | "records";
const navigation = [
  { id: "overview", title: "Overview", icon: Activity }, { id: "setup", title: "Route & aircraft", icon: RouteIcon },
  { id: "weather", title: "Weather", icon: CloudSun }, { id: "checks", title: "Airspace & checks", icon: ShieldAlert },
  { id: "report", title: "Evidence report", icon: FileText }, { id: "records", title: "Saved missions", icon: FolderOpen },
] as const;
const statuses = { pending: "Pending review", reviewed: "Reviewed", restriction: "Restriction flagged", na: "Not applicable" };
const show = (value: number | null, digits = 1) => value !== null && Number.isFinite(value) ? value.toFixed(digits) : "—";
const dateText = (value: string) => value ? new Date(value).toLocaleString("en-CA", { timeZone: "UTC", dateStyle: "medium", timeStyle: "short" }) + " UTC" : "Not set";
const nowInput = () => new Date().toISOString().slice(0, 16);

function External({ url, children }: { url: string; children: ReactNode }) {
  return <a href={url} target="_blank" rel="noopener noreferrer">{children}<ArrowUpRight size={13} aria-hidden="true" /></a>;
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return <label className="field"><span>{label}</span>{children}</label>;
}

function Diagram({ route, centre, pilot }: { route: Route | null; centre: Point | null; pilot: Point | null }) {
  const points = route?.parts.flat() ?? [];
  const anchor = points[0];
  const toPlane = (p: Point) => [longitudeDelta(anchor.lon, p.lon) * Math.max(.01, Math.cos((centre?.lat ?? anchor.lat) * Math.PI / 180)), -p.lat];
  const xs = points.map(p => toPlane(p)[0]), ys = points.map(p => toPlane(p)[1]);
  const loX = Math.min(...xs), hiX = Math.max(...xs), loY = Math.min(...ys), hiY = Math.max(...ys);
  const scale = Math.min(566 / Math.max(.00001, hiX - loX), 174 / Math.max(.00001, hiY - loY));
  const xy = (p: Point) => {
    const [x, y] = toPlane(p);
    return [376 + (x - (loX + hiX) / 2) * scale, 139 + (y - (loY + hiY) / 2) * scale];
  };
  const start = anchor ? xy(anchor) : null, end = anchor ? xy(points[points.length - 1]) : null;
  const middle = centre && anchor ? xy(centre) : null;
  const pl = pilot && anchor ? xy(pilot) : null;
  return <div className="diagram">
    <svg viewBox="0 0 752 278" role="img" aria-label="North-up schematic of the imported route, without terrain or airspace overlays">
      <defs>
        <pattern id="small-grid" width="25" height="25" patternUnits="userSpaceOnUse"><path d="M25 0H0V25" fill="none" stroke="#294050" strokeWidth=".6" /></pattern>
        <pattern id="grid" width="100" height="100" patternUnits="userSpaceOnUse"><rect width="100" height="100" fill="url(#small-grid)" /><path d="M100 0H0V100" fill="none" stroke="#34505f" strokeWidth="1" /></pattern>
        <radialGradient id="panel-glow"><stop stopColor="#193c3c" /><stop offset="1" stopColor="#122630" /></radialGradient>
      </defs>
      <rect width="752" height="278" fill="url(#panel-glow)" />
      <rect width="752" height="278" fill="url(#grid)" opacity=".84" />
      <path d="M376 0V278M0 139H752" stroke="#587277" strokeWidth=".7" strokeDasharray="4 7" opacity=".5" />
      {route?.parts.map((part, i) => {
        const path = part.map(p => xy(p).join(",")).join(" ");
        return <g key={i}><polyline points={path} fill="none" stroke="#69eed5" strokeWidth="10" strokeLinecap="round" strokeLinejoin="round" opacity=".17" /><polyline points={path} fill="none" stroke="#78f4d8" strokeWidth="3.1" strokeLinecap="round" strokeLinejoin="round" /></g>;
      })}
      {start && <g><circle cx={start[0]} cy={start[1]} r="7" fill="#81f5d9" stroke="#10262c" strokeWidth="2" /><text x={start[0] - 11} y={start[1] + 21} textAnchor="end" className="plot-label">START</text></g>}
      {end && <g><circle cx={end[0]} cy={end[1]} r="6" fill="#132e35" stroke="#81f5d9" strokeWidth="2" /><text x={end[0] + 11} y={end[1] + 21} className="plot-label">END</text></g>}
      {middle && <g><circle cx={middle[0]} cy={middle[1]} r="9" fill="#172a32" stroke="#ffcc7d" strokeWidth="1.3" strokeDasharray="2 2" /><circle cx={middle[0]} cy={middle[1]} r="3.4" fill="#ffcc7d" /></g>}
      {pl && pl[0] > 20 && pl[0] < 732 && pl[1] > 20 && pl[1] < 258 && <g><circle cx={pl[0]} cy={pl[1]} r="7" fill="#b4c9ff" stroke="#10262c" strokeWidth="2" /><text x={pl[0] + 10} y={pl[1] - 11} className="plot-label">PILOT</text></g>}
      {!anchor && <g><circle cx="376" cy="127" r="19" fill="none" stroke="#81f5d9" strokeDasharray="3 4" /><path d="M376 116v22m-11-11h22" stroke="#81f5d9" /><text x="376" y="172" textAnchor="middle" className="plot-label">IMPORT A KML TO PLOT YOUR ROUTE</text></g>}
      <g transform="translate(713,42)"><text y="-12" textAnchor="middle" className="plot-label">N</text><path d="M0-4 7 14 0 10-7 14Z" fill="#9bb8ba" /></g>
    </svg>
    <span className="diagram-tag"><Crosshair size={13} /> ROUTE SCHEMATIC</span>
  </div>;
}

function evidence(m: Mission, evaluated: ReturnType<typeof evaluate>) {
  const e = evaluated;
  const start = m.route?.parts[0]?.[0];
  const lastPart = m.route?.parts.at(-1);
  const end = lastPart?.at(-1);
  const location = (p: Point | null | undefined) => p ? coords(p) + "  " + mapUrl(p) : "Not set";
  const lines = [
    "DRONE_SOP  /  PRE-FLIGHT EVIDENCE", m.name.trim() || "Untitled mission",
    "Generated " + new Date().toISOString(),
    "Planning evidence only. Restrictions and authorization require independent verification.",
    "", "MISSION & ROUTE",
    "Mission time " + (e.time || "Not set") + "  |  Category " + m.operation,
    "Aircraft " + drones[m.drone].label + "  |  " + modes[Number(m.mode)] + "  |  Planning speed " + show(number(m.speed)) + " m/s",
    "Planned altitude " + show(e.altitude, 0) + " m AGL",
    "KML " + (m.route?.name ?? "Not imported") + "  |  " + e.route.points + " points",
    "Start " + location(start), "End " + location(end), "Route centre " + location(e.route.centre), "Pilot " + location(e.location),
    "Horizontal distance " + (e.route.metres ? show(e.route.metres / 1000, 2) + " km / " + show(e.route.metres / 1852, 2) + " NM" : "—"),
    "Tentative transit  Calm " + formatTime(e.calm) + "  |  Wind-adjusted " + formatTime(e.adjusted),
    "Transit excludes climb, descent, manoeuvring, hover, unplotted return and reserve.",
    "", "WEATHER",
    "Reference " + (m.target === "route" ? "Route centre" : "Pilot location") + "  |  " + location(e.target),
    "Source " + (e.forecast ? "Open-Meteo model (tentative)" : m.weatherMode === "manual" ? "Pilot-entered (verify)" : "Forecast pending"),
    ...(e.forecast ? [`Valid ${e.forecast.valid}  |  Retrieved ${e.forecast.fetched}`, `Wind height ${e.forecast.altitude} m AGL; model layers ${e.forecast.lower}/${e.forecast.upper} m`] : []),
    "Wind " + (e.hasWind ? show(e.wind) + " kt" + (e.wind ? " from " + show(e.from, 0) + "° true" : " calm") : "—") + "  |  Gust " + show(e.gust) + " kt  |  Visibility " + show(e.visibility) + " km",
    ...(m.weatherMode === "manual" && m.weatherNote ? ["Pilot weather source/notes " + m.weatherNote] : []),
    "", "RESTRICTIONS & VALIDATION", ...(e.warnings.length ? e.warnings.map(w => "• " + w) : ["No input warnings. Complete independent operational checks."]),
    "", "CHECKS  /  " + e.completed + " of " + checklist.length + " documented  /  " + e.flagged + " flagged",
    ...checklist.flatMap(item => {
      const check = m.checks[item.id];
      return [item.title + " — " + statuses[check?.status ?? "pending"] + (check?.at ? " · " + check.at : ""), ...(check?.note ? ["  " + check.note] : []), ...item.links.map(([label, url]) => "  " + label + " " + url)];
    }),
    ...(m.notes ? ["", "MISSION NOTES", m.notes] : []),
  ];
  return lines.join("\n");
}

export default function MissionPlanner() {
  const [mission, setMission] = useState<Mission>(sampleMission);
  const [section, setSection] = useState<Section>("overview");
  const [saved, setSaved] = useState<RecordRow[]>([]);
  const [recordId, setRecordId] = useState<string | null>(null);
  const [recordUpdated, setRecordUpdated] = useState<string | null>(null);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const [recordsError, setRecordsError] = useState("");
  const [pending, setPending] = useState("");
  const [dirty, setDirty] = useState(false);
  const [drag, setDrag] = useState(false);
  const [remove, setRemove] = useState<string | null>(null);
  const input = useRef<HTMLInputElement>(null);
  const active = useRef<HTMLDivElement>(null);
  const recordRequest = useRef(0);
  const loadToken = useRef(0);
  const revision = useRef(0);
  const currentForecastKey = useRef("");
  const e = evaluate(mission);
  const hasRoute = e.route.metres > 0;
  useEffect(() => { currentForecastKey.current = forecastKey(mission, e.target); }, [mission, e.target]);
  const sample = mission.route?.sample;
  const aircraft = drones[mission.drone];
  const shortWind = e.hasWind ? show(e.wind) : "—";
  const report = section === "report" ? evidence(mission, e) : "";

  async function refreshRecords() {
    const token = ++recordRequest.current;
    try {
      const records = listMissions();
      if (token === recordRequest.current) {
        setSaved(records);
        setRecordsError("");
      }
    } catch (err) {
      if (token === recordRequest.current) setRecordsError((err as Error).message);
    }
  }

  useEffect(() => { void refreshRecords(); }, []);
  useEffect(() => {
    if (!dirty) return;
    function warn(event: BeforeUnloadEvent) { event.preventDefault(); }
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [dirty]);

  function go(id: Section) {
    setSection(id);
    setError("");
    setNotice("");
    if (id === "records") void refreshRecords();
    requestAnimationFrame(() => { active.current?.focus({ preventScroll: true }); window.scrollTo({ top: 0 }); });
  }
  function edit(patch: Partial<Mission>, recheck = true) {
    setMission(m => ({ ...m, ...patch, ...(recheck ? { checks: Object.fromEntries(Object.entries(m.checks).map(([key, check]) => [
      key, check.status === "restriction" ? check : { ...check, status: "pending", at: "" },
    ])) } : {}) }));
    ++revision.current;
    setDirty(true);
  }
  function setCheck(id: string, patch: Partial<CheckRecord>) {
    setMission(m => {
      const old = m.checks[id] ?? { status: "pending", note: "", at: "" };
      const check = { ...old, ...patch };
      check.at = check.status === "pending" ? "" : new Date().toISOString();
      return { ...m, checks: { ...m.checks, [id]: check } };
    });
    ++revision.current;
    setDirty(true);
  }
  function replaceDraft(next: Mission, id: string | null, updated: string | null = null) {
    ++loadToken.current;
    setMission(next); setRecordId(id); setRecordUpdated(updated); setDirty(false); setPending(""); setError(""); setNotice("");
  }
  function startNew() {
    if (dirty && !window.confirm("Discard unsaved edits and start a new mission?")) return;
    replaceDraft({ ...blankMission(), time: nowInput() }, null);
    go("setup");
  }
  async function importFile(file?: File) {
    if (!file) return;
    setError(""); setNotice("");
    if (!file.name.toLowerCase().endsWith(".kml") || file.size > 5 * 1024 * 1024) {
      setError("Choose a .kml file up to 5 MB. KMZ is unsupported."); return;
    }
    const token = ++loadToken.current;
    setPending("import");
    try {
      const route = parseKml(await file.text(), file.name);
      if (token !== loadToken.current) return;
      if (sample) {
        setMission({ ...blankMission(), route, time: nowInput(), name: file.name.replace(/\.kml$/i, "").slice(0, 100) });
        setRecordId(null); setRecordUpdated(null); ++revision.current; setDirty(true);
      } else {
        edit({ route, forecast: null, ...(mission.name ? {} : { name: file.name.replace(/\.kml$/i, "").slice(0, 100) }) });
      }
      setNotice("Route imported. Verify coordinates and update mission inputs.");
    } catch (err) { if (token === loadToken.current) setError((err as Error).message); }
    finally { if (token === loadToken.current) setPending(""); }
  }
  function onFile(event: ChangeEvent<HTMLInputElement>) {
    void importFile(event.target.files?.[0]);
    event.target.value = "";
  }
  async function fetchForecast() {
    if (!e.target || !e.time || !Number.isFinite(e.altitude) || e.altitude < 10 || e.altitude > 180) {
      setError("Select a valid reference point, UTC time and altitude of 10–180 m AGL."); return;
    }
    const key = forecastKey(mission, e.target), token = loadToken.current;
    const params = new URLSearchParams({ lat: String(e.target.lat), lon: String(e.target.lon), alt: String(e.altitude), time: e.time });
    setPending("forecast"); setError(""); setNotice("");
    try {
      const forecast: Forecast = { ...await fetchModelForecast(params), key };
      if (token !== loadToken.current) return;
      if (key !== currentForecastKey.current) {
        setError("Forecast inputs changed. Fetch again for the selected coordinates, time and altitude."); return;
      }
      edit({ forecast });
      setNotice("Tentative model forecast retrieved. Check the valid hour and reference point.");
    } catch (err) { if (token === loadToken.current) setError((err as Error).message); }
    finally { if (token === loadToken.current) setPending(""); }
  }
  async function saveMission() {
    if (sample) { setError("Start a new mission or import your own route before saving."); return; }
    if (!mission.name.trim()) { go("setup"); setError("Enter a mission name before saving."); return; }
    const id = recordId ?? crypto.randomUUID();
    const sentRevision = revision.current;
    setPending("save"); setError(""); setNotice("");
    try {
      const record = await saveRecord(id, recordUpdated, { ...mission, name: mission.name.trim() });
      setRecordId(record.id); setRecordUpdated(record.updated);
      const current = revision.current === sentRevision;
      if (current) setDirty(false);
      setNotice(current ? "Mission saved in this browser." : "Earlier edits saved. This draft has additional unsaved changes.");
      void refreshRecords();
    } catch (err) { setError((err as Error).message); }
    finally { setPending(""); }
  }
  async function openRecord(id: string) {
    if (dirty && !window.confirm("Discard unsaved edits and open the saved mission?")) return;
    setPending("open"); setError("");
    try {
      const data = readMission(id);
      replaceDraft({ ...blankMission(), ...data.mission }, id, data.updated);
      go("overview"); setNotice("Saved mission opened. Recheck time-sensitive evidence before reuse.");
    } catch (err) { setError((err as Error).message); }
    finally { setPending(""); }
  }
  async function deleteRecord(id: string) {
    setPending("delete"); setError("");
    try {
      await removeRecord(id);
      if (id === recordId) { setRecordId(null); setRecordUpdated(null); setDirty(true); }
      setRemove(null); setNotice("Saved record deleted."); void refreshRecords();
    } catch (err) { setError((err as Error).message); }
    finally { setPending(""); }
  }
  function download() {
    const url = URL.createObjectURL(new Blob([evidence(mission, e)], { type: "text/plain;charset=utf-8" }));
    const a = document.createElement("a");
    a.href = url;
    a.download = (mission.name.trim().replace(/[^\w-]+/g, "-").replace(/^-|-$/g, "") || "Drone-SOP") + "-preflight.txt";
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 500);
  }
  async function copy() {
    try { await navigator.clipboard.writeText(evidence(mission, e)); setNotice("Evidence report copied."); }
    catch { setError("Clipboard access is unavailable. Download the report instead."); }
  }
  const maps = [
    ["Route start", mission.route?.parts[0]?.[0]], ["Route end", mission.route?.parts.at(-1)?.at(-1)],
    ["Route centre", e.route.centre], ["Pilot location", e.location],
  ] as const;
  const coordList = <div className="coordinates">{maps.map(([label, point]) => <div className="coord" key={label}>
    <div><span>{label}</span><strong>{coords(point ?? null)}</strong></div>
    {point && <External url={mapUrl(point)}>Google Maps</External>}
  </div>)}</div>;
  const warningList = e.warnings.length ? <ul className="warning-list">{e.warnings.map(w => <li key={w}><TriangleAlert size={15} />{w}</li>)}</ul> : <p className="helper">No input warnings. Verify the operational checks for this mission.</p>;
  const steps = [
    { id: "setup", number: "01", name: "Route & aircraft", detail: hasRoute ? `${e.route.points} points · ${aircraft.label}` : "Import route and set aircraft", ready: hasRoute },
    { id: "weather", number: "02", name: "Weather", detail: e.forecast ? "Model forecast · tentative" : e.hasWind ? "Pilot-entered inputs" : "Weather inputs required", ready: e.hasWind },
    { id: "checks", number: "03", name: "Airspace & checks", detail: `${e.completed}/${checklist.length} documented` + (e.flagged ? ` · ${e.flagged} flagged` : ""), ready: e.completed === checklist.length },
    { id: "report", number: "04", name: "Evidence report", detail: "Review, copy or download", ready: false },
  ] as const;

  return <div className="shell">
    <aside className="rail">
      <div className="brand"><span className="brand-icon"><Crosshair size={25} /></span><div><strong>Drone<span>_</span>SOP</strong><small>RPAS FIELD TOOLS</small></div></div>
      <div className="rail-inner">
        <div className="rail-label">WORKSPACE</div>
        <nav aria-label="Mission planner">{navigation.map(({ id, title, icon: Icon }) => <button key={id} className={section === id ? "nav-item selected" : "nav-item"} aria-current={section === id ? "page" : undefined} onClick={() => go(id)}><Icon size={18} /><span>{title}</span>{section === id && <span className="nav-dot" />}</button>)}</nav>
        <div className="rail-label resource-label">OFFICIAL SOURCES</div>
        <div className="rail-links"><External url={refs.cars}>CARs Part IX</External><External url={refs.nav}>NAV CANADA</External></div>
      </div>
      <div className="rail-bottom"><span className="country">CA</span><div><strong>Canadian RPAS</strong><small>Planning workspace</small></div></div>
    </aside>
    <main>
      <header className="topbar">
        <div className="breadcrumb"><a href="../tools.html">Drone_SOP Tools</a><ChevronRight size={14} /><strong>{navigation.find(n => n.id === section)?.title}</strong></div>
        <div className="top-actions"><button className="button outline" onClick={startNew} disabled={!!pending}><Plus size={16} /> New mission</button><button className="button solid" onClick={() => void saveMission()} disabled={!!pending}><Save size={16} />{pending === "save" ? "Saving…" : "Save mission"}</button></div>
      </header>
      <div className="workspace" ref={active} tabIndex={-1}>
        <input ref={input} type="file" accept=".kml,application/vnd.google-earth.kml+xml" hidden onChange={onFile} />
        {error && <div className="feedback error" role="alert"><TriangleAlert size={17} />{error}</div>}
        {notice && <div className="feedback notice" role="status"><Check size={17} />{notice}</div>}
        {section === "overview" && <>
          <div className="heading"><div><div className="eyebrow"><span /> FLIGHT OPERATIONS</div><h1>Mission planner</h1><p>Plan your route, assess conditions, and document your pre-flight checks.</p></div><span className="chip status-chip"><span />{sample ? "Training sample" : dirty ? "Unsaved draft" : recordId ? "Saved mission" : "Draft mission"}</span></div>
          <div className="banner"><span className="banner-icon"><ShieldAlert size={21} /></span><div><strong>Planning only · Flight status unverified</strong><p>Check airspace, NOTAMs and local restrictions before flight. Estimates and checklist entries do not grant authorization.</p></div><button onClick={() => go("checks")}>Review checks <ChevronRight size={16} /></button></div>
          <div className="metrics">
            <Metric icon={<RouteIcon />} title="ROUTE DISTANCE" value={hasRoute ? show(e.route.metres / 1000, 2) : "—"} unit="km" detail={hasRoute ? show(e.route.metres / 1852, 2) + " NM · horizontal track" : "Import KML to measure"} />
            <Metric icon={<Gauge />} title="EST. TRANSIT" value={formatTime(e.adjusted ?? e.calm)} detail={e.adjusted !== null ? "Wind-adjusted · tentative" : e.calm !== null ? "Calm baseline · tentative" : "Awaiting route and speed"} />
            <Metric icon={<Wind />} title="WIND AT ALTITUDE" value={shortWind} unit="kt" detail={(e.hasWind && e.wind ? show(e.from, 0) + "° true · " : "") + (Number.isFinite(e.altitude) ? e.altitude + " m AGL" : "Set planned height")} />
            <Metric icon={<ShieldAlert />} title="CHECKS DOCUMENTED" value={String(e.completed)} unit={"/ " + checklist.length} detail={e.flagged ? `${e.flagged} restriction${e.flagged === 1 ? "" : "s"} flagged` : "Pilot review required"} />
          </div>
          <div className="overview-grid">
            <section className="card route-card">
              <div className="card-heading"><div><div className="eyebrow">ROUTE OVERVIEW</div><h2>{mission.name || "Untitled mission"}</h2></div><button className="button outline compact" disabled={!!pending} onClick={() => input.current?.click()}><Upload size={16} /> Import KML</button></div>
              <Diagram route={mission.route} centre={e.route.centre} pilot={e.location} />
              <div className="plot-footer"><span><i className="track-key" /> Imported track</span><span><i className="centre-key" /> Route centre</span><span><i className="pilot-key" /> Pilot</span><span className="plot-count">{hasRoute ? `${e.route.points} points · ${mission.route?.parts.length} track(s)` : "No route loaded"}</span></div>
              {coordList}
            </section>
            <div className="right-stack">
              <section className="card workflow"><div className="card-heading"><div><div className="eyebrow">FLIGHT PREP</div><h2>Mission workflow</h2></div><SlidersHorizontal size={19} /></div>
              {steps.map(step => <button key={step.id} className="step" onClick={() => go(step.id)}><span className={step.ready ? "step-number done" : "step-number"}>{step.number}</span><span><strong>{step.name}</strong><small>{step.detail}</small></span><ChevronRight size={16} /></button>)}
              </section>
              <section className="card validations"><div className="card-heading"><div><div className="eyebrow">REVIEW BEFORE FLIGHT</div><h2>Validation warnings</h2></div><span className="chip warning-count">{e.warnings.length}</span></div>{warningList}</section>
            </div>
          </div>
        </>}
        {section === "setup" && <>
          <Heading label="STEP 01 / MISSION SETUP" title="Route & aircraft" detail="Import the planned track and confirm aircraft, operating category, height and pilot position." />
          <div className="detail-grid">
            <section className="card detail-card"><PanelHeader icon={<RouteIcon />} title="Mission and route" />
              <Field label="Mission name"><input maxLength={100} value={mission.name} onChange={ev => edit({ name: ev.target.value }, false)} /></Field>
              <button className={drag ? "drop active" : "drop"} disabled={!!pending} onClick={() => input.current?.click()}
                onDragOver={ev => { ev.preventDefault(); if (!pending) setDrag(true); }} onDragLeave={() => setDrag(false)}
                onDrop={ev => { ev.preventDefault(); setDrag(false); if (!pending) void importFile(ev.dataTransfer.files[0]); }}>
                <Upload size={25} /><strong>{mission.route?.name ?? "Choose a KML file or drop it here"}</strong>
                <small>{mission.route ? "Choose or drop a KML to replace this route" : "KML LineString or gx:Track · up to 5 MB"}</small>
              </button>
              <div className="field-row">
                <Field label="Mission time (UTC)"><input type="datetime-local" value={mission.time} onChange={ev => edit({ time: ev.target.value })} /></Field>
                <Field label="Planned altitude (m AGL)"><input type="number" min="0" step="any" value={mission.altitude} onChange={ev => edit({ altitude: ev.target.value })} /></Field>
              </div>
              <button className="text-button" onClick={() => edit({ time: nowInput() })}>Use current UTC time</button>
              <p className="helper">The route measures horizontal distance. Set height independently of any KML altitude or controller takeoff-relative height.</p>
            </section>
            <section className="card detail-card"><PanelHeader icon={<Gauge />} title="Aircraft and operation" />
              <Field label="Aircraft"><select value={mission.drone} onChange={ev => edit({ drone: ev.target.value, speed: String(drones[ev.target.value].speeds[Number(mission.mode)]) })}>{Object.entries(drones).map(([id, d]) => <option key={id} value={id}>{d.label}</option>)}</select></Field>
              <div className="field-row">
                <Field label="Flight mode"><select value={mission.mode} onChange={ev => edit({ mode: ev.target.value, speed: String(aircraft.speeds[Number(ev.target.value)]) })}>{modes.map((mode, i) => <option key={mode} value={i}>{mode}</option>)}</select></Field>
                <Field label="Planning speed (m/s)"><input type="number" min="0.1" step="any" value={mission.speed} onChange={ev => edit({ speed: ev.target.value })} /></Field>
              </div>
              <p className="helper">Editable planning presets. Use a sustainable speed for your aircraft and controller settings. {aircraft.link && <External url={aircraft.link}>DJI reference</External>}</p>
              <Field label="Intended operating category"><select value={mission.operation} onChange={ev => edit({ operation: ev.target.value })}>{operations.map(op => <option key={op}>{op}</option>)}</select></Field>
            </section>
            <section className="card detail-card"><PanelHeader icon={<MapPin />} title="Pilot location" />
              <div className="field-row">
                <Field label="Pilot latitude (decimal °)"><input type="number" min="-90" max="90" step="any" placeholder="44.000000" value={mission.lat} onChange={ev => edit({ lat: ev.target.value })} /></Field>
                <Field label="Pilot longitude (decimal °)"><input type="number" min="-180" max="180" step="any" placeholder="-79.000000" value={mission.lon} onChange={ev => edit({ lon: ev.target.value })} /></Field>
              </div>
              <p className="helper">Enter your actual planned pilot position. The along-route midpoint is a separate forecast reference.</p>
              {coordList}
            </section>
            <section className="card detail-card"><PanelHeader icon={<FileText />} title="Mission notes" />
              <Field label="Purpose, crew or operating limits"><textarea rows={5} maxLength={4000} value={mission.notes} onChange={ev => edit({ notes: ev.target.value }, false)} placeholder="Add launch and recovery details, abort criteria, or references." /></Field>
              <button className="button solid" onClick={() => go("weather")}>Continue to weather <ChevronRight size={16} /></button>
            </section>
          </div>
        </>}
        {section === "weather" && <>
          <Heading label="STEP 02 / CONDITIONS" title="Weather & flight estimate" detail="Use a forecast or enter wind at the planned altitude. Verify conditions over the whole route." />
          <div className="detail-grid">
            <section className="card detail-card"><PanelHeader icon={<CloudSun />} title="Weather inputs" />
              <div className="segmented" aria-label="Weather source">{[["manual", "Manual entry"], ["forecast", "Model forecast"]].map(([value, label]) => <button key={value} aria-pressed={mission.weatherMode === value} onClick={() => edit({ weatherMode: value })}>{label}</button>)}</div>
              <div className="field-row">
                <Field label="Weather reference"><select value={mission.target} onChange={ev => edit({ target: ev.target.value })}><option value="route">Route centre</option><option value="pilot">Pilot location</option></select></Field>
                <Field label="Planned altitude (m AGL)"><input type="number" min="0" step="any" value={mission.altitude} onChange={ev => edit({ altitude: ev.target.value })} /></Field>
              </div>
              <p className="helper coordinate-hint">{coords(e.target)} {e.target && <External url={mapUrl(e.target)}>Verify in Google Maps</External>}</p>
              {mission.weatherMode === "manual" ? <>
                <div className="field-row">
                  <Field label="Wind at height (kt)"><input type="number" min="0" step="any" value={mission.wind} onChange={ev => edit({ wind: ev.target.value })} /></Field>
                  <Field label="Wind from (° true)"><input type="number" min="0" max="360" step="any" value={mission.direction} onChange={ev => edit({ direction: ev.target.value })} /></Field>
                  <Field label="Gusts (kt)"><input type="number" min="0" step="any" value={mission.gust} onChange={ev => edit({ gust: ev.target.value })} /></Field>
                  <Field label="Visibility (km)"><input type="number" min="0" step="any" value={mission.visibility} onChange={ev => edit({ visibility: ev.target.value })} /></Field>
                </div>
                <Field label="Source, observation time and notes"><input maxLength={400} value={mission.weatherNote} onChange={ev => edit({ weatherNote: ev.target.value })} placeholder="e.g. observation location, source and time" /></Field>
              </> : <>
                <Field label="Mission time (UTC)"><input type="datetime-local" value={mission.time} onChange={ev => edit({ time: ev.target.value })} /></Field>
                <div className="inline-actions"><button className="button solid" disabled={!!pending} onClick={() => void fetchForecast()}><CloudSun size={16} />{pending === "forecast" ? "Fetching…" : "Fetch forecast"}</button><button className="text-button" onClick={() => edit({ time: nowInput() })}>Use current UTC time</button></div>
                <p className="helper">The request sends the selected coordinates to Open-Meteo. Wind uses 10, 80, 120 and 180 m AGL model layers with vector interpolation between layers. Forecast time uses the nearest hour. <External url={refs.weather}>Open-Meteo</External></p>
                {e.forecast && <div className="forecast-summary"><strong>Tentative model forecast</strong><span>Valid {dateText(e.forecast.valid)} · Retrieved {dateText(e.forecast.fetched)}</span><span>Wind {show(e.forecast.speed)} kt from {show(e.forecast.direction, 0)}° true · {e.forecast.lower === e.forecast.upper ? e.forecast.lower + " m model layer" : e.forecast.lower + "–" + e.forecast.upper + " m model layers"}</span><span>10 m gust {show(e.forecast.gust)} kt · Surface visibility {show(e.visibility)} km · {show(e.forecast.temperature)} °C · {show(e.forecast.precipitation)} mm precipitation</span></div>}
              </>}
            </section>
            <div className="right-stack">
              <section className="card detail-card"><PanelHeader icon={<Gauge />} title="Transit estimates" />
                <dl className="results">
                  <div><dt>Distance</dt><dd>{hasRoute ? show(e.route.metres / 1000, 2) + " km / " + show(e.route.metres / 1852, 2) + " NM" : "—"}</dd></div>
                  <div><dt>Calm baseline</dt><dd>{formatTime(e.calm)}</dd></div>
                  <div><dt>Wind-adjusted</dt><dd>{formatTime(e.adjusted)}</dd></div>
                  <div><dt>Slowest leg</dt><dd>{e.minGround === null ? "—" : show(e.minGround) + " m/s ground speed"}</dd></div>
                </dl>
                <p className="helper">Tentative horizontal transit assumes constant airspeed and wind per flight. Add time for climb, descent, turns, hover, unplotted return and battery reserve.</p>
              </section>
              <section className="card detail-card"><PanelHeader icon={<TriangleAlert />} title="Validation warnings" />{warningList}</section>
            </div>
          </div>
        </>}
        {section === "checks" && <>
          <Heading label="STEP 03 / VERIFICATION" title="Airspace & operational checks" detail="Use the official sources for your full operating area and time. Record what you checked and flag any restriction." />
          <div className="banner checks-banner"><span className="banner-icon"><ShieldAlert size={21} /></span><div><strong>{e.completed} of {checklist.length} checks documented · {e.flagged} restrictions flagged</strong><p>Entries are pilot records. Changes to planning inputs reopen reviewed checks and retain flagged restrictions.</p></div></div>
          <div className="check-grid">{checklist.map((item, i) => {
            const record = mission.checks[item.id];
            return <section className="card detail-card check-card" key={item.id}>
              <div className="check-title"><span className="step-number">{String(i + 1).padStart(2, "0")}</span><h2>{item.title}</h2></div>
              <p className="helper">{item.detail}</p>
              <div className="source-links">{item.links.map(([label, url]) => <External key={label} url={url}>{label}</External>)}</div>
              <div className="field-row">
                <Field label={item.title + " status"}><select value={record?.status ?? "pending"} onChange={ev => setCheck(item.id, { status: ev.target.value as CheckRecord["status"] })}>{Object.entries(statuses).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></Field>
                <Field label="Evidence or reason"><input maxLength={600} value={record?.note ?? ""} onChange={ev => setCheck(item.id, { note: ev.target.value })} placeholder="Reference, limitation or reason" /></Field>
              </div>
              {record?.at && <small className="helper">Recorded {dateText(record.at)}</small>}
            </section>;
          })}</div>
        </>}
        {section === "report" && <>
          <Heading label="STEP 04 / OUTPUT" title="Pre-flight evidence report" detail="Capture the route, weather assumptions, validation warnings and your review records in one text report." />
          <section className="card detail-card report-card"><div className="card-heading"><PanelHeader icon={<FileText />} title={mission.name || "Untitled mission"} /><div className="inline-actions"><button className="button outline" onClick={() => void copy()}>Copy report</button><button className="button solid" onClick={download}><ArrowDownToLine size={16} /> Download .txt</button></div></div>
            <pre className="report">{report}</pre>
          </section>
        </>}
        {section === "records" && <>
          <Heading label="MISSION ARCHIVE" title="Saved missions" detail="Records stay in this browser. Recheck time-sensitive evidence before reopening a saved mission." />
          <section className="card detail-card"><PanelHeader icon={<FolderOpen />} title="Mission records" />
            {recordsError && <div className="feedback error"><TriangleAlert size={17} />{recordsError}<button className="text-button" onClick={() => void refreshRecords()}>Retry</button></div>}
            {!saved.length && !recordsError && <div className="empty"><FolderOpen size={31} /><h3>No saved missions yet</h3><p>Use Save mission to keep a record on this device. Download the evidence report for a portable copy.</p><button className="button outline" onClick={startNew} disabled={!!pending}><Plus size={16} /> New mission</button></div>}
            {saved.map(record => <div className="record" key={record.id}>
              <div><strong>{record.name}</strong><small>Updated {dateText(record.updated)}</small></div>
              <div className="inline-actions">{remove === record.id ? <><button className="button outline compact" disabled={!!pending} onClick={() => setRemove(null)}>Cancel</button><button className="button danger compact" disabled={!!pending} onClick={() => void deleteRecord(record.id)}>Confirm delete</button></> : <><button className="button outline compact" disabled={!!pending} onClick={() => void openRecord(record.id)}>Open</button><button className="text-button" disabled={!!pending} onClick={() => setRemove(record.id)}>Delete</button></>}</div>
            </div>)}
          </section>
        </>}
        <footer className="footer"><span><Compass size={15} /> DRONE_SOP · CANADIAN RPAS MISSION PLANNER</span><span>Verify conditions and applicable restrictions before flight.</span></footer>
      </div>
    </main>
  </div>;
}

function PanelHeader({ icon, title }: { icon: ReactNode; title: string }) {
  return <div className="panel-heading"><span>{icon}</span><h2>{title}</h2></div>;
}
function Heading({ label, title, detail }: { label: string; title: string; detail: string }) {
  return <div className="heading"><div><div className="eyebrow"><span /> {label}</div><h1>{title}</h1><p>{detail}</p></div></div>;
}
function Metric({ icon, title, value, unit, detail }: { icon: ReactNode; title: string; value: string; unit?: string; detail: string }) {
  return <div className="metric card"><div className="metric-top"><span className="metric-icon">{icon}</span><span>{title}</span></div><div className="metric-value">{value} {unit && <small>{unit}</small>}</div><div className="metric-detail">{detail}</div></div>;
}
