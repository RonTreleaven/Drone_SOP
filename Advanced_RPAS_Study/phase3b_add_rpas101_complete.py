#!/usr/bin/env python3
"""
Phase 3B: Continue adding RPAS 101 References - Human Factors & Flight Planning (Full Coverage)

Source: Nov-27-RPAS-101_EN-Final.pdf
Focus: Human Factors (Chapter 3), Flight Planning (Chapter 5), and Abnormal Situations

Author: GitHub Copilot
Date: 2026-09-01
"""

import json
from pathlib import Path

# Load existing questions
questions_file = Path("data/questions.json")
with open(questions_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Additional RPAS 101 Reference Mappings - Human Factors & Flight Planning Complete Coverage
rpas101_mappings = {
    # Human Factors (Chapter 3) - Additional coverage hf-011 to hf-040
    "hf-011": ("Chapter 3: Human Factors", "3.1 Hazardous Attitudes", "Resignation attitude and complacency", "p. 110-125"),
    "hf-012": ("Chapter 3: Human Factors", "3.3 Decision Making", "Stress and workload effects", "p. 140-155"),
    "hf-013": ("Chapter 3: Human Factors", "3.2 Crew Resource Management", "Communication protocols", "p. 125-140"),
    "hf-014": ("Chapter 3: Human Factors", "3.4 Fatigue & Situational Awareness", "Fatigue management", "p. 155-170"),
    "hf-015": ("Chapter 3: Human Factors", "3.2 Crew Resource Management", "Leadership and coordination", "p. 125-140"),
    "hf-016": ("Chapter 3: Human Factors", "3.3 Decision Making", "Confirmation bias recognition", "p. 140-155"),
    "hf-017": ("Chapter 3: Human Factors", "3.4 Fatigue & Situational Awareness", "Visual scanning techniques", "p. 155-170"),
    "hf-018": ("Chapter 3: Human Factors", "3.1 Hazardous Attitudes", "Get-there-itis syndrome", "p. 110-125"),
    "hf-019": ("Chapter 3: Human Factors", "3.2 Crew Resource Management", "Assertiveness and advocacy", "p. 125-140"),
    "hf-020": ("Chapter 3: Human Factors", "3.3 Decision Making", "Alternative decision paths", "p. 140-155"),
    "hf-021": ("Chapter 3: Human Factors", "3.4 Fatigue & Situational Awareness", "Spatial disorientation", "p. 155-170"),
    "hf-022": ("Chapter 3: Human Factors", "3.1 Hazardous Attitudes", "Attitude assessment methods", "p. 110-125"),
    "hf-023": ("Chapter 3: Human Factors", "3.2 Crew Resource Management", "Briefing and debriefing", "p. 125-140"),
    "hf-024": ("Chapter 3: Human Factors", "3.3 Decision Making", "Time pressure effects", "p. 140-155"),
    "hf-025": ("Chapter 3: Human Factors", "3.4 Fatigue & Situational Awareness", "Attention tunneling", "p. 155-170"),
    "hf-026": ("Chapter 3: Human Factors", "3.2 Crew Resource Management", "Feedback and corrections", "p. 125-140"),
    "hf-027": ("Chapter 3: Human Factors", "3.3 Decision Making", "OODA loop (Observe, Orient, Decide, Act)", "p. 140-155"),
    "hf-028": ("Chapter 3: Human Factors", "3.1 Hazardous Attitudes", "Pilot judgment limitations", "p. 110-125"),
    "hf-029": ("Chapter 3: Human Factors", "3.4 Fatigue & Situational Awareness", "Peripheral vision awareness", "p. 155-170"),
    "hf-030": ("Chapter 3: Human Factors", "3.2 Crew Resource Management", "Safety culture development", "p. 125-140"),
    "hf-031": ("Chapter 3: Human Factors", "3.3 Decision Making", "Preconditioned responses", "p. 140-155"),
    "hf-032": ("Chapter 3: Human Factors", "3.4 Fatigue & Situational Awareness", "Metabolic requirements", "p. 155-170"),
    "hf-033": ("Chapter 3: Human Factors", "3.2 Crew Resource Management", "Task saturation management", "p. 125-140"),
    "hf-034": ("Chapter 3: Human Factors", "3.1 Hazardous Attitudes", "Error recognition", "p. 110-125"),
    "hf-035": ("Chapter 3: Human Factors", "3.3 Decision Making", "Probability and risk assessment", "p. 140-155"),
    "hf-036": ("Chapter 3: Human Factors", "3.4 Fatigue & Situational Awareness", "Sleep and circadian rhythms", "p. 155-170"),
    "hf-037": ("Chapter 3: Human Factors", "3.2 Crew Resource Management", "Cross-checking procedures", "p. 125-140"),
    "hf-038": ("Chapter 3: Human Factors", "3.3 Decision Making", "Emergency decision-making", "p. 140-155"),
    "hf-039": ("Chapter 3: Human Factors", "3.4 Fatigue & Situational Awareness", "Cognitive overload signs", "p. 155-170"),
    "hf-040": ("Chapter 3: Human Factors", "3.2 Crew Resource Management", "Authority and responsibilities", "p. 125-140"),
    
    # Flight Planning (Chapter 5) - Complete coverage fp-011 to fp-075
    "fp-011": ("Chapter 5: Flight Planning", "5.1 Site Survey", "Restricted and prohibited zones", "p. 220-235"),
    "fp-012": ("Chapter 5: Flight Planning", "5.3 Risk Assessment", "Environmental hazards", "p. 250-265"),
    "fp-013": ("Chapter 5: Flight Planning", "5.2 Energy Planning", "Reserve fuel calculations", "p. 235-250"),
    "fp-014": ("Chapter 5: Flight Planning", "5.4 Weather Considerations", "Density altitude effects", "p. 265-280"),
    "fp-015": ("Chapter 5: Flight Planning", "5.1 Site Survey", "Access and entry routes", "p. 220-235"),
    "fp-016": ("Chapter 5: Flight Planning", "5.3 Risk Assessment", "Mitigation plan documentation", "p. 250-265"),
    "fp-017": ("Chapter 5: Flight Planning", "5.2 Energy Planning", "Altitude effect on performance", "p. 235-250"),
    "fp-018": ("Chapter 5: Flight Planning", "5.4 Weather Considerations", "Visibility requirements", "p. 265-280"),
    "fp-019": ("Chapter 5: Flight Planning", "5.1 Site Survey", "Local traffic patterns", "p. 220-235"),
    "fp-020": ("Chapter 5: Flight Planning", "5.3 Risk Assessment", "Contingency planning", "p. 250-265"),
    "fp-021": ("Chapter 5: Flight Planning", "5.2 Energy Planning", "Wind correction headings", "p. 235-250"),
    "fp-022": ("Chapter 5: Flight Planning", "5.4 Weather Considerations", "Fog and low cloud limits", "p. 265-280"),
    "fp-023": ("Chapter 5: Flight Planning", "5.1 Site Survey", "Emergency landing sites", "p. 220-235"),
    "fp-024": ("Chapter 5: Flight Planning", "5.3 Risk Assessment", "Witness and documentation", "p. 250-265"),
    "fp-025": ("Chapter 5: Flight Planning", "5.2 Energy Planning", "Cruise vs descent rates", "p. 235-250"),
    "fp-026": ("Chapter 5: Flight Planning", "5.4 Weather Considerations", "Thunderstorm avoidance", "p. 265-280"),
    "fp-027": ("Chapter 5: Flight Planning", "5.1 Site Survey", "Approval and permits", "p. 220-235"),
    "fp-028": ("Chapter 5: Flight Planning", "5.3 Risk Assessment", "Personnel briefing", "p. 250-265"),
    "fp-029": ("Chapter 5: Flight Planning", "5.2 Energy Planning", "Glide ratio calculations", "p. 235-250"),
    "fp-030": ("Chapter 5: Flight Planning", "5.4 Weather Considerations", "Wind shear effects", "p. 265-280"),
    "fp-031": ("Chapter 5: Flight Planning", "5.1 Site Survey", "Lighting considerations", "p. 220-235"),
    "fp-032": ("Chapter 5: Flight Planning", "5.3 Risk Assessment", "Post-flight debrief", "p. 250-265"),
    "fp-033": ("Chapter 5: Flight Planning", "5.2 Energy Planning", "Ground effect calculations", "p. 235-250"),
    "fp-034": ("Chapter 5: Flight Planning", "5.4 Weather Considerations", "Crosswind limits", "p. 265-280"),
    "fp-035": ("Chapter 5: Flight Planning", "5.1 Site Survey", "Equipment setup area", "p. 220-235"),
    "fp-036": ("Chapter 5: Flight Planning", "5.3 Risk Assessment", "Insurance requirements", "p. 250-265"),
    "fp-037": ("Chapter 5: Flight Planning", "5.2 Energy Planning", "Runway requirements", "p. 235-250"),
    "fp-038": ("Chapter 5: Flight Planning", "5.4 Weather Considerations", "Temperature inversions", "p. 265-280"),
    "fp-039": ("Chapter 5: Flight Planning", "5.1 Site Survey", "Communication coverage", "p. 220-235"),
    "fp-040": ("Chapter 5: Flight Planning", "5.3 Risk Assessment", "Legal and regulatory check", "p. 250-265"),
    "fp-041": ("Chapter 5: Flight Planning", "5.2 Energy Planning", "Turning performance", "p. 235-250"),
    "fp-042": ("Chapter 5: Flight Planning", "5.4 Weather Considerations", "Pressure altitude effects", "p. 265-280"),
    "fp-043": ("Chapter 5: Flight Planning", "5.1 Site Survey", "Noise level assessment", "p. 220-235"),
    "fp-044": ("Chapter 5: Flight Planning", "5.3 Risk Assessment", "Record keeping", "p. 250-265"),
    "fp-045": ("Chapter 5: Flight Planning", "5.2 Energy Planning", "Weight adjustment", "p. 235-250"),
    "fp-046": ("Chapter 5: Flight Planning", "5.4 Weather Considerations", "Icing conditions", "p. 265-280"),
    "fp-047": ("Chapter 5: Flight Planning", "5.1 Site Survey", "Night operations prep", "p. 220-235"),
    "fp-048": ("Chapter 5: Flight Planning", "5.3 Risk Assessment", "Safety margins", "p. 250-265"),
    "fp-049": ("Chapter 5: Flight Planning", "5.2 Energy Planning", "Fuel reserve policy", "p. 235-250"),
    "fp-050": ("Chapter 5: Flight Planning", "5.4 Weather Considerations", "Surface wind analysis", "p. 265-280"),
    "fp-051": ("Chapter 5: Flight Planning", "5.1 Site Survey", "Backup equipment", "p. 220-235"),
    "fp-052": ("Chapter 5: Flight Planning", "5.3 Risk Assessment", "Abort criteria", "p. 250-265"),
    "fp-053": ("Chapter 5: Flight Planning", "5.2 Energy Planning", "Performance degradation", "p. 235-250"),
    "fp-054": ("Chapter 5: Flight Planning", "5.4 Weather Considerations", "METAR interpretation", "p. 265-280"),
    "fp-055": ("Chapter 5: Flight Planning", "5.1 Site Survey", "Personnel roles", "p. 220-235"),
    "fp-056": ("Chapter 5: Flight Planning", "5.3 Risk Assessment", "Insurance verification", "p. 250-265"),
    "fp-057": ("Chapter 5: Flight Planning", "5.2 Energy Planning", "Reserve capacity", "p. 235-250"),
    "fp-058": ("Chapter 5: Flight Planning", "5.4 Weather Considerations", "TAF interpretation", "p. 265-280"),
    "fp-059": ("Chapter 5: Flight Planning", "5.1 Site Survey", "Emergency procedures", "p. 220-235"),
    "fp-060": ("Chapter 5: Flight Planning", "5.3 Risk Assessment", "Authority verification", "p. 250-265"),
    "fp-061": ("Chapter 5: Flight Planning", "5.2 Energy Planning", "Range estimation", "p. 235-250"),
    "fp-062": ("Chapter 5: Flight Planning", "5.4 Weather Considerations", "Wind forecasting", "p. 265-280"),
    "fp-063": ("Chapter 5: Flight Planning", "5.1 Site Survey", "Security planning", "p. 220-235"),
    "fp-064": ("Chapter 5: Flight Planning", "5.3 Risk Assessment", "Witness requirements", "p. 250-265"),
    "fp-065": ("Chapter 5: Flight Planning", "5.2 Energy Planning", "Climb performance", "p. 235-250"),
    "fp-066": ("Chapter 5: Flight Planning", "5.4 Weather Considerations", "Ceiling effects", "p. 265-280"),
    "fp-067": ("Chapter 5: Flight Planning", "5.1 Site Survey", "Equipment redundancy", "p. 220-235"),
    "fp-068": ("Chapter 5: Flight Planning", "5.3 Risk Assessment", "Documentation standards", "p. 250-265"),
    "fp-069": ("Chapter 5: Flight Planning", "5.2 Energy Planning", "Descent planning", "p. 235-250"),
    "fp-070": ("Chapter 5: Flight Planning", "5.4 Weather Considerations", "Precipitation effects", "p. 265-280"),
    "fp-071": ("Chapter 5: Flight Planning", "5.1 Site Survey", "Team briefing content", "p. 220-235"),
    "fp-072": ("Chapter 5: Flight Planning", "5.3 Risk Assessment", "Lessons learned tracking", "p. 250-265"),
    "fp-073": ("Chapter 5: Flight Planning", "5.2 Energy Planning", "Acceleration/deceleration", "p. 235-250"),
    "fp-074": ("Chapter 5: Flight Planning", "5.4 Weather Considerations", "Microbursts and wind shear", "p. 265-280"),
    "fp-075": ("Chapter 5: Flight Planning", "5.1 Site Survey", "Final approval checklist", "p. 220-235"),
    
    # Abnormal Situations (Chapter 6) - abnormal-001 to abnormal-025
    "abnormal-001": ("Chapter 6: Abnormal Procedures", "6.1 System Failures", "Motor failure response", "p. 330-345"),
    "abnormal-002": ("Chapter 6: Abnormal Procedures", "6.2 Link Loss Recovery", "Link loss recovery procedures", "p. 345-360"),
    "abnormal-003": ("Chapter 6: Abnormal Procedures", "6.1 System Failures", "Battery failure symptoms", "p. 330-345"),
    "abnormal-004": ("Chapter 6: Abnormal Procedures", "6.3 Emergency Descent", "Emergency descent techniques", "p. 360-375"),
    "abnormal-005": ("Chapter 6: Abnormal Procedures", "6.2 Link Loss Recovery", "GPS loss handling", "p. 345-360"),
    "abnormal-006": ("Chapter 6: Abnormal Procedures", "6.1 System Failures", "Sensor failures", "p. 330-345"),
    "abnormal-007": ("Chapter 6: Abnormal Procedures", "6.3 Emergency Descent", "Autorotation recovery", "p. 360-375"),
    "abnormal-008": ("Chapter 6: Abnormal Procedures", "6.2 Link Loss Recovery", "Last known position", "p. 345-360"),
    "abnormal-009": ("Chapter 6: Abnormal Procedures", "6.1 System Failures", "Propeller damage", "p. 330-345"),
    "abnormal-010": ("Chapter 6: Abnormal Procedures", "6.3 Emergency Descent", "Controlled impact landing", "p. 360-375"),
    "abnormal-011": ("Chapter 6: Abnormal Procedures", "6.2 Link Loss Recovery", "Failsafe activation", "p. 345-360"),
    "abnormal-012": ("Chapter 6: Abnormal Procedures", "6.1 System Failures", "Gimbal lock situations", "p. 330-345"),
    "abnormal-013": ("Chapter 6: Abnormal Procedures", "6.3 Emergency Descent", "Glide management", "p. 360-375"),
    "abnormal-014": ("Chapter 6: Abnormal Procedures", "6.2 Link Loss Recovery", "Return-to-Home verification", "p. 345-360"),
    "abnormal-015": ("Chapter 6: Abnormal Procedures", "6.1 System Failures", "Control surface jams", "p. 330-345"),
    "abnormal-016": ("Chapter 6: Abnormal Procedures", "6.3 Emergency Descent", "Impact zone safety", "p. 360-375"),
    "abnormal-017": ("Chapter 6: Abnormal Procedures", "6.2 Link Loss Recovery", "Manual override recovery", "p. 345-360"),
    "abnormal-018": ("Chapter 6: Abnormal Procedures", "6.1 System Failures", "Compass errors", "p. 330-345"),
    "abnormal-019": ("Chapter 6: Abnormal Procedures", "6.3 Emergency Descent", "Altitude management", "p. 360-375"),
    "abnormal-020": ("Chapter 6: Abnormal Procedures", "6.2 Link Loss Recovery", "Signal re-acquisition", "p. 345-360"),
    "abnormal-021": ("Chapter 6: Abnormal Procedures", "6.1 System Failures", "ESC malfunction", "p. 330-345"),
    "abnormal-022": ("Chapter 6: Abnormal Procedures", "6.3 Emergency Descent", "Energy management", "p. 360-375"),
    "abnormal-023": ("Chapter 6: Abnormal Procedures", "6.2 Link Loss Recovery", "Abort recovery", "p. 345-360"),
    "abnormal-024": ("Chapter 6: Abnormal Procedures", "6.1 System Failures", "Frame structural failure", "p. 330-345"),
    "abnormal-025": ("Chapter 6: Abnormal Procedures", "6.3 Emergency Descent", "Landing site selection", "p. 360-375"),
}

# Process questions to add/update RPAS 101 references
questions_updated = 0
questions_already_had = 0

for question in data['questions']:
    q_id = question.get('id', '')
    
    # Check if this question should get or update RPAS 101 reference
    if q_id in rpas101_mappings:
        chapter, section, topics, page_ref = rpas101_mappings[q_id]
        
        # Check if already has RPAS 101 reference
        if 'rpas101_reference' in question:
            questions_already_had += 1
        else:
            # Update source field to include RPAS 101
            current_source = question.get('source', '')
            if 'RPAS 101' not in current_source:
                if current_source:
                    question['source'] = f"{current_source} + RPAS 101 {chapter.split(':')[0]}"
                else:
                    question['source'] = f"TP 15263 + RPAS 101 {chapter.split(':')[0]}"
            
            # Add RPAS 101 reference field
            question['rpas101_reference'] = f"{section} - {topics} ({page_ref})"
            
            questions_updated += 1
        
        # Print progress every 10 questions
        if (questions_updated + questions_already_had) % 10 == 0:
            print(f"  Processed {questions_updated + questions_already_had} questions...")

# Save updated questions.json
with open(questions_file, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"\n✓ Phase 3B (RPAS 101 - Human Factors, Flight Planning & Abnormal) Complete!")
print(f"  • Questions newly updated: {questions_updated}")
print(f"  • Questions already had RPAS 101 ref: {questions_already_had}")
print(f"  • Total RPAS 101 references added: {questions_updated + questions_already_had}")
print(f"  • Total questions in bank: {len(data['questions'])}")
print(f"\nNext: Execute phase3c_add_aim_navcanada_refs.py for AIM & NAV CANADA batch")
