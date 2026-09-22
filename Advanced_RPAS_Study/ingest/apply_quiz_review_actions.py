#!/usr/bin/env python3
"""Apply exported quiz review approvals to data/questions.json.

Usage:
    python ingest/apply_quiz_review_actions.py path/to/quiz-review-actions.json --dry-run
    python ingest/apply_quiz_review_actions.py path/to/quiz-review-actions.json

The browser quiz runs on static GitHub Pages, so it cannot write questions.json directly.
This script applies the downloaded review-actions JSON locally, backs up questions.json,
and removes approved reviewFlags from matching questions.
"""

import argparse
import json
import shutil
from collections import Counter
from datetime import date, datetime
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("actions_json", help="Downloaded quiz-review-actions.json file")
    parser.add_argument("--dry-run", action="store_true", help="Report changes without writing questions.json")
    args = parser.parse_args()

    repo = Path(__file__).resolve().parents[1]
    qpath = repo / "data" / "questions.json"
    backup_dir = repo / "ingest" / "backups"
    actions_path = Path(args.actions_json)

    data = json.loads(qpath.read_text(encoding="utf-8-sig"))
    payload = json.loads(actions_path.read_text(encoding="utf-8-sig"))
    approvals = payload.get("approvals") or []
    by_id = {q["id"]: q for q in data["questions"]}

    missing = []
    changed = []
    removed_counts = Counter()
    reviewed_sets = Counter()

    for approval in approvals:
        qid = approval.get("id")
        if qid not in by_id:
            missing.append(qid)
            continue

        question = by_id[qid]
        before = list(question.get("reviewFlags") or [])
        remove = set(approval.get("clearedFlags") or [])
        after = [flag for flag in before if flag not in remove]
        removed = [flag for flag in before if flag in remove]

        reviewed = set(approval.get("reviewedSets") or [])

        if removed:
            if after:
                question["reviewFlags"] = after
            else:
                question.pop("reviewFlags", None)
            removed_counts.update(removed)

        if reviewed:
            question["reviewedSets"] = sorted(set(question.get("reviewedSets") or []) | reviewed)
            reviewed_sets.update(reviewed)

        if removed or reviewed:
            changed.append(qid)

    print(f"Approvals in file: {len(approvals)}")
    print(f"Questions changed: {len(changed)}")
    if removed_counts:
        print("Removed reviewFlags:")
        for flag, count in sorted(removed_counts.items()):
            print(f"  {flag}: {count}")
    if reviewed_sets:
        print("Reviewed non-reviewFlag sets:")
        for label, count in sorted(reviewed_sets.items()):
            print(f"  {label}: {count}")
    if missing:
        print(f"Missing question ids: {', '.join(str(x) for x in missing)}")

    if args.dry_run:
        print("DRY RUN - no questions.json changes made.")
        return

    if not changed:
        print("No review actions to apply; questions.json unchanged.")
        return

    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = backup_dir / f"questions_before_review_actions_{stamp}.json"
    shutil.copy2(qpath, backup)

    data["updated"] = date.today().isoformat()
    data["lastUpdated"] = date.today().isoformat()
    note = (
        f"{date.today().isoformat()} QUIZ REVIEW: applied review approvals to "
        f"{len(changed)} questions using {actions_path.name}."
    )
    if note not in data.setdefault("migrationNotes", []):
        data["migrationNotes"].append(note)

    qpath.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Updated: {qpath}")
    print(f"Backup: {backup}")


if __name__ == "__main__":
    main()
