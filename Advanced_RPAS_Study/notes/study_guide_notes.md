# Advanced RPAS Study Guide Notes

Last updated: 2026-08-29

## Reference hierarchy

1. **Aeronautics Act** and **Justice Laws — CARs Part IX**: authoritative legal sources.
2. **TP 15263 / TP 15530**: official exam knowledge-requirement blueprints — use these to scope and structure quiz categories/difficulty, since they state exactly what each exam tests.
3. **Transport Canada Drone Pilot Study Resources**: master official study-resource index.
4. **Transport Canada CARs index**: navigation.
5. **TC AIM (TP 14371)**: operational explanation and study context (RPA chapter held locally; other chapters — RAC, MET, AGA, etc. — available on demand).
6. **TP 12863 / TP 12864 (Human Factors handbooks)**: source for the human-factors category.
7. **RPAS 101**: explanatory study guide.
8. **NAV CANADA publications**: operational aeronautical information (CFS, VNC/VTA, DAH, VFR Phraseology Guide).
9. **ROC-A study guide (RIC-21)**: radio/phraseology licensing reference.

When sources conflict, prefer current CARs and current official Transport Canada / NAV CANADA material.

## Gold-source document policy

- `data/references.json` is the index of record: every reference entry should have a `url` (source of truth) and, where the document is freely redistributable, a `localCopy` path into `docs/` plus a `pdfUrl` for the direct file.
- Paid/licensed NAV CANADA products (VNC, VTA, CFS, CWAS, DAH) are cited by URL only — no local copy, since they aren't freely downloadable.
- `docs/` currently holds: Aeronautics Act, TC AIM 2026-1 RPA chapter, TP 15263, TP 15530, NAV CANADA VFR Phraseology Guide.
- Any regulatory citation used in a quiz question should be spot-checked against its gold source before being trusted for exam prep — AI-drafted citations are a starting point, not verified fact until checked.

## Study system

The project uses quizzes for two purposes:

1. Build a reusable library of exam-like questions covering all Canadian Advanced RPAS knowledge areas.
2. Identify knowledge gaps and reinforce weak concepts until mastered.

Track:
- Category / domain
- Difficulty
- Source / regulatory basis
- Correct answer and rationale
- Performance by category
- Missed concepts and reinforcement status
- Mastery status
- Last tested / last verified dates

## Current recurring reinforcement targets

- NOTAM Q-line vertical limits / flight-level interpretation
- Division V controlled-airspace authorization vs operations requiring an SFOC-RPAS

## Quiz app development log

- **2026-08-28**: Pilot batch of 12 questions seeded for the `regulations` category in `data/questions.json` (schemaVersion 2). Built adaptive quiz engine in `quiz.html`: weighted random question selection favoring categories/questions with lower recorded accuracy, per-category/per-question stats stored in browser `localStorage`, and an "export round" button producing a JSON snippet in `progress.json`'s session shape (no server-side write from a static site, so export is manual-merge only).
- **2026-08-29**: Confirmed TP 15263 (Basic/Advanced) and TP 15530 (Level 1 Complex) are the official exam blueprints; downloaded both PDFs plus the free NAV CANADA VFR Phraseology guide into `docs/`. Expanded `references.json` with real, verified URLs (Aeronautics Act, TP 15263/15530, TP 12863/12864, ROC-A guide, NAV CANADA products/phraseology, full TC AIM chapter index).
- **2026-08-29 (later)**: Generated a full pass across all 14 categories in `questions.json` — 540 questions total, mixed easy/medium/hard/tricky difficulty, each with rationale + source citation. Category counts flex (20-50) based on topic breadth rather than forcing an artificial uniform count. Validated JSON structure and confirmed no duplicate IDs.
- **Known gaps / next steps**:
  - Regulatory/technical citations were AI-drafted from general knowledge of CARs Part IX / TP 15263 / TP 15530 structure and have **not** been individually spot-verified against the gold-source PDFs in `docs/` — recommend a verification pass before treating this bank as exam-ready.
  - `radio` (20), `abnormal` (25), `flight-planning` (25), `navigation` (25), `visual-observers` (30) could be expanded further if targeted study reveals gaps.
  - The adaptive quiz engine (`quiz.html`) has not yet been tested against the full 540-question bank — recommend a run-through to confirm performance/UX at this scale.
  - `progress.json` still only tracks round-level scores; consider extending its schema to log per-category accuracy trends over time, feeding back into the quiz's weighting beyond browser-local `localStorage`.
