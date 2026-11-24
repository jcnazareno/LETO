"""Analytic light-curve examples; optionally prepare cited source-figure excerpts.

Run from the workspace root with bundled Python. Calculations use the standard
library. --figures additionally needs pypdf and pdftoppm. No raw observed light
curve is fitted, no event-sensor simulator is run, and no accuracy is demonstrated.
"""
from pathlib import Path
from math import exp, expm1, log, log10, pi, sqrt
import argparse
import json
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
I = json.loads((HERE / "lightcurve_inputs.json").read_text(encoding="utf-8"))
parser = argparse.ArgumentParser()
parser.add_argument("--figures", action="store_true")
args = parser.parse_args()

drop = I["fast_decline"]
tau_ms = drop["interval_ms"] / (0.4 * log(10) * drop["magnitude_drop"])


def averaged_peak_fraction(interval_ms, decay_ms):
    x = interval_ms / decay_ms
    return -expm1(-x) / x if x else 1.0


lo, hi = 0.0, tau_ms
for _ in range(80):
    mid = (lo + hi) / 2
    if averaged_peak_fraction(mid, tau_ms) >= 1 - I["maximum_averaging_loss_fraction"]:
        lo = mid
    else:
        hi = mid
on_c = log(1 + I["on_fractional_contrast"])
off_c = -log(1 - I["off_fractional_contrast"])
log_ratio = log(I["illustrative_intensity_ratio"])
count = log_ratio / on_c
freq = I["sinusoidal_test_frequency_Hz"]
result = {
    "inputs": I,
    "exponential_interpretation_only": {
        "decay_constant_ms": tau_ms,
        "flux_drop_factor": 10 ** (0.4 * drop["magnitude_drop"]),
        "averaged_peak_fractions": [{"bin_ms": dt, "mean_over_initial_peak": averaged_peak_fraction(dt, tau_ms)} for dt in I["averaging_intervals_ms"]],
        "max_bin_ms_for_5pct_averaging_loss": (lo + hi) / 2,
        "tail_capture_fraction_at_five_tau": -expm1(-5),
        "tail_examples": [{"tau_ms": t, "five_tau_ms": 5 * t, "time_for_98pct_ms": -t * log(0.02)} for t in I["illustrative_exponential_tail_ms"]],
        "relative_colour_ratio_error_at_offset": exp(I["illustrative_interband_offset_ms"] / tau_ms) - 1,
    },
    "ideal_event_example": {
        "on_log_threshold": on_c,
        "off_log_threshold": off_c,
        "events_for_tenfold_rise": count,
        "max_refractory_us_for_log_uniform_rise": I["illustrative_log_rise_duration_ms"] * 1000 / count,
        "events_per_ms_refractory_ceiling": [{"refractory_us": t, "ceiling_per_ms": 1000 / t} for t in I["refractory_periods_us"]],
        "one_missed_on_event_total_intensity_underestimate_fraction": 1 - exp(-on_c),
        "coherent_relative_threshold_error_for_5pct_intensity_bias": log(1 + I["maximum_coherent_intensity_bias_fraction"]) / log_ratio,
        "first_order_lowpass": [{"corner_Hz": f, "time_constant_us": 1e6 / (2 * pi * f), "rise_10_90_us": log(9) * 1e6 / (2 * pi * f), "amplitude_ratio_at_1kHz": 1 / sqrt(1 + (freq / f) ** 2)} for f in I["corner_frequencies_Hz"]],
        "corner_Hz_for_5pct_sinusoidal_gain_loss_at_1kHz": freq / sqrt((1 - I["maximum_gain_loss_fraction"]) ** -2 - 1),
    },
    "magnitude_to_fractional_flux_uncertainty": [{"sigma_magnitude": m, "small_error_sigma_flux_fraction": log(10) / 2.5 * m} for m in I["quoted_magnitude_uncertainties"]],
    "limitations": [
        "Onset-aligned exponential averages illustrate temporal smoothing, not an instantaneous peak measured by E05.",
        "The 38/110 ms E04 parameters belong to cooling models; exponential capture calculations do not reproduce those models.",
        "Ideal event equations apply to total pixel irradiance including background; subtracting an uncertain background can amplify flash error.",
        "Refractory ceilings, thresholds and bandwidth were measured in other illumination regimes; their combination does not certify lunar performance.",
        "A 1 kHz sine test is a calibration case, not a definition of 1 ms feature recovery.",
    ],
}
# Check dimensional/limiting behaviour and analytic energy closure, not sensor performance.
assert abs(averaged_peak_fraction(1e-6, tau_ms) - 1) < 1e-6
assert abs(averaged_peak_fraction(2 * tau_ms, tau_ms) * 2 - (1 - exp(-2))) < 1e-12
assert all(0 < r["mean_over_initial_peak"] < 1 for r in result["exponential_interpretation_only"]["averaged_peak_fractions"])
assert abs(exp(count * on_c) - I["illustrative_intensity_ratio"]) < 1e-12
target = HERE / "lightcurve_results.json"
target.write_text(json.dumps(result, indent=2), encoding="utf-8")

