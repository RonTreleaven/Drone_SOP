#!/usr/bin/env python3
"""
PHASE 2: QUESTION GAP FILLER
Generates structured question templates for underrepresented domains
Uses TP 15263 learning objectives as framework
"""

import json
from pathlib import Path

# Load TP 15263 requirements
tp_file = Path(__file__).parent / "docs" / "knowledge_requirements_extracted.json"
questions_file = Path(__file__).parent / "data" / "questions.json"

with open(tp_file, 'r', encoding='utf-8') as f:
    tp_data = json.load(f)

with open(questions_file, 'r', encoding='utf-8') as f:
    q_data = json.load(f)

print("=" * 100)
print("PHASE 2: COVERAGE GAP ANALYSIS & QUESTION GENERATION FRAMEWORK")
print("=" * 100)

# Map TP 15263 sections to question categories
section_to_category = {
    "2": "aircraft-systems",      # RPA airframes, power plants, propulsion and systems
    "3": "human-factors",         # Human Factors  
    "4": "weather",               # Meteorology
    "5": "navigation",            # Navigation  ← GAP
    "6": "flight-planning",       # Flight Operations (includes performance, W&B)  ← GAP
    "7": "aircraft-systems",      # Theory of Flight
    "8": "radio"                  # Radiotelephony  ← GAP
}

questions = q_data.get("questions", [])

# Identify critical gaps
print("\nTP 15263 SECTION MAPPING & GAPS:\n")
print(f"{'Section':10} {'Topic':50} {'Current':10} {'Target':10} {'Gap':10}")
print("-" * 100)

gaps = {}
for section, category in section_to_category.items():
    section_data = tp_data.get("sections", {}).get(section, {})
    title = section_data.get("title", "")[:50]
    knowledge_areas = len(section_data.get("knowledge_areas", []))
    
    current = len([q for q in questions if q.get("category") == category])
    target = 77  # Balanced distribution (525/7 sections ≈ 75)
    gap = max(0, target - current)
    
    print(f"Section {section} {title:50} {current:10} {target:10} {gap:10}")
    
    if gap > 0:
        gaps[section] = {
            "category": category,
            "current": current,
            "target": target,
            "gap": gap,
            "knowledge_areas": knowledge_areas,
            "title": section_data.get("title")
        }

print("\n" + "=" * 100)
print("PRIORITY GAPS (Needing Most Questions)")
print("=" * 100)

sorted_gaps = sorted(gaps.items(), key=lambda x: x[1]['gap'], reverse=True)
for section, info in sorted_gaps:
    print(f"\nSection {section}: {info['title']}")
    print(f"  Current questions: {info['current']}")
    print(f"  Target: {info['target']}")
    print(f"  Questions needed: {info['gap']}")
    print(f"  Knowledge areas in TP 15263: {info['knowledge_areas']}")

# Extract learning objectives from TP 15263 for each critical gap
print("\n" + "=" * 100)
print("LEARNING OBJECTIVES FOR GAP DOMAINS")
print("=" * 100)

for section in ["5", "6", "8"]:  # Navigation, Flight Ops, Radio
    if section not in tp_data.get("sections", {}):
        continue
    
    section_data = tp_data["sections"][section]
    title = section_data.get("title", "")
    areas = section_data.get("knowledge_areas", [])
    
    print(f"\n--- SECTION {section}: {title} ---")
    
    # Show first 10 learning areas
    for area in areas[:10]:
        area_name = area.get("name", "")
        if area_name and area_name.strip():
            print(f"  • {area_name}")
            
            # Show subtopics
            for sub in area.get("subtopics", [])[:2]:
                sub_name = sub.get("name", "")
                if sub_name and sub_name.strip():
                    print(f"      - {sub_name}")

# Generate question template framework
print("\n" + "=" * 100)
print("QUESTION GENERATION FRAMEWORK")
print("=" * 100)

template = """
NEW QUESTION TEMPLATE (Adapt for each learning objective):

ID: [auto-generate: nav-001, nav-002, etc.]
Category: [navigation|flight-planning|radio]
Difficulty: [easy|medium|hard] (mix evenly)
Question: [Based on TP 15263 learning objective]
Choices: [4 choices - only 1 correct, others plausible]
answerIndex: [0-3]
Rationale: [Cite specific TP 15263 section + source document]
Source: "TP 15263 Section X.Y + [CARs/RPAS 101/AIM reference]"
carsSection: [if applicable, e.g., "901.27"]

SOURCES TO USE:
- TP 15263: Learning objective framework
- Nov-27-RPAS-101_EN-Final.pdf: Explanations + examples
- aim-2026-1_rpa_en_March_19_2026.pdf: Procedures
- CARs: Regulatory backing
- NAVCANADA_VFR-Phraseology.pdf: Radio questions
"""

print(template)

# Export gap analysis for manual question creation
export_file = Path(__file__).parent / "phase2_gap_analysis.json"
export_data = {
    "timestamp": "2026-09-01",
    "current_total": len(questions),
    "target_total": 525,  # Adjust if needed
    "gaps_by_priority": [
        {
            "section": section,
            "category": info["category"],
            "title": info["title"],
            "current": info["current"],
            "target": info["target"],
            "questions_needed": info["gap"],
            "knowledge_areas_in_tp": info["knowledge_areas"]
        }
        for section, info in sorted_gaps
    ]
}

with open(export_file, 'w', encoding='utf-8') as f:
    json.dump(export_data, f, indent=2)

print(f"\n✓ Gap analysis exported to: phase2_gap_analysis.json")

print("\n" + "=" * 100)
print("RECOMMENDED APPROACH FOR PHASE 2")
print("=" * 100)

print("""
Given the large number of questions needed (+161), recommend STAGED approach:

STAGE 2A (QUICK WINS - 30 questions):
  • Radio phraseology basics (10-15 questions)
    - Common frequencies, emergency procedures, call signs
    - Source: NAVCANADA_VFR-Phraseology.pdf
  • Navigation coordinate systems (10-15 questions)
    - Latitude/longitude, grid references, magnetic variation
    - Source: TP 15263 Section 5 + RPAS 101

STAGE 2B (MEDIUM EFFORT - 60 questions):
  • Flight operations + decision-making (30-35 questions)
    - Site survey scenarios (CARs 901.27)
    - Weight & balance, performance considerations
    - Source: TP 15263 Section 6 + AIM
  • Navigation calculations + flight planning (25-30 questions)
    - Wind corrections, distance/time calculations
    - Chart interpretation, waypoint planning
    - Source: TP 15263 Section 5

STAGE 2C (COMPREHENSIVE - 70 questions):
  • Advanced radio procedures (15-20 questions)
  • Navigation theory depth (20-25 questions)
  • Flight operations scenarios (25-30 questions)

TOOLS TO HELP:
1. Use phase2_new_questions_template.py to generate questions in batch
2. Reference TP 15263 learning objectives (extracted JSON)
3. Cross-check answers against authoritative sources
4. Maintain consistent difficulty distribution

TIMELINE:
  Stage 2A: 2-3 hours (30 questions)
  Stage 2B: 4-5 hours (60 questions)
  Stage 2C: 6-8 hours (70 questions)
  TOTAL: ~14 hours of focused work
""")

print("=" * 100)
