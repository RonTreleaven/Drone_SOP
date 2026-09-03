# Batch 3 — 100-question Advanced RPAS expansion

Batch 3 contains **112 candidates**. `Merge_Batch3.py` compares them against your actual local
`data/questions.json` and selects **100 non-duplicate questions** according to these category targets:

```json
{
  "regulations": 8,
  "airspace": 8,
  "aerodromes": 8,
  "notams": 7,
  "weather": 8,
  "visual-observers": 6,
  "human-factors": 7,
  "aircraft-systems": 8,
  "maintenance": 6,
  "abnormal": 6,
  "flight-planning": 8,
  "radio": 7,
  "navigation": 7,
  "safety": 6
}
```

## Dry run first

```powershell
cd "C:\Users\Ron Treleaven\Drone_SOP\Advanced_RPAS_Study"
python .\ingest\batch3\Merge_Batch3.py --dry-run
```

Review:

`ingest\batch3\Batch3_dryrun_audit.json`

The default near-duplicate threshold is `0.72`. The audit records the closest existing question for
each rejected near-duplicate.

## Merge

Only merge if the dry run reports `100 / 100`:

```powershell
python .\ingest\batch3\Merge_Batch3.py
```

If fewer than 100 survive, the script refuses to change `questions.json` by default. That is intentional:
the shortfall should be filled with new questions rather than weakening duplicate controls.

## Scope

- TP 15263 Fourth Edition (03/2025) defines exam scope.
- CARs / Justice Laws is the legal authority for regulatory questions.
- TC AIM is supporting operational guidance.
- NAV CANADA and RIC-21 are used where TP 15263 calls for those subjects.
- Level 1 Complex/BVLOS-specific privilege questions are not part of core Advanced Exam Mode.
