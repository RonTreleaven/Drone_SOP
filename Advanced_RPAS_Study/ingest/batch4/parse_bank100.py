#!/usr/bin/env python3
"""Parse Bank_100_extracted.txt into Batch4_candidate_pool.json (file 1: regulations + weather)."""
import json, re
from pathlib import Path
from datetime import date

here = Path(__file__).resolve().parent
text = (here / "Bank_100_extracted.txt").read_text(encoding="utf-8")
lines = [l.rstrip() for l in text.splitlines()]

# Find start of numbered question 1 (skip front matter) and stop before the closing "Source-scope map" section.
start_idx = next(i for i, l in enumerate(lines) if re.match(r"^1\.\s", l))
end_idx = next(i for i, l in enumerate(lines) if l.startswith("Source-scope map"))
body = lines[start_idx:end_idx]

q_re = re.compile(r"^(\d+)\.\s+(.*)$")
choice_re = re.compile(r"^([A-D])\.\s+(.*)$")
answer_re = re.compile(r"^Answer:\s+([A-D])\.\s+(.*)$")
authority_re = re.compile(r"^Authority:\s+(.*)$")

raw = []
cur = None
for l in body:
    if not l.strip():
        continue
    if l.startswith("Section "):
        continue
    m = q_re.match(l)
    if m:
        if cur:
            raw.append(cur)
        cur = {"num": int(m.group(1)), "question": m.group(2), "choices": [], "answer_letter": None, "rationale": None, "authority": None}
        continue
    m = choice_re.match(l)
    if m and cur is not None:
        cur["choices"].append(m.group(2))
        continue
    m = answer_re.match(l)
    if m and cur is not None:
        cur["answer_letter"] = m.group(1)
        cur["rationale"] = m.group(2)
        continue
    m = authority_re.match(l)
    if m and cur is not None:
        cur["authority"] = m.group(1)
        continue
if cur:
    raw.append(cur)

assert len(raw) == 100, f"expected 100 questions, got {len(raw)}"
for q in raw:
    assert len(q["choices"]) == 4, q
    assert q["answer_letter"] and q["rationale"] and q["authority"], q

LETTER_IDX = {"A": 0, "B": 1, "C": 2, "D": 3}

HARD_KEYWORDS = [
    "NOT", "except", "level 1 complex", "declaration", "standard 922", "standard 921",
    "sfoc", "903.0", "dnd", "flight reviewer", "firefighting", "designated airport",
]
EASY_KEYWORDS = [
    "is best described as", "is:", "is the", "what is the", "which gases", "lines joining",
    "the boundary between", "standard sea-level", "standard altimeter reference",
]

def classify_difficulty(q_text, rationale, authority):
    blob = f"{q_text} {rationale} {authority}"
    blob_lower = blob.lower()
    hard_hits = sum(1 for kw in HARD_KEYWORDS if kw.lower() in blob_lower)
    # multiple regulatory citations chained together (e.g. "901.25(2), 901.71(2)") -> harder
    citation_count = len(re.findall(r"\d{3}\.\d+", authority))
    if "not" in q_text.lower().split() or hard_hits >= 2 or citation_count >= 2:
        return "hard"
    easy_hits = sum(1 for kw in EASY_KEYWORDS if kw.lower() in blob_lower)
    if easy_hits >= 1 and citation_count <= 1 and hard_hits == 0:
        return "easy"
    return "medium"

def cars_section(authority):
    m = re.search(r"(\d{3}\.\d+(?:\(\d+\))?(?:\([a-z]\))?)", authority)
    return m.group(1) if m else None

today = date.today().isoformat()
questions = []
for q in raw:
    n = q["num"]
    if n <= 50:
        category = "regulations"
        tp_section = 1
        knowledge_area = "Air law, air traffic rules and procedures"
        source_refs = ["ref-tp-15263", "ref-justice-cars"]
    else:
        category = "weather"
        tp_section = 4
        knowledge_area = "Meteorology"
        source_refs = ["ref-tp-15263", "ref-tc-aim-full"]

    difficulty = classify_difficulty(q["question"], q["rationale"], q["authority"])
    cs = cars_section(q["authority"]) if category == "regulations" else None

    prefix = "b4-regu" if category == "regulations" else "b4-wx"
    local_n = n if category == "regulations" else n - 50
    qid = f"{prefix}-{local_n:03d}"

    entry = {
        "id": qid,
        "category": category,
        "difficulty": difficulty,
        "question": q["question"],
        "choices": q["choices"],
        "answerIndex": LETTER_IDX[q["answer_letter"]],
        "rationale": q["rationale"],
        "examScope": "core-advanced",
        "tp15263Section": tp_section,
        "knowledgeArea": knowledge_area,
        "knowledgeTopic": q["authority"],
        "learningObjective": q["rationale"],
        "source": q["authority"],
        "sourceRefs": source_refs,
        "lastVerified": today,
        "origin": {"type": "batch4-docx-ingest", "batch": "Batch 4", "sourceFile": "Canadian_Advanced_RPAS_Validated_MCQ_Bank_100.docx"},
    }
    if cs:
        entry["carsSection"] = cs
    questions.append(entry)

pool = {
    "schemaVersion": 1,
    "batch": "batch4",
    "reviewDate": today,
    "candidatePoolSize": len(questions),
    "targetMergeCount": len(questions),
    "categoryTargets": {
        "regulations": sum(1 for q in questions if q["category"] == "regulations"),
        "weather": sum(1 for q in questions if q["category"] == "weather"),
    },
    "scopeAuthority": {
        "document": "TP 15263 Fourth Edition, 03/2025",
        "rule": "Core questions must map to an Advanced knowledge topic/objective. CARs Part IX/other CARs provide legal authority; TC AIM/NAV CANADA/Standards 921/922 provide supporting operational material where applicable.",
    },
    "questions": questions,
}

out_path = here / "Batch4_candidate_pool.json"
out_path.write_text(json.dumps(pool, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

diff_counts = {}
for q in questions:
    diff_counts[q["difficulty"]] = diff_counts.get(q["difficulty"], 0) + 1
print("Wrote", out_path)
print("Category targets:", pool["categoryTargets"])
print("Difficulty distribution:", diff_counts)
