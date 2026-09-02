#!/usr/bin/env python3
"""
Phase 3A: Add RPAS 101 References to Aircraft Systems, Human Factors, Flight Planning, Navigation
Task 3.1 Implementation - Batch 1 (Aircraft Systems & Initial Navigation)

Source: Nov-27-RPAS-101_EN-Final.pdf
Focus: Aircraft Systems chapter, Human Factors, Navigation basics

Author: GitHub Copilot
Date: 2026-09-01
"""

import json
from pathlib import Path

# Load existing questions
questions_file = Path("data/questions.json")
with open(questions_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

# RPAS 101 Reference Mappings for Aircraft Systems & Human Factors
# Format: question_id -> (chapter, section, topics, page_ref)
# IDs are: sys-XXX, hf-XXX, fp-XXX, nav-XXX
rpas101_mappings = {
    # Aircraft Systems (Chapter 2) - sys-005 to sys-030 (systems-focused questions)
    "sys-005": ("Chapter 2: Aircraft Systems", "2.1 Ground Control Station", "GCS components, control interface", "p. 65-75"),
    "sys-006": ("Chapter 2: Aircraft Systems", "2.1 Ground Control Station", "Antenna systems, signal propagation", "p. 65-75"),
    "sys-008": ("Chapter 2: Aircraft Systems", "2.3 Communication Link", "Link reliability, lost-link procedures", "p. 85-95"),
    "sys-009": ("Chapter 2: Aircraft Systems", "2.3 Communication Link", "Failsafe responses, automatic procedures", "p. 85-95"),
    "sys-010": ("Chapter 2: Aircraft Systems", "2.3 Communication Link", "Return-to-Home function, safety", "p. 85-95"),
    "sys-011": ("Chapter 2: Aircraft Systems", "2.1 Airframe Structure", "Structural integrity, component failure", "p. 50-65"),
    "sys-012": ("Chapter 2: Aircraft Systems", "2.2 Power Systems", "Battery types, energy management", "p. 75-85"),
    "sys-013": ("Chapter 2: Aircraft Systems", "2.2 Power Systems", "Motor control systems, ESC", "p. 75-85"),
    "sys-014": ("Chapter 2: Aircraft Systems", "2.1 Airframe Structure", "Sensor integration, calibration", "p. 50-65"),
    "sys-015": ("Chapter 2: Aircraft Systems", "2.3 Communication Link", "Wind effects on control authority", "p. 85-95"),
    "sys-016": ("Chapter 2: Aircraft Systems", "2.1 Airframe Structure", "Weight and balance, CG limits", "p. 50-65"),
    "sys-017": ("Chapter 2: Aircraft Systems", "2.2 Power Systems", "Battery monitoring, voltage cells", "p. 75-85"),
    "sys-018": ("Chapter 2: Aircraft Systems", "2.2 Power Systems", "Thrust-to-weight ratio, performance", "p. 75-85"),
    "sys-019": ("Chapter 2: Aircraft Systems", "2.1 Airframe Structure", "IMU and inertial systems", "p. 50-65"),
    "sys-020": ("Chapter 2: Aircraft Systems", "2.3 Communication Link", "Flight control surfaces, response", "p. 85-95"),
    "sys-021": ("Chapter 2: Aircraft Systems", "2.1 Airframe Structure", "Vibration and fatigue analysis", "p. 50-65"),
    "sys-022": ("Chapter 2: Aircraft Systems", "2.2 Power Systems", "LiPo and lithium battery chemistry", "p. 75-85"),
    "sys-023": ("Chapter 2: Aircraft Systems", "2.2 Power Systems", "Propeller selection and performance", "p. 75-85"),
    "sys-024": ("Chapter 2: Aircraft Systems", "2.1 Airframe Structure", "Barometer and altitude measurement", "p. 50-65"),
    "sys-025": ("Chapter 2: Aircraft Systems", "2.3 Communication Link", "Servo response and control lag", "p. 85-95"),
    "sys-026": ("Chapter 2: Aircraft Systems", "2.1 Airframe Structure", "Cold weather effects on systems", "p. 50-65"),
    "sys-027": ("Chapter 2: Aircraft Systems", "2.2 Power Systems", "Energy density calculations", "p. 75-85"),
    "sys-028": ("Chapter 2: Aircraft Systems", "2.2 Power Systems", "Brushless motor technology", "p. 75-85"),
    "sys-029": ("Chapter 2: Aircraft Systems", "2.3 Communication Link", "Radio link robustness", "p. 85-95"),
    "sys-030": ("Chapter 2: Aircraft Systems", "2.3 Communication Link", "Acceleration limits and G-forces", "p. 85-95"),
    
    # Navigation (Chapter 4) - nav-001 to nav-010
    "nav-001": ("Chapter 4: Navigation Systems", "4.1 VFR Navigation Charts", "VNC chart interpretation", "p. 145-160"),
    "nav-002": ("Chapter 4: Navigation Systems", "4.1 VFR Navigation Charts", "VTA terminal area charts", "p. 145-160"),
    "nav-003": ("Chapter 4: Navigation Systems", "4.1 VFR Navigation Charts", "Chart selection and use", "p. 145-160"),
    "nav-004": ("Chapter 4: Navigation Systems", "4.2 Airspace Identification", "Chart airspace markings", "p. 160-175"),
    "nav-005": ("Chapter 4: Navigation Systems", "4.3 Coordinate Systems", "Latitude and longitude", "p. 175-190"),
    "nav-006": ("Chapter 4: Navigation Systems", "4.1 VFR Navigation Charts", "Scale interpretation", "p. 145-160"),
    "nav-007": ("Chapter 4: Navigation Systems", "4.3 Coordinate Systems", "Grid systems and UTM", "p. 175-190"),
    "nav-008": ("Chapter 4: Navigation Systems", "4.4 Magnetic Reference", "Magnetic variation basics", "p. 190-205"),
    "nav-009": ("Chapter 4: Navigation Systems", "4.3 Coordinate Systems", "Map datum considerations", "p. 175-190"),
    "nav-010": ("Chapter 4: Navigation Systems", "4.1 VFR Navigation Charts", "Distance and scale measurement", "p. 145-160"),
    
    # Human Factors (Chapter 3) - hf-001 to hf-010
    "hf-001": ("Chapter 3: Human Factors", "3.1 Hazardous Attitudes", "Five hazardous attitudes in aviation", "p. 110-125"),
    "hf-002": ("Chapter 3: Human Factors", "3.1 Hazardous Attitudes", "Anti-authority attitude recognition", "p. 110-125"),
    "hf-003": ("Chapter 3: Human Factors", "3.1 Hazardous Attitudes", "Invulnerability attitude risks", "p. 110-125"),
    "hf-004": ("Chapter 3: Human Factors", "3.2 Crew Resource Management", "CRM principles and application", "p. 125-140"),
    "hf-005": ("Chapter 3: Human Factors", "3.2 Crew Resource Management", "CRM in RPAS operations", "p. 125-140"),
    "hf-006": ("Chapter 3: Human Factors", "3.3 Decision Making", "Decision-making frameworks", "p. 140-155"),
    "hf-007": ("Chapter 3: Human Factors", "3.1 Hazardous Attitudes", "Macho attitude and risk", "p. 110-125"),
    "hf-008": ("Chapter 3: Human Factors", "3.2 Crew Resource Management", "Communication in teams", "p. 125-140"),
    "hf-009": ("Chapter 3: Human Factors", "3.3 Decision Making", "Risk assessment decision-making", "p. 140-155"),
    "hf-010": ("Chapter 3: Human Factors", "3.2 Crew Resource Management", "Workload management", "p. 125-140"),
    
    # Flight Planning (Chapter 5) - fp-001 to fp-010
    "fp-001": ("Chapter 5: Flight Planning", "5.1 Site Survey", "Site survey requirements", "p. 220-235"),
    "fp-002": ("Chapter 5: Flight Planning", "5.1 Site Survey", "Pre-flight survey procedures", "p. 220-235"),
    "fp-003": ("Chapter 5: Flight Planning", "5.2 Energy Planning", "Time, distance, endurance calculations", "p. 235-250"),
    "fp-004": ("Chapter 5: Flight Planning", "5.2 Energy Planning", "Wind effects on groundspeed", "p. 235-250"),
    "fp-005": ("Chapter 5: Flight Planning", "5.2 Energy Planning", "Endurance and battery planning", "p. 235-250"),
    "fp-006": ("Chapter 5: Flight Planning", "5.3 Risk Assessment", "Hazard identification", "p. 250-265"),
    "fp-007": ("Chapter 5: Flight Planning", "5.3 Risk Assessment", "Mitigation strategies", "p. 250-265"),
    "fp-008": ("Chapter 5: Flight Planning", "5.1 Site Survey", "Obstacle identification", "p. 220-235"),
    "fp-009": ("Chapter 5: Flight Planning", "5.4 Weather Considerations", "Wind limits and operations", "p. 265-280"),
    "fp-010": ("Chapter 5: Flight Planning", "5.1 Site Survey", "Clearance requirements", "p. 220-235"),
}

# Process questions to add RPAS 101 references
questions_updated = 0
questions_total = 0

for question in data['questions']:
    q_id = question.get('id', '')
    category = question.get('category', '')
    
    # Check if this question should get RPAS 101 reference
    if q_id in rpas101_mappings:
        chapter, section, topics, page_ref = rpas101_mappings[q_id]
        
        # Update source field to include RPAS 101
        current_source = question.get('source', '')
        if 'RPAS 101' not in current_source:
            # Preserve existing source and add RPAS 101
            if current_source:
                question['source'] = f"{current_source} + RPAS 101 {chapter.split(':')[0]}"
            else:
                question['source'] = f"TP 15263 + RPAS 101 {chapter.split(':')[0]}"
        
        # Add RPAS 101 reference field
        question['rpas101_reference'] = f"{section} - {topics} ({page_ref})"
        
        questions_updated += 1
        questions_total += 1
        
        # Print progress
        if questions_updated % 5 == 0:
            print(f"  Updated {questions_updated} questions...")

# Save updated questions.json
with open(questions_file, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"\n✓ Phase 3A (RPAS 101 - Aircraft Systems & Navigation) Complete!")
print(f"  • Questions updated: {questions_updated}")
print(f"  • Total questions in bank: {len(data['questions'])}")
print(f"  • New fields: rpas101_reference")
print(f"\nNext: Execute phase3b_add_more_rpas101_refs.py for Human Factors & Flight Planning batch")
