# Advanced RPAS Chat Quiz Ingest

Copy the `ingest` folder into:

`C:\Users\Ron Treleaven\Drone_SOP\Advanced_RPAS_Study\`

Result:

```text
Advanced_RPAS_Study/
├─ data/
│  ├─ questions.json
│  └─ references.json
└─ ingest/
   ├─ README.md
   ├─ backups/
   ├─ batch1/
   │  ├─ Batch1_questions_merge_fragment.json
   │  ├─ Batch1_DQ-2026-08-27-01_review.json
   │  ├─ Batch1_reference_integrity.md
   │  └─ Merge_Batch1.py
   └─ batch2/
      ├─ Batch2_questions_merge_fragment.json
      ├─ Batch2_review.md
      └─ Merge_Batch2.py
```

## Recommended workflow

From PowerShell:

```powershell
cd "C:\Users\Ron Treleaven\Drone_SOP\Advanced_RPAS_Study"

python .\ingest\batch1\Merge_Batch1.py --dry-run
python .\ingest\batch2\Merge_Batch2.py --dry-run
```

Review the reported question IDs and counts first.

Then merge:

```powershell
python .\ingest\batch1\Merge_Batch1.py
python .\ingest\batch2\Merge_Batch2.py
```

Each real merge:
- validates the fragment
- skips question IDs already in `questions.json`
- backs up `questions.json` into `ingest/backups/`
- appends only new questions
- updates `totalQuestions`
- updates the file date
- appends a migration note

## Scope policy

Core Advanced exam questions must map to TP 15263 Advanced knowledge requirements.

Primary authority hierarchy:
1. TP 15263 — exam scope / learning objective
2. Canadian Aviation Regulations, especially Part IX — legal requirement
3. TC AIM, especially RPA — official operational interpretation
4. NAV CANADA / ISED / other official sources only where required by the TP 15263 topic

Supplemental questions may remain in the bank but should be excluded from normal Advanced Exam Mode.
