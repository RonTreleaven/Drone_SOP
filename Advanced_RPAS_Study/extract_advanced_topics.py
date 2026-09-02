#!/usr/bin/env python3
"""
Extract Knowledge Requirements and analyze Advanced topics
"""

import json
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict

docx_path = Path(r"C:\Users\Ron Treleaven\Drone_SOP\Advanced_RPAS_Study\docs\Knowledge_Requirements_Advanced.docx")

try:
    # Extract text from DOCX (ZIP file)
    with zipfile.ZipFile(docx_path, 'r') as zip_ref:
        xml_content = zip_ref.read('word/document.xml')
        
    # Parse XML
    root = ET.fromstring(xml_content)
    
    # Namespace for Word documents
    namespaces = {
        'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
    }
    
    # Extract all text
    full_text = []
    for para in root.findall('.//w:p', namespaces):
        text_elements = para.findall('.//w:t', namespaces)
        para_text = ''.join([t.text for t in text_elements if t.text])
        if para_text.strip():
            full_text.append(para_text)
    
    # Save to file
    output_path = Path(r"C:\Users\Ron Treleaven\Drone_SOP\Advanced_RPAS_Study\docs\knowledge_requirements_extracted.txt")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(full_text))
    
    print(f"✓ Extracted {len(full_text)} paragraphs")
    print(f"✓ Saved to: {output_path}")
    
    # Extract key topics and learning objectives
    topics = []
    learning_objectives = []
    cars_references = []
    aim_references = []
    
    for line in full_text:
        if 'learning objective' in line.lower() or 'state that' in line.lower() or 'recall' in line.lower() or 'describe' in line.lower():
            learning_objectives.append(line)
        
        if 'CARS' in line and any(num in line for num in ['60', '61', '62']):
            cars_references.append(line)
        
        if 'AIM' in line or 'Section' in line:
            aim_references.append(line)
    
    # Save analysis
    analysis = {
        "total_paragraphs": len(full_text),
        "learning_objectives": learning_objectives[:50],  # First 50
        "cars_references": cars_references[:50],
        "aim_references": aim_references[:50]
    }
    
    with open(r"C:\Users\Ron Treleaven\Drone_SOP\Advanced_RPAS_Study\docs\knowledge_analysis.json", 'w', encoding='utf-8') as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Analysis saved")
    print(f"  • Learning objectives found: {len(learning_objectives)}")
    print(f"  • CARS references found: {len(cars_references)}")
    print(f"  • AIM references found: {len(aim_references)}")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
