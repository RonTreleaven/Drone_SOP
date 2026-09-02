# Advanced RPAS Question Bank Audit Report
**Date:** 2026-09-01
**Audit Scope:** Basic/Advanced Pilot only (excluding Level 1 Complex, BVLOS)
**Question Bank:** 540 questions across 14 categories

---

## 📊 AUDIT SUMMARY

### Current Status
✅ **Complete:** All questions have sources and timestamps
⚠️ **Critical Issue:** Only 8 questions have verified CARs section numbers (901.xx)
⚠️ **Coverage Gap:** Navigation (25 vs 77 needed), Flight Ops (25 vs 77), Radio (20 vs 77)
🆕 **New:** TP 15263 requirements extracted; RPAS 101 ready for integration

---

## 🔴 PHASE 1: REGULATORY ACCURACY (HIGHEST PRIORITY)

### The Problem
- **50 regulation questions exist**
- **Only 3 have specific CARS section numbers** (901.xx)
- **47 questions cite CARs vaguely** ("CARs Part IX – aerodrome proximity operating rules")

### Why This Matters
- Wrong/vague citations → students cannot verify answers
- Exam questions must reference exact regulatory text
- Paraphrased rationales don't hold up under scrutiny

### What Needs to Be Done
Map each of the 50 regulation questions to its **primary CARS section**, verified against:
- `CARs_SOR-96-433_FullText.xml` (extracted provisions)
- `CARs_SOR-96-433_FullText.pdf` (full text)
- Official Justice Laws website: https://laws-lois.justice.gc.ca/eng/regulations/SOR-96-433/

### Tool to Help
**Script:** `verify_cars_sections.py` (already created)
- Suggests section candidates based on question keywords
- Shows first 20 unmapped questions with candidates
- Output: Use candidates as starting point, verify against actual CARs text

### Sample Candidates (from script output)
```
reg-001 → 901.26 (pilot certificate requirement)
reg-002 → 901.26 (operating near aerodromes)
reg-005 → 901.07 (airspace authorization)
reg-012 → 901.07, 901.26 (Class F airspace + certificates)
reg-013 → 901.01 (definitions like "operating weight")
```

### Template for Updates
```json
{
  "id": "reg-001",
  "carsSection": "901.26",
  "source": "CARs Section 901.26 – Pilot Certificate Requirements",
  "rationale": "CARs Section 901.26 requires the Pilot Certificate – Small RPAS (Advanced Operations) for Advanced RPAS operations. [Direct quote from section]"
}
```

---

## 🟡 PHASE 2: TP 15263 COVERAGE GAPS

### The Problem
TP 15263 (official exam blueprint) has 7 knowledge domains, but coverage is uneven:

| Section | Topic | Current | Target | Gap |
|---------|-------|---------|--------|-----|
| 2 | RPA Airframes/Systems | 50 | 77 | -27 |
| 3 | Human Factors | 40 | 77 | -37 |
| 4 | Meteorology | 50 | 77 | -27 |
| **5** | **Navigation** | **25** | **77** | **-52** ⚠️ |
| **6** | **Flight Operations** | **25** | **77** | **-52** ⚠️ |
| 7 | Theory of Flight | 50 | 77 | -27 |
| **8** | **Radiotelephony** | **20** | **77** | **-57** ⚠️ |

### Why This Matters
- Navigation + Flight Operations + Radio = 161 questions short of exam blueprint
- Students won't be prepared for all exam question types
- These are HIGH-WEIGHT topics on the actual exam

### What Needs to Be Done
1. **Create ~52 new Navigation questions** covering:
   - Coordinate systems (latitude, longitude, variation)
   - Charts and map interpretation
   - Flight planning calculations
   - GNSS/GPS fundamentals
   
2. **Create ~52 new Flight Operations questions** covering:
   - Pilot responsibilities and decision-making
   - Aircraft performance and limitations
   - Weight & balance
   - Site survey requirements (CARs 901.27)
   - VLOS vs Extended VLOS operations
   
3. **Create ~57 new Radiotelephony questions** covering:
   - Radio procedures and phraseology
   - Common frequencies
   - Emergency communications
   - Crew resource management

### Resources to Use
- TP 15263 extracted JSON: `knowledge_requirements_extracted.json` (132 specific learning areas)
- RPAS 101 Study Guide: `Nov-27-RPAS-101_EN-Final.pdf` (explanations, examples)
- AIM RPA Chapter: `aim-2026-1_rpa_en_March_19_2026.pdf` (official procedures)
- NAV CANADA Phraseology: `NAVCANADA_VFR-Phraseology.pdf` (radio references)

---

## 🟡 PHASE 3: SOURCE INTEGRATION

### The Problem
- 0 questions reference RPAS 101 (just integrated)
- Many questions lack specific document citations
- Rationales are paraphrased, not sourced

### What Needs to Be Done
Enhance 50-100 existing questions with multi-source citations:

**Before:**
```json
"source": "CARs Part IX – operating procedures"
```

**After:**
```json
"source": "CARs Section 901.23(1) – Establishment of Operating Procedures + TP 15263 Section 6.1 + RPAS 101 Chapter 3"
```

