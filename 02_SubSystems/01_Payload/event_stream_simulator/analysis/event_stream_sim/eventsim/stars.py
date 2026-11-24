"""Stars beyond the limb (handoff 2026-11-11 item 3.4, 11 Nov 2026).

Catalogue: Yale Bright Star Catalogue, 5th rev. ed. (Hoffleit & Warren 1991, CDS V/50), J2000 positions, V and B-V,
read from data/external/BSC5/catalog.gz (9110 objects to V ~ 6.5; proper motion ignored).

Frame: the simulator's Moon-fixed frame has the Earth on +x (no libration) and its z axis is taken as the ecliptic
north pole (the 1.5 deg tilt of the lunar equator is ignored). Seen from the Moon, the Earth's ecliptic longitude is
lambda_E = lambda_sun - lon_subsolar, where lon_subsolar is the scene preset's sub-solar longitude and lambda_sun
the Sun's ecliptic longitude (env stars.sun_ecliptic_lon_deg, an assumption: the season of the observation). A star
at ecliptic (lambda, beta) then has Moon-fixed longitude lambda - lambda_E - w_moon t and latitude beta.

Brightness in the 600-900 nm band, scaled from the Sun through the same chain as the sunlit scene:
  E_star = sun.irradiance * band.solar_fraction * 10^(-0.4 (V - V_sun)) * c(B-V),
V_sun = -26.76 (Willmer 2018, ApJS 236, 47, Table 3, Johnson V, Vega). c is a black-body colour term: the
600-900 nm to V-band flux ratio of a black body at T(B-V), relative to the Sun's, with T(B-V) from Ballesteros
(2012, EPL 97, 34008, Eq. 14) and the solar B-V = 0.65 (assumed); the V band is approximated as a Gaussian centred at
551 nm with 88 nm FWHM. Electrons: E_star / e_ph(750 nm) * aperture area * transmission * QE (as for flashes), spread
by the PSF (core and halo, erf integrals) and scaled by the point-source field gain (cos theta).

Occultation: a star is hidden when the ray from the spacecraft in its direction meets the lunar sphere.
Test stars (env stars.test_mags): extra stars of the given V magnitudes (B-V 0.65), placed at random sky pixels of
the crop at mid-run (seed stars.test_seed), defined as fixed inertial directions so that they drift like real stars.
stars.test_place = 'limb' instead puts them next to the limb so that each rises or sets during the run.
"""
from __future__ import annotations
import gzip
import math
from pathlib import Path
import numpy as np
from scipy.special import erf

ROOT = Path(__file__).resolve().parents[3]
BSC5 = ROOT / 'data' / 'external' / 'BSC5' / 'catalog.gz'
V_SUN = -26.76
BV_SUN = 0.65
EPS_J2000 = math.radians(23.4392911)
H, C, KB = 6.62607015e-34, 2.99792458e8, 1.380649e-23


def load_bsc5(path=BSC5):
    """RA, Dec [rad], V, B-V (NaN if missing) for the catalogue entries with a position and V."""
    ra, de, v, bv = [], [], [], []
    with gzip.open(path, 'rt', encoding='latin-1') as f:
        for line in f:
            line = line.rstrip('\n').ljust(200)
            if not line[75:77].strip() or not line[102:107].strip():
                continue                                   # entries without J2000 position or V (novae etc.)
            rah, ram, ras = int(line[75:77]), int(line[77:79]), float(line[79:83])
            sgn = -1.0 if line[83] == '-' else 1.0
            ded, dem, des = int(line[84:86]), int(line[86:88]), int(line[88:90])
            ra.append(math.radians(15.0 * (rah + ram / 60.0 + ras / 3600.0)))
            de.append(sgn * math.radians(ded + dem / 60.0 + des / 3600.0))
            v.append(float(line[102:107]))
            b = line[109:114].strip()
            bv.append(float(b) if b else np.nan)
    return np.array(ra), np.array(de), np.array(v), np.array(bv)


def equ_to_ecl(ra, de):
    """Unit vectors in J2000 ecliptic coordinates."""
    x = np.cos(de) * np.cos(ra); y = np.cos(de) * np.sin(ra); z = np.sin(de)
    ce, se = math.cos(EPS_J2000), math.sin(EPS_J2000)
    return np.stack([x, ce * y + se * z, -se * y + ce * z], -1)


def bv_to_T(bv):
    """Black-body temperature [K] from B-V (Ballesteros 2012, Eq. 14)."""
    bv = np.asarray(bv, float)
    return 4600.0 * (1.0 / (0.92 * bv + 1.7) + 1.0 / (0.92 * bv + 0.62))


def _planck(lam_m, T):
    return 1.0 / lam_m ** 5 / np.expm1(H * C / (lam_m * KB * T))


