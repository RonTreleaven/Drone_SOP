#!/usr/bin/env python3
"""
Analyze Advanced RPAS Knowledge Requirements and map to current questions
"""

import json
from pathlib import Path
from collections import defaultdict

# Load current questions
with open(Path("data/questions.json"), 'r', encoding='utf-8') as f:
    data = json.load(f)

# Key Advanced topics
advanced_topics = {
    "ADIZ Operations": ["air defence identification zone"],
    "Aerodrome Operations": ["operator approval", "ATC approval"],
    "Aerodrome Prohibitions": ["movement area restrictions", "towing"],
    "Aerodrome Safety": ["fire prevention", "smoking"],
    "Aerodrome Traffic Rules": ["traffic pattern", "circuit turns"],
    "Aeronautics Act Definitions": ["aerodrome", "airport"],
    "Airport Certificate": ["certificate requirements"],
    "Airport Prohibitions": ["movement area access"],
    "Airspace Classification": ["Class A", "Class B", "Class C"],
    "Bird Strike Prevention": ["wildlife management"],
    "CARs Application": ["indoor operations"],
    "CMNPS Airspace": ["navigation performance"],
    "Compliance & Inspection": ["aviation documents"],
    "Continuous Listening Watch": ["frequency monitoring"],
    "Control Zones": ["control zone procedures"],
    "ESCAT Plan": ["emergency situation"],
    "Fire Control Authorization": ["fire control authority"],
    "Forest Fire Restrictions": ["forest fire area"],
    "Forest Fire Weather": ["smoke effects"],
    "Laser Light Shows": ["laser safety"],
    "MF Circuit Procedures": ["downwind reporting"],
    "Mandatory Frequency (MF)": ["MF reporting"],
    "Meteorological Impact": ["weather briefing"],
    "Navigation Precision": ["positioning accuracy"],
    "Noise Abatement": ["noise sensitive"],
    "Radio Communication Failure": ["communication failure"],
    "Restricted Airspace": ["restricted area"],
    "Special Use Airspace": ["military operating"],
    "Two-way Radio Failure": ["radio failure"],
    "VFR Minimums": ["minimum operating"],
    "War Equipment": ["munitions of war"],
    "Weapons Restriction": ["weapons not permitted"],
}

# Check coverage
topic_coverage = defaultdict(int)
for question in data['questions']:
    question_text = question.get('question', '').lower()
    rationale = question.get('rationale', '').lower()
    combined = question_text + " " + rationale
    
    for topic, keywords in advanced_topics.items():
        for keyword in keywords:
            if keyword.lower() in combined:
                topic_coverage[topic] += 1
                break

print("="*100)
print("ADVANCED TOPICS COVERAGE UPDATE")
print("="*100)

print("\nTOPIC COVERAGE:")
print("-"*100)

no_coverage = 0
limited = 0
good = 0
excellent = 0

for topic in sorted(advanced_topics.keys()):
    count = topic_coverage.get(topic, 0)
    if count == 0:
        status = "[NONE]"
        no_coverage += 1
    elif count == 1:
        status = "[1-Q]"
        limited += 1
    elif count <= 3:
        status = "[FEW]"
        good += 1
    else:
        status = "[MANY]"
        excellent += 1
    print(f"  {status} {topic:40s} : {count:2d} questions")

print(f"\nCOVERAGE SUMMARY:")
print("-"*100)
total = len(advanced_topics)
print(f"  No Coverage:       {no_coverage} ({100*no_coverage/total:.0f}%)")
print(f"  Limited (1 q):     {limited} ({100*limited/total:.0f}%)")
print(f"  Good (2-3 q):      {good} ({100*good/total:.0f}%)")
print(f"  Excellent (4+ q):  {excellent} ({100*excellent/total:.0f}%)")

print(f"\nQUESTION STATISTICS:")
print("-"*100)
print(f"  Total Questions: {len(data['questions'])}")
print(f"  Advanced Topics: {total}")
print(f"  Average/Topic:   {len(data['questions'])/total:.1f}")

print("\n" + "="*100)
