# Quiz Review Actions Workflow

This folder stores exported QuizReview approval files, usually named:

```text
quiz-review-actions.json
quiz-review-actions (1).json
```

These files are created from `quiz.html` after reviewing questions and choosing **Approve & clear active review flags**.

## Two Ways To Apply Review Approvals

### Option 1 - Export and Apply With Script

This is the safest maintenance workflow.

The browser exports a review-actions JSON file. You then apply it locally with a dry run first:

```powershell
cd "C:\Users\Ron Treleaven\Drone_SOP\Advanced_RPAS_Study"

python .\ingest\apply_quiz_review_actions.py ".\review_actions\quiz-review-actions.json" --dry-run
python .\ingest\apply_quiz_review_actions.py ".\review_actions\quiz-review-actions.json"
```

If the browser saves another file with `(1)` or another suffix:

```powershell
python .\ingest\apply_quiz_review_actions.py ".\review_actions\quiz-review-actions (1).json" --dry-run
python .\ingest\apply_quiz_review_actions.py ".\review_actions\quiz-review-actions (1).json"
```

The script:

- Reads the exported approvals.
- Removes the approved `reviewFlags` from matching questions.
- Adds any `reviewedSets` values, such as `todays-added`.
- Updates `data/questions.json`.
- Creates a backup in `ingest/backups/`.

The script does **not** require port `8765`.

## Option 2 - Local Admin Write API

This lets the browser update `data/questions.json` immediately when you approve a question.

Run:

```powershell
cd "C:\Users\Ron Treleaven\Drone_SOP\Advanced_RPAS_Study"
python .\ingest\serve_quiz_admin.py
```

Then open:

```text
http://127.0.0.1:8765/quiz.html
```

When this mode is active, QuizReview should show that local admin write is enabled. Approvals are written immediately and backups are created.

Port `8765` is required only for this immediate-write browser mode.

## Existing Local Web Server On Port 8000

It is fine to serve the site normally on port `8000`, for example:

```text
http://localhost:8000/Advanced_RPAS_Study/quiz.html
```

The quiz will still work. If the admin API on port `8765` is not running, the page falls back to export-only mode.

Recommended approach:

1. Use port `8000` for normal local browsing and testing.
2. Use QuizReview tools to approve questions.
3. Download the review-actions JSON.
4. Run `apply_quiz_review_actions.py` with `--dry-run`.
5. Run the same command without `--dry-run` if the dry run looks correct.

This gives a clear checkpoint before changing `data/questions.json`.

