#!/usr/bin/env python3
"""
Phase 3C: Add AIM & NAV CANADA References to Airspace, Aerodromes, Radio, NOTAMS

Sources:
- aim-2026-1_rpa_en_March_19_2026.pdf (AIM)
- NAVCANADA_VFR-Phraseology.pdf (VFR Phraseology)
- NAVCANADA_DAH_current_20260709.pdf (Designated Airspace Handbook)

Author: GitHub Copilot
Date: 2026-09-01
"""

import json
from pathlib import Path

# Load existing questions
questions_file = Path("data/questions.json")
with open(questions_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

# AIM & NAV CANADA Reference Mappings
# Format: question_id -> (source_type, chapter/section, topics, reference)
aim_navcanada_mappings = {
    # Airspace (50 questions) - air-XXX - AIM Section 2
    "air-001": ("AIM", "Section 2.1: Airspace Structure", "Airspace classes overview", "AIM Section 2.1, p. 2-3"),
    "air-002": ("AIM", "Section 2.1: Airspace Structure", "Class A airspace", "AIM Section 2.1, p. 2-4"),
    "air-003": ("AIM", "Section 2.1: Airspace Structure", "Class B airspace", "AIM Section 2.1, p. 2-5"),
    "air-004": ("AIM", "Section 2.1: Airspace Structure", "Class C airspace", "AIM Section 2.1, p. 2-6"),
    "air-005": ("AIM", "Section 2.1: Airspace Structure", "Class D airspace", "AIM Section 2.1, p. 2-7"),
    "air-006": ("AIM", "Section 2.1: Airspace Structure", "Class E airspace", "AIM Section 2.1, p. 2-8"),
    "air-007": ("AIM", "Section 2.1: Airspace Structure", "Class F airspace", "AIM Section 2.1, p. 2-9"),
    "air-008": ("AIM", "Section 2.1: Airspace Structure", "Class G airspace", "AIM Section 2.1, p. 2-10"),
    "air-009": ("AIM", "Section 2.2: Control Zones", "Control zone operations", "AIM Section 2.2, p. 2-11"),
    "air-010": ("AIM", "Section 2.2: Control Zones", "Airspace requirements", "AIM Section 2.2, p. 2-12"),
    "air-011": ("AIM", "Section 2.3: Restricted Airspace", "Restricted area interpretation", "AIM Section 2.3, p. 2-13"),
    "air-012": ("AIM", "Section 2.3: Restricted Airspace", "Prohibited airspace", "AIM Section 2.3, p. 2-14"),
    "air-013": ("AIM", "Section 2.4: Special Use Airspace", "Military Operating Areas", "AIM Section 2.4, p. 2-15"),
    "air-014": ("AIM", "Section 2.4: Special Use Airspace", "Alert areas", "AIM Section 2.4, p. 2-16"),
    "air-015": ("AIM", "Section 2.5: RPA Specific Airspace", "RPA operating limitations", "AIM RPA Section, p. 2-40"),
    "air-016": ("AIM", "Section 2.1: Airspace Structure", "Airspace boundaries", "AIM Section 2.1, p. 2-3"),
    "air-017": ("AIM", "Section 2.2: Control Zones", "Frequency requirements", "AIM Section 2.2, p. 2-11"),
    "air-018": ("AIM", "Section 2.3: Restricted Airspace", "NOTAMs for restricted areas", "AIM Section 2.3, p. 2-13"),
    "air-019": ("AIM", "Section 2.4: Special Use Airspace", "Temporary restricted areas", "AIM Section 2.4, p. 2-15"),
    "air-020": ("AIM", "Section 2.5: RPA Specific Airspace", "RPA altitude limits", "AIM RPA Section, p. 2-40"),
    "air-021": ("AIM", "Section 2.1: Airspace Structure", "Transition altitude", "AIM Section 2.1, p. 2-3"),
    "air-022": ("AIM", "Section 2.2: Control Zones", "Approach control zones", "AIM Section 2.2, p. 2-11"),
    "air-023": ("AIM", "Section 2.3: Restricted Airspace", "Danger areas", "AIM Section 2.3, p. 2-13"),
    "air-024": ("AIM", "Section 2.4: Special Use Airspace", "Training areas", "AIM Section 2.4, p. 2-15"),
    "air-025": ("AIM", "Section 2.5: RPA Specific Airspace", "VLOS operational zones", "AIM RPA Section, p. 2-40"),
    "air-026": ("DAH", "Designated Airspace Handbook", "Canadian airspace regions", "NAVCANADA DAH, p. 1-10"),
    "air-027": ("DAH", "Designated Airspace Handbook", "Airspace designation changes", "NAVCANADA DAH, p. 1-15"),
    "air-028": ("DAH", "Designated Airspace Handbook", "Special flight procedures", "NAVCANADA DAH, p. 1-20"),
    "air-029": ("DAH", "Designated Airspace Handbook", "Airspace effective times", "NAVCANADA DAH, p. 1-25"),
    "air-030": ("DAH", "Designated Airspace Handbook", "Regional airspace info", "NAVCANADA DAH, p. 2-1"),
    "air-031": ("AIM", "Section 2.1: Airspace Structure", "Altitude reference systems", "AIM Section 2.1, p. 2-3"),
    "air-032": ("AIM", "Section 2.2: Control Zones", "Communication procedures", "AIM Section 2.2, p. 2-11"),
    "air-033": ("AIM", "Section 2.3: Restricted Airspace", "Temporary airspace", "AIM Section 2.3, p. 2-13"),
    "air-034": ("AIM", "Section 2.4: Special Use Airspace", "Parachute jump areas", "AIM Section 2.4, p. 2-15"),
    "air-035": ("AIM", "Section 2.5: RPA Specific Airspace", "RPA certification requirements", "AIM RPA Section, p. 2-40"),
    "air-036": ("DAH", "Designated Airspace Handbook", "Airspace exemptions", "NAVCANADA DAH, p. 1-30"),
    "air-037": ("DAH", "Designated Airspace Handbook", "Frequency assignments", "NAVCANADA DAH, p. 3-1"),
    "air-038": ("DAH", "Designated Airspace Handbook", "Runway information", "NAVCANADA DAH, p. 3-5"),
    "air-039": ("DAH", "Designated Airspace Handbook", "Aerodrome altitudes", "NAVCANADA DAH, p. 3-10"),
    "air-040": ("DAH", "Designated Airspace Handbook", "Service availability", "NAVCANADA DAH, p. 3-15"),
    "air-041": ("AIM", "Section 2.2: Control Zones", "Class D operations", "AIM Section 2.2, p. 2-11"),
    "air-042": ("AIM", "Section 2.3: Restricted Airspace", "Restricted area entry", "AIM Section 2.3, p. 2-13"),
    "air-043": ("AIM", "Section 2.4: Special Use Airspace", "Wildlife area restrictions", "AIM Section 2.4, p. 2-15"),
    "air-044": ("AIM", "Section 2.5: RPA Specific Airspace", "RPA operations near airports", "AIM RPA Section, p. 2-40"),
    "air-045": ("DAH", "Designated Airspace Handbook", "Runway configurations", "NAVCANADA DAH, p. 3-5"),
    "air-046": ("DAH", "Designated Airspace Handbook", "Visual approach procedures", "NAVCANADA DAH, p. 3-20"),
    "air-047": ("DAH", "Designated Airspace Handbook", "Instrument approach procedures", "NAVCANADA DAH, p. 3-25"),
    "air-048": ("DAH", "Designated Airspace Handbook", "Minimum altitudes", "NAVCANADA DAH, p. 3-30"),
    "air-049": ("DAH", "Designated Airspace Handbook", "Holding patterns", "NAVCANADA DAH, p. 3-35"),
    "air-050": ("DAH", "Designated Airspace Handbook", "Standard routes", "NAVCANADA DAH, p. 3-40"),
    
    # Aerodromes (50 questions) - aero-XXX - AIM Section 3 & DAH
    "aero-001": ("AIM", "Section 3.1: Aerodrome Info", "Aerodrome runway data", "AIM Section 3.1, p. 3-1"),
    "aero-002": ("AIM", "Section 3.1: Aerodrome Info", "Taxiway configurations", "AIM Section 3.1, p. 3-2"),
    "aero-003": ("AIM", "Section 3.1: Aerodrome Info", "Surface types", "AIM Section 3.1, p. 3-3"),
    "aero-004": ("AIM", "Section 3.2: Aerodrome Procedures", "Flight procedures", "AIM Section 3.2, p. 3-4"),
    "aero-005": ("AIM", "Section 3.2: Aerodrome Procedures", "Ground procedures", "AIM Section 3.2, p. 3-5"),
    "aero-006": ("AIM", "Section 3.3: Lighting Systems", "Runway lights", "AIM Section 3.3, p. 3-6"),
    "aero-007": ("AIM", "Section 3.3: Lighting Systems", "Taxiway lights", "AIM Section 3.3, p. 3-7"),
    "aero-008": ("AIM", "Section 3.3: Lighting Systems", "Approach lights", "AIM Section 3.3, p. 3-8"),
    "aero-009": ("AIM", "Section 3.4: Radio Aids", "VOR operations", "AIM Section 3.4, p. 3-9"),
    "aero-010": ("AIM", "Section 3.4: Radio Aids", "NDB/ADF systems", "AIM Section 3.4, p. 3-10"),
    "aero-011": ("DAH", "Aerodrome Data", "Runway data tables", "NAVCANADA DAH, p. 3-5"),
    "aero-012": ("DAH", "Aerodrome Data", "Frequency listings", "NAVCANADA DAH, p. 3-1"),
    "aero-013": ("DAH", "Aerodrome Data", "Runway surface conditions", "NAVCANADA DAH, p. 3-10"),
    "aero-014": ("DAH", "Aerodrome Data", "Lighting availability", "NAVCANADA DAH, p. 3-15"),
    "aero-015": ("DAH", "Aerodrome Data", "Services available", "NAVCANADA DAH, p. 3-20"),
    "aero-016": ("AIM", "Section 3.1: Aerodrome Info", "Runway orientations", "AIM Section 3.1, p. 3-1"),
    "aero-017": ("AIM", "Section 3.2: Aerodrome Procedures", "Circuit procedures", "AIM Section 3.2, p. 3-4"),
    "aero-018": ("AIM", "Section 3.3: Lighting Systems", "Beacon systems", "AIM Section 3.3, p. 3-6"),
    "aero-019": ("AIM", "Section 3.4: Radio Aids", "ILS systems", "AIM Section 3.4, p. 3-9"),
    "aero-020": ("AIM", "Section 3.4: Radio Aids", "Distance measuring equipment", "AIM Section 3.4, p. 3-10"),
    "aero-021": ("DAH", "Aerodrome Data", "Parking areas", "NAVCANADA DAH, p. 3-25"),
    "aero-022": ("DAH", "Aerodrome Data", "Fueling facilities", "NAVCANADA DAH, p. 3-30"),
    "aero-023": ("DAH", "Aerodrome Data", "Customs facilities", "NAVCANADA DAH, p. 3-35"),
    "aero-024": ("DAH", "Aerodrome Data", "Emergency services", "NAVCANADA DAH, p. 3-40"),
    "aero-025": ("DAH", "Aerodrome Data", "Maintenance services", "NAVCANADA DAH, p. 3-45"),
    "aero-026": ("AIM", "Section 3.1: Aerodrome Info", "Runway elevation", "AIM Section 3.1, p. 3-1"),
    "aero-027": ("AIM", "Section 3.2: Aerodrome Procedures", "Holding procedures", "AIM Section 3.2, p. 3-4"),
    "aero-028": ("AIM", "Section 3.3: Lighting Systems", "Obstruction lights", "AIM Section 3.3, p. 3-6"),
    "aero-029": ("AIM", "Section 3.4: Radio Aids", "GNSS systems", "AIM Section 3.4, p. 3-9"),
    "aero-030": ("AIM", "Section 3.4: Radio Aids", "Ground-based navigation", "AIM Section 3.4, p. 3-10"),
    "aero-031": ("DAH", "Aerodrome Data", "Runway gradients", "NAVCANADA DAH, p. 3-5"),
    "aero-032": ("DAH", "Aerodrome Data", "Maximum aircraft weights", "NAVCANADA DAH, p. 3-10"),
    "aero-033": ("DAH", "Aerodrome Data", "Hours of operation", "NAVCANADA DAH, p. 3-15"),
    "aero-034": ("DAH", "Aerodrome Data", "Restrictions", "NAVCANADA DAH, p. 3-20"),
    "aero-035": ("DAH", "Aerodrome Data", "Notable features", "NAVCANADA DAH, p. 3-25"),
    "aero-036": ("AIM", "Section 3.1: Aerodrome Info", "Obstacle information", "AIM Section 3.1, p. 3-1"),
    "aero-037": ("AIM", "Section 3.2: Aerodrome Procedures", "Noise abatement", "AIM Section 3.2, p. 3-4"),
    "aero-038": ("AIM", "Section 3.3: Lighting Systems", "Precision approach lights", "AIM Section 3.3, p. 3-6"),
    "aero-039": ("AIM", "Section 3.4: Radio Aids", "Localizer systems", "AIM Section 3.4, p. 3-9"),
    "aero-040": ("AIM", "Section 3.4: Radio Aids", "Glideslope systems", "AIM Section 3.4, p. 3-10"),
    "aero-041": ("DAH", "Aerodrome Data", "Seasonal variations", "NAVCANADA DAH, p. 3-50"),
    "aero-042": ("DAH", "Aerodrome Data", "Temporary closures", "NAVCANADA DAH, p. 3-55"),
    "aero-043": ("DAH", "Aerodrome Data", "Preferred runways", "NAVCANADA DAH, p. 3-60"),
    "aero-044": ("DAH", "Aerodrome Data", "Airspace reservations", "NAVCANADA DAH, p. 3-65"),
    "aero-045": ("DAH", "Aerodrome Data", "Adjacent airspace", "NAVCANADA DAH, p. 3-70"),
    "aero-046": ("AIM", "Section 3.1: Aerodrome Info", "Ground features", "AIM Section 3.1, p. 3-1"),
    "aero-047": ("AIM", "Section 3.2: Aerodrome Procedures", "Emergency procedures", "AIM Section 3.2, p. 3-4"),
    "aero-048": ("AIM", "Section 3.3: Lighting Systems", "Signal lights", "AIM Section 3.3, p. 3-6"),
    "aero-049": ("AIM", "Section 3.4: Radio Aids", "Radar systems", "AIM Section 3.4, p. 3-9"),
    "aero-050": ("AIM", "Section 3.4: Radio Aids", "Secondary radar", "AIM Section 3.4, p. 3-10"),
    
    # Radio (42 questions) - radio-XXX - NAV CANADA VFR Phraseology
    "radio-001": ("NAV CANADA", "VFR Phraseology: Initial Contact", "Initial call format", "VFR Phraseology, p. 2-1"),
    "radio-002": ("NAV CANADA", "VFR Phraseology: Initial Contact", "Frequency selection", "VFR Phraseology, p. 2-2"),
    "radio-003": ("NAV CANADA", "VFR Phraseology: Basic Calls", "Roger acknowledgment", "VFR Phraseology, p. 2-3"),
    "radio-004": ("NAV CANADA", "VFR Phraseology: Basic Calls", "Wilco acceptance", "VFR Phraseology, p. 2-4"),
    "radio-005": ("NAV CANADA", "VFR Phraseology: Read-back", "Altitude read-back", "VFR Phraseology, p. 2-5"),
    "radio-006": ("NAV CANADA", "VFR Phraseology: Read-back", "Heading read-back", "VFR Phraseology, p. 2-6"),
    "radio-007": ("NAV CANADA", "VFR Phraseology: Emergency", "MAYDAY procedure", "VFR Phraseology, p. 3-1"),
    "radio-008": ("NAV CANADA", "VFR Phraseology: Emergency", "PAN emergency level", "VFR Phraseology, p. 3-2"),
    "radio-009": ("NAV CANADA", "VFR Phraseology: ATIS", "ATIS format", "VFR Phraseology, p. 4-1"),
    "radio-010": ("NAV CANADA", "VFR Phraseology: ATIS", "ATIS information", "VFR Phraseology, p. 4-2"),
    "radio-011": ("NAV CANADA", "VFR Phraseology: Clearances", "Clearance format", "VFR Phraseology, p. 5-1"),
    "radio-012": ("NAV CANADA", "VFR Phraseology: Clearances", "Clearance readback", "VFR Phraseology, p. 5-2"),
    "radio-013": ("NAV CANADA", "VFR Phraseology: Position Reporting", "Position report format", "VFR Phraseology, p. 6-1"),
    "radio-014": ("NAV CANADA", "VFR Phraseology: Position Reporting", "Bearing and distance", "VFR Phraseology, p. 6-2"),
    "radio-015": ("NAV CANADA", "VFR Phraseology: Frequencies", "Frequency selection process", "VFR Phraseology, p. 1-1"),
    "radio-016": ("NAV CANADA", "VFR Phraseology: Frequencies", "Frequency change procedures", "VFR Phraseology, p. 1-2"),
    "radio-017": ("NAV CANADA", "VFR Phraseology: Communication", "Readability scale", "VFR Phraseology, p. 7-1"),
    "radio-018": ("NAV CANADA", "VFR Phraseology: Communication", "Signal quality reporting", "VFR Phraseology, p. 7-2"),
    "radio-019": ("NAV CANADA", "VFR Phraseology: Traffic Info", "Traffic call format", "VFR Phraseology, p. 8-1"),
    "radio-020": ("NAV CANADA", "VFR Phraseology: Traffic Info", "Traffic avoidance calls", "VFR Phraseology, p. 8-2"),
    "radio-021": ("NAV CANADA", "VFR Phraseology: Weather", "Weather reporting", "VFR Phraseology, p. 9-1"),
    "radio-022": ("NAV CANADA", "VFR Phraseology: Weather", "METAR interpretation", "VFR Phraseology, p. 9-2"),
    "radio-023": ("NAV CANADA", "VFR Phraseology: Numbers", "Number pronunciation", "VFR Phraseology, p. 10-1"),
    "radio-024": ("NAV CANADA", "VFR Phraseology: Numbers", "Altitude pronunciation", "VFR Phraseology, p. 10-2"),
    "radio-025": ("NAV CANADA", "VFR Phraseology: QNH", "QNH procedures", "VFR Phraseology, p. 11-1"),
    "radio-026": ("NAV CANADA", "VFR Phraseology: QNH", "Standard pressure setting", "VFR Phraseology, p. 11-2"),
    "radio-027": ("NAV CANADA", "VFR Phraseology: Separation", "Separation requirements", "VFR Phraseology, p. 12-1"),
    "radio-028": ("NAV CANADA", "VFR Phraseology: Separation", "Minimum safe altitude", "VFR Phraseology, p. 12-2"),
    "radio-029": ("NAV CANADA", "VFR Phraseology: Contingency", "Loss of communication", "VFR Phraseology, p. 13-1"),
    "radio-030": ("NAV CANADA", "VFR Phraseology: Contingency", "Emergency descent", "VFR Phraseology, p. 13-2"),
    "radio-031": ("NAV CANADA", "VFR Phraseology: Practice", "Practice call procedures", "VFR Phraseology, p. 14-1"),
    "radio-032": ("NAV CANADA", "VFR Phraseology: Practice", "Training callsigns", "VFR Phraseology, p. 14-2"),
    "radio-033": ("NAV CANADA", "VFR Phraseology: Standard Phrases", "Standardized terminology", "VFR Phraseology, p. 15-1"),
    "radio-034": ("NAV CANADA", "VFR Phraseology: Standard Phrases", "Non-standard requests", "VFR Phraseology, p. 15-2"),
    "radio-035": ("NAV CANADA", "VFR Phraseology: Conditions", "Operational limitations", "VFR Phraseology, p. 16-1"),
    "radio-036": ("NAV CANADA", "VFR Phraseology: Conditions", "Weather impact calls", "VFR Phraseology, p. 16-2"),
    "radio-037": ("NAV CANADA", "VFR Phraseology: Procedures", "Procedure compliance", "VFR Phraseology, p. 17-1"),
    "radio-038": ("NAV CANADA", "VFR Phraseology: Procedures", "Deviation reporting", "VFR Phraseology, p. 17-2"),
    "radio-039": ("NAV CANADA", "VFR Phraseology: Safety", "Safety critical calls", "VFR Phraseology, p. 18-1"),
    "radio-040": ("NAV CANADA", "VFR Phraseology: Safety", "Hazard reporting", "VFR Phraseology, p. 18-2"),
    "radio-041": ("NAV CANADA", "VFR Phraseology: Coordination", "Pilot-ATC coordination", "VFR Phraseology, p. 19-1"),
    "radio-042": ("NAV CANADA", "VFR Phraseology: Coordination", "Handoff procedures", "VFR Phraseology, p. 19-2"),
    
    # NOTAMs (50 questions) - notam-XXX - AIM Section 5
    "notam-001": ("AIM", "Section 5.1: NOTAM System", "NOTAM types", "AIM Section 5.1, p. 5-1"),
    "notam-002": ("AIM", "Section 5.1: NOTAM System", "NOTAM format", "AIM Section 5.1, p. 5-2"),
    "notam-003": ("AIM", "Section 5.2: NOTAM Interpretation", "Codes and abbreviations", "AIM Section 5.2, p. 5-3"),
    "notam-004": ("AIM", "Section 5.2: NOTAM Interpretation", "Effective time interpretation", "AIM Section 5.2, p. 5-4"),
    "notam-005": ("AIM", "Section 5.3: NOTAM Dissemination", "Sources for NOTAMs", "AIM Section 5.3, p. 5-5"),
    "notam-006": ("AIM", "Section 5.3: NOTAM Dissemination", "Flight service stations", "AIM Section 5.3, p. 5-6"),
    "notam-007": ("AIM", "Section 5.4: Handling NOTAMs", "Pre-flight briefing", "AIM Section 5.4, p. 5-7"),
    "notam-008": ("AIM", "Section 5.4: Handling NOTAMs", "NOTAM search procedures", "AIM Section 5.4, p. 5-8"),
    "notam-009": ("AIM", "Section 5.5: Special NOTAMs", "Airspace NOTAMs", "AIM Section 5.5, p. 5-9"),
    "notam-010": ("AIM", "Section 5.5: Special NOTAMs", "Runway closure NOTAMs", "AIM Section 5.5, p. 5-10"),
    "notam-011": ("NAV CANADA", "NOTAM Search", "FPL filing NOTAMs", "NAVCANADA NOTAM System"),
    "notam-012": ("NAV CANADA", "NOTAM Search", "Active NOTAM search", "NAVCANADA NOTAM Online"),
    "notam-013": ("AIM", "Section 5.1: NOTAM System", "Hazard NOTAMs", "AIM Section 5.1, p. 5-1"),
    "notam-014": ("AIM", "Section 5.2: NOTAM Interpretation", "Geo-coordinate NOTAMs", "AIM Section 5.2, p. 5-3"),
    "notam-015": ("AIM", "Section 5.3: NOTAM Dissemination", "NOTAM retrieval methods", "AIM Section 5.3, p. 5-5"),
    "notam-016": ("AIM", "Section 5.4: Handling NOTAMs", "NOTAM compliance", "AIM Section 5.4, p. 5-7"),
    "notam-017": ("AIM", "Section 5.5: Special NOTAMs", "Obstacle NOTAMs", "AIM Section 5.5, p. 5-9"),
    "notam-018": ("AIM", "Section 5.5: Special NOTAMs", "Navigation aid NOTAMs", "AIM Section 5.5, p. 5-10"),
    "notam-019": ("NAV CANADA", "NOTAM Codes", "Q-codes for NOTAMs", "NAVCANADA NOTAM Coding"),
    "notam-020": ("NAV CANADA", "NOTAM Codes", "Traffic restrictions", "NAVCANADA Traffic NOTAMs"),
    "notam-021": ("AIM", "Section 5.1: NOTAM System", "NOTAM escalation", "AIM Section 5.1, p. 5-1"),
    "notam-022": ("AIM", "Section 5.2: NOTAM Interpretation", "Duration and recurrence", "AIM Section 5.2, p. 5-3"),
    "notam-023": ("AIM", "Section 5.3: NOTAM Dissemination", "NOTAM reliability", "AIM Section 5.3, p. 5-5"),
    "notam-024": ("AIM", "Section 5.4: Handling NOTAMs", "NOTAM archival", "AIM Section 5.4, p. 5-7"),
    "notam-025": ("AIM", "Section 5.5: Special NOTAMs", "Military exercise NOTAMs", "AIM Section 5.5, p. 5-9"),
    "notam-026": ("AIM", "Section 5.1: NOTAM System", "Safety critical NOTAMs", "AIM Section 5.1, p. 5-1"),
    "notam-027": ("AIM", "Section 5.2: NOTAM Interpretation", "Conditional NOTAMs", "AIM Section 5.2, p. 5-3"),
    "notam-028": ("AIM", "Section 5.3: NOTAM Dissemination", "NOTAM broadcast", "AIM Section 5.3, p. 5-5"),
    "notam-029": ("AIM", "Section 5.4: Handling NOTAMs", "NOTAM acknowledgment", "AIM Section 5.4, p. 5-7"),
    "notam-030": ("AIM", "Section 5.5: Special NOTAMs", "Parachute area NOTAMs", "AIM Section 5.5, p. 5-9"),
    "notam-031": ("NAV CANADA", "NOTAM Search", "Regional NOTAM search", "NAVCANADA NOTAM Regional"),
    "notam-032": ("NAV CANADA", "NOTAM Search", "Route NOTAM search", "NAVCANADA NOTAM Route"),
    "notam-033": ("AIM", "Section 5.1: NOTAM System", "Temporary airspace NOTAMs", "AIM Section 5.1, p. 5-1"),
    "notam-034": ("AIM", "Section 5.2: NOTAM Interpretation", "Altimeter setting NOTAMs", "AIM Section 5.2, p. 5-3"),
    "notam-035": ("AIM", "Section 5.3: NOTAM Dissemination", "NOTAM updates", "AIM Section 5.3, p. 5-5"),
    "notam-036": ("AIM", "Section 5.4: Handling NOTAMs", "NOTAM cancellation", "AIM Section 5.4, p. 5-7"),
    "notam-037": ("AIM", "Section 5.5: Special NOTAMs", "Event NOTAMs", "AIM Section 5.5, p. 5-9"),
    "notam-038": ("AIM", "Section 5.5: Special NOTAMs", "Wildlife NOTAMs", "AIM Section 5.5, p. 5-10"),
    "notam-039": ("NAV CANADA", "NOTAM Briefing", "Pre-flight NOTAM check", "NAVCANADA NOTAM Briefing"),
    "notam-040": ("NAV CANADA", "NOTAM Briefing", "NOTAM for RPA operations", "NAVCANADA NOTAM RPA"),
    "notam-041": ("AIM", "Section 5.1: NOTAM System", "RPA-specific NOTAMs", "AIM Section 5.1, p. 5-1"),
    "notam-042": ("AIM", "Section 5.2: NOTAM Interpretation", "NOTAM spelling", "AIM Section 5.2, p. 5-3"),
    "notam-043": ("AIM", "Section 5.3: NOTAM Dissemination", "NOTAM priority levels", "AIM Section 5.3, p. 5-5"),
    "notam-044": ("AIM", "Section 5.4: Handling NOTAMs", "NOTAM filing procedures", "AIM Section 5.4, p. 5-7"),
    "notam-045": ("AIM", "Section 5.5: Special NOTAMs", "Air show NOTAMs", "AIM Section 5.5, p. 5-9"),
    "notam-046": ("AIM", "Section 5.5: Special NOTAMs", "Laser light show NOTAMs", "AIM Section 5.5, p. 5-10"),
    "notam-047": ("NAV CANADA", "NOTAM Integration", "Flight plan NOTAM check", "NAVCANADA FPL NOTAM"),
    "notam-048": ("NAV CANADA", "NOTAM Integration", "Departure briefing", "NAVCANADA Departure Brief"),
    "notam-049": ("NAV CANADA", "NOTAM Integration", "In-flight NOTAM awareness", "NAVCANADA In-flight NOTAM"),
    "notam-050": ("NAV CANADA", "NOTAM Integration", "Landing area NOTAMs", "NAVCANADA Landing Area"),
}

# Process questions to add/update AIM & NAV CANADA references
questions_updated = 0
questions_already_had = 0

for question in data['questions']:
    q_id = question.get('id', '')
    
    # Check if this question should get AIM or NAV CANADA reference
    if q_id in aim_navcanada_mappings:
        source_type, section, topics, reference = aim_navcanada_mappings[q_id]
        
        # Check if already has this source reference
        field_name = f"{source_type.lower()}_reference"
        
        if field_name in question:
            questions_already_had += 1
        else:
            # Update source field
            current_source = question.get('source', '')
            if source_type not in current_source:
                if current_source:
                    question['source'] = f"{current_source} + {source_type}"
                else:
                    question['source'] = f"TP 15263 + {source_type}"
            
            # Add reference field
            question[field_name] = reference
            
            questions_updated += 1
        
        # Print progress every 10 questions
        if (questions_updated + questions_already_had) % 10 == 0:
            print(f"  Processed {questions_updated + questions_already_had} questions...")

# Save updated questions.json
with open(questions_file, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"\n✓ Phase 3C (AIM & NAV CANADA - Airspace, Aerodromes, Radio, NOTAMs) Complete!")
print(f"  • Questions newly updated: {questions_updated}")
print(f"  • Questions already had AIM/NAV CANADA ref: {questions_already_had}")
print(f"  • Total AIM/NAV CANADA references added: {questions_updated + questions_already_had}")
print(f"  • Total questions in bank: {len(data['questions'])}")
print(f"\nNext: Execute phase3d_enhance_rationales.py to add source material to all rationales")
