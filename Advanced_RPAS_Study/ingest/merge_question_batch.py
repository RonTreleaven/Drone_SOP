#!/usr/bin/env python3
r"""Merge an Advanced RPAS quiz question candidate pool after duplicate screening.

Dry run:
    python .\ingest\merge_question_batch.py .\ingest\batch6\Batch6_candidate_pool.json --dry-run

Merge:
    python .\ingest\merge_question_batch.py .\ingest\batch6\Batch6_candidate_pool.json

Candidate pools must contain:

{
  "batch": "Batch 6",
  "categoryTargets": {"notams": 8, "...": 0},
  "questions": [...]
}
"""
import argparse
import json
import re
import shutil
from collections import Counter
from datetime import date, datetime
from difflib import SequenceMatcher
from pathlib import Path

STOP = {
    "a", "an", "the", "and", "or", "of", "to", "in", "on", "for", "with", "is", "are",
    "be", "being", "been", "what", "which", "why", "how", "when", "where", "who",
    "under", "does", "do", "should", "would", "could", "pilot", "rpa", "rpas",
    "operation", "operations", "advanced", "statement", "best", "most", "correct",
}

REQUIRED = {
    "id",
    "category",
    "difficulty",
    "question",
    "choices",
    "answerIndex",
    "rationale",
    "examScope",
    "examLevel",
    "tp15263Section",
    "knowledgeArea",
    "knowledgeTopic",
    "learningObjective",
    "source",
    "sourceRefs",
    "exactRefs",
    "lastVerified",
}

LEVEL1_MARKERS = (
    "bvlos",
    "level 1 complex",
    "tp 15530",
    "detect-and-avoid",
    "detect and avoid",
    "daa",
    "rpoc",
)


def norm(text):
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", str(text).lower())).strip()


def tokens(text):
    return {word for word in norm(text).split() if len(word) > 2 and word not in STOP}


def similarity(left, right):
    left_norm, right_norm = norm(left), norm(right)
    sequence = SequenceMatcher(None, left_norm, right_norm).ratio()
    left_tokens, right_tokens = tokens(left), tokens(right)
    jaccard = (len(left_tokens & right_tokens) / len(left_tokens | right_tokens)) if (left_tokens or right_tokens) else 0.0
    return max(sequence, jaccard * 1.10), sequence, jaccard


def validate_candidate(candidate):
    missing = REQUIRED - set(candidate)
    if missing:
        raise ValueError(f"{candidate.get('id', '<unknown>')} missing fields: {sorted(missing)}")
    if len(candidate["choices"]) != 4:
        raise ValueError(f"{candidate['id']} must have four choices")
    if not isinstance(candidate["answerIndex"], int) or not 0 <= candidate["answerIndex"] < 4:
        raise ValueError(f"{candidate['id']} has invalid answerIndex")
    if not candidate.get("sourceRefs"):
        raise ValueError(f"{candidate['id']} must include at least one sourceRefs entry")
    if not candidate.get("exactRefs"):
        raise ValueError(f"{candidate['id']} must include at least one exactRefs entry")

    searchable = " ".join(
        str(candidate.get(field, ""))
        for field in ("question", "rationale", "source", "knowledgeTopic", "learningObjective")
    ).lower()
    scope = candidate.get("examScope")
    if scope in {"core-advanced", "core-basic-advanced"}:
        marker = next((value for value in LEVEL1_MARKERS if value in searchable), None)
        if marker:
            raise ValueError(f"{candidate['id']} contains Level 1/BVLOS marker in default scope: {marker}")


