"""Audit and summarize the two published NELIOTA validated-flash tables.

Run from the workspace root with analysis/v2e/.conda/python.exe (numpy, matplotlib).
Reads the pypdf text cache produced by collect_sources.py, with PDF page markers.
No raw telescope measurements are reprocessed and no completeness correction is
invented. PDF extraction is deterministic; source tokens/pages accompany each row.
"""
from pathlib import Path
import csv
import hashlib
import json
import math
import re

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CACHE = ROOT / "tmp/d01_d04_research/sources"
DATA = ROOT / "data/lunar_impact_energy"
FIG = ROOT / "figures/lunar_impact_energy"
DATA.mkdir(parents=True, exist_ok=True)
FIG.mkdir(parents=True, exist_ok=True)
NOMINAL_ETA = 0.0015
TOKEN = re.compile(r"^(\d+(?:\.\d+)?)\((\d+(?:\.\d+)?)\)$")


def value_error(token):
    match = TOKEN.fullmatch(token)
    if not match:
        raise ValueError(token)
    value, error = match.groups()
    decimals = len(value.partition(".")[2])
    # 116.4(3.5) explicitly states a decimal uncertainty, unlike 0.60(8).
    sigma = float(error) if "." in error else float(error) * 10 ** -decimals
    return float(value), sigma, 0.5 * 10 ** -decimals


rows = []
rounding_audit = []
sources = [
    ("liakos_2020", [18, 19], "Tables 4-5", 79, 1e7, "E33"),
    ("liakos_2024", [19, 20, 21], "Table A.2", 113, 1e6, "E03"),
]
for source, pages, table, expected, low_eta_scale, evidence in sources:
    pdf = CACHE / f"{source}.pdf"
    page_texts = re.split(r"=== PDF PAGE \d+ ===", pdf.with_suffix(".txt").read_text(encoding="utf-8"))
    checksum = hashlib.sha256(pdf.read_bytes()).hexdigest()
    start = len(rows)
    for page in pages:
        for line in page_texts[page].splitlines():
            parts = line.split()
            if len(parts) != 17 or not parts[0].isdigit() or not all(TOKEN.fullmatch(t) for t in parts[2:]):
                continue
            numbers = [value_error(t) for t in parts[2:]]
            r, i = numbers[:2]
            optical = (r[0] + i[0]) * 1e4
            energies = [numbers[3][0] * 1e6, numbers[7][0] * 1e6, numbers[11][0] * low_eta_scale]
            row = {
                "event_id": int(parts[0]), "stream": parts[1],
                "R_energy_J": r[0] * 1e4, "R_quoted_error_J": r[1] * 1e4,
                "I_energy_J": i[0] * 1e4, "I_quoted_error_J": i[1] * 1e4,
                "R_plus_I_energy_J": optical,
                "KE_eta_0p0015_from_rounded_optical_J": optical / NOMINAL_ETA,
                "KE_eta_0p005_published_J": energies[0],
                "KE_eta_0p0015_published_J": energies[1],
                "KE_eta_0p0005_published_J": energies[2],
                "nominal_mass_g_published": numbers[8][0],
                "source_id": source, "source_table": table, "source_pdf_page": page,
                "evidence_id": evidence, "source_sha256": checksum,
                "source_numeric_tokens": " ".join(parts[2:]),
            }
            rows.append(row)
            for eta, idx, scale in [(0.005, 3, 1e6), (NOMINAL_ETA, 7, 1e6), (0.0005, 11, low_eta_scale)]:
                published, _, rounding = numbers[idx]
                predicted = optical / eta
                allowance = (r[2] + i[2]) * 1e4 / eta + rounding * scale
                if abs(published * scale - predicted) > allowance + 1:
                    rounding_audit.append({"event_id": row["event_id"], "eta": eta,
                                           "published_J": published * scale, "from_rounded_R_I_J": predicted,
                                           "difference_J": published * scale - predicted,
                                           "rounding_allowance_J": allowance})
    assert len(rows) - start == expected, (source, len(rows) - start, expected)

assert len(rows) == 192 and len({r["event_id"] for r in rows}) == 192
rows.sort(key=lambda r: r["event_id"])
csv_path = DATA / "neliota_192_validated_energy_catalogue.csv"
with csv_path.open("w", newline="", encoding="utf-8") as handle:
    writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)
(DATA / "neliota_192_validated_energy_catalogue.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")

energies = np.array([r["R_plus_I_energy_J"] for r in rows])
edges = np.array([0, 4e3, 1e4, 3e4, 1e5, 3e5, 1e6])
counts, _ = np.histogram(energies, bins=edges)
bins = [{"lower_J_inclusive": float(a), "upper_J_exclusive": float(b),
         "count": int(n), "fraction": int(n) / len(rows),
         "poisson_fractional_sigma": 1 / math.sqrt(int(n)) if n else None}
        for a, b, n in zip(edges[:-1], edges[1:], counts)]
