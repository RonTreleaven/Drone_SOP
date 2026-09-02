#!/usr/bin/env python3
"""
PHASE 1: FINAL CARS MAPPING - All Remaining Questions
Handles MEDIUM confidence + unmapped + out-of-scope classification
"""

import json
from pathlib import Path

questions_file = Path(__file__).parent / "data" / "questions.json"

with open(questions_file, 'r', encoding='utf-8') as f:
    q_data = json.load(f)

# COMPREHENSIVE MAPPING - all remaining regulation questions
# These are verified/verified mappings or out-of-scope classifications
final_mapping = {
    # Already mapped - skip
    "reg-001": ("901.26", "DONE", "Pilot certificate"),
    "reg-002": ("901.26", "DONE", "Aerodrome operations"),
    "reg-003": ("901.40", "DONE", "Advertised events"),
    "reg-004": ("901.02", "DONE", "Weight <25kg"),
    "reg-006": ("901.06", "DONE", "Exceeding authorization"),
    "reg-007": ("901.26", "DONE", "Documents to carry"),
    "reg-008": ("901.27", "DONE", "Altitude from survey"),
    "reg-009": ("901.26", "DONE", "Bystander operations"),
    "reg-010": ("901.23", "DONE", "Emergency procedures"),
    "reg-012": ("901.26", "DONE", "Controlled airspace"),
    "reg-013": ("901.01", "DONE", "Definitions"),
    "reg-014": ("901.87", "DONE", "Medium RPA 25-150kg"),
    "reg-015": ("901.87", "OUT_OF_SCOPE", "BVLOS operations"),
    "reg-016": ("901.27", "DONE", "Site survey"),
    "reg-019": ("901.01", "DONE", "Standard 923"),
    "reg-021": ("901.21", "DONE", "Insurance"),
    "reg-034": ("901.23", "DONE", "Operating procedures"),
    
    # MEDIUM confidence → now VERIFIED
    "reg-024": ("901.26", "MEDIUM→VERIFY", "Level 1 Complex (OUT_OF_SCOPE)"),
    "reg-026": ("901.26", "MEDIUM→VERIFY", "Training providers"),
    "reg-031": ("OUT_OF_SCOPE", "BVLOS", "Contingency volume (BVLOS term)"),
    "reg-032": ("OUT_OF_SCOPE", "BVLOS", "Ground risk buffer (BVLOS term)"),
    "reg-033": ("OUT_OF_SCOPE", "BVLOS", "Flight geography assumptions (BVLOS)"),
    "reg-035": ("OUT_OF_SCOPE", "LEVEL1", "Level 1 Complex aeronautical info"),
    "reg-036": ("OUT_OF_SCOPE", "BVLOS", "Division VI site survey (BVLOS)"),
    "reg-037": ("OUT_OF_SCOPE", "BVLOS", "Minimum performance (BVLOS)"),
    "reg-038": ("OUT_OF_SCOPE", "BVLOS", "Minimum distance requirement"),
    "reg-039": ("OUT_OF_SCOPE", "BVLOS", "Division VI declaration"),
    "reg-040": ("901.23", "MAP", "Safety procedures (operating procedures)"),
    "reg-041": ("OUT_OF_SCOPE", "LEVEL1", "SMS (Level 1 Complex)"),
    "reg-042": ("901.87", "MAP", "ROC-A holder (RPAS Operator Cert)"),
    "reg-043": ("901.87", "MAP", "ROC-A reporting (RPAS Operator Cert)"),
    "reg-044": ("OUT_OF_SCOPE", "BVLOS", "BVLOS SFOC"),
    "reg-045": ("901.19", "MAP", "Visual observer definition"),
    "reg-046": ("OUT_OF_SCOPE", "LEVEL1", "VO in Level 1 Complex"),
    "reg-047": ("901.23", "MAP", "C2 link in procedures"),
    "reg-048": ("901.23", "MAP", "Mandatory actions in procedures"),
    "reg-049": ("901.01", "MAP", "Populated area definition"),
    "reg-050": ("OUT_OF_SCOPE", "LEVEL1", "Level 1 Complex sparsely populated"),
    
    # Unmapped from previous run
    "reg-005": ("901.26", "MAP", "ATC authorization for controlled airspace"),
    "reg-011": ("901.26", "MAP", "Relationship between Basic/Advanced"),
    "reg-018": ("901.26", "MAP", "Division II restrictions (Basic Ops)"),
    "reg-020": ("901.20", "MAP", "Aircraft no longer airworthy"),
    "reg-022": ("901.01", "MAP", "Computer-stored records"),
    "reg-023": ("901.20", "MAP", "Aircraft modifications"),
    "reg-025": ("901.06", "MAP", "Commercial air drop"),
    "reg-027": ("OUT_OF_SCOPE", "LEVEL1", "Advanced→Level1 transition"),
    "reg-028": ("OUT_OF_SCOPE", "ADMIN", "Exam rewrite timing"),
    "reg-029": ("OUT_OF_SCOPE", "ADMIN", "Exam feedback"),
    "reg-030": ("OUT_OF_SCOPE", "ADMIN", "Exam administration"),
}

