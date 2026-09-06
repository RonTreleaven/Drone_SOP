#!/usr/bin/env python3
"""Select and merge Batch 4 questions after duplicate screening against local questions.json.

Dry run:
    python .\\ingest\\batch4\\Merge_Batch4.py --dry-run --pool Batch4_candidate_pool.json

Merge:
    python .\\ingest\\batch4\\Merge_Batch4.py --pool Batch4_candidate_pool.json

The script reconstructs similarity from the ACTUAL local questions.json. It enforces category quotas,
skips duplicate IDs, rejects high stem similarity, creates a backup, and writes a detailed audit report.
"""
import argparse, json, re, shutil
from collections import Counter
from datetime import datetime, date
from difflib import SequenceMatcher
from pathlib import Path

STOP = {
    "a","an","the","and","or","of","to","in","on","for","with","is","are","be","being","been",
    "what","which","why","how","when","where","who","under","does","do","should","would","could",
    "pilot","rpa","rpas","operation","operations","advanced","statement","best","most","correct"
}
REQUIRED = {
    "id","category","difficulty","question","choices","answerIndex","rationale","examScope",
    "tp15263Section","knowledgeArea","knowledgeTopic","learningObjective","source","sourceRefs","lastVerified"
}

def norm(s):
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", s.lower())).strip()

def tokens(s):
    return {w for w in norm(s).split() if len(w) > 2 and w not in STOP}

def similarity(a,b):
    na, nb = norm(a), norm(b)
    seq = SequenceMatcher(None, na, nb).ratio()
    ta, tb = tokens(a), tokens(b)
    jac = (len(ta & tb) / len(ta | tb)) if (ta or tb) else 0.0
    score = max(seq, jac * 1.10)
    return score, seq, jac

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--pool", default="Batch4_candidate_pool.json")
    ap.add_argument("--threshold", type=float, default=0.72,
                    help="Reject candidate if max similarity to an existing stem reaches this value")
    ap.add_argument("--allow-shortfall", action="store_true",
                    help="Allow a real merge even if fewer than the target survive screening")
    args = ap.parse_args()

    here = Path(__file__).resolve().parent
    repo = here.parents[1]
    qpath = repo / "data" / "questions.json"
    cpath = here / args.pool
    audit_path = here / (Path(args.pool).stem.replace("candidate_pool", "dryrun_audit") + ".json")

    data = json.loads(qpath.read_text(encoding="utf-8"))
    pool = json.loads(cpath.read_text(encoding="utf-8"))
    targets = pool["categoryTargets"]

    existing = data["questions"]
    existing_ids = {q["id"] for q in existing}
    selected, rejected = [], []
    selected_by_cat = Counter()

    for cand in pool["questions"]:
        missing = REQUIRED - set(cand)
        if missing:
            raise ValueError(f"{cand.get('id','<unknown>')} missing fields: {sorted(missing)}")
        if len(cand["choices"]) != 4:
            raise ValueError(f"{cand['id']} must have four choices")
        if not 0 <= cand["answerIndex"] < 4:
            raise ValueError(f"{cand['id']} has invalid answerIndex")

        cat = cand["category"]
        if selected_by_cat[cat] >= targets.get(cat, 0):
            rejected.append({"id":cand["id"],"reason":"category quota filled"})
            continue
        if cand["id"] in existing_ids:
            rejected.append({"id":cand["id"],"reason":"duplicate id"})
            continue

        best = None
        for old in existing:
            score, seq, jac = similarity(cand["question"], old.get("question",""))
            if best is None or score > best["score"]:
                best = {"score":score,"sequence":seq,"jaccard":jac,
                        "existingId":old.get("id"),"existingQuestion":old.get("question","")}
        for old in selected:
            score, seq, jac = similarity(cand["question"], old["question"])
            if best is None or score > best["score"]:
                best = {"score":score,"sequence":seq,"jaccard":jac,
                        "existingId":old.get("id"),"existingQuestion":old.get("question","")}

        if best and best["score"] >= args.threshold:
            rejected.append({"id":cand["id"],"reason":"near duplicate","match":best})
            continue

        selected.append(cand)
        selected_by_cat[cat] += 1

    shortfalls = {cat:targets[cat]-selected_by_cat[cat] for cat in targets if selected_by_cat[cat] < targets[cat]}
    audit = {
        "date": date.today().isoformat(),
        "threshold": args.threshold,
        "currentBankSize": len(existing),
        "candidatePool": len(pool["questions"]),
        "target": sum(targets.values()),
        "selected": len(selected),
        "selectedByCategory": dict(selected_by_cat),
        "shortfalls": shortfalls,
        "selectedIds": [q["id"] for q in selected],
        "rejected": rejected
    }
    audit_path.write_text(json.dumps(audit,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")

    print(f"Current bank: {len(existing)} questions")
    print(f"Batch 4 candidate pool ({args.pool}): {len(pool['questions'])}")
    print(f"Selected after duplicate screening: {len(selected)} / {sum(targets.values())}")
    for cat in targets:
        print(f"  {cat:18s} {selected_by_cat[cat]:2d}/{targets[cat]:2d}")
    print(f"Audit: {audit_path}")
    if shortfalls:
        print("SHORTFALLS:")
        for cat,n in shortfalls.items():
            print(f"  {cat}: {n}")
    print(f"Near-duplicate rejections: {sum(1 for r in rejected if r['reason']=='near duplicate')}")

    if args.dry_run:
        print("DRY RUN — no questions.json changes made.")
        return

    if len(selected) < sum(targets.values()) and not args.allow_shortfall:
        raise SystemExit("Refusing merge: fewer questions survived screening than targeted. Review the audit or rerun with --allow-shortfall.")

    backup_dir = repo / "ingest" / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = backup_dir / f"questions_before_{Path(args.pool).stem}_{stamp}.json"
    shutil.copy2(qpath, backup)

    data["questions"].extend(selected)
    data["totalQuestions"] = len(data["questions"])
    data["updated"] = date.today().isoformat()
    note = (f"{date.today().isoformat()} CHAT BATCH 4 ({args.pool}): duplicate-screened docx ingest; "
            f"{len(selected)} TP 15263 core-Advanced questions selected from {len(pool['questions'])} candidates.")
    if note not in data.setdefault("migrationNotes", []):
        data["migrationNotes"].append(note)
    qpath.write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(f"Merged {len(selected)} questions. New total: {data['totalQuestions']}")
    print(f"Backup: {backup}")

if __name__ == "__main__":
    main()
