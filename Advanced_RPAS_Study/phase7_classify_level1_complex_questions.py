#!/usr/bin/env python3
"""Classify TP 15530/BVLOS/Level 1 Complex questions outside the default TP 15263 pool."""

import json
import re
from datetime import date
from pathlib import Path


LEVEL_1_PATTERN = re.compile(
    r"\b(BVLOS|beyond visual line[- ]of[- ]sight|Level 1 Complex|TP\s*15530|detect[- ]and[- ]avoid|\bDAA\b)\b",
    re.IGNORECASE,
)


def searchable_text(question):
    values = [
        question.get("id"),
        question.get("question"),
        question.get("rationale"),
        question.get("source"),
        question.get("examScope"),
        question.get("examLevel"),
        question.get("knowledgeArea"),
        question.get("knowledgeTopic"),
        question.get("learningObjective"),
    ]
    values.extend(question.get("sourceRefs") or [])
    return " ".join(str(value) for value in values if value)


path = Path("data/questions.json")
data = json.loads(path.read_text(encoding="utf-8"))
changed = []

for question in data["questions"]:
    if not LEVEL_1_PATTERN.search(searchable_text(question)):
        continue

    before_scope = question.get("examScope")
    before_level = question.get("examLevel")
    question["examScope"] = "level-1-complex"
    question["examLevel"] = "level-1-complex"
    changed.append((question.get("id"), before_scope, before_level))

if not changed:
    print("No Level 1 Complex/BVLOS questions required classification.")
else:
    data["updated"] = date.today().isoformat()
    data["lastUpdated"] = date.today().isoformat()
    data["migrationNotes"].append(
        f"2026-09-03 PHASE 7: Classified {len(changed)} TP 15530/BVLOS/Level 1 Complex questions as examScope level-1-complex so they are excluded from the default TP 15263 Basic/Advanced pool."
    )
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Classified {len(changed)} Level 1 Complex/BVLOS questions.")
