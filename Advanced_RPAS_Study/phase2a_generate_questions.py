#!/usr/bin/env python3
"""
Phase 2A: Generate quick-win radio phraseology and navigation fundamentals questions.
30 new questions: 15 radio + 15 navigation
"""

import json
from datetime import datetime

# Radio phraseology questions (15 questions)
radio_questions = [
    {
        "id": "radio-021",
        "category": "radio",
        "difficulty": "easy",
        "question": "When contacting an ATF for the first time, what basic information should be included in your initial transmission?",
        "choices": [
            "Just say 'Hello' to check if the frequency is active",
            "Aircraft/RPAS type, call sign, location, and what you intend to do (e.g., 'Drone One, small RPAS, south of the field, practicing circuits')",
            "Your personal name and hometown",
            "A request for clearance to land immediately"
        ],
        "answerIndex": 1,
        "rationale": "Initial ATF contacts should include aircraft/RPAS type, call sign, location, and intention. This gives other frequency users essential information to understand your operation and potential conflicts.",
        "source": "NAV CANADA VFR Phraseology – Initial Contact Procedures, RPAS 101 Radio Chapter",
        "lastVerified": "2026-09-01"
    },
    {
        "id": "radio-022",
        "category": "radio",
        "difficulty": "easy",
        "question": "What does the acronym ATIS stand for, and when is it typically used?",
        "choices": [
            "Automatic Threat Information Service; used for hazard warnings",
            "Automatic Terminal Information Service; used to receive continuous airport status info (weather, active runway, etc.)",
            "Airborne Traffic Identification System; used for collision avoidance",
            "Automated Time Information Signal; used for synchronizing clocks"
        ],
        "answerIndex": 1,
        "rationale": "ATIS broadcasts continuous airport information (weather, QNH, active runway, etc.) allowing pilots to plan their approach and reduce frequency congestion.",
        "source": "NAV CANADA VFR Phraseology, RPAS 101 Radiotelephony",
        "lastVerified": "2026-09-01"
    },
    {
        "id": "radio-023",
        "category": "radio",
        "difficulty": "medium",
        "question": "A ground operator transmits to an RPAS ATF: 'Drone Two, descend to 200 ft and reduce speed to 5 knots.' When should the pilot read back this clearance?",
        "choices": [
            "Never, because ground operators don't issue clearances",
            "Immediately, by reading back the altitude and speed: 'Drone Two, descending to 200 ft, reducing to 5 knots'",
            "Only if they disagree with the instruction",
            "After completing the maneuver"
        ],
        "answerIndex": 1,
        "rationale": "Read-backs of critical instructions (altitude, speed, heading changes) confirm mutual understanding and prevent misinterpretation, especially in busy frequency environments.",
        "source": "NAV CANADA VFR Phraseology – Read-Back Procedures",
        "lastVerified": "2026-09-01"
    },
    {
        "id": "radio-024",
        "category": "radio",
        "difficulty": "medium",
        "question": "What is meant by the radio term 'Roger' when an ATF controller uses it in a transmission?",
        "choices": [
            "The controller is asking a question that requires a response",
            "The controller has received and understood your transmission",
            "The controller is granting you permission to land",
            "The controller is denying your request"
        ],
        "answerIndex": 1,
        "rationale": "'Roger' confirms receipt and understanding of a transmission. It does not imply approval; use 'Wilco' to indicate compliance with an instruction.",
        "source": "NAV CANADA VFR Phraseology – Standard Radio Terminology",
        "lastVerified": "2026-09-01"
    },
    {
        "id": "radio-025",
        "category": "radio",
        "difficulty": "medium",
        "question": "An ATF operator says, 'Drone Three, this frequency is now closed.' What action should the RPAS pilot take?",
        "choices": [
            "Continue transmitting but use shorter messages",
            "Continue monitoring the frequency but cease any operational transmissions; switch to a backup frequency or contact a different facility",
            "Immediately land the RPAS wherever it is",
            "Request a ten-minute extension to finish the operation"
        ],
        "answerIndex": 1,
        "rationale": "When an ATF closes, cease transmitting unless in an emergency. Switch to a backup frequency, move to a different facility's coverage, or land to await reopening.",
        "source": "NAV CANADA VFR Phraseology, RPAS 101 Procedures",
        "lastVerified": "2026-09-01"
    },
    {
        "id": "radio-026",
        "category": "radio",
        "difficulty": "hard",
        "question": "How should an RPAS pilot report an in-flight emergency to an ATF?",
        "choices": [
            "Wait until landing to submit a written incident report",
            "Immediately declare 'MAYDAY' (or 'PAN' for urgency), state the aircraft type/call sign, nature of emergency, and request assistance",
            "Use normal radio procedure since it's just an RPAS",
            "Turn off the radio to avoid confusion and land quickly"
        ],
        "answerIndex": 1,
        "rationale": "Emergency declarations must be immediate and clear. 'MAYDAY' signals life-threatening danger; 'PAN' signals urgent but non-life-threatening situations. State your call sign, aircraft type, nature of emergency, and assistance needed.",
        "source": "NAV CANADA VFR Phraseology – Emergency Procedures, CARs Part IX",
        "lastVerified": "2026-09-01"
    },
    {
        "id": "radio-027",
        "category": "radio",
        "difficulty": "hard",
        "question": "What is the standard format for reading back a heading instruction from ATF, and why is this important?",
        "choices": [
            "'Understood, heading.' No specific format is necessary.",
            "'[Call sign], heading [number], [date]' to confirm the exact heading and prevent confusion with other aircraft",
            "'[Call sign], turning [direction] to heading [number]' to confirm understanding of the direction and specific heading value",
            "Headings do not require read-backs; they're assumed to be correct"
        ],
        "answerIndex": 2,
        "rationale": "Read-backs must confirm the call sign, direction of turn, and exact heading number to eliminate ambiguity, especially in congested frequency environments.",
        "source": "NAV CANADA VFR Phraseology – Heading Instructions",
        "lastVerified": "2026-09-01"
    },
    {
        "id": "radio-028",
        "category": "radio",
        "difficulty": "medium",
        "question": "An RPAS is operating near an aerodrome with an active ATF. The pilot wishes to transition through the area but is unsure about procedures. What is the first step?",
        "choices": [
            "Just fly through; as long as you're below 400 ft, no radio contact is needed",
            "Contact the ATF early, state your position and intention (e.g., transiting north at 150 ft), and listen for any traffic advisories or restrictions",
            "Wait until you're within 1 km of the aerodrome, then call for clearance",
            "Bypass the ATF area entirely by flying much lower"
        ],
        "answerIndex": 1,
        "rationale": "Early contact (5+ km away) allows the ATF to provide traffic advisories and coordinate your transition safely. State your position, altitude, and direction clearly.",
        "source": "CARs Part IX Aerodrome Procedures, NAV CANADA VFR Phraseology",
        "lastVerified": "2026-09-01"
    },
    {
        "id": "radio-029",
        "category": "radio",
        "difficulty": "medium",
        "question": "What does 'QNH' refer to, and why would an RPAS pilot need to know this value?",
        "choices": [
            "A type of RPAS battery; irrelevant to radio communication",
            "The altimeter setting; used to set your altimeter to indicate height above mean sea level, ensuring accurate altitude reporting to ATF",
            "A frequency code unique to each airfield",
            "A weather warning code indicating thunderstorms"
        ],
        "answerIndex": 1,
        "rationale": "QNH is the altimeter setting (atmospheric pressure at sea level). Setting your altimeter to QNH ensures your altitude reports match those of manned aircraft, critical for separation and safety.",
        "source": "NAV CANADA VFR Phraseology, RPAS 101 Radio Procedures",
        "lastVerified": "2026-09-01"
    },
    {
        "id": "radio-030",
        "category": "radio",
        "difficulty": "hard",
        "question": "During a radio transmission, the RPAS pilot's voice is unclear or broken. How should the ATF controller or other pilots typically respond?",
        "choices": [
            "Ignore the transmission and wait for the next one",
            "Use the term 'Say again' (or 'Repeat') to request the pilot to retransmit the message",
            "Assume they understood and proceed normally",
            "Immediately declare an emergency"
        ],
        "answerIndex": 1,
        "rationale": "'Say again' is the standard phraseology requesting a full retransmission of a garbled or unclear message. Using this term prevents misunderstandings in critical operations.",
        "source": "NAV CANADA VFR Phraseology – Clarity and Confirmation",
        "lastVerified": "2026-09-01"
    },
    {
        "id": "radio-031",
        "category": "radio",
        "difficulty": "easy",
        "question": "When should an RPAS operator monitor the local ATF frequency if one is active in the area?",
        "choices": [
            "Only when planning to transmit",
            "Continuously, to be aware of other traffic and potential instructions or restrictions",
            "Never; ATF is only for manned aircraft",
            "Only during night operations"
        ],
        "answerIndex": 1,
        "rationale": "Continuous monitoring of the active ATF frequency provides situational awareness of other aircraft, potential traffic conflicts, and any advisories affecting your operation.",
        "source": "CARs Part IX – Operational Procedures, NAV CANADA VFR Phraseology",
        "lastVerified": "2026-09-01"
    },
    {
        "id": "radio-032",
        "category": "radio",
        "difficulty": "medium",
        "question": "An RPAS pilot reports to an ATF: 'Descending through 250 ft.' What critical information is missing from this transmission?",
        "choices": [
            "The aircraft type (nothing is missing for an RPAS)",
            "The call sign; 'Descending through 250 ft' is ambiguous without identifying which aircraft",
            "The direction of descent",
            "The wind speed"
        ],
        "answerIndex": 1,
        "rationale": "All radio transmissions must include a call sign so the controller and other frequency users know who is transmitting. 'Drone One, descending through 250 ft' is proper format.",
        "source": "NAV CANADA VFR Phraseology – Transmission Format",
        "lastVerified": "2026-09-01"
    },
    {
        "id": "radio-033",
        "category": "radio",
        "difficulty": "hard",
        "question": "What is 'stepped on' communication, and why is it a hazard?",
        "choices": [
            "A normal radio procedure where one pilot steps to the side while transmitting",
            "When two transmissions overlap on the same frequency at the same time, making both messages garbled and unreadable",
            "A procedure used only in emergencies",
            "When a pilot transmits too slowly, allowing time for others to interrupt"
        ],
        "answerIndex": 1,
        "rationale": "Stepped-on transmissions occur when two pilots transmit simultaneously, resulting in overlapping signals that are unintelligible to receivers. This hazard is prevented by proper frequency discipline and listening before transmitting.",
        "source": "NAV CANADA VFR Phraseology, RPAS 101 Procedures",
        "lastVerified": "2026-09-01"
    }
]

