#!/usr/bin/env python3
"""Merge Batch 1 reviewed questions into Advanced_RPAS_Study/data/questions.json.

Usage:
    python Merge_Batch1.py --dry-run
    python Merge_Batch1.py

The script:
- locates the repository root relative to this file
- validates required question fields
- skips existing question IDs
- creates a timestamped backup of questions.json before a real merge
- updates totalQuestions, updated, and migrationNotes
"""
import argparse
import json
import shutil
from datetime import datetime, date
from pathlib import Path

REQUIRED_FIELDS = {
    "id", "category", "difficulty", "question", "choices",
    "answerIndex", "rationale", "examScope", "knowledgeArea",
    "knowledgeTopic", "learningObjective", "source", "sourceRefs",
    "lastVerified"
}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Validate and report without modifying questions.json")
    args = parser.parse_args()

    script_path = Path(__file__).resolve()
    repo = script_path.parents[2]
    questions_path = repo / "data" / "questions.json"
    fragment_path = script_path.with_name("Batch1_questions_merge_fragment.json")

    if not questions_path.exists():
        raise FileNotFoundError(f"questions.json not found: {questions_path}")
    if not fragment_path.exists():
        raise FileNotFoundError(f"fragment not found: {fragment_path}")

    data = json.loads(questions_path.read_text(encoding="utf-8"))
    fragment = json.loads(fragment_path.read_text(encoding="utf-8"))

    if "questions" not in data or not isinstance(data["questions"], list):
        raise ValueError("questions.json does not contain a questions array")
    if "questions" not in fragment or not isinstance(fragment["questions"], list):
        raise ValueError("merge fragment does not contain a questions array")

    existing_ids = {q.get("id") for q in data["questions"]}
    new_questions = []

    for q in fragment["questions"]:
        missing = REQUIRED_FIELDS.difference(q)
        if missing:
            raise ValueError(f"{q.get('id', '<unknown>')} missing required fields: {sorted(missing)}")
        if not isinstance(q["choices"], list) or len(q["choices"]) != 4:
            raise ValueError(f"{q['id']} must have exactly four choices")
        if not isinstance(q["answerIndex"], int) or not 0 <= q["answerIndex"] < len(q["choices"]):
            raise ValueError(f"{q['id']} has invalid answerIndex")
        if q["id"] not in existing_ids:
            new_questions.append(q)

    print(f"Batch 1: {len(fragment['questions'])} reviewed merge candidates")
    print(f"Already present: {len(fragment['questions']) - len(new_questions)}")
    print(f"New questions: {len(new_questions)}")
    for q in new_questions:
        print(f"  + {q['id']}  [{q['examScope']}]  {q['knowledgeTopic']}")

    if args.dry_run:
        print("DRY RUN — no files changed.")
        return

    if not new_questions:
        print("Nothing to merge.")
        return

    backup_dir = repo / "ingest" / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"questions_before_batch_1_{stamp}.json"
    shutil.copy2(questions_path, backup_path)

    data["questions"].extend(new_questions)
    data["updated"] = date.today().isoformat()
    data["totalQuestions"] = len(data["questions"])

    migration_notes = data.setdefault("migrationNotes", [])
    migration_note = '2026-09-03 CHAT BATCH 1: Added reviewed historical ChatGPT questions with TP 15263 mappings; TC AIM terminology item tagged supplemental.'
    if migration_note not in migration_notes:
        migration_notes.append(migration_note)

    questions_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8"
    )

    print(f"Merged {len(new_questions)} questions.")
    print(f"New total: {data['totalQuestions']}")
    print(f"Backup: {backup_path}")

if __name__ == "__main__":
    main()
