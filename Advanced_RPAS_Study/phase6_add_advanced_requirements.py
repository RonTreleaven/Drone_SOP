#!/usr/bin/env python3
"""Add Phase 6 questions for specific Advanced Operations knowledge requirements."""

import json
from datetime import date
from pathlib import Path


QUESTIONS = [
    {
        "id": "adv6-001",
        "category": "regulations",
        "difficulty": "hard",
        "question": "An applicant completed the Advanced Operations examination 13 months ago and has not completed a flight review. Can the Minister issue an Advanced Operations pilot certificate on that application?",
        "choices": [
            "Yes, passing the examination is the only requirement.",
            "No. The applicant must have successfully completed the flight review within the 12 months before applying.",
            "Yes, provided the applicant has flown at least once in the last 24 months.",
            "No. A flight review must be repeated every 30 days before applying."
        ],
        "answerIndex": 1,
        "rationale": "CARs 901.64(c) requires successful completion of a Standard 921 flight review within the 12 months before the application date. A 13-month-old review does not meet that issuance condition.",
        "source": "CARs 901.64(c); TP 15263, Section 1 - Canadian Aviation Regulations",
        "carsSection": "901.64",
        "lastVerified": "2026-09-01"
    },
    {
        "id": "adv6-002",
        "category": "regulations",
        "difficulty": "medium",
        "question": "Which activity can satisfy the 24-month recency requirement for an Advanced Operations pilot?",
        "choices": [
            "Completing any examination listed in CARs 901.65(1)(b)(i), an eligible flight review, or recurrent training in Standard 921.04.",
            "Making a single recreational flight with any micro-RPA.",
            "Renewing an RPAS registration certificate.",
            "Reading the manufacturer manual annually."
        ],
        "answerIndex": 0,
        "rationale": "CARs 901.65(1)(b) recognizes specified examinations, flight reviews, and recurrent training activities. CARs 901.65(2) also requires a record of the qualifying activity and date to be retained for at least 24 months.",
        "source": "CARs 901.65(1)(b) and 901.65(2); TP 15263, Section 1 - Canadian Aviation Regulations",
        "carsSection": "901.65",
        "lastVerified": "2026-09-01"
    },
    {
        "id": "adv6-003",
        "category": "regulations",
        "difficulty": "easy",
        "question": "During an Advanced Operations flight, what two documents must be easily accessible to the pilot?",
        "choices": [
            "The pilot certificate and documentation showing the pilot meets recency requirements.",
            "The RPAS purchase receipt and insurance policy only.",
            "A paper copy of every applicable CARs Part.",
            "The manufacturer's marketing brochure and battery warranty."
        ],
        "answerIndex": 0,
        "rationale": "CARs 901.66 requires the applicable Advanced or Level 1 Complex pilot certificate and documentation demonstrating compliance with the recency requirement in CARs 901.65 to be easily accessible during the operation.",
        "source": "CARs 901.66(a)-(b); TP 15263, Section 1 - Canadian Aviation Regulations",
        "carsSection": "901.66",
        "lastVerified": "2026-09-01"
    },
    {
        "id": "adv6-004",
        "category": "aircraft-systems",
        "difficulty": "hard",
        "question": "A pilot plans a small-RPA VLOS operation in controlled airspace. What aircraft-side regulatory condition applies before the operation?",
        "choices": [
            "A declaration to the Minister must cover that RPAS model and each applicable Standard 922 technical requirement.",
            "The pilot may use any registered small RPA because the Advanced certificate alone is sufficient.",
            "A declaration is only required for flights above 400 ft AGL.",
            "Only a verbal statement from the manufacturer is required."
        ],
        "answerIndex": 0,
        "rationale": "CARs 901.69(a) prohibits a small-RPA VLOS operation in controlled airspace unless a declaration has been made for that model and for each Standard 922 technical requirement applicable to the operation.",
        "source": "CARs 901.69(a); Standard 922 - RPAS Safety Assurance; TC AIM RPA chapter - Controlled airspace operations",
        "carsSection": "901.69",
        "lastVerified": "2026-09-01"
    },
    {
        "id": "adv6-005",
        "category": "aircraft-systems",
        "difficulty": "hard",
        "question": "After modifying a declared RPA, a pilot wants to use it for an operation listed in CARs 901.69. What must the pilot be able to demonstrate to the Minister?",
        "choices": [
            "That the modified system continues to meet the applicable Standard 922 technical requirements.",
            "That the modification reduced the RPA's weight.",
            "That the modification was completed more than 30 days before flight.",
            "That the pilot has flown the original RPA model for at least 10 hours."
        ],
        "answerIndex": 0,
        "rationale": "Under CARs 901.70(1)(a), a modified RPAS used for an operation described in 901.69 must still meet the applicable Standard 922 technical requirements. CARs 901.70(1)(b) also requires applicable modification instructions to be followed.",
        "source": "CARs 901.70(1)(a)-(b); Standard 922 - RPAS Safety Assurance",
        "carsSection": "901.70",
        "lastVerified": "2026-09-01"
    },
    {
        "id": "adv6-006",
        "category": "airspace",
        "difficulty": "hard",
        "question": "When requested by the air traffic services provider for a proposed Advanced RPAS flight in controlled airspace, which information must the pilot provide?",
        "choices": [
            "The operation's date, time and duration; aircraft details; vertical and horizontal boundaries; pilot details; lost-link and emergency procedures; and termination process/time.",
            "Only the pilot's certificate number and home address.",
            "Only the desired altitude and a copy of the weather forecast.",
            "Only the RPAS registration number."
        ],
        "answerIndex": 0,
        "rationale": "CARs 901.71(1)(a)-(k) specifies the information that must be provided if requested by the ATS provider, including operating-area boundaries, lost command-and-control link procedures, emergency procedures, and termination process/time.",
        "source": "CARs 901.71(1)(a)-(k); TC AIM RPA chapter - Controlled airspace operations",
        "carsSection": "901.71",
        "lastVerified": "2026-09-01"
    },
    {
        "id": "adv6-007",
        "category": "airspace",
        "difficulty": "medium",
        "question": "An Advanced RPAS authorization permits controlled-airspace flight, but the pilot cannot readily produce it during the operation. Is that compliant?",
        "choices": [
            "No. The authorization must be easily accessible to the pilot during the operation.",
            "Yes. The authorization only needs to be available after landing.",
            "Yes, if the RPAS remains below 400 ft AGL.",
            "No. The authorization must be carried only by a visual observer."
        ],
        "answerIndex": 0,
        "rationale": "CARs 901.71(3) requires the authorization for controlled-airspace operation to be easily accessible to the pilot throughout the operation.",
        "source": "CARs 901.71(3); TC AIM RPA chapter - Controlled airspace operations",
        "carsSection": "901.71",
        "lastVerified": "2026-09-01"
    },
    {
        "id": "adv6-008",
        "category": "airspace",
        "difficulty": "medium",
        "question": "ATC issues an instruction directly to an RPAS pilot operating in controlled airspace under Division V. What is the pilot's obligation?",
        "choices": [
            "Comply with the instruction.",
            "Comply only if the instruction was included in the original authorization.",
            "Treat the instruction as advisory because the aircraft is remotely piloted.",
            "Wait for the RPAS manufacturer to approve the instruction."
        ],
        "answerIndex": 0,
        "rationale": "CARs 901.72 requires a pilot operating a remotely piloted aircraft in controlled airspace under Division V to comply with all ATC instructions directed at that pilot.",
        "source": "CARs 901.72; TC AIM RPA chapter - Air traffic services and controlled airspace",
        "carsSection": "901.72",
        "lastVerified": "2026-09-01"
    },
    {
        "id": "adv6-009",
        "category": "aerodromes",
        "difficulty": "hard",
        "question": "An Advanced VLOS operation is planned 2 NM from an airport centre. Which condition permits the operation under Division V?",
        "choices": [
            "It is conducted in accordance with the established RPAS safe-use procedure applicable to that airport.",
            "The pilot announces the flight on social media before launch.",
            "The RPA remains below 100 ft AGL.",
            "The pilot has logged at least 24 months of flight time."
        ],
        "answerIndex": 0,
        "rationale": "CARs 901.73 prohibits a Division V operation less than 3 NM from an airport centre, or less than 1 NM from a heliport centre, unless it follows the established RPAS safe-use procedure applicable to that airport or heliport.",
        "source": "CARs 901.73; TC AIM RPA chapter - Operations near airports and heliports",
        "carsSection": "901.73",
        "lastVerified": "2026-09-01"
    },
    {
        "id": "adv6-010",
        "category": "visual-observers",
        "difficulty": "hard",
        "question": "Which condition is required for an extended VLOS operation under CARs 901.74?",
        "choices": [
            "The RPA must remain no more than 2 NM from the pilot, control station, and visual observer at all times.",
            "The RPA may be any distance from the visual observer if it has a camera.",
            "The pilot may operate from a moving vehicle during launch and recovery.",
            "The operation may be conducted directly over uninvolved persons if it remains below 400 ft AGL."
        ],
        "answerIndex": 0,
        "rationale": "CARs 901.74(1)(b) limits the RPA to no more than 2 NM from the pilot, control station, and visual observer. Sections 901.74(1)(a) and (c) also set location and 30 m separation conditions.",
        "source": "CARs 901.74(1)(a)-(c); TP 15263, Section 6 - Flight operations",
        "carsSection": "901.74",
        "lastVerified": "2026-09-01"
    },
    {
        "id": "adv6-011",
        "category": "visual-observers",
        "difficulty": "hard",
        "question": "For an extended VLOS operation, what must the visual observer maintain unaided visual contact with?",
        "choices": [
            "The airspace in which the RPA operates, sufficiently to detect conflicting traffic and other hazards and take avoidance action.",
            "Only the RPA's video feed.",
            "Only the pilot at the control station.",
            "Only the RPA during takeoff and landing."
        ],
        "answerIndex": 0,
        "rationale": "CARs 901.74(2) requires a visual observer in an extended VLOS operation to maintain unaided visual contact with the operating airspace sufficient to detect conflicting air traffic and other hazards and take action to avoid them.",
        "source": "CARs 901.74(2); TP 15263, Section 6 - Visual observers",
        "carsSection": "901.74",
        "lastVerified": "2026-09-01"
    },
    {
        "id": "adv6-012",
        "category": "visual-observers",
        "difficulty": "medium",
        "question": "Which qualification is acceptable for a visual observer supporting an extended VLOS operation under Division V?",
        "choices": [
            "A Basic, Advanced, or Level 1 Complex RPAS pilot certificate, provided the other visual-observer conditions are met.",
            "No qualification is needed if the observer has a smartphone.",
            "Only an Advanced Operations pilot certificate is acceptable.",
            "Only a manned-aircraft commercial pilot licence is acceptable."
        ],
        "answerIndex": 0,
        "rationale": "CARs 901.75(a) accepts a Basic, Advanced, or Level 1 Complex RPAS pilot certificate. The observer must also maintain the required unaided visual contact and stay within 2 NM of the RPA under CARs 901.75(b)-(c).",
        "source": "CARs 901.75(a)-(c); TP 15263, Section 6 - Visual observers",
        "carsSection": "901.75",
        "lastVerified": "2026-09-01"
    },
    {
        "id": "adv6-013",
        "category": "airspace",
        "difficulty": "hard",
        "question": "An RPAS becomes uncontrolled and inadvertently enters, or is likely to enter, Class F Special Use Restricted airspace. What must occur immediately?",
        "choices": [
            "Notify the appropriate ATS unit or user agency.",
            "Wait until the RPAS lands, then include it in the flight log.",
            "Notify only the RPAS manufacturer.",
            "Continue monitoring; notification is only required after a collision."
        ],
        "answerIndex": 0,
        "rationale": "CARs 900.07 requires immediate notification of the appropriate ATS unit or user agency when an uncontrolled RPA inadvertently enters, or is likely to enter, Class F Special Use Restricted airspace. The DAH identifies the affected areas and responsible agencies.",
        "source": "CARs 900.07; CARs 601.04(2); NAV CANADA Designated Airspace Handbook, Class F Special Use Airspace",
        "carsSection": "900.07",
        "lastVerified": "2026-09-01"
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
data["migrationNotes"].append(
    "2026-09-01 PHASE 6: Added 13 Advanced Operations questions aligned to CARs 900.07 and 901.64-901.75, with TP 15263, TC AIM RPA, and DAH references."
)
path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

print(f"Added {len(QUESTIONS)} Phase 6 questions. Total: {data['totalQuestions']}")