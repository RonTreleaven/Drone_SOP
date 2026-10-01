# Advanced RPAS Question Batch Log

This log records additional-question batches for the Advanced RPAS quiz bank and defines the standard future workflow.

Trigger phrase:

`Generate Additional Questions for our Adv Drone Quiz`

When that phrase is used, continue from this log and the current live repo state. The goal is to generate a reviewed candidate pool, duplicate-screen it against the live question bank, and merge only accepted survivors into `data/questions.json`.

## Canonical Files

- Repo: `C:\Users\Ron Treleaven\Drone_SOP`
- Study app: `Advanced_RPAS_Study`
- Live bank: `Advanced_RPAS_Study/data/questions.json`
- References: `Advanced_RPAS_Study/data/references.json`
- Batch folders: `Advanced_RPAS_Study/ingest/batchN`
- Backups: `Advanced_RPAS_Study/ingest/backups`

Do not use the OneDrive study folder as the canonical repo.

## Standard Workflow

1. Check repository state:
   - `git status --short`
   - `git branch --show-current`
   - `git log -5 --oneline`
2. Inspect the live question bank:
   - total question count
   - `examScope` counts
   - category counts for `core-advanced`
   - latest `migrationNotes`
3. Create or continue the next batch folder under `ingest/`.
4. Generate more candidate questions than the target merge count.
5. Save candidates as `BatchN_candidate_pool.json` with `categoryTargets`.
6. Use the existing Batch 3/4 merge-script pattern:
   - validate required fields
   - reject duplicate IDs
   - reject near-duplicate stems against the live bank and within the batch
   - enforce category targets
   - write a dry-run audit JSON
   - prefer the reusable helper: `python .\ingest\merge_question_batch.py .\ingest\batchN\BatchN_candidate_pool.json --dry-run`
7. Inspect the dry-run audit before merging.
8. Merge only selected survivors:
   - back up `data/questions.json`
   - append selected questions
   - update `totalQuestions`, `updated`, and `migrationNotes`
9. Validate JSON, IDs, counts, scope, and category distribution.
10. Update this log with generated, selected, rejected, audit, backup, validation, and remaining concerns.

## Required Fields For New Questions

Each merged question should include:

- `id`
- `category`
- `difficulty`
- `question`
- `choices`
- `answerIndex`
- `rationale`
- `source`
- `sourceRefs`
- `exactRefs`
- `lastVerified`
- `examScope`
- `examLevel`
- `tp15263Section`
- `knowledgeArea`
- `knowledgeTopic`
- `learningObjective`

Every generated candidate should include at least one `exactRefs` entry.

## Scope Policy

Default Advanced study-pool questions use:

- `examScope: "core-advanced"`
- or `examScope: "core-basic-advanced"` when the tested knowledge is genuinely shared by Basic and Advanced.

Do not place BVLOS, Level 1 Complex, TP 15530, DAA-system, or RPOC material in the default pool. Those belong under `examScope: "level-1-complex"` or in a held/supplemental candidate file unless explicitly requested.

Primary source hierarchy:

1. TP 15263 for exam scope and learning objectives.
2. Canadian Aviation Regulations, especially Part IX, for legal requirements.
3. TC AIM for official operational interpretation and context.
4. NAV CANADA / ISED / other official sources where the TP 15263 topic requires them.

## Known Weak / High-Value Topics

Prioritize scenario-driven questions on:

- inclusive vs exclusive regulatory boundaries
- visual observers and EVLOS
- altitude limits and obstacle/structure exceptions
- Class F CYA/CYD/CYR interpretation
- NOTAM Q-line, Q-code, geographical reference, radius, timing, and vertical-limit interpretation
- weather minima and deteriorating conditions
- airport, heliport, aerodrome, and controlled-airspace procedures
- person-distance and bystander rules
- RPAS records, serviceability, defects, and modifications
- ATC authorization and compliance with instructions
- site survey requirements and publication currency
- emergency, contingency, lost-link, and flyaway procedures
- collision avoidance, right-of-way, and crew responsibility
- night and EVLOS privileges
- authoritative-source interpretation

## Batch History

### Batch 1 - 2026-09-03

