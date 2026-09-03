# Advanced RPAS — Batch 1 Review

## Repository write status
No GitHub repository files were changed. The GitHub connector returned HTTP 403 when asked to create the staging file.

## Batch 1 disposition
- Reviewed: 10 complete questions recovered from `DQ-2026-08-27-01`
- Accepted for merge review: 6
- Held for semantic-duplicate review: 4

### Accepted
1. Q01 — TC AIM “should” vs “shall”
2. Q03 — CAR 901.19: 12-hour alcohol boundary
3. Q06 — CAR 901.35: icing exception
4. Q07 — CAR 901.65: 24-month Advanced recency
5. Q09 — TC AIM expanded Advanced privileges: sheltered + EVLOS
6. Q10 — CAR 901.47(4): DND aerodrome authorization

### Held
- Q02 — RPA vs RPAS definition
- Q04 — visual-observer reliable/timely communication
- Q05 — CAR 901.27 site-survey person-distance factor
- Q08 — declaration + ATS authorization; overlaps Phase 6 material

## Reference-integrity findings
- Justice Laws CARs pages used for validation show the regulations current to 2026-06-21 and last amended 2026-06-17.
- TC AIM RPA 2026-1 remains the current Transport Canada RPA chapter located on the current AIM page, effective 2026-03-19.
- CNOP Version 12 is current, effective 2026-05-14; NAV CANADA lists the next issue for 2026-10-29.
- `references.json` currently has no dedicated CNOP registry entry. Add one before importing NOTAM/CNOP-derived questions.
- The stored DAH reference points to Issue 322, effective 2026-07-09 to 2026-09-03. NAV CANADA's operational-guides page was still serving that file as “current” during this check even though the document itself expires at 0901Z 2026-09-03. Do not silently replace it with an assumed new filename; mark it stale/pending resolution until NAV CANADA serves the successor issue.
