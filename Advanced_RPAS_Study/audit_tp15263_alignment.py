#!/usr/bin/env python3
"""
Advanced RPAS Question Bank Audit v2
Maps current questions to TP 15263 domains and identifies gaps/source verification needs
"""

import json
from collections import defaultdict
from pathlib import Path

# Load data
questions_file = Path(__file__).parent / "data" / "questions.json"
requirements_file = Path(__file__).parent / "docs" / "knowledge_requirements_extracted.json"

with open(questions_file, 'r', encoding='utf-8') as f:
    questions_data = json.load(f)
questions = questions_data.get("questions", [])

with open(requirements_file, 'r', encoding='utf-8') as f:
    requirements_data = json.load(f)

print("=" * 90)
print("ADVANCED RPAS QUESTION BANK AUDIT v2: TP 15263 ALIGNMENT")
print("=" * 90)

# Map TP 15263 sections to question categories
tp_section_map = {
    "2": "aircraft-systems",      # RPA airframes, power plants, propulsion and systems
    "3": "human-factors",          # Human Factors
    "4": "weather",                # Meteorology
    "5": "navigation",             # Navigation
    "6": "flight-planning",        # Flight Operations (includes performance, W&B, etc.)
    "7": "aircraft-systems",       # Theory of Flight
    "8": "radio"                   # Radiotelephony
}

# Extract all domain titles from TP 15263
tp_sections = {}
for sec_num, sec_data in requirements_data.get("sections", {}).items():
    tp_sections[sec_num] = {
        "title": sec_data.get("title"),
        "areas_count": len(sec_data.get("knowledge_areas", []))
    }

print("\n1. TP 15263 STRUCTURE (ADVANCED PILOT)")
print("-" * 90)
for sec_num in sorted(tp_sections.keys(), key=lambda x: int(x)):
    info = tp_sections[sec_num]
    print(f"  Section {sec_num}: {info['title'][:70]:70} ({info['areas_count']} areas)")

# Current question distribution
print("\n2. CURRENT QUESTION DISTRIBUTION BY CATEGORY")
print("-" * 90)
cat_count = defaultdict(int)
for q in questions:
    cat = q.get("category", "unknown")
    cat_count[cat] += 1

for cat in sorted(cat_count.keys()):
    print(f"  {cat:25} {cat_count[cat]:3d} questions")

# Gap analysis: which TP 15263 sections have sparse coverage
print("\n3. COVERAGE ANALYSIS (Questions vs TP 15263 Domains)")
print("-" * 90)
print(f"{'TP Section':12} {'Domain':40} {'Target Questions':16} {'Current':8} {'Status':12}")
print("-" * 90)

# Estimate "target" number of questions per domain (balanced distribution)
target_per_domain = len(questions) // len(tp_sections)

for sec_num in sorted(tp_sections.keys(), key=lambda x: int(x)):
    section_info = tp_sections[sec_num]
    title = section_info["title"][:38]
    
    # Map to question category
    mapped_cat = tp_section_map.get(sec_num, "other")
    current = cat_count.get(mapped_cat, 0)
    
    status = "✓ OK" if current >= target_per_domain else f"✗ LOW ({current}/{target_per_domain})"
    
    print(f"Section {sec_num:2} {title:40} {target_per_domain:16} {current:8} {status:12}")

# Source verification analysis
print("\n4. SOURCE VERIFICATION STATUS (by Category)")
print("-" * 90)
print(f"{'Category':25} {'Total':6} {'With CARs Sec#':16} {'Missing CARs Sec#':16}")
print("-" * 90)

for cat in sorted(cat_count.keys()):
    cat_questions = [q for q in questions if q.get("category") == cat]
    with_cars_sec = len([q for q in cat_questions if q.get("carsSection")])
    without_cars_sec = len(cat_questions) - with_cars_sec
    
    pct_complete = int((with_cars_sec / len(cat_questions) * 100)) if cat_questions else 0
    
    print(f"{cat:25} {len(cat_questions):6} {with_cars_sec:6} ({pct_complete:3}%) {without_cars_sec:16}")

# Priority verification checklist
print("\n5. PRIORITY VERIFICATION CHECKLIST")
print("-" * 90)

# Regulations category needs high CARs coverage
reg_questions = [q for q in questions if q.get("category") == "regulations"]
reg_with_section = [q for q in reg_questions if q.get("carsSection")]

print(f"\n  REGULATIONS (Critical - all should map to specific CARs sections):")
print(f"    Total: {len(reg_questions)}")
print(f"    With specific CARs section: {len(reg_with_section)}")
print(f"    Without specific section: {len(reg_questions) - len(reg_with_section)}")

if len(reg_questions) - len(reg_with_section) > 0:
    print(f"    ⚠️  REQUIRED ACTION: Map {len(reg_questions) - len(reg_with_section)} questions to CARs sections")
    
    # Show sample
    missing_sec = [q for q in reg_questions if not q.get("carsSection")][:3]
    print(f"\n    Sample regulations questions needing CARs sections:")
    for q in missing_sec:
        src = q.get("source", "")[:60]
        print(f"      {q.get('id'):15} {src}")

# Radio coverage check
radio_questions = [q for q in questions if q.get("category") == "radio"]
print(f"\n  RADIO/TELEPHONY (TP 15263 Section 8):")
print(f"    Current questions: {len(radio_questions)}")
print(f"    Recommended minimum: 15-20")
if len(radio_questions) < 15:
    print(f"    ⚠️  UNDERREPRESENTED - consider adding {15 - len(radio_questions)}-{20 - len(radio_questions)} more questions")

# RPAS 101 integration status
print(f"\n  RPAS 101 INTEGRATION:")
rpas101_refs = len([q for q in questions if "RPAS 101" in q.get("source", "")])
print(f"    Questions referencing RPAS 101: {rpas101_refs}")
print(f"    ℹ️  RPAS 101 should support conceptual understanding for ~50-100 questions")

# Action items summary
print("\n6. ACTION ITEMS (PRIORITY ORDER)")
print("-" * 90)
print("""
  PHASE 1 - REGULATORY ACCURACY (HIGH PRIORITY)
    [ ] Map all 50 regulation questions to specific CARs sections (901.xx format)
    [ ] Cross-check against CARs_SOR-96-433_FullText.xml for accuracy
    [ ] Reference correct regulation text in rationale (not paraphrase)
    
  PHASE 2 - TP 15263 COVERAGE (MEDIUM PRIORITY)
    [ ] Verify that all 7 TP 15263 sections have representative questions
    [ ] Add questions to underrepresented domains (e.g., radio: currently {})
    [ ] Map questions to specific TP 15263 learning objectives
    
  PHASE 3 - SOURCE LINKS (MEDIUM PRIORITY)
    [ ] Add RPAS 101 references where conceptual alignment exists
    [ ] Link questions to specific AIM chapters (TC RPA guidance)
    [ ] Add NAV CANADA DAH references where airspace/NOTAM questions apply
    
  PHASE 4 - VALIDATION (LOW PRIORITY)
    [ ] Remove or reclassify any Level 1 Complex questions
    [ ] Verify no questions are BVLOS-specific (out of Advanced Pilot scope)
    [ ] Confirm all rationales reference authoritative sources
""".format(len(radio_questions)))

print("=" * 90)
