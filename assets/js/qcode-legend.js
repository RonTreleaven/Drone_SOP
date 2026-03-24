(function () {
  "use strict";

  const SUBJECT_CATEGORY_LABELS = {
    A: "Airspace Organization (A)",
    C: "Communications and Surveillance Facilities (C)",
    F: "Facilities and Services (F)",
    G: "GNSS Services (G)",
    I: "Instrument and Microwave Landing System (I)",
    L: "Lighting Facilities (L)",
    M: "Movement and Landing Area (M)",
    N: "Terminal and En Route Navigation Facilities (N)",
    O: "Other Information (O)",
    P: "Air Traffic Procedures (P)",
    R: "Navigation Warnings: Airspace Restrictions (R)",
    S: "Air Traffic and VOLMET Services (S)",
    W: "Navigation Warnings: Warnings (W)",
    X: "Custom / Other (X)",
    K: "Checklists (K)"
  };

  const CONDITION_CATEGORY_LABELS = {
    A: "Availability (A)",
    C: "Changes (C)",
    H: "Hazard Conditions (H)",
    L: "Limitations (L)",
    X: "Other (XX)"
  };

  const Q_SUBJECT_CUSTOM = [
    { code: "NX", meaning: "Navaid (general)", category: "Terminal and En Route Navigation Facilities (N)" },
    { code: "XX", meaning: "Other / unspecified subject", category: "Custom / Other (X)" }
  ];

  const DEFAULT_TRAFFIC_CODES = [
    { code: "I", meaning: "IFR" },
    { code: "V", meaning: "VFR" },
    { code: "IV", meaning: "IFR + VFR" }
  ];

  const DEFAULT_SCOPE_CODES = [
    { code: "A", meaning: "Aerodrome" },
    { code: "E", meaning: "Enroute" },
    { code: "W", meaning: "Warnings" },
    { code: "AE", meaning: "Aerodrome + Enroute" },
    { code: "AW", meaning: "Aerodrome + Warnings" },
    { code: "EW", meaning: "Enroute + Warnings" },
    { code: "AEW", meaning: "Aerodrome + Enroute + Warnings" }
  ];

  function escapeHtml(value) {
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/\"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function stripTrailingCategoryLetter(label) {
    return String(label || "").replace(/\s*\([A-Z]\)\s*$/i, "").trim();
  }

  function normalizeSubjectCategoryLabel(rawTitle, code) {
    if (rawTitle) {
      return String(rawTitle)
        .replace(/^ATM\s+/i, "")
        .replace(/^CNS\s+/i, "")
        .replace(/^AGA\s+/i, "")
        .replace(/^COM\s+/i, "")
        .trim();
    }
    const letter = code ? String(code).slice(0, 1).toUpperCase() : "";
    return SUBJECT_CATEGORY_LABELS[letter] || "Other";
  }

  function normalizeConditionCategoryLabel(rawTitle, code) {
    if (rawTitle) {
      return String(rawTitle).trim();
    }
    const letter = code ? String(code).slice(0, 1).toUpperCase() : "";
    return CONDITION_CATEGORY_LABELS[letter] || "Other";
  }

  function formatSubjectSectionTitle(label, code) {
    const letter = code ? String(code).slice(0, 1).toUpperCase() : "";
    const cleanLabel = stripTrailingCategoryLetter(label);
    return "Subject - [" + letter + "*] " + cleanLabel;
  }

  function formatConditionSectionTitle(label, code) {
    const letter = code ? String(code).slice(0, 1).toUpperCase() : "";
    const cleanLabel = stripTrailingCategoryLetter(label);
    return "Condition - [" + letter + "*] " + cleanLabel;
  }

  function normalizeQuery(value) {
    return String(value || "")
      .toUpperCase()
      .replace(/[^A-Z*]/g, "")
      .replace(/\*+/g, "*")
      .trim();
  }

  function filterLegendRows(rows, query) {
    if (!query) return rows;
    const normalized = query.endsWith("*") ? query.slice(0, -1) : query;
    if (!normalized) return rows;
    return rows.filter(function (entry) {
      return String(entry.code || "").toUpperCase().startsWith(normalized);
    });
  }

  function renderLegendSection(title, rows, codeHeader, options) {
    if (!rows.length) return "";
    const opts = options || {};
    const sectionId = opts.sectionId || title.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
    const isCollapsed = opts.collapsed !== false;
    const highlightPrefix = String(opts.highlightPrefix || "").toUpperCase();
    const body = rows
      .map(function (entry) {
        const codeText = String(entry.code || "").toUpperCase();
        const isHit = highlightPrefix && codeText.startsWith(highlightPrefix);
        return "\n          <tr class=\"" + (isHit ? "q-legend-hit" : "") + "\">\n            <td class=\"q-legend-col-code\">" + escapeHtml(entry.code) + "</td>\n            <td>" + escapeHtml(entry.meaning) + "</td>\n          </tr>\n        ";
      })
      .join("");

    return "\n      <section class=\"q-legend-section " + (isCollapsed ? "collapsed" : "") + "\" data-section-id=\"" + escapeHtml(sectionId) + "\">\n        <div class=\"q-legend-section-head\">\n          <h3>" + escapeHtml(title) + "</h3>\n          <button class=\"q-legend-toggle\" type=\"button\" data-action=\"toggle\">Show</button>\n        </div>\n        <table class=\"q-legend-table\">\n          <thead>\n            <tr>\n              <th>" + escapeHtml(codeHeader || "Code") + "</th>\n              <th>Meaning</th>\n            </tr>\n          </thead>\n          <tbody>" + body + "</tbody>\n        </table>\n      </section>\n    ";
  }

  function createController(options) {
    const opts = options || {};
    let subjectCodes = Array.isArray(opts.subjectCodes) ? opts.subjectCodes.slice() : [];
    let conditionCodes = Array.isArray(opts.conditionCodes) ? opts.conditionCodes.slice() : [];
    const trafficCodes = Array.isArray(opts.trafficCodes) ? opts.trafficCodes.slice() : DEFAULT_TRAFFIC_CODES.slice();
    const scopeCodes = Array.isArray(opts.scopeCodes) ? opts.scopeCodes.slice() : DEFAULT_SCOPE_CODES.slice();
    const dataSources = {
      subjects: (opts.dataSources && opts.dataSources.subjects) || "data/Subjects.json",
      conditions: (opts.dataSources && opts.dataSources.conditions) || "data/Conditions.json"
    };

    const state = {
      bodyEl: null,
      infoEl: null,
      subjectInput: null,
      conditionInput: null,
      clearBtn: null,
      showAllBtn: null,
      subjectMap: new Map(),
      conditionMap: new Map()
    };

    function rebuildMaps() {
      state.subjectMap = new Map(subjectCodes.map(function (entry) { return [entry.code, entry.meaning]; }));
      state.conditionMap = new Map(conditionCodes.map(function (entry) { return [entry.code, entry.meaning]; }));
    }

    function applySubjectCustomRows() {
      if (!Array.isArray(Q_SUBJECT_CUSTOM) || !Q_SUBJECT_CUSTOM.length) return;
      const existing = new Set(subjectCodes.map(function (entry) { return entry.code; }));
      Q_SUBJECT_CUSTOM.forEach(function (entry) {
        const code = String(entry.code || "").toUpperCase().trim();
        if (!code || code.length !== 2 || existing.has(code)) return;
        subjectCodes.push({
          code: code,
          meaning: String(entry.meaning || "").trim(),
          category: String(entry.category || "").trim()
        });
        existing.add(code);
      });
    }

    function getSections(subjectQuery, conditionQuery) {
      const subjectPrefix = String(subjectQuery || "").replace(/\*/g, "");
      const conditionPrefix = String(conditionQuery || "").replace(/\*/g, "");
      const subjectRows = filterLegendRows(subjectCodes.slice().sort(function (a, b) { return a.code.localeCompare(b.code); }), subjectQuery);
      const conditionRows = filterLegendRows(conditionCodes.slice().sort(function (a, b) { return a.code.localeCompare(b.code); }), conditionQuery);
      const trafficRows = trafficCodes.slice().sort(function (a, b) { return a.code.localeCompare(b.code); });
      const scopeRows = scopeCodes.slice().sort(function (a, b) { return a.code.localeCompare(b.code); });

      const subjectGroups = new Map();
      subjectRows.forEach(function (entry) {
        const label = normalizeSubjectCategoryLabel(entry.category, entry.code);
        const letter = String(entry.code || "").slice(0, 1).toUpperCase();
        if (!subjectGroups.has(letter)) subjectGroups.set(letter, { label: label, rows: [] });
        subjectGroups.get(letter).rows.push(entry);
      });

      const subjectSections = Array.from(subjectGroups.entries())
        .sort(function (a, b) { return a[0].localeCompare(b[0]); })
        .map(function (pair) {
          const letter = pair[0];
          const group = pair[1];
          const rows = group.rows;
          const hasMatch = subjectPrefix && rows.some(function (entry) { return String(entry.code || "").toUpperCase().startsWith(subjectPrefix); });
          return renderLegendSection(formatSubjectSectionTitle(group.label, letter), rows, "Subject", {
            collapsed: subjectPrefix ? !hasMatch : true,
            highlightPrefix: subjectPrefix
          });
        });

      const conditionGroups = new Map();
      conditionRows.forEach(function (entry) {
        const label = normalizeConditionCategoryLabel(entry.category, entry.code);
        const letter = String(entry.code || "").slice(0, 1).toUpperCase();
        if (!conditionGroups.has(letter)) conditionGroups.set(letter, { label: label, rows: [] });
        conditionGroups.get(letter).rows.push(entry);
      });

      const conditionSections = Array.from(conditionGroups.entries())
        .sort(function (a, b) { return a[0].localeCompare(b[0]); })
        .map(function (pair) {
          const letter = pair[0];
          const group = pair[1];
          const rows = group.rows;
          const hasMatch = conditionPrefix && rows.some(function (entry) { return String(entry.code || "").toUpperCase().startsWith(conditionPrefix); });
          return renderLegendSection(formatConditionSectionTitle(group.label, letter), rows, "Condition", {
            collapsed: conditionPrefix ? !hasMatch : true,
            highlightPrefix: conditionPrefix
          });
        });

      return subjectSections
        .concat(conditionSections)
        .concat([
          renderLegendSection("Traffic Codes", trafficRows, "Traffic"),
          renderLegendSection("Scope Codes", scopeRows, "Scope")
        ])
        .filter(Boolean);
    }

    function updateToggleLabels() {
      if (!state.bodyEl) return;
      const sections = state.bodyEl.querySelectorAll(".q-legend-section");
      sections.forEach(function (section) {
        const btn = section.querySelector(".q-legend-toggle");
        if (!btn) return;
        btn.textContent = section.classList.contains("collapsed") ? "Show" : "Hide";
      });

      if (state.showAllBtn) {
        const hasCollapsed = Array.from(sections).some(function (section) { return section.classList.contains("collapsed"); });
        state.showAllBtn.textContent = hasCollapsed ? "Show all" : "Hide all";
      }
    }

    function updateInfo(subjectQuery, conditionQuery) {
      if (!state.infoEl) return;
      const subjectCode = String(subjectQuery || "").replace(/\*/g, "");
      const conditionCode = String(conditionQuery || "").replace(/\*/g, "");
      const subjectMeaning = subjectCode && subjectCode.length === 2 ? getSubjectMeaning(subjectCode) : "";
      const conditionMeaning = conditionCode && conditionCode.length === 2 ? getConditionMeaning(conditionCode) : "";

      if (subjectCode && conditionCode) {
        state.infoEl.textContent = subjectCode + conditionCode + " = " + (subjectMeaning || "Unknown subject") + ", " + (conditionMeaning || "Unknown condition");
      } else if (subjectCode) {
        state.infoEl.textContent = subjectCode + " = " + (subjectMeaning || "Unknown subject") + ". Enter a condition to see the pair meaning.";
      } else if (conditionCode) {
        state.infoEl.textContent = conditionCode + " = " + (conditionMeaning || "Unknown condition") + ". Enter a subject to see the pair meaning.";
      } else {
        state.infoEl.textContent = "Enter both subject and condition codes to see a combined meaning.";
      }
    }

    function renderCurrent() {
      if (!state.bodyEl) return;
      const rawSubject = state.subjectInput ? state.subjectInput.value : "";
      const rawCondition = state.conditionInput ? state.conditionInput.value : "";
      const subjectQuery = normalizeQuery(rawSubject);
      const conditionQuery = normalizeQuery(rawCondition);
      const sections = getSections(subjectQuery, conditionQuery);

      state.bodyEl.innerHTML = sections.length
        ? sections.join("")
        : '<p class="q-legend-note">No legend entries match your search.</p>';

      updateToggleLabels();
      updateInfo(subjectQuery, conditionQuery);
    }

    function bindUi(binding) {
      state.bodyEl = binding.bodyEl || null;
      state.infoEl = binding.infoEl || null;
      state.subjectInput = binding.subjectInput || null;
      state.conditionInput = binding.conditionInput || null;
      state.clearBtn = binding.clearBtn || null;
      state.showAllBtn = binding.showAllBtn || null;

      if (state.subjectInput) {
        state.subjectInput.addEventListener("input", function () {
          state.subjectInput.value = normalizeQuery(state.subjectInput.value);
          renderCurrent();
        });
      }

      if (state.conditionInput) {
        state.conditionInput.addEventListener("input", function () {
          state.conditionInput.value = normalizeQuery(state.conditionInput.value);
          renderCurrent();
        });
      }

      if (state.clearBtn) {
        state.clearBtn.addEventListener("click", function () {
          if (state.subjectInput) state.subjectInput.value = "";
          if (state.conditionInput) state.conditionInput.value = "";
          renderCurrent();
          if (state.subjectInput) state.subjectInput.focus();
        });
      }

      if (state.bodyEl && !state.bodyEl.dataset.toggleBound) {
        state.bodyEl.dataset.toggleBound = "1";
        state.bodyEl.addEventListener("click", function (event) {
          const target = event.target;
          if (!(target instanceof Element)) return;
          if (!target.classList.contains("q-legend-toggle")) return;
          const section = target.closest(".q-legend-section");
          if (!section) return;
          section.classList.toggle("collapsed");
          updateToggleLabels();
        });
      }

      if (state.showAllBtn && !state.showAllBtn.dataset.bound) {
        state.showAllBtn.dataset.bound = "1";
        state.showAllBtn.addEventListener("click", function () {
          if (!state.bodyEl) return;
          const sections = Array.from(state.bodyEl.querySelectorAll(".q-legend-section"));
          const hasCollapsed = sections.some(function (section) { return section.classList.contains("collapsed"); });
          sections.forEach(function (section) {
            section.classList.toggle("collapsed", !hasCollapsed);
          });
          updateToggleLabels();
        });
      }

      renderCurrent();
    }

    function getSubjectMeaning(code) {
      return state.subjectMap.get(String(code || "").toUpperCase()) || "";
    }

    function getConditionMeaning(code) {
      return state.conditionMap.get(String(code || "").toUpperCase()) || "";
    }

    function hasSubject(code) {
      return state.subjectMap.has(String(code || "").toUpperCase());
    }

    function hasCondition(code) {
      return state.conditionMap.has(String(code || "").toUpperCase());
    }

    function getSubjectCategoryTooltip(letter) {
      const raw = SUBJECT_CATEGORY_LABELS[String(letter || "").toUpperCase()] || "Other";
      return stripTrailingCategoryLetter(normalizeSubjectCategoryLabel(raw, letter));
    }

    function getSubjectCodes() {
      return subjectCodes.slice();
    }

    function getConditionCodes() {
      return conditionCodes.slice();
    }

    async function loadData() {
      try {
        const responses = await Promise.all([
          fetch(dataSources.subjects, { cache: "no-store" }),
          fetch(dataSources.conditions, { cache: "no-store" })
        ]);

        if (!responses[0].ok || !responses[1].ok) {
          rebuildMaps();
          return false;
        }

        const subjectsData = await responses[0].json();
        const conditionsData = await responses[1].json();

        if (Array.isArray(subjectsData) && subjectsData.length) {
          subjectCodes = subjectsData
            .filter(function (entry) { return entry && typeof entry.code === "string"; })
            .map(function (entry) {
              return {
                code: String(entry.code || "").toUpperCase().trim(),
                meaning: String(entry.meaning || "").trim(),
                category: String(entry.category || "").trim()
              };
            })
            .filter(function (entry) { return entry.code.length === 2; });
        }

        applySubjectCustomRows();

        if (Array.isArray(conditionsData) && conditionsData.length) {
          conditionCodes = conditionsData
            .filter(function (entry) { return entry && typeof entry.code === "string"; })
            .map(function (entry) {
              return {
                code: String(entry.code || "").toUpperCase().trim(),
                meaning: String(entry.meaning || "").trim(),
                category: String(entry.category || "").trim()
              };
            })
            .filter(function (entry) { return entry.code.length === 2; });
        }

        rebuildMaps();
        renderCurrent();
        return true;
      } catch (error) {
        rebuildMaps();
        return false;
      }
    }

    applySubjectCustomRows();
    rebuildMaps();

    return {
      bindUi: bindUi,
      render: renderCurrent,
      loadData: loadData,
      getSubjectMeaning: getSubjectMeaning,
      getConditionMeaning: getConditionMeaning,
      hasSubject: hasSubject,
      hasCondition: hasCondition,
      getSubjectCategoryTooltip: getSubjectCategoryTooltip,
      getSubjectCodes: getSubjectCodes,
      getConditionCodes: getConditionCodes
    };
  }

  window.QCodeLegend = {
    createController: createController
  };
})();