### Where Each Source Applies
| Document | Best For |
|----------|----------|
| TP 15263 | Learning objectives, study framework |
| RPAS 101 | Conceptual understanding, explanations |
| CARs | Legal requirements, specific regulations |
| AIM | Operational procedures, airspace rules |
| NAV CANADA DAH | NOTAM/airspace questions |
| NAVCANADA Phraseology | Radio/communications questions |

---

## 🟢 PHASE 4: VALIDATION & CLEANUP

### Quality Checks to Perform
- [ ] No questions require Level 1 Complex operations (scope creep)
- [ ] No questions are BVLOS-specific (out of Advanced Pilot scope)
- [ ] All rationales cite authoritative sources (no AI paraphrase without backup)
- [ ] No duplicate questions across categories
- [ ] Difficulty distribution is reasonable (easy ~35%, medium ~33%, hard ~30%, tricky ~2%)

### Success Criteria
- ✅ 100% of regulation questions have `carsSection` field
- ✅ ≥77 questions per TP 15263 domain (all 7 sections)
- ✅ All sources are specific (not generic "CARs Part IX")
- ✅ Zero out-of-scope questions
- ✅ RPAS 101 + AIM referenced where applicable

---

## 📋 TOOLS CREATED

| Tool | Purpose | Status |
|------|---------|--------|
| `audit_questions.py` | Baseline distribution analysis | ✅ Ready |
| `audit_tp15263_alignment.py` | TP 15263 gap detection | ✅ Ready |
| `verify_cars_sections.py` | CARS section keyword matching | ✅ Ready |
| (TBD) `gap_filler_generator.py` | Auto-suggest new questions | Needed |
| (TBD) `final_validation.py` | Pre-release quality check | Needed |

### How to Use Existing Tools
```bash
# Baseline audit
python audit_questions.py

# TP 15263 alignment
python audit_tp15263_alignment.py

# CARS section mapping help
python verify_cars_sections.py
```

---

## 📚 GOLD-SOURCE DOCUMENTS (All in `/docs`)

| Document | Type | Key Use |
|----------|------|---------|
| `TP15263_E_Knowledge-Requirements-Basic-Advanced.pdf` | 📋 Blueprint | Knowledge domains & structure |
| `Nov-27-RPAS-101_EN-Final.pdf` | 📖 Study Guide | Conceptual explanations |
| `CARs_SOR-96-433_FullText.xml` | 📄 Structured | Section number extraction |
| `CARs_SOR-96-433_FullText.pdf` | 📄 Full Text | Legal reference & verification |
| `aim-2026-1_rpa_en_March_19_2026.pdf` | 📖 AIM Chapter | Operational procedures |
| `NAVCANADA_DAH_current_20260709.pdf` | 📍 Airspace Index | NOTAM/airspace context |
| `NAVCANADA_VFR-Phraseology.pdf` | 📢 Radio Guide | Radiotelephony reference |
| `knowledge_requirements_extracted.json` | 📊 Structured Data | Programmatic analysis |

---

## 🎯 RECOMMENDED NEXT STEPS

### Week 1 (PHASE 1 - REGULATORY)
1. Run `verify_cars_sections.py` → review first 10 candidates
2. For each unmapped regulation question:
   - Read suggested CARS section in PDF
   - Confirm it matches the question's correct answer
   - Update `questions.json` with `"carsSection": "901.XX"`
   - Verify rationale quotes exact CARs text (not paraphrase)
3. Document any questions that don't match a single section → flag for rewrite

### Week 2-3 (PHASE 2 - COVERAGE GAPS)
1. Extract learning objectives from TP 15263 for Navigation, Flight Ops, Radio
2. Design 5-10 new questions per objective
3. Source from RPAS 101, AIM, or existing CARs examples
4. Verify scope: no Level 1 Complex, no BVLOS

### Week 3-4 (PHASE 3 - SOURCES)
1. Add RPAS 101 references to aircraft-systems, human-factors questions
2. Link AIM chapters to airspace/operations questions
3. Update `source` fields to multi-reference format

### Week 4-5 (PHASE 4 - VALIDATION)
1. Create Level 1 Complex/BVLOS filter
2. Run final `audit_tp15263_alignment.py`
3. Export clean question bank for exam prep

---

## 📞 KEY CONTACTS & RESOURCES

**Official CARs:**
- Justice Laws: https://laws-lois.justice.gc.ca/eng/regulations/SOR-96-433/
- Search for section: https://laws-lois.justice.gc.ca/eng/regulations/SOR-96-433/section-901.XX.html

**Transport Canada:**
- RPAS Learning: https://tc.canada.ca/en/aviation/remotely-piloted-aircraft-systems-rpas
- Knowledge Requirements: Look for TP 15263 / TP 15530

**NAV CANADA:**
- Products: https://www.navcanada.ca/
- DAH: Designated Airspace Handbook (local PDF available)

---

## 📈 METRICS TO TRACK

Track progress with these metrics:

```
Week 1: Regulation questions with CARs sections: 3/50 → 25/50 → 50/50
Week 2: Navigation questions: 25 → 35 → 50+ 
Week 3: Flight Operations questions: 25 → 40 → 55+
Week 4: Radio questions: 20 → 40 → 70+
Week 5: All sources with specific section numbers: 8/540 → 200/540 → 540/540
```

---

**Document Generated:** 2026-09-01 by GitHub Copilot with Explore subagent
**Last Updated:** [See session memory: /memories/session/question_bank_audit_plan.md]
