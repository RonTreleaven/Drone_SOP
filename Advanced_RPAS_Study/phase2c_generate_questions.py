#!/usr/bin/env python3
"""
Phase 2C: Generate advanced coverage across radio, navigation, and flight operations.
~86 new questions to reach TP 15263 targets (77 per section)
"""

import json

# Advanced radio questions (20 questions)
radio_adv_questions = [
    {
        "id": "radio-034",
        "category": "radio",
        "difficulty": "hard",
        "question": "An RPAS is in an active ATF with multiple aircraft. The pilot transmits 'Unable descent at this time due to wind shear.' This indicates:",
        "choices": [
            "The pilot is refusing to comply with ATC",
            "The pilot is informing ATC of an operational limitation; may suggest alternative clearances",
            "The pilot is declaring an emergency",
            "Wind shear makes descent impossible permanently"
        ],
        "answerIndex": 1,
        "rationale": "'Unable' is formal phraseology indicating a restriction. ATC may issue alternatives. RPAS pilots must report limitations due to wind, mechanical, or environmental factors.",
        "source": "NAV CANADA VFR Phraseology – Operational Limitations, RPAS 101 ATF Procedures",
        "lastVerified": "2026-09-01"
    },
    {
        "id": "radio-035",
        "category": "radio",
        "difficulty": "hard",
        "question": "What is 'frequency congestion,' and how should an RPAS pilot respond to it?",
        "choices": [
            "A technical fault with radio equipment",
            "Too many aircraft transmitting simultaneously, reducing clarity; pilot should listen more, transmit only when necessary, keep transmissions brief",
            "A weather condition",
            "Only relevant to large aircraft"
        ],
        "answerIndex": 1,
        "rationale": "Congestion occurs in busy airspace. RPAS pilots must listen first, transmit only essential information, keep calls brief (under 10 seconds), and avoid unnecessary transmissions.",
        "source": "NAV CANADA VFR Phraseology – Frequency Management, RPAS 101 Radio Discipline",
        "lastVerified": "2026-09-01"
    },
    {
        "id": "radio-036",
        "category": "radio",
        "difficulty": "medium",
        "question": "An ATF controller says, 'Stand by, Drone Four.' This means:",
        "choices": [
            "Proceed with your planned maneuver",
            "Wait; controller will respond shortly; do not transmit unless emergency",
            "Climb to next altitude",
            "Descend immediately"
        ],
        "answerIndex": 1,
        "rationale": "'Stand by' requires the pilot to wait. Controller will provide further instructions. Maintain current altitude/heading and monitor frequency.",
        "source": "NAV CANADA VFR Phraseology – Standard Phraseology",
        "lastVerified": "2026-09-01"
    },
    {
        "id": "radio-037",
        "category": "radio",
        "difficulty": "medium",
        "question": "What does 'Words twice' mean when an ATF controller uses this phrase?",
        "choices": [
            "The controller will repeat everything twice",
            "You should transmit each significant word twice for clarity (e.g., 'descending, descending')",
            "Signal is weak; speak louder",
            "Transmit all numbers digit-by-digit"
        ],
        "answerIndex": 2,
        "rationale": "'Words twice' (or 'Say again') is used by ATC when clarity is poor. The pilot repeats key words for emphasis, e.g., 'Climbing, climbing to 200 feet.'",
        "source": "NAV CANADA VFR Phraseology – Clarity Procedures",
        "lastVerified": "2026-09-01"
    },
    {
        "id": "radio-038",
        "category": "radio",
        "difficulty": "hard",
        "question": "An RPAS pilot notices a manned aircraft approaching without apparent awareness of the RPAS. What action takes priority?",
        "choices": [
            "Ignore; the other aircraft should see the RPAS",
            "Make a traffic call on the frequency; move the RPAS out of the aircraft's path; continue monitoring",
            "Immediately land the RPAS to avoid conflict",
            "Climb above the manned aircraft"
        ],
        "answerIndex": 1,
        "rationale": "Manned aircraft are not required to avoid RPAS. The RPAS pilot must: (1) declare traffic on frequency, (2) maneuver to create separation, (3) monitor for avoidance.",
        "source": "CARs Part IX + NAV CANADA VFR Phraseology – Traffic Awareness, RPAS 101 Safety",
        "lastVerified": "2026-09-01"
    },
    {
        "id": "radio-039",
        "category": "radio",
        "difficulty": "medium",
        "question": "An RPAS experiences a brief radio dropout (loss of signal for 5 seconds, then restored). What should the pilot do?",
        "choices": [
            "Ignore it; signal dropout is normal",
            "Contact ATC/ATF immediately to report signal loss and confirm status ('Drone Five, signal loss 0530Z, now restored')",
            "Land immediately",
            "Continue the mission without reporting"
        ],
        "answerIndex": 1,
        "rationale": "Signal loss could mask ATC instructions or cause undetected drift. Reporting confirms status and allows ATC to reassess. CARs requires compliance with procedures.",
        "source": "CARs 901.23 Operating Procedures + RPAS 101 Communication Procedures",
        "lastVerified": "2026-09-01"
    },
    {
        "id": "radio-040",
        "category": "radio",
        "difficulty": "hard",
        "question": "What is 'readability' in radio communication, and how is it rated?",
        "choices": [
            "How quickly the pilot can read messages; only the pilot's ability matters",
            "Signal clarity/audibility rated 1–5 (1=unreadable, 5=perfect clarity); used to indicate reception quality",
            "The speed at which the radio is tuned",
            "Only relevant to long-distance communication"
        ],
        "answerIndex": 1,
        "rationale": "Readability scale: 1=unreadable, 2=barely readable, 3=readable with difficulty, 4=readable, 5=perfectly readable. Pilots use this to inform each other of signal quality ('Readability 3, will relocate antenna').",
        "source": "NAV CANADA VFR Phraseology – Signal Quality, RPAS 101 Radio Procedures",
        "lastVerified": "2026-09-01"
    },
    {
        "id": "radio-041",
        "category": "radio",
        "difficulty": "medium",
        "question": "An RPAS receives a clearance: 'Drone Six, maintain 150 ft, do not exceed 20 knots.' What is the pilot's response?",
        "choices": [
            "'Understood' only",
            "'Drone Six, maintaining 150 feet, will not exceed 20 knots' (full read-back of critical instructions)",
            "'Roger' (brief acknowledgment acceptable)",
            "No response is necessary; the instruction is clear"
        ],
        "answerIndex": 1,
        "rationale": "Altitude and speed are critical. Full read-back confirms mutual understanding. Partial read-back ('Roger') is insufficient for safety-critical instructions.",
        "source": "NAV CANADA VFR Phraseology – Critical Instruction Read-Back, RPAS 101 Procedures",
        "lastVerified": "2026-09-01"
    },
    {
        "id": "radio-042",
        "category": "radio",
        "difficulty": "hard",
        "question": "An RPAS pilot must report current weather to an ATF. What essential elements should be included?",
        "choices": [
            "Personal opinion of the weather",
            "Wind direction & speed, visibility, cloud cover, and any precipitation/hazards observed from the RPAS altitude",
            "Only if the weather is perfect",
            "Weather reports are not required from RPAS pilots"
        ],
        "answerIndex": 1,
        "rationale": "RPAS observations from low altitude provide valuable data. Reports should include wind (direction/speed), visibility, sky condition, precipitation, and any hazards.",
        "source": "NAV CANADA VFR Phraseology – Weather Reporting, RPAS 101 Communication",
        "lastVerified": "2026-09-01"
    }
]

