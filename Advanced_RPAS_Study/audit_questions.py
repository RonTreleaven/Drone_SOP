#!/usr/bin/env python3
"""
Advanced RPAS Question Bank Audit Tool
Compares questions.json against gold-source requirements
"""

import json
from collections import defaultdict
from pathlib import Path

# Load questions
questions_file = Path(__file__).parent / "data" / "questions.json"
with open(questions_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

questions = data.get("questions", [])

print("=" * 80)
print("ADVANCED RPAS QUESTION BANK AUDIT REPORT")
print(f"Total Questions: {len(questions)}")
print("=" * 80)

# 1. Category Distribution
print("\n1. CATEGORY DISTRIBUTION")
print("-" * 80)
cat_count = defaultdict(int)
for q in questions:
    cat = q.get("category", "unknown")
    cat_count[cat] += 1

for cat in sorted(cat_count.keys()):
    print(f"  {cat:25} {cat_count[cat]:3d} questions")

# 2. Difficulty Distribution
print("\n2. DIFFICULTY DISTRIBUTION")
print("-" * 80)
diff_count = defaultdict(int)
for q in questions:
    diff = q.get("difficulty", "unknown")
    diff_count[diff] += 1

for diff in sorted(diff_count.keys()):
    print(f"  {diff:25} {diff_count[diff]:3d} questions")

# 3. Source Citation Analysis
print("\n3. SOURCE CITATION ANALYSIS")
print("-" * 80)
source_types = defaultdict(int)
missing_source = []
unverified = []
verified = []

for q in questions:
    q_id = q.get("id")
    source = q.get("source", "").strip()
    last_verified = q.get("lastVerified", "")
    
    if not source:
        missing_source.append(q_id)
    else:
        # Extract source type
        if "CARs" in source or "901." in source:
            source_types["CARs"] += 1
        elif "TP 15263" in source or "TP 15530" in source:
            source_types["TC Knowledge Requirement"] += 1
        elif "AIM" in source:
            source_types["AIM"] += 1
        elif "NAV CANADA" in source or "DAH" in source:
            source_types["NAV CANADA"] += 1
        else:
            source_types["Other"] += 1
        
        if last_verified:
            verified.append(q_id)
        else:
            unverified.append(q_id)

print(f"\n  Source Type Distribution:")
for src_type in sorted(source_types.keys()):
    print(f"    {src_type:35} {source_types[src_type]:3d}")

print(f"\n  Questions with verification date: {len(verified)}")
print(f"  Questions without verification:  {len(unverified)}")
print(f"  Questions missing source:        {len(missing_source)}")

if missing_source[:5]:
    print(f"\n  First 5 missing sources: {missing_source[:5]}")

# 4. CARS Section References
print("\n4. CARS SECTION REFERENCES (Verified)")
print("-" * 80)
cars_sections = defaultdict(int)
for q in questions:
    cars_sec = q.get("carsSection", "").strip()
    if cars_sec:
        cars_sections[cars_sec] += 1

if cars_sections:
    for sec in sorted(cars_sections.keys(), key=lambda x: float(x.split(".")[-1]) if "." in x else 0):
        print(f"  {sec:15} {cars_sections[sec]:3d} questions")
else:
    print("  ⚠ No CARS sections with specific section numbers found!")

# 5. Questions by Category & Difficulty
print("\n5. CATEGORY × DIFFICULTY MATRIX")
print("-" * 80)
matrix = defaultdict(lambda: defaultdict(int))
for q in questions:
    cat = q.get("category", "unknown")
    diff = q.get("difficulty", "unknown")
    matrix[cat][diff] += 1

difficulties = ["easy", "medium", "hard", "tricky"]
print(f"\n{'Category':25} {'Easy':>6} {'Medium':>6} {'Hard':>6} {'Tricky':>6} {'Total':>6}")
print("-" * 60)
for cat in sorted(matrix.keys()):
    row = matrix[cat]
    total = sum(row.values())
    counts = [str(row.get(d, 0)) for d in difficulties]
    print(f"{cat:25} {counts[0]:>6} {counts[1]:>6} {counts[2]:>6} {counts[3]:>6} {total:>6}")

# 6. Sample questions missing proper source links
print("\n6. QUESTIONS NEEDING SOURCE VERIFICATION")
print("-" * 80)
needs_review = [q for q in questions if not q.get("carsSection") and "CARs" in q.get("source", "")]
print(f"\n  CARs questions without specific section numbers: {len(needs_review)}")
if needs_review[:3]:
    print("\n  Sample questions:")
    for q in needs_review[:3]:
        print(f"    ID: {q.get('id')}")
        print(f"    Q:  {q.get('question')[:70]}...")
        print(f"    Source: {q.get('source')}")
        print()

# 7. Export data for next phase
print("\n7. SUMMARY FOR NEXT AUDIT PHASE")
print("-" * 80)
print(f"  Total questions: {len(questions)}")
print(f"  Questions needing CARs section verification: {len(needs_review)}")
print(f"  Questions with unverified status: {len(unverified)}")
print(f"  Questions missing sources: {len(missing_source)}")
print(f"\n  ACTION ITEMS:")
print(f"    1. Extract TP 15263 knowledge domains (see TP15263_E_Knowledge-Requirements-Basic-Advanced.pdf)")
print(f"    2. Map current questions to TP 15263 domains")
print(f"    3. Verify CARs section numbers against CARs_SOR-96-433_FullText.xml")
print(f"    4. Add RPAS 101 references where applicable")
print(f"    5. Flag questions that don't align with Advanced Pilot scope (remove Level 1 Complex)")

print("\n" + "=" * 80)
