#!/usr/bin/env python3
"""
Generate new Advanced RPAS questions for uncovered topics

Generates 3-5 questions per uncovered topic based on:
- CARs Part IX (detailed text)
- AIM Chapter on RPAS
- Learning objectives from Knowledge Requirements
"""

import json
from pathlib import Path
from datetime import datetime

# Template for new questions covering gaps
new_questions_data = [
    # AERODROME OPERATIONS (CARs 301-302)
    {
        "id": "aero-adv-001",
        "category": "aerodromes",
        "difficulty": "hard",
        "question": "Before operating an aircraft at an uncontrolled aerodrome, the pilot-in-command must ensure that:",
        "choices": [
            "There is no likelihood of collision and the aerodrome is suitable for the intended operation",
            "The aerodrome has an airport certificate issued",
            "Weather conditions are VFR with minimum 3 miles visibility",
            "Proper filing of a flight plan has been completed"
        ],
        "answerIndex": 0,
        "rationale": "CARs 602.96(2) requires the pilot-in-command to be satisfied that there is no likelihood of collision with another aircraft or vehicle, and that the aerodrome is suitable for the intended operation. This is a fundamental requirement before any aerodrome operation.",
        "source": "CARs 602.96 + TP 15263 Section 7",
        "carsSection": "602.96"
    },
    {
        "id": "aero-adv-002",
        "category": "aerodromes",
        "difficulty": "hard",
        "question": "When operating at an uncontrolled aerodrome, the pilot-in-command must conform to or avoid the traffic pattern formed by other aircraft. What is the mandatory turning direction within the aerodrome traffic circuit?",
        "choices": [
            "All turns to the left, unless right turns are specified by the Minister or authorized by ATC",
            "All turns to the right to ensure visibility of other aircraft",
            "Alternating left and right turns depending on runway direction",
            "Turns in either direction as determined by wind direction"
        ],
        "answerIndex": 0,
        "rationale": "CARs 602.96(3)(c) specifies that all turns within the aerodrome traffic circuit must be to the left, except where right turns are specified by the Minister in the Canada Flight Supplement or authorized by the appropriate air traffic control unit. This is a safety requirement to ensure predictable aircraft movements.",
        "source": "CARs 602.96(3)(c) + AIM RPA Section 8.2",
        "carsSection": "602.96"
    },
    {
        "id": "aero-adv-003",
        "category": "aerodromes",
        "difficulty": "hard",
        "question": "An RPA is operating near an aerodrome listed in the Canada Flight Supplement. What must the pilot ensure regarding the established aircraft traffic pattern?",
        "choices": [
            "The operation does not interfere with an aircraft operating in the established traffic pattern",
            "The pilot files a flight plan before operating nearby",
            "The RPA follows the same circuit turns as crewed aircraft",
            "No additional consideration is needed when the RPA remains below 400 feet AGL"
        ],
        "answerIndex": 0,
        "rationale": "CAR 901.47(1) prohibits operating an RPA at or near an aerodrome listed in the Canada Flight Supplement or Water Aerodrome Supplement in a manner that could interfere with an aircraft operating in the established traffic pattern.",
        "source": "CAR 901.47(1) + TP 15263 Section 1",
        "carsSection": "901.47"
    },
    {
        "id": "aero-adv-004",
        "category": "aerodromes",
        "difficulty": "hard",
        "question": "At a controlled aerodrome, what clearance must a pilot-in-command obtain before taxiing, taking off, or landing?",
        "choices": [
            "Clearance from the appropriate air traffic control unit, either by radio communication or visual signal",
            "Clearance from the aerodrome operations manager only",
            "Notification to other aircraft on the common frequency",
            "A filed flight plan is sufficient clearance"
        ],
        "answerIndex": 0,
        "rationale": "CARs 602.96(3)(g) requires that where the aerodrome is a controlled aerodrome, the pilot-in-command must obtain clearance from the appropriate air traffic control unit, either by radio communication or by visual signal, before taxiing, taking off, or landing. This is a mandatory safety requirement at all controlled aerodromes.",
        "source": "CARs 602.96(3)(g) + AIM RPA Section 3.1",
        "carsSection": "602.96"
    },
    
    # AERODROME PROHIBITIONS (CARs 301-302)
    {
        "id": "aero-adv-005",
        "category": "aerodromes",
        "difficulty": "hard",
        "question": "No person shall walk, stand, drive a vehicle, park an aircraft, or cause an obstruction on the movement area of an aerodrome except in accordance with permission given by:",
        "choices": [
            "The operator of the aerodrome AND the appropriate air traffic services unit (if applicable)",
            "The operator of the aerodrome only",
            "Any ground personnel present at the aerodrome",
            "Self-authorization based on pilot judgment"
        ],
        "answerIndex": 0,
        "rationale": "CARs 301.08(a) prohibits persons from walking, standing, driving, or parking on an aerodrome movement area unless permission is given by (i) the operator of the aerodrome, and (ii) where applicable, the appropriate air traffic services unit. Both approvals may be required.",
        "source": "CARs 301.08(a) + TP 15263 Section 7",
        "carsSection": "301.08"
    },
    {
        "id": "aero-adv-006",
        "category": "aerodromes",
        "difficulty": "medium",
        "question": "What lighting is required when towing an aircraft on the active movement area of an aerodrome at night?",
        "choices": [
            "Operating wingtip, tail and anti-collision lights on the aircraft, OR lights on the towing vehicle directed at the aircraft",
            "Landing lights on both the towing vehicle and aircraft",
            "Only anti-collision lights on the aircraft being towed",
            "Navigation lights are sufficient for night towing"
        ],
        "answerIndex": 0,
        "rationale": "CARs 301.08(b) requires that when towing an aircraft on an active movement area at night, the aircraft must display operating wingtip, tail and anti-collision lights, OR be illuminated by lights mounted on the towing vehicle and directed at the aircraft. This ensures visibility to other personnel and aircraft.",
        "source": "CARs 301.08(b) + AIM RPA Section 8.3",
        "carsSection": "301.08"
    },
    {
        "id": "aero-adv-007",
        "category": "aerodromes",
        "difficulty": "medium",
        "question": "Which of the following is prohibited at an aerodrome according to CARs 301.08?",
        "choices": [
            "Knowingly removing, defacing, or interfering with aerodrome markers or lights used for air navigation without permission",
            "Removing aircraft from the apron during daylight hours",
            "Conducting routine maintenance on the active taxiway",
            "Communicating with ground control on the mandatory frequency"
        ],
        "answerIndex": 0,
        "rationale": "CARs 301.08(e) prohibits persons from knowingly removing, defacing, extinguishing or interfering with a marker, marking, light or signal used at an aerodrome for air navigation purposes, except with permission from the aerodrome operator and, where applicable, the appropriate air traffic services unit. This protects essential navigation aids.",
        "source": "CARs 301.08(e) + TP 15263 Section 7",
        "carsSection": "301.08"
    },
    
    # AERODROME SAFETY (Fire Prevention)
    {
        "id": "aero-adv-008",
        "category": "aerodromes",
        "difficulty": "medium",
        "question": "Where is smoking or the display of an open flame prohibited at an aerodrome according to CARs 301.09?",
        "choices": [
            "On an apron, on aircraft loading bridges, or in areas where it could create a fire hazard",
            "Only on the active runway",
            "In hangars and maintenance areas only",
            "Smoking is permitted anywhere on the aerodrome except near fuel trucks"
        ],
        "answerIndex": 0,
        "rationale": "CARs 301.09(1) prohibits smoking or display of an open flame: (a) on an apron, (b) on aircraft loading bridges or galleries overhanging an apron, or (c) in any area where it could create a fire hazard. The aerodrome operator may authorize exceptions for maintenance operations under specific safe conditions.",
        "source": "CARs 301.09 + TP 15263 Section 7",
        "carsSection": "301.09"
    },
    {
        "id": "aero-adv-009",
        "category": "aerodromes",
        "difficulty": "medium",
        "question": "Under what conditions may the operator of an aerodrome authorize maintenance or servicing operations involving open flame or spark on an apron?",
        "choices": [
            "When the operations are conducted in a manner not likely to create a fire hazard that could endanger persons or property",
            "Never - open flame and spark are always prohibited on aprons",
            "Only during daylight hours with at least one fire extinguisher present",
            "Only with approval from the local fire department"
        ],
        "answerIndex": 0,
        "rationale": "CARs 301.09(2) allows the aerodrome operator to, in writing, authorize maintenance or servicing operations on an apron that involve use or development of open flame or spark IF they are conducted in a manner that is not likely to create a fire hazard endangering persons or property. Special authorization is required.",
        "source": "CARs 301.09(2) + TP 15263 Section 7",
        "carsSection": "301.09"
    },
    
    # RADIO COMMUNICATION FAILURE (CARs 602.136-602.138)
    {
        "id": "radio-adv-001",
        "category": "radio",
        "difficulty": "hard",
        "question": "When operating a VFR aircraft in Class B, C, or D airspace and experiencing a two-way radio communication failure, what action must the pilot-in-command take first?",
        "choices": [
            "Leave the airspace by landing at the control zone aerodrome or by the shortest route",
            "Squawk 7600 on the transponder and continue flight",
            "Return to the departure aerodrome immediately",
            "Descend to 1,000 feet AGL and continue the flight"
        ],
        "answerIndex": 0,
        "rationale": "CARs 602.138(a) requires that in the event of two-way radio communication failure while operating in Class B, C, or D airspace, the pilot-in-command must leave the airspace by either landing at the control zone aerodrome OR by the shortest route. The transponder must be set to code 7600.",
        "source": "CARs 602.138 + AIM RPA Section 3.2",
        "carsSection": "602.138"
    },
    {
        "id": "radio-adv-002",
        "category": "radio",
        "difficulty": "hard",
        "question": "In a two-way radio communication failure during VFR flight in Class B, C, or D airspace, what transponder code must be set?",
        "choices": [
            "7600",
            "7500",
            "1200",
            "7700"
        ],
        "answerIndex": 0,
        "rationale": "CARs 602.138(b) specifies that when there is a two-way radio communication failure, the pilot-in-command must set the transponder to code 7600. This code alerts ATC to the communication failure and aids in tracking the aircraft's position.",
        "source": "CARs 602.138(b) + AIM RPA Section 3.2",
        "carsSection": "602.138"
    },
    {
        "id": "radio-adv-003",
        "category": "radio",
        "difficulty": "hard",
        "question": "When experiencing a two-way radio communication failure between an IFR aircraft and the controlling ATC unit, what should the pilot-in-command do regarding the transponder?",
        "choices": [
            "Set the transponder to code 7600 to alert ATC of the communication failure",
            "Set the transponder to 1200 and attempt to land at the nearest airport",
            "Turn off the transponder to prevent false signals",
            "Continue squawking the assigned code and attempt visual signaling"
        ],
        "answerIndex": 0,
        "rationale": "CARs 602.137(1) requires that in the event of a two-way radio communication failure in IFR flight, the pilot-in-command must set the transponder to code 7600, maintain listening watch for control messages, and attempt to establish communications through any available means.",
        "source": "CARs 602.137(1) + AIM RPA Section 3.2",
        "carsSection": "602.137"
    },
    {
        "id": "radio-adv-004",
        "category": "radio",
        "difficulty": "hard",
        "question": "What procedures must an IFR pilot follow if unable to establish radio communications with any air traffic services facility after a communication failure?",
        "choices": [
            "Comply with procedures specified by the Minister in the Canada Air Pilot and Canada Flight Supplement, unless specific instructions for anticipated failure were previously received",
            "Return to the departure airport immediately under VFR rules",
            "Declare an emergency on all frequencies",
            "Continue on the assigned clearance indefinitely until reaching destination"
        ],
        "answerIndex": 0,
        "rationale": "CARs 602.137(2) states that if communications cannot be established with any air traffic services facility (directly or by relay), the pilot-in-command must comply with procedures specified by the Minister in the Canada Air Pilot and Canada Flight Supplement, except where specific instructions for an anticipated communications failure were previously received from ATC.",
        "source": "CARs 602.137(2) + TP 15263 Section 5",
        "carsSection": "602.137"
    },
    
    # MANDATORY FREQUENCY (MF) PROCEDURES (CARs 602.97-602.103)
    {
        "id": "radio-adv-005",
        "category": "radio",
        "difficulty": "hard",
        "question": "In a Mandatory Frequency (MF) area at an uncontrolled aerodrome, the pilot-in-command of a VFR aircraft must maintain a listening watch on:",
        "choices": [
            "The mandatory frequency specified for use in the MF area",
            "The common frequency (126.7 MHz) for all MF areas in Canada",
            "The frequency of the nearest towered airport",
            "Any frequency that provides ground station contact"
        ],
        "answerIndex": 0,
        "rationale": "CARs 602.97(2) requires that the pilot-in-command of a VFR or IFR aircraft operating within an MF area must maintain a listening watch on the mandatory frequency specified for use in that particular MF area. Each MF area has a specific designated frequency.",
        "source": "CARs 602.97(2) + AIM RPA Section 3.3",
        "carsSection": "602.97"
    },
    {
        "id": "radio-adv-006",
        "category": "radio",
        "difficulty": "hard",
        "question": "Before entering the maneuvering area of an uncontrolled aerodrome within an MF area, the pilot-in-command must:",
        "choices": [
            "Report intentions on the mandatory frequency before entering the maneuvering area",
            "Request permission from the weather briefing office",
            "File a position report 10 minutes before arrival",
            "Obtain a departure clearance from the nearest ATC facility"
        ],
        "answerIndex": 0,
        "rationale": "CARs 602.99 requires that the pilot-in-command of a VFR or IFR aircraft at an uncontrolled aerodrome in an MF area must report the pilot-in-command's intentions before entering the maneuvering area of the aerodrome on the MF frequency.",
        "source": "CARs 602.99 + AIM RPA Section 3.3",
        "carsSection": "602.99"
    },
    {
        "id": "radio-adv-007",
        "category": "radio",
        "difficulty": "hard",
        "question": "What must a pilot-in-command report when joining the aerodrome traffic circuit at an uncontrolled MF area aerodrome?",
        "choices": [
            "Aircraft position in the circuit and intentions on the mandatory frequency",
            "Only the aircraft call sign and type",
            "Altitude and heading to the nearest hundred",
            "No report is required if a previous MF report was made"
        ],
        "answerIndex": 0,
        "rationale": "CARs 602.101(b) specifies that when joining the aerodrome traffic circuit at an uncontrolled aerodrome in an MF area, the pilot-in-command must report the aircraft's position in the circuit. Additional reports are required when on downwind leg, final approach, and when clear of the surface after landing.",
        "source": "CARs 602.101(b) + AIM RPA Section 3.3",
        "carsSection": "602.101"
    },
    {
        "id": "radio-adv-008",
        "category": "radio",
        "difficulty": "medium",
        "question": "How far in advance should a VFR aircraft pilot report entering an MF area when arriving at an uncontrolled aerodrome?",
        "choices": [
            "At least 5 minutes before entering the area, when circumstances permit",
            "Immediately upon entering the MF area boundary",
            "10 minutes before entering the area",
            "Only after landing at the aerodrome"
        ],
        "answerIndex": 0,
        "rationale": "CARs 602.101(a) requires that when arriving at an uncontrolled aerodrome in an MF area, the pilot-in-command must report before entering the MF area and, where circumstances permit, shall do so at least five minutes before entering the area, providing position, altitude, and estimated time of landing.",
        "source": "CARs 602.101(a) + AIM RPA Section 3.3",
        "carsSection": "602.101"
    },
    
    # FOREST FIRE OPERATIONS (CARs 601.15-601.17)
    {
        "id": "flight-adv-001",
        "category": "flight-planning",
        "difficulty": "hard",
        "question": "What is the minimum altitude required when operating an aircraft over a forest fire area or within 5 nautical miles of it?",
        "choices": [
            "3,000 feet AGL or above",
            "2,000 feet AGL or above",
            "1,500 feet AGL or above",
            "No minimum altitude over forest fires"
        ],
        "answerIndex": 0,
        "rationale": "CARs 601.15(a) states that no person shall operate an aircraft over a forest fire area or over any area within five nautical miles of a forest fire area at an altitude of less than 3,000 feet AGL. This is a mandatory restriction to ensure safety and not interfere with firefighting operations.",
        "source": "CARs 601.15(a) + TP 15263 Section 6",
        "carsSection": "601.15"
    },
    {
        "id": "flight-adv-002",
        "category": "flight-planning",
        "difficulty": "hard",
        "question": "Who may operate an aircraft in a forest fire area at an altitude below 3,000 feet AGL?",
        "choices": [
            "Persons authorized by a fire control authority for fire control operations, or persons with ministerial authorization",
            "Any licensed pilot with appropriate aircraft type rating",
            "Only Department of Transport personnel",
            "No one - the 3,000 ft AGL minimum is absolute"
        ],
        "answerIndex": 0,
        "rationale": "CARs 601.17(1) provides exceptions to the forest fire altitude restriction: (a) persons operating with authorization from an appropriate fire control authority for fire control assistance, (b) persons with written authorization from the Minister, or (c) Department of Transport personnel conducting surveillance or enforcement operations.",
        "source": "CARs 601.17(1) + TP 15263 Section 6",
        "carsSection": "601.17"
    },
    {
        "id": "flight-adv-003",
        "category": "flight-planning",
        "difficulty": "hard",
        "question": "If a pilot receives authorization from the Minister to operate in a forest fire area below 3,000 feet AGL, what document must be on board the aircraft?",
        "choices": [
            "A written authorization from the Minister specifying approved conditions",
            "A letter from the fire control authority",
            "A NOTAM confirming the fire location",
            "The pilot's certificate with a fire operations endorsement"
        ],
        "answerIndex": 0,
        "rationale": "CARs 601.17(4) states that no person shall operate an aircraft under ministerial authorization unless the authorization is on board and the aircraft is operated in accordance with any conditions specified in the authorization. The authorization must be carried and available for inspection.",
        "source": "CARs 601.17(4) + TP 15263 Section 6",
        "carsSection": "601.17"
    },
    {
        "id": "flight-adv-004",
        "category": "flight-planning",
        "difficulty": "medium",
        "question": "What document will inform pilots of airspace restrictions related to forest fire operations?",
        "choices": [
            "NOTAM (Notice to Airmen) issued by the Minister describing the forest fire area and restricted airspace",
            "Canada Flight Supplement entry for that aerodrome",
            "Flight Service Station briefing only",
            "Pilot must contact local fire control authority directly"
        ],
        "answerIndex": 0,
        "rationale": "CARs 601.16 states that the Minister may issue a NOTAM relating to restrictions on aircraft operation in case of forest fire that describes: (a) the location and dimensions of the forest fire area, and (b) the airspace in which forest fire control operations are being conducted. NOTAMs are the official means of communicating temporary flight restrictions.",
        "source": "CARs 601.16 + AIM RPA Section 4.2",
        "carsSection": "601.16"
    },
    
    # LASER/DIRECTED LIGHT RESTRICTIONS (CARs 601.20-601.22)
    {
        "id": "safety-adv-001",
        "category": "safety",
        "difficulty": "hard",
        "question": "What authorization is required before projecting a directed bright light source (such as a laser) into navigable airspace?",
        "choices": [
            "Written authorization from the Minister must be obtained before the projection",
            "Notification to the local airport is sufficient",
            "Only daylight operations are restricted",
            "The NOTAM must be issued by the airport operator"
        ],
        "answerIndex": 0,
        "rationale": "CARs 601.21(1) requires that any person planning to project a directed bright light source into navigable airspace must: (a) submit a written request to the Minister for authorization, and (b) obtain written authorization from the Minister before projection.",
        "source": "CARs 601.21(1) + TP 15263 Section 6",
        "carsSection": "601.21"
    },
    {
        "id": "safety-adv-002",
        "category": "safety",
        "difficulty": "hard",
        "question": "Under what condition will the Minister issue authorization for projecting a directed bright light source into navigable airspace?",
        "choices": [
            "If the projection is not likely to create a hazard to aviation safety or cause damage to an aircraft",
            "If the projection occurs only during daylight hours",
            "If the aerodrome operator provides written approval",
            "Authorization is never granted for laser projections in airspace"
        ],
        "answerIndex": 0,
        "rationale": "CARs 601.21(2) states that the Minister shall issue written authorization for the projection if the projection is not likely to create a hazard to aviation safety or cause damage to an aircraft or injury to persons on board. The Minister may also specify conditions to ensure safety in the authorization.",
        "source": "CARs 601.21(2) + TP 15263 Section 6",
        "carsSection": "601.21"
    },
    {
        "id": "safety-adv-003",
        "category": "safety",
        "difficulty": "medium",
        "question": "A pilot-in-command sees a laser beam or directed light projected into airspace ahead. According to CARs 601.22, what must be true to intentionally operate into this beam?",
        "choices": [
            "The pilot must have ministerial authorization to operate in the area where the laser is projected",
            "The pilot can enter any area with lasers if operating under IFR",
            "No authorization is needed if above 5,000 feet AGL",
            "The pilot should always avoid the area unless it's an emergency"
        ],
        "answerIndex": 0,
        "rationale": "CARs 601.22(1) states that no pilot-in-command shall intentionally operate an aircraft into a beam from a directed bright light source or into an area where such light is projected, unless the aircraft is operated in accordance with ministerial authorization. Such authorization may be granted if operation is not likely to create a hazard to aviation safety.",
        "source": "CARs 601.22(1) + TP 15263 Section 6",
        "carsSection": "601.22"
    },
    
    # ESCAT PLAN (CARs 602.146)
    {
        "id": "flight-adv-005",
        "category": "flight-planning",
        "difficulty": "hard",
        "question": "When the ESCAT Plan is implemented for an aircraft entering Canadian domestic airspace, what must the pilot-in-command do before taking off?",
        "choices": [
            "Obtain approval for the flight from the appropriate air traffic services unit",
            "File a detailed flight plan with the local FSS",
            "Notify the nearest military base",
            "Ensure the aircraft has a transponder capable of squawking 7600"
        ],
        "answerIndex": 0,
        "rationale": "CARs 602.146(2)(a) requires that when notified of the implementation of the ESCAT Plan, the pilot-in-command must obtain approval for the flight from the appropriate air traffic services unit before takeoff. This is a mandatory pre-flight requirement during emergency situations.",
        "source": "CARs 602.146(2)(a) + TP 15263 Section 5",
        "carsSection": "602.146"
    },
    {
        "id": "flight-adv-006",
        "category": "flight-planning",
        "difficulty": "hard",
        "question": "What position reporting requirements apply to an aircraft operating outside controlled airspace when ESCAT Plan is in effect?",
        "choices": [
            "Position reports at least every 30 minutes to the appropriate air traffic services unit",
            "Position reports only when requested by ATC",
            "No position reports required outside controlled airspace",
            "Position reports only at waypoints listed in the flight plan"
        ],
        "answerIndex": 0,
        "rationale": "CARs 602.146(2)(c)(ii) requires that when operating outside controlled airspace under ESCAT Plan, the pilot-in-command must provide position reports to ATC at least every 30 minutes. Inside controlled airspace, reporting follows normal IFR position reporting procedures.",
        "source": "CARs 602.146(2)(c) + TP 15263 Section 5",
        "carsSection": "602.146"
    },
    
    # WEAPONS AND WAR EQUIPMENT (CARs 606.01)
    {
        "id": "regulations-adv-001",
        "category": "regulations",
        "difficulty": "medium",
        "question": "Under what circumstances may weapons or ammunition be carried on board a Canadian aircraft?",
        "choices": [
            "Only when authorized in writing by the Minister",
            "Weapons are never permitted on Canadian aircraft",
            "Only for military aircraft conducting official operations",
            "Weapons may be carried by private pilots with appropriate licensing"
        ],
        "answerIndex": 0,
        "rationale": "CARs 606.01 prohibits any person from carrying weapons, ammunition, or other equipment designed for use in war on board an aircraft unless the aircraft is a Canadian aircraft AND the Minister has authorized the carriage of such equipment. Authorization must be explicitly granted.",
        "source": "CARs 606.01 + TP 15263 Section 6",
        "carsSection": "606.01"
    },
    {
        "id": "regulations-adv-002",
        "category": "regulations",
        "difficulty": "medium",
        "question": "What type of equipment designed for use in war requires ministerial authorization before being carried on a Canadian aircraft?",
        "choices": [
            "Weapons, ammunition, and other equipment designed for use in war",
            "Only weapons; ammunition requires no authorization",
            "Military communication equipment only",
            "Navigation and sensing systems used in military operations"
        ],
        "answerIndex": 0,
        "rationale": "CARs 606.01 specifically prohibits carrying 'weapons, ammunition or other equipment designed for use in war' on board an aircraft. This broad restriction covers all offensive or defensive military equipment and requires ministerial authorization for any such carriage.",
        "source": "CARs 606.01 + TP 15263 Section 6",
        "carsSection": "606.01"
    },
]