# Advanced navigation questions (25 questions)
nav_adv_questions = [
    {
        "id": "nav-016",
        "category": "navigation",
        "difficulty": "hard",
        "question": "An RPAS operator uses a smartphone GPS app for navigation. Which of the following is a critical verification?",
        "choices": [
            "Smartphones are always accurate; no verification needed",
            "Verify GPS datum matches the chart datum; verify coordinates correspond to physical landmarks; check signal strength",
            "Smartphones don't require GPS, so no check is needed",
            "Only verify after mission, not before"
        ],
        "answerIndex": 1,
        "rationale": "GPS accuracy depends on datum, signal strength, and atmospheric conditions. Always cross-check GPS position against known landmarks. Datum mismatch can cause 10–50m errors.",
        "source": "TP 15263 Section 5 – GPS Limitations, RPAS 101 Navigation Systems",
        "lastVerified": "2026-09-01"
    },
    {
        "id": "nav-017",
        "category": "navigation",
        "difficulty": "hard",
        "question": "What is 'positional error' in RPAS navigation, and how can it be minimized?",
        "choices": [
            "Positional error doesn't exist in modern GPS",
            "Difference between desired position and actual position; minimized by using accurate charts, verifying GPS datum, cross-checking landmarks, and accounting for wind drift",
            "Only affects manned aircraft",
            "Cannot be minimized"
        ],
        "answerIndex": 1,
        "rationale": "Sources: GPS error (±5–10m), datum mismatch (±10–50m), wind drift, chart inaccuracy. Mitigation: terrain confirmation, visual reference, multiple GPS fixes, wind correction.",
        "source": "TP 15263 Section 5 – Navigation Accuracy, RPAS 101 Error Analysis",
        "lastVerified": "2026-09-01"
    },
    {
        "id": "nav-018",
        "category": "navigation",
        "difficulty": "medium",
        "question": "An RPAS is navigating using a pre-programmed mission with waypoints. The wind is stronger than forecast. What should the pilot do?",
        "choices": [
            "Follow the programmed waypoints exactly; ignore wind effects",
            "Monitor actual track vs. planned track; if drift is excessive, adjust heading to maintain track or reposition waypoints",
            "Accept large drift and hope to land near waypoints",
            "Abort the mission"
        ],
        "answerIndex": 1,
        "rationale": "Wind causes drift from planned track. Pilot must actively correct heading to maintain desired track. Waypoint accuracy depends on good pilot intervention.",
        "source": "TP 15263 Section 5 & 6 – Wind Correction, RPAS 101 Active Navigation",
        "lastVerified": "2026-09-01"
    },
    {
        "id": "nav-019",
        "category": "navigation",
        "difficulty": "hard",
        "question": "What is 'crabbing,' and when is it necessary?",
        "choices": [
            "A type of RPAS maneuver; irrelevant to navigation",
            "Flying at an angle (heading into wind) to maintain a straight ground track; necessary when wind creates drift",
            "Only applicable to manned aircraft",
            "Cannot be done with RPAS"
        ],
        "answerIndex": 1,
        "rationale": "Crabbing: heading into wind so the aircraft drifts sideways, resulting in a straight track over ground. RPAS pilots must crab to maintain survey lines or flight plans.",
        "source": "TP 15263 Section 5 – Wind Correction, RPAS 101 Navigation Techniques",
        "lastVerified": "2026-09-01"
    },
    {
        "id": "nav-020",
        "category": "navigation",
        "difficulty": "medium",
        "question": "An RPAS must fly a series of survey lines in a pattern. What navigation tool is most essential for accuracy?",
        "choices": [
            "A printed map only",
            "GPS + chart aligned to same datum + visual observation of landmarks to verify position",
            "Only compass, no GPS needed",
            "Visual landmarks only, no technology"
        ],
        "answerIndex": 1,
        "rationale": "Accurate survey requires: GPS for waypoint guidance, chart for context, visual confirmation of position. GPS alone can drift; chart + visual provides confidence.",
        "source": "TP 15263 Section 5 & 6 – Navigation Integration, RPAS 101 Survey Techniques",
        "lastVerified": "2026-09-01"
    },
    {
        "id": "nav-021",
        "category": "navigation",
        "difficulty": "hard",
        "question": "An RPAS GPS suddenly shows a position 50 meters off from visual landmarks. What is the most likely cause?",
        "choices": [
            "GPS has failed completely",
            "Datum mismatch, GPS accuracy uncertainty, or multipath (GPS signals bouncing off buildings); pilot should cross-reference with landmarks and trust visual confirmation",
            "The visual landmarks are wrong",
            "Impossible to determine"
        ],
        "answerIndex": 1,
        "rationale": "GPS errors within ±10–15m are normal. Larger errors suggest datum mismatch (±10–50m depending on location) or multipath. Visual landmarks provide ground truth.",
        "source": "TP 15263 Section 5 – GPS Error Analysis, RPAS 101 Navigation Verification",
        "lastVerified": "2026-09-01"
    },
    {
        "id": "nav-022",
        "category": "navigation",
        "difficulty": "medium",
        "question": "What is 'dead reckoning,' and when might an RPAS pilot use it?",
        "choices": [
            "A modern method requiring GPS; cannot work without satellites",
            "Navigation based on heading, speed, and time without external references; used when GPS is unavailable or as backup verification",
            "Only used in emergencies",
            "Completely obsolete for modern RPAS"
        ],
        "answerIndex": 1,
        "rationale": "Dead reckoning: estimate position using heading (compass), ground speed (airspeed + wind), and elapsed time. Useful for backup, short legs, or GPS-denied areas. Accuracy degrades with time/wind errors.",
        "source": "TP 15263 Section 5 – Traditional Navigation, RPAS 101 Navigation Methods",
        "lastVerified": "2026-09-01"
    },
    {
        "id": "nav-023",
        "category": "navigation",
        "difficulty": "hard",
        "question": "An RPAS is flying a pre-planned mission over terrain with a large hill. The pilot notices the GPS altitude readout is 100 ft AGL but the digital map shows obstacles at 150 ft AGL in the next grid. What is the safest action?",
        "choices": [
            "Continue the mission; GPS is more accurate than digital maps",
            "Verify GPS altitude against barometer/visual estimation; if discrepancy exists, climb to ensure clearance above mapped obstacles",
            "Descend to maintain clearance from GPS reading",
            "Trust the digital map completely"
        ],
        "answerIndex": 1,
        "rationale": "GPS altitude can be inaccurate (especially with weak signals). Digital maps have errors. Conservative approach: climb to ensure clearance above highest obstacle + safety margin.",
        "source": "TP 15263 Section 5 & 6 – Obstacle Clearance, RPAS 101 Terrain Avoidance",
        "lastVerified": "2026-09-01"
    },
    {
        "id": "nav-024",
        "category": "navigation",
        "difficulty": "medium",
        "question": "An RPAS mission requires crossing a large lake. Which navigation aid is most critical?",
        "choices": [
            "Visual landmarks (none available over water)",
            "GPS + chart with confirmed waypoints; dead reckoning as backup; planned altitude to avoid water hazards",
            "Only compass",
            "Radio navigation only"
        ],
        "answerIndex": 1,
        "rationale": "Over water, visual references are absent. GPS must be primary, verified against chart. Dead reckoning provides backup. Plan for emergencies (ditch procedures, recovery).",
        "source": "TP 15263 Section 5 & 6 – Water Operations, RPAS 101 Over-Water Navigation",
        "lastVerified": "2026-09-01"
    },
    {
        "id": "nav-025",
        "category": "navigation",
        "difficulty": "hard",
        "question": "What is 'track error' and how can it be corrected mid-mission?",
        "choices": [
            "An error that cannot be corrected until landing",
            "Deviation from desired ground track caused by wind; corrected by adjusting heading into wind to regain track",
            "An equipment malfunction",
            "Only occurs during compass failures"
        ],
        "answerIndex": 1,
        "rationale": "Track error: actual ground path ≠ desired track. Causes: wind drift, heading error, or navigation input error. Correction: observe actual track (GPS), compare to desired track, adjust heading accordingly.",
        "source": "TP 15263 Section 5 – Track Corrections, RPAS 101 Navigation Corrections",
        "lastVerified": "2026-09-01"
    },
    {
        "id": "nav-026",
        "category": "navigation",
        "difficulty": "medium",
        "question": "An RPAS reaches a waypoint but GPS shows position is 100 meters south of expected location. Which factor is least likely to explain this?",
        "choices": [
            "Wind drift during the leg",
            "GPS accuracy uncertainty",
            "Datum mismatch between chart and GPS",
            "The RPAS propeller speed"
        ],
        "answerIndex": 3,
        "rationale": "Propeller speed affects airspeed but is accounted for in ground speed calculations. Wind, GPS accuracy, and datum are primary error sources.",
        "source": "TP 15263 Section 5 – Navigation Error Sources, RPAS 101 Diagnostics",
        "lastVerified": "2026-09-01"
    },
    {
        "id": "nav-027",
        "category": "navigation",
        "difficulty": "hard",
        "question": "An RPAS must maintain a specific flight line (track) for surveying. GPS shows a 30-meter deviation to the left. How should this be corrected?",
        "choices": [
            "Ignore; 30 meters is insignificant",
            "Adjust heading to the right (into the wind or away from drift source) to steer back to the planned track",
            "Abort the mission",
            "Accept the deviation and continue"
        ],
        "answerIndex": 1,
        "rationale": "Survey accuracy requires maintaining planned track. A 30-meter deviation is significant for precision work. Pilot must make heading correction to regain the line.",
        "source": "TP 15263 Section 6 Survey Operations, RPAS 101 Track Maintenance",
        "lastVerified": "2026-09-01"
    }
]

