"""Read-only verification of saved Excel caches, structures and local Markdown links."""
import csv
import json
import math
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import unquote
from zipfile import ZipFile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BOOK = ROOT / "outputs/d01_d04_research_2026-10-28/d01_d04_research.xlsx"
NS = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
mapping = json.loads((HERE / "workbook_cells.json").read_text())
model = json.loads((HERE / "model_results.json").read_text())

with ZipFile(BOOK) as archive:
    workbook = ET.fromstring(archive.read("xl/workbook.xml"))
    names = [s.attrib["name"] for s in workbook.find("s:sheets", NS)]
    assert names == ["Candidate values", "Photon budget", "Localization", "Comparators", "Evidence", "Decisions", "Light curves", "Reconstruction", "Energy distribution", "Energy catalogue"]
    errors = []
    formulas = 0
    cached = {}
    pane_count = 0
    for i, name in enumerate(names, 1):
        sheet = ET.fromstring(archive.read(f"xl/worksheets/sheet{i}.xml"))
        assert sheet.find("s:mergeCells", NS) is None, f"Unexpected merged cells on {name}"
        pane_count += len(sheet.findall("s:sheetViews/s:sheetView/s:pane", NS))
        for cell in sheet.findall("s:sheetData/s:row/s:c", NS):
            address = cell.attrib["r"]
            value = cell.find("s:v", NS)
            if cell.attrib.get("t") == "e":
                errors.append((name, address, value.text if value is not None else "missing"))
            if cell.find("s:f", NS) is not None:
                formulas += 1
                assert value is not None, (name, address, "missing cached result")
                cached[(name, address)] = value.text
    assert not errors, errors
    assert pane_count == 10, pane_count
    p = mapping["photon"]
    l = mapping["localization"]
    expected = [
        ("Photon budget", f"B{p['snr']}", model["base_photon_budget"]["snr_detection"]),
        ("Photon budget", f"B{p['peakSNR']}", model["base_photon_budget"]["snr_characterization_peak_bin"]),
        ("Photon budget", f"B{p['energyRss']}", model["energy_rss_fraction"]),
        ("Photon budget", f"B{p['peakRss']}", model["peak_rss_fraction"]),
        ("Localization", "G9", model["localization"][2]["major95_km"]),
        ("Candidate values", "C7", model["base_photon_budget"]["radiant_exposure_J_m2"]),
        ("Candidate values", "C8", 1000),
        ("Candidate values", "C9", 3000),
        ("Candidate values", "C10", 10000),
        ("Candidate values", "C19", 5),
        ("Candidate values", "C20", 1),
    ]
    for sheet, address, value in expected:
        assert math.isclose(float(cached[(sheet, address)]), value, rel_tol=1e-9, abs_tol=1e-20), (sheet,address)
    energy_rows = json.loads((ROOT / "data/lunar_impact_energy/neliota_192_validated_energy_catalogue.json").read_text())
    energy_results = json.loads((HERE / "energy_distribution_results.json").read_text())
    assert len(energy_rows) == len({r['event_id'] for r in energy_rows}) == 192
    assert energy_results['rounding_consistency_exceptions'] == []
    for i,row in enumerate(energy_rows, 7):
        assert math.isclose(float(cached[('Energy catalogue',f'G{i}')]), row['R_plus_I_energy_J'], rel_tol=1e-12)
        assert math.isclose(float(cached[('Energy catalogue',f'H{i}')]), row['R_plus_I_energy_J']/0.0015, rel_tol=1e-12)
    for i,bin_row in enumerate(energy_results['histogram'], 13):
        assert float(cached[('Energy distribution',f'C{i}')]) == bin_row['count']
        assert math.isclose(float(cached[('Energy distribution',f'D{i}')]), bin_row['fraction'], rel_tol=1e-12, abs_tol=1e-20)