# Load existing questions
questions_path = Path("data/questions.json")
with open(questions_path, 'r', encoding='utf-8') as f:
    existing_data = json.load(f)

# Add new questions
existing_data['questions'].extend(new_questions_data)

# Update question count
existing_data['totalQuestions'] = len(existing_data['questions'])
existing_data['lastUpdated'] = datetime.now().isoformat()

# Save updated questions
with open(questions_path, 'w', encoding='utf-8') as f:
    json.dump(existing_data, f, indent=2, ensure_ascii=False)

print("=" * 100)
print("GENERATED NEW ADVANCED QUESTIONS - PHASE 5")
print("=" * 100)
print(f"\n✓ Added {len(new_questions_data)} new questions covering gap topics")
print(f"✓ Total questions now: {existing_data['totalQuestions']}")
print(f"✓ Updated: {existing_data['lastUpdated']}")

# Breakdown by topic
topic_breakdown = {
    "Aerodrome Operations & Safety": 3 + 2 + 2 + 1,  # aero-adv-001 through aero-adv-009
    "Radio Communication Failure": 4,  # radio-adv-001 through radio-adv-004
    "Mandatory Frequency Procedures": 4,  # radio-adv-005 through radio-adv-008
    "Forest Fire Operations": 4,  # flight-adv-001 through flight-adv-004
    "Laser/Directed Light Restrictions": 3,  # safety-adv-001 through safety-adv-003
    "ESCAT Plan": 2,  # flight-adv-005 through flight-adv-006
    "Weapons & Equipment": 2,  # regulations-adv-001 through regulations-adv-002
}

print("\n[NEW QUESTIONS BY TOPIC]")
print("-" * 100)
for topic, count in topic_breakdown.items():
    print(f"  {topic:40s} : {count:2d} new questions")

print("\n[QUESTIONS BY CATEGORY]")
print("-" * 100)
category_counts = {}
for q in new_questions_data:
    cat = q['category']
    category_counts[cat] = category_counts.get(cat, 0) + 1

for cat in sorted(category_counts.keys()):
    print(f"  {cat:20s} : {category_counts[cat]:2d} new questions")

print("\n" + "=" * 100)
