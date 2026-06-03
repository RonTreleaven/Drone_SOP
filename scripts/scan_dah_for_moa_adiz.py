from __future__ import annotations

import re
from pathlib import Path

from pypdf import PdfReader

PDF_PATH = Path("data/airspace/_maintenance required/dah20260514.pdf")
OUT_PATH = Path("data/airspace/reports/dah20260514_moa_adiz_scan.txt")

TERMS = ["MOA", "ADIZ"]
coord_pattern = re.compile(
    r"(\b\d{2,3}\s*[: ]\s*\d{2}\s*[: ]\s*\d{2}\s*[NSEW]\b)|(\b\d{2,3}°\s*\d{2}'\s*\d{2}(?:\.\d+)?\"?\s*[NSEW]\b)",
    re.IGNORECASE,
)


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def lines_with_terms(lines: list[str], term: str) -> list[int]:
    out = []
    for i, line in enumerate(lines):
        if re.search(rf"(^|[^A-Z0-9]){re.escape(term)}([^A-Z0-9]|$)", line, re.IGNORECASE):
            out.append(i)
    return out


def main() -> None:
    if not PDF_PATH.exists():
        raise SystemExit(f"Missing PDF: {PDF_PATH}")

    reader = PdfReader(str(PDF_PATH))

    all_hits: list[dict] = []
    for page_index, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        if not text.strip():
            continue

        raw_lines = [ln for ln in text.splitlines() if ln.strip()]
        lines = [normalize(ln) for ln in raw_lines]

        for term in TERMS:
            hit_indexes = lines_with_terms(lines, term)
            for idx in hit_indexes:
                start = max(0, idx - 2)
                end = min(len(lines), idx + 3)
                snippet = "\n".join(lines[start:end])

                # Look for coordinate-like strings near the hit to infer polygon definitions.
                local_window = " ".join(lines[max(0, idx - 10) : min(len(lines), idx + 11)])
                coord_matches = coord_pattern.findall(local_window)
                coord_like_found = bool(coord_pattern.search(local_window))

                all_hits.append(
                    {
                        "page": page_index,
                        "term": term,
                        "line": idx + 1,
                        "coord_like_found": coord_like_found,
                        "snippet": snippet,
                    }
                )

    out_lines: list[str] = []
    out_lines.append(f"PDF: {PDF_PATH}")
    out_lines.append(f"Pages: {len(reader.pages)}")
    out_lines.append(f"Total hits: {len(all_hits)}")
    out_lines.append("")

    for term in TERMS:
        term_hits = [h for h in all_hits if h["term"] == term]
        out_lines.append(f"{term} hits: {len(term_hits)}")
        if term_hits:
            pages = sorted({h["page"] for h in term_hits})
            out_lines.append("Pages: " + ", ".join(str(p) for p in pages))
        out_lines.append("")

    if all_hits:
        out_lines.append("Detailed hits:")
        out_lines.append("")
        for h in all_hits:
            out_lines.append(
                f"[Page {h['page']}, line {h['line']}, term {h['term']}, coord_like_nearby={h['coord_like_found']}]"
            )
            out_lines.append(h["snippet"])
            out_lines.append("")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text("\n".join(out_lines), encoding="utf-8")

    print(f"Wrote scan report: {OUT_PATH}")
    print(f"MOA hits: {sum(1 for h in all_hits if h['term'] == 'MOA')}")
    print(f"ADIZ hits: {sum(1 for h in all_hits if h['term'] == 'ADIZ')}")


if __name__ == "__main__":
    main()