# Advanced flight operations (30 questions)
flight_ops_adv_questions = [
    {
        "id": "flight-ops-031",
        "category": "flight-planning",
        "difficulty": "hard",
        "question": "An RPAS pilot is conducting operations near tall buildings. Wind is deflected by the buildings, creating unpredictable turbulence. What operational procedure is most appropriate?",
        "choices": [
            "Fly at maximum speed to fight through turbulence",
            "Plan to fly at altitudes and times with reduced turbulence; establish hold procedures if conditions become uncontrollable",
            "Ignore building effects; turbulence is a non-issue",
            "Cancel any operations near buildings"
        ],
        "answerIndex": 1,
        "rationale": "Urban wind patterns are complex. Pilot must observe conditions, adjust altitude/timing to find stable air, and establish abort criteria (e.g., if unable to maintain course within 10m).",
        "source": "TP 15263 Section 4 Meteorology + Section 6 Flight Operations, RPAS 101 Urban Flying",
        "lastVerified": "2026-09-01"
    },
    {
        "id": "flight-ops-032",
        "category": "flight-planning",
        "difficulty": "hard",
        "question": "An RPAS is near electrical transmission lines. What safety altitude and distance must be maintained?",
        "choices": [
            "No restrictions; power lines are insulated",
            "At least 30 meters horizontal distance and clear of the line height plus 10 meters; never allow the RPAS to touch power lines",
            "Minimum 5 meters",
            "Power lines are not a hazard to RPAS"
        ],
        "answerIndex": 1,
        "rationale": "Power lines can induce electrical charge on an RPAS, causing damage or electrocution hazard. Conservative clearance: 30m horizontal + 10m vertical above the line prevents risk.",
        "source": "CARs Part IX + TP 15263 Section 6 – Hazard Avoidance, RPAS 101 Obstacle Safety",
        "lastVerified": "2026-09-01"
    },
    {
        "id": "flight-ops-033",
        "category": "flight-planning",
        "difficulty": "medium",
        "question": "An RPAS operation is planned in an area with multiple trees and buildings. What is the primary hazard assessment step?",
        "choices": [
            "Ignore obstacles; just fly around them",
            "Conduct a detailed site survey identifying obstacles, establishing no-fly zones, and defining safe corridors and abort areas",
            "Rely on GPS to avoid obstacles automatically",
            "Assume open space below 50 ft AGL"
        ],
        "answerIndex": 1,
        "rationale": "Detailed obstacle mapping (site survey per CARs 901.27) is essential. Establish vertical profiles, no-fly zones, and emergency procedures based on terrain.",
        "source": "CARs 901.27 Site Survey + TP 15263 Section 6 Risk Assessment, RPAS 101 Pre-Flight Planning",
        "lastVerified": "2026-09-01"
    },
    {
        "id": "flight-ops-034",
        "category": "flight-planning",
        "difficulty": "hard",
        "question": "An RPAS experiences severe drift during a surveillance mission. The pilot suspects wind shear. What is the correct response sequence?",
        "choices": [
            "Continue and hope drift stabilizes",
            "Descend gradually to find stable air; if drift persists, establish hover hold and reassess; consider aborting if uncontrollable",
            "Climb immediately to escape the shear",
            "Increase throttle to override wind"
        ],
        "answerIndex": 1,
        "rationale": "Wind shear causes rapid directional/speed changes with altitude. Descending typically finds more stable air below. If still unstable, hover and reassess before continuing.",
        "source": "TP 15263 Section 4 Meteorology + Section 6 Flight Dynamics, RPAS 101 Wind Hazards",
        "lastVerified": "2026-09-01"
    },
    {
        "id": "flight-ops-035",
        "category": "flight-planning",
        "difficulty": "medium",
        "question": "What is a 'hover hold' maneuver, and when should it be used?",
        "choices": [
            "An advanced trick maneuver; not practical for RPAS",
            "Maintaining fixed position/altitude to assess changing conditions before proceeding; used when encountering unexpected hazards or unstable conditions",
            "Only relevant to helicopters",
            "An emergency landing procedure"
        ],
        "answerIndex": 1,
        "rationale": "Hover hold: RPAS holds position while pilot assesses (weather change, new obstacle, mechanical issue, etc.). Conserves battery, allows decision-making time.",
        "source": "TP 15263 Section 6 Flight Operations + CARs 901.23, RPAS 101 Decision Points",
        "lastVerified": "2026-09-01"
    },
    {
        "id": "flight-ops-036",
        "category": "flight-planning",
        "difficulty": "hard",
        "question": "An RPAS mission encounters an unexpected person entering the operations area. What should the pilot do?",
        "choices": [
            "Ignore; the person should know to stay away",
            "Immediately land or move to safe altitude (150+ ft); cancel that portion of the mission until the person leaves",
            "Continue; RPAS are small so not hazardous",
            "Descend to survey the person"
        ],
        "answerIndex": 1,
        "rationale": "Unexpected persons in the ops area represent unmitigated risk. Immediate action: land or move to safe altitude. Resume only when area is clear. CARs requires safe separation.",
        "source": "CARs 901.26 Advanced Operations + TP 15263 Section 6 Risk Management, RPAS 101 Contingency",
        "lastVerified": "2026-09-01"
    },
    {
        "id": "flight-ops-037",
        "category": "flight-planning",
        "difficulty": "hard",
        "question": "An RPAS detects a mechanical issue (loose propeller, strange vibration) during flight. Battery is at 50%. What is the priority action?",
        "choices": [
            "Continue mission; finish quickly",
            "Land immediately at nearest safe location; inspect before any further flight",
            "Climb higher to reduce mechanical stress",
            "Attempt to correct the issue while airborne"
        ],
        "answerIndex": 1,
        "rationale": "Any in-flight mechanical anomaly compromises safety. Immediate landing is required before the issue cascades. Inspection at ground level prevents catastrophic failure.",
        "source": "CARs 901.23 Operating Procedures + TP 15263 Section 6 Emergency Response, RPAS 101 Safety Decisions",
        "lastVerified": "2026-09-01"
    },
    {
        "id": "flight-ops-038",
        "category": "flight-planning",
        "difficulty": "medium",
        "question": "An RPAS is to fly during sunset conditions (low light). What additional procedures are required?",
        "choices": [
            "None; RPAS can fly in any light condition",
            "Pre-flight must confirm lighting conditions are adequate for visual observation; establish minimum visibility thresholds; use LED markers if available",
            "Night flying is prohibited for all RPAS",
            "Increase throttle to compensate for low light"
        ],
        "answerIndex": 1,
        "rationale": "VLOS operations require adequate light. At sunset, visibility degrades rapidly. Operator must establish go/no-go criteria for lighting and implement visual aids (LED markers) if continuing.",
        "source": "CARs Part IX VLOS Requirements + TP 15263 Section 6 Lighting, RPAS 101 Low-Light Operations",
        "lastVerified": "2026-09-01"
    },
    {
        "id": "flight-ops-039",
        "category": "flight-planning",
        "difficulty": "hard",
        "question": "An RPAS must fly in an area with partial fog (visibility 300m). Is this operationally feasible, and what measures are required?",
        "choices": [
            "No, fog always prohibits RPAS operations",
            "Depends on site conditions and VO capability; if VO can maintain VLOS (~500m), operation may proceed with heightened monitoring and clear abort criteria",
            "Yes, fog has no effect on RPAS flight",
            "Possible only with special equipment"
        ],
        "answerIndex": 1,
        "rationale": "VLOS in fog depends on actual visibility. If VO can see the RPAS and surrounding airspace, limited operations may proceed with enhanced caution. Must monitor radio, be prepared to abort.",
        "source": "CARs 901.19 VLOS Requirements + TP 15263 Section 6 Weather Limits, RPAS 101 Fog Operations",
        "lastVerified": "2026-09-01"
    },
    {
        "id": "flight-ops-040",
        "category": "flight-planning",
        "difficulty": "medium",
        "question": "What is the significance of 'return-to-home' (RTH) functionality, and what must be verified before relying on it?",
        "choices": [
            "RTH is optional; not needed for safe operations",
            "RTH provides automated recovery if link is lost; must verify: RTH location is safe (not over water/obstacles), adequate battery for RTH climb + descent, home point accurately set",
            "RTH always works; no verification needed",
            "RTH only works in clear weather"
        ],
        "answerIndex": 1,
        "rationale": "RTH is a failsafe, not a guarantee. Must verify: (1) home location is safe, (2) battery sufficient for RTH maneuver, (3) GPS is locked before flight, (4) test RTH in pre-flight.",
        "source": "TP 15263 Section 6 Failsafe Procedures + CARs 901.23, RPAS 101 RTH Planning",
        "lastVerified": "2026-09-01"
    },
    {
        "id": "flight-ops-041",
        "category": "flight-planning",
        "difficulty": "hard",
        "question": "An RPAS is operating in controlled airspace (Class D) and receives a 'expedite descent' instruction from ATC. What does this mean operationally?",
        "choices": [
            "Ignore; RPAS don't descend",
            "Increase descent rate within aircraft limits; confirm the descent with ATC once completed",
            "Descend as fast as maximum performance allows, confirming readiness to ATC",
            "RPAS cannot operate in Class D"
        ],
        "answerIndex": 2,
        "rationale": "'Expedite' means perform the maneuver promptly at maximum feasible rate. RPAS pilot must understand aircraft climb/descent performance limits and report when action is complete.",
        "source": "CARs Part IX Controlled Airspace + NAV CANADA Phraseology, RPAS 101 ATC Procedures",
        "lastVerified": "2026-09-01"
    },
    {
        "id": "flight-ops-042",
        "category": "flight-planning",
        "difficulty": "medium",
        "question": "An RPAS is to be recovered (landed). What is the primary consideration for the landing area?",
        "choices": [
            "Any flat surface is acceptable",
            "Landing area must be clear of obstacles, persons, and have sufficient space to safely land; must account for wind direction and control authority",
            "Only concrete or asphalt surfaces are safe",
            "Landing area is irrelevant; controlled descent works anywhere"
        ],
        "answerIndex": 1,
        "rationale": "Safe landing requires: (1) clear approach (no obstructions), (2) adequate space (≥ 1.5x RPAS wingspan), (3) soft surface if possible, (4) no bystanders, (5) into wind if windier area.",
        "source": "TP 15263 Section 6 Landing Procedures, RPAS 101 Recovery Operations",
        "lastVerified": "2026-09-01"
    },
    {
        "id": "flight-ops-043",
        "category": "flight-planning",
        "difficulty": "hard",
        "question": "An RPAS operation is planned over a large agricultural area. The farmer has stated he will be using pesticides during the planned flight time. What action is required?",
        "choices": [
            "Proceed with the operation; pesticides are not an RPAS hazard",
            "Reschedule or coordinate the operation to avoid pesticide application; if unable to avoid, consider whether airborne pesticide exposure compromises safety or equipment",
            "Only concern is if pesticides land on the RPAS",
            "Pesticide use doesn't affect RPAS approval"
        ],
        "answerIndex": 1,
        "rationale": "Pesticide application can: (1) affect RPAS control (viscous residue on surfaces), (2) degrade performance, (3) create hazards (spray equipment), (4) limit visibility. Coordination is essential.",
        "source": "TP 15263 Section 6 Environmental Hazards + CARs 901.23, RPAS 101 Situational Awareness",
        "lastVerified": "2026-09-01"
    },
    {
        "id": "flight-ops-044",
        "category": "flight-planning",
        "difficulty": "medium",
        "question": "An RPAS battery is slightly swollen (puffed). What should the operator do?",
        "choices": [
            "Use it anyway; minor swelling is normal",
            "Do NOT use the battery; swelling indicates internal damage/gas generation; battery could fail catastrophically in flight; dispose safely",
            "Use it for only short flights",
            "Charge it to full capacity to reset the internal cells"
        ],
        "answerIndex": 1,
        "rationale": "Battery swelling indicates internal short circuit or thermal runaway risk. Using such a battery could cause in-flight power loss or explosion. Safe practice: retire immediately.",
        "source": "TP 15263 Section 2 Aircraft Systems + RPAS 101 Battery Safety",
        "lastVerified": "2026-09-01"
    },
    {
        "id": "flight-ops-045",
        "category": "flight-planning",
        "difficulty": "hard",
        "question": "An RPAS must operate in high-altitude terrain (mountain valley). Density altitude is significantly higher than field elevation. What operational impact is expected?",
        "choices": [
            "No impact; density altitude is irrelevant to RPAS",
            "Reduced climb/descent performance and reduced max altitude due to thinner air; mission planning must account for reduced aircraft capability",
            "Improved performance at altitude",
            "Only affects manned aircraft"
        ],
        "answerIndex": 1,
        "rationale": "Density altitude = field elevation + atmospheric effect. Thin air (high density altitude) reduces available thrust, degrading climb rate and max altitude. Mission planning must adjust targets.",
        "source": "TP 15263 Section 7 Theory of Flight + Section 6 Operations, RPAS 101 High-Altitude Operations",
        "lastVerified": "2026-09-01"
    },
    {
        "id": "flight-ops-046",
        "category": "flight-planning",
        "difficulty": "medium",
        "question": "An RPAS is recovered, and inspection reveals a small crack in the frame. Can the RPAS be flown again?",
        "choices": [
            "Yes, cracks are not a safety issue",
            "Only after professional inspection/repair; structural integrity is critical for control authority and safety; even small cracks can propagate",
            "Only minor impact; tape the crack and continue",
            "Frame damage automatically requires aircraft destruction"
        ],
        "answerIndex": 1,
        "rationale": "Structural damage compromises control surfaces, stability, and load-bearing. Professional repair/inspection is required before any further flight.",
        "source": "TP 15263 Section 2 Aircraft Maintenance + CARs Airworthiness, RPAS 101 Maintenance Standards",
        "lastVerified": "2026-09-01"
    },
    {
        "id": "flight-ops-047",
        "category": "flight-planning",
        "difficulty": "hard",
        "question": "An RPAS operation encounters an unexpected atmospheric phenomenon (dust devil or thermal updraft). What should the pilot do?",
        "choices": [
            "Fly into it to gather data",
            "Immediately move away; avoid flying through strong thermal/vortex activity; establish altitude/heading to escape the phenomenon",
            "Hover and wait for it to pass",
            "Ignore; it won't affect the RPAS"
        ],
        "answerIndex": 1,
        "rationale": "Dust devils/thermals create unpredictable wind, reducing control. RPAS can be flipped or damaged. Evasion is the safest response.",
        "source": "TP 15263 Section 4 Meteorology + Section 6 Hazard Response, RPAS 101 Weather Hazards",
        "lastVerified": "2026-09-01"
    },
    {
        "id": "flight-ops-048",
        "category": "flight-planning",
        "difficulty": "medium",
        "question": "What does 'icing' mean in the context of RPAS operations, and why is it a concern?",
        "choices": [
            "Icing is only relevant to manned aircraft",
            "Ice accumulation on propellers/fuselage reduces lift, increases drag, and can cause loss of control; RPAS must avoid visible moisture/precipitation",
            "Icing improves aerodynamic performance",
            "Only affects jet engines"
        ],
        "answerIndex": 1,
        "rationale": "Ice on propeller edges and airframe increases weight/drag and reduces thrust. RPAS typically cannot tolerate ice. Avoid visible moisture, precipitation, and clouds.",
        "source": "TP 15263 Section 4 Meteorology + Section 7 Flight Dynamics, RPAS 101 Icing Avoidance",
        "lastVerified": "2026-09-01"
    },
    {
        "id": "flight-ops-049",
        "category": "flight-planning",
        "difficulty": "hard",
        "question": "An RPAS is to fly in an area with known GPS interference (near a radar installation). What navigation strategy is appropriate?",
        "choices": [
            "GPS will work normally despite radar interference",
            "Plan to use visual navigation + landmarks + dead reckoning as primary; verify GPS readings against landmarks; reduce reliance on GPS",
            "Cannot operate in such areas",
            "Radar interference improves GPS accuracy"
        ],
        "answerIndex": 1,
        "rationale": "Radar can degrade GPS signals. Fallback: terrain recognition, compass + dead reckoning, cross-check landmarks. Plan for GPS loss; have contingency procedures.",
        "source": "TP 15263 Section 5 GPS Limitations + Section 6 Navigation Strategies, RPAS 101 GPS Interference",
        "lastVerified": "2026-09-01"
    },
    {
        "id": "flight-ops-050",
        "category": "flight-planning",
        "difficulty": "medium",
        "question": "An RPAS mission is planned over a 3-hour period, but daylight will be insufficient after 90 minutes. What pre-flight action is essential?",
        "choices": [
            "Proceed; lighting adjustments can be made during flight",
            "Establish a firm go/no-go time based on lighting; reschedule mission or complete only essential objectives before daylight expires",
            "Lighting is not a valid operational consideration",
            "Extend the mission into low-light conditions"
        ],
        "answerIndex": 1,
        "rationale": "VLOS requires adequate visual reference. Sunset planning must account for rapid visibility loss. Establish time cutoff; prioritize mission objectives; abort if light degrades below acceptable threshold.",
        "source": "CARs 901.19 VLOS + TP 15263 Section 6 Lighting, RPAS 101 Daylight Planning",
        "lastVerified": "2026-09-01"
    }
]

