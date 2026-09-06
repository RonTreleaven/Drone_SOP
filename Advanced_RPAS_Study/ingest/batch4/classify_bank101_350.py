#!/usr/bin/env python3
"""Parse Bank_101-350_extracted.txt into candidate questions with per-question category classification
for Section 1 (101-150) and Section 6 (251-300), which are content-mixed sections."""
import json, re
from pathlib import Path
from datetime import date

here = Path(__file__).resolve().parent
text = (here / "Bank_101-350_extracted.txt").read_text(encoding="utf-8")
lines = [l.rstrip() for l in text.splitlines()]

start_idx = next(i for i, l in enumerate(lines) if re.match(r"^101\.\s", l))
end_idx = next(i for i, l in enumerate(lines) if l.startswith("Validation notes"))
body = lines[start_idx:end_idx]

q_re = re.compile(r"^(\d+)\.\s+(.*)$")
choice_re = re.compile(r"^([A-D])\.\s+(.*)$")
answer_re = re.compile(r"^Answer:\s+([A-D])\.\s+(.*)$")
authority_re = re.compile(r"^Authority:\s+(.*)$")

raw = []
cur = None
for l in body:
    if not l.strip():
        continue
    if l.startswith("Section "):
        continue
    m = q_re.match(l)
    if m:
        if cur:
            raw.append(cur)
        cur = {"num": int(m.group(1)), "question": m.group(2), "choices": [], "answer_letter": None, "rationale": None, "authority": None}
        continue
    m = choice_re.match(l)
    if m and cur is not None:
        cur["choices"].append(m.group(2))
        continue
    m = answer_re.match(l)
    if m and cur is not None:
        cur["answer_letter"] = m.group(1)
        cur["rationale"] = m.group(2)
        continue
    m = authority_re.match(l)
    if m and cur is not None:
        cur["authority"] = m.group(1)
        continue
if cur:
    raw.append(cur)

assert len(raw) == 250, f"expected 250 questions, got {len(raw)}"
for q in raw:
    assert len(q["choices"]) == 4, q
    assert q["answer_letter"] and q["rationale"] and q["authority"], q

# --- Section 1 (101-150) classification: mixed airspace / regulations / aerodromes / safety / notams / radio
def classify_section1(q):
    blob = f"{q['question']} {q['rationale']} {q['authority']}".lower()
    if "notam" in blob:
        return "notams"
    if re.search(r"\b(class [abcde]\b|control zone|controlled airspace|ndas?\b|sda\b|northern domestic|southern domestic|escat|atf\b|mf area|terminal control area|tca\b|airspace class)", blob):
        return "airspace"
    if re.search(r"radio operator|two-way radio|listening watch|transponder|roc-a|7600|7700|communications failure", blob):
        return "radio"
    if re.search(r"collision hazard|dnd aerodrome", blob):
        return "safety"
    if "aerodrome" in blob or "airport" in blob:
        return "aerodromes"
    return "regulations"

# --- Section 6 (251-300) classification: mixed aerodromes / regulations / safety / human-factors /
#     visual-observers / abnormal / maintenance / flight-planning / airspace
def classify_section6(q):
    blob = f"{q['question']} {q['rationale']} {q['authority']}".lower()
    if re.search(r"\bmf area\b|\batf\b", blob):
        return "airspace"
    if re.search(r"\bapron\b|\brunway\b|taxiway|movement area|manoeuvring area|traffic circuit|windsock|obstruction light|uncontrolled aerodrome|circuit\b", blob):
        return "aerodromes"
    if re.search(r"visual observer", blob):
        return "visual-observers"
    if re.search(r"automation complacency|checklist|positive transfer of control|crew brief", blob):
        return "human-factors"
    if re.search(r"battery|propeller strike|hard landing|charging|damaged lithium|pre-flight inspection|serviceability", blob):
        return "maintenance"
    if re.search(r"flyaway|lost.link|lost-link|gnss loss|control-link quality|contingency for c2|contingency for gnss", blob):
        return "abnormal"
    if re.search(r"site survey|launch.recovery|launch/recovery|emergency landing area|first-aid|site access|weather deteriorates|headwind on the return|turbulence|low-battery return-to-home|automated return-to-home", blob):
        return "flight-planning"
    if re.search(r"people|crew member reports a crewed aircraft conflict|movement area incursion|unexpected person|interfere with aircraft in an established traffic pattern", blob):
        return "safety"
    return "regulations"

section_map = {}
for q in raw:
    n = q["num"]
    if 101 <= n <= 150:
        section_map[n] = classify_section1(q)
    elif 151 <= n <= 200:
        section_map[n] = "weather"
    elif 201 <= n <= 250:
        section_map[n] = "navigation"
    elif 251 <= n <= 300:
        section_map[n] = classify_section6(q)
    elif 301 <= n <= 350:
        section_map[n] = "radio"
    else:
        raise ValueError(n)

for q in raw:
    q["category"] = section_map[q["num"]]

report_path = here / "Bank_101-350_classification_report.txt"
with report_path.open("w", encoding="utf-8") as f:
    for q in raw:
        f.write(f"{q['num']:>3} [{q['category']:16s}] {q['question']}\n")
print("Wrote", report_path)
from collections import Counter
print(Counter(q["category"] for q in raw))

# Stash parsed raw questions (with authority/rationale/letters) for the next build step.
(here / "_parsed_101_350.json").write_text(json.dumps(raw, indent=2, ensure_ascii=False), encoding="utf-8")
