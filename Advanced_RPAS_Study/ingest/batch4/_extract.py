from pathlib import Path
from docx import Document
from docx.table import Table, _Cell
from docx.text.paragraph import Paragraph

root = Path(r"C:\Users\Ron Treleaven\Drone_SOP")
source = root / r"Advanced_RPAS_Study\ingest\batch4\Canadian_Advanced_RPAS_Validated_MCQ_Bank_100.docx"
target = root / r"Advanced_RPAS_Study\ingest\batch4\Bank_100_extracted.txt"
doc = Document(source)
lines = []
paragraph_count = 0

def extract_container(element, parent):
    global paragraph_count
    for child in element.iterchildren():
        if child.tag.endswith('}p'):
            paragraph_count += 1
            lines.append(Paragraph(child, parent).text)
        elif child.tag.endswith('}tbl'):
            table = Table(child, parent)
            for row in table.rows:
                for cell in row.cells:
                    extract_container(cell._tc, cell)

extract_container(doc.element.body, doc)
text = "\n".join(lines)
target.write_text(text, encoding="utf-8")
print(f"Total character count: {len(text)}")
print(f"Paragraphs extracted: {paragraph_count}")
print("First 100 lines:")
for i, line in enumerate(lines[:100], 1):
    print(f"{i}: {line}")
