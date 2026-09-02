# PHASE 3: SOURCE INTEGRATION - PLAN & IMPLEMENTATION

**Status:** Ready to Execute
**Date:** 2026-09-01
**Previous Phase:** Phase 2 (COMPLETE) - 639 questions, +114 added

---

## Phase 3 Overview

**Goal:** Integrate multi-source citations (RPAS 101, AIM, NAV CANADA) into questions to provide comprehensive reference material.

**Current State:**
- 639 questions in questions.json
- All regulation questions have CARs section mappings
- Most questions cite generic sources (e.g., "TP 15263 Section 5 – Navigation")
- 0 questions currently cite RPAS 101, AIM, or NAV CANADA as primary sources

**After Phase 3:**
- 639 questions with enhanced source citations
- Multi-source format: "CARs 901.23 + TP 15263 Section 6 + RPAS 101 Chapter 3"
- Rationales updated to include direct source quotes (not paraphrases)
- All major sources represented: CARs, TP 15263, RPAS 101, AIM, NAV CANADA

---

## Phase 3 Tasks

### Task 3.1: Add RPAS 101 References (50-75 questions)

**Target Categories:**
- aircraft-systems (50 questions) - RPAS fundamentals
- human-factors (40 questions) - Pilot certification, decision-making
- flight-planning (75 questions) - Site survey, risk assessment, energy management
- navigation (67 questions) - Coordinate systems, flight planning
- abnormal (25 questions) - Emergency procedures

**RPAS 101 Chapters to Map:**
- Chapter 1: Introduction to RPAS
- Chapter 2: Aircraft Systems & Performance
- Chapter 3: Human Factors & Pilot Certification
- Chapter 4: Navigation Systems
- Chapter 5: Flight Planning & Risk Management
- Chapter 6: Emergency Procedures

**Reference Format:**
```json
{
  "source": "CARs 901.26 + TP 15263 Section 2 + RPAS 101 Chapter 2",
  "rpas101_reference": "Aircraft Systems - Weight & Balance (page XX)"
}
```

**Estimated Time:** 2-3 hours

---

### Task 3.2: Add AIM Chapter References (30-40 questions)

**Target Categories:**
- airspace (50 questions) - Class A-D airspace, NOTAM interpretation
- aerodromes (50 questions) - Aerodrome procedures, runway operations
- radio (42 questions) - Phraseology, communication procedures
- notams (50 questions) - NOTAM dissemination and use

**AIM Sections to Map:**
- Section 2: Airspace
- Section 3: Aerodromes
- Section 4: Radiotelephony
- Section 5: NOTAM System
- Section 6: RPA Operations (Chapter RPA)

**Reference Format:**
```json
{
  "source": "CARs 901.19 + TP 15263 Section 6 + AIM Section 2",
  "aim_reference": "Airspace - Class D Control Zones"
}
```

**Estimated Time:** 1.5-2 hours

---

### Task 3.3: Add NAV CANADA References (20-30 questions)

**Target Categories:**
- radio (42 questions) - VFR Phraseology, standard transmissions
- notams (50 questions) - NOTAM dissemination
- airspace (50 questions) - Designated Airspace Handbook info

**NAV CANADA Materials to Map:**
- VFR Phraseology Guide
- Designated Airspace Handbook (DAH)
- Aviation Safety Letters (NOTAM examples)

**Reference Format:**
```json
{
  "source": "NAV CANADA VFR Phraseology + RPAS 101 Radio",
  "navcanada_reference": "Standard Phraseology - Initial Contact (Section 2.1)"
}
```

**Estimated Time:** 1-1.5 hours

---

### Task 3.4: Update All Rationales (Universal)

**Process:**
1. For questions with updated sources, enhance rationale to include direct quote
2. Example before:
   ```
   "rationale": "Wind shear reduces control authority."
   ```
3. Example after:
   ```
   "rationale": "Wind shear creates unpredictable wind changes with altitude, reducing control authority. TP 15263 Section 4 states: 'Pilots must be aware of wind shear and its effects on aircraft performance.' RPAS 101 recommends: 'If shear is encountered, descend to find stable air immediately.'"
   ```

