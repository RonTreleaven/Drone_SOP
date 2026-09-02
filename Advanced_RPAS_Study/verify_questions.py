import json
with open('data/questions.json') as f:
    d = json.load(f)
print(f'Total Questions: {len(d["questions"])}')
print('\nLast 10 question IDs:')
for q in d['questions'][-10:]:
    print(f'  {q["id"]}')
