#!/usr/bin/env python3
"""Add TP 15263 core Basic/Advanced expansion questions."""

import json
from datetime import date
from pathlib import Path


QUESTIONS = [
    {
        "id": "tp15263-001",
        "category": "regulations",
        "difficulty": "hard",
        "question": "A pilot plans a VLOS small-RPA flight in Class C controlled airspace. Which statement best describes the regulatory starting point?",
        "choices": [
            "The pilot must operate in accordance with an authorization from the air traffic control unit.",
            "The pilot may enter Class C airspace if the RPA remains below 122 m AGL.",
            "The pilot may enter Class C airspace after broadcasting intentions on 126.7 MHz.",
            "The pilot may enter Class C airspace if a visual observer is used."
        ],
        "answerIndex": 0,
        "rationale": "Controlled-airspace RPAS operations are not made legal by altitude, blind broadcast, or use of an observer alone. CARs 901.14 requires the operation to be in accordance with the applicable ATC authorization.",
        "source": "CARs 901.14; TP 15263, Section 1 - controlled airspace operating rules",
        "sourceRefs": ["CARs 901.14", "TP 15263 Section 1"],
        "carsSection": "901.14",
        "examScope": "core-basic-advanced",
        "examLevel": "advanced",
        "tp15263Section": "1",
        "knowledgeArea": "Canadian Aviation Regulations",
        "knowledgeTopic": "Controlled airspace",
        "learningObjective": "Describe the communication and authorization requirements for small-RPA VLOS operations in controlled airspace.",
        "lastVerified": "2026-09-03"
    },
    {
        "id": "tp15263-002",
        "category": "airspace",
        "difficulty": "hard",
        "question": "During a flight near controlled airspace, the RPA loses command and control and is likely to enter the control zone. What is the immediate required action?",
        "choices": [
            "Notify the appropriate ATS unit or user agency immediately.",
            "Wait until the RPA lands, then enter the event in the flight log.",
            "Continue the flight if the aircraft is still visible.",
            "Notify Transport Canada within 30 days."
        ],
        "answerIndex": 0,
        "rationale": "CARs 901.15 requires immediate notification when an RPA is no longer under the pilot's control and inadvertently enters, or is likely to enter, controlled airspace.",
        "source": "CARs 901.15; TP 15263, Section 1 - airspace and emergency procedures",
        "sourceRefs": ["CARs 901.15", "TP 15263 Section 1"],
        "carsSection": "901.15",
        "examScope": "core-basic-advanced",
        "examLevel": "basic-advanced",
        "tp15263Section": "1",
        "knowledgeArea": "Canadian Aviation Regulations",
        "knowledgeTopic": "Loss of control near controlled airspace",
        "learningObjective": "Recall the immediate notification requirement when an uncontrolled RPA enters or may enter controlled airspace.",
        "lastVerified": "2026-09-03"
    },
    {
        "id": "tp15263-003",
        "category": "airspace",
        "difficulty": "medium",
        "question": "An RPA is drifting toward Class F restricted airspace listed in the Designated Airspace Handbook after a command-link failure. What must the operator ensure?",
        "choices": [
            "The appropriate ATS unit or user agency is notified immediately.",
            "The operator waits for the airspace user agency to call first.",
            "The event is reported only if another aircraft takes avoiding action.",
            "The flight continues because Class F restrictions do not apply to small RPA."
        ],
        "answerIndex": 0,
        "rationale": "CARs 900.07 requires immediate notification if an RPA is no longer under control and inadvertently enters, or is likely to enter, Class F Special Use Restricted airspace.",
        "source": "CARs 900.07; NAV CANADA DAH; TP 15263, Section 1 - Class F airspace",
        "sourceRefs": ["CARs 900.07", "NAV CANADA DAH", "TP 15263 Section 1"],
        "carsSection": "900.07",
        "examScope": "core-basic-advanced",
        "examLevel": "basic-advanced",
        "tp15263Section": "1",
        "knowledgeArea": "Canadian Aviation Regulations",
        "knowledgeTopic": "Class F Special Use Restricted airspace",
        "learningObjective": "Recall the required action when an uncontrolled RPA enters or may enter Class F restricted airspace.",
        "lastVerified": "2026-09-03"
    },
    {
        "id": "tp15263-004",
        "category": "flight-planning",
        "difficulty": "hard",
        "question": "A site survey shows a tower crane inside the planned lateral area, a nearby road with intermittent pedestrian traffic, and a possible emergency landing area. What is the best regulatory interpretation?",
        "choices": [
            "The pilot must determine whether the operational volume is suitable before flight, taking relevant site-survey factors into account.",
            "The pilot may ignore ground hazards if the RPA will remain more than 30 m from people.",
            "The pilot only needs to confirm weather and battery state before launch.",
            "The pilot may proceed if the RPA has a return-to-home function."
        ],
        "answerIndex": 0,
        "rationale": "CARs 901.27 requires the pilot to determine that the operational volume is suitable by conducting a site survey before the operation. Obstacles, bystanders, traffic, and emergency areas are operational suitability factors.",
        "source": "CARs 901.27; TP 15263, Section 6 - site surveys and flight operations",
        "sourceRefs": ["CARs 901.27", "TP 15263 Section 6"],
        "carsSection": "901.27",
        "examScope": "core-basic-advanced",
        "examLevel": "basic-advanced",
        "tp15263Section": "6",
        "knowledgeArea": "Flight operations",
        "knowledgeTopic": "Site survey and operational volume",
        "learningObjective": "Assess whether the operational volume is suitable before commencing a small-RPA operation.",
        "lastVerified": "2026-09-03"
    },
    {
        "id": "tp15263-005",
        "category": "weather",
        "difficulty": "medium",
        "question": "A multirotor normally launches safely at sea level, but the planned site is hot, humid, and at a high field elevation. What is the key performance concern?",
        "choices": [
            "Higher density altitude can reduce lift and power margin, increasing takeoff and climb risk.",
            "Higher density altitude always improves propeller efficiency.",
            "Humidity eliminates the need to consider battery temperature.",
            "Field elevation matters only to crewed aircraft."
        ],
        "answerIndex": 0,
        "rationale": "TP 15263 meteorology and performance knowledge requires pilots to assess density altitude and weather effects against the aircraft's operating limitations before flight.",
        "source": "TP 15263, Sections 4 and 6 - density altitude and aircraft performance",
        "sourceRefs": ["TP 15263 Section 4", "TP 15263 Section 6"],
        "examScope": "core-basic-advanced",
        "examLevel": "basic-advanced",
        "tp15263Section": "4",
        "knowledgeArea": "Meteorology",
        "knowledgeTopic": "Density altitude",
        "learningObjective": "Assess weather and density-altitude effects for anticipated launch and flight performance.",
        "lastVerified": "2026-09-03"
    },
    {
        "id": "tp15263-006",
        "category": "human-factors",
        "difficulty": "medium",
        "question": "A pilot has been scanning mostly through the control-station display and has not looked around the operating area for several minutes. Which human-factors risk is most directly involved?",
        "choices": [
            "Reduced situational awareness from poor visual scanning.",
            "Improved vigilance because instrument displays replace outside scanning.",
            "A regulatory violation only if the RPA is above 122 m AGL.",
            "A radio-phraseology issue rather than a human-factors issue."
        ],
        "answerIndex": 0,
        "rationale": "TP 15263 human-factors objectives include visual scanning and situational awareness. Display fixation can reduce the pilot's awareness of aircraft, people, obstacles, and changing conditions.",
        "source": "TP 15263, Section 3 - visual scanning and situational awareness",
        "sourceRefs": ["TP 15263 Section 3"],
        "examScope": "core-basic-advanced",
        "examLevel": "basic-advanced",
        "tp15263Section": "3",
        "knowledgeArea": "Human factors",
        "knowledgeTopic": "Visual scanning and situational awareness",
        "learningObjective": "Describe good scanning techniques and factors that affect situational awareness.",
        "lastVerified": "2026-09-03"
    },
    {
        "id": "tp15263-007",
        "category": "visual-observers",
        "difficulty": "hard",
        "question": "A visual observer is watching the RPA video feed from the passenger seat while also driving the support vehicle. Which statement best applies?",
        "choices": [
            "The observer may not perform visual-observer duties while operating a moving vehicle.",
            "This is permitted if the vehicle remains below 30 km/h.",
            "This is permitted in uncontrolled airspace only.",
            "This is permitted if the pilot and observer use radios."
        ],
        "answerIndex": 0,
        "rationale": "CARs 901.20 prohibits a visual observer from performing visual-observer duties while operating a moving vehicle, vessel, or aircraft.",
        "source": "CARs 901.20; TP 15263, Section 6 - visual observers",
        "sourceRefs": ["CARs 901.20", "TP 15263 Section 6"],
        "carsSection": "901.20",
        "examScope": "core-basic-advanced",
        "examLevel": "basic-advanced",
        "tp15263Section": "6",
        "knowledgeArea": "Flight operations",
        "knowledgeTopic": "Visual observers",
        "learningObjective": "Apply visual-observer limitations and responsibilities to operational scenarios.",
        "lastVerified": "2026-09-03"
    },
    {
        "id": "tp15263-008",
        "category": "aerodromes",
        "difficulty": "hard",
        "question": "An Advanced VLOS flight is planned 0.8 NM from the centre of a heliport. What condition must be satisfied under Division V?",
        "choices": [
            "The operation must follow the established RPAS safe-use procedure applicable to that heliport.",
            "The pilot may proceed if the RPA remains below rooftop height.",
            "The pilot may proceed after notifying any nearby building owner.",
            "No special condition applies because heliports are not airports."
        ],
        "answerIndex": 0,
        "rationale": "CARs 901.73 prohibits Division V operations less than 1 NM from the centre of a heliport unless the operation follows the established RPAS safe-use procedure for that heliport.",
        "source": "CARs 901.73; TP 15263, Section 1 - aerodromes, airports, and heliports",
        "sourceRefs": ["CARs 901.73", "TP 15263 Section 1"],
        "carsSection": "901.73",
        "examScope": "core-advanced",
        "examLevel": "advanced",
        "tp15263Section": "1",
        "knowledgeArea": "Canadian Aviation Regulations",
        "knowledgeTopic": "Operations near heliports",
        "learningObjective": "Apply airport and heliport proximity rules for Advanced small-RPA operations.",
        "lastVerified": "2026-09-03"
    },
    {
        "id": "tp15263-009",
        "category": "radio",
        "difficulty": "medium",
        "question": "When making an operational radio call, which information is most important for other aviation users to build traffic awareness?",
        "choices": [
            "Who you are calling, who you are, where you are, altitude, intentions, and any relevant timing.",
            "Only the pilot's name and phone number.",
            "Only the RPA manufacturer's model name.",
            "Only the battery percentage and camera heading."
        ],
        "answerIndex": 0,
        "rationale": "TP 15263 radiotelephony objectives require practical understanding of routine calls, position reports, common frequencies, and clear phraseology. A useful call identifies station, aircraft/pilot, position, altitude, and intentions.",
        "source": "TP 15263, Section 8 - routine calls and radiotelephony",
        "sourceRefs": ["TP 15263 Section 8"],
        "examScope": "core-advanced",
        "examLevel": "advanced",
        "tp15263Section": "8",
        "knowledgeArea": "Radiotelephony",
        "knowledgeTopic": "Routine calls",
        "learningObjective": "List the contents of a routine call to ATC or an advisory broadcast.",
        "lastVerified": "2026-09-03"
    },
    {
        "id": "tp15263-010",
        "category": "navigation",
        "difficulty": "medium",
        "question": "A NOTAM or chart reference gives a position in latitude and longitude. What core navigation skill is being tested when the pilot transfers it to a VNC or VTA?",
        "choices": [
            "Operational understanding of coordinates and aeronautical-chart interpretation.",
            "Radio reception troubleshooting.",
            "Battery endurance calculation.",
            "Manufacturer safety-assurance declaration review."
        ],
        "answerIndex": 0,
        "rationale": "TP 15263 navigation objectives include longitude/latitude understanding and using VNC/VTA charts to locate positions and interpret aeronautical chart information.",
        "source": "TP 15263, Section 5 - coordinates and aeronautical charts",
        "sourceRefs": ["TP 15263 Section 5"],
        "examScope": "core-basic-advanced",
        "examLevel": "basic-advanced",
        "tp15263Section": "5",
        "knowledgeArea": "Navigation",
        "knowledgeTopic": "Coordinates and charts",
        "learningObjective": "Locate a position on an aeronautical chart using coordinate information.",
        "lastVerified": "2026-09-03"
    },
    {
        "id": "tp15263-011",
        "category": "theory-of-flight",
        "difficulty": "medium",
        "question": "A fixed-wing RPA is loaded with the centre of gravity too far aft. Which effect is the best exam-style concern?",
        "choices": [
            "Reduced longitudinal stability and more difficult pitch recovery.",
            "Improved stability in all axes.",
            "No effect because only total weight matters.",
            "A radio interference hazard only."
        ],
        "answerIndex": 0,
        "rationale": "TP 15263 theory-of-flight objectives include stability and centre-of-gravity effects. An aft CG reduces longitudinal stability and can make recovery more difficult.",
        "source": "TP 15263, Section 7 - stability and centre of gravity",
        "sourceRefs": ["TP 15263 Section 7"],
        "examScope": "core-basic-advanced",
        "examLevel": "basic-advanced",
        "tp15263Section": "7",
        "knowledgeArea": "Theory of flight",
        "knowledgeTopic": "Stability and centre of gravity",
        "learningObjective": "Explain how centre-of-gravity position affects longitudinal stability.",
        "lastVerified": "2026-09-03"
    },
    {
        "id": "tp15263-012",
        "category": "aircraft-systems",
        "difficulty": "medium",
        "question": "A pilot finds swelling in one lithium battery pack during pre-flight. What is the best operational decision?",
        "choices": [
            "Remove the battery from service and follow safe handling/disposal procedures.",
            "Use the battery if the first voltage reading is normal.",
            "Use the battery only for flights below 30 m AGL.",
            "Cool it briefly and continue because swelling is cosmetic."
        ],
        "answerIndex": 0,
        "rationale": "TP 15263 systems knowledge includes batteries, electrical components, and keeping system components serviceable. Battery swelling is a serviceability and fire-risk indicator.",
        "source": "TP 15263, Section 2 - electrical systems and batteries",
        "sourceRefs": ["TP 15263 Section 2"],
        "examScope": "core-basic-advanced",
        "examLevel": "basic-advanced",
        "tp15263Section": "2",
        "knowledgeArea": "RPA systems",
        "knowledgeTopic": "Batteries and electrical systems",
        "learningObjective": "Assess battery condition and serviceability before flight.",
        "lastVerified": "2026-09-03"
    },
    {
        "id": "tp15263-013",
        "category": "flight-planning",
        "difficulty": "hard",
        "question": "Before launch, forecast winds are within limits, but gusts at the site are increasing and exceed the aircraft manual's demonstrated limit. What should the pilot do?",
        "choices": [
            "Delay or cancel unless the operation can be kept within the RPAS limitations.",
            "Launch and rely on GPS position hold to overcome the gusts.",
            "Launch only if flying into wind during takeoff.",
            "Proceed because forecasts, not observed weather, govern the decision."
        ],
        "answerIndex": 0,
        "rationale": "TP 15263 requires pilots to assess actual weather and aircraft performance against operating limitations. CARs pre-flight duties also require the pilot to verify that the aircraft is fit and the operation can be conducted safely.",
        "source": "CARs 901.28; TP 15263, Sections 4 and 6 - weather, limits, and pre-flight planning",
        "sourceRefs": ["CARs 901.28", "TP 15263 Section 4", "TP 15263 Section 6"],
        "carsSection": "901.28",
        "examScope": "core-basic-advanced",
        "examLevel": "basic-advanced",
        "tp15263Section": "6",
        "knowledgeArea": "Flight operations",
        "knowledgeTopic": "Weather and aircraft limitations",
        "learningObjective": "Use observed weather and performance limitations to make a safe go/no-go decision.",
        "lastVerified": "2026-09-03"
    },
    {
        "id": "tp15263-014",
        "category": "regulations",
        "difficulty": "medium",
        "question": "What is the regulatory issue if a pilot flies so close to a helicopter that the helicopter pilot must manoeuvre to avoid conflict?",
        "choices": [
            "CARs prohibits operating an RPA in such proximity to another aircraft as to create a risk of collision.",
            "There is no issue if the RPA is lighter than 25 kg.",
            "There is no issue if the RPA remains in uncontrolled airspace.",
            "The only issue is whether the RPA had a transponder."
        ],
        "answerIndex": 0,
        "rationale": "CARs 901.18 is a direct collision-risk rule. Airspace class, aircraft weight under the small-RPA category, or equipment do not remove the duty to avoid creating a collision risk.",
        "source": "CARs 901.18; TP 15263, Section 1 - right-of-way and collision avoidance",
        "sourceRefs": ["CARs 901.18", "TP 15263 Section 1"],
        "carsSection": "901.18",
        "examScope": "core-basic-advanced",
        "examLevel": "basic-advanced",
        "tp15263Section": "1",
        "knowledgeArea": "Canadian Aviation Regulations",
        "knowledgeTopic": "Collision avoidance",
        "learningObjective": "Apply the prohibition against operating an RPA near another aircraft in a way that creates collision risk.",
        "lastVerified": "2026-09-03"
    },
    {
        "id": "tp15263-015",
        "category": "human-factors",
        "difficulty": "medium",
        "question": "A pilot took a new over-the-counter cold medication before an early morning RPAS operation. Which TP 15263 topic is most directly engaged?",
        "choices": [
            "Medication effects, alertness, and pilot fitness.",
            "Aeronautical chart longitude conversion.",
            "Manufacturer declaration of safety assurance.",
            "Runway marking recognition only."
        ],
        "answerIndex": 0,
        "rationale": "TP 15263 human-factors objectives include medication effects, fatigue, alertness, and other physiological or psychological factors that can impair pilot performance.",
        "source": "TP 15263, Section 3 - medications and alertness",
        "sourceRefs": ["TP 15263 Section 3"],
        "examScope": "core-basic-advanced",
        "examLevel": "basic-advanced",
        "tp15263Section": "3",
        "knowledgeArea": "Human factors",
        "knowledgeTopic": "Medication and alertness",
        "learningObjective": "Describe how medication and alertness affect RPAS pilot performance.",
        "lastVerified": "2026-09-03"
    },
    {
        "id": "tp15263-016",
        "category": "navigation",
        "difficulty": "hard",
        "question": "A pilot converts a planned launch time from local time to UTC incorrectly and misses a NOTAM active period by one hour. Which knowledge requirement was weak?",
        "choices": [
            "Time conversion between UTC and local time for flight planning.",
            "Servo-motor function.",
            "Angle of attack recovery.",
            "Visual-observer qualification."
        ],
        "answerIndex": 0,
        "rationale": "TP 15263 navigation objectives include the 24-hour system and converting UTC to local time and vice versa. NOTAM timing errors can invalidate pre-flight planning.",
        "source": "TP 15263, Section 5 - time and longitude; NAV CANADA NOTAM context",
        "sourceRefs": ["TP 15263 Section 5", "NAV CANADA NOTAM procedures"],
        "examScope": "core-basic-advanced",
        "examLevel": "basic-advanced",
        "tp15263Section": "5",
        "knowledgeArea": "Navigation",
        "knowledgeTopic": "UTC and local time",
        "learningObjective": "Convert UTC to local time and local time to UTC for operational planning.",
        "lastVerified": "2026-09-03"
    },
    {
        "id": "tp15263-017",
        "category": "radio",
        "difficulty": "medium",
        "question": "A pilot hears a weak transmission that may indicate crewed traffic near the operating area. What is the best radiotelephony and crew-resource response?",
        "choices": [
            "Clarify the traffic information if appropriate and update the RPAS plan to maintain separation.",
            "Ignore the call because RPAS pilots are not affected by aviation radio traffic.",
            "Increase altitude to improve radio reception before assessing traffic.",
            "Continue unless ATC directly orders the RPAS to land."
        ],
        "answerIndex": 0,
        "rationale": "TP 15263 radiotelephony includes reception factors and advisory communication. The operational purpose is traffic awareness and conflict avoidance, not radio use in isolation.",
        "source": "TP 15263, Section 8 - radio reception and advisory communications",
        "sourceRefs": ["TP 15263 Section 8"],
        "examScope": "core-advanced",
        "examLevel": "advanced",
        "tp15263Section": "8",
        "knowledgeArea": "Radiotelephony",
        "knowledgeTopic": "Reception performance and traffic advisories",
        "learningObjective": "Describe factors affecting radio reception and apply advisory information to avoid conflict.",
        "lastVerified": "2026-09-03"
    },
    {
        "id": "tp15263-018",
        "category": "aircraft-systems",
        "difficulty": "hard",
        "question": "After a firmware update, a control station shows changed return-to-home behaviour. What is the best pre-flight response?",
        "choices": [
            "Review and verify the current configuration before relying on the function operationally.",
            "Assume the previous settings were preserved and proceed.",
            "Disable all automated functions because automation is not permitted.",
            "Proceed if the battery is fully charged."
        ],
        "answerIndex": 0,
        "rationale": "TP 15263 systems topics include the control station, software versions, orientation, and system configuration. Software changes can alter critical behaviour and should be verified before flight.",
        "source": "TP 15263, Section 2 - control station and software versions",
        "sourceRefs": ["TP 15263 Section 2"],
        "examScope": "core-basic-advanced",
        "examLevel": "basic-advanced",
        "tp15263Section": "2",
        "knowledgeArea": "RPA systems",
        "knowledgeTopic": "Control station software and configuration",
        "learningObjective": "Verify control-station configuration and software behaviour before flight.",
        "lastVerified": "2026-09-03"
    },
    {
        "id": "tp15263-019",
        "category": "weather",
        "difficulty": "medium",
        "question": "Why can a low cloud base or lowering visibility matter even when an RPA remains below the maximum permitted altitude?",
        "choices": [
            "The pilot must still maintain VLOS and avoid creating conflict with other aircraft or hazards.",
            "Cloud base has no relevance below 122 m AGL.",
            "Visibility matters only for night operations.",
            "Weather minima apply only to aircraft carrying people."
        ],
        "answerIndex": 0,
        "rationale": "TP 15263 meteorology includes cloud and visibility effects on operations. Altitude compliance does not replace VLOS, traffic awareness, and hazard avoidance duties.",
        "source": "TP 15263, Section 4 - cloud, visibility, and operational weather",
        "sourceRefs": ["TP 15263 Section 4"],
        "examScope": "core-basic-advanced",
        "examLevel": "basic-advanced",
        "tp15263Section": "4",
        "knowledgeArea": "Meteorology",
        "knowledgeTopic": "Visibility and cloud",
        "learningObjective": "Assess cloud and visibility conditions for safe VLOS RPAS operations.",
        "lastVerified": "2026-09-03"
    },
    {
        "id": "tp15263-020",
        "category": "flight-planning",
        "difficulty": "hard",
        "question": "A pilot plans to rely on one emergency landing site, but the wind direction would put the RPA over uninvolved people during a likely forced landing. What should change?",
        "choices": [
            "The plan should be revised so emergency procedures and recovery areas do not create unacceptable risk to people or property.",
            "Nothing; emergency planning is optional for small RPA.",
            "Only the checklist title needs to be changed.",
            "The flight may continue if the RPA is insured."
        ],
        "answerIndex": 0,
        "rationale": "TP 15263 flight-operations objectives require practical pre-flight planning, hazard assessment, and emergency procedures. The site survey and operational plan must remain suitable for actual conditions.",
        "source": "CARs 901.27; TP 15263, Section 6 - emergency procedures and site survey",
        "sourceRefs": ["CARs 901.27", "TP 15263 Section 6"],
        "carsSection": "901.27",
        "examScope": "core-basic-advanced",
        "examLevel": "basic-advanced",
        "tp15263Section": "6",
        "knowledgeArea": "Flight operations",
        "knowledgeTopic": "Emergency planning",
        "learningObjective": "Apply site-survey and emergency-planning knowledge to avoid creating risk during abnormal events.",
        "lastVerified": "2026-09-03"
    }
]


path = Path("data/questions.json")
data = json.loads(path.read_text(encoding="utf-8"))
existing_ids = {question["id"] for question in data["questions"]}
duplicates = existing_ids.intersection(question["id"] for question in QUESTIONS)
if duplicates:
    raise ValueError(f"Question IDs already exist: {sorted(duplicates)}")

data["questions"].extend(QUESTIONS)
data["totalQuestions"] = len(data["questions"])
data["updated"] = date.today().isoformat()
data["lastUpdated"] = date.today().isoformat()
data["migrationNotes"].append(
    "2026-09-03 PHASE 7: Added 20 TP 15263 core Basic/Advanced expansion questions with explicit examScope, examLevel, TP section, learning objective, and sourceRefs metadata."
)
path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

print(f"Added {len(QUESTIONS)} TP 15263 core questions. Total: {data['totalQuestions']}")
