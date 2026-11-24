"""Read-only final document checks, after PDF generation and visual review.

Dependencies: bundled pypdf and pdfplumber. Validates layout/navigation and the
mission-statement source transcription; it does not validate sensor performance.
"""
from pathlib import Path
from zipfile import ZipFile
import hashlib
import json
import re
import xml.etree.ElementTree as ET

import pdfplumber
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[2]
PDF = ROOT / "outputs/d01_d04_research_2026-10-28/lunar_impact_d01_d04_report.pdf"
QA = ROOT / "tmp/pdfs/d01_d04_report"
reader = PdfReader(PDF)
texts = [page.extract_text() or "" for page in reader.pages]
assert len(texts) == 14, "Recheck pagination/visual layout after a report change"
assert "1.3 Flash light curves" in texts[1]
assert "1.4 Reconstructing" in texts[3]
assert "1.5 Impact energies" in texts[5] and "1.6 What is missed" in texts[6]
assert "2 Methodology" in texts[8] and "Trades and curve examples" in texts[8]
assert "reference conditions in §2.1" in " ".join(texts[9].split())
assert all(f"{i+1} / 14" in t for i,t in enumerate(texts))
assert all((QA / f"page-{i+1:02}.png").exists() for i in range(14))
all_text = "\n".join(texts)
assert all(term in all_text for term in ["2.895", "0.30", "10.7%", "69.4%", "8.3 s", "39 evidence", "4200", "580,000", "388 MJ", "41 days", "0.2 J", "146/46"])
assert not any(token in all_text for token in ["turn22", "turn25", "on page 3"])
outside = []
with pdfplumber.open(PDF) as pdf:
    for i,page in enumerate(pdf.pages, 1):
        outside.extend((i,c["text"]) for c in page.chars
                       if c["x0"] < 40 or c["x1"] > page.width-40
                       or c["top"] < 15 or c["bottom"] > page.height-15)
assert not outside, outside[:10]
outlines = [(entry.title, reader.get_destination_page_number(entry)+1) for entry in reader.outline]
assert [n for _,n in outlines] == [1,2,3,4,5,6,7,8,9,10,11,11,12,13,14]
links = [str(ann.get_object()["/A"]["/URI"]) for page in reader.pages for ann in page.get("/Annots", [])
         if ann.get_object().get("/A", {}).get("/URI")]
assert len(links) == 31 and all(link.startswith("https://") for link in links)

book = ROOT / "outputs/mission_definition_2026-10-27/mission_statement_research.xlsx"
note = ROOT / "outputs/mission_definition_2026-10-27/mission_statement_refinement_2026-10-28.md"
ns = {"s":"http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
with ZipFile(book) as z:
    strings = ["".join(t.text or "" for t in item.iter(f"{{{ns['s']}}}t"))
               for item in ET.fromstring(z.read("xl/sharedStrings.xml"))]
    sheet = ET.fromstring(z.read("xl/worksheets/sheet1.xml"))
    cells = {c.attrib["r"]:strings[int(c.find("s:v", ns).text)]
             for c in sheet.findall("s:sheetData/s:row/s:c", ns) if c.attrib.get("t") == "s"}
quotes = re.findall(r"^> (.+)$", note.read_text(encoding="utf-8"), flags=re.M)
assert len(quotes) == 6
assert [quotes[i] for i in [0,2,4]] == [cells[addr] for addr in ["C7","C8","C9"]]
historical_hash = hashlib.sha256(book.read_bytes()).hexdigest()
assert historical_hash == "cc0600b7793c04f28087d6f47da96d8e36ef9cc8e5f240557ca380ac2cb5424b"
report = {
    "pdf": str(PDF), "sha256": hashlib.sha256(PDF.read_bytes()).hexdigest(),
    "pages": len(texts), "visually_reviewed_pages": list(range(1,15)),
    "review": "All 14 pages reviewed; added energy sections and updated method/conclusion/source pages checked; negative exponents rendered with explicit superscript markup",
    "characters_outside_safe_bounds": len(outside), "page_numbers_verified": True,
    "outline_destinations": outlines, "source_links": len(links),
    "new_chapters_and_key_values_checked": True,
    "historical_workbook_preserved_sha256": historical_hash,
    "original_statement_quotes_match_cells": ["C7","C8","C9"],
    "limitations": "Literature and analytic examples; no new calibrated lunar sensor experiment or native Excel application test",
}
(QA / "verification.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
