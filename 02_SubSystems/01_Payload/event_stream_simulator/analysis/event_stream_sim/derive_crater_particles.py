"""Particle environment per IMX636 pixel from LRO CRaTER Level-2 data (4 Nov 2026 update, stage 2).

Inputs : data/crater/crater_<yyyyddd>.json, reduced on the team computer from the PDS Level-2
         PRI/SEC files in data/external/CRATER. The reduction script (s2_crater_extract.py, formerly under tmp/)
         is no longer in the workspace; the reduced files are the maintained inputs of this derivation. Days: 2019-340/341 (6-7 Dec 2019, solar minimum) and 2024-337/338 (2-3 Dec 2024, near the
         cycle-25 maximum); quiet days (D2 singles constant within +-2% hour to hour).
Output : data/crater_particles.json (values entered in profiles/environment.json) and
         figures/crater_particles.png.
Usage  : python derive_crater_particles.py

Method (every conversion assumption is listed in ASSUMPTIONS below and in the output file):
  1. Rate. Hits per cm^2 of a flat sensor per second.
     a. Singles: D2 singles counter (thick, 1000 um, 35 mm diameter, threshold ~35 keV; Spence et al. 2010,
        Sects. 3.1.4, 3.3.3) divided by the detector area 9.62 cm^2. A flat detector in an isotropic flux counts
        2 pi I per cm^2 (both faces). This includes everything that deposits >35 keV in 1 mm Si (also secondaries
        and lunar albedo particles); used as the nominal (upper) value.
     b. Telescope: D2&D4&D6 coincidences (geometry of D1.D6, G = 0.569 cm^2 sr, Spence et al. 2010 Table 5)
        give the zenith intensity I of particles that penetrate ~8 g/cm^2 of TEP; 2 pi I is a lower value.
     c. Moon shadow. For a nadir-facing plate at altitude h the Moon (half-angle a, sin a = R/(R+h)) blocks the
        cos-weighted part pi I sin^2 a, so the rate is 2 pi I (1 - sin^2 a / 2). CRaTER's D2 faces nadir
        (detector axis zenith-nadir). Singles are corrected second by second with LRO's altitude from MOONVEC
        and rescaled to 3000 km. The telescope looks at zenith (unblocked), so only the 3000 km factor applies.
  2. LET spectrum. D2 LET (keV/um = deposit / 1000 um) of D2&D4 events (field ~27 deg half angle, path factor
     1.00-1.12) is the nominal spectrum; all D2 events (wide field, path factor up to ~3) give an upper bound.
     The D2 LLD (~7 ADU, 0.21 keV/um) cuts the low side of the minimum-ionising peak.
  3. Charge per pixel. Monte Carlo of straight tracks through a sensitive layer of depth d under a 4.86 um pitch:
     cos-weighted isotropic directions on the plate, uniform entry point, chord per pixel column, charge =
     LET x chord / (3.6 eV) x thin-layer straggling (lognormal, sigma_ln 0.5), no diffusion.
"""
from __future__ import annotations
import json
import math
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DATA = ROOT / 'data'
IN = DATA / 'crater'
FIG = ROOT / 'figures'
R_MOON = 1737.4
H_ORBIT = 3000.0
A_DET = math.pi * 1.75 ** 2          # cm^2, 35 mm diameter
G_TEL = 0.569                        # cm^2 sr, D1.D6 (D2.D6 is 0.15 mm shorter; difference neglected)

ASSUMPTIONS = {
    'sensitive_depth_um': dict(value=3.0, range=[2.0, 6.0], status='assumed',
                               note='IMX636 is a stacked back-illuminated sensor; the photodiode depth is not published. 3 um gives 320 e- for the CRaTER MIP peak (0.38 keV/um), close to the former 300 e- assumption.'),
    'pixel_pitch_um': dict(value=4.86, status='datasheet', note='Sony IMX636 flyer'),
    'e_per_pair_eV': dict(value=3.6, range=[3.6, 3.65], status='published', note='silicon, room temperature'),
    'straggling_sigma_ln': dict(value=0.5, range=[0.3, 0.8], status='assumed',
                                note='energy-loss straggling in a few-um layer is much wider than in CRaTER\'s 1 mm; lognormal stand-in'),
    'angular_distribution': dict(value='isotropic, cos-weighted on the sensor plane', status='assumed',
                                 note='omnidirectional GCR; spacecraft shielding treated as isotropic'),
    'shielding': dict(value='as CRaTER D2 (0.81 mm Al end cap plus LRO structure)', status='assumed',
                      note='GCR above ~100 MeV dominates; the spectrum is not transported through the camera housing'),
    'diffusion': dict(value='none (charge stays in the crossed pixel columns)', status='assumed'),
    'albedo_particles': dict(value='included in the singles rate at LRO altitude, not rescaled', status='assumed',
                             note='lunar albedo protons and secondaries are a few percent; scaling them as GCR slightly overstates them at 3000 km'),
    'telescope_geometry': dict(value='D2&D4&D6 coincidence treated as D1.D6 (G = 0.569 cm^2 sr)', status='derived',
                               note='thin-detector flags are set on every event and cannot define D1 coincidences'),
    'nuclear_interactions': dict(value='LET tail above ~2 keV/um includes interaction products in 1 mm Si', status='assumed',
                                 note='the per-um interaction probability is far lower in a 3 um layer, so the tail is an upper bound for the pixel'),
}

