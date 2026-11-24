# Lunar impact-energy research data

**Reproduction status, 29 October 2026:** the command and library versions below record the 28 October Windows analysis run. The relocated `.conda/python.exe` has not been reverified as a Linux runtime. See the [analysis README relocation limits](../../analysis/d01_d04_research/README.md) before rebuilding. This documentation pass did not regenerate the catalogue, plots or source audit; the two source discrepancies below remain evidence gaps.

Reviewed **28 October 2026**. These are transcribed published estimates, not new telescope measurements. The report introduction §§1.5–1.6 explains the interpretation; the [workbook](../../outputs/d01_d04_research_2026-10-28/d01_d04_research.xlsx) includes the distribution and every event.

## Population and provenance

The CSV and equivalent JSON contain **192 validated NELIOTA flashes**, observed from 2017 through August 2023. They combine 79 rows from [Liakos et al. (2020), author v1](https://arxiv.org/pdf/1911.06101v1), Tables 4–5, PDF pp18–19, and 113 rows from [Liakos et al. (2024), author v1](https://arxiv.org/pdf/2403.19613v1), Table A.2, PDF pp19–21. Suspected/unconfirmed events are excluded. This is the complete compilation of those validated tables; it is **not a complete lunar population or complete energy interval**, nor a claim to include every survey or every later detection. Journal PDF downloads failed; the precise author versions are retained.

Each row preserves the source ID, table, one-based PDF page, SHA-256 and original numeric tokens. R/I energies and quoted errors are converted from ×10⁴ J into joules. Parenthesized errors refer to the last digits, except explicitly decimal errors such as `116.4(3.5)`. No covariance between R and I is published in these tables, so a combined optical-energy uncertainty is not invented.

The 2020 last kinetic-energy column is **×10⁷ J**; the corresponding 2024 column is **×10⁶ J**. All three converted kinetic scenarios agree with the sum of the optical energies within the rounding precision of the source tokens. Source headers, faintest/brightest rows and representative entries were checked in the PDF images. Energies are hemispheric-equivalent integrated source R and I bands, not bolometric energy and not the mission's provisional 600–900 nm band.

## Reproduction and definitions

Run the [analysis script](../../analysis/d01_d04_research/calculate_energy_distribution.py) from the workspace root:

```powershell
& 'C:/Users/gordo/Desktop/SMD/analysis/v2e/.conda/python.exe' -X utf8 analysis/d01_d04_research/calculate_energy_distribution.py
```

It uses the existing NumPy 1.26.4 / Matplotlib 3.10.9 environment only for analysis/plotting; it does not run or change v2e. The source text cache is produced with the bundled Python and pypdf by `collect_sources.py --remote-only --only liakos_2020 liakos_2024`. Full commands are in the [analysis README](../../analysis/d01_d04_research/README.md).

Expected outputs: CSV/JSON catalogue here; `energy_distribution_results.json` under the analysis directory; PNG/PDF figures under `figures/lunar_impact_energy/`. Quantiles use NumPy's linear interpolation of the rounded source optical energies. Histogram bins are lower-inclusive, upper-exclusive and **unequal in width**. Counts are 0,27,88,53,15,9 in [0,4k), [4k,10k), [10k,30k), [30k,100k), [100k,300k), [300k,1M) J. Do not interpret a bin-count maximum as a physical peak in the underlying population.

The cumulative figure maps the same optical sample using K=(R+I)/η for three common η values. Curves represent conversion assumptions, **not independent samples or confidence intervals**. Published kinetic estimates are preserved separately because source rounding can produce slightly different values. Photon band, emission direction and η must be matched before comparing another instrument or converting to kinetic energy. Mass further needs an assumed impact speed.

## Retained source discrepancies

1. The 2024 §6 narrative gives 0.8 MJ–1.05 GJ across η scenarios. **Current assessment:** that sentence discusses the paper's Fig. 23 (author v1 p. 11), whose points also vary velocity by meteoroid origin; the 2024 Table A.2 maximum at η=0.0005 is 1.027 GJ. The narrative may therefore describe a different sample or convention rather than an error. The retained 2020 table has a **1.164 GJ** maximum (ID97, η=0.0005); its nominal entry is 388±12 MJ. The data preserve the tables and flag the disagreement. This review does not silently reconcile it.
2. The combined source-table stream labels yield **146 sporadic /46 stream-associated** flashes, while 2024 Table 2 normalizes rates with **145/47**. The published exposure/rate comparison retains Table 2. No event is relabelled to force agreement. Reconcile classifications with the authors before fitting source-specific fluxes.

## Limits on inference

No intrinsic power-law slope, lower physical cutoff, complete rate curve or global energy distribution is inferred. Recovering those needs measured detection/confirmation probability, exposure by energy/place/time, saturation and missing-energy bounds, plus emission/η assumptions. The faintest observed row is not a 95%-completeness threshold. The strongest recorded flash and the much larger crater-inferred event are contextual literature records, outside this NELIOTA sample; they are not appended to its histogram.