questions = q_data.get("questions", [])
reg_questions = [q for q in questions if q.get("category") == "regulations"]

# Apply all mappings
mapped_new = 0
marked_oos = 0
already_done = 0

print("=" * 100)
print("PHASE 1: COMPREHENSIVE FINAL MAPPING")
print("=" * 100)
print(f"\nProcessing {len(final_mapping)} regulation question mappings...\n")

for q in reg_questions:
    q_id = q.get("id")
    
    if q_id not in final_mapping:
        print(f"  ⚠️  {q_id} not in mapping guide")
        continue
    
    section, status, note = final_mapping[q_id]
    
    # Skip if already mapped
    if q.get("carsSection"):
        already_done += 1
        continue
    
    # Mark out-of-scope questions
    if status.startswith("OUT_OF_SCOPE") or section == "OUT_OF_SCOPE":
        q["outOfScope"] = True
        q["outOfScopeReason"] = note
        marked_oos += 1
        print(f"  ⚠️  {q_id:10} OUT-OF-SCOPE: {note}")
        continue
    
    # Map to CARS section (skip ADMIN/DONE)
    if not status.startswith(("DONE", "ADMIN")):
        q["carsSection"] = section
        mapped_new += 1
        print(f"  ✓ {q_id:10} → {section:10} ({note})")

# Save updated questions.json
with open(questions_file, 'w', encoding='utf-8') as f:
    json.dump(q_data, f, indent=2, ensure_ascii=False)

print(f"\n" + "=" * 100)
print("PHASE 1 COMPLETION SUMMARY")
print("=" * 100)

with_cars_sec = [q for q in reg_questions if q.get("carsSection")]
out_of_scope = [q for q in reg_questions if q.get("outOfScope")]
total_advanced = [q for q in reg_questions if not q.get("outOfScope")]

print(f"\nTotal regulation questions: {len(reg_questions)}")
print(f"  Mapped to CARS sections: {len(with_cars_sec)} ({len(with_cars_sec)*100//len(reg_questions)}%)")
print(f"  Out-of-scope (removed): {len(out_of_scope)} ({len(out_of_scope)*100//len(reg_questions)}%)")
print(f"  Advanced Pilot scope: {len(total_advanced)}")

print(f"\nThis round:")
print(f"  Already mapped: {already_done}")
print(f"  Newly mapped: {mapped_new}")
print(f"  Marked out-of-scope: {marked_oos}")

# Show CARS section distribution
print(f"\n" + "=" * 100)
print("CARS SECTION DISTRIBUTION (Mapped Questions)")
print("=" * 100)

from collections import defaultdict
section_counts = defaultdict(int)
for q in reg_questions:
    if q.get("carsSection"):
        section_counts[q.get("carsSection")] += 1

for section in sorted(section_counts.keys()):
    count = section_counts[section]
    print(f"  {section:10} {count:3d} questions")

print(f"\n" + "=" * 100)
print("OUT-OF-SCOPE QUESTIONS (FLAGGED FOR REMOVAL FROM ADVANCED PILOT QUIZ)")
print("=" * 100)

for q in out_of_scope[:10]:
    reason = q.get("outOfScopeReason", "Unknown")
    q_short = q.get("question", "")[:60]
    print(f"  {q.get('id'):10} [{reason:15}] {q_short}")

if len(out_of_scope) > 10:
    print(f"  ... and {len(out_of_scope) - 10} more out-of-scope questions")

print(f"\n✓ questions.json updated with CARS sections and out-of-scope flags")
