import json
from pathlib import Path

questions_file = Path("data/questions.json")
with open(questions_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Show first 10 aircraft-systems questions
aircraft_sys = [q for q in data['questions'] if q.get('category') == 'aircraft-systems'][:10]
print("Aircraft Systems Question IDs:")
for q in aircraft_sys:
    print(f"  ID: {q.get('id')} | Question: {q.get('question')[:50]}...")

# Show first 5 human-factors
human_fac = [q for q in data['questions'] if q.get('category') == 'human-factors'][:5]
print("\nHuman Factors Question IDs:")
for q in human_fac:
    print(f"  ID: {q.get('id')} | Question: {q.get('question')[:50]}...")

# Show first 5 flight-planning
flight_plan = [q for q in data['questions'] if q.get('category') == 'flight-planning'][:5]
print("\nFlight Planning Question IDs:")
for q in flight_plan:
    print(f"  ID: {q.get('id')} | Question: {q.get('question')[:50]}...")

# Show first 5 navigation
nav = [q for q in data['questions'] if q.get('category') == 'navigation'][:5]
print("\nNavigation Question IDs:")
for q in nav:
    print(f"  ID: {q.get('id')} | Question: {q.get('question')[:50]}...")