EPOCHS = {'solar_min': ['2019340', '2019341'], 'solar_max': ['2024337', '2024338']}
EPOCH_LABEL = {'solar_min': '6-7 Dec 2019 (cycle 24/25 minimum)', 'solar_max': '2-3 Dec 2024 (near cycle 25 maximum)'}


def plate_factor(h_km):
    s = R_MOON / (R_MOON + np.asarray(h_km, float))
    return 1 - s ** 2 / 2


def mc_deposits(let_edges, hist, n, rng, depth_um, pitch_um=4.86, eps_eV=3.6, sig=0.5, max_px=400):
    """Sample n hits: returns per-hit LET, angle, pixel count and per-pixel charges (list of arrays)."""
    p = hist / hist.sum()
    k = rng.choice(len(p), size=n, p=p)
    let = np.exp(rng.uniform(np.log(let_edges[k]), np.log(let_edges[k + 1])))        # keV/um, log-uniform in bin
    cos_t = np.sqrt(rng.random(n)); sin_t = np.sqrt(1 - cos_t ** 2)
    phi = rng.uniform(0, 2 * np.pi, n)
    x0, y0 = rng.random(n), rng.random(n)                                                # entry inside pixel (0,0)
    horiz = np.minimum(depth_um * sin_t / np.maximum(cos_t, 1e-6) / pitch_um, max_px)   # horizontal length in px
    out = []
    for i in range(n):
        L = horiz[i]
        if L < 1e-6:
            chords = np.array([depth_um / cos_t[i]])
        else:
            dx, dy = math.cos(phi[i]), math.sin(phi[i])
            # parameter values where the projected track crosses pixel boundaries
            ts = [0.0, L]
            for d0, dd in ((x0[i], dx), (y0[i], dy)):
                if abs(dd) > 1e-12:
                    lo, hi = sorted((d0, d0 + dd * L))
                    for b in range(int(math.floor(lo)) + 1, int(math.ceil(hi))):
                        ts.append((b - d0) / dd)
            ts = np.unique(np.clip(ts, 0, L))
            seg = np.diff(ts)
            seg = seg[seg > 1e-9]
            chords = seg / L * (depth_um / cos_t[i])                                     # 3D chord per pixel (um)
        q = let[i] * 1e3 / eps_eV * chords * np.exp(rng.normal(0, sig, len(chords)))
        out.append(q)
    return let, cos_t, out


