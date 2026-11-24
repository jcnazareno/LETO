"""Deterministic radiometric bounds and a local linear localization budget.

Dependencies: Python standard library only. No event-camera emulator is used.
Inputs: model_inputs.json. Outputs: model_results.json, parameter_sweep.csv.
All fluxes are energy fluxes. Event counts are never equated with photons.
"""
import csv
import json
import math
from pathlib import Path
from statistics import NormalDist

HERE = Path(__file__).resolve().parent
P = json.loads((HERE / "model_inputs.json").read_text(encoding="utf-8"))
H = 6.62607015e-34
C = 299792458.0
KB = 1.380649e-23
ARCSEC = math.pi / (180 * 3600)


def planck(wavelength_m, temperature_K):
    return 2 * H * C**2 / wavelength_m**5 / math.expm1(H * C / (wavelength_m * KB * temperature_K))


def integrate(fn, a, b, steps=1200):
    step = (b - a) / steps
    return step * (0.5 * (fn(a) + fn(b)) + sum(fn(a + i * step) for i in range(1, steps)))


def photon_factor(temperature_K):
    a, b = P["band_min_nm"] * 1e-9, P["band_max_nm"] * 1e-9
    energy = integrate(lambda x: planck(x, temperature_K), a, b)
    photons = integrate(lambda x: planck(x, temperature_K) * x / (H * C), a, b)
    return photons / energy


def photon_budget(range_km, aperture_m, radiance, tau_ms):
    distance_m = range_km * 1000
    area = math.pi * aperture_m**2 / 4
    angular_pixel_rad = P["pixel_pitch_um"] * 1e-6 / P["focal_length_m"]
    omega = P["noise_equivalent_pixels"] * angular_pixel_rad**2
    efficiency = P["effective_photon_detection_fraction"]
    photons_per_J = photon_factor(P["temperature_K"])
    # Radiance is integrated over the study band. Its spectral shape is independently assumed.
    background_rate = radiance * area * omega * efficiency * P["background_effective_wavelength_nm"] * 1e-9 / (H * C)
    tau_s = tau_ms / 1000
    window_s = P["detection_window_ms"] / 1000
    bin_s = P["peak_bin_ms"] / 1000
    reference_s = P["background_reference_ms"] / 1000
    exposure = P["detection_energy_2pi_J"] / (2 * math.pi * distance_m**2)
    electrons_total = exposure * area * efficiency * photons_per_J
    signal_window = electrons_total * (1 - math.exp(-window_s / tau_s))
    background_window = background_rate * window_s
    background_reference_variance = background_rate * window_s**2 / reference_s
    snr_detection = signal_window / math.sqrt(signal_window + background_window + background_reference_variance)
    proxy_snr_required = P["false_alarm_sigma"] + NormalDist().inv_cdf(P["detection_probability"])
    q2 = proxy_snr_required**2
    source_required = (q2 + math.sqrt(q2*q2 + 4*q2*(background_window + background_reference_variance))) / 2
    char_total = electrons_total * P["characterization_energy_2pi_J"] / P["detection_energy_2pi_J"]
    peak_signal = char_total * (1 - math.exp(-bin_s / tau_s))
    peak_variance = peak_signal + background_rate * bin_s + background_rate * bin_s**2 / reference_s
    snr_peak = peak_signal / math.sqrt(peak_variance)
    return dict(range_km=range_km, aperture_m=aperture_m, background_band_radiance_W_m2_sr=radiance,
                decay_constant_ms=tau_ms, photons_per_J=photons_per_J,
                radiant_exposure_J_m2=exposure, source_electrons_total=electrons_total,
                source_electrons_window=signal_window, background_electrons_s=background_rate,
                background_electrons_window=background_window, background_reference_variance=background_reference_variance,
                snr_detection=snr_detection, proxy_threshold_energy_J=source_required / signal_window * P["detection_energy_2pi_J"], characterization_electrons_peak_bin=peak_signal,
                snr_characterization_peak_bin=snr_peak, peak_statistical_fractional_uncertainty=1/snr_peak)


