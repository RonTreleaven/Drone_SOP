#!/usr/bin/env python3
import json

with open('data/questions.json') as f:
    data = json.load(f)
    
# Count by category
cats = {}
for q in data['questions']:
    cat = q['category']
    cats[cat] = cats.get(cat, 0) + 1

print('=== PHASE 2A VERIFICATION ===')
print()
print('Questions by Category (After Phase 2A):')
print('  Radio:      %d (+13 from Phase 2A)' % cats.get('radio', 0))
print('  Navigation: %d (+12 from Phase 2A)' % cats.get('navigation', 0))
print()
print('Total Questions: %d (was 525, +25)' % len(data['questions']))
print()
print('Full category breakdown:')
for cat in sorted(cats.keys()):
    print('  %s: %d' % (cat, cats[cat]))
