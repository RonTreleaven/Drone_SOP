from pathlib import Path
from docx import Document
from docx.table import Table, _Cell
from docx.text.paragraph import Paragraph
from docx.oxml.text.paragraph import CT_P
from docx.oxml.table import CT_Tbl

root = Path(r"C:\Users\Ron Treleaven\Drone_SOP\Advanced_RPAS_Study")
src = root / "ingest" / "batch4" / "Canadian_Advanced_RPAS_Validated_MCQ_Bank_101-350.docx"
out = root / "ingest" / "batch4" / "Bank_101-350_extracted.txt"

def iter_blocks(parent):
    parent_elm = parent._element.body if hasattr(parent, "_element") and hasattr(parent._element, "body") else parent._tc
    for child in parent_elm.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, parent)
        elif isinstance(child, CT_Tbl):
            yield Table(child, parent)

def extract_cell(cell, lines):
    global paragraph_count
    for block in iter_blocks(cell):
        if isinstance(block, Paragraph):
            lines.append(block.text)
            paragraph_count += 1
        else:
            extract_table(block, lines)

def extract_table(table, lines):
    for row in table.rows:
        for cell in row.cells:
            lines.append(cell.text)
            extract_cell(cell, lines)

doc = Document(str(src))
lines = []
paragraph_count = 0
for block in iter_blocks(doc):
    if isinstance(block, Paragraph):
        lines.append(block.text)
        paragraph_count += 1
    else:
        extract_table(block, lines)

out.write_text("\n".join(lines), encoding="utf-8")
print(f"total characters: {sum(len(line) for line in lines) + max(0, len(lines)-1)}")
print(f"paragraphs extracted: {paragraph_count}")
print(f"output: {out}")