def source_cells(file, sheet_index):
    """Compare substantive cells and resolved cell styles in the unchanged model sheets."""
    with ZipFile(file) as z:
        strings = []
        if "xl/sharedStrings.xml" in z.namelist():
            for item in ET.fromstring(z.read("xl/sharedStrings.xml")):
                strings.append("".join(t.text or "" for t in item.iter(f"{{{NS['s']}}}t")))
        style_root = ET.fromstring(z.read("xl/styles.xml"))
        xfs = list(style_root.find("s:cellXfs", NS))
        style_parts = {key: list(style_root.find(f"s:{key}", NS)) for key in ["fonts", "fills", "borders"]}
        formats = {n.attrib["numFmtId"]:n.attrib["formatCode"] for n in style_root.findall("s:numFmts/s:numFmt", NS)}
        sheet = ET.fromstring(z.read(f"xl/worksheets/sheet{sheet_index}.xml"))
        out = {}
        for c in sheet.findall("s:sheetData/s:row/s:c", NS):
            v, f = c.find("s:v", NS), c.find("s:f", NS)
            if v is None and f is None and c.find("s:is", NS) is None:
                continue
            kind = c.attrib.get("t", "n")
            value = v.text if v is not None else None
            if kind == "s":
                value = strings[int(value)]
            elif kind == "inlineStr":
                value = "".join(t.text or "" for t in c.findall("s:is//s:t", NS))
            elif kind == "n" and value is not None:
                value = float(value)
            xf = xfs[int(c.attrib.get("s", "0"))]
            style = {k:v for k,v in xf.attrib.items() if k not in ["fontId","fillId","borderId","numFmtId"]}
            for field, group in [("fontId","fonts"),("fillId","fills"),("borderId","borders")]:
                style[field] = ET.tostring(style_parts[group][int(xf.attrib.get(field,"0"))], encoding="unicode")
            style["format"] = formats.get(xf.attrib.get("numFmtId", "0"), xf.attrib.get("numFmtId", "0"))
            style["children"] = [ET.tostring(child, encoding="unicode") for child in xf]
            out[c.attrib["r"]] = (kind if kind not in ["s","inlineStr"] else "text", value, f.text if f is not None else None, style)
        columns = [ET.tostring(c, encoding="unicode") for c in sheet.findall("s:cols/s:col", NS)]
        panes = [ET.tostring(p, encoding="unicode") for p in sheet.findall("s:sheetViews/s:sheetView/s:pane", NS)]
        return out, columns, panes


preservation = []
before = ROOT / "tmp/d01_d04_research/before_lightcurve_update.xlsx"
if before.exists():
    for index, name in enumerate(names[:3], 1):
        old, new = source_cells(before, index), source_cells(BOOK, index)
        assert old == new, f"Unintended cell/style/column/pane change on {name}"
        preservation.append(name)

with (HERE / "parameter_sweep.csv").open(newline="", encoding="utf-8") as file:
    sweep = list(csv.DictReader(file))
assert len(sweep) == 54
for row in sweep:
    assert all(math.isfinite(float(x)) for x in row.values())

broken_links = []
for file in [ROOT/"analysis/d01_d04_research.md", ROOT/"design_driving_quantities.md", ROOT/"questions.md", HERE/"README.md",
             ROOT/"outputs/mission_definition_2026-10-27/mission_statement_refinement_2026-10-28.md",
             ROOT/"outputs/mission_definition_2026-10-27/mission_objective_energy_review_2026-10-28.md",
             ROOT/"data/lunar_impact_energy/README.md"]:
    for link in re.findall(r"\]\(([^)]+)\)", file.read_text(encoding="utf-8")):
        if "://" in link or link.startswith("#"):
            continue
        target = (file.parent / unquote(link.split("#")[0])).resolve()
        if not target.exists():
            broken_links.append((str(file), link))
assert not broken_links, broken_links

report = {"xlsx": str(BOOK), "worksheets": names, "formula_cells_with_cached_results": formulas,
          "excel_error_cells": len(errors), "freeze_panes": pane_count,
          "independent_numeric_comparisons": len(expected), "csv_rows": len(sweep),
          "unchanged_model_sheets_cell_style_column_and_pane_comparison": preservation,
          "energy_catalogue_rows_checked":len(energy_rows), "energy_numeric_cache_comparisons":396,
          "broken_local_markdown_links": len(broken_links), "native_Excel_test": "not performed"}
target = ROOT / "tmp/d01_d04_research/workbook_previews/saved_file_verification.json"
target.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