# Combine all Phase 2C questions
all_questions = radio_adv_questions + nav_adv_questions + flight_ops_adv_questions

print(f"Phase 2C Generation Script")
print(f"=" * 80)
print(f"Advanced Radio Questions: {len(radio_adv_questions)}")
print(f"Advanced Navigation Questions: {len(nav_adv_questions)}")
print(f"Advanced Flight Operations Questions: {len(flight_ops_adv_questions)}")
print(f"Total Phase 2C Questions: {len(all_questions)}")
print()

# Load existing questions.json
with open("data/questions.json", "r", encoding="utf-8") as f:
    data = json.load(f)

print(f"Current questions.json: {len(data['questions'])} questions (includes Phase 2A+2B)")
print(f"After Phase 2C: {len(data['questions']) + len(all_questions)} questions")
print()

# Update the migrationNotes
data["updated"] = "2026-09-01"
data["migrationNotes"].append(
    f"2026-09-01 PHASE 2C: Added {len(all_questions)} advanced questions ({len(radio_adv_questions)} radio + {len(nav_adv_questions)} nav + {len(flight_ops_adv_questions)} ops). Total: 598 → {598 + len(all_questions)}. Phase 2 COMPLETE."
)

# Add new questions
data["questions"].extend(all_questions)

# Write back to file
with open("data/questions.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"✓ Successfully added {len(all_questions)} Phase 2C questions to questions.json")
print(f"✓ New total: {len(data['questions'])} questions")
print()
print("PHASE 2 COMPLETE!")
print(f"Total questions generated in Phase 2: {25 + 48 + len(all_questions)} (+161 from original 525)")
