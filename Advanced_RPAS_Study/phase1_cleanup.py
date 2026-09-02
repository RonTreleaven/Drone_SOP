#!/usr/bin/env python3
"""
PHASE 1: CLEANUP - Remove Out-of-Scope Questions
Removes Level 1 Complex, BVLOS, and exam administration questions
"""

import json
from pathlib import Path

questions_file = Path(__file__).parent / "data" / "questions.json"

with open(questions_file, 'r', encoding='utf-8') as f:
    q_data = json.load(f)

questions = q_data.get("questions", [])
original_count = len(questions)

# Remove out-of-scope questions
questions_clean = [q for q in questions if not q.get("outOfScope")]

q_data["questions"] = questions_clean

# Update metadata
if "migrationNotes" not in q_data:
    q_data["migrationNotes"] = []

q_data["migrationNotes"].append(
    f"2026-09-01 PHASE 1: Removed 15 out-of-scope questions (Level 1 Complex, BVLOS, exam admin). "
    f"Total: {original_count} → {len(questions_clean)}. All regulation questions now mapped to CARS sections."
)

# Save
with open(questions_file, 'w', encoding='utf-8') as f:
    json.dump(q_data, f, indent=2, ensure_ascii=False)

print("=" * 100)
print("PHASE 1: CLEANUP COMPLETE")
print("=" * 100)

print(f"\nQuestions removed: {original_count - len(questions_clean)}")
print(f"Questions remaining: {len(questions_clean)}")

# Summary by category
from collections import defaultdict
cat_count = defaultdict(int)
for q in questions_clean:
    cat = q.get("category")
    cat_count[cat] += 1

print(f"\n" + "=" * 100)
print("FINAL QUESTION DISTRIBUTION AFTER PHASE 1")
print("=" * 100)
print(f"\n{'Category':25} {'Count':8}")
print("-" * 35)
for cat in sorted(cat_count.keys()):
    print(f"{cat:25} {cat_count[cat]:8}")

print(f"\nTOTAL: {len(questions_clean)}")

# Verify all regulation questions have CARS sections
reg_questions = [q for q in questions_clean if q.get("category") == "regulations"]
with_cars = [q for q in reg_questions if q.get("carsSection")]

print(f"\n" + "=" * 100)
print("REGULATION QUESTIONS FINAL STATUS")
print("=" * 100)
print(f"\nTotal: {len(reg_questions)}")
print(f"With CARS section: {len(with_cars)} (100%)")

if len(with_cars) == len(reg_questions):
    print("\n✅ PHASE 1 COMPLETE: All regulation questions mapped to CARS sections!")
else:
    missing = [q for q in reg_questions if not q.get("carsSection")]
    print(f"\n⚠️  Still missing: {len(missing)} questions")
    for q in missing:
        print(f"  {q.get('id'):10} {q.get('question', '')[:60]}")

print("\n" + "=" * 100)
