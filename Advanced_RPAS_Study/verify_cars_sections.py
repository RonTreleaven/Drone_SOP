#!/usr/bin/env python3
"""
CARS Section Mapper
Helps verify regulation questions against specific CARs sections
Reads CARs_SOR-96-433_FullText.xml to find relevant sections
"""

import json
import re
from pathlib import Path
from xml.etree import ElementTree as ET

# Load questions and CARS data
questions_file = Path(__file__).parent / "data" / "questions.json"
cars_xml_file = Path(__file__).parent / "docs" / "CARs_SOR-96-433_FullText.xml"

with open(questions_file, 'r', encoding='utf-8') as f:
    questions_data = json.load(f)
questions = questions_data.get("questions", [])

# Parse CARS XML
tree = ET.parse(cars_xml_file)
root = tree.getroot()

# Extract all section numbers and text snippets
cars_sections = {}
for provision in root.findall('.//{http://justice.gc.ca/lims}Provision'):
    section_elem = provision.find('{http://justice.gc.ca/lims}SectionNumber')
    text_elem = provision.find('{http://justice.gc.ca/lims}ProvisionText')
    
    if section_elem is not None and text_elem is not None:
        sec_num = section_elem.text
        text = text_elem.text
        if sec_num and text:
            cars_sections[sec_num] = text[:500]  # First 500 chars

# Get regulation questions
reg_questions = [q for q in questions if q.get("category") == "regulations"]
unmapped = [q for q in reg_questions if not q.get("carsSection")]

print("=" * 100)
print("CARS SECTION VERIFICATION TOOL")
print("=" * 100)
print(f"\nTotal regulation questions: {len(reg_questions)}")
print(f"Already mapped: {len(reg_questions) - len(unmapped)}")
print(f"Needing mapping: {len(unmapped)}")

print("\n" + "=" * 100)
print("UNMAPPED REGULATION QUESTIONS - CANDIDATES FOR SECTION ASSIGNMENT")
print("=" * 100)

# Available CARS sections relevant to Part IX
part_ix_sections = [sec for sec in sorted(cars_sections.keys()) if sec.startswith("901.")]
print(f"\nAvailable Part IX sections (903+ total): {len(part_ix_sections)}")
print(f"Sample sections: {', '.join(part_ix_sections[:10])}...\n")

# Analyze each unmapped question for keyword matches
keyword_map = {
    "901.01": ["definitions", "define", "means"],
    "901.02": ["applies to", "applies in respect", "application"],
    "901.06": ["reckless", "negligent", "safety", "endanger"],
    "901.07": ["notify", "notified", "Class F", "airspace"],
    "901.08": ["security perimeter", "emergency"],
    "901.19": ["visual observer", "VO"],
    "901.20": ["certificate of registration", "registered"],
    "901.21": ["insurance"],
    "901.23": ["procedures", "normal", "emergency"],
    "901.26": ["pilot certificate", "basic operations", "advanced operations"],
    "901.27": ["site survey", "operational volume"],
    "901.40": ["advertised event", "bystander", "SFOC"],
    "901.87": ["RPAS Operator Certificate", "ROC"],
}

print(f"\n{'Q#':8} {'Category':12} {'Question':60} {'Keyword Match':20}")
print("-" * 100)

matched_candidates = []
for idx, q in enumerate(unmapped[:20]):  # Show first 20
    q_id = q.get("id")
    question = q.get("question", "")[:60]
    source = q.get("source", "").lower()
    question_lower = question.lower()
    
    # Try to find keyword matches
    matches = []
    for section, keywords in keyword_map.items():
        if any(kw.lower() in question_lower or kw.lower() in source for kw in keywords):
            matches.append(section)
    
    match_str = ", ".join(matches) if matches else "❓ Unknown"
    print(f"{q_id:8} {q.get('category'):12} {question:60} {match_str:20}")
    
    if matches:
        matched_candidates.append({
            "id": q_id,
            "question": question,
            "candidates": matches,
            "source": source
        })

print("\n" + "=" * 100)
print("RECOMMENDED CARS SECTION ASSIGNMENTS")
print("=" * 100)
print(f"\nBased on keyword matching, here are candidates:")
print(f"(Verify each by reading the actual CARs text!)\n")

for item in matched_candidates[:5]:
    print(f"Question: {item['id']}")
    print(f"  Text: {item['question']}")
    print(f"  Candidates: {', '.join(item['candidates'])}")
    print(f"  Action: Read each section and choose PRIMARY section")
    print()

print("=" * 100)
print("NEXT STEPS")
print("=" * 100)
print("""
1. Review each matched question above
2. Read the recommended CARS section(s) in CARs_SOR-96-433_FullText.pdf
3. Confirm the section matches the question's correct answer
4. Update questions.json with: "carsSection": "901.XX"
5. Update rationale to quote the exact CARs section text
6. Re-run audit_tp15263_alignment.py to verify

KEY RESOURCES:
- CARs_SOR-96-433_FullText.pdf (full text with numbering)
- CARs_Part_IX_quiz_reference.json (extracted provisions)
- https://laws-lois.justice.gc.ca/eng/regulations/SOR-96-433/ (official version)

CAUTION:
- Do NOT guess at section numbers
- Verify against XML/PDF before updating
- When in doubt, consult the official Justice Laws website
""")