**Categories to Update (by priority):**
1. PRIORITY 1: radio (42 qns) - use NAV CANADA + RPAS 101
2. PRIORITY 1: navigation (67 qns) - use RPAS 101 + TP 15263
3. PRIORITY 2: airspace (50 qns) - use AIM + CARs
4. PRIORITY 2: flight-planning (75 qns) - use TP 15263 + RPAS 101
5. PRIORITY 3: Others

**Estimated Time:** 2-3 hours

**Total Phase 3 Estimated Time:** 6-9 hours

---

## Implementation Strategy

### Approach: Batch Processing
- Process questions in batches of 10-15
- Verify each source citation against actual documents
- Test JSON structure after each batch
- Commit changes incrementally

### Tools Provided:
- phase3_add_rpas101_refs.py (to be created)
- phase3_add_aim_refs.py (to be created)
- phase3_add_navcanada_refs.py (to be created)
- phase3_update_rationales.py (to be created)

### Quality Checks:
- All citations must match actual source documents (no fabricated references)
- No false "direct quotes" - only include actual text from documents
- Maintain JSON structure validity
- Verify no duplicate source mappings
- Run: `python -m json.tool data/questions.json` to validate

---

## Success Criteria for Phase 3

- [ ] 50-75 questions have RPAS 101 references
- [ ] 30-40 questions have AIM references
- [ ] 20-30 questions have NAV CANADA references
- [ ] All source citations follow consistent format
- [ ] All rationales include substantive source material (not generic)
- [ ] JSON remains valid and parseable
- [ ] No questions have false or fabricated citations
- [ ] All questions still have verified primary sources (CARs/TP 15263)

---

## Document Inventory for Phase 3

| Document | Type | Primary Use | Status |
|----------|------|------------|--------|
| RPAS 101 Final | PDF | Aircraft systems, human factors, flight planning | ✓ Available |
| AIM RPA Chapter | PDF | Airspace, procedures, NOTAM | ✓ Available |
| VFR Phraseology | PDF | Radio communication questions | ✓ Available |
| CARs Part IX | PDF/XML | Regulation questions, operating limits | ✓ Available |
| DAH Handbook | PDF | Airspace, NOTAM context | ✓ Available |
| TP 15263 | PDF | All sections, learning objectives | ✓ Available |

---

## Phase 3 Execution Checklist

### Pre-Execution
- [ ] Review all source documents (PDFs available in /docs)
- [ ] Identify key passages/chapters by category
- [ ] Create reference mapping spreadsheet
- [ ] Test JSON editing workflow with single question

### Execution (Batch Processing)
- [ ] Process aircraft-systems + human-factors (RPAS 101)
- [ ] Process flight-planning + navigation (RPAS 101)
- [ ] Process airspace + aerodromes (AIM)
- [ ] Process radio + notams (NAV CANADA)
- [ ] Update rationales (universal)

### Post-Execution
- [ ] Validate JSON structure
- [ ] Spot-check 10-15 random questions for accuracy
- [ ] Verify no duplicate citations
- [ ] Generate Phase 3 completion report
- [ ] Document all changes in migration notes

---

## Notes for Implementation

1. **Source Document Access:**
   - All PDFs are in `/Advanced_RPAS_Study/docs/`
   - Search functionality or manual section review possible
   - Create extraction notes for future reference

2. **Citation Format Consistency:**
   - Use consistent ordering: Regulations first, then TP 15263, then other sources
   - Example: "CARs 901.27 + TP 15263 Section 6 + RPAS 101 Chapter 5 + AIM Section 2"

3. **Rationale Enhancement:**
   - Keep rationales educational (explain the "why")
   - Include direct quotes only when accurate
   - Link concepts to regulation/procedures

4. **Quality Assurance:**
   - Never fabricate citations
   - Verify each source statement against actual document
   - If unsure, add generic reference (e.g., "RPAS 101 Flight Planning") rather than specific quote

---

## Next Phase: Phase 4 (Validation & Cleanup)

After Phase 3 completes:
- Validate all sources are accurate (spot checks)
- Verify coverage targets are met
- Run final quality assurance scripts
- Generate final audit report
- Prepare question bank for deployment

---

**Phase 3 Ready to Begin**
Execute when ready to proceed with source integration.
