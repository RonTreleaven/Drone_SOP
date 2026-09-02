#!/usr/bin/env python3
import json

with open('data/questions.json') as f:
    data = json.load(f)
    
# Count by category
cats = {}
for q in data['questions']:
    cat = q['category']
    cats[cat] = cats.get(cat, 0) + 1

print('=' * 80)
print('PHASE 2 PROGRESS UPDATE (2A + 2B)')
print('=' * 80)
print()
print('COMBINED PROGRESS:')
print('  Phase 2A (Radio + Navigation Basics):  +25 questions')
print('  Phase 2B (Flight Ops + Nav Calcs):    +48 questions')
print('  Total Phase 2 Added So Far:           +73 questions')
print()
print('QUESTION BANK:')
print('  Before Phase 2: 525 questions')
print('  After Phase 2A: 550 questions')
print('  After Phase 2B: 598 questions')
print('  Still Needed (Phase 2C):              ~86 questions')
print()
print('CATEGORY BREAKDOWN (After Phase 2A+2B):')
print('  Radio:          %3d (+13 from Phase 2A)' % cats.get('radio', 0))
print('  Navigation:     %3d (+30 from Phase 2A+2B)' % cats.get('navigation', 0))
print('  Flight-Planning:%3d (+30 from Phase 2B)' % cats.get('flight-planning', 0))
print()
print('ALL CATEGORIES:')
for cat in sorted(cats.keys()):
    print('  %-18s %3d' % (cat + ':', cats[cat]))
print()
print('TOTAL: %d questions' % len(data['questions']))
print()
print('TP 15263 TARGET: ~77 questions per section')
print('Current shortfalls:')
print('  • Radio: 33/77 (+44 still needed)')
print('  • Navigation: 37/77 (+40 still needed)')
print('  • Flight Operations (via flight-planning): 55/77 (+22 still needed)')
print()
print('=' * 80)
