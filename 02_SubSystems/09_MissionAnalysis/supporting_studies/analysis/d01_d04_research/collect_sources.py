"""Cache public research PDFs and extract text with one-based PDF page markers.

Run from the workspace root with the bundled Python. Supplied PDFs are read only.
Network failures are recorded rather than replaced by unverified material.
"""
from pathlib import Path
import argparse
import hashlib
import json
import urllib.request
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "tmp" / "d01_d04_research" / "sources"
CACHE.mkdir(parents=True, exist_ok=True)
REMOTE = {
    "liakos_2020_journal": "https://www.aanda.org/articles/aa/pdf/2020/01/aa36709-19.pdf",
    "liakos_2024_journal": "https://www.aanda.org/articles/aa/pdf/2024/07/aa49542-24.pdf",
    "homogeneity_2026": "https://www.nature.com/articles/s43247-026-03270-z.pdf",
    "horanyi_2015": "https://spacephysics.princeton.edu/sites/g/files/toruqf1376/files/media/15_horanyi_a.pdf",
    "pokorny_2019": "https://ntrs.nasa.gov/api/citations/20210011054/downloads/Kuchner_Meteoroids%20at%20the%20Moon%20Orbital.pdf",
    "liakos_2020": "https://arxiv.org/pdf/1911.06101v1",
    "moorhead_2020": "https://arxiv.org/pdf/1909.05947v2",
    "mem3_guide_2020": "https://ntrs.nasa.gov/api/citations/20200000563/downloads/20200000563.pdf",
    "liakos_2024": "https://arxiv.org/pdf/2403.19613v1",
    "athanasopoulos_2026": "https://arxiv.org/pdf/2605.19635v3",
    "giancono_2026": "https://arxiv.org/pdf/2606.07177v1",
    "pancalli_2024": "https://re.public.polimi.it/retrieve/f609816c-3cf5-4468-93bc-12ee09e38135/PANCM01-24.pdf",
    "sheward_2025": "https://www.aanda.org/articles/aa/pdf/2025/07/aa55481-25.pdf",
    "benson_2025": "https://amostech.com/TechnicalPapers/2025/Satellite-Characterization/Benson.pdf",
    "sony_imx636_2025": "https://www.sony-semicon.com/files/62/flyer_industry/IMX636-AAMR-Flyer.pdf",
    "prophesee_imx636_2024": "https://prophesee.ai/wp-content/uploads/2024/06/IMX636-AAMR-C-Product-Brief-2024-1.pdf",
    "montanes_2007": "https://bbso.njit.edu/Research/EarthShine/literature/Montanes_etal_2007_AJ.pdf",
    "pancalli_2024_delft": "https://repository.tudelft.nl/file/File_ae131bed-1bbd-43dc-ade7-53d05321ea64?preview=1",
    "scidvs_2024": "https://arxiv.org/pdf/2409.09648v1",
    "wang_2020": "https://arxiv.org/pdf/2012.09378v1",
    "transient_calibration_2026": "https://mdpi-res.com/d_attachment/remotesensing/remotesensing-18-03201/article_deploy/remotesensing-18-03201.pdf",
    "scheerlinck_2018": "https://arxiv.org/pdf/1811.00386v1",
    "wang_akf_2021": "https://openaccess.thecvf.com/content/ICCV2021/papers/Wang_An_Asynchronous_Kalman_Filter_for_Hybrid_Event_Cameras_ICCV_2021_paper.pdf",
    "madiedo_2014": "https://arxiv.org/pdf/1402.5490v1",
}
parser = argparse.ArgumentParser()
parser.add_argument("--remote-only", action="store_true")
parser.add_argument("--only", nargs="+", choices=sorted(REMOTE), help="Refresh only these remote source IDs; retain other manifest records.")
args = parser.parse_args()

records = []
for name, url in REMOTE.items():
    if args.only and name not in args.only:
        continue
    target = CACHE / f"{name}.pdf"
    rec = {"id": name, "url": url, "access_date": "2026-10-28"}
    try:
        if not target.exists():
            req = urllib.request.Request(url, headers={"User-Agent": "MissionResearch/1.0"})
            with urllib.request.urlopen(req, timeout=45) as response:
                content = response.read()
            if not content.startswith(b"%PDF"):
                raise ValueError("Response was not a PDF")
            target.write_bytes(content)
        reader = PdfReader(target)
        extracted = "\n\n".join(
            f"=== PDF PAGE {i + 1} ===\n{page.extract_text()}"
            for i, page in enumerate(reader.pages)
        )
        target.with_suffix(".txt").write_text(extracted, encoding="utf-8")
        rec.update(status="cached", pages=len(reader.pages), sha256=hashlib.sha256(target.read_bytes()).hexdigest())
    except Exception as exc:
        rec.update(status="unavailable", error=str(exc))
    records.append(rec)
    print(f"{name}: {rec['status']}", flush=True)

for source in ([] if args.remote_only else (ROOT / "literarute").glob("*.pdf")):
    reader = PdfReader(source)
    text = "\n\n".join(f"=== PDF PAGE {i+1} ===\n{p.extract_text()}" for i, p in enumerate(reader.pages))
    (CACHE / (source.stem + ".txt")).write_text(text, encoding="utf-8")

manifest_path = CACHE / "manifest.json"
if args.only and manifest_path.exists():
    old_records = json.loads(manifest_path.read_text(encoding="utf-8"))
    reviewed = {record["id"] for record in records}
    records = [record for record in old_records if record["id"] not in reviewed] + records
manifest_path.write_text(json.dumps(records, indent=2), encoding="utf-8")
