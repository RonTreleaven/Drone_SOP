import json
import re
from pypdf import PdfReader

PDF_PATH = "NAVCANADA_DAH_current_20260709.pdf"
OUT_PATH = "DAH_area_index.json"

reader = PdfReader(PDF_PATH)
code_re = re.compile(r"\bCY[RADG]\d{2,4}[A-Z]?\b")

index = {}
for page_num, page in enumerate(reader.pages, start=1):
    try:
        text = page.extract_text() or ""
    except Exception:
        text = ""
    for m in code_re.finditer(text):
        code = m.group(0)
        if code not in index:
            start = max(0, m.start() - 20)
            end = min(len(text), m.end() + 200)
            snippet = " ".join(text[start:end].split())
            index[code] = {"code": code, "firstPage": page_num, "snippet": snippet}

meta = {
    "sourceFile": PDF_PATH,
    "sourceUrl": "https://www.navcanada.ca/en/dah20260709.pdf",
    "effectiveDate": "2026-07-09",
    "pageCount": len(reader.pages),
    "uniqueAreaCodesFound": len(index),
}

with open(OUT_PATH, "w", encoding="utf-8") as f:
    json.dump({"metadata": meta, "areas": index}, f, ensure_ascii=False, indent=2)

print(json.dumps(meta, indent=2))
print("Sample entries:")
for i, (k, v) in enumerate(index.items()):
    if i >= 5:
        break
    print(k, "-> page", v["firstPage"], ":", v["snippet"][:120])
