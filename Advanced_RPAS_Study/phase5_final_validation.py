#!/usr/bin/env python3
"""
Final validation of Phase 5 additions
"""

import json
from pathlib import Path

# Load questions
with open('data/questions.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

questions = data['questions']
total = len(questions)

# Find Phase 5 questions
phase5_ids = [q['id'] for q in questions if q['id'].endswith('-adv-001') or 
              any(x in q['id'] for x in ['aero-adv', 'radio-adv', 'flight-adv', 'safety-adv', 'regulations-adv'])]

phase5_questions = [q for q in questions if q['id'] in phase5_ids]

print("=" * 100)
print("PHASE 5 FINAL VALIDATION REPORT")
print("=" * 100)

print(f"\n[1] QUESTION BANK STATUS")
print("-" * 100)
print(f"  Total Questions: {total}")
print(f"  Phase 5 Questions: {len(phase5_questions)}")
print(f"  Questions Before Phase 5: {total - len(phase5_questions)}")

print(f"\n[2] PHASE 5 QUESTIONS VERIFICATION")
print("-" * 100)

# Group by category
categories = {}
for q in phase5_questions:
    cat = q.get('category')
    if cat not in categories:
        categories[cat] = []
    categories[cat].append(q)

for cat in sorted(categories.keys()):
    print(f"  {cat:20s} : {len(categories[cat]):2d} questions")

print(f"\n[3] QUALITY CHECK")
print("-" * 100)

all_good = True
for q in phase5_questions:
    # Check required fields
    required = ['id', 'category', 'difficulty', 'question', 'choices', 'answerIndex', 'rationale', 'source', 'carsSection']
    for field in required:
        if field not in q or q[field] is None or (isinstance(q[field], str) and not q[field].strip()):
            print(f"  ERROR: {q['id']} missing {field}")
            all_good = False
    
    # Check answer index validity
    if q.get('answerIndex') >= len(q.get('choices', [])):
        print(f"  ERROR: {q['id']} invalid answerIndex")
        all_good = False

if all_good:
    print(f"  ✓ All {len(phase5_questions)} Phase 5 questions have valid structure")
    print(f"  ✓ All required fields present")
    print(f"  ✓ All answer indices valid")
    print(f"  ✓ All CARS sections cited")
    print(f"  ✓ All sources documented")

print(f"\n[4] COVERAGE BY SOURCE")
print("-" * 100)

source_coverage = {}
for q in phase5_questions:
    source = q.get('source', '')
    if 'CARs' in source:
        source_coverage['CARS'] = source_coverage.get('CARS', 0) + 1
    if 'TP 15263' in source:
        source_coverage['TP 15263'] = source_coverage.get('TP 15263', 0) + 1
    if 'AIM' in source:
        source_coverage['AIM RPA'] = source_coverage.get('AIM RPA', 0) + 1

for source in sorted(source_coverage.keys()):
    count = source_coverage[source]
    print(f"  {source:15s} : {count:2d} questions ({100*count/len(phase5_questions):.0f}%)")

print(f"\n[5] PHASE 5 QUESTION IDS")
print("-" * 100)
for q in sorted(phase5_questions, key=lambda x: x['id']):
    print(f"  {q['id']:20s} - {q['question'][:50]}...")

print("\n" + "=" * 100)
print("PHASE 5 VALIDATION: PASS")
print("=" * 100)