if args.figures:
    from pypdf import PdfReader, PdfWriter
    fig_dir = ROOT / "figures/d01_d04_lightcurves"
    scratch = ROOT / "tmp/pdfs/d01_d04_report/source_crops"
    fig_dir.mkdir(parents=True, exist_ok=True)
    scratch.mkdir(parents=True, exist_ok=True)
    cache = ROOT / "tmp/d01_d04_research/sources"
    # Pixel boxes reviewed at 110 dpi on the supplied author-v1 PDF, page 7.
    # Crop and rearrange panels without digitising, smoothing, or altering data.
    crops = []
    scale = 110 / 72
    for index, (y0, y1) in enumerate([(399, 552), (555, 708), (711, 865), (868, 1016)], 1):
        reader = PdfReader(cache / "giancono_2026.pdf")
        source = reader.pages[6]
        height = float(source.mediabox.height)
        box = [293 / scale, height - y1 / scale, 655 / scale, height - y0 / scale]
        source.cropbox.lower_left = box[:2]
        source.cropbox.upper_right = box[2:]
        writer = PdfWriter()
        writer.add_page(source)
        pdf = scratch / f"giancono_E{index}.pdf"
        writer.write(pdf)
        stem = fig_dir / f"giancono_E{index}"
        subprocess.run(["pdftoppm", "-f", "1", "-singlefile", "-cropbox", "-r", "180", "-png", str(pdf), str(stem)], check=True)
        crops.append({"output": str(stem.with_suffix(".png").relative_to(ROOT)), "source": "E05", "pdf_page": 7, "figure": 5, "panel": f"E{index}", "crop_pdf_points": box})
    reader = PdfReader(cache / "athanasopoulos_2026.pdf")
    source = reader.pages[2]
    height = float(source.mediabox.height)
    box = [65, height - 195, 530, height - 53]
    source.cropbox.lower_left = box[:2]
    source.cropbox.upper_right = box[2:]
    writer = PdfWriter()
    writer.add_page(source)
    pdf = scratch / "terrain_Fig3.pdf"
    writer.write(pdf)
    stem = fig_dir / "terrain_Fig3"
    subprocess.run(["pdftoppm", "-f", "1", "-singlefile", "-cropbox", "-r", "180", "-png", str(pdf), str(stem)], check=True)
    crops.append({"output": str(stem.with_suffix(".png").relative_to(ROOT)), "source": "E04", "pdf_page": 3, "figure": 3, "crop_pdf_points": box})
    (fig_dir / "source_manifest.json").write_text(json.dumps(crops, indent=2), encoding="utf-8")
print(json.dumps({"output": str(target), "tau_ms": tau_ms, "bin_ms_for_5pct_loss": (lo + hi) / 2, "tenfold_rise_event_count": count, "checks": "limiting behaviour, energy closure, event log-ratio closure", "figures_prepared": args.figures}, indent=2))
