# Radiation data and numerical provenance

Reviewed 29 October 2026. These datasets distinguish source evidence, digitized published models and this study's calculations. No environment/transport service was run.

| File | Provenance / meaning |
| --- | --- |
| `source_register.csv` | Reviewed sources, conditions, exact locations, URLs and access. Full records: [research_data.json](../../analysis/radiation_environment_research/research_data.json). |
| `nasa_fig10_digitized.csv` | Four NASA dose curves at 1,2,2.54,3,5 mm Al; original raster coordinates, reading allowance and model conditions. |
| `matched_comparison.csv` | Matching published solar-maximum/source-95% Si/Al-sphere ratios only. Reading limits use 0.85/1.15 and 1.15/0.85. |
| `let_reference_readings.csv` | Order-of-magnitude NASA Fig 8 flux above LET10 MeV cm²/mg, after 2.54 mm Al; factor-two reading range, insufficient angular detail for rates. |
| `measurement_comparators.csv` | Separate LRO12.2 rad(Si)/333 days and CRaTER372 microGy/day annualizations; not matched cases. |
| `proton_test_comparator.csv` | Author-reported 64 MeV DAVIS346 beam exposure,1.498e11 p/cm² at 20 krad; no NIEL/lunar-life transfer. |
| `body_occultation.csv` | Isotropic primary scalar solid angle only; no geomagnetic/secondary response. |
| `shield_mass.csv` | Areal Al mass and exact six-wall cube; assumed density 2.7 g/cm³,0.1 m internal side,1 m² bus skin. |
| `sep_incident_screening.csv` | NOAA>=10 MeV thresholds with assumed isotropy and IMX636 footprint; before shielding/response. |
| `quiet_incident_sensitivity.csv` | Hypothetical 4π scalar flux and two-face plane incidence; not measured GCR prediction. |
| `availability_sensitivity.csv` | Assumed exclusion/reset cases; not predicted flight downtime. |

## Raster extraction and checks

Source: Steiner, Caffrey and Barth, NASA/TM-20250006822, July 2025. [NASA PDF](https://ntrs.nasa.gov/api/citations/20250006822/downloads/TM-20250006822.pdf).

Fig 10 is printed p 11 / one-based PDFp 15. Original raster `tmp/radiation_environment_research/fig10-000.png` is 1691×1075 pixels. x=146–1651 maps log 10(mils)=0–4; y=18–842 maps log 10(krad(Si)/year)=7 to-3. The script selects known RGB curve colors in narrow y windows, using median y across a seven-pixel x strip; lunar gray markers are accepted. Positions appear on `fig10_digitization_audit.png`. At 2.54 mm the 2.175 krad/year lunar reading agrees with the printed 2.17 within 1%. The±15% reading allowance is not source-model uncertainty or a confidence interval.

Fig 8 is printed p 9 / PDFp 13, read only to order of magnitude at LET>10. Source image: `fig8-000.png`, page preview:`nasa_fig8.png`. Factor-two reading range; no differential spectrum or rate reconstructed. Complete NASA model/version/epoch inputs are not published.

```bash
pdfimages -f 15 -l 15 -png tmp/radiation_environment_research/sources/nasa_tm_20250006822.pdf tmp/radiation_environment_research/fig10
pdfimages -f 13 -l 13 -png tmp/radiation_environment_research/sources/nasa_tm_20250006822.pdf tmp/radiation_environment_research/fig8
```

Inputs/formulas: [model_inputs.json](../../analysis/radiation_environment_research/model_inputs.json), [calculate.py](../../analysis/radiation_environment_research/calculate.py). Runtime/commands: [analysis README](../../analysis/radiation_environment_research/README.md). Cache hashes: `tmp/radiation_environment_research/source_cache_manifest.json`. No missing selected-device or exact-orbit value is silently filled by a proxy.
