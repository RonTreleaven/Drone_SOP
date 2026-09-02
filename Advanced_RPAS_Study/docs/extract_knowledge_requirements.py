import pdfplumber
import re
import json

pdf_path = 'TP15263_E_Knowledge-Requirements-Basic-Advanced.pdf'

with pdfplumber.open(pdf_path) as pdf:
    full_text = ''
    for page in pdf.pages:
        text = page.extract_text()
        if text:
            full_text += text + '\n'

# Find where Advanced Pilot section starts
advanced_start = full_text.lower().find('division v advanced operations')
if advanced_start == -1:
    advanced_start = full_text.lower().find('advanced pilot')

# Find where the next major section starts
advanced_end = len(full_text)
level1_pos = full_text.lower().find('level 1 complex')
bvlos_pos = full_text.lower().find('bvlos')
appendix_pos = full_text.lower().find('appendix')

for pos in [level1_pos, bvlos_pos, appendix_pos]:
    if pos > advanced_start and pos > 0:
        advanced_end = min(advanced_end, pos)

# Extract the Advanced section
advanced_section = full_text[advanced_start:advanced_end]

# Save to file for inspection
with open('advanced_section_raw.txt', 'w', encoding='utf-8') as f:
    f.write(advanced_section)

print(f"Advanced section extracted ({len(advanced_section)} characters)")
print(f"Saved to advanced_section_raw.txt")

# Now parse it to find sections and knowledge areas
# Look for lines starting with "Section" followed by knowledge areas
lines = advanced_section.split('\n')

knowledge_domains = []
current_section = None
current_domain = None
current_knowledge_area = None
in_objectives = False

for i, line in enumerate(lines):
    line_stripped = line.strip()
    
    # Skip empty lines
    if not line_stripped:
        continue
    
    # Look for section headers (e.g., "Section 1: Air Law")
    section_match = re.match(r'^Section\s+(\d+):\s*(.+)$', line_stripped, re.IGNORECASE)
    if section_match:
        current_section = {
            'number': section_match.group(1),
            'title': section_match.group(2).strip(),
            'knowledge_areas': []
        }
        knowledge_domains.append(current_section)
        print(f"\nFound Section {current_section['number']}: {current_section['title']}")
        continue
    
    # Look for knowledge areas (lines that start with numbers or are formatted differently)
    # These are typically indented and start with a number or bullet
    if current_section and re.match(r'^\s+\d+\.\s+', line_stripped):
        current_knowledge_area = {
            'title': line_stripped,
            'subtopics': []
        }
        current_section['knowledge_areas'].append(current_knowledge_area)

# Save structured output
print(f"\n\nExtracted {len(knowledge_domains)} knowledge domains")
for domain in knowledge_domains:
    print(f"  - Section {domain['number']}: {domain['title']}")
    print(f"    Knowledge Areas: {len(domain['knowledge_areas'])}")

with open('knowledge_domains.json', 'w', encoding='utf-8') as f:
    json.dump(knowledge_domains, f, indent=2)

print("\nStructured data saved to knowledge_domains.json")
