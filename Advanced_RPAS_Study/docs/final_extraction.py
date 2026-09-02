import pdfplumber
import json
import re

pdf_path = 'TP15263_E_Knowledge-Requirements-Basic-Advanced.pdf'

# Extract all text from PDF
with pdfplumber.open(pdf_path) as pdf:
    full_text = ''
    for page in pdf.pages:
        text = page.extract_text()
        if text:
            full_text += text + '\n'

# Extract Advanced Pilot section
advanced_start = full_text.lower().find('division v advanced operations')
if advanced_start == -1:
    advanced_start = full_text.lower().find('advanced pilot')

advanced_end = len(full_text)
for pos_str in ['level 1 complex', 'bvlos']:
    pos = full_text.lower().find(pos_str)
    if pos > advanced_start > 0:
        advanced_end = min(advanced_end, pos)

advanced_text = full_text[advanced_start:advanced_end]

# Parse sections
sections = {}
section_matches = list(re.finditer(r'^Section\s+(\d+):\s*(.+?)$', advanced_text, re.MULTILINE))

for idx, match in enumerate(section_matches):
    section_num = match.group(1)
    section_title = match.group(2).strip()
    
    # Get content from this section to the next section (or end)
    start_pos = match.end()
    if idx + 1 < len(section_matches):
        end_pos = section_matches[idx + 1].start()
    else:
        end_pos = len(advanced_text)
    
    section_content = advanced_text[start_pos:end_pos]
    
    # Parse knowledge areas and their content
    knowledge_areas = []
    
    # Split by knowledge area headers (not numbered, followed by numbered items)
    lines = section_content.split('\n')
    current_area = None
    current_subtopic = None
    current_objectives = []
    
    for line_idx, line in enumerate(lines):
        stripped = line.strip()
        
        if not stripped:
            continue
        
        # Skip metadata lines
        if any(skip in stripped for skip in ['RPAS Knowledge areas', 'type of operation', 
                                               'Basic Advanced', 'able to:']):
            continue
        
        # Detect knowledge area header (starts without bullet, followed by numbered items)
        if (not any(c in line for c in ['\uf0fc', '\uf0b7']) and 
            not stripped[0].isdigit() and
            len(stripped) < 100):
            
            # Check if next lines have numbered items
            has_items = False
            for j in range(line_idx + 1, min(line_idx + 5, len(lines))):
                if '\uf0fc' in lines[j] or ('\uf0b7' in lines[j] and re.search(r'\d+\.', lines[j])):
                    has_items = True
                    break
            
            if has_items:
                if current_area:
                    knowledge_areas.append(current_area)
                current_area = {'name': stripped, 'subtopics': []}
                current_subtopic = None
        
        # Parse subtopics and objectives
        elif current_area and ('\uf0fc' in line or '\uf0b7' in line):
            # Extract text without special characters
            clean_line = re.sub(r'^[\uf0fc\uf0b7\s]+', '', line).strip()
            
            # If starts with number, it's a subtopic
            if re.match(r'^\d+\.\s+', clean_line):
                # Save previous subtopic if any
                if current_subtopic:
                    current_area['subtopics'].append(current_subtopic)
                
                # Extract subtopic name and any trailing objective
                parts = re.split(r'\uf0b7', clean_line)
                subtopic_name = re.sub(r'^\d+\.\s+', '', parts[0]).strip()
                current_subtopic = {'name': subtopic_name, 'objectives': []}
                
                # If there's content after the bullet, it's an objective
                if len(parts) > 1:
                    for obj_part in parts[1:]:
                        obj = obj_part.strip()
                        if obj:
                            current_subtopic['objectives'].append(obj)
            
            # If it's just a bullet without number, it might be a continued objective
            elif current_subtopic:
                objective = clean_line
                if objective:
                    current_subtopic['objectives'].append(objective)
    
    # Save last subtopic
    if current_subtopic:
        current_area['subtopics'].append(current_subtopic)
    
    if current_area:
        knowledge_areas.append(current_area)
    
    sections[section_num] = {
        'title': section_title,
        'knowledge_areas': knowledge_areas
    }

# Save to JSON
output = {
    'title': 'ADVANCED PILOT KNOWLEDGE REQUIREMENTS',
    'source': 'TP15263_E_Knowledge-Requirements-Basic-Advanced.pdf',
    'section': 'ADVANCED PILOT ONLY (Excluding Level 1 Complex and BVLOS)',
    'sections': sections
}

with open('knowledge_requirements_extracted.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

# Create formatted text output
with open('knowledge_requirements_extracted.txt', 'w', encoding='utf-8') as f:
    f.write('='*120 + '\n')
    f.write('ADVANCED PILOT KNOWLEDGE REQUIREMENTS\n')
    f.write('SOURCE: TP15263_E_Knowledge-Requirements-Basic-Advanced.pdf\n')
    f.write('SECTION: Advanced Pilot Only\n')
    f.write('='*120 + '\n\n')
    
    for section_num in sorted(sections.keys(), key=lambda x: int(x)):
        section = sections[section_num]
        f.write(f"\n{'─'*120}\n")
        f.write(f"SECTION {section_num}: {section['title'].upper()}\n")
        f.write(f"{'─'*120}\n\n")
        
        for area_idx, area in enumerate(section['knowledge_areas'], 1):
            f.write(f"{section_num}.{area_idx}  {area['name'].upper()}\n\n")
            
            for sub_idx, subtopic in enumerate(area['subtopics'], 1):
                f.write(f"  {section_num}.{area_idx}.{sub_idx}  {subtopic['name']}\n")
                
                if subtopic.get('objectives'):
                    f.write(f"      Advanced Learning Objectives:\n")
                    for obj_num, obj in enumerate(subtopic['objectives'], 1):
                        # Wrap long objectives
                        obj_text = obj.replace('\n', ' ').strip()
                        if len(obj_text) > 100:
                            f.write(f"      {obj_num}. {obj_text}\n")
                        else:
                            f.write(f"      {obj_num}. {obj_text}\n")
                f.write('\n')
        
        f.write('\n')

# Print summary
print('='*120)
print('EXTRACTION COMPLETE - Advanced Pilot Knowledge Requirements')
print('='*120)
print()

total_areas = 0
total_subtopics = 0
total_objectives = 0

for section_num in sorted(sections.keys(), key=lambda x: int(x)):
    section = sections[section_num]
    n_areas = len(section['knowledge_areas'])
    n_subs = sum(len(a['subtopics']) for a in section['knowledge_areas'])
    n_objs = sum(len(s['objectives']) for a in section['knowledge_areas'] for s in a['subtopics'])
    
    total_areas += n_areas
    total_subtopics += n_subs
    total_objectives += n_objs
    
    print(f"Section {section_num}: {section['title']}")
    print(f"  • Knowledge Areas: {n_areas}")
    print(f"  • Subtopics/Learning Items: {n_subs}")
    print(f"  • Learning Objectives: {n_objs}")
    print()

print('─'*120)
print(f"TOTALS:")
print(f"  • Total Knowledge Domains (Sections): {len(sections)}")
print(f"  • Total Knowledge Areas: {total_areas}")
print(f"  • Total Subtopics/Learning Items: {total_subtopics}")
print(f"  • Total Learning Objectives Identified: {total_objectives}")
print('─'*120)

print(f"\nOutput files generated:")
print(f"  1. knowledge_requirements_extracted.json  (Structured JSON format)")
print(f"  2. knowledge_requirements_extracted.txt   (Readable text format)")

print('='*120)
