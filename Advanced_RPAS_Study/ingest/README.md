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

## Local quiz admin review

GitHub Pages is static, so the hosted quiz cannot write back to `data/questions.json`. On a development PC with the local repo, run the optional local admin server:

```powershell
cd "C:\Users\Ron Treleaven\Drone_SOP\Advanced_RPAS_Study"
python .\ingest\serve_quiz_admin.py
```

Open:

```text
http://127.0.0.1:8765/quiz.html
```

When this server is detected, QuizReview approvals update `data/questions.json` immediately and create a backup under `ingest/backups/`. If the server is not detected, the quiz remains in export-only mode and downloads a review-actions JSON file.

To apply an exported review-actions file manually:

```powershell
python .\ingest\apply_quiz_review_actions.py path\to\quiz-review-actions.json --dry-run
python .\ingest\apply_quiz_review_actions.py path\to\quiz-review-actions.json
```

## Question reference standard

New generated questions should include both document-level references and exact human-readable references.

- `source`: short display citation, such as `TP 15263 Sections 1 and 8; CARs 901.72`
- `sourceRefs`: array of document/reference IDs or concise authority strings used for linking and validation
- `exactRefs`: array of exact rows, sections, titles, objectives, or short quotes that explain the answer

Recommended `exactRefs` shape:

```json
"exactRefs": [
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

Use `sourceRefs` for links to source documents. Use `exactRefs` for what should appear beneath the rationale in the quiz as the precise evidence. Keep any `quote` value short and directly relevant.