def best_match(candidate, existing, selected):
    best = None
    for old in existing:
        score, sequence, jaccard = similarity(candidate["question"], old.get("question", ""))
        if best is None or score > best["score"]:
            best = {
                "score": score,
                "sequence": sequence,
                "jaccard": jaccard,
                "existingId": old.get("id"),
                "existingQuestion": old.get("question", ""),
            }
    for old in selected:
        score, sequence, jaccard = similarity(candidate["question"], old["question"])
        if best is None or score > best["score"]:
            best = {
                "score": score,
                "sequence": sequence,
                "jaccard": jaccard,
                "existingId": old.get("id"),
                "existingQuestion": old.get("question", ""),
            }
    return best


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("pool", help="Path to BatchN_candidate_pool.json")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--threshold", type=float, default=0.72)
    parser.add_argument("--allow-shortfall", action="store_true")
    parser.add_argument("--audit", help="Optional audit output path")
    args = parser.parse_args()

    app_root = Path(__file__).resolve().parents[1]
    qpath = app_root / "data" / "questions.json"
    pool_path = Path(args.pool).resolve()
    if not pool_path.exists():
        raise SystemExit(f"Candidate pool not found: {pool_path}")

    data = json.loads(qpath.read_text(encoding="utf-8"))
    pool = json.loads(pool_path.read_text(encoding="utf-8"))
    targets = pool["categoryTargets"]
    target_total = sum(targets.values())
    audit_path = Path(args.audit).resolve() if args.audit else pool_path.with_name(
        pool_path.stem.replace("candidate_pool", "dryrun_audit") + ".json"
    )

    existing = data["questions"]
    existing_ids = {question["id"] for question in existing}
    selected = []
    rejected = []
    selected_by_category = Counter()

    for candidate in pool["questions"]:
        validate_candidate(candidate)
        category = candidate["category"]
        if selected_by_category[category] >= targets.get(category, 0):
            rejected.append({"id": candidate["id"], "reason": "category quota filled"})
            continue
        if candidate["id"] in existing_ids:
            rejected.append({"id": candidate["id"], "reason": "duplicate id"})
            continue

        match = best_match(candidate, existing, selected)
        if match and match["score"] >= args.threshold:
            rejected.append({"id": candidate["id"], "reason": "near duplicate", "match": match})
            continue

        selected.append(candidate)
        selected_by_category[category] += 1

    shortfalls = {
        category: targets[category] - selected_by_category[category]
        for category in targets
        if selected_by_category[category] < targets[category]
    }
    audit = {
        "date": date.today().isoformat(),
        "batch": pool.get("batch", pool_path.stem),
        "threshold": args.threshold,
        "currentBankSize": len(existing),
        "candidatePool": len(pool["questions"]),
        "target": target_total,
        "selected": len(selected),
        "selectedByCategory": dict(selected_by_category),
        "shortfalls": shortfalls,
        "selectedIds": [question["id"] for question in selected],
        "rejected": rejected,
    }
    audit_path.write_text(json.dumps(audit, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"Current bank: {len(existing)} questions")
    print(f"Candidate pool: {len(pool['questions'])}")
    print(f"Selected after duplicate screening: {len(selected)} / {target_total}")
    for category in targets:
        print(f"  {category:18s} {selected_by_category[category]:3d}/{targets[category]:3d}")
    print(f"Audit: {audit_path}")
    if shortfalls:
        print("SHORTFALLS:")
        for category, count in shortfalls.items():
            print(f"  {category}: {count}")
    print(f"Near-duplicate rejections: {sum(1 for item in rejected if item['reason'] == 'near duplicate')}")

    if args.dry_run:
        print("DRY RUN - no questions.json changes made.")
        return
    if len(selected) < target_total and not args.allow_shortfall:
        raise SystemExit("Refusing merge: fewer questions survived screening than targeted.")

    backup_dir = app_root / "ingest" / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = backup_dir / f"questions_before_{pool_path.stem}_{stamp}.json"
    shutil.copy2(qpath, backup)

    data["questions"].extend(selected)
    data["totalQuestions"] = len(data["questions"])
    data["updated"] = date.today().isoformat()
    note = (
        f"{date.today().isoformat()} {pool.get('batch', pool_path.stem).upper()}: "
        f"duplicate-screened ingest; {len(selected)} questions selected from "
        f"{len(pool['questions'])} candidates."
    )
    if note not in data.setdefault("migrationNotes", []):
        data["migrationNotes"].append(note)
    qpath.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"Merged {len(selected)} questions. New total: {data['totalQuestions']}")
    print(f"Backup: {backup}")


if __name__ == "__main__":
    main()
