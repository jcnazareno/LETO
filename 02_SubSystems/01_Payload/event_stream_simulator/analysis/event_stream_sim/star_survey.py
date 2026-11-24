"""Stars behind the limb, geometric survey (11 Nov 2026): for the limb scene crop, which BSC5 stars are visible in
the sky part of the crop during a run, as a function of the assumed season (Sun ecliptic longitude). No pixel
simulation; uses the scene camera, occultation test and star brightness of eventsim/stars.py.

  python star_survey.py [--scene limb] [--duration 20]

Writes data/stars/star_survey_<scene>.json and figures/stars/star_survey_<scene>.png.
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from run_sim import load_profiles, DATA, FIG       # noqa: E402
from eventsim import scenes, stars                  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--scene', default='limb')
    ap.add_argument('--duration', type=float, default=20.0)
    a = ap.parse_args()
    P = load_profiles('imx636', sets=['env.stars.enabled=false'])
    sc = scenes.build(a.scene, P['sensor'], P['optics'], P['env'], duration=a.duration)
    x0, y0, w, h = sc.crop
    cc, rr = np.meshgrid(np.arange(x0, x0 + w) + 0.5, np.arange(y0, y0 + h) + 0.5)
    sky_frac = float((~sc.cam.cast(cc, rr, a.duration / 2)[1]).mean())
    rows = []
    for lam in range(0, 360, 5):
        P['env'].set('stars.sun_ecliptic_lon_deg', float(lam))
        sf = stars.StarField(sc.cam, sc.rad, P['sensor'], P['optics'], P['env'], sc.crop, a.duration,
                             sc.meta['subsolar_latlon'], lambda c, r, t: sc.cam.cast(c, r, t)[1])
        vis = []
        for k in range(len(sf.d0)):
            seen = False
            for t in np.linspace(0, a.duration, 41):
                c, r, v = sf._project(sf.d0[k:k + 1], t)
                if v[0] and x0 <= c[0] < x0 + w and y0 <= r[0] < y0 + h:
                    seen = True; break
            if seen:
                vis.append(dict(V=float(sf.mag[k]), e_s=float(sf.flux[k])))
        rows.append(dict(sun_ecliptic_lon_deg=lam, n_visible=len(vis),
                         brightest_V=min((v['V'] for v in vis), default=None),
                         brightest_e_s=max((v['e_s'] for v in vis), default=0.0), stars=vis))
    out = dict(scene=a.scene, crop=list(sc.crop), duration_s=a.duration, sky_fraction_of_crop=sky_frac,
               note='BSC5 stars visible (not occulted, inside the crop) at any of 41 times during the run, per assumed '
                    'Sun ecliptic longitude; brightness from eventsim/stars.py (600-900 nm, electrons/s for the whole star).',
               star_V0_e_s=float(P['env']['sun.irradiance_W_m2'] * P['env']['band.solar_fraction']
                                 * 10 ** (-0.4 * (0 - stars.V_SUN)) * sc.rad.A_ap * sc.rad.T * sc.rad.qe / sc.rad.e_ph),
               rows=rows)
    d = DATA / 'stars'; d.mkdir(exist_ok=True); f = FIG / 'stars'; f.mkdir(exist_ok=True)
    (d / f'star_survey_{a.scene}.json').write_text(json.dumps(out, indent=1))
    lam = [r['sun_ecliptic_lon_deg'] for r in rows]
    fig, ax = plt.subplots(2, 1, figsize=(9, 5.5), sharex=True)
    ax[0].bar(lam, [r['n_visible'] for r in rows], width=4, color='#2a78d6')
    ax[0].set_ylabel('BSC5 stars in crop sky'); ax[0].grid(alpha=.25, lw=.5)
    bv = [r['brightest_V'] if r['brightest_V'] is not None else np.nan for r in rows]
    ax[1].plot(lam, bv, 'o', c='#eb6834', ms=4)
    ax[1].invert_yaxis(); ax[1].set_ylabel('brightest star V [mag]'); ax[1].grid(alpha=.25, lw=.5)
    ax[1].set_xlabel('assumed Sun ecliptic longitude (season) [deg]')
    fig.suptitle(f'Stars behind the limb, {a.scene} crop {w}×{h} px ({100 * sky_frac:.0f}% sky), {a.duration:g} s run '
                 f'(geometry only; V = 0 gives {out["star_V0_e_s"]:.2g} e⁻/s)', fontsize=9)
    fig.tight_layout(); fig.savefig(f / f'star_survey_{a.scene}.png', dpi=150); plt.close(fig)
    nv = np.array([r['n_visible'] for r in rows])
    print(f'sky fraction {sky_frac:.2f}; V=0 star {out["star_V0_e_s"]:.3g} e-/s; stars visible per season: '
          f'median {np.median(nv):.0f}, max {nv.max()}; seasons with a star brighter than V=3: '
          f'{sum(1 for r in rows if r["brightest_V"] is not None and r["brightest_V"] < 3)} of {len(rows)}')


if __name__ == '__main__':
    main()
