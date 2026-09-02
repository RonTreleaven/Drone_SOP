#!/usr/bin/env python3
"""
Analyze Advanced RPAS Knowledge Requirements and map to current questions

Identifies:
1. All Advanced topics from Knowledge Requirements document
2. Current question coverage
3. Gaps and areas needing more questions
4. Recommendations for new question generation
"""

import json
from pathlib import Path
from collections import defaultdict

# Load current questions
with open(Path("data/questions.json"), 'r', encoding='utf-8') as f:
    data = json.load(f)

# Key Advanced topics extracted from the Knowledge Requirements document
# These are the topics that require Advanced pilot knowledge
advanced_topics = {
    # Aeronautics Act & CARs Part I
    "Aeronautics Act Definitions": ["aerodrome", "airport", "pilot-in-command"],
    "CARs Application": ["indoor operations exemption", "underground operations exemption", "military aircraft"],
    "Compliance & Inspection": ["aviation documents inspection", "record keeping", "computer records"],
    
    # Aerodromes & Airports (CARs 301-302)
    "Aerodrome Prohibitions": ["movement area restrictions", "vehicle parking", "aircraft towing at night", "marker interference"],
    "Aerodrome Safety": ["fire prevention", "smoking restrictions", "open flame", "bird control"],
    "Aerodrome Operations": ["operator approval", "ATC approval", "lighting requirements", "obstruction removal"],
    "Airport Prohibitions": ["airport certificate requirements", "movement area access", "taxiway operations"],
    "Airport Certificate": ["airport certificate conditions", "use restrictions", "operational limits"],
    
    # Forest Fire Operations (CARs 601)
    "Forest Fire Restrictions": ["forest fire area operations", "minimum altitude (3000 ft AGL)", "fire control operations"],
    "Fire Control Authorization": ["fire control authority authorization", "NOTAM compliance", "special operations"],
    "Laser Light Shows": ["laser safety", "directed light source restrictions", "NOTAM requirements for laser"],
    
    # Operating & Flight Rules (CARs 602)
    "Aerodrome Traffic Rules": ["traffic pattern avoidance", "circuit turns", "runway entry procedures"],
    "VFR Minimums": ["minimum operating conditions", "uncontrolled airspace rules", "visibility requirements"],
    "Mandatory Frequency (MF)": ["MF area procedures", "MF reporting", "ground station communication", "approach procedures"],
    "MF Circuit Procedures": ["downwind reporting", "final approach reporting", "clear of surface reporting"],
    "Radio Communication Failure": ["VFR communication failure procedures", "IFR communication failure procedures", "transponder code 7600"],
    "Two-way Radio Failure": ["Class B/C/D airspace failure", "landing procedures", "shortest route exits"],
    "Continuous Listening Watch": ["frequency monitoring", "radio watch procedures", "communication protocols"],
    "ESCAT Plan": ["emergency situation procedures", "ESCAT notification", "position reporting requirements"],
    
    # Munitions & Special Equipment (CARs 606)
    "Weapons Restriction": ["weapons not permitted", "ammunition restrictions", "authorization required"],
    "War Equipment": ["munitions of war", "carriage restrictions", "Canadian aircraft requirements"],
    
    # Airspace & Navigation
    "Airspace Classification": ["Class A airspace", "Class B airspace", "Class C airspace", "Class D airspace", "Class E airspace", "Class F airspace", "Class G airspace"],
    "Control Zones": ["control zone procedures", "transition areas", "terminal control areas"],
    "Restricted Airspace": ["restricted area operations", "prohibited areas", "danger areas", "advisory areas"],
    "Special Use Airspace": ["military operating areas", "alert areas", "parachute jump areas", "training areas"],
    "ADIZ Operations": ["air defence identification zone", "ADIZ reporting", "transponder requirements"],
    
    # Advanced Navigation
    "CMNPS Airspace": ["Canadian Minimum Navigation Performance Specifications", "RNPC requirements", "GNSS operations"],
    "Navigation Precision": ["positioning accuracy", "GPS errors", "navigation equipment requirements"],
    
    # Weather & Conditions
    "Forest Fire Weather": ["smoke effects on visibility", "air quality impacts", "thermal effects in fire areas"],
    "Meteorological Impact": ["weather briefing procedures", "METAR interpretation", "TAF understanding"],
    
    # Environmental & Safety
    "Bird Strike Prevention": ["wildlife management", "bird control procedures", "wildlife areas"],
    "Noise Abatement": ["noise sensitive areas", "turn restrictions", "altitude compliance"],
}

# Analyze current question coverage
topic_coverage = defaultdict(list)
category_coverage = defaultdict(int)