def localization(emission_deg):
    # Tangent-plane, independent Gaussian allocations. Emission is local angle from the surface normal.
    e = math.radians(emission_deg)
    angular_pixel = P["pixel_pitch_um"] * 1e-6 / P["focal_length_m"] / ARCSEC
    angular_sigma = math.sqrt((P["centroid_sigma_px"] * angular_pixel)**2 + P["attitude_sigma_arcsec"]**2
                              + P["boresight_sigma_arcsec"]**2 + P["residual_jitter_sigma_arcsec"]**2)
    angular_ground_sigma_km = P["range_km"] * angular_sigma * ARCSEC
    common_variance = angular_ground_sigma_km**2 + P["orbit_horizontal_sigma_km"]**2
    major_sigma = math.sqrt(common_variance / math.cos(e)**2 + P["map_horizontal_sigma_km"]**2
                            + (P["topography_height_sigma_km"] * math.tan(e))**2)
    minor_sigma = math.sqrt(common_variance + P["map_horizontal_sigma_km"]**2)
    k95 = math.sqrt(-2 * math.log(1-P["horizontal_confidence"]))
    return dict(emission_deg=emission_deg, angular_sigma_arcsec=angular_sigma, major95_km=k95*major_sigma,
                minor95_km=k95*minor_sigma, area95_km2=math.pi*k95**2*major_sigma*minor_sigma)


base = photon_budget(P["range_km"], P["aperture_m"], P["background_band_radiance_W_m2_sr"], P["decay_constant_ms"])
pixel_angle = P["pixel_pitch_um"] * 1e-6 / P["focal_length_m"]
pixel_area = (P["pixel_pitch_um"] * 1e-6)**2
max_chip_irradiance = (P["characterization_energy_2pi_J"] / (2*math.pi*(P["range_km"]*1000)**2)
                       / (P["decay_constant_ms"] / 1000) * math.pi*P["aperture_m"]**2/4
                       * P["optical_transmission_for_lux_bound"] / pixel_area)
background_chip_irradiance = P["background_band_radiance_W_m2_sr"] * pixel_angle**2 * math.pi*P["aperture_m"]**2/4 * P["optical_transmission_for_lux_bound"] / pixel_area
trials_h = P["sensor_width_px"] * P["sensor_height_px"] * 3600 / (P["peak_bin_ms"] / 1000)
tail = 0.5 * math.erfc(P["false_alarm_sigma"] / math.sqrt(2))
results = {
    "inputs": P,
    "base_photon_budget": base,
    "survey_option": {"characterization_energy_2pi_J": 3000, "peak_bin_ms": 5},
    "pixel_angle_arcsec": pixel_angle/ARCSEC,
    "pixel_ground_scale_km": P["range_km"]*pixel_angle,
    "f_number": P["focal_length_m"] / P["aperture_m"],
    "fov_width_deg": math.degrees(2*math.atan(P["sensor_width_px"] * P["pixel_pitch_um"]*1e-6 / (2*P["focal_length_m"]))),
    "fov_height_deg": math.degrees(2*math.atan(P["sensor_height_px"] * P["pixel_pitch_um"]*1e-6 / (2*P["focal_length_m"]))),
    "spectral_photons_per_J": [{"temperature_K": t, "photons_per_J": photon_factor(t)} for t in [2000,3000,4500]],
    "earth_exposure_detection_J_m2": P["detection_energy_2pi_J"] / (2*math.pi*(P["earth_reference_range_km"]*1000)**2),
    "minimum_expected_snr_gaussian_proxy": P["false_alarm_sigma"] + NormalDist().inv_cdf(P["detection_probability"]),
    "gaussian_trials_h": trials_h,
    "gaussian_false_trials_h_at_8sigma": trials_h * tail,
    "gaussian_false_trials_h_at_5sigma": trials_h * 0.5 * math.erfc(5/math.sqrt(2)),
    "max_single_pixel_chip_lux_bound": 683*(max_chip_irradiance + background_chip_irradiance),
    "light_time_s": P["range_km"]*1000/C,
    "localization": [localization(e) for e in [0,30,60,70,80]],
    "terrain_search_area_limit_km2": math.pi*5**2,
    "crater_search_area_limit_km2": math.pi,
    "energy_rss_fraction": math.sqrt(sum(x*x for x in P["energy_uncertainty_allocations"].values())),
    "peak_rss_fraction": math.sqrt(sum(x*x for x in P["peak_uncertainty_allocations"].values())),
    "source_coordinate_error_arc_km": P["moon_radius_km"] * math.radians(0.5),
    "sample_per_group_for_30pct_difference_3sigma_poisson": math.ceil(2*(3/0.3)**2),
}
rows = [photon_budget(r,d,b,t) for r in [10000,50000,80000]
        for d in [0.05,0.1,0.2] for b in [1e-5,1e-3,1e-2] for t in [10,100]]
(HERE / "model_results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
with (HERE / "parameter_sweep.csv").open("w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(file, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)
print(json.dumps({k:v for k,v in results.items() if k not in ["inputs"]}, indent=2))
