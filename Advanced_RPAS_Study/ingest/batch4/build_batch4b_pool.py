#!/usr/bin/env python3
"""Build Batch4b_candidate_pool.json from _parsed_101_350.json (post-classification)."""
import json, re
from pathlib import Path
from datetime import date

here = Path(__file__).resolve().parent
raw = json.loads((here / "_parsed_101_350.json").read_text(encoding="utf-8"))

LETTER_IDX = {"A": 0, "B": 1, "C": 2, "D": 3}

KNOWLEDGE_AREA = {
    "regulations": "Air law, air traffic rules and procedures",
    "airspace": "Air law, air traffic rules and procedures",
    "aerodromes": "Air law, air traffic rules and procedures",
    "notams": "Navigation",
    "safety": "Air law, air traffic rules and procedures",
    "weather": "Meteorology",
    "navigation": "Navigation",
    "flight-planning": "Flight operations",
    "abnormal": "Flight operations",
    "visual-observers": "Flight operations",
    "maintenance": "RPA airframes, power plants, propulsion and systems",
    "human-factors": "Human factors",
    "radio": "Radiotelephony",
}
TP_SECTION = {
    "regulations": 1, "airspace": 1, "aerodromes": 1, "notams": 1, "safety": 1,
    "weather": 4, "navigation": 5, "flight-planning": 6, "abnormal": 6,
    "visual-observers": 6, "maintenance": 6, "human-factors": 6, "radio": 8,
}
SOURCE_REFS = {
    "regulations": ["ref-tp-15263", "ref-justice-cars"],
    "airspace": ["ref-tp-15263", "ref-tc-aim-full"],
    "aerodromes": ["ref-tp-15263", "ref-tc-aim-full"],
    "notams": ["ref-tp-15263", "ref-tc-aim-full"],
    "safety": ["ref-tp-15263", "ref-justice-cars"],
    "weather": ["ref-tp-15263", "ref-tc-aim-full"],
    "navigation": ["ref-tp-15263", "ref-tc-aim-full"],
    "flight-planning": ["ref-tp-15263"],
    "abnormal": ["ref-tp-15263"],
    "visual-observers": ["ref-tp-15263"],
    "maintenance": ["ref-tp-15263"],
    "human-factors": ["ref-tp-15263", "ref-tp-12864"],
    "radio": ["ref-tp-15263", "ref-tc-aim-full"],
}
ID_PREFIX = {
    "regulations": "regu", "airspace": "asp", "aerodromes": "aero", "notams": "notam",
    "safety": "safe", "weather": "wx", "navigation": "nav", "flight-planning": "fp",
    "abnormal": "abn", "visual-observers": "vo", "maintenance": "maint",
    "human-factors": "hf", "radio": "radio",
}
BATCH_TAG = "b4b"  # file 2 (101-350) — distinct from file 1's "b4-" prefix to avoid ID collisions

HARD_KEYWORDS = [
    "not", "except", "level 1 complex", "declaration", "standard 922", "standard 921",
    "sfoc", "903.0", "dnd", "flight reviewer", "escat", "northern domestic",
]
EASY_KEYWORDS = [
    "is best described as", "is:", "is the", "what is the", "primarily indicates",
    "phonetic word for", "commonly pronounced", "means:", "the standard",
]

def classify_difficulty(q_text, rationale, authority):
    blob = f"{q_text} {rationale} {authority}".lower()
    hard_hits = sum(1 for kw in HARD_KEYWORDS if kw in blob)
    citation_count = len(re.findall(r"\d{3}\.\d+", authority))
    if hard_hits >= 2 or citation_count >= 2:
        return "hard"
    easy_hits = sum(1 for kw in EASY_KEYWORDS if kw in blob)
    if easy_hits >= 1 and citation_count <= 1 and hard_hits == 0:
        return "easy"
    return "medium"

def cars_section(authority):
    m = re.search(r"(\d{3}\.\d+(?:\(\d+\))?(?:\([a-z]\))?)", authority)
    return m.group(1) if m else None

today = date.today().isoformat()
questions = []
counters = {}
for q in raw:
    cat = q["category"]
    counters[cat] = counters.get(cat, 0) + 1
    local_n = counters[cat]
    qid = f"{BATCH_TAG}-{ID_PREFIX[cat]}-{local_n:03d}"

    difficulty = classify_difficulty(q["question"], q["rationale"], q["authority"])
    cs = cars_section(q["authority"])

    entry = {
        "id": qid,
        "category": cat,
        "difficulty": difficulty,
        "question": q["question"],
        "choices": q["choices"],
        "answerIndex": LETTER_IDX[q["answer_letter"]],
        "rationale": q["rationale"],
        "examScope": "core-advanced",
        "tp15263Section": TP_SECTION[cat],
        "knowledgeArea": KNOWLEDGE_AREA[cat],
        "knowledgeTopic": q["authority"],
        "learningObjective": q["rationale"],
        "source": q["authority"],
        "sourceRefs": SOURCE_REFS[cat],
        "lastVerified": today,
        "origin": {"type": "batch4-docx-ingest", "batch": "Batch 4", "sourceFile": "Canadian_Advanced_RPAS_Validated_MCQ_Bank_101-350.docx"},
    }
    if cs:
        entry["carsSection"] = cs
    questions.append(entry)

category_targets = {}
for q in questions:
    category_targets[q["category"]] = category_targets.get(q["category"], 0) + 1

pool = {
    "schemaVersion": 1,
    "batch": "batch4",
    "reviewDate": today,
    "candidatePoolSize": len(questions),
    "targetMergeCount": len(questions),
    "categoryTargets": category_targets,
    "scopeAuthority": {
        "document": "TP 15263 Fourth Edition, 03/2025",
        "rule": "Core questions must map to an Advanced knowledge topic/objective. CARs Part IX/other CARs provide legal authority; TC AIM/NAV CANADA/ISED/Standards 921/922 provide supporting operational material where applicable.",
    },
    "questions": questions,
}

out_path = here / "Batch4b_candidate_pool.json"
out_path.write_text(json.dumps(pool, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

diff_counts = {}
for q in questions:
    diff_counts[q["difficulty"]] = diff_counts.get(q["difficulty"], 0) + 1
print("Wrote", out_path)
print("Category targets:", category_targets)
print("Difficulty distribution:", diff_counts)