- **2026-08-29 (CARs deep-linking)**: Downloaded the full CARs regulation as gold-source PDF (`docs/CARs_SOR-96-433_FullText.pdf`) and XML (`docs/CARs_SOR-96-433_FullText.xml`) from Justice Laws. Confirmed the Justice Laws full-text page uses anchors in the form `#s-901.27`, matching the user's requested deep-link format. Added `sectionUrlTemplate` to the `ref-justice-cars` entry in `references.json` (`.../FullText.html#s-{section}`). `quiz.html` now renders a clickable "CARs 901.27"-style link in the answer feedback whenever a question has an optional `carsSection` field, via the new `carsSectionLink()` helper.
  - Parsed the local XML to verify real section numbers for a handful of topics already covered in `questions.json`, and tagged 5 questions with confirmed `carsSection` values: `reg-003` → 901.40 (Advertised Events), `reg-017` → 901.87 (Requirement for RPAS Operator Certificate), `vo-001` → 901.19 (Visual Observers), `fp-001`/`fp-002` → 901.26/901.27 (Site Survey).
  - **Remaining work**: the other ~535 questions still cite CARs only by general Part IX/Division description, not a specific verified section number. Adding `carsSection` further should only be done after confirming the exact section against `CARs_SOR-96-433_FullText.xml` (or the PDF) — do not guess/invent specific section numbers, since a wrong but confident-looking clickable citation is worse than no citation.
- **2026-08-31 (DAH citation correction)**: User flagged that the CYR/CYA Class F airspace questions (`air-005`, `air-006`) cited only a generic NAV CANADA product catalogue page, which isn't a real regulatory "shall/shall not" source. Parsed the local CARs XML for the actual chain: **CARs 601.01** lists restricted/advisory/danger airspace as recognized types; **601.02** classifies Class F as "Special Use Restricted" or "Special Use Advisory" (both "as specified in the Designated Airspace Handbook"); **601.04(2)** is the actual enforceable rule — "No person shall operate an aircraft in Class F Special Use Restricted airspace unless authorized..."; **900.07** (Part IX) is the RPAS-specific inadvertent-entry notification duty, also referencing the DAH by name. Both questions now cite these real sections with working `carsSection` deep-links instead of the generic NAV CANADA page. Confirmed no dedicated free NAV CANADA DAH landing page exists (checked two plausible URL patterns, both 404) — `ref-navcanada-products` notes updated to say so explicitly and point to the CARs sections as the actual regulatory basis.
  - **New local dataset**: `docs/CARs_Part_IX_quiz_reference.json` (Part IX only) and `docs/CARs_quiz_reference.jsonl` (full CARs, ~1,643 sections, one JSON object per line) were produced while investigating this — these map every CARs section number to its exact text and are useful for future `carsSection` verification passes without re-parsing the raw XML each time.
- **2026-08-31 (DAH gold source found)**: The DAH turns out to be a **free** publication after all — found via NAV CANADA's Operational Guides page (`https://www.navcanada.ca/en/aeronautical-information/operational-guides.aspx`), not the paid-product catalogue page used earlier. Downloaded the current issue (effective 2026-07-09, 216 pages) to `docs/NAVCANADA_DAH_current_20260709.pdf`. Added a dedicated `ref-navcanada-dah` entry in `references.json` with `pdfUrl`/`localCopy`, separate from `ref-navcanada-products` (which now only covers the genuinely paid VNC/VTA/CFS/CWAS products). `quiz.html`'s source-linkification map now points "Designated Airspace Handbook" and "DAH" mentions at this specific entry.
  - **Staleness risk**: NAV CANADA posts a new DAH issue periodically (next issue was already published at time of writing: `dah20260903.pdf`, effective 2026-09-03). The operational-guides page always shows "Current Issue" / "Next Issue" links — `localCopy` will go stale and should be periodically re-downloaded and the `lastVerified`/URL updated.
  - **Derived lookup index**: extracted `docs/DAH_area_index.json` — 241 unique Class F area codes (CYR/CYA/CYD-style) found via regex scan of the PDF text, each with the PDF page number and a short snippet, using `docs/extract_dah_index.py` (kept for re-running against future DAH issues). This isn't a fully structured table parse (PDF table layout doesn't convert perfectly to plain text), but it's enough to jump straight to the right page for a specific area code instead of searching all 216 pages manually.
