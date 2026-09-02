import re
import json

# Read the raw extracted section
with open('advanced_section_raw.txt', 'r', encoding='utf-8') as f:
    text = f.read()

knowledge_domains = []
current_section = None
current_main_area = None
current_knowledge_area = None

lines = text.split('\n')

i = 0
while i < len(lines):
    line = lines[i].rstrip()
    stripped = line.strip()
    
    # Skip empty lines
    if not stripped:
        i += 1
        continue
    
    # Match section headers: "Section N: Title"
    section_match = re.match(r'^Section\s+(\d+):\s*(.+?)$', stripped)
    if section_match:
        current_section = {
            'section_num': section_match.group(1),
            'section_title': section_match.group(2).strip(),
            'knowledge_areas': []
        }
        knowledge_domains.append(current_section)
        current_main_area = None
        current_knowledge_area = None
        i += 1
        continue
    
    # Skip the header line "RPAS Knowledge areas (topics) Sample learning objectives"
    if 'RPAS Knowledge areas' in stripped or 'type of operation' in stripped:
        i += 1
        continue
    
    # Match main knowledge area headers (like "Airframes", "Electrical systems", etc.)
    # These are typically:
    # - Not indented or lightly indented
    # - Not starting with a number and dot (unlike subtopics)
    # - Usually a single capitalized word or phrase
    # - Followed by numbered items
    if current_section and stripped and not stripped.startswith('•'):
        # Check if this looks like a knowledge area header
        # (not a numbered item, not learning objective text)
        if (not re.match(r'^\d+\.\s+', stripped) and
            not re.match(r'^(Describe|Explain|Identify|State|Recall|Assess|List|Discuss|Demonstrate|Interpret|Determine|Compare|Define|Give|Recognize|Resolve|Promote|Place|Locate|Relate|Use|Provide|Discuss|Interpret|Demonstrate)\s', stripped) and
            not any(keyword in stripped for keyword in ['basic', 'advanced', 'CAR', 'AIM', 'must be', 'The RPA pilot']) and
            len(stripped) < 80 and
            not stripped[0].islower()):
            
            # Check if next few lines contain numbered items to confirm this is a knowledge area
            found_numbered_item = False
            for j in range(i+1, min(i+5, len(lines))):
                if re.match(r'^\s+\d+\.\s+', lines[j]):
                    found_numbered_item = True
                    break
            
            if found_numbered_item:
                current_main_area = {
                    'name': stripped,
                    'subareas': []
                }
                current_section['knowledge_areas'].append(current_main_area)
                current_knowledge_area = None
                i += 1
                continue
    
    # Match numbered subtopics/subareas (indented): "  1. Name" or "    1. Name"
    if current_main_area and re.match(r'^\s+\d+\.\s+', stripped):
        subarea_name = re.sub(r'^\s+\d+\.\s+', '', stripped)
        # Remove any trailing explanatory text
        subarea_name = subarea_name.split('(')[0].strip()
        
        current_knowledge_area = {
            'name': subarea_name,
            'advanced_objectives': []
        }
        current_main_area['subareas'].append(current_knowledge_area)
        i += 1
        continue
    
    # Match learning objectives - these typically start with action verbs
    # and may span multiple lines
    if current_knowledge_area:
        objective_verbs = ['Describe', 'Explain', 'Identify', 'State', 'Recall', 
                          'Assess', 'List', 'Discuss', 'Demonstrate', 'Interpret',
                          'Determine', 'Compare', 'Define', 'Give', 'Recognize',
                          'Resolve', 'Promote', 'Place', 'Locate', 'Relate', 'Use',
                          'Provide', 'Distinguish', 'Demonstrate', 'Interpret',
                          'Show', 'Develop', 'Apply', 'Analyze', 'Calculate']
        
        if any(stripped.startswith(verb) for verb in objective_verbs):
            # Remove leading bullet point if present
            objective = re.sub(r'^•\s*', '', stripped)
            current_knowledge_area['advanced_objectives'].append(objective)
    
    i += 1

# Remove sections with no knowledge areas
knowledge_domains = [s for s in knowledge_domains if s['knowledge_areas']]

# Save as JSON
with open('knowledge_domains_structured.json', 'w', encoding='utf-8') as f:
    json.dump(knowledge_domains, f, indent=2, ensure_ascii=False)

# Print summary
print("=" * 90)
print("ADVANCED PILOT KNOWLEDGE REQUIREMENTS - STRUCTURED EXTRACTION")
print("=" * 90)

for section in knowledge_domains:
    print(f"\n{'='*90}")
    print(f"SECTION {section['section_num']}: {section['section_title'].upper()}")
    print(f"{'='*90}")
    print(f"Total Knowledge Areas: {len(section['knowledge_areas'])}\n")
    
    for idx, area in enumerate(section['knowledge_areas'], 1):
        print(f"{idx}. {area['name'].upper()}")
        
        total_subareas = len(area['subareas'])
        total_objectives = sum(len(sub['advanced_objectives']) for sub in area['subareas'])
        
        print(f"   Subareas: {total_subareas} | Total Learning Objectives: {total_objectives}")
        
        for sub_idx, subarea in enumerate(area['subareas'], 1):
            print(f"\n   {idx}.{sub_idx} {subarea['name']}")
            if subarea['advanced_objectives']:
                for obj_idx, obj in enumerate(subarea['advanced_objectives'], 1):
                    obj_text = obj if len(obj) <= 85 else obj[:85] + "..."
                    print(f"       • {obj_text}")
        print()

print(f"\n{'='*90}")
print(f"SUMMARY")
print(f"{'='*90}")
print(f"Total Sections: {len(knowledge_domains)}")
total_areas = sum(len(s['knowledge_areas']) for s in knowledge_domains)
total_subareas = sum(len(sub) for s in knowledge_domains for area in s['knowledge_areas'] for sub in [area['subareas']])
total_objectives = sum(len(sub['advanced_objectives']) 
                       for s in knowledge_domains 
                       for area in s['knowledge_areas']
                       for sub in area['subareas'])

print(f"Total Knowledge Areas: {total_areas}")
print(f"Total Subareas/Subtopics: {sum(len(a['subareas']) for s in knowledge_domains for a in s['knowledge_areas'])}")
print(f"Total Advanced Learning Objectives: {total_objectives}")
print(f"\nStructured JSON saved to: knowledge_domains_structured.json")
print("=" * 90)
