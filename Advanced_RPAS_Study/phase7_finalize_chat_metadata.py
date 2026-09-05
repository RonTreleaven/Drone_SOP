#!/usr/bin/env python3
"""Finalize metadata for reviewed chat-imported TP 15263 questions."""

import json
from datetime import date
from pathlib import Path


ADVANCED_IDS = {
    "chat-20260827-03",
    "chat-20260827-06",
    "chat-20260827-07",
    "chat-20260827-09",
    "chat-20260827-10",
    "chat-20260902-01-q02",
    "chat-20260902-01-q06",
    "chat-20260902-01-q09",
    "chat-20260902-01-q10",
    "chat-20260902-02-q03",
    "chat-20260902-02-q04",
    "chat-20260902-02-q05",
    "chat-20260902-02-q07",
    "chat-20260902-02-q08",
    "chat-20260902-02-q09",
}

SUPPLEMENTAL_IDS = {"chat-20260827-01"}


def add_flag(question, flag):
    flags = question.setdefault("reviewFlags", [])
    if flag not in flags:
        flags.append(flag)


path = Path("data/questions.json")
data = json.loads(path.read_text(encoding="utf-8"))
by_id = {question["id"]: question for question in data["questions"]}

for question_id in ADVANCED_IDS:
    question = by_id[question_id]
    question["examScope"] = "core-advanced"
    question["examLevel"] = "advanced"
    add_flag(question, "reviewed-chat-import")

for question_id in SUPPLEMENTAL_IDS:
    question = by_id[question_id]
    question["examScope"] = "supplemental"
    question["examLevel"] = "supplemental"
    add_flag(question, "reviewed-chat-import")

data["updated"] = date.today().isoformat()
data["lastUpdated"] = date.today().isoformat()
data["migrationNotes"].append(
    "2026-09-03 PHASE 7: Finalized examLevel metadata for reviewed chat-import questions and restored the EVLOS/advanced-privilege item to core Advanced scope."
)
path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

print(f"Finalized {len(ADVANCED_IDS) + len(SUPPLEMENTAL_IDS)} reviewed chat-import questions.")