- 10 recovered questions reviewed.
- 6 accepted.
- 4 held.
- See `ingest/batch1/`.

### Batch 2 - 2026-09-03

- 20 reviewed.
- 10 accepted.
- 10 held or excluded.
- Common rejection reasons: duplicates, BVLOS / Level 1 Complex scope, weakly supported EVLOS wording, ambiguous regulatory mapping.
- See `ingest/batch2/`.

### Batch 3 - 2026-09-22

- Local duplicate-screened ingest.
- 112 candidates reviewed.
- 99 TP 15263 core-Advanced questions selected and merged.
- 2 rejected as near duplicates.
- 1-question aerodromes shortfall.
- Audit: `ingest/batch3/Batch3_dryrun_audit.json`.
- Backup: `ingest/backups/questions_before_batch3_20260922_082118.json`.

### Batch 3 Leftovers - 2026-09-22

- 10 reviewed leftover questions added.
- Forest-fire NOTAM candidate `b3-nota-008` omitted by review decision.

### Batch 4 - 2026-09-06 to 2026-09-08

- `Batch4_candidate_pool.json`: 96 selected from 100 candidates.
- `Batch4b_candidate_pool.json`: 200 selected from 250 candidates.
- `VNC_VTA_legend_candidate_pool.json`: 4 selected from 4 candidates.
- See `ingest/batch4/`.

### Batch 5 Plan - 2026-09-22

- Existing plan for 51 additional questions.
- Prioritizes `theory-of-flight`, abnormal, visual observers, human factors, maintenance, aircraft systems, NOTAMs, safety, aerodromes, flight planning, and radio.
- See `ingest/batch5/Batch5_51_question_gap_plan.md`.

### Batch 6 Request - 2026-10-01

- User initially requested an additional 100 questions across all categories, then requested 50 questions for the first merge.
- Focus should include known weak/high-value topics listed above.
- Current observed live bank before new generation:
  - total questions: 1125
  - `core-advanced`: 480
  - `core-basic-advanced`: 348
  - `level-1-complex`: 296
  - `supplemental`: 1
- Existing uncommitted local change before this workflow work:
  - `Advanced_RPAS_Study/CARs_Part_IX_English.html`
- Next action:
  - create `ingest/batch6/`
  - generate a candidate pool larger than requested merge target
  - dry-run duplicate screening
  - merge exactly the requested survivor count only after audit review, unless the user approves a shortfall

### Batch 6 Merge - 2026-10-01

- Request: `Generate 50 Additional Questions for our Adv Drone Quiz and update the question.json`.
- Candidate pool: `ingest/batch6/Batch6_candidate_pool.json`.
- Candidate generator: `ingest/batch6/build_batch6_pool.py`.
- Candidates generated: 59.
- Target selected/merged: 50.
- Selected after duplicate screening: 50.
- Near-duplicate rejections: 0.
- Shortfalls: none.
- Audit: `ingest/batch6/Batch6_dryrun_audit.json`.
- Backup: `ingest/backups/questions_before_Batch6_candidate_pool_20261001_113721.json`.
- Live bank after merge:
  - total questions: 1175
  - `data/questions.json` `totalQuestions`: 1175
  - `updated`: 2026-10-01
- Batch 6 category mix:
  - `theory-of-flight`: 5
  - `visual-observers`: 4
  - `notams`: 4
  - `abnormal`: 4
  - `human-factors`: 4
  - `maintenance`: 4
  - `aircraft-systems`: 4
  - `safety`: 4
  - `aerodromes`: 3
  - `flight-planning`: 3
  - `radio`: 3
  - `airspace`: 3
  - `navigation`: 3
  - `weather`: 1
  - `regulations`: 1
- Validation performed:
  - `python -m json.tool .\data\questions.json`
  - duplicate ID check: 0 duplicates
  - Batch 6 required `exactRefs`: 0 missing
  - Batch 6 choice/answer-index check: 0 invalid
  - default-pool Level 1/BVLOS marker check: 0 markers
- Remaining concerns:
  - No unresolved source/scope concerns identified in this merge.
  - Existing unrelated local change remains: `Advanced_RPAS_Study/CARs_Part_IX_English.html`.
