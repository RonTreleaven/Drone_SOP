# Batch 5 Gap Plan - 51 Additional Advanced RPAS Questions

Date: 2026-09-22

## Current Result

Batch 3 was merged after duplicate screening.

- Starting bank: 1,016 questions
- Batch 3 candidates reviewed: 112
- Batch 3 selected and merged: 99
- Batch 3 rejected as near duplicates: 2
- Batch 3 shortfall: 1 aerodromes question
- New bank total: 1,115 questions
- Backup: `ingest/backups/questions_before_batch3_20260922_082118.json`
- Audit: `ingest/batch3/Batch3_dryrun_audit.json`

The original 150-question objective now needs 51 additional reviewed questions.

## Quiz Data Requirements

The quiz app loads:

- `data/~tmp40_categories.json`
- `data/questions.json`
- `data/references.json`

Each new question should include:

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

Use `examScope: "core-advanced"` or `examScope: "core-basic-advanced"` for the default Advanced study pool.

Do not place BVLOS, Level 1 Complex, TP 15530, or detect-and-avoid material in the default pool. Those belong under `examScope: "level-1-complex"`.

### Exact Reference Standard

Use `sourceRefs` for linkable document IDs or source labels. Use `exactRefs` for the precise source row, section, or topic the student should see after answering.

Example:

```json
"source": "TP 15263 Sections 1 and 8; CARs 901.72",
"sourceRefs": ["ref-tp-15263", "ref-justice-cars"],
"exactRefs": [
  {
    "source": "TP 15263",
    "section": "1",
    "sectionTitle": "Air law, air traffic rules and procedures",
    "topic": "ATC clearances/instructions/mandatory read back procedures"
  },
  {
    "source": "TP 15263",
    "section": "8",
    "sectionTitle": "Radiotelephony",
    "topic": "Communications - Common frequencies",
    "objective": "List the contents of a routine call to ATC."
  },
  {
    "source": "CARs",
    "section": "901.72",
    "title": "Compliance with air traffic control instructions"
  }
]
```

For Batch 5, every generated candidate should include at least one `exactRefs` entry. Questions based on TP 15263 should include the exact section/topic/objective row where practical. Questions based on CARs/AIM should include the precise section/subsection title and a short quote only if it is needed to make the answer evidence clear.

## Batch 5 Target Mix

Batch 5 should prioritize weak categories and TP 15263 coverage gaps rather than repeating weather, navigation, or regulations.

| Category | Target | Reason |
| --- | ---: | --- |
| `theory-of-flight` | 18 | The live bank had only 1 question before Batch 3 and Batch 3 does not cover this category. |
| `abnormal` | 5 | Low current count; important for lost-link, fly-away, contingency, emergency decision-making. |
| `visual-observers` | 4 | Low current count; important Advanced operations crew coordination topic. |
| `human-factors` | 4 | Low current count; TP 15263 Section 3 has broad objectives. |
| `maintenance` | 4 | Low current count; useful for records, serviceability, defects, and post-maintenance checks. |
| `aircraft-systems` | 4 | Supports TP 15263 Section 2 and pairs well with theory of flight. |
| `notams` | 3 | Reinforces operational planning and active restrictions. |
| `safety` | 3 | Reinforces right-of-way, collision avoidance, public safety, and risk controls. |
| `aerodromes` | 2 | Closes the Batch 3 one-question aerodromes shortfall and adds one extra scenario. |
| `flight-planning` | 2 | Supports site survey and operational volume scenarios. |
| `radio` | 2 | Keeps phraseology and ATS communication represented. |

Total: 51

## Proposed Sources

Primary:

- TP 15263, especially Sections 2, 3, 6, 7, and 8
- CARs Part IX, especially operational limitations, visual observers, emergency procedures, records, and pilot responsibilities
- TC AIM RPA and RAC where operational context is needed

Supporting:

- CARs Part VI for aerodrome, MF, airspace, NOTAM, and emergency/context questions
- NAV CANADA references for NOTAM and chart-use questions

## Merge Workflow

1. Create `ingest/batch5/Batch5_candidate_pool.json` with at least 60 candidates for a target merge of 51.
2. Include `categoryTargets` matching the target mix above.
3. Reuse the Batch 3/4 duplicate-screening logic:
   - reject duplicate IDs
   - reject high semantic similarity against the live bank and within Batch 5
   - validate required fields
   - validate at least one `exactRefs` entry
   - validate four choices and valid `answerIndex`
4. Dry run first and inspect `Batch5_dryrun_audit.json`.
5. Merge only the surviving 51, or merge a shortfall only after review.
6. Back up `data/questions.json` before writing.
7. Update `totalQuestions`, `updated`, and `migrationNotes`.

## Suggested ID Prefixes

Use `b5-` IDs with category hints:

- `b5-theory-001`
- `b5-abn-001`
- `b5-vo-001`
- `b5-hf-001`
- `b5-maint-001`
- `b5-sys-001`
- `b5-notam-001`
- `b5-safety-001`
- `b5-aero-001`
- `b5-fp-001`
- `b5-radio-001`