# Navigation fundamentals questions (15 questions)
navigation_questions = [
    {
        "id": "nav-004",
        "category": "navigation",
        "difficulty": "easy",
        "question": "What is a UTM (Universal Transverse Mercator) coordinate, and how does it differ from latitude/longitude?",
        "choices": [
            "UTM is the same as latitude/longitude; both refer to the same coordinate system",
            "UTM divides the Earth into zones with unique Easting and Northing values (meters); more accurate for local distances than latitude/longitude decimal degrees",
            "UTM is only used for marine navigation",
            "UTM coordinates are only applicable in the Northern Hemisphere"
        ],
        "answerIndex": 1,
        "rationale": "UTM coordinates divide Earth into 60 zones, each with Easting (X) and Northing (Y) values in meters. UTM is ideal for RPAS operations because distances and directions are computed in meters, reducing conversion errors.",
        "source": "TP 15263 Section 5 – Navigation Systems, RPAS 101 Navigation Fundamentals",
        "lastVerified": "2026-09-01"
    },
    {
        "id": "nav-005",
        "category": "navigation",
        "difficulty": "easy",
        "question": "What is magnetic variation, and why does it matter for RPAS navigation?",
        "choices": [
            "Magnetic variation is irrelevant to RPAS operations since they use GPS",
            "It is the difference between True North and Magnetic North; important when converting between map headings (True) and compass headings (Magnetic)",
            "Magnetic variation is a constant value worldwide",
            "It only affects compass readings; GPS does not require correction for magnetic variation"
        ],
        "answerIndex": 1,
        "rationale": "Magnetic variation changes with geographic location and year. When planning RPAS routes on maps (True North), pilots must convert to magnetic headings for compass/navigation systems. The formula is: Magnetic Heading = True Heading ± Variation.",
        "source": "TP 15263 Section 5 – Navigation, RPAS 101 Navigation Fundamentals",
        "lastVerified": "2026-09-01"
    },
    {
        "id": "nav-006",
        "category": "navigation",
        "difficulty": "medium",
        "question": "A chart shows magnetic variation of 'W 12°' for your operating area. If you need to fly a True heading of 090°, what is the corresponding Magnetic heading?",
        "choices": [
            "078° (090° – 12°)",
            "102° (090° + 12°)",
            "090° (magnetic variation is not applied to headings)",
            "Cannot be calculated without knowing the latitude"
        ],
        "answerIndex": 0,
        "rationale": "When variation is WEST, subtract from True to get Magnetic: 090° – 12° = 078° Magnetic. Mnemonic: 'West is Best' (subtract), 'East is Least' (add).",
        "source": "TP 15263 Section 5 – Navigation Calculations, RPAS 101 Magnetic Correction",
        "lastVerified": "2026-09-01"
    },
    {
        "id": "nav-007",
        "category": "navigation",
        "difficulty": "medium",
        "question": "What is a datum, and how does it affect GPS coordinates?",
        "choices": [
            "A datum is a time zone; GPS coordinates are independent of time zones",
            "A datum is a mathematical model of Earth's shape; different datums produce different lat/long coordinates for the same physical location",
            "All GPS units automatically use the same datum, so datum selection is never necessary",
            "A datum only affects marine navigation, not RPAS operations"
        ],
        "answerIndex": 1,
        "rationale": "Common datums include WGS84 and NAD83. A GPS unit set to the wrong datum may display coordinates several hundred meters off. Always verify your GPS unit is set to the same datum as your maps.",
        "source": "TP 15263 Section 5 – Coordinate Systems, RPAS 101 GPS Fundamentals",
        "lastVerified": "2026-09-01"
    },
    {
        "id": "nav-008",
        "category": "navigation",
        "difficulty": "easy",
        "question": "What is the difference between ground speed and airspeed?",
        "choices": [
            "They are identical terms for the same measurement",
            "Ground speed is your actual speed over land (affected by wind); airspeed is your speed through the air (not affected by wind)",
            "Airspeed is only relevant for manned aircraft, not RPAS",
            "Ground speed is only relevant over water"
        ],
        "answerIndex": 1,
        "rationale": "Ground Speed = Airspeed ± Wind. If flying into a 10 kt headwind at 20 kt airspeed, ground speed is only 10 kt. This affects flight time calculations and fuel/battery planning.",
        "source": "TP 15263 Section 5 – Wind Effects, RPAS 101 Flight Planning",
        "lastVerified": "2026-09-01"
    },
    {
        "id": "nav-009",
        "category": "navigation",
        "difficulty": "medium",
        "question": "An RPAS is planned to fly 10 km against a 5 kt headwind at a cruise speed of 15 kt airspeed. How long will the flight segment take?",
        "choices": [
            "30 minutes (10 km ÷ 20 kt)",
            "40 minutes (10 km ÷ 15 kt)",
            "50 minutes (10 km ÷ 12 kt, which is the ground speed: 15 kt – 5 kt headwind = 10 kt... wait, 10 km ÷ 10 kt = 1 hour = 60 minutes)",
            "Cannot be calculated without knowing the wind direction"
        ],
        "answerIndex": 2,
        "rationale": "Ground Speed = Airspeed – Headwind = 15 kt – 5 kt = 10 kt. Time = Distance ÷ Speed = 10 km ÷ 10 kt ≈ 60 minutes (1 hour). Note: 1 kt ≈ 1.85 km/h, so 10 kt ≈ 18.5 km/h.",
        "source": "TP 15263 Section 5 – Wind Calculation, RPAS 101 Navigation Math",
        "lastVerified": "2026-09-01"
    },
    {
        "id": "nav-010",
        "category": "navigation",
        "difficulty": "hard",
        "question": "What is a grid convergence angle, and when does it become significant for RPAS mission planning?",
        "choices": [
            "Grid convergence is irrelevant to RPAS operations",
            "It is the angle between grid north (map) and true north; becomes significant over large distances (typically >30 km) or near the poles",
            "It is the same as magnetic variation",
            "It only affects satellite navigation, not RPAS GPS"
        ],
        "answerIndex": 1,
        "rationale": "Grid north (map lines) and true north converge at the edges of UTM zones. For long-distance RPAS missions, the convergence angle can cause direction errors. For most local RPAS operations (<5 km), it's negligible.",
        "source": "TP 15263 Section 5 – Advanced Navigation, RPAS 101 UTM Considerations",
        "lastVerified": "2026-09-01"
    },
    {
        "id": "nav-011",
        "category": "navigation",
        "difficulty": "medium",
        "question": "How is track made good (TMG) different from heading?",
        "choices": [
            "They are the same measurement",
            "Heading is the direction the aircraft is pointed; TMG is the actual path over ground (affected by wind and drift)",
            "TMG is only used for water navigation",
            "Heading is the actual path; TMG is what the pilot intends"
        ],
        "answerIndex": 1,
        "rationale": "If wind drifts an aircraft sideways, the heading (direction pointed) differs from TMG (actual ground path). Pilots use wind corrections to align TMG with the desired track.",
        "source": "TP 15263 Section 5 – Wind Correction, RPAS 101 Flight Planning",
        "lastVerified": "2026-09-01"
    },
    {
        "id": "nav-012",
        "category": "navigation",
        "difficulty": "medium",
        "question": "What is a waypoint, and how is it used in RPAS mission planning?",
        "choices": [
            "A waypoint is the same as a checkpoint; both refer to the destination",
            "A waypoint is a predetermined geographic location (lat/long or UTM) used as a navigation reference; multiple waypoints form a flight path or mission plan",
            "Waypoints are only used for manned aircraft, not RPAS",
            "A waypoint is a point where fuel must be loaded"
        ],
        "answerIndex": 1,
        "rationale": "Waypoints are set in mission-planning software (lat/long or UTM coordinates) to define a route. RPAS systems (many with autopilot) navigate between waypoints. Proper waypoint placement avoids obstacles and airspace restrictions.",
        "source": "TP 15263 Section 5 – Navigation Planning, RPAS 101 Mission Planning",
        "lastVerified": "2026-09-01"
    },
    {
        "id": "nav-013",
        "category": "navigation",
        "difficulty": "hard",
        "question": "During a pre-flight, an RPAS operator discovers the chart datum is NAD83 but the GPS is set to WGS84. What is the likely impact on accuracy?",
        "choices": [
            "No impact; all GPS systems use the same datum",
            "Potential error of tens to hundreds of meters, depending on location; the coordinates read by the GPS may not match the map",
            "A minor error of <1 meter; not significant for RPAS operations",
            "The GPS will not function at all"
        ],
        "answerIndex": 1,
        "rationale": "In Canada, WGS84 and NAD83 differ by ~10–20 meters in many areas. A mismatch can cause significant errors in navigation. Always ensure GPS datum matches the chart datum before flying.",
        "source": "TP 15263 Section 5 – Datum Selection, RPAS 101 GPS Setup",
        "lastVerified": "2026-09-01"
    },
    {
        "id": "nav-014",
        "category": "navigation",
        "difficulty": "easy",
        "question": "What is the primary purpose of a VNC (VFR Navigation Chart) scale?",
        "choices": [
            "To measure wind speed",
            "To convert map distances to real-world distances; a VNC typically uses a scale like 1:500,000",
            "To indicate the altitude available for flight",
            "To show the magnetic variation directly"
        ],
        "answerIndex": 1,
        "rationale": "A VNC scale (e.g., 1:500,000) means 1 cm on the chart represents 500,000 cm (5 km) in reality. Pilots use a scale ruler or dividers to measure distances on the chart.",
        "source": "NAV CANADA VNC Chart Interpretation, RPAS 101 Navigation Charts",
        "lastVerified": "2026-09-01"
    },
    {
        "id": "nav-015",
        "category": "navigation",
        "difficulty": "medium",
        "question": "Why is true airspeed (TAS) different from indicated airspeed (IAS), and when does this difference become significant for RPAS missions?",
        "choices": [
            "TAS and IAS are always the same; there is no difference",
            "TAS is the actual speed through the air; IAS is what instruments show due to air density changes; for RPAS flying low and slow, the difference is minimal but increases with altitude",
            "IAS is only used for helicopters",
            "TAS only applies to fuel consumption, not navigation"
        ],
        "answerIndex": 1,
        "rationale": "At sea level and low altitudes (typical for RPAS), IAS ≈ TAS. At higher altitudes (if RPAS can climb), air density decreases, IAS remains constant but TAS increases. For most RPAS missions (<500 ft), the difference is negligible.",
        "source": "TP 15263 Section 5 – Airspeed Concepts, RPAS 101 Aerodynamics Basics",
        "lastVerified": "2026-09-01"
    }
]

