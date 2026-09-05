#!/usr/bin/env python3
"""Normalize legacy questions into the TP 15263 Basic/Advanced study scope."""

import json
import re
from datetime import date
from pathlib import Path


LEVEL_1_PATTERN = re.compile(
    r"\b(BVLOS|beyond visual line[- ]of[- ]sight|Level 1 Complex|TP\s*15530|detect[- ]and[- ]avoid|\bDAA\b)\b",
    re.IGNORECASE,
)
ADVANCED_PATTERN = re.compile(
    r"\b(Advanced Operations|Advanced RPAS|Advanced pilot|controlled airspace|ATC authorization|near people|over people|"
    r"Standard 922|901\.64|901\.65|901\.66|901\.69|901\.70|901\.71|901\.72|901\.73|901\.74|901\.75)\b",
    re.IGNORECASE,
)
SOURCE_PATTERN = re.compile(
    r"\b(TP\s*15263|CARs?|Canadian Aviation Regulations|TC AIM|AIM|NAV CANADA|NOTAM|DAH|CFS|RPAS 101|901\.|900\.|601\.|602\.)\b",
    re.IGNORECASE,
)
TP15263_PATTERN = re.compile(r"\bTP\s*15263\b", re.IGNORECASE)

SECTION_BY_CATEGORY = {
    "regulations": "1",
    "airspace": "1",
    "aerodromes": "1",
    "notams": "5",
    "weather": "4",
    "visual-observers": "6",
    "human-factors": "3",
    "aircraft-systems": "2",
    "maintenance": "2",
    "abnormal": "6",
    "flight-planning": "6",
    "radio": "8",
    "navigation": "5",
    "safety": "1",
    "theory-of-flight": "7",
}

AREA_BY_SECTION = {
    "1": "Air law, air traffic rules and procedures",
    "2": "RPA airframes, power plants, propulsion and systems",
    "3": "Human factors",
    "4": "Meteorology",
    "5": "Navigation",
    "6": "Flight operations",
    "7": "Theory of flight",
    "8": "Radiotelephony",
}


def searchable_text(question):
    values = [
        question.get("id"),
        question.get("category"),
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


def add_flag(question, flag):
    flags = question.setdefault("reviewFlags", [])
    if flag not in flags:
        flags.append(flag)


path = Path("data/questions.json")
data = json.loads(path.read_text(encoding="utf-8"))
normalized = 0
level1 = 0
source_review = 0
tp_mapping_review = 0

for question in data["questions"]:
    text = searchable_text(question)

    if LEVEL_1_PATTERN.search(text):
        if question.get("examScope") != "level-1-complex" or question.get("examLevel") != "level-1-complex":
            question["examScope"] = "level-1-complex"
            question["examLevel"] = "level-1-complex"
            level1 += 1
        add_flag(question, "scope-level-1-complex")
        continue

    if question.get("id", "").startswith("tp15263-"):
        add_flag(question, "phase7-tp15263-batch-1")
        continue

    if question.get("examScope") or question.get("examLevel"):
        continue

    is_advanced = bool(ADVANCED_PATTERN.search(text))
    question["examLevel"] = "advanced" if is_advanced else "basic-advanced"
    question["examScope"] = "core-advanced" if is_advanced else "core-basic-advanced"
    add_flag(question, "legacy-normalized")

    section = str(question.get("tp15263Section") or SECTION_BY_CATEGORY.get(question.get("category"), "")).strip()
    if section:
        question["tp15263Section"] = section
        question.setdefault("knowledgeArea", AREA_BY_SECTION.get(section, question.get("category", "")))

    if not TP15263_PATTERN.search(text):
        add_flag(question, "needs-tp15263-mapping")
        tp_mapping_review += 1

    if not SOURCE_PATTERN.search(text):
        add_flag(question, "needs-source-review")
        source_review += 1

    normalized += 1

data["totalQuestions"] = len(data["questions"])
data["updated"] = date.today().isoformat()
data["lastUpdated"] = date.today().isoformat()
data["migrationNotes"].append(
    "2026-09-03 PHASE 7: Normalized legacy non-Level-1 questions into TP 15263 Basic/Advanced scope with examLevel, tp15263Section, knowledgeArea, and reviewFlags for source/mapping cleanup."
)
path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

print(f"Normalized legacy questions: {normalized}")
print(f"Level 1 Complex corrections: {level1}")
print(f"Needs TP 15263 mapping review: {tp_mapping_review}")
print(f"Needs source review: {source_review}")