def main():
    rng = np.random.default_rng(20261104)
    res = dict(created='2026-11-04', inputs=[f'crater_{d}.json' for v in EPOCHS.values() for d in v],
               source='LRO CRaTER Level-2 (PDS PPI lro-crater, data-der-pri/-sec, V01); geometry Spence et al. 2010, Space Sci. Rev. 150, 243-284',
               assumptions=ASSUMPTIONS, orbit_altitude_km=H_ORBIT, plate_factor_3000km=float(plate_factor(H_ORBIT)), epochs={})
    f3000 = float(plate_factor(H_ORBIT))
    for ep, days in EPOCHS.items():
        R = [json.loads((IN / f'crater_{d}.json').read_text()) for d in days]
        live = sum(r['live_s'] for r in R)
        singles = sum(r['singles_sum'][1] for r in R) / live / A_DET                     # cm^-2 s^-1 at LRO
        tpl = sum(r['mean_tplate'] * r['live_s'] for r in R) / live
        tel = sum(r['n_d2d4d6'] for r in R) / live                                      # counts/s
        I = tel / G_TEL
        rate_singles = singles / tpl * f3000
        rate_tel = 2 * math.pi * I * f3000
        # day-to-day spread as a statistical/variability indicator
        per_day = [r['singles_sum'][1] / r['live_s'] / A_DET / r['mean_tplate'] * f3000 for r in R]
        edges = np.array(R[0]['let_edges_keV_um'])
        h_nom = np.sum([r['hist_let_d2_d2d4'] for r in R], 0); h_any = np.sum([r['hist_let_d2_any'] for r in R], 0)
        ccdf = lambda h: (np.cumsum(h[::-1])[::-1] / h.sum())
        # Monte Carlo of pixel charges for the nominal depth and the depth range
        mcs = {}
        for d in (2.0, 3.0, 6.0):
            for lab, h in (('nominal', h_nom), ('wide_field', h_any)):
                if lab == 'wide_field' and d != 3.0:
                    continue
                let, ct, q = mc_deposits(edges, h, 40000, rng, d)
                qmax = np.array([x.max() for x in q]); npx = np.array([len(x) for x in q]); qall = np.concatenate(q)
                mcs[f'{lab}_d{d:g}um'] = dict(
                    depth_um=d, spectrum=lab, median_pixel_charge_e=float(np.median(qall)),
                    pixel_charge_percentiles_e={p: float(np.percentile(qall, p)) for p in (10, 50, 90, 99, 99.9)},
                    fraction_hits_max_pixel_gt_2000e=float((qmax > 2e3).mean()),
                    fraction_hits_max_pixel_gt_1e4e=float((qmax > 1e4).mean()),
                    fraction_hits_max_pixel_gt_1e5e=float((qmax > 1e5).mean()),
                    pixels_per_hit_percentiles={p: float(np.percentile(npx, p)) for p in (50, 90, 99)},
                    mean_pixels_per_hit=float(npx.mean()))
        res['epochs'][ep] = dict(
            label=EPOCH_LABEL[ep], days=days, live_s=live,
            lro_altitude_km=[min(r['alt_km']['min'] for r in R), float(np.median([r['alt_km']['median'] for r in R])), max(r['alt_km']['max'] for r in R)],
            lro_plate_factor=tpl,
            singles_d2_cm2_s_at_lro=singles, telescope_counts_s=tel, telescope_intensity_cm2_s_sr=I,
            hit_rate_3000km_cm2_s=dict(nominal_singles=rate_singles, lower_telescope=rate_tel, per_day_singles=per_day),
            let_edges_keV_um=edges.tolist(), let_hist_d2d4=h_nom.tolist(), let_hist_d2_any=h_any.tolist(),
            let_ccdf_at={str(x): float(ccdf(h_nom)[np.searchsorted(edges, x) if np.searchsorted(edges, x) < len(h_nom) else -1]) for x in (0.5, 1, 2, 5, 10, 30)},
            pixel_mc=mcs)
        m = mcs['nominal_d3um']
        print(f"{ep}: LRO alt {res['epochs'][ep]['lro_altitude_km']}, plate {tpl:.3f}; 3000 km hits/cm2/s singles {rate_singles:.2f} "
              f"(days {', '.join(f'{x:.2f}' for x in per_day)}), telescope {rate_tel:.2f}; median pixel charge {m['median_pixel_charge_e']:.0f} e-, "
              f">2e3 e- {m['fraction_hits_max_pixel_gt_2000e']:.3f}, >1e4 {m['fraction_hits_max_pixel_gt_1e4e']:.4f}, px/hit p50/p90/p99 "
              f"{m['pixels_per_hit_percentiles']}")
    (DATA / 'crater_particles.json').write_text(json.dumps(res, indent=1))
    # figure: LET CCDF and pixel-charge CCDF
    try:
        import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
        fig, ax = plt.subplots(1, 2, figsize=(10, 3.8))
        for ep, c in (('solar_min', '#1f5fa8'), ('solar_max', '#c0392b')):
            E = res['epochs'][ep]; e = np.array(E['let_edges_keV_um'])
            for k, ls in (('let_hist_d2d4', '-'), ('let_hist_d2_any', ':')):
                h = np.array(E[k]); ax[0].step(e[:-1], np.cumsum(h[::-1])[::-1] / h.sum(), where='post', color=c, ls=ls,
                                                label=f"{ep.replace('_', ' ')}, {'D2&D4' if k.endswith('d2d4') else 'all D2'}")
        ax[0].set(xscale='log', yscale='log', xlabel='LET in Si [keV/µm] (D2)', ylabel='fraction of hits above', ylim=(1e-5, 1.2))
        ax[0].legend(fontsize=8); ax[0].grid(alpha=0.3)
        for ep, c in (('solar_min', '#1f5fa8'), ('solar_max', '#c0392b')):
            E = res['epochs'][ep]; e = np.array(E['let_edges_keV_um']); h = np.array(E['let_hist_d2d4'])
            _, _, q = mc_deposits(e, h, 20000, np.random.default_rng(5), 3.0)
            qm = np.sort(np.array([x.max() for x in q]))
            ax[1].plot(qm, 1 - np.arange(len(qm)) / len(qm), color=c, label=f"{ep.replace('_', ' ')}: {E['hit_rate_3000km_cm2_s']['nominal_singles']:.2f} hits cm⁻² s⁻¹")
        ax[1].axvline(2e3, color='0.5', ls='--', lw=0.8); ax[1].text(2.1e3, 0.5, 'former "heavy" range', fontsize=7, color='0.4')
        ax[1].set(xscale='log', yscale='log', xlabel='largest charge per pixel in a hit [e⁻] (3 µm layer)', ylabel='fraction of hits above', ylim=(1e-5, 1.2))
        ax[1].legend(fontsize=8); ax[1].grid(alpha=0.3)
        fig.tight_layout(); FIG.mkdir(parents=True, exist_ok=True); fig.savefig(FIG / 'crater_particles.png', dpi=130)
    except Exception as ex:   # figure is optional
        print('figure skipped:', ex)


if __name__ == '__main__':
    main()
