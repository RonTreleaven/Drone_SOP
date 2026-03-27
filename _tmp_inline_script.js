
    const API_BASE = "https://plan.navcanada.ca/weather/api/alpha/";
    const DIRECT_TIMEOUT_MS = 5000;
    const PROXY_TIMEOUT_MS = 14000;
    const PROXY_PROVIDERS = [
      {
        name: "cloudflare",
        label: "Cloudflare Worker",
        buildUrl: targetUrl => `https://navcan-proxy.rontreleaven.workers.dev/?url=${encodeURIComponent(targetUrl)}`
      },
      {
        name: "corsproxy",
        label: "CorsProxy",
        buildUrl: targetUrl => `https://corsproxy.io/?${encodeURIComponent(targetUrl)}`
      }
    ];
    const CACHE_TTL_MS = 5 * 60 * 1000;
    const LIVE_FETCH_COOLDOWN_MS = 30 * 60 * 1000;
    const FRESH_BANNER_WINDOW_MS = 60 * 60 * 1000;
    const LAST_FIR_STORAGE_KEY = "fetchnotams:lastFir";
    const LAST_ICAO_STORAGE_KEY = "fetchnotams:lastIcao";
    const VIEW_MODE_KEY = "fetchnotams:viewMode";
    const MOBILE_PANE_MODE_KEY = "fetchnotams:mobilePaneMode";
    const MAP_PAYLOAD_STORAGE_PREFIX = "fetchnotams:map:payload:";
    const MAP_LIVE_UNFILTERED_STORAGE_KEY = "fetchnotams:map:live:latest";
    const MAP_PAYLOAD_TTL_MS = 2 * 60 * 60 * 1000;
    const FIR_CODES = ["CZVR", "CZEG", "CZWG", "CZYZ", "CZUL", "CZQM", "CZQX"];
    const FIR_CODE_SET = new Set(FIR_CODES);
    const DISPLAY_TIME_ZONE = "America/Toronto";

    const el = {
      form: document.getElementById("fetchForm"),
      fetchNotamsBtn: document.getElementById("fetchNotamsBtn"),
      firInput: document.getElementById("firInput"),
      icaoInput: document.getElementById("icaoInput"),
      notamInput: document.getElementById("notamInput"),
      icaoList: document.getElementById("icaoList"),
      currentFirValue: document.getElementById("currentFirValue"),
      currentIcaoValue: document.getElementById("currentIcaoValue"),
      clearEntriesBtn: document.getElementById("clearEntriesBtn"),
      airportsFoundInline: document.getElementById("airportsFoundInline"),
      notamsInScopeInline: document.getElementById("notamsInScopeInline"),
      maxItems: document.getElementById("maxItems"),
      toggleQFilterBtn: document.getElementById("toggleQFilterBtn"),
      qSetAllExcludeBtn: document.getElementById("qSetAllExcludeBtn"),
      qSetAllIncludeBtn: document.getElementById("qSetAllIncludeBtn"),
      sortByPriorityBtn: document.getElementById("sortByPriorityBtn"),
      qResetDefaultsBtn: document.getElementById("qResetDefaultsBtn"),
      qFilterSummary: document.getElementById("qFilterSummary"),
      openQLegend:
        document.getElementById("openQLegend") ||
        document.getElementById("openQCodeLegend") ||
        document.getElementById("openQCodeLegendBtn") ||
        document.querySelector(".q-help-btn"),
      qLegendModal: document.getElementById("qLegendModal"),
      closeQLegend: document.getElementById("closeQLegend"),
      popoutQLegend: document.getElementById("popoutQLegend"),
      qLegendSearch: document.getElementById("qLegendSearch"),
      qLegendConditionSearch: document.getElementById("qLegendConditionSearch"),
      qLegendClearSearch: document.getElementById("qLegendClearSearch"),
      qLegendShowAll: document.getElementById("qLegendShowAll"),
      qLegendInfo: document.getElementById("qLegendInfo"),
      qLegendBody: document.getElementById("qLegendBody"),
      qLegendPopoutStatus: document.getElementById("qLegendPopoutStatus"),
      lastFetchBanner: document.getElementById("lastFetchBanner"),
      loadingState: document.getElementById("loadingState"),
      loadingText: document.querySelector("#loadingState .loading-text"),
      sourceValue: document.getElementById("sourceValue"),
      fetchTimeValue: document.getElementById("fetchTimeValue"),
      totalValue: document.getElementById("totalValue"),
      shownValue: document.getElementById("shownValue"),
      updatedValue: document.getElementById("updatedValue"),
      unknownQCodesValue: document.getElementById("unknownQCodesValue"),
      resultsHeaderText: document.getElementById("resultsHeaderText"),
      resultsList: document.getElementById("resultsList"),
      viewAllOnMapBtn: document.getElementById("viewAllOnMapBtn"),
      refreshFromCacheBtn: document.getElementById("refreshFromCacheBtn")
      ,
      viewToggleBtn: document.getElementById("viewToggleBtn"),
      mobilePaneToggle: document.getElementById("mobilePaneToggle")
    };

    function getAutoViewMode() {
      return window.matchMedia("(max-width: 900px)").matches ? "mobile" : "desktop";
    }

    function detectDeviceType() {
      const ua = navigator.userAgent || "";
      const touchPoints = navigator.maxTouchPoints || 0;
      const coarsePointer = window.matchMedia("(pointer: coarse)").matches;
      const viewportWidth = Math.min(window.innerWidth || 0, window.screen.width || Number.MAX_SAFE_INTEGER);

      const isiPadOS = /Macintosh/i.test(ua) && touchPoints > 1;
      const isTabletUA = /iPad|Tablet|PlayBook|Silk|(Android(?!.*Mobile))/i.test(ua);
      const isPhoneUA = /iPhone|iPod|Android.*Mobile|Windows Phone|Mobile/i.test(ua);

      if (isiPadOS || isTabletUA || (coarsePointer && viewportWidth >= 768 && viewportWidth <= 1100)) {
        return "tablet";
      }

      if (isPhoneUA || (coarsePointer && viewportWidth < 768)) {
        return "phone";
      }

      return "desktop";
    }

    function applyDeviceType(type) {
      document.body.classList.remove("device-phone", "device-tablet", "device-desktop");
      document.body.classList.add(`device-${type}`);
      document.body.dataset.deviceType = type;
    }

    function initDeviceType() {
      const update = () => applyDeviceType(detectDeviceType());
      update();
      window.addEventListener("resize", update);
      window.addEventListener("orientationchange", update);
    }

    function applyViewMode(mode) {
      const isMobile = mode === "mobile";
      document.body.classList.toggle("view-mobile", isMobile);
      document.body.classList.toggle("view-desktop", !isMobile);
      if (!el.viewToggleBtn) return;
      el.viewToggleBtn.setAttribute("aria-pressed", isMobile ? "true" : "false");
      el.viewToggleBtn.title = isMobile ? "Switch to desktop view" : "Switch to mobile view";
      const label = el.viewToggleBtn.querySelector(".toggle-label");
      if (label) label.textContent = isMobile ? "Mobile" : "Desktop";
      syncMobilePaneMode();
    }

    function applyMobilePaneMode(mode) {
      const detailMode = mode === "details";
      const canApply = document.body.classList.contains("view-mobile");
      document.body.classList.toggle("mobile-detail-focus", canApply && detailMode);
      if (!el.mobilePaneToggle) return;
      el.mobilePaneToggle.setAttribute("aria-pressed", detailMode ? "true" : "false");
      el.mobilePaneToggle.title = detailMode ? "Switch to input view" : "Switch to detail view";
      const label = el.mobilePaneToggle.querySelector(".toggle-label");
      if (label) label.textContent = detailMode ? "Inputs" : "Detail";
      scheduleMobileDockUpdate();
    }

    function syncMobilePaneMode() {
      const isMobileView = document.body.classList.contains("view-mobile");
      if (!el.mobilePaneToggle) return;
      el.mobilePaneToggle.hidden = !isMobileView;
      if (!isMobileView) {
        document.body.classList.remove("mobile-detail-focus");
        el.mobilePaneToggle.classList.remove("dock-left", "hidden-for-input");
        return;
      }
      const storedMode = localStorage.getItem(MOBILE_PANE_MODE_KEY);
      const mode = storedMode === "details" ? "details" : "inputs";
      applyMobilePaneMode(mode);
      scheduleMobileDockUpdate();
    }

    function rectsIntersect(a, b, pad = 8) {
      if (!a || !b) return false;
      const ax1 = a.left - pad;
      const ay1 = a.top - pad;
      const ax2 = a.right + pad;
      const ay2 = a.bottom + pad;
      return !(ax2 < b.left || ax1 > b.right || ay2 < b.top || ay1 > b.bottom);
    }

    function scheduleMobileDockUpdate() {
      if (mobileDockRafId) {
        cancelAnimationFrame(mobileDockRafId);
      }
      mobileDockRafId = requestAnimationFrame(() => {
        mobileDockRafId = 0;
        updateMobilePaneDockPosition();
      });
    }

    function updateMobilePaneDockPosition() {
      const toggle = el.mobilePaneToggle;
      if (!toggle) return;

      const isMobileView = document.body.classList.contains("view-mobile");
      if (!isMobileView || toggle.hidden) {
        toggle.classList.remove("dock-left");
        return;
      }

      toggle.classList.remove("dock-left");
      const toggleRect = toggle.getBoundingClientRect();
      const targetNodes = [
        el.viewAllOnMapBtn,
        document.querySelector("#qFilterSection .section-head-actions"),
        document.querySelector(".results-header-actions")
      ];

      const shouldDockLeft = targetNodes.some(node => {
        if (!(node instanceof Element)) return false;
        const style = window.getComputedStyle(node);
        if (style.display === "none" || style.visibility === "hidden") return false;
        const rect = node.getBoundingClientRect();
        if (rect.width < 1 || rect.height < 1) return false;
        return rectsIntersect(toggleRect, rect, 10);
      });

      toggle.classList.toggle("dock-left", shouldDockLeft);
    }

    function initViewMode() {
      const stored = localStorage.getItem(VIEW_MODE_KEY);
      if (stored === "mobile" || stored === "desktop") {
        applyViewMode(stored);
      } else {
        applyViewMode(getAutoViewMode());
      }

      window.addEventListener("resize", () => {
        const pref = localStorage.getItem(VIEW_MODE_KEY);
        if (pref === "mobile" || pref === "desktop") return;
        applyViewMode(getAutoViewMode());
      });

      if (el.viewToggleBtn) {
        el.viewToggleBtn.addEventListener("click", () => {
          const isMobile = document.body.classList.contains("view-mobile");
          const next = isMobile ? "desktop" : "mobile";
          localStorage.setItem(VIEW_MODE_KEY, next);
          applyViewMode(next);
        });
      }

      if (el.mobilePaneToggle) {
        el.mobilePaneToggle.addEventListener("click", () => {
          const inDetail = document.body.classList.contains("mobile-detail-focus");
          const nextMode = inDetail ? "inputs" : "details";
          localStorage.setItem(MOBILE_PANE_MODE_KEY, nextMode);
          applyMobilePaneMode(nextMode);
        });
      }

      window.addEventListener("scroll", scheduleMobileDockUpdate, { passive: true });
      window.addEventListener("resize", scheduleMobileDockUpdate);

      document.addEventListener("focusin", event => {
        if (!el.mobilePaneToggle) return;
        if (!document.body.classList.contains("view-mobile")) return;
        const target = event.target;
        if (!(target instanceof Element)) return;
        if (!target.closest("input, select, textarea")) return;
        el.mobilePaneToggle.classList.add("hidden-for-input");
      });

      document.addEventListener("focusout", () => {
        if (!el.mobilePaneToggle) return;
        el.mobilePaneToggle.classList.remove("hidden-for-input");
        scheduleMobileDockUpdate();
      });
    }

    let currentItems = [];
    let currentDataSite = "";
    let currentFilteredItems = [];
    let pendingMapPayloadInfo = null;
    let qLegendPopupWindow = null;
    let qLegendOpenedAtMs = 0;
    let qLegendLastLaunchAtMs = 0;
    let lastSelectedIcao = normalizeCode(localStorage.getItem(LAST_ICAO_STORAGE_KEY) || "", 4);
    let hasAutoFocusedIcao = false;
    let lastFetchActionSite = "";
    let mobileDockRafId = 0;

    const TRACKED_Q_CATEGORIES = ["A", "C", "F", "G", "I", "L", "M", "N", "O", "P", "R", "S", "W", "X"];
    let Q_SUBJECT_CODES = [
      // Airspace organization (A)
      { code: "AA", meaning: "Minimum altitude (specify en route/crossing/safe)" },
      { code: "AC", meaning: "Class B/C/D/E surface area" },
      { code: "AD", meaning: "Air defense identification zone" },
      { code: "AE", meaning: "Control area" },
      { code: "AF", meaning: "Flight information region" },
      { code: "AH", meaning: "Upper control area" },
      { code: "AL", meaning: "Minimum usable flight level" },
      { code: "AN", meaning: "Area navigation route" },
      { code: "AO", meaning: "Oceanic control area" },
      { code: "AP", meaning: "Reporting point (specify)" },
      { code: "AR", meaning: "ATS route (specify)" },
      { code: "AT", meaning: "Terminal control area" },
      { code: "AU", meaning: "Upper flight information region" },
      { code: "AV", meaning: "Upper advisory area" },
      { code: "AX", meaning: "Significant point" },
      { code: "AZ", meaning: "Aerodrome traffic zone" },
      // Communications and surveillance (C)
      { code: "CA", meaning: "Air/ground facility (specify service/frequency)" },
      { code: "CB", meaning: "ADS-B (specify)" },
      { code: "CC", meaning: "ADS-C (specify)" },
      { code: "CD", meaning: "CPDLC (specify)" },
      { code: "CE", meaning: "En-route surveillance radar" },
      { code: "CG", meaning: "Ground controlled approach system" },
      { code: "CL", meaning: "SELCAL" },
      { code: "CM", meaning: "Surface movement radar" },
      { code: "CP", meaning: "Precision approach radar (specify runway)" },
      { code: "CR", meaning: "Surveillance radar element of PAR (specify wavelength)" },
      { code: "CS", meaning: "Secondary surveillance radar" },
      { code: "CT", meaning: "Terminal area surveillance radar" },
      // Facilities and services (F)
      { code: "FA", meaning: "Aerodrome" },
      { code: "FB", meaning: "Friction measuring device (specify type)" },
      { code: "FC", meaning: "Ceiling measurement equipment" },
      { code: "FD", meaning: "Docking system (AGNIS, BOLDS, etc.)" },
      { code: "FE", meaning: "Oxygen (specify type)" },
      { code: "FF", meaning: "Fire fighting and rescue" },
      { code: "FG", meaning: "Ground movement control" },
      { code: "FH", meaning: "Helicopter alighting area/platform" },
      { code: "FI", meaning: "Aircraft de-icing (specify)" },
      { code: "FJ", meaning: "Oils (specify type)" },
      { code: "FL", meaning: "Landing direction indicator" },
      { code: "FM", meaning: "Meteorological service (specify type)" },
      { code: "FO", meaning: "Fog dispersal system" },
      { code: "FP", meaning: "Heliport" },
      { code: "FS", meaning: "Snow removal equipment" },
      { code: "FT", meaning: "Transmissometer (specify runway)" },
      { code: "FU", meaning: "Fuel availability" },
      { code: "FW", meaning: "Wind direction indicator" },
      { code: "FZ", meaning: "Customs/immigration" },
      // GNSS services (G)
      { code: "GA", meaning: "GNSS airfield-specific operations (specify)" },
      { code: "GW", meaning: "GNSS area-wide operations (specify)" },
      // Instrument and microwave landing systems (I)
      { code: "IC", meaning: "Instrument landing system (specify runway)" },
      { code: "ID", meaning: "DME associated with ILS" },
      { code: "IG", meaning: "Glide path (ILS) (specify runway)" },
      { code: "II", meaning: "Inner marker (ILS) (specify runway)" },
      { code: "IL", meaning: "Localizer (ILS) (specify runway)" },
      { code: "IM", meaning: "Middle marker (ILS) (specify runway)" },
      { code: "IN", meaning: "Localizer (not associated with ILS)" },
      { code: "IO", meaning: "Outer marker (ILS) (specify runway)" },
      { code: "IS", meaning: "ILS Category I (specify runway)" },
      { code: "IT", meaning: "ILS Category II (specify runway)" },
      { code: "IU", meaning: "ILS Category III (specify runway)" },
      { code: "IW", meaning: "Microwave landing system (specify runway)" },
      { code: "IX", meaning: "Locator, outer (ILS) (specify runway)" },
      { code: "IY", meaning: "Locator, middle (ILS) (specify runway)" },
      // Lighting facilities (L)
      { code: "LA", meaning: "Approach lighting system (specify runway/type)" },
      { code: "LB", meaning: "Aerodrome beacon" },
      { code: "LC", meaning: "Runway centre line lights (specify runway)" },
      { code: "LD", meaning: "Landing direction indicator lights" },
      { code: "LE", meaning: "Runway edge lights (specify runway)" },
      { code: "LF", meaning: "Sequenced flashing lights (specify runway)" },
      { code: "LG", meaning: "Pilot-controlled lighting" },
      { code: "LH", meaning: "High intensity runway lights (specify runway)" },
      { code: "LI", meaning: "Runway end identifier lights (specify runway)" },
      { code: "LJ", meaning: "Runway alignment indicator lights (specify runway)" },
      { code: "LK", meaning: "Category II components of approach lighting (specify runway)" },
      { code: "LL", meaning: "Low intensity runway lights (specify runway)" },
      { code: "LM", meaning: "Medium intensity runway lights (specify runway)" },
      { code: "LP", meaning: "Precision approach path indicator (specify runway)" },
      { code: "LR", meaning: "All landing area lighting facilities" },
      { code: "LS", meaning: "Stopway lights (specify runway)" },
      { code: "LT", meaning: "Threshold lights (specify runway)" },
      { code: "LU", meaning: "Helicopter approach path indicator" },
      { code: "LV", meaning: "Visual approach slope indicator system (specify type/runway)" },
      { code: "LW", meaning: "Heliport lighting" },
      { code: "LX", meaning: "Taxiway centre line lights (specify taxiway)" },
      { code: "LY", meaning: "Taxiway edge lights (specify taxiway)" },
      { code: "LZ", meaning: "Runway touchdown zone lights (specify runway)" },
      // Movement and landing area (M)
      { code: "MA", meaning: "Movement area" },
      { code: "MB", meaning: "Bearing strength (specify part of landing/movement area)" },
      { code: "MC", meaning: "Clearway (specify runway)" },
      { code: "MD", meaning: "Declared distances (specify runway)" },
      { code: "MG", meaning: "Taxiing guidance system" },
      { code: "MH", meaning: "Runway arresting gear (specify runway)" },
      { code: "MK", meaning: "Parking area" },
      { code: "MM", meaning: "Daylight markings (specify threshold/centre line/etc.)" },
      { code: "MN", meaning: "Apron" },
      { code: "MO", meaning: "Stopbar (specify runway)" },
      { code: "MP", meaning: "Aircraft stands (specify)" },
      { code: "MR", meaning: "Runway (specify runway)" },
      { code: "MS", meaning: "Stopway (specify runway)" },
      { code: "MT", meaning: "Threshold (specify runway)" },
      { code: "MU", meaning: "Runway turning bay (specify runway)" },
      { code: "MW", meaning: "Strip/shoulder (specify runway)" },
      { code: "MX", meaning: "Taxiway(s) (specify)" },
      { code: "MY", meaning: "Rapid exit taxiway (specify)" },
      // Terminal and en route navigation facilities (N)
      { code: "NA", meaning: "All radio navigation facilities (except...)" },
      { code: "NB", meaning: "Nondirectional radio beacon" },
      { code: "NC", meaning: "DECCA" },
      { code: "ND", meaning: "Distance measuring equipment" },
      { code: "NF", meaning: "Fan marker" },
      { code: "NL", meaning: "Locator (specify identification)" },
      { code: "NM", meaning: "VOR/DME" },
      { code: "NN", meaning: "TACAN" },
      { code: "NO", meaning: "OMEGA" },
      { code: "NT", meaning: "VORTAC" },
      { code: "NV", meaning: "VOR" },
      // Other information (O)
      { code: "OA", meaning: "Aeronautical information service" },
      { code: "OB", meaning: "Obstacle (specify details)" },
      { code: "OE", meaning: "Aircraft entry requirements" },
      { code: "OL", meaning: "Obstacle lights (specify)" },
      { code: "OR", meaning: "Rescue coordination centre" },
      // Air traffic procedures (P)
      { code: "PA", meaning: "Standard instrument arrival (specify route designator)" },
      { code: "PB", meaning: "Standard VFR arrival" },
      { code: "PC", meaning: "Contingency procedures" },
      { code: "PD", meaning: "Standard instrument departure (specify route designator)" },
      { code: "PE", meaning: "Standard VFR departure" },
      { code: "PF", meaning: "Flow control procedure" },
      { code: "PH", meaning: "Holding procedure" },
      { code: "PI", meaning: "Instrument approach procedure (specify type/runway)" },
      { code: "PK", meaning: "VFR approach procedure" },
      { code: "PL", meaning: "Flight plan processing" },
      { code: "PM", meaning: "Aerodrome operating minima (specify)" },
      { code: "PN", meaning: "Noise operating restriction" },
      { code: "PO", meaning: "Obstacle clearance altitude/height (specify procedure)" },
      { code: "PR", meaning: "Radio failure procedure" },
      { code: "PT", meaning: "Transition altitude/level (specify)" },
      { code: "PU", meaning: "Missed approach procedure (specify runway)" },
      { code: "PX", meaning: "Minimum holding altitude (specify fix)" },
      { code: "PZ", meaning: "ADIZ procedure" },
      // Navigation warnings: airspace restrictions (R)
      { code: "RA", meaning: "Airspace reservation (specify)" },
      { code: "RD", meaning: "Danger area (specify)" },
      { code: "RM", meaning: "Military operating area" },
      { code: "RO", meaning: "Overflying restriction (specify)" },
      { code: "RP", meaning: "Prohibited area (specify)" },
      { code: "RR", meaning: "Restricted area (specify)" },
      { code: "RT", meaning: "Temporary restricted area (specify area)" },
      // Air traffic and VOLMET services (S)
      { code: "SA", meaning: "Automatic terminal information service" },
      { code: "SB", meaning: "ATS reporting office" },
      { code: "SC", meaning: "Area control centre" },
      { code: "SE", meaning: "Flight information service" },
      { code: "SF", meaning: "Aerodrome flight information service" },
      { code: "SL", meaning: "Flow control centre" },
      { code: "SO", meaning: "Oceanic area control centre" },
      { code: "SP", meaning: "Approach control service" },
      { code: "SS", meaning: "Flight service station" },
      { code: "ST", meaning: "Aerodrome control tower" },
      { code: "SU", meaning: "Upper area control centre" },
      { code: "SV", meaning: "VOLMET broadcast" },
      { code: "SY", meaning: "Upper advisory service (specify)" },
      // Navigation warnings: warnings (W)
      { code: "WA", meaning: "Air display" },
      { code: "WB", meaning: "Aerobatics" },
      { code: "WC", meaning: "Captive balloon or kite" },
      { code: "WD", meaning: "Demolition of explosives" },
      { code: "WE", meaning: "Exercises (specify)" },
      { code: "WF", meaning: "Air refueling" },
      { code: "WG", meaning: "Glider flying" },
      { code: "WH", meaning: "Blasting" },
      { code: "WJ", meaning: "Banner/target towing" },
      { code: "WL", meaning: "Ascent of free balloon" },
      { code: "WM", meaning: "Missile, gun or rocket firing" },
      { code: "WP", meaning: "Parachute/paragliding/hang gliding" },
      { code: "WR", meaning: "Radioactive materials or toxic chemicals" },
      { code: "WS", meaning: "Burning or blowing gas" },
      { code: "WT", meaning: "Mass movement of aircraft" },
      { code: "WU", meaning: "Unmanned aircraft" },
      { code: "WV", meaning: "Formation flight" },
      { code: "WW", meaning: "Significant volcanic activity" },
      { code: "WY", meaning: "Aerial survey" },
      { code: "WZ", meaning: "Model flying" },
      // Other / unspecified
      { code: "XX", meaning: "Other / unspecified" }
    ];
    let Q_CONDITION_CODES = [
      // Availability (A)
      { code: "AC", meaning: "Withdrawn for maintenance" },
      { code: "AD", meaning: "Available for daylight operation" },
      { code: "AF", meaning: "Flight checked and found reliable" },
      { code: "AG", meaning: "Operating but ground checked only (awaiting flight check)" },
      { code: "AH", meaning: "Hours of service are now (specify)" },
      { code: "AK", meaning: "Resumed normal operations" },
      { code: "AL", meaning: "Operative subject to previous limitations/conditions" },
      { code: "AM", meaning: "Military operations only" },
      { code: "AN", meaning: "Available for night operation" },
      { code: "AO", meaning: "Operational" },
      { code: "AP", meaning: "Available, prior permission required" },
      { code: "AR", meaning: "Available on request" },
      { code: "AS", meaning: "Unserviceable" },
      { code: "AU", meaning: "Not available (specify reason if needed)" },
      { code: "AW", meaning: "Completely withdrawn" },
      { code: "AX", meaning: "Previously promulgated shutdown canceled" },
      // Changes (C)
      { code: "CA", meaning: "Activated" },
      { code: "CC", meaning: "Completed" },
      { code: "CD", meaning: "Deactivated" },
      { code: "CE", meaning: "Erected" },
      { code: "CF", meaning: "Operating frequency changed to" },
      { code: "CG", meaning: "Downgraded to" },
      { code: "CH", meaning: "Changed" },
      { code: "CI", meaning: "Identification/call sign changed to" },
      { code: "CL", meaning: "Realigned" },
      { code: "CM", meaning: "Displaced" },
      { code: "CN", meaning: "Canceled" },
      { code: "CO", meaning: "Operating" },
      { code: "CP", meaning: "Operating on reduced power" },
      { code: "CR", meaning: "Temporarily replaced by" },
      { code: "CS", meaning: "Installed" },
      { code: "CT", meaning: "On test, do not use" },
      // Hazard conditions (H)
      { code: "HA", meaning: "Braking action (poor/medium/good)" },
      { code: "HB", meaning: "Friction coefficient is ..." },
      { code: "HC", meaning: "Covered by compacted snow to depth of" },
      { code: "HD", meaning: "Covered by dry snow to a depth of" },
      { code: "HE", meaning: "Covered by water to a depth of" },
      { code: "HF", meaning: "Totally free of snow and ice" },
      { code: "HG", meaning: "Grass cutting in progress" },
      { code: "HH", meaning: "Hazard due to (specify)" },
      { code: "HI", meaning: "Covered by ice" },
      { code: "HJ", meaning: "Launch planned (balloon/space)" },
      { code: "HK", meaning: "Bird migration in progress" },
      { code: "HL", meaning: "Snow clearance completed" },
      { code: "HM", meaning: "Marked by (specify)" },
      { code: "HN", meaning: "Covered by wet snow or slush" },
      { code: "HO", meaning: "Obscured by snow" },
      { code: "HP", meaning: "Snow clearance in progress" },
      { code: "HQ", meaning: "Operation canceled (balloon/space)" },
      { code: "HR", meaning: "Standing water" },
      { code: "HS", meaning: "Sanding in progress" },
      { code: "HT", meaning: "Approach according to signal area only" },
      { code: "HU", meaning: "Launch in progress (balloon/space)" },
      { code: "HV", meaning: "Work completed" },
      { code: "HW", meaning: "Work in progress" },
      { code: "HX", meaning: "Concentration of birds" },
      { code: "HY", meaning: "Snow banks exist (specify height)" },
      { code: "HZ", meaning: "Covered by frozen ruts and ridges" },
      // Limitations (L)
      { code: "LA", meaning: "Operating on auxiliary power supply" },
      { code: "LB", meaning: "Reserved for aircraft based therein" },
      { code: "LC", meaning: "Closed" },
      { code: "LD", meaning: "Unsafe" },
      { code: "LE", meaning: "Operating without auxiliary power supply" },
      { code: "LF", meaning: "Interference from" },
      { code: "LG", meaning: "Operating without identification" },
      { code: "LH", meaning: "Unserviceable for aircraft heavier than" },
      { code: "LI", meaning: "Closed to IFR operations" },
      { code: "LK", meaning: "Operating as a fixed light" },
      { code: "LL", meaning: "Usable for length/width of..." },
      { code: "LN", meaning: "Closed to all night operations" },
      { code: "LP", meaning: "Prohibited to" },
      { code: "LR", meaning: "Aircraft restricted to runways/taxiways" },
      { code: "LS", meaning: "Subject to interruption" },
      { code: "LT", meaning: "Limited to" },
      { code: "LV", meaning: "Closed to VFR operations" },
      { code: "LW", meaning: "Will take place" },
      { code: "LX", meaning: "Operating but caution advised due to" },
      // Other / unspecified
      { code: "TT", meaning: "Trigger (AIP/AIRAC notification)" },
      { code: "XX", meaning: "Other / unspecified" }
    ];
    const Q_TRAFFIC_CODES = [
      { code: "I", meaning: "IFR" },
      { code: "V", meaning: "VFR" },
      { code: "IV", meaning: "IFR + VFR" }
    ];
    const Q_SCOPE_CODES = [
      { code: "A", meaning: "Aerodrome" },
      { code: "E", meaning: "Enroute" },
      { code: "W", meaning: "Warnings" },
      { code: "AE", meaning: "Aerodrome + Enroute" },
      { code: "AW", meaning: "Aerodrome + Warnings" },
      { code: "EW", meaning: "Enroute + Warnings" },
      { code: "AEW", meaning: "Aerodrome + Enroute + Warnings" }
    ];
    let Q_SUBJECT_CODE_MAP = new Map(Q_SUBJECT_CODES.map(entry => [entry.code, entry.meaning]));
    let Q_CONDITION_CODE_MAP = new Map(Q_CONDITION_CODES.map(entry => [entry.code, entry.meaning]));
    const Q_LEGEND_DATA_SOURCES = {
      subjects: "data/Subjects.json",
      conditions: "data/Conditions.json"
    };
    const qLegendController = window.QCodeLegend
      ? window.QCodeLegend.createController({
          subjectCodes: Q_SUBJECT_CODES,
          conditionCodes: Q_CONDITION_CODES,
          trafficCodes: Q_TRAFFIC_CODES,
          scopeCodes: Q_SCOPE_CODES,
          dataSources: Q_LEGEND_DATA_SOURCES
        })
      : null;
    const Q_PRIORITY_BY_CATEGORY = {
      O: 90,
      W: 85,
      R: 82,
      A: 55,
      S: 52,
      N: 48,
      C: 45,
      P: 38,
      G: 36,
      I: 28,
      F: 16,
      L: 12,
      M: 12,
      X: 10,
      K: 10
    };
    const Q_PRIORITY_BY_CONDITION = {
      CL: 22,
      CA: 20,
      CN: 18,
      AS: 18,
      AU: 16,
      CH: 12,
      CT: 10,
      CR: 10,
      HW: 10,
      LW: 8,
      TT: 6,
      XX: 0
    };
    const Q_PRIORITY_OVERRIDES = [
      { subject: "OB", score: 95, label: "Critical", reason: "Obstacle" },
      { subject: "OL", score: 92, label: "High", reason: "Obstacle lighting" },
      { subject: "WU", score: 92, label: "High", reason: "Unmanned aircraft activity" },
      { subject: "WP", score: 88, label: "High", reason: "Parachute/paragliding" },
      { subject: "WH", score: 88, label: "High", reason: "Blasting" },
      { subject: "WM", score: 88, label: "High", reason: "Firing activity" },
      { subject: "WA", score: 86, label: "High", reason: "Air display" },
      { subject: "WB", score: 86, label: "High", reason: "Aerobatics" },
      { subject: "WC", score: 86, label: "High", reason: "Captive balloon/kite" },
      { subject: "WR", score: 86, label: "High", reason: "Radioactive/toxic materials" },
      { subject: "RT", score: 90, label: "High", reason: "Temporary restricted area" },
      { subject: "RR", score: 90, label: "High", reason: "Restricted area" },
      { subject: "RP", score: 90, label: "High", reason: "Prohibited area" },
      { subject: "RD", score: 86, label: "High", reason: "Danger area" },
      { subject: "RA", score: 84, label: "High", reason: "Airspace reservation" }
    ];

    function goBack(event) {
      event.preventDefault();
      if (window.history.length > 1) {
        window.history.back();
        return;
      }
      window.location.href = "tools.html";
    }

    function normalizeCode(value, maxLen) {
      return String(value || "")
        .trim()
        .toUpperCase()
        .replace(/[^A-Z0-9]/g, "")
        .slice(0, maxLen);
    }

    function persistLastIcao(code) {
      const normalized = normalizeCode(code, 4);
      lastSelectedIcao = normalized;
      if (!normalized) {
        return;
      }
      localStorage.setItem(LAST_ICAO_STORAGE_KEY, normalized);
    }

    function persistLastFir(code) {
      const normalized = normalizeCode(code, 4);
      if (!normalized) return;
      localStorage.setItem(LAST_FIR_STORAGE_KEY, normalized);
    }

    function updateSelectionSummary() {
      const selectedFir = normalizeCode(el.firInput.value, 4);
      const selectedIcao = normalizeCode(el.icaoInput.value, 4);
      el.currentFirValue.textContent = selectedFir || "-";
      el.currentIcaoValue.textContent = selectedIcao || "-";
      updateFirReferenceCounts();
    }

    function updateFirReferenceCounts() {
      const selectedFir = normalizeCode(el.firInput?.value, 4);
      const hasCurrentSiteData = !!currentDataSite && Array.isArray(currentItems);

      FIR_CODES.forEach(firCode => {
        const row = document.querySelector(`[data-fir-row="${firCode}"]`);
        const countCell = document.querySelector(`[data-fir-count="${firCode}"]`);
        const sourceEl = document.querySelector(`[data-fir-source="${firCode}"]`);
        if (!row || !countCell || !sourceEl) return;

        let count = 0;
        let sourceText = "None";
        let sourceClass = "none";

        if (hasCurrentSiteData && currentDataSite === firCode) {
          count = currentItems.length;
          sourceText = "Current";
          sourceClass = "current";
        } else {
          const cache = loadCache(firCode);
          const cacheItems = Array.isArray(cache?.items) ? cache.items : [];
          if (cacheItems.length > 0) {
            count = cacheItems.length;
            sourceText = "Cached";
            sourceClass = "cached";
          }
        }

        countCell.textContent = String(count);
        sourceEl.textContent = sourceText;
        sourceEl.classList.remove("current", "cached", "none");
        sourceEl.classList.add(sourceClass);
        row.classList.toggle("active", !!selectedFir && selectedFir === firCode);
      });
    }

    function setupFirReferenceTable() {
      document.querySelectorAll("[data-fir-row]").forEach(row => {
        row.addEventListener("click", () => {
          const firCode = normalizeCode(row.getAttribute("data-fir-row") || "", 4);
          if (!firCode || !el.firInput) return;
          el.firInput.value = firCode;
          persistLastFir(firCode);
          updateSelectionSummary();
          applyFirButtonStates(firCode);
          if (el.firInput) el.firInput.focus();
        });
      });
    }

    function initializeFirReferencePanel() {
      const section = document.getElementById("firReferenceSection");
      if (!section) return;

      const hasCurrentLive = !!currentDataSite && Array.isArray(currentItems) && currentItems.length > 0;
      const hasAnyCache = FIR_CODES.some(code => {
        const cache = loadCache(code);
        return Array.isArray(cache?.items) && cache.items.length > 0;
      });

      section.classList.toggle("collapsed", hasCurrentLive || hasAnyCache);
      const toggleBtn = section.querySelector("[data-collapse-target='#firReferenceSection']");
      if (toggleBtn) {
        toggleBtn.textContent = section.classList.contains("collapsed") ? "Show" : "Hide";
      }

      updateFirReferenceCounts();
    }

    function setIcaoSelection(code) {
      const normalized = normalizeCode(code, 4);
      if (!normalized) {
        el.icaoInput.value = "";
        updateSelectionSummary();
        return;
      }
      el.icaoInput.value = normalized;
      updateSelectionSummary();
      persistLastIcao(normalized);
    }

    function refreshIcaoOptionsFromItems(items) {
      const airports = buildAirportUniverseFromItems(items || []);
      const selectedBefore = normalizeCode(el.icaoInput.value, 4);
      const preferredIcao = selectedBefore || lastSelectedIcao;
      const optionsHtml = airports
        .map(code => `<option value="${escapeHtml(code)}"></option>`)
        .join("");
      if (el.icaoList) {
        el.icaoList.innerHTML = optionsHtml;
      }

      if (preferredIcao) {
        setIcaoSelection(preferredIcao);
      } else {
        setIcaoSelection("");
      }
    }

    function extractAirportCodeFromRaw(rawText) {
      if (!rawText || typeof rawText !== "string") return "";
      const m = rawText.match(/A\)\s*([A-Z0-9]{3,4})/i);
      if (!m) return "";
      return normalizeCode(m[1], 4);
    }

    function isLikelyIcaoAirport(code) {
      if (!code) return false;
      const normalized = normalizeCode(code, 4);
      if (!/^C[A-Z0-9]{3}$/.test(normalized)) return false;
      if (normalized === "CXXX") return false;
      if (FIR_CODE_SET.has(normalized)) return false;
      return true;
    }

    function buildAirportUniverseFromItems(items) {
      const set = new Set();

      for (const item of items) {
        const locCode = normalizeCode(item?.location || "", 4);
        if (isLikelyIcaoAirport(locCode)) {
          set.add(locCode);
        }

        const rawCode = extractAirportCodeFromRaw(item?.raw || "");
        const rawCode4 = normalizeCode(rawCode, 4);
        if (isLikelyIcaoAirport(rawCode4)) {
          set.add(rawCode4);
        }
      }

      return Array.from(set).sort();
    }

    function updateAirportUniverseInfo(items) {
      const airports = buildAirportUniverseFromItems(items || []);
      const countText = String(airports.length);
      el.airportsFoundInline.textContent = countText;
    }

    function toPrettyDate(iso) {
      if (!iso) return "-";
      const d = new Date(iso);
      if (Number.isNaN(d.getTime())) return "-";
      const dateText = d.toLocaleString("en-CA", {
        year: "numeric",
        month: "short",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
        hour12: false,
        timeZone: DISPLAY_TIME_ZONE
      });
      const tzText = new Intl.DateTimeFormat("en-CA", {
        timeZone: DISPLAY_TIME_ZONE,
        timeZoneName: "short"
      })
        .formatToParts(d)
        .find(part => part.type === "timeZoneName")?.value || "ET";
      return `${dateText} ${tzText}`;
    }

    function toUtcDateTime(iso) {
      if (!iso) return "-";
      const d = new Date(iso);
      if (Number.isNaN(d.getTime())) return "-";
      const utcText = d.toLocaleString("en-CA", {
        year: "numeric",
        month: "short",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
        hour12: false,
        timeZone: "UTC"
      });
      return `${utcText} UTC`;
    }

    function updateLastFetchBanner(iso, sourceLabel = "Fetch") {
      if (!iso) {
        el.lastFetchBanner.textContent = "Last Fetch: - EDT | - UTC";
        el.lastFetchBanner.classList.remove("fresh", "stale");
        return;
      }

      const edtText = toPrettyDate(iso);
      const utcText = toUtcDateTime(iso);
      const d = new Date(iso);
      const ageMs = Number.isNaN(d.getTime()) ? Infinity : (Date.now() - d.getTime());
      const ageMins = Number.isFinite(ageMs) ? Math.max(0, Math.floor(ageMs / 60000)) : null;
      const ageText = ageMins == null ? "age n/a" : `age ${ageMins}m`;

      el.lastFetchBanner.textContent = `Last ${sourceLabel}: ${edtText} | ${utcText} | ${ageText}`;
      const isFresh = ageMs >= 0 && ageMs < FRESH_BANNER_WINDOW_MS;
      el.lastFetchBanner.classList.toggle("fresh", isFresh);
      el.lastFetchBanner.classList.toggle("stale", !isFresh);
    }

    function getCacheAgeMs(site) {
      const cached = loadCache(site);
      const fetchedAt = cached?.fetchedAt;
      if (!fetchedAt) return Infinity;
      const d = new Date(fetchedAt);
      if (Number.isNaN(d.getTime())) return Infinity;
      return Date.now() - d.getTime();
    }

    function buildApiUrl(site) {
      const params = new URLSearchParams();
      params.append("site", site);

      params.append("alpha", "notam");

      params.append("notam_choice", "default");
      params.append("_", String(Date.now()));
      return `${API_BASE}?${params.toString()}`;
    }

    function cacheKeyForSite(site) {
      return `fetchnotams:site:${site}`;
    }

    function getLastFir() {
      return normalizeCode(localStorage.getItem(LAST_FIR_STORAGE_KEY) || "", 4);
    }

    function loadCache(site) {
      const raw = localStorage.getItem(cacheKeyForSite(site));
      if (!raw) return null;
      try {
        return JSON.parse(raw);
      } catch {
        return null;
      }
    }

    function saveCache(site, payload) {
      localStorage.setItem(cacheKeyForSite(site), JSON.stringify(payload));
    }

    async function fetchWithTimeout(url, timeoutMs, options = {}) {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
      try {
        const res = await fetch(url, {
          method: "GET",
          signal: controller.signal,
          cache: "no-store",
          credentials: "omit",
          headers: options.headers || undefined
        });
        if (!res.ok) {
          throw new Error(`HTTP ${res.status}`);
        }
        return await res.json();
      } finally {
        clearTimeout(timeoutId);
      }
    }

    function parseTextBlock(value) {
      if (typeof value !== "string") return "";
      try {
        const parsed = JSON.parse(value);
        if (parsed && typeof parsed === "object") {
          return parsed.raw || parsed.english || parsed.french || "";
        }
      } catch {
        return value;
      }
      return "";
    }

    function parseQLine(rawText) {
      const m = (rawText || "").match(/Q\)\s*([^\n\r]+)/i);
      if (!m) return null;
      const line = String(m[1] || "").trim();
      if (!line) return null;
      const parts = line.split("/").map(part => String(part || "").trim());
      const fir = normalizeCode(parts[0], 4);
      const qcode = normalizeCode(parts[1], 5);
      if (!qcode || qcode.length !== 5 || qcode[0] !== "Q") return null;
      const subject = qcode.slice(1, 3);
      const category = subject.slice(0, 1);
      const condition = qcode.slice(3, 5);
      const traffic = String(parts[2] || "").toUpperCase().replace(/[^A-Z]/g, "");
      const purpose = String(parts[3] || "").toUpperCase().replace(/[^A-Z]/g, "");
      const scope = String(parts[4] || "").toUpperCase().replace(/[^A-Z]/g, "");
      return { fir, qcode, subject, category, condition, traffic, purpose, scope };
    }

    function extractNotamNumber(rawText) {
      const value = String(rawText || "");
      if (!value) return "";
      const m = value.match(/\(([A-Z]\d{4}\/\d{2})\s+NOTAM/i);
      if (m) return m[1];
      const m2 = value.match(/\b([A-Z]\d{4}\/\d{2})\b/);
      return m2 ? m2[1] : "";
    }

    function rebuildQCodeMaps() {
      Q_SUBJECT_CODE_MAP = new Map(Q_SUBJECT_CODES.map(entry => [entry.code, entry.meaning]));
      Q_CONDITION_CODE_MAP = new Map(Q_CONDITION_CODES.map(entry => [entry.code, entry.meaning]));
    }

    async function loadQCodeLegendData() {
      if (!qLegendController) return false;
      const loaded = await qLegendController.loadData();
      Q_SUBJECT_CODES = qLegendController.getSubjectCodes();
      Q_CONDITION_CODES = qLegendController.getConditionCodes();
      rebuildQCodeMaps();
      return loaded;
    }

    function getQSubjectMeaning(code) {
      if (!code) return "";
      return Q_SUBJECT_CODE_MAP.get(code) || "";
    }

    function getQConditionMeaning(code) {
      if (!code) return "";
      return Q_CONDITION_CODE_MAP.get(code) || "";
    }

    function scoreQCode(qInfo) {
      if (!qInfo) return { score: 0, label: "Unknown", reason: "" };
      const override = Q_PRIORITY_OVERRIDES.find(entry => entry.subject === qInfo.subject);
      if (override) {
        return { score: override.score, label: override.label, reason: override.reason };
      }
      const base = Q_PRIORITY_BY_CATEGORY[qInfo.category] || 0;
      const conditionBoost = Q_PRIORITY_BY_CONDITION[qInfo.condition] || 0;
      const score = base + conditionBoost;
      let label = "Low";
      if (score >= 85) label = "High";
      else if (score >= 60) label = "Medium";
      return { score, label, reason: "" };
    }

    function isPrioritySortEnabled() {
      return String(el.sortByPriorityBtn?.dataset.state || "on") === "on";
    }

    function dmsTokenToDecimal(token, isLat) {
      const clean = (token || "").toUpperCase().trim();
      const dir = clean.slice(-1);
      const body = clean.slice(0, -1);

      if (isLat && !/[NS]/.test(dir)) return null;
      if (!isLat && !/[EW]/.test(dir)) return null;

      const degDigits = isLat ? 2 : 3;
      if (!/^\d+$/.test(body)) return null;
      if (body.length !== degDigits + 2 && body.length !== degDigits + 4) return null;

      const deg = Number(body.slice(0, degDigits));
      const min = Number(body.slice(degDigits, degDigits + 2));
      const sec = body.length === degDigits + 4 ? Number(body.slice(degDigits + 2, degDigits + 4)) : 0;

      if (min >= 60 || sec >= 60) return null;

      let dd = deg + (min / 60) + (sec / 3600);
      if (dir === "S" || dir === "W") dd = -dd;
      return dd;
    }

    function linkifyDmsCoordinatePairs(text) {
      const value = text || "";
      const pairRegex = /(\d{4,6}[NS])\s*(\d{5,7}[EW])/gi;
      let lastIndex = 0;
      let match;
      const out = [];

      while ((match = pairRegex.exec(value)) !== null) {
        out.push(escapeHtml(value.slice(lastIndex, match.index)));

        const latToken = (match[1] || "").toUpperCase();
        const lonToken = (match[2] || "").toUpperCase();
        const lat = dmsTokenToDecimal(latToken, true);
        const lon = dmsTokenToDecimal(lonToken, false);

        if (lat == null || lon == null) {
          out.push(escapeHtml(match[0]));
        } else {
          const href = `NotamsMap.html?lat=${lat.toFixed(6)}&lon=${lon.toFixed(6)}&focus=1&src=fetchnotams`;
          out.push(`<a class="coord-link" href="${href}" onclick="return openMapTab(event, this);" title="Lookup on Map?" aria-label="Lookup on Map?">${escapeHtml(latToken)}&nbsp;${escapeHtml(lonToken)}</a>`);
        }

        lastIndex = pairRegex.lastIndex;
      }

      out.push(escapeHtml(value.slice(lastIndex)));
      return out.join("");
    }

    function extractDmsCoordinatePairsFromText(text) {
      const value = String(text || "");
      const pairRegex = /(\d{4,6}[NS])\s*(\d{5,7}[EW])/gi;
      const found = [];
      let match;

      while ((match = pairRegex.exec(value)) !== null) {
        const latToken = (match[1] || "").toUpperCase();
        const lonToken = (match[2] || "").toUpperCase();
        const lat = dmsTokenToDecimal(latToken, true);
        const lon = dmsTokenToDecimal(lonToken, false);
        if (lat == null || lon == null) continue;
        if (lat < -90 || lat > 90 || lon < -180 || lon > 180) continue;
        found.push({ lat, lon });
      }

      return found;
    }

    function extractPrimaryCoordinateFromNotam(rawText) {
      const value = String(rawText || "");
      if (!value) return null;

      const eMatch = value.match(/E\)\s*([\s\S]*?)(?=(?:\n|\r\n?)[A-Z]\)|$)/);
      const eSection = eMatch ? String(eMatch[0] || "") : "";
      const eCoords = extractDmsCoordinatePairsFromText(eSection);
      if (eCoords.length > 0) {
        return eCoords[0];
      }

      const anyCoords = extractDmsCoordinatePairsFromText(value);
      return anyCoords.length > 0 ? anyCoords[0] : null;
    }

    function pruneOldMapPayloads() {
      const now = Date.now();
      const staleKeys = [];
      for (let i = 0; i < localStorage.length; i += 1) {
        const key = localStorage.key(i);
        if (!key || !key.startsWith(MAP_PAYLOAD_STORAGE_PREFIX)) continue;
        try {
          const raw = localStorage.getItem(key);
          const parsed = raw ? JSON.parse(raw) : null;
          const createdAt = Number(parsed?.createdAt || 0);
          if (!createdAt || (now - createdAt) > MAP_PAYLOAD_TTL_MS) {
            staleKeys.push(key);
          }
        } catch {
          staleKeys.push(key);
        }
      }
      for (const key of staleKeys) {
        localStorage.removeItem(key);
      }
    }

    function buildMapPayloadFromItems(items, maxMarkers = 120) {
      const records = [];
      const seen = new Set();
      let rawCoordinateCount = 0;

      for (const item of items || []) {
        const coord = extractPrimaryCoordinateFromNotam(item?.raw || "");
        if (!coord) continue;

        rawCoordinateCount += 1;
        const key = `${coord.lat.toFixed(6)},${coord.lon.toFixed(6)}`;
        if (seen.has(key)) continue;
        seen.add(key);

        if (records.length < maxMarkers) {
          records.push({
            lat: Number(coord.lat.toFixed(6)),
            lon: Number(coord.lon.toFixed(6)),
            start: item?.startValidity || null,
            end: item?.endValidity || null,
            raw: String(item?.raw || "")
          });
        }
      }

      return {
        records,
        uniqueMarkerCount: seen.size,
        rawCoordinateCount,
        truncated: seen.size > records.length
      };
    }

    function storeMapPayload(records) {
      pruneOldMapPayloads();
      const key = `${MAP_PAYLOAD_STORAGE_PREFIX}${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
      const payload = {
        createdAt: Date.now(),
        records
      };
      localStorage.setItem(key, JSON.stringify(payload));
      return key;
    }

    function storeLatestLivePayloadFromItems(items, maxMarkers = 1200, firCode = "") {
      const payloadInfo = buildMapPayloadFromItems(items, maxMarkers);
      const records = payloadInfo?.records || [];
      if (!records.length) return 0;

      const payload = {
        createdAt: Date.now(),
        records,
        scope: "live-unfiltered",
        fir: normalizeCode(firCode, 4)
      };
      localStorage.setItem(MAP_LIVE_UNFILTERED_STORAGE_KEY, JSON.stringify(payload));
      return records.length;
    }

    function buildBatchMapUrlFromPayloadKey(payloadKey, payloadInfo) {
      const records = payloadInfo?.records || [];
      if (!records.length || !payloadKey) return "";

      const first = records[0];
      const params = new URLSearchParams();
      params.set("src", "fetchnotams");
      params.set("focus", "1");
      params.set("airports", "off");
      params.set("payload_key", payloadKey);
      params.set("lat", String(first.lat));
      params.set("lon", String(first.lon));
      if (payloadInfo.truncated) {
        params.set("marker_truncated", "1");
      }

      return `NotamsMap.html?${params.toString()}`;
    }

    function updateViewAllOnMapButton(displayItems) {
      const payloadInfo = buildMapPayloadFromItems(displayItems, 120);
      const hasPayload = payloadInfo.records.length > 0;
      const notamCount = Array.isArray(displayItems) ? displayItems.length : 0;
      const markerCount = payloadInfo.records.length;

      pendingMapPayloadInfo = hasPayload ? payloadInfo : null;
      el.viewAllOnMapBtn.disabled = !hasPayload;

      if (!hasPayload) {
        el.viewAllOnMapBtn.textContent = "View all on map";
        el.viewAllOnMapBtn.title = "No coordinates found in displayed results";
        return;
      }

      if (markerCount === notamCount) {
        el.viewAllOnMapBtn.textContent = `View all on map (${markerCount})`;
      } else {
        el.viewAllOnMapBtn.textContent = `View all on map (${notamCount} NOTAMs, ${markerCount} markers)`;
      }

      if (payloadInfo.truncated) {
        el.viewAllOnMapBtn.title = `Showing first ${markerCount} unique markers (more available)`;
      } else {
        el.viewAllOnMapBtn.title = `Open ${notamCount} displayed NOTAM(s) as ${markerCount} marker(s)`;
      }
    }

    function openMapTab(event, anchorEl) {
      if (event) event.preventDefault();
      const href = anchorEl && anchorEl.href ? anchorEl.href : null;
      if (!href) return false;

      const popup = window.open(href, "_blank");
      if (popup) {
        popup.focus();
      } else {
        window.location.href = href;
      }
      return false;
    }

    function buildNotamDescriptionHtml(rawText) {
      const value = String(rawText || "");
      const eMatch = value.match(/E\)\s*([\s\S]*?)(?=(?:\n|\r\n?)[A-Z]\)|$)/);
      if (!eMatch || typeof eMatch.index !== "number") {
        return escapeHtml(value);
      }

      const start = eMatch.index;
      const end = start + eMatch[0].length;
      const before = value.slice(0, start);
      const eSection = eMatch[0];
      const after = value.slice(end);
      return `${escapeHtml(before)}<span class="e-highlight">${linkifyDmsCoordinatePairs(eSection)}</span>${escapeHtml(after)}`;
    }

    function getQCategoryModeMap() {
      const map = new Map();
      document.querySelectorAll(".qcat-toggle").forEach(node => {
        const category = normalizeCode(node.dataset.qcat || "", 1);
        const state = String(node.dataset.state || "include").toLowerCase() === "exclude" ? "exclude" : "include";
        if (category) {
          map.set(category, state);
        }
      });
      return map;
    }

    function setQCategoryButtonState(button, state) {
      const category = normalizeCode(button.dataset.qcat || "", 1);
      const normalizedState = state === "exclude" ? "exclude" : "include";
      button.dataset.state = normalizedState;
      button.classList.remove("include", "exclude");
      button.classList.add(normalizedState);
      button.textContent = `${category}*: ${normalizedState === "exclude" ? "Exclude" : "Include"}`;
    }

    function updateQCategoryTooltips() {
      document.querySelectorAll(".qcat-toggle").forEach(node => {
        const category = normalizeCode(node.dataset.qcat || "", 1);
        if (!category) return;
        const label = getSubjectCategoryTooltip(category);
        const text = `${category} = ${label}`;
        node.dataset.tooltip = text;
        node.title = text;
      });
    }

    function resetQFilterDefaults() {
      document.querySelectorAll(".qcat-toggle").forEach(node => {
        const category = normalizeCode(node.dataset.qcat || "", 1);
        const defaultState = category === "O" ? "include" : "exclude";
        setQCategoryButtonState(node, defaultState);
      });
      updateQFilterSummary();
    }

    function setSortPriorityState(isOn) {
      const on = !!isOn;
      if (!el.sortByPriorityBtn) return;
      el.sortByPriorityBtn.dataset.state = on ? "on" : "off";
      el.sortByPriorityBtn.classList.toggle("is-on", on);
      el.sortByPriorityBtn.textContent = `Sort by priority: ${on ? "ON" : "OFF"}`;
    }

    function isQFilterEnabled() {
      return String(el.toggleQFilterBtn?.dataset.state || "off").toLowerCase() === "on";
    }

    function setQFilterToggleState(enabled) {
      const isOn = !!enabled;
      el.toggleQFilterBtn.dataset.state = isOn ? "on" : "off";
      el.toggleQFilterBtn.classList.toggle("is-on", isOn);
      el.toggleQFilterBtn.textContent = isOn ? "Filters ON" : "Filters OFF";
    }

    function updateQFilterSummary() {
      const enabled = isQFilterEnabled();
      const modeMap = getQCategoryModeMap();
      const excluded = TRACKED_Q_CATEGORIES.filter(category => modeMap.get(category) === "exclude");
      const included = TRACKED_Q_CATEGORIES.filter(category => modeMap.get(category) !== "exclude");
      const excludedText = excluded.length > 0 ? excluded.join(",") : "none";
      const includedText = included.length > 0 ? included.join(",") : "none";
      const sortText = isPrioritySortEnabled() ? "Priority sort on." : "Priority sort off.";
      if (!enabled) {
        el.qFilterSummary.textContent = `Q filter is off. Live results are unchanged. ${sortText}`;
        return;
      }
      el.qFilterSummary.textContent = `Q filter on: include ${includedText} | exclude ${excludedText}. ${sortText}`;
    }

    function getSubjectCategoryTooltip(letter) {
      return qLegendController ? qLegendController.getSubjectCategoryTooltip(letter) : "Other";
    }

    function renderQSubjectLegendTable() {
      if (qLegendController) {
        qLegendController.render();
      }
    }

    function openQCodeLegend() {
      el.qLegendModal.classList.add("open");
      el.qLegendModal.setAttribute("aria-hidden", "false");
      qLegendOpenedAtMs = Date.now();
      setQCodeLegendPopoutStatus("", "");
      if (el.qLegendSearch) {
        requestAnimationFrame(() => el.qLegendSearch.focus());
      }
    }

    function setQCodeLegendPopoutStatus(message, tone = "") {
      if (!el.qLegendPopoutStatus) return;
      const msg = String(message || "").trim();
      el.qLegendPopoutStatus.textContent = msg;
      el.qLegendPopoutStatus.classList.remove("show", "warn", "ok");
      if (!msg) return;
      el.qLegendPopoutStatus.classList.add("show");
      if (tone === "warn" || tone === "ok") {
        el.qLegendPopoutStatus.classList.add(tone);
      }
    }

    function openQCodeLegendPopup() {
      try {
        const popupWidth = 860;
        const popupHeight = 900;
        const left = Math.max(20, window.screenX + window.outerWidth - popupWidth - 30);
        const top = Math.max(20, window.screenY + 70);
        const features = [
          `width=${popupWidth}`,
          `height=${popupHeight}`,
          `left=${left}`,
          `top=${top}`,
          "resizable=yes",
          "scrollbars=yes",
          "menubar=no",
          "toolbar=no",
          "location=no",
          "status=no"
        ].join(",");

        qLegendPopupWindow = window.open("QCodeLegend.html", "NotamQCodeLegendWindow", features);

        if (!qLegendPopupWindow || qLegendPopupWindow.closed) {
          setQCodeLegendPopoutStatus("Pop-out blocked by browser settings. Allow pop-ups for this page, then click Pop out again.", "warn");
          return false;
        }
        qLegendPopupWindow.focus();
        setQCodeLegendPopoutStatus("Standalone Q-Code Legend opened in a separate window.", "ok");
        return true;
      } catch (error) {
        console.warn("[FetchNotams] Q legend popup failed, using modal fallback.", error);
        setQCodeLegendPopoutStatus("Pop-out failed to open due to a browser/runtime error. Keep using the in-page legend.", "warn");
        return false;
      }
    }

    function launchQCodeLegend(event) {
      if (event) {
        event.preventDefault();
      }
      const now = Date.now();
      if (now - qLegendLastLaunchAtMs < 200) {
        return;
      }
      qLegendLastLaunchAtMs = now;
      renderQSubjectLegendTable();
      // Keep trigger behavior deterministic: open in-page modal first.
      openQCodeLegend();
    }

    function closeQCodeLegend() {
      el.qLegendModal.classList.remove("open");
      el.qLegendModal.setAttribute("aria-hidden", "true");
      if (el.qLegendSearch) el.qLegendSearch.value = "";
      if (el.qLegendConditionSearch) el.qLegendConditionSearch.value = "";
      renderQSubjectLegendTable();
    }

    function parseNotamItems(payload) {
      const arr = Array.isArray(payload?.data) ? payload.data : [];
      const mapped = arr
        .filter(item => item && item.type === "notam")
        .map(item => ({
          pk: String(item.pk || ""),
          location: String(item.location || "CXXX"),
          startValidity: item.startValidity || null,
          endValidity: item.endValidity || null,
          raw: parseTextBlock(item.text)
        }))
        .filter(item => item.raw);

      mapped.sort((a, b) => {
        const ta = a.startValidity ? new Date(a.startValidity).getTime() : 0;
        const tb = b.startValidity ? new Date(b.startValidity).getTime() : 0;
        return tb - ta;
      });

      return mapped;
    }

    function setStatusClass(target, state) {
      target.classList.remove("status-ok", "status-warn", "status-err");
      if (state) target.classList.add(state);
    }

    function setLoading(active, message) {
      if (typeof message === "string" && el.loadingText) {
        el.loadingText.textContent = message;
      }
      el.loadingState.classList.toggle("active", active);
      el.loadingState.setAttribute("aria-busy", active ? "true" : "false");
    }

    function setFetchButtonState(state) {
      if (!el.fetchNotamsBtn) return;
      el.fetchNotamsBtn.classList.remove("btn-attn", "btn-muted");
      if (state === "attention") {
        el.fetchNotamsBtn.classList.add("btn-attn");
      } else if (state === "muted") {
        el.fetchNotamsBtn.classList.add("btn-muted");
      }
    }

    function setUseCacheButtonState(isFresh) {
      if (!el.refreshFromCacheBtn) return;
      el.refreshFromCacheBtn.classList.toggle("btn-attn", !!isFresh);
    }

    function applyFirButtonStates(firCode) {
      const ageMs = getCacheAgeMs(firCode);
      const hasFreshCache = Number.isFinite(ageMs) && ageMs < FRESH_BANNER_WINDOW_MS;
      if (hasFreshCache) {
        setUseCacheButtonState(true);
        setFetchButtonState("muted");
      } else {
        setUseCacheButtonState(false);
        setFetchButtonState("attention");
      }
    }

    function resetToNoData(message = "No data loaded yet.", buttonState = "attention") {
      currentItems = [];
      currentDataSite = "";
      refreshIcaoOptionsFromItems([]);
      updateAirportUniverseInfo([]);
      render([], normalizeCode(el.firInput.value, 4) || "-", message);
      el.fetchTimeValue.textContent = "-";
      el.updatedValue.textContent = "-";
      setStatusClass(el.sourceValue, "");
      setFetchButtonState(buttonState);
      updateFirReferenceCounts();
    }

    function render(items, site, sourceLabel) {
      const maxCountRaw = Number(el.maxItems.value);
      const maxCount = Number.isFinite(maxCountRaw) ? maxCountRaw : 100;
      const qFilterEnabled = isQFilterEnabled();
      const qCategoryModes = getQCategoryModeMap();
      const icaoFilter = normalizeCode(el.icaoInput.value, 4);
      const notamFilterRaw = String(el.notamInput?.value || "").toUpperCase().replace(/\s+/g, "");

      const icaoFiltered = icaoFilter
        ? items.filter(item => item.location.includes(icaoFilter) || item.raw.includes(icaoFilter))
        : items;

      const inputFiltered = notamFilterRaw
        ? icaoFiltered.filter(item => {
            const notamNumber = extractNotamNumber(item.raw || "").toUpperCase().replace(/\s+/g, "");
            return notamNumber.includes(notamFilterRaw);
          })
        : icaoFiltered;

      const filtered = qFilterEnabled
        ? inputFiltered.filter(item => {
            const qInfo = parseQLine(item.raw || "");
            if (!qInfo) return true;
            const mode = qCategoryModes.get(qInfo.category) || "include";
            return mode !== "exclude";
          })
        : inputFiltered;

      currentFilteredItems = filtered;

      const missingQCodes = new Set();
      const decorated = filtered.map(item => {
        const qInfo = parseQLine(item.raw || "");
        const priority = scoreQCode(qInfo);
        let missingSubject = false;
        let missingCondition = false;
        let missingQCode = false;

        if (qInfo?.subject) {
          missingSubject = !Q_SUBJECT_CODE_MAP.has(qInfo.subject);
        }
        if (qInfo?.condition) {
          missingCondition = !Q_CONDITION_CODE_MAP.has(qInfo.condition);
        }
        if (!qInfo || missingSubject || missingCondition) {
          missingQCode = true;
          if (qInfo?.qcode) {
            missingQCodes.add(qInfo.qcode);
          } else {
            missingQCodes.add("Q????");
          }
        }

        return { item, qInfo, priority, missingSubject, missingCondition, missingQCode };
      });

      if (isPrioritySortEnabled()) {
        decorated.sort((a, b) => {
          if (b.priority.score !== a.priority.score) {
            return b.priority.score - a.priority.score;
          }
          const ta = a.item.startValidity ? new Date(a.item.startValidity).getTime() : 0;
          const tb = b.item.startValidity ? new Date(b.item.startValidity).getTime() : 0;
          return tb - ta;
        });
      }

      const displayItems = maxCount === 0 ? decorated : decorated.slice(0, maxCount);
      updateViewAllOnMapButton(displayItems.map(entry => entry.item));
      scheduleMobileDockUpdate();
      const html = displayItems
        .map(entry => {
          const item = entry.item;
          const qInfo = entry.qInfo;
          const priority = entry.priority;
          const notamNumber = extractNotamNumber(item.raw || "");
          const title = notamNumber || (item.pk ? item.pk : "NO-ID");
          const start = toPrettyDate(item.startValidity);
          const end = toPrettyDate(item.endValidity);
          const subjectMeaning = qInfo ? getQSubjectMeaning(qInfo.subject) : "";
          const conditionMeaning = qInfo ? getQConditionMeaning(qInfo.condition) : "";
          const qLine = qInfo
            ? `${qInfo.qcode}${subjectMeaning ? ` (${qInfo.subject}: ${subjectMeaning})` : ""}${conditionMeaning ? ` - ${qInfo.condition}: ${conditionMeaning}` : ""}`
            : "Q-code not found";
          const labelKey = String(priority.label || "").toLowerCase();
          const priorityTone = (labelKey === "high" || labelKey === "critical")
            ? "high"
            : (labelKey === "medium" ? "medium" : "low");
          const missingNote = entry.missingQCode ? "Unknown Q-code" : "";
          const qcodeClass = entry.missingQCode ? "missing" : "";
          return `
            <li class="notam-item">
              <div class="notam-line1">
                <span class="notam-id">${escapeHtml(title)}</span>
                <span class="notam-loc">${escapeHtml(item.location)}</span>
                <span class="notam-time">Start (EDT/ET): ${escapeHtml(start)} | End (EDT/ET): ${escapeHtml(end)}</span>
              </div>
              <div class="notam-line2">
                <span class="qcode-pill ${qcodeClass}">${escapeHtml(qInfo ? qInfo.qcode : "Q----")}</span>
                <span class="priority-pill ${priorityTone}">${escapeHtml(priority.label)}</span>
                ${missingNote ? `<span class="qcode-missing-note">${escapeHtml(missingNote)}</span>` : ""}
                <span class="qcode-meaning">${escapeHtml(qLine)}</span>
              </div>
              <pre class="notam-preview">${buildNotamDescriptionHtml(item.raw)}</pre>
            </li>
          `;
        })
        .join("");

      el.resultsList.innerHTML = html;
      el.totalValue.textContent = String(items.length);
      el.shownValue.textContent = String(displayItems.length);
      el.notamsInScopeInline.textContent = String(inputFiltered.length);
      updateAirportUniverseInfo(inputFiltered);
      const icaoLabel = normalizeCode(el.icaoInput.value, 4) || "-";
      el.resultsHeaderText.textContent = `${site}/${icaoLabel}: NOTAMs as filtered = ${filtered.length}, showing ${displayItems.length}.`;
      if (el.unknownQCodesValue) {
        el.unknownQCodesValue.textContent = String(missingQCodes.size);
      }
      const hasFirInput = !!normalizeCode(el.firInput.value, 4);
      if (!hasFirInput) {
        setFetchButtonState("default");
      } else {
        setFetchButtonState(items.length > 0 ? "muted" : "attention");
      }
      el.sourceValue.textContent = sourceLabel;
      updateQFilterSummary();
      updateFirReferenceCounts();
    }

    function escapeHtml(value) {
      return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/\"/g, "&quot;")
        .replace(/'/g, "&#39;");
    }

    async function fetchLive(site) {
      const url = buildApiUrl(site);
      const t0 = performance.now();

      try {
        const proxyErrors = [];

        for (const proxy of PROXY_PROVIDERS) {
          try {
            const proxiedUrl = proxy.buildUrl(url);
            const payload = await fetchWithTimeout(proxiedUrl, PROXY_TIMEOUT_MS, { headers: proxy.headers });
            const elapsed = Math.round(performance.now() - t0);
            return {
              payload,
              source: `Live via ${proxy.label}`,
              elapsedMs: elapsed
            };
          } catch (proxyError) {
            proxyErrors.push(`${proxy.name}: ${proxyError.message || "unknown"}`);
          }
        }

        const payload = await fetchWithTimeout(url, DIRECT_TIMEOUT_MS);
        const elapsed = Math.round(performance.now() - t0);
        return {
          payload,
          source: "Live (direct)",
          elapsedMs: elapsed,
          warning: `Proxy fetch failed: ${proxyErrors.join(" | ")}`
        };
      } catch (fetchError) {
        throw new Error(
          `Proxy and direct fetch failed. ${fetchError.message || "unknown"}`
        );
      }
    }

    async function loadAndRender({ fromCacheOnly = false } = {}) {
      let site = normalizeCode(el.firInput.value, 4);
      if (!site || site.length < 3) {
        if (fromCacheOnly) {
          const fallbackFir = getLastFir();
          if (!fallbackFir) {
            alert("No cached FIR available. Enter a FIR code first.");
            return;
          }
          site = fallbackFir;
          el.firInput.value = site;
        } else {
          alert("Select a valid FIR (4 chars). Example: CZYZ");
          return;
        }
      }

      const cached = loadCache(site);
      const hasCache = !!(cached && Array.isArray(cached.items));

      el.firInput.value = site;
      persistLastFir(site);
      updateSelectionSummary();
      setLoading(
        true,
        fromCacheOnly
          ? "Loading NOTAMs from cache..."
          : (hasCache
              ? "Refreshing NOTAMs in background..."
              : "Loading NOTAMs (cache first, live refresh in progress)...")
      );

      const now = Date.now();

      if (cached && Array.isArray(cached.items)) {
        currentItems = cached.items;
        currentDataSite = site;
        storeLatestLivePayloadFromItems(currentItems, 1200, site);
        refreshIcaoOptionsFromItems(currentItems);
        updateAirportUniverseInfo(currentItems);
        render(currentItems, site, "Cache");
        el.updatedValue.textContent = toPrettyDate(cached.fetchedAt || cached.savedAt);
        updateLastFetchBanner(cached.fetchedAt || cached.savedAt, "Cache");
        el.fetchTimeValue.textContent = "0 ms";
        setStatusClass(el.sourceValue, "status-ok");
      }

      if (fromCacheOnly) {
        el.notamsInScopeInline.textContent = String(currentItems.length);
        setLoading(false);
        return;
      }

      try {
        const fresh = await fetchLive(site);
        const parsedItems = parseNotamItems(fresh.payload);

        currentItems = parsedItems;
        currentDataSite = site;
        storeLatestLivePayloadFromItems(currentItems, 1200, site);
        refreshIcaoOptionsFromItems(currentItems);
        updateAirportUniverseInfo(currentItems);
        render(currentItems, site, fresh.source);

        el.fetchTimeValue.textContent = `${fresh.elapsedMs} ms`;
        const nowIso = new Date().toISOString();
        el.updatedValue.textContent = toPrettyDate(nowIso);
        updateLastFetchBanner(nowIso, "Fetch");

        if (fresh.source.includes("proxy")) {
          setStatusClass(el.sourceValue, "status-warn");
        } else {
          setStatusClass(el.sourceValue, "status-ok");
        }

        saveCache(site, {
          site,
          fetchedAt: nowIso,
          savedAt: now,
          items: parsedItems
        });
        persistLastFir(site);
      } catch (error) {
        const hasFreshCache = cached && Array.isArray(cached.items) && (now - Number(cached.savedAt || 0) <= CACHE_TTL_MS);
        if (hasFreshCache) {
          refreshIcaoOptionsFromItems(cached.items);
          updateAirportUniverseInfo(cached.items);
          render(cached.items, site, "Cache (live failed)");
          el.fetchTimeValue.textContent = "timeout/fail";
          el.updatedValue.textContent = `${toPrettyDate(cached.fetchedAt)} (cached)`;
          setStatusClass(el.sourceValue, "status-warn");
          el.resultsHeaderText.textContent = `${site}: Live fetch failed, showing recent cache.`;
        } else {
          currentItems = [];
          currentDataSite = "";
          refreshIcaoOptionsFromItems([]);
          updateAirportUniverseInfo([]);
          el.notamsInScopeInline.textContent = "0";
          render([], site, "No data");
          el.fetchTimeValue.textContent = "failed";
          el.updatedValue.textContent = "-";
          setStatusClass(el.sourceValue, "status-err");
          el.resultsHeaderText.textContent = `${site}: ${error.message}`;
        }
      } finally {
        setLoading(false);
        if (!hasAutoFocusedIcao && el.icaoInput) {
          hasAutoFocusedIcao = true;
          requestAnimationFrame(() => el.icaoInput.focus());
        }
      }
    }

    el.form.addEventListener("submit", async event => {
      event.preventDefault();
      const site = normalizeCode(el.firInput.value, 4);
      if (!site) {
        alert("Enter a FIR code (4 chars). Example: CZYZ");
        return;
      }
      const cacheAgeMs = getCacheAgeMs(site);
      const firChanged = site !== lastFetchActionSite;

      if (!firChanged && cacheAgeMs >= 0 && cacheAgeMs < LIVE_FETCH_COOLDOWN_MS) {
        const mins = Math.floor(cacheAgeMs / 60000);
        const wantsLiveRefresh = window.confirm(
          `Last fetch for ${site} was ${mins} minute(s) ago. Do you really want to refresh live now?\n\n` +
          "Select Cancel to use cache instead."
        );

        if (!wantsLiveRefresh) {
          await loadAndRender({ fromCacheOnly: true });
          render(currentItems, site, el.sourceValue.textContent || "-");
          return;
        }
      }

      lastFetchActionSite = site;
      loadAndRender();
    });

    el.firInput.addEventListener("input", () => {
      const firCode = normalizeCode(el.firInput.value, 4);
      el.firInput.value = firCode;
      updateSelectionSummary();
      applyFirButtonStates(firCode);
    });

    el.icaoInput.addEventListener("input", () => {
      el.icaoInput.value = normalizeCode(el.icaoInput.value, 4);
      persistLastIcao(el.icaoInput.value);
      updateSelectionSummary();
      const site = normalizeCode(el.firInput.value, 4) || "CZYZ";
      render(currentItems, site, el.sourceValue.textContent || "-");
    });

    if (el.notamInput) {
      el.notamInput.addEventListener("input", () => {
        const site = normalizeCode(el.firInput.value, 4) || "CZYZ";
        render(currentItems, site, el.sourceValue.textContent || "-");
      });
    }

    if (el.clearEntriesBtn) {
      el.clearEntriesBtn.addEventListener("click", () => {
        el.firInput.value = "";
        el.icaoInput.value = "";
        if (el.notamInput) el.notamInput.value = "";
        updateSelectionSummary();
        lastFetchActionSite = "";
        lastSelectedIcao = "";
        localStorage.removeItem(LAST_ICAO_STORAGE_KEY);
        resetToNoData("No data loaded yet.", "default");
        const lastFir = getLastFir();
        const cache = lastFir ? loadCache(lastFir) : null;
        const cacheAgeMs = cache?.fetchedAt ? (Date.now() - new Date(cache.fetchedAt).getTime()) : Infinity;
        setUseCacheButtonState(cacheAgeMs >= 0 && cacheAgeMs <= FRESH_BANNER_WINDOW_MS);
        el.icaoInput.value = "";
        el.icaoInput.dispatchEvent(new Event("input"));
      });
    }


    el.maxItems.addEventListener("change", () => {
      const site = normalizeCode(el.firInput.value, 4) || "CZYZ";
      render(currentItems, site, el.sourceValue.textContent || "-");
    });

    el.toggleQFilterBtn.addEventListener("click", () => {
      setQFilterToggleState(!isQFilterEnabled());
      const site = normalizeCode(el.firInput.value, 4) || "CZYZ";
      render(currentItems, site, el.sourceValue.textContent || "-");
    });

    document.querySelectorAll(".qcat-toggle").forEach(node => {
      node.addEventListener("click", () => {
        const nextState = String(node.dataset.state || "include").toLowerCase() === "exclude" ? "include" : "exclude";
        setQCategoryButtonState(node, nextState);
        const site = normalizeCode(el.firInput.value, 4) || "CZYZ";
        render(currentItems, site, el.sourceValue.textContent || "-");
      });
    });

    el.qSetAllExcludeBtn.addEventListener("click", () => {
      document.querySelectorAll(".qcat-toggle").forEach(node => {
        setQCategoryButtonState(node, "exclude");
      });
      const site = normalizeCode(el.firInput.value, 4) || "CZYZ";
      render(currentItems, site, el.sourceValue.textContent || "-");
    });

    el.qSetAllIncludeBtn.addEventListener("click", () => {
      document.querySelectorAll(".qcat-toggle").forEach(node => {
        setQCategoryButtonState(node, "include");
      });
      const site = normalizeCode(el.firInput.value, 4) || "CZYZ";
      render(currentItems, site, el.sourceValue.textContent || "-");
    });

    if (el.qResetDefaultsBtn) {
      el.qResetDefaultsBtn.addEventListener("click", () => {
        resetQFilterDefaults();
        const site = normalizeCode(el.firInput.value, 4) || "CZYZ";
        render(currentItems, site, el.sourceValue.textContent || "-");
      });
    }

    if (el.sortByPriorityBtn) {
      el.sortByPriorityBtn.addEventListener("click", () => {
        const isOn = String(el.sortByPriorityBtn.dataset.state || "on") === "on";
        setSortPriorityState(!isOn);
        const site = normalizeCode(el.firInput.value, 4) || "CZYZ";
        render(currentItems, site, el.sourceValue.textContent || "-");
      });
    }

    if (el.openQLegend) {
      el.openQLegend.addEventListener("click", launchQCodeLegend);
    }

    setupFirReferenceTable();
    initializeFirReferencePanel();

    if (qLegendController) {
      qLegendController.bindUi({
        bodyEl: el.qLegendBody,
        infoEl: el.qLegendInfo,
        subjectInput: el.qLegendSearch,
        conditionInput: el.qLegendConditionSearch,
        clearBtn: el.qLegendClearSearch,
        showAllBtn: el.qLegendShowAll
      });
    }

    // Overlay-safe fallback: if another element steals click target, hit-test button bounds.
    document.addEventListener("pointerup", event => {
      if (!el.openQLegend || !event.isPrimary) return;
      if (el.qLegendModal.classList.contains("open")) return;

      const target = event.target;
      if (target instanceof Element && (target === el.openQLegend || el.openQLegend.contains(target))) {
        return;
      }

      const rect = el.openQLegend.getBoundingClientRect();
      const x = event.clientX;
      const y = event.clientY;
      const inside = x >= rect.left && x <= rect.right && y >= rect.top && y <= rect.bottom;
      if (!inside) return;

      launchQCodeLegend(event);
    }, true);

    el.closeQLegend.addEventListener("click", () => {
      closeQCodeLegend();
    });

    el.popoutQLegend.addEventListener("click", () => {
      renderQSubjectLegendTable();
      openQCodeLegendPopup();
    });

    el.qLegendModal.addEventListener("click", event => {
      const target = event.target;
      if (target instanceof Element && target.hasAttribute("data-close-qlegend")) {
        if (Date.now() - qLegendOpenedAtMs < 300) {
          return;
        }
        closeQCodeLegend();
      }
    });

    document.addEventListener("keydown", event => {
      if (event.key === "Escape" && el.qLegendModal.classList.contains("open")) {
        closeQCodeLegend();
      }
    });

    if (el.refreshFromCacheBtn) {
      el.refreshFromCacheBtn.addEventListener("click", async () => {
        await loadAndRender({ fromCacheOnly: true });
        const site = normalizeCode(el.firInput.value, 4) || "CZYZ";
        render(currentItems, site, el.sourceValue.textContent || "-");
        setUseCacheButtonState(false);
      });
    }

    document.querySelectorAll("[data-collapse-target]").forEach(btn => {
      btn.addEventListener("click", () => {
        const targetSelector = btn.getAttribute("data-collapse-target");
        if (!targetSelector) return;
        const section = document.querySelector(targetSelector);
        if (!section) return;
        section.classList.toggle("collapsed");
        btn.textContent = section.classList.contains("collapsed") ? "Show" : "Hide";
      });
    });

    document.querySelectorAll("[data-section-head-target]").forEach(headSpan => {
      headSpan.addEventListener("click", () => {
        const targetSelector = headSpan.getAttribute("data-section-head-target");
        if (!targetSelector) return;
        const section = document.querySelector(targetSelector);
        if (!section) return;
        section.classList.toggle("collapsed");
        const isCollapsed = section.classList.contains("collapsed");
        const toggleBtn = section.querySelector(".section-toggle[data-collapse-target]");
        if (toggleBtn) toggleBtn.textContent = isCollapsed ? "Show" : "Hide";
      });
    });

    el.viewAllOnMapBtn.addEventListener("click", () => {
      const payloadInfo = pendingMapPayloadInfo;
      const records = payloadInfo?.records || [];
      if (!records.length) {
        alert("No obstacle coordinates found in the current displayed results.");
        return;
      }

      const payloadKey = storeMapPayload(records);
      const url = buildBatchMapUrlFromPayloadKey(payloadKey, payloadInfo);
      if (!url) {
        alert("No obstacle coordinates found in the current displayed results.");
        return;
      }

      const popup = window.open(url, "_blank");
      if (popup) {
        popup.focus();
      } else {
        window.location.href = url;
      }
    });

    initDeviceType();
    initViewMode();
    refreshIcaoOptionsFromItems([]);
    setQFilterToggleState(true);
    setSortPriorityState(true);
    loadQCodeLegendData().finally(() => {
      renderQSubjectLegendTable();
      updateQFilterSummary();
    });
    resetQFilterDefaults();
    updateQCategoryTooltips();

    const initialFir = getLastFir();
    if (initialFir) {
      el.firInput.value = initialFir;
      updateSelectionSummary();
      loadAndRender({ fromCacheOnly: true });
    } else {
      resetToNoData("No data loaded yet.", "attention");
      updateSelectionSummary();
    }
    updateFirReferenceCounts();
  
