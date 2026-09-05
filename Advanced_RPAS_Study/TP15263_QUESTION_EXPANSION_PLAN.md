# TP 15263 Question Expansion Plan

## Goal

Build 200-300 additional Canadian RPAS exam-study questions against **TP 15263, Knowledge Requirements for Pilots of Remotely Piloted Aircraft Systems, 250 g up to and Including 25 kg, Operating within Visual Line-of-Sight**, Fourth Edition, March 2025.

The default quiz pool should support Advanced RPAS exam preparation, while retaining Basic knowledge where TP 15263 marks it as applicable. Level 1 Complex, BVLOS, and TP 15530 material must not appear in the default Advanced study pool.

## Source Hierarchy

1. TP 15263 knowledge requirement topic and learning objective.
2. Canadian Aviation Regulations and associated standards, especially CARs Part IX and Standards 921/922 where applicable.
3. TC AIM RPA chapter and relevant AIM material for operational context.
4. NAV CANADA material where the question depends on NOTAMs, airspace, DAH, CFS, RPA procedures, or radiotelephony context.
5. RPAS 101 only as supporting study context, not as the primary authority for a regulatory answer.

## Scope Fields

Every new question should include:

- `examScope`: one of `core-basic-advanced`, `core-advanced`, `supplemental`, `level-1-complex`.
- `examLevel`: one of `basic`, `advanced`, `basic-advanced`, `supplemental`, `level-1-complex`.
- `tp15263Section`: string section number from TP 15263 where applicable.
- `knowledgeArea`: broad TP 15263 area.
- `knowledgeTopic`: specific topic/subtopic when known.
- `learningObjective`: the tested objective in plain language.
- `sourceRefs`: array of precise sources used to verify the answer.

## Default Pool Rules

The default quiz pool includes:

- `examScope: "core-basic-advanced"`
- `examScope: "core-advanced"`

The default quiz pool excludes:

- `examScope: "supplemental"`
- `examScope: "level-1-complex"`
- Any source or question text that is primarily TP 15530, BVLOS, Level 1 Complex, detect-and-avoid, DAA, or beyond visual line-of-sight.

## Target Coverage

The 200-300 question expansion should be produced in reviewed batches. A practical target is 240 questions:

| TP 15263 Section | Knowledge Area | Target New Questions |
| --- | --- | ---: |
| 1 | Air law, regulations, and procedures | 50 |
| 2 | RPA airframes, power plants, propulsion and systems | 30 |
| 3 | Human factors | 25 |
| 4 | Meteorology | 35 |
| 5 | Navigation | 35 |
| 6 | Flight operations | 45 |
| 7 | Theory of flight | 15 |
| 8 | Radiotelephony | 20 |

## Batch Policy

Generate in batches of 25-40 questions. Each batch should:

- Prefer scenario questions over definition-only questions.
- Include A-D choices with one defensibly correct answer.
- Use plausible distractors that reflect common RPAS exam traps.
- Include concise rationales with exact source references.
- Avoid semantic duplicates of existing questions.
- Be validated before merging into `data/questions.json`.

## Initial Work Needed

1. Normalize existing blank `examScope`, `examLevel`, and TP 15263 metadata.
2. Move TP 15530, BVLOS, Level 1 Complex, and detect-and-avoid questions out of the default pool.
3. Produce batch 1 from high-priority weak areas:
   - regulatory boundaries
   - aerodrome/airport/heliport operations
   - visual observers
   - altitude and distance limits
   - Class F CYA/CYR
   - NOTAM interpretation
   - weather minima and density altitude
   - RPAS records and recency
4. Re-run validation after every batch.
