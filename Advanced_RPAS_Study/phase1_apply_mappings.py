#!/usr/bin/env python3
"""
PHASE 1: Apply CARS Section Mappings to questions.json
Updates regulation questions with verified CARS section numbers
"""

import json
from pathlib import Path

# Load mapping results and questions
mapping_file = Path(__file__).parent / "phase1_mapping_for_verification.json"
questions_file = Path(__file__).parent / "data" / "questions.json"

with open(mapping_file, 'r', encoding='utf-8') as f:
    mapping_data = json.load(f)

with open(questions_file, 'r', encoding='utf-8') as f:
    q_data = json.load(f)

# Apply HIGH confidence mappings
high_confidence = [m for m in mapping_data.get("proposed_mappings", []) 
                   if m.get("confidence") == "HIGH"]

print("=" * 100)
print("PHASE 1: APPLYING HIGH CONFIDENCE CARS SECTION MAPPINGS")
print("=" * 100)
print(f"\nTotal HIGH confidence mappings to apply: {len(high_confidence)}\n")

updated_count = 0
questions = q_data.get("questions", [])

for mapping in high_confidence:
    q_id = mapping.get("id")
    section = mapping.get("section")
    
    # Find and update the question
    for q in questions:
        if q.get("id") == q_id and not q.get("carsSection"):
            q["carsSection"] = section
            updated_count += 1
            print(f"  ✓ {q_id:10} → {section:10}")
            break

print(f"\n{updated_count} questions updated with carsSection")

# Save updated questions.json
with open(questions_file, 'w', encoding='utf-8') as f:
    json.dump(q_data, f, indent=2, ensure_ascii=False)

print(f"✓ questions.json updated and saved\n")

# Summary
print("=" * 100)
print("CARS SECTION MAPPING STATUS AFTER PHASE 1 UPDATE")
print("=" * 100)

reg_questions = [q for q in questions if q.get("category") == "regulations"]
with_cars_sec = [q for q in reg_questions if q.get("carsSection")]
without_cars_sec = len(reg_questions) - len(with_cars_sec)

print(f"\nRegulation questions: {len(reg_questions)}")
print(f"  With CARS sections: {len(with_cars_sec)} ({len(with_cars_sec)*100//len(reg_questions)}%)")
print(f"  Without sections:   {without_cars_sec} ({without_cars_sec*100//len(reg_questions)}%)")

# Show questions still needing mapping
print(f"\nQuestions still needing CARS section mapping:")
print("-" * 100)
print(f"{'ID':10} {'Question':70}")
print("-" * 100)

for q in reg_questions:
    if not q.get("carsSection"):
        q_short = q.get("question", "")[:70]
        print(f"{q.get('id'):10} {q_short:70}")

print("\n" + "=" * 100)
print("NEXT STEPS")
print("=" * 100)
print("""
Remaining work for PHASE 1:

1. MEDIUM CONFIDENCE MAPPINGS (15 questions):
   - Verify each against CARs PDF before applying
   - Run: phase1_medium_confidence_review.py
   - Manually update with high confidence

2. UNMAPPED QUESTIONS (16 questions):
   - Use: verify_cars_sections.py for keyword suggestions
   - Read CARs sections manually
   - Map each to correct section

3. RATIONALE UPDATES (all 50 questions):
   - Update rationale to quote exact CARS section text
   - Example: rationale should include "[Direct quote from CARs 901.26]"
   
4. VERIFICATION:
   - Run: audit_tp15263_alignment.py
   - Confirm: 50/50 regulation questions have carsSection field
""")

print("=" * 100)
