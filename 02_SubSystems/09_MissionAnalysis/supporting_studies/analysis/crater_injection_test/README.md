# Crater-injection test kit (pre-SRR work item 2)

**Purpose.** The impact-energy conversion proposal assumes how often the TriScape200 crater camera, imaging from 300 km with 0.9 m pixels, finds a fresh crater of diameter D by comparing its image with an archived LROC NAC "before" image, and how well it measures D. These two assumptions decide most of the pair yield. They are placeholders in [`joint_model.py`](../flash_crater_models/joint_model.py):

| Quantity | Model | Placeholder values |
|---|---|---|
| Crater confirmation | c(D) = CMAX · Φ((ln D − ln(k · GSD)) / KW) | CMAX = 0.85, k = 3.5 pixels, KW = 0.15, GSD = 0.9 m |
| Diameter error | sd(ln D) = hypot(a, b / D_px) | a = 0.03, b = 0.35 pixels |

This kit measures them on real lunar images. It needs LROC NAC downloads, which our cloud analysis environment cannot make, so the team runs it locally. Everything runs on a laptop with Python 3.10 or newer.

## What the kit does

The kit has three test modes and one summary step:

1. **Injection.** Synthetic fresh craters are rendered into a real NAC image, with shading, shadows and a bright ejecta halo, for the scene's Sun geometry. Both images are then degraded to the crater camera: pixel integration to 0.9 m, the optics' blur, shot and read noise for about 300 electrons per pixel, and the camera's RGB Bayer sampling with demosaicking. The "after" image is compared with the "before" image by a matched filter whose false-alarm rate is set to 0.01 candidates per km², about 0.05 per flash error region. The kit records which craters are found and fits their diameters.
2. **Real new craters.** LROC has published the craters that formed during the LRO mission, with matched before/after NAC image IDs and measured diameters ([new-craters shapefile](https://data.lroc.im-ldi.com/lroc/view_rdr/SHAPEFILE_GLOBAL_NEW_CRATERS), Speyerer et al. 2016). Degrading those real pairs to our camera tests the whole chain without any crater model. This is the strongest test, and the injection results should be checked against it.
3. **Human review.** The kit exports randomised before/after image chips, half of them with an injected crater, and an empty answer sheet. A team member marks the chips that contain a new crater without seeing the key; the kit then scores the answers. This tells us whether a person confirms craters as well as the automated detector.
4. **Summary.** Pools all runs and fits the two curves above. It writes `data/crater_injection_test/results.json` and `crater_test.png` (completeness and diameter error, with the current placeholders for comparison).

## Installation

```
pip install numpy scipy matplotlib tifffile pillow
python crater_test.py selftest --out selftest_output
```

The self-test builds synthetic terrain and runs the full injection chain in about a minute. Its output checks the code only; it is not evidence about the real Moon. The result shipped in `selftest_output/` is noise-limited. At 55° Sun incidence, completeness reaches 50% at k = 3.5 camera pixels (3.2 m), with a width of 0.08 in ln D. The diameter error is about 0.43 px / D_px, with a +2% median bias. c_max is close to 1 because the before and after images are identical apart from noise. Real scenes will lower c_max and probably widen the curve.

## Getting the images

1. Download the new-craters shapefile from the [LROC page](https://data.lroc.im-ldi.com/lroc/view_rdr/SHAPEFILE_GLOBAL_NEW_CRATERS). Its table lists for each crater `lat`, `lon`, `before_img`, `after_img` and `diam_m`. Open the `.dbf` table in any spreadsheet or GIS tool.
2. Pick craters of 2–10 m diameter, spread over mare and highland and over Sun incidence angles of 20–70° (the crater camera's normal imaging mode). About 30 craters is a useful first set.
3. Download the calibrated NAC images (CDRNAC, `.IMG`) for both product IDs, for example through the PDS Geosciences Node's [Lunar Orbital Data Explorer](https://ode.rsl.wustl.edu/moon/pagehelp/Content/Missions_Instruments/LRO/LROC/CDR/CDRNAC.htm). Each NAC image is large (5000 samples by up to 52,224 lines), so keep only the pairs you need. The kit reads PDS3 `.IMG` files directly; GeoTIFF, TIFF and PNG chips also work.
4. Note for each image its pixel scale (about 0.5 m at 50 km altitude; given in the product metadata), the Sun incidence angle and the Sun direction within the image.

For injection runs you can use the same images, or any other NAC images. A **before/after pair with matched lighting** (`--after`) is more realistic than a single image, because it includes real registration and illumination differences.

The [flash and crater models](../flash_crater_models/) and [their inputs](../../data/flash_crater_models/) are used by the yield and lunar-texture calculations.

## Geometry conventions

- `--gsd`: source pixel scale in metres.
- `--inc`: Sun incidence angle from the local vertical, in degrees.
- `--az`: direction towards the Sun within the image, in degrees clockwise from image "up" (decreasing line number).

NAC images are not north-up, so check `--az` by eye. Export a few review chips and compare their injected craters with real craters in the same image: the shadow must fall on the same side.

## Commands

```
# 1. injection into one scene (window of 1.5 km around a chosen centre)
python crater_test.py inject --before M1234567890RC.IMG --after M1345678901RC.IMG --gsd 0.52 --inc 48 --az 95 \
       --chip 21000 2500 --out runs/site01

# 2. real new craters: fill in real_craters.csv (template below), one row per crater
python crater_test.py real --list real_craters.csv --out runs/real

# 3. human review: export 120 chips, fill in runs/site01/review/my_answers.csv, then score
python crater_test.py review-export --before M1234567890RC.IMG --gsd 0.52 --inc 48 --az 95 --chip 21000 2500 --out runs/site01
python crater_test.py review-score --out runs/site01 --answers runs/site01/review/my_answers.csv

# 4. pooled fit of all runs
python crater_test.py summary --runs runs/site01 runs/site02 runs/real
```

The CSV for real craters (`real_craters_template.csv`) has one row per crater. Line and sample are the crater's pixel position in each image; find them by eye in an image viewer, since the pair shows the new crater. The pixel scale, diameter and Sun geometry come from the shapefile and the image metadata.

Options for camera sensitivity studies: `--signal-e` (electrons per pixel, default 300), `--read-e` (default 15), `--psf-px` (default 0.6), `--halo-amp` (ejecta brightening, default 0.10; negative for dark halos), `--halo-extent` (radii, default 3), `--depth` and `--rim` (fractions of D, defaults 0.20 and 0.04), `--fa-per-km2` (false-alarm density, default 0.01), `--gsd-dst` (crater-camera pixel, default 0.9; use 0.45 to test imaging from 150 km) and `--no-bayer`.

## Suggested test plan

| Step | Runs | Purpose | Effort |
|---|---|---|---|
| 1 | `selftest` | Check the installation | minutes |
| 2 | Injection into 6–8 NAC scenes (mare and highland; Sun incidence about 25°, 45° and 65°), with `--after` pairs where possible | Completeness and diameter error by terrain and Sun angle | about half a day |
| 3 | 30 real new craters of 2–10 m | Check the injection results against real craters | about one day, mostly image download and locating the craters |
| 4 | Human review of 120 chips by two people | Compare manual confirmation with the automated detector | about one hour per person |
| 5 | `summary` of all runs | Pooled fit of CMAX, k, KW, a and b | minutes |

**Using the result.** Enter the fitted values in `joint_model.py` (`CMAX`, `KW`, the default `k=3.5`, and the diameter error `np.hypot(0.03, 0.35 / Dpx)`). Then rerun `python joint_model.py yields` and the fits, and update the proposal's yield and precision tables. If the real-crater completeness at 3–4 m is clearly lower than the injection results, use the real-crater values: they include effects the crater model leaves out.

## First results on real NAC tiles (3 November 2026)

Our analysis environment cannot reach the LROC archive, but a public crater dataset on GitHub contains real calibrated NAC tiles (Yang et al., CraterDANet; GPL-3.0). `real_tiles/real_tiles_run.py` runs the injection mode on the four tiles whose source images have native pixels of 0.60–0.84 m. Sun incidence (62–82°) comes from the LROC observation pages, and the Sun azimuth from a fit to the dataset's labelled craters (`real_tiles/sun_geometry.json`). For fresh craters with depth/diameter 0.14, the centre of the published range, the pooled 50% point is **k = 3.58 px (3.2 m)**, against the placeholder's 3.5 px. The width is 0.10 and the diameter error 0.46 px / D_px. For depth/diameter 0.20 and 0.10, k is 3.26 and 4.19 px. Before and after were the same tile apart from noise, so the plateau (≈0.99) is an upper bound. Results: [crater-test note](../../outputs/crater_test/crater_test_results.md); data in `data/crater_injection_test/`. The real-new-crater mode and the human review remain for the team.

## Real new-crater pairs (3 November 2026)

`real_pairs/` runs the real-crater test on eight catalogued new craters (2.5–9.8 m) whose NAC images the team downloaded to `data/external/NAC_CDR/`. `cut_windows.py` (team computer) cuts the before/after windows. `real_pairs_run.py` registers each pair (global affine fit, then a smooth residual shift field), sets the pair's own threshold for 0.01 false candidates per km² and tests the located craters (`located_craters.json`) with the kit's bowl filter and with a new **reflectance-anomaly detector** (multi-scale Laplacian of Gaussian, both signs). It also measures the craters' reflectance profiles and injects craters with measured-type dark halos into the real pairs. `real_pairs_figures.py` and `real_pairs_yield.py` make the figures and the yield table. Results ([LROC/LOLA follow-up](../../outputs/lroc_lola_update/lroc_lola_update.md), section 3):

- Pairs registered to ≤0.1 NAC pixel have thresholds near the noise-only level. With such registration the 3.2, 4.0 and 6.2 m craters are found in every repeat; two pairs at 0.12–0.16 pixels have twice the threshold, and three pairs could not be registered well enough.
- Four of five located new craters have **dark** halos (−6 to −12%, extending to 2–4 D), not the bright halo of the kit's crater model; the bowl filter misses the dark ones below 4 m.
- Injection with dark halos into the well-registered pairs: 50% at **3.63 px (3.3 m)**, width 0.21, plateau 1.0; over all five usable pairs the plateau is 0.68.

Run `real_pairs_run.py` with `python -I` (about 1–2 hours on two cores). For the human review, use only well-registered pairs.

## Limitations

- **Crater model.** The injected crater is a fresh simple bowl (depth 0.2 D, rim 0.04 D) with a bright halo of +10% out to 3 radii, on locally flat ground, with Lunar-Lambert photometry. Real fresh craters vary in depth, rim shape and halo brightness; four of the five real new craters tested on 3 November 2026 have dark halos (use `--halo-amp -0.08 --halo-extent 6` for that type).
- **Images and noise.** Noise, blur and Bayer sampling follow the TriScape200 class (3.2 µm pixels, 1067 mm focal length, RGB Bayer) with stated assumptions; no measured image-quality data are used.
- **Detection.** The matched filter uses the known Sun geometry; a human reviewer may do better or worse, which is what step 4 tests.
- **Registration and lighting.** With a single image, the before and after differ only by noise, so the result is an upper bound. Matched-lighting pairs and the real-crater mode include real differences.
- **Sun angle matters.** In the synthetic tests a 4 m crater at 50° incidence was close to the threshold but was found reliably at 55°. Runs must therefore span the 20–70° range of the imaging mode.

## Files

- `crater_test.py`: the kit (all modes).
- `real_craters_template.csv`: input template for the real-crater mode.
- `selftest_output/`: the shipped self-test result (synthetic terrain; code check only).
- `real_tiles/`: runner and fitted Sun geometry for the real-tile test (data are downloaded separately with `git clone`; run with `python -I`).
- `real_pairs/`: real new-crater pairs (metadata, window cutter, runner, figures, yield).