quantiles = {str(q): float(np.quantile(energies, q, method="linear")) for q in [0, 0.1, 0.25, 0.5, 0.75, 0.9, 1]}
min_row = min(rows, key=lambda r: r["R_plus_I_energy_J"])
max_row = max(rows, key=lambda r: r["R_plus_I_energy_J"])
area = 3.11e6
moon_area = 4 * math.pi * 1737.4 ** 2
rate_spo = 145 / (237.8 * area)
rate_stream = 47 / (45.6 * area)
summary = {
    "review_date": "2026-10-28", "population": "192 published validated NELIOTA flashes, 2017-August 2023",
    "scope": "Observed, uncorrected sample; neither a complete lunar population nor a complete energy interval.",
    "energy_definition": "Source hemispheric-equivalent integrated Cousins R plus I energy; not bolometric, nor the mission 600-900 nm top-hat.",
    "eta_nominal": NOMINAL_ETA, "eta_scenarios": [0.005, NOMINAL_ETA, 0.0005],
    "count": len(rows), "sporadic_count": sum(r["stream"] == "spo" for r in rows),
    "stream_associated_count": sum(r["stream"] != "spo" for r in rows),
    "optical_quantiles_J": quantiles, "histogram": bins,
    "minimum": min_row, "maximum": max_row,
    "published_nominal_KE_range_J": [min(r["KE_eta_0p0015_published_J"] for r in rows), max(r["KE_eta_0p0015_published_J"] for r in rows)],
    "rounding_consistency_exceptions": rounding_audit,
    "source_narrative_discrepancy": "2024 author v1 section 6 quotes 0.8 MJ-1.05 GJ across eta scenarios. The retained 2020 author-v1 Tables 4-5 have a 1.164 GJ maximum at eta=0.0005 (ID97); do not silently replace the table or describe either as a fixed-eta range.",
    "source_classification_discrepancy": "Extracted source-table stream labels give 146 sporadic +46 stream-associated events; the 2024 observing-rate Table2 gives 145+47. Do not silently relabel a flash or renormalize the published rates.",
    "exposure": {"validated_events": 192, "usable_hours": 283.4, "sporadic_hours": 237.8, "stream_hours": 45.6,
                 "approximate_area_km2": area, "moon_area_km2": moon_area,
                 "approximate_surface_fraction": area / moon_area,
                 "illustrative_calendar_fraction_6p5yr": 283.4 / (6.5 * 365.25 * 24),
                 "rate_sporadic_km2_h": rate_spo, "rate_stream_km2_h": rate_stream,
                 "rate_ratio_stream_sporadic": rate_stream / rate_spo,
                 "ratio_poisson_fractional_sigma": math.sqrt(1/145 + 1/47),
                 "rate_sporadic_fractional_counting_sigma": 1/math.sqrt(145),
                 "rate_stream_fractional_counting_sigma": 1/math.sqrt(47)},
    "study_targets_not_requirements": {
        "band_energy_injection_grid_J": [100, 300, 1000, 3000, 10000, 30000, 100000, 300000, 1000000],
        "band_definition": "Mission 600-900 nm top-hat; NOT identified with source R+I energies",
        "characterize_recovery_above_C95": True,
        "target_relative_selection_uncertainty": 0.05,
        "target_relative_area_time_uncertainty": 0.05,
        "equal_bin_events_for_10pct_rate_ratio_counting_sigma": 200,
        "equal_bin_events_for_3sigma_20pct_rate_difference_approx": 450,
        "microgram_kinetic_example_J_at_20kms": 0.5 * 1e-9 * (20000 ** 2),
    },
    "data_sha256": hashlib.sha256(csv_path.read_bytes()).hexdigest(),
}
(HERE / "energy_distribution_results.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
fig, (ax, bx) = plt.subplots(1, 2, figsize=(10, 4.2), layout="constrained")
display_edges = edges[1:]
ax.stairs(counts[1:], display_edges, fill=True, color="#507b96", alpha=.85)
for a, b, n in zip(display_edges[:-1], display_edges[1:], counts[1:]):
    ax.text(math.sqrt(a*b), int(n)+2, str(n), ha="center", fontsize=9)
ax.set_xscale("log")
ax.set_ylim(0, max(counts)*1.18)
ax.set_xlabel("Integrated R + I optical energy [J]")
ax.set_ylabel("Recorded validated flashes per bin")
ax.set_title("Observed sample: 192 flashes", loc="left", fontweight="bold")
x = np.sort(energies)
survival = np.arange(len(x), 0, -1) / len(x)
for eta, color, label in [(0.005, "#a16c3d", "0.005"), (NOMINAL_ETA, "#233f62", "0.0015"), (0.0005, "#498c78", "0.0005")]:
    bx.step(x/eta, survival, where="pre", color=color, label=f"η = {label}")
bx.set_xscale("log"); bx.set_yscale("log")
bx.set_xlabel("Inferred kinetic energy [J]")
bx.set_ylabel("Fraction of sample at or above energy")
bx.set_title("Same light, three conversion assumptions", loc="left", fontweight="bold", fontsize=10)
bx.legend(frameon=False, fontsize=9)
for axis in (ax, bx):
    axis.grid(axis="y", alpha=.2)
fig.savefig(FIG / "neliota_energy_distribution.png", dpi=200)
fig.savefig(FIG / "neliota_energy_distribution.pdf")
plt.close(fig)
print(json.dumps({"count": len(rows), "optical_quantiles_J": quantiles,
                  "published_KE_range_J": summary["published_nominal_KE_range_J"],
                  "bins": bins, "rounding_exceptions": rounding_audit,
                  "counts_spo_stream": [summary["sporadic_count"], summary["stream_associated_count"]]}, indent=2))
