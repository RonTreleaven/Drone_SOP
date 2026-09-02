#!/usr/bin/env python3
"""
PHASE 1: CARS Section Mapping Tool
Systematically maps 50 regulation questions to verified CARS sections
"""

import json
from pathlib import Path

# Load the CARS reference JSON with all provisions
cars_ref_file = Path(__file__).parent / "docs" / "CARs_Part_IX_quiz_reference.json"
questions_file = Path(__file__).parent / "data" / "questions.json"

with open(cars_ref_file, 'r', encoding='utf-8') as f:
    cars_data = json.load(f)

with open(questions_file, 'r', encoding='utf-8') as f:
    q_data = json.load(f)

# Extract all Part IX sections (901.xx)
provisions = cars_data.get("provisions", {})
part_ix_sections = {sec: text for sec, text in provisions.items() 
                    if sec.startswith("901.") and isinstance(text, dict)}

print("=" * 100)
print("PHASE 1: CARS SECTION MAPPING REFERENCE GUIDE")
print("=" * 100)
print(f"\nTotal Part IX sections available: {len(part_ix_sections)}")

# Group by subsection for easier browsing
sections_by_group = {}
for sec in sorted(part_ix_sections.keys()):
    base = sec.split("(")[0]  # e.g., "901.01" from "901.01(1)"
    if base not in sections_by_group:
        sections_by_group[base] = []
    sections_by_group[base].append(sec)

print("\nKey CARS Sections (for mapping regulation questions):\n")
print(f"{'Section':12} {'Description':70}")
print("-" * 85)

# Create a reference guide for common sections
common_sections = {
    "901.01": "Definitions",
    "901.02": "Applicability",
    "901.06": "General operating rules (reckless/negligent)",
    "901.07": "Notify ATS of inadvertent airspace entry",
    "901.08": "Security perimeter restrictions",
    "901.19": "Visual Observer requirements",
    "901.20": "Certificate of registration",
    "901.21": "Insurance requirements",
    "901.23": "Establishment of operating procedures (normal & emergency)",
    "901.26": "Pilot Certificate – Small RPAS (Basic/Advanced)",
    "901.27": "Site survey requirements",
    "901.40": "Advertised/controlled events (requires SFOC)",
    "901.87": "RPAS Operator Certificate requirement",
}

for sec, desc in common_sections.items():
    if sec in part_ix_sections:
        print(f"{sec:12} {desc:70}")

print("\n" + "=" * 100)
print("REGULATION QUESTIONS NEEDING MAPPING")
print("=" * 100)

# Get all regulation questions
questions = q_data.get("questions", [])
reg_questions = [q for q in questions if q.get("category") == "regulations"]
unmapped = [q for q in reg_questions if not q.get("carsSection")]

print(f"\nTotal regulation questions: {len(reg_questions)}")
print(f"Already mapped: {len(reg_questions) - len(unmapped)}")
print(f"Needing mapping: {len(unmapped)}\n")

# Display unmapped questions with suggested sections
print(f"{'ID':10} {'Question':65} {'Primary Section':20}")
print("-" * 95)

# Create a detailed mapping guide based on question keywords
mapping_guide = {
    "pilot certificate": ["901.26"],
    "visual observer": ["901.19"],
    "site survey": ["901.27"],
    "operating procedures": ["901.23"],
    "insurance": ["901.21"],
    "registration": ["901.20"],
    "certificate of registration": ["901.20"],
    "advertised event": ["901.40"],
    "RPAS Operator Certificate": ["901.87"],
    "bystander": ["901.87", "901.40"],
    "SFOC": ["901.40"],
    "controlled airspace": ["901.26", "901.27"],
    "operat": ["901.23"],
    "aerodromes": ["901.27"],
    "weight": ["901.01"],
    "definitions": ["901.01"],
}

for q in unmapped[:30]:  # Show first 30
    q_id = q.get("id")
    question = q.get("question", "")
    q_lower = question.lower()
    
    # Find matching section
    matching_sections = []
    for keyword, sections in mapping_guide.items():
        if keyword.lower() in q_lower:
            matching_sections.extend(sections)
    
    # Remove duplicates and prioritize
    matching_sections = sorted(list(set(matching_sections)))
    primary = matching_sections[0] if matching_sections else "TBD"
    
    q_short = question[:65] if len(question) > 65 else question
    print(f"{q_id:10} {q_short:65} {primary:20}")

print("\n" + "=" * 100)
print("MAPPING STRATEGY")
print("=" * 100)
print("""
The 47 unmapped regulation questions should be mapped as follows:

1. Read the question and answer carefully
2. Identify the PRIMARY regulation topic
3. Match to CORRECT CARS section from common_sections above
4. Cross-check against CARs_SOR-96-433_FullText.pdf to verify
5. Update rationale to quote exact section text

EXAMPLE MAPPING:
Question: "Which pilot certificate is required to conduct Advanced RPAS operations?"
Answer: "Pilot Certificate – Small RPAS (Advanced Operations)"
→ PRIMARY SECTION: 901.26 (Pilot Certificate Requirements)
Verification: Read 901.26 in PDF, confirm it states Advanced Pilot requirements

KEY VALIDATION RULES:
✓ Each question should map to ONLY ONE primary section
✓ Rationale should quote the exact section, not paraphrase
✓ Answer must be defensible by reading that section
✗ If section doesn't support the answer → question needs rewrite
✗ If answer spans multiple sections → pick primary + note secondary in source
""")

# Generate a CSV-style mapping template
print("\n" + "=" * 100)
print("MAPPING TEMPLATE (for systematic updates)")
print("=" * 100)
print("\nID,Question_Short,Suggested_Section,Verified_Section,Status")
print("-" * 100)

for q in unmapped[:20]:
    q_id = q.get("id")
    q_short = q.get("question", "")[:50].replace(",", ";")
    
    matching_sections = []
    for keyword, sections in mapping_guide.items():
        if keyword.lower() in q.get("question", "").lower():
            matching_sections.extend(sections)
    
    suggested = matching_sections[0] if matching_sections else "901.01"
    print(f"{q_id},{q_short},{suggested},[VERIFY],pending")

print("\n" + "=" * 100)
print("NEXT STEP: Update questions.json")
print("=" * 100)
print("""
Once you've verified each section mapping:

1. Open questions.json
2. For each regulation question, add:
   "carsSection": "901.XX"
   
3. Update rationale to include quote from section

4. Run verification script to confirm all mapped

See: update_cars_sections.py for automated template
""")