for question in data['questions']:
    q_id = question.get('id')
    question_text = question.get('question', '').lower()
    rationale = question.get('rationale', '').lower()
    
    category = question.get('category', '')
    category_coverage[category] += 1
    
    # Check which advanced topics are covered
    for topic, keywords in advanced_topics.items():
        for keyword in keywords:
            if keyword.lower() in question_text or keyword.lower() in rationale:
                topic_coverage[topic].append(q_id)
                break

# Generate report
print("=" * 100)
print("ADVANCED RPAS KNOWLEDGE REQUIREMENTS - GAP ANALYSIS")
print("=" * 100)

print("\n[1] TOPIC COVERAGE ANALYSIS")
print("-" * 100)

topics_with_coverage = []
topics_without_coverage = []

for topic in sorted(advanced_topics.keys()):
    covered_ids = set(topic_coverage.get(topic, []))
    num_questions = len(covered_ids)
    
    if num_questions == 0:
        topics_without_coverage.append((topic, advanced_topics[topic]))
        print(f"  ✗ {topic:40s} : {num_questions:2d} questions (NO COVERAGE)")
    elif num_questions == 1:
        print(f"  ⚠ {topic:40s} : {num_questions:2d} question  (LIMITED)")
    elif num_questions <= 2:
        print(f"  ~ {topic:40s} : {num_questions:2d} questions (BASIC)")
    elif num_questions <= 4:
        print(f"  ✓ {topic:40s} : {num_questions:2d} questions (GOOD)")
    else:
        print(f"  ✓✓ {topic:40s} : {num_questions:2d} questions (EXCELLENT)")
        if num_questions == 0:
            topics_without_coverage.append((topic, advanced_topics[topic]))
            print(f"  [NO] {topic:40s} : {num_questions:2d} questions (NO COVERAGE)")
        elif num_questions == 1:
            print(f"  [LIM] {topic:40s} : {num_questions:2d} question  (LIMITED)")
        elif num_questions <= 2:
            print(f"  [BAS] {topic:40s} : {num_questions:2d} questions (BASIC)")
        elif num_questions <= 4:
            print(f"  [GD] {topic:40s} : {num_questions:2d} questions (GOOD)")
        else:
            print(f"  [EXC] {topic:40s} : {num_questions:2d} questions (EXCELLENT)")
        topics_with_coverage.append(topic)

print(f"\n[2] COVERAGE SUMMARY")
print("-" * 100)
total_topics = len(advanced_topics)
covered_topics = len(topics_with_coverage)
uncovered_topics = len(topics_without_coverage)

print(f"  Total Advanced Topics:      {total_topics}")
print(f"  Topics with Coverage:       {covered_topics} ({100*covered_topics/total_topics:.0f}%)")
print(f"  Topics WITHOUT Coverage:    {uncovered_topics} ({100*uncovered_topics/total_topics:.0f}%)")

print(f"\n[3] TOPICS NEEDING MORE QUESTIONS (NO COVERAGE or LIMITED)")
print("-" * 100)

priority_topics = []
for topic, keywords in topics_without_coverage:
    print(f"\n  🔴 {topic} (PRIORITY)")
    print(f"     Keywords: {', '.join(keywords[:3])}")
    priority_topics.append(topic)

print(f"\n[4] CATEGORY DISTRIBUTION")
print("-" * 100)
for cat in sorted(category_coverage.keys()):
    count = category_coverage[cat]
    print(f"  {cat:20s} : {count:3d} questions")

print(f"\n[5] RECOMMENDATIONS FOR NEW QUESTIONS")
print("-" * 100)
print(f"\n  Priority: Generate questions for {len(priority_topics)} uncovered topics")
print(f"\n  High Priority Topics (Advanced-only):")
for i, topic in enumerate(priority_topics[:5], 1):
    print(f"    {i}. {topic}")

print(f"\n  Suggested approach:")
print(f"    • Generate 3-5 questions per uncovered topic")
print(f"    • Focus on CARS citations and specific regulations")
print(f"    • Link to AIM sections where applicable")
print(f"    • Include real-world scenarios for Advanced operations")

print("\n" + "=" * 100)

# Save analysis to JSON
analysis_output = {
    "total_advanced_topics": total_topics,
    "topics_with_coverage": covered_topics,
    "topics_without_coverage": uncovered_topics,
    "coverage_percentage": f"{100*covered_topics/total_topics:.0f}%",
    "uncovered_topics": [t[0] for t in topics_without_coverage],
    "category_distribution": dict(category_coverage),
    "total_questions": len(data['questions'])
}

with open(Path("docs/advanced_gap_analysis.json"), 'w', encoding='utf-8') as f:
    json.dump(analysis_output, f, indent=2)

print(f"✓ Analysis saved to docs/advanced_gap_analysis.json")