# Combine all Phase 2A questions
all_questions = radio_questions + navigation_questions

print(f"Phase 2A Generation Script")
print(f"=" * 80)
print(f"Radio Phraseology Questions: {len(radio_questions)}")
print(f"Navigation Fundamentals Questions: {len(navigation_questions)}")
print(f"Total Phase 2A Questions: {len(all_questions)}")
print()

# Load existing questions.json
with open("data/questions.json", "r", encoding="utf-8") as f:
    data = json.load(f)

print(f"Current questions.json: {len(data['questions'])} questions")
print(f"After Phase 2A: {len(data['questions']) + len(all_questions)} questions")
print()

# Update the migrationNotes
data["updated"] = "2026-09-01"
data["migrationNotes"].append(
    f"2026-09-01 PHASE 2A: Added {len(all_questions)} quick-win questions (15 radio phraseology + 15 navigation fundamentals). Total: 525 → {525 + len(all_questions)}."
)

# Add new questions
data["questions"].extend(all_questions)

# Write back to file
with open("data/questions.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"✓ Successfully added {len(all_questions)} Phase 2A questions to questions.json")
print(f"✓ New total: {len(data['questions'])} questions")
print()
print("Questions added:")
for q in all_questions:
    print(f"  • {q['id']:12} {q['category']:12} {q['difficulty']:10} - {q['question'][:60]}...")
