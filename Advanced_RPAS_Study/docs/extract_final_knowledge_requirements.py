import re
import json

# Read the raw extracted section
with open('advanced_section_raw.txt', 'r', encoding='utf-8') as f:
    text = f.read()

knowledge_domains = []
current_section = None
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
        current_knowledge_area = None
        i += 1
        continue
    
    # Skip the header lines
    if 'RPAS Knowledge areas' in stripped or 'type of operation' in stripped or 'Basic Advanced' in stripped or 'able to:' in stripped:
        i += 1
        continue
    
    # Match knowledge area headers (like "Airframes", "Aviation physiology", "General", etc.)
    # These are NOT indented and not starting with special PDF characters or numbers
    if current_section and stripped and not any(c in stripped for c in ['\uf0fc', '\uf0b7']):
        # Check if next line contains numbered items with special PDF characters
        has_numbered_items = False
        for j in range(i+1, min(i+5, len(lines))):
            next_line = lines[j]
            if ('\uf0fc' in next_line and '1.' in next_line) or ('\uf0b7' in next_line):
                has_numbered_items = True
                break
        
        if has_numbered_items and not any(word in stripped for word in ['Section', 'The RPA pilot', 'must be']):
            current_knowledge_area = {
                'name': stripped,
                'subtopics': []
            }
            current_section['knowledge_areas'].append(current_knowledge_area)
            i += 1
            continue
    
    # Match numbered subtopics: lines with special PDF bullets and numbers
    # Pattern: \uf0fc (and possibly more \uf0fc) followed by number. Text
    if current_knowledge_area and ('\uf0fc' in line or '\uf0b7' in line):
        # Extract the subtopic or objective
        # Remove the special characters and extract the text
        text_without_bullets = re.sub(r'^[\uf0fc\uf0b7\s]+', '', line)
        
        # Check if this is a numbered item (subtopic) or an objective (bullet after text)
        # Numbered items start with number like "1. Text"
        if re.match(r'^\d+\.\s+', text_without_bullets):
            # This is a subtopic
            subtopic = re.sub(r'^\d+\.\s+', '', text_without_bullets).strip()
            current_knowledge_area['subtopics'].append(subtopic)
        elif re.match(r'^\d+\.\s+.*\uf0b7', text_without_bullets):
            # This line contains both a subtopic and an objective
            parts = text_without_bullets.split('\uf0b7')
            if parts:
                # Extract the subtopic part
                subtopic = re.sub(r'^\d+\.\s+', '', parts[0]).strip()
                current_knowledge_area['subtopics'].append({
                    'name': subtopic,
                    'objectives': []
                })
                # Extract objectives from remaining parts
                for obj_part in parts[1:]:
                    obj = obj_part.strip()
                    if obj:
                        current_knowledge_area['subtopics'][-1]['objectives'].append(obj)
    
    i += 1

# Clean up the structure - standardize subtopics format
for section in knowledge_domains:
    for area in section['knowledge_areas']:
        # Flatten any nested structures
        new_subtopics = []
        for sub in area['subtopics']:
            if isinstance(sub, dict):
                new_subtopics.append(sub)
            else:
                new_subtopics.append({'name': sub, 'objectives': []})
        area['subtopics'] = new_subtopics

# Save as JSON
with open('knowledge_domains_final.json', 'w', encoding='utf-8') as f:
    json.dump(knowledge_domains, f, indent=2, ensure_ascii=False)

# Print formatted output
print("\n" + "="*100)
print("ADVANCED PILOT KNOWLEDGE REQUIREMENTS")
print("="*100 + "\n")

for section in knowledge_domains:
    print(f"\n{'─'*100}")
    print(f"SECTION {section['section_num']}: {section['section_title'].upper()}")
    print(f"{'─'*100}\n")
    
    for area_idx, area in enumerate(section['knowledge_areas'], 1):
        print(f"{area_idx}. {area['name'].upper()}")
        
        if area['subtopics']:
            for sub_idx, subtopic in enumerate(area['subtopics'], 1):
                if isinstance(subtopic, dict):
                    print(f"   {area_idx}.{sub_idx} {subtopic['name']}")
                    if subtopic.get('objectives'):
                        for obj in subtopic['objectives']:
                            obj_text = obj if len(obj) <= 80 else obj[:77] + "..."
                            print(f"         • {obj_text}")
                else:
                    print(f"   {area_idx}.{sub_idx} {subtopic}")
        print()

# Print summary
print(f"\n{'='*100}")
print(f"SUMMARY STATISTICS")
print(f"{'='*100}\n")

total_sections = len(knowledge_domains)
total_areas = sum(len(s['knowledge_areas']) for s in knowledge_domains)
total_subtopics = sum(len(a['subtopics']) for s in knowledge_domains for a in s['knowledge_areas'])
total_objectives = sum(len(sub.get('objectives', [])) 
                       for s in knowledge_domains 
                       for a in s['knowledge_areas'] 
                       for sub in a['subtopics'] 
                       if isinstance(sub, dict))

print(f"Total Knowledge Domains (Sections): {total_sections}")
print(f"Total Knowledge Areas: {total_areas}")
print(f"Total Subtopics/Learning Areas: {total_subtopics}")
print(f"Total Advanced Learning Objectives: {total_objectives}")

print(f"\n{'─'*100}")
print("Section Breakdown:")
print(f"{'─'*100}\n")

for section in knowledge_domains:
    area_count = len(section['knowledge_areas'])
    subtopic_count = sum(len(a['subtopics']) for a in section['knowledge_areas'])
    obj_count = sum(len(sub.get('objectives', [])) 
                   for a in section['knowledge_areas'] 
                   for sub in a['subtopics'] 
                   if isinstance(sub, dict))
    
    print(f"Section {section['section_num']}: {section['section_title']}")
    print(f"  • Knowledge Areas: {area_count}")
    print(f"  • Subtopics: {subtopic_count}")
    print(f"  • Advanced Objectives: {obj_count}\n")

print("="*100)
print("Output saved to: knowledge_domains_final.json")
print("="*100)