def _band_ratio(T):
    lam = np.linspace(400e-9, 1000e-9, 1201)
    T = np.atleast_1d(np.asarray(T, float))
    B = _planck(lam[None, :], T[:, None])
    band = (lam >= 600e-9) & (lam <= 900e-9)
    sv = np.exp(-0.5 * ((lam - 551e-9) / (88e-9 / 2.3548)) ** 2)
    return np.trapezoid(B * band, lam, axis=1) / np.trapezoid(B * sv, lam, axis=1)


def colour_factor(bv):
    """600-900 nm flux per unit V flux, relative to the Sun (black-body approximation)."""
    bv = np.where(np.isfinite(bv), bv, BV_SUN)
    return _band_ratio(bv_to_T(bv)) / _band_ratio(bv_to_T(BV_SUN))[0]


def _psf_frac(x0, x1, c, s1, s2, hf):
    r1 = 1.0 / (s1 * math.sqrt(2))
    v = 0.5 * (erf((x1 - c) * r1) - erf((x0 - c) * r1))
    if hf > 0:
        r2 = 1.0 / (s2 * math.sqrt(2))
        v = (1 - hf) * v + hf * 0.5 * (erf((x1 - c) * r2) - erf((x0 - c) * r2))
    return v


class StarField:
    def __init__(self, cam, rad, sensor, optics, env, crop, duration, subsolar_latlon, hit_fn):
        self.cam, self.crop = cam, crop
        x0, y0, w, h = crop
        self.w, self.h = w, h
        self.psf = (optics['psf.sigma_px'], optics['psf.halo_sigma_px'], optics['psf.halo_fraction'])
        self.R = cam.R
        self.w_moon = env['moon.rotation_rad_s']
        lam_sun = math.radians(float(env.get('stars.sun_ecliptic_lon_deg', 0.0)))
        self.lam_E = lam_sun - math.radians(subsolar_latlon[1])
        E_band = env['sun.irradiance_W_m2'] * env['band.solar_fraction']
        k_e = rad.A_ap * rad.T * rad.qe / rad.e_ph                    # electrons per (W m^-2) of band irradiance
        dirs, flux, mags, src = [], [], [], []
        if env.get('stars.catalogue', True) and BSC5.exists():
            ra, de, v, bv = load_bsc5()
            sel = v <= float(env.get('stars.mag_limit', 7.0))
            ecl = equ_to_ecl(ra[sel], de[sel])
            lon = np.arctan2(ecl[:, 1], ecl[:, 0]) - self.lam_E
            lat = np.arcsin(np.clip(ecl[:, 2], -1, 1))
            d0 = np.stack([np.cos(lat) * np.cos(lon), np.cos(lat) * np.sin(lon), np.sin(lat)], -1)   # Moon frame, t=0
            dirs.append(d0); mags.append(v[sel])
            flux.append(E_band * 10 ** (-0.4 * (v[sel] - V_SUN)) * colour_factor(bv[sel]) * k_e)
            src += ['bsc5'] * int(sel.sum())
        self.catalogue_loaded = bool(src)
        tm = list(env.get('stars.test_mags', []) or [])
        if tm:
            rng = np.random.default_rng(int(env.get('stars.test_seed', 5)))
            t_mid = duration / 2
            cc, rr = np.meshgrid(np.arange(x0, x0 + w) + 0.5, np.arange(y0, y0 + h) + 0.5)
            sky = ~hit_fn(cc, rr, t_mid)
            ys, xs = np.nonzero(sky[5:-5, 5:-5])
            place = env.get('stars.test_place', 'sky')

            def d0_of(c, r):
                P, z, up, right = cam.state(t_mid)
                xu, yu = cam.pix_to_norm(c, r)
                jx, jy = cam.jitter(t_mid)
                d = (xu + jx) * right + (yu + jy) * up + z
                d = d / np.linalg.norm(d)
                ang = self.w_moon * t_mid                                 # back to the t = 0 Moon frame
                ca, sa = math.cos(ang), math.sin(ang)
                return np.array([ca * d[0] - sa * d[1], sa * d[0] + ca * d[1], d[2]])
            if place == 'limb':
                # sky pixels next to the limb whose star is visible at one end of the run and occulted at the other
                edge = sky & ~(np.roll(sky, 1, 0) & np.roll(sky, -1, 0) & np.roll(sky, 1, 1) & np.roll(sky, -1, 1))
                edge[:5] = edge[-5:] = False; edge[:, :5] = edge[:, -5:] = False
                ys, xs = np.nonzero(edge)
                order = rng.permutation(len(xs))
                cand = []
                for k in order:
                    d0 = d0_of(x0 + xs[k] + 0.5, y0 + ys[k] + 0.5)
                    v0 = self._project(d0[None], 0.0)[2][0]; v1 = self._project(d0[None], duration)[2][0]
                    if v0 != v1:
                        cand.append(d0)
                    if len(cand) >= len(tm):
                        break
            elif len(xs):
                cand = []
                for m in tm:
                    k = rng.integers(len(xs))
                    cand.append(d0_of(x0 + 5 + xs[k] + 0.5, y0 + 5 + ys[k] + 0.5))
            else:
                cand = []
            for m, d0 in zip(tm, cand):
                dirs.append(d0[None]); mags.append(np.array([m]))
                flux.append(np.array([E_band * 10 ** (-0.4 * (m - V_SUN)) * k_e]))
                src.append(f'test_V{m:g}')
        if not dirs:
            self.d0 = np.zeros((0, 3)); self.flux = np.zeros(0); self.mag = np.zeros(0); self.src = []
            self.meta = dict(n_in_field=0, catalogue=self.catalogue_loaded)
            return
        d0 = np.concatenate(dirs); fl = np.concatenate(flux); mg = np.concatenate(mags)
        # keep stars that come within the crop (+10 px) at the start, middle or end of the run
        keep = np.zeros(len(d0), bool)
        for t in (0.0, duration / 2, duration):
            c, r, front = self._project(d0, t)
            keep |= front & (c > x0 - 10) & (c < x0 + w + 10) & (r > y0 - 10) & (r < y0 + h + 10)
        self.d0, self.flux, self.mag = d0[keep], fl[keep], mg[keep]
        self.src = [s for s, k in zip(src, keep) if k]
        track = []                                          # crop pixel position and visibility every 0.5 s
        ts = np.arange(0.0, duration + 1e-9, 0.5)
        for t in ts:
            c, r, v = self._project(self.d0, t)
            track.append((c - x0, r - y0, v))
        self.meta = dict(n_in_field=int(keep.sum()), catalogue=self.catalogue_loaded,
                         sun_ecliptic_lon_deg=float(env.get('stars.sun_ecliptic_lon_deg', 0.0)), track_t_s=ts.tolist(),
                         stars=[dict(src=s, V=float(m), e_s=float(f),
                                     track_px=[[round(float(tr[0][k]), 2), round(float(tr[1][k]), 2), bool(tr[2][k])]
                                               for tr in track])
                                for k, (s, m, f) in enumerate(zip(self.src, self.mag, self.flux))])

    def _dirs(self, t):
        a = -self.w_moon * t
        ca, sa = math.cos(a), math.sin(a)
        d = self.d0
        return np.stack([ca * d[:, 0] - sa * d[:, 1], sa * d[:, 0] + ca * d[:, 1], d[:, 2]], -1)

    def _project(self, d0, t):
        a = -self.w_moon * t
        ca, sa = math.cos(a), math.sin(a)
        d = np.stack([ca * d0[:, 0] - sa * d0[:, 1], sa * d0[:, 0] + ca * d0[:, 1], d0[:, 2]], -1)
        P, z, up, right = self.cam.state(t)
        dz = d @ z
        front = dz > 1e-6
        dzs = np.where(front, dz, 1.0)
        xu, yu = (d @ right) / dzs, (d @ up) / dzs
        jx, jy = self.cam.jitter(t)
        c, r = self.cam.norm_to_pix(xu - jx, yu - jy)
        b = d @ P
        disc = b * b - (P @ P - self.R ** 2)
        occ = (disc >= 0) & (-b - np.sqrt(np.maximum(disc, 0)) > 0)
        return c, r, front & ~occ

    def rate(self, t):
        out = np.zeros((self.h, self.w), np.float32)
        if len(self.d0) == 0:
            return out
        x0, y0 = self.crop[0], self.crop[1]
        c, r, vis = self._project(self.d0, t)
        s1, s2, hf = self.psf
        rr = int(math.ceil(3 * (s2 if hf > 0 else s1))) + 1
        for k in np.nonzero(vis)[0]:
            cx, cy = c[k] - x0, r[k] - y0
            i0, i1 = max(int(cx) - rr, 0), min(int(cx) + rr + 1, self.w)
            j0, j1 = max(int(cy) - rr, 0), min(int(cy) + rr + 1, self.h)
            if i0 >= i1 or j0 >= j1:
                continue
            xs = np.arange(i0, i1, dtype=float); ys = np.arange(j0, j1, dtype=float)
            fx = _psf_frac(xs, xs + 1, cx, s1, s2, hf); fy = _psf_frac(ys, ys + 1, cy, s1, s2, hf)
            g = float(self.cam.point_gain(np.array(c[k]), np.array(r[k])))
            out[j0:j1, i0:i1] += (self.flux[k] * g * fy[:, None] * fx[None, :]).astype(np.float32)
        return out
