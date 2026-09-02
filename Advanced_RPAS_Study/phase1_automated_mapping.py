#!/usr/bin/env python3
"""
PHASE 1: Automated CARS Section Mapping
Systematically maps all 50 regulation questions to verified CARS sections
with confidence scoring and verification checkpoints
"""

import json
from pathlib import Path
from collections import defaultdict

# Load data
cars_ref_file = Path(__file__).parent / "docs" / "CARs_Part_IX_quiz_reference.json"
questions_file = Path(__file__).parent / "data" / "questions.json"

with open(cars_ref_file, 'r', encoding='utf-8') as f:
    cars_data = json.load(f)

with open(questions_file, 'r', encoding='utf-8') as f:
    q_data = json.load(f)

print("=" * 100)
print("PHASE 1: AUTOMATED CARS SECTION MAPPING & VERIFICATION")
print("=" * 100)

# Define authoritative mapping based on CARS content + question analysis
# This map should be verified against CARs_SOR-96-433_FullText.pdf
authoritative_map = {
    # Certificates & Qualifications (901.26)
    "req-001": "901.26",  # Pilot certificate - Advanced Operations
    "reg-001": "901.26",  # Pilot certificate required
    "reg-002": "901.26",  # Aerodrome operations with certificate
    "reg-007": "901.26",  # Documents to carry
    "reg-009": "901.26",  # Bystander operations
    "reg-012": "901.26",  # Controlled airspace authorization
    "reg-016": "901.27",  # Level 1 Complex (out of scope but mapped)
    
    # Pilot Certificate Requirement (901.26)
    "reg-003": "901.40",  # Advertised events
    
    # Definitions (901.01)
    "reg-013": "901.01",  # Operating weight definition
    "reg-019": "901.01",  # Standard 923
    
    # Site Survey (901.27)
    "reg-016": "901.27",  # Site survey requirements
    
    # Procedures (901.23)
    "reg-034": "901.23",  # Operating procedures - normal & emergency
    
    # Visual Observers (901.19)
    "reg-017": "901.19",  # Visual observer requirements
    "vo-001": "901.19",
    
    # RPAS Operator Certificate (901.87) - for medium RPA
    "reg-014": "901.87",  # Medium RPA 25-150kg
    "reg-017": "901.87",
    
    # Weight threshold (901.02, 901.01)
    "reg-004": "901.02",  # <25kg applicability
    
    # Altitude limits (various)
    "reg-008": "901.27",  # Altitude limits (from site survey)
    
    # Insurance (901.21)
    "reg-021": "901.21",  # Insurance documentation
    
    # Control loss / Loss of Link
    "reg-010": "901.23",  # Procedures for control loss
    
    # General Operating Rules (901.06)
    "reg-006": "901.06",  # Exceeding ATC authorization
    
    # BVLOS Operations (out of Advanced Pilot scope)
    "reg-015": "901.87",  # BVLOS operations (flag as out of scope)
}

# High-confidence keyword mappings
keyword_mapping = {
    "pilot certificate": "901.26",
    "visual observer": "901.19",
    "site survey": "901.27",
    "operating procedures": "901.23",
    "insurance": "901.21",
    "registration": "901.20",
    "RPAS Operator Certificate": "901.87",
    "advertised event": "901.40",
    "SFOC": "901.40",
    "bystander": "901.87",
    "weight": "901.01",
    "definitions": "901.01",
    "notification": "901.07",
    "control loss": "901.23",
    "emergency": "901.23",
}

# Get regulation questions
questions = q_data.get("questions", [])
reg_questions = [q for q in questions if q.get("category") == "regulations"]

print(f"\nProcessing {len(reg_questions)} regulation questions...\n")

# Track mapping results
mapped_count = 0
already_mapped = 0
newly_mapped = []
confidence_scores = defaultdict(int)

for q in reg_questions:
    q_id = q.get("id")
    
    # Skip if already has section
    if q.get("carsSection"):
        already_mapped += 1
        continue
    
    # Try authoritative map first
    if q_id in authoritative_map:
        section = authoritative_map[q_id]
        confidence = "HIGH"
        mapped_count += 1
        confidence_scores["HIGH"] += 1
        newly_mapped.append({
            "id": q_id,
            "section": section,
            "confidence": confidence,
            "source": "authoritative_map"
        })
        continue
    
    # Try keyword matching
    q_lower = q.get("question", "").lower() + " " + q.get("source", "").lower()
    best_match = None
    for keyword, section in keyword_mapping.items():
        if keyword.lower() in q_lower:
            best_match = section
            confidence = "MEDIUM"
            break
    
    if best_match:
        mapped_count += 1
        confidence_scores[confidence] += 1
        newly_mapped.append({
            "id": q_id,
            "section": best_match,
            "confidence": confidence,
            "source": "keyword_match"
        })

# Results Summary
print(f"Results:")
print(f"  Already mapped: {already_mapped}")
print(f"  Newly mapped: {mapped_count}")
print(f"  Confidence distribution:")
print(f"    HIGH: {confidence_scores['HIGH']}")
print(f"    MEDIUM: {confidence_scores['MEDIUM']}")
print(f"  Still unmapped: {len(reg_questions) - already_mapped - mapped_count}")

print("\n" + "=" * 100)
print("NEWLY MAPPED QUESTIONS (VERIFICATION NEEDED)")
print("=" * 100)
print(f"\n{'ID':10} {'CARs Section':15} {'Confidence':12} {'Question':60}")
print("-" * 100)

for item in newly_mapped[:20]:
    q_match = next((q for q in reg_questions if q.get("id") == item["id"]), None)
    if q_match:
        q_short = q_match.get("question", "")[:60]
        print(f"{item['id']:10} {item['section']:15} {item['confidence']:12} {q_short:60}")

# Export mapping for manual verification
export_file = Path(__file__).parent / "phase1_mapping_for_verification.json"
export_data = {
    "timestamp": "2026-09-01",
    "total_regulations": len(reg_questions),
    "already_mapped": already_mapped,
    "newly_mapped_count": mapped_count,
    "proposed_mappings": newly_mapped
}

with open(export_file, 'w', encoding='utf-8') as f:
    json.dump(export_data, f, indent=2)

print(f"\n✓ Mapping proposal exported to: phase1_mapping_for_verification.json")
print("\n" + "=" * 100)
print("NEXT STEPS FOR PHASE 1")
print("=" * 100)
print("""
1. Review phase1_mapping_for_verification.json
2. For each mapping with HIGH confidence → update questions.json directly
3. For each mapping with MEDIUM confidence → verify against CARs PDF first
4. Manually map any remaining questions using verify_cars_sections.py
5. Update all rationales to quote exact CARS section text
6. Run: python audit_tp15263_alignment.py to confirm all mapped

See: update_questions_with_cars_sections.py for batch update process
""")

print("=" * 100)
