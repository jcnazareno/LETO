"""LRO WAC 643 nm albedo and LOLA LDEM_64 heights -> lat/lon radiance-factor maps for one scene region.

Inputs (read-only, staged locations; override with EVENTSIM_WAC_DIR / EVENTSIM_LOLA_DIR):
  * WAC Hapke-normalised 643 nm tiles, float32, 76 px/deg, 6840 samples, PDS3 label of 27360 bytes, line 0 at
    the northern edge. Near side: E350N0450 (0-70 N, 0-90 E), E350N3150 (0-70 N, 270-360 E), E350S3150
    (70 S-0, 270-360 E), E350S0450 (70 S-0, 0-90 E; added 4 Nov 2026). Far side (added 4 Nov 2026): E350N1350
    (0-70 N, 90-180 E), E350S1350 (70 S-0, 90-180 E), E350S2250 (70 S-0, 180-270 E). Bounds checked against the
    embedded PDS3 labels. E350N2250 (0-70 N, 180-270 E) is not available. Tiles whose file is absent are skipped;
    their area is filled with the mean albedo and flagged (albedo_valid = False).
    Invalid samples: non-finite, <= 0 or > 2.
  * LOLA LDEM_64 heights, int16 x 0.5 m, 64 px/deg, rows 70 N -> 70 S: either the three crops in EVENTSIM_LOLA_DIR
    (lon 0-90 E and 270-360 E, 5760 columns each; lon 90-270 E, 11520 columns) or, if those are absent, the same
    rows 1280-10239 read directly from the full data/external/LOLA_DATA/ldem_64.img (11520 x 23040, little-endian;
    the crops are bit-identical slices of it: md5 095693fe..., 40fe587f..., c8681bd4...).
  * Albedo normalisation: the near-side mean (|lat| < 60) of the three original near-side tiles (NORM_TILES), kept
    unchanged so that near-side scenes and S17 stay comparable; the cached value is reused.
Products on a regular lat/lon grid at the WAC spacing (1/76 deg, ~0.4 km):
  * albedo normalised to the near-side mean (|lat| < 60 of the three tiles), as in S17;
  * Lunar-Lambert factor LL = 2 L mu0/(mu0 + mu) + (1 - L) mu0 from LOLA slopes for a given light direction and
    the spacecraft direction (L = 0.7, S17);
  * cast shadows for a light source (Sun) by marching the horizon along the light azimuth on LOLA heights with
    lunar curvature; penumbra of the 0.53 deg solar disc.
"""
from __future__ import annotations
import math
import os
from pathlib import Path
import numpy as np
from scipy import ndimage

_ROOT = Path(__file__).resolve().parents[3]
_EXTERNAL = _ROOT / 'data' / 'external'
WAC_DIR = Path(os.environ.get('EVENTSIM_WAC_DIR', str(_EXTERNAL / 'ALBEDO_WAC_HAPKE_NORMALIZED_REFLECTANCE_643NM')))
LOLA_DIR = Path(os.environ.get('EVENTSIM_LOLA_DIR', str(_ROOT / 'data' / 'lola_crops')))
LOLA_FULL = Path(os.environ.get('EVENTSIM_LOLA_FULL', str(_EXTERNAL / 'LOLA_DATA' / 'ldem_64.img')))
_LOLA_COLS = {(0.0, 90.0): (0, 5760), (270.0, 360.0): (17280, 23040), (90.0, 270.0): (5760, 17280)}
WAC_TILES = {'E350N0450': (0.0, 70.0, 0.0, 90.0), 'E350N3150': (0.0, 70.0, 270.0, 360.0),
             'E350S3150': (-70.0, 0.0, 270.0, 360.0),
             # added 4 Nov 2026 (bounds from the embedded PDS3 labels)
             'E350S0450': (-70.0, 0.0, 0.0, 90.0),
             'E350N1350': (0.0, 70.0, 90.0, 180.0), 'E350S1350': (-70.0, 0.0, 90.0, 180.0),
             'E350S2250': (-70.0, 0.0, 180.0, 270.0)}
NORM_TILES = ('E350N0450', 'E350N3150', 'E350S3150')   # near-side normalisation as in S17 (unchanged)
LOLA_FILES = {(0.0, 90.0): 'ldem64_lat-70_70_E000_090.int16', (270.0, 360.0): 'ldem64_lat-70_70_E270_360.int16',
              (90.0, 270.0): 'ldem64_lat-70_70_E090_270.int16'}   # far side added 4 Nov 2026
WAC_PPD, LOLA_PPD = 76, 64
R_MOON_M = 1737.4e3


def _wac_memmap(tile):
    path = WAC_DIR / f'WAC_HAPKE_643NM_{tile}.IMG'
    S = 6840
    L = (path.stat().st_size - 27360) // (4 * S)
    return np.memmap(path, dtype='<f4', mode='r', offset=27360, shape=(L, S))


def _wac_exists(tile):
    return (WAC_DIR / f'WAC_HAPKE_643NM_{tile}.IMG').exists()


def _lola_exists(lon_key):
    return (LOLA_DIR / LOLA_FILES[lon_key]).exists() or LOLA_FULL.exists()


def _lola_memmap(lon_key):
    """Crop file if present, else the identical slice of the full LDEM_64 file (read-only views)."""
    ncol = int(round((lon_key[1] - lon_key[0]) * LOLA_PPD))
    crop = LOLA_DIR / LOLA_FILES[lon_key]
    if crop.exists():
        return np.memmap(crop, dtype='<i2', mode='r', shape=(8960, ncol))
    full = np.memmap(LOLA_FULL, dtype='<i2', mode='r', shape=(11520, 23040))
    c0, c1 = _LOLA_COLS[lon_key]
    return full[1280:10240, c0:c1]


def available():
    """True if the near-side normalisation tiles and the near-side LOLA crops are present."""
    return all(_wac_exists(t) for t in NORM_TILES) and \
        all(_lola_exists(k) for k in ((0.0, 90.0), (270.0, 360.0)))


def coverage():
    """Which WAC tiles and LOLA crops are present (for run metadata)."""
    return {'wac': {t: _wac_exists(t) for t in WAC_TILES},
            'lola': {f'{k[0]:.0f}-{k[1]:.0f}E': _lola_exists(k) for k in LOLA_FILES},
            'lola_source': 'crops' if all((LOLA_DIR / f).exists() for f in LOLA_FILES.values()) else str(LOLA_FULL)}


_MEAN = None


def nearside_mean_albedo():
    global _MEAN
    cache = _ROOT / 'data' / 'wac_nearside_mean.json'
    if _MEAN is None and cache.exists():
        import json
        _MEAN = json.loads(cache.read_text())['mean_albedo_abs_lat_lt_60']
    if _MEAN is None:
        vals = []
        for t in NORM_TILES:
            la0, la1, _, _ = WAC_TILES[t]
            a = np.array(_wac_memmap(t)[::20, ::20], dtype=np.float64)
            lat = la1 - (np.arange(a.shape[0]) * 20 + 0.5) / WAC_PPD
            a[~np.isfinite(a) | (a <= 0) | (a > 2)] = np.nan
            vals.append(a[np.abs(lat) < 60].ravel())
        _MEAN = float(np.nanmean(np.concatenate(vals)))
        import json
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps({'mean_albedo_abs_lat_lt_60': _MEAN, 'tiles': list(NORM_TILES), 'sampling': 'every 20th line/sample'}))
    return _MEAN


def _sample_tiles(lat, lon, kind):
    """Bilinear samples of WAC (kind='wac') or LOLA heights in m (kind='lola') at lat/lon arrays (deg)."""
    out = np.full(lat.shape, np.nan, np.float32)
    lon = lon % 360.0
    if kind == 'wac':
        for t, (la0, la1, lo0, lo1) in WAC_TILES.items():
            m = (lat >= la0) & (lat < la1) & (lon >= lo0) & (lon < lo1)
            if not m.any() or not _wac_exists(t):
                continue
            mm = _wac_memmap(t)
            r = (la1 - lat[m]) * WAC_PPD - 0.5; c = (lon[m] - lo0) * WAC_PPD - 0.5
            r0, r1 = max(int(r.min()) - 2, 0), min(int(r.max()) + 3, mm.shape[0])
            c0, c1 = max(int(c.min()) - 2, 0), min(int(c.max()) + 3, mm.shape[1])
            sub = np.array(mm[r0:r1, c0:c1], dtype=np.float32)
            bad = ~np.isfinite(sub) | (sub <= 0) | (sub > 2)
            if bad.any():
                med = np.nanmedian(np.where(bad, np.nan, sub)) if (~bad).any() else np.nan
                sub[bad] = med
            out[m] = ndimage.map_coordinates(sub, [r - r0, c - c0], order=1, mode='nearest')
    else:
        for (lo0, lo1), _ in LOLA_FILES.items():
            m = (lat >= -70) & (lat < 70) & (lon >= lo0) & (lon < lo1)
            if not m.any() or not _lola_exists((lo0, lo1)):
                continue
            mm = _lola_memmap((lo0, lo1))
            r = (70.0 - lat[m]) * LOLA_PPD - 0.5; c = (lon[m] - lo0) * LOLA_PPD - 0.5
            r0, r1 = max(int(r.min()) - 2, 0), min(int(r.max()) + 3, mm.shape[0])
            c0, c1 = max(int(c.min()) - 2, 0), min(int(c.max()) + 3, mm.shape[1])
            sub = np.array(mm[r0:r1, c0:c1], dtype=np.float32) * 0.5
            out[m] = ndimage.map_coordinates(sub, [r - r0, c - c0], order=1, mode='nearest')
    return out


class RegionMaps:
    """Albedo and shading factors on a lat/lon grid covering [lat0, lat1] x [lon0, lon1] (lon may exceed 360)."""

    def __init__(self, lat0, lat1, lon0, lon1, res_deg=1.0 / WAC_PPD):
        self.res = res_deg
        self.lat_top = lat1
        self.lon_left = lon0
        nr = int(math.ceil((lat1 - lat0) / res_deg)); nc = int(math.ceil((lon1 - lon0) / res_deg))
        self.lat = lat1 - (np.arange(nr) + 0.5) * res_deg
        self.lon = lon0 + (np.arange(nc) + 0.5) * res_deg
        LAT, LON = np.meshgrid(self.lat, self.lon, indexing='ij')
        self.LAT, self.LON = LAT, LON
        a = _sample_tiles(LAT, LON, 'wac')
        self.albedo_valid = np.isfinite(a)
        mean = nearside_mean_albedo()
        self.albedo = np.where(self.albedo_valid, a / mean, 1.0).astype(np.float32)
        h = _sample_tiles(LAT, LON, 'lola')
        self.height_valid = np.isfinite(h)
        self.height = np.where(self.height_valid, h, 0.0).astype(np.float32)
        # slopes (ENU) in m/m
        dy = res_deg * math.pi / 180 * R_MOON_M
        dx = dy * np.cos(np.radians(LAT))
        dzdr, dzdc = np.gradient(self.height.astype(np.float64))
        dzdn = -dzdr / dy; dzde = dzdc / dx
        nrm = np.sqrt(dzde ** 2 + dzdn ** 2 + 1.0)
        self.normal = np.stack([-dzde / nrm, -dzdn / nrm, 1.0 / nrm], -1)
        self.dx_m, self.dy_m = dx, dy

    def enu(self, vec):
        """Components of a Moon-fixed direction (3,) or per-point (...,3) in local east/north/up."""
        la, lo = np.radians(self.LAT), np.radians(self.LON)
        e = np.stack([-np.sin(lo), np.cos(lo), np.zeros_like(lo)], -1)
        n = np.stack([-np.sin(la) * np.cos(lo), -np.sin(la) * np.sin(lo), np.cos(la)], -1)
        u = np.stack([np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)], -1)
        v = np.broadcast_to(vec, u.shape)
        return (v * e).sum(-1), (v * n).sum(-1), (v * u).sum(-1)

    def lunar_lambert(self, light_dir, sc_pos_km, L=0.7):
        """LL factor for a distant light (Moon-fixed unit vector) seen from the spacecraft position (km).
        L: a number, or 'mcewen' for the phase-angle polynomial of the USGS ISIS LunarLambertMcEwen photometric model
        (A. McEwen 1995): L(a) = 1 - 0.019 a + 2.42e-4 a^2 - 1.46e-6 a^3, a = phase angle in degrees, evaluated per
        map point and clipped to [0, 1] (0 = Lambert, 1 = Lommel-Seeliger; the cubic turns negative above ~105 deg).
        Also returns the phase-angle map in self.last_phase_deg."""
        le, ln_, lu = self.enu(light_dir)
        mu0 = np.clip(self.normal[..., 0] * le + self.normal[..., 1] * ln_ + self.normal[..., 2] * lu, 0, None)
        la, lo = np.radians(self.LAT), np.radians(self.LON)
        pts = np.stack([np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)], -1) * (R_MOON_M / 1e3)
        v = sc_pos_km - pts
        v /= np.linalg.norm(v, axis=-1, keepdims=True)
        ve, vn, vu = self.enu_pts(v)
        mu = np.clip(self.normal[..., 0] * ve + self.normal[..., 1] * vn + self.normal[..., 2] * vu, 1e-3, None)
        cos_a = np.clip(v @ np.asarray(light_dir, float), -1.0, 1.0)
        a = np.degrees(np.arccos(cos_a))
        self.last_phase_deg = a.astype(np.float32)
        if isinstance(L, str):
            if L != 'mcewen':
                raise ValueError(f'unknown lunar-Lambert L model {L!r}')
            L = np.clip(1.0 - 0.019 * a + 2.42e-4 * a ** 2 - 1.46e-6 * a ** 3, 0.0, 1.0)
        ll = 2 * L * mu0 / (mu0 + mu) + (1 - L) * mu0
        return ll.astype(np.float32), lu

    def enu_pts(self, v):
        la, lo = np.radians(self.LAT), np.radians(self.LON)
        e = np.stack([-np.sin(lo), np.cos(lo), np.zeros_like(lo)], -1)
        n = np.stack([-np.sin(la) * np.cos(lo), -np.sin(la) * np.sin(lo), np.cos(la)], -1)
        u = np.stack([np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)], -1)
        return (v * e).sum(-1), (v * n).sum(-1), (v * u).sum(-1)

    def cast_shadow(self, light_dir, max_km=150.0, step_km=0.4, height_fn=None):
        """Soft lit fraction (0..1) for a distant light: horizon march along the light azimuth with curvature.

        Since the 4 Nov 2026 review (E10) the march samples an extended height grid that reaches max_km beyond
        the region in the light direction (before, rays leaving the region reused its edge height). Rays that
        meet missing terrain (outside the LOLA crops, |lat| > 70 deg) are counted in self.shadow_info.
        height_fn(lat, lon) -> heights [m] (NaN = missing) replaces LOLA for tests."""
        le, ln_, lu = self.enu(light_dir)
        el = np.arcsin(np.clip(lu, -1, 1))
        az_e, az_n = np.mean(le), np.mean(ln_)
        nh = math.hypot(az_e, az_n)
        self.shadow_info = dict(max_km=max_km, step_km=step_km, extended=True, ray_missing_terrain_fraction=0.0)
        if nh < 1e-6:
            return np.ones_like(self.height)
        ue, un = az_e / nh, az_n / nh
        hfn = height_fn or (lambda la, lo: _sample_tiles(la, lo, 'lola'))
        # extended grid aligned with this one, reaching max_km (+2 cells) in the light direction
        mdeg = math.degrees(max_km * 1e3 / R_MOON_M)
        coslat = max(math.cos(math.radians(float(np.max(np.abs(self.lat))))), 0.2)
        top = int(math.ceil(mdeg * max(un, 0.0) / self.res)) + 2
        bot = int(math.ceil(mdeg * max(-un, 0.0) / self.res)) + 2
        right = int(math.ceil(mdeg * max(ue, 0.0) / coslat / self.res)) + 2
        left = int(math.ceil(mdeg * max(-ue, 0.0) / coslat / self.res)) + 2
        nr, nc = self.height.shape
        lat_e = (self.lat_top + top * self.res) - (np.arange(nr + top + bot) + 0.5) * self.res
        lon_e = (self.lon_left - left * self.res) + (np.arange(nc + left + right) + 0.5) * self.res
        LA, LO = np.meshgrid(lat_e, lon_e, indexing='ij')
        he = hfn(LA, LO).astype(np.float64)
        valid = np.isfinite(he)
        he = np.where(valid, he, 0.0)
        hor = np.full(self.height.shape, -1.0)
        miss = np.zeros(self.height.shape, bool)
        rr, cc = np.meshgrid(np.arange(nr), np.arange(nc), indexing='ij')
        dxm = float(np.mean(self.dx_m)); dym = float(self.dy_m)
        h = self.height.astype(np.float64)
        vf = valid.astype(np.float32)
        for d in np.arange(step_km, max_km, step_km):
            dm = d * 1e3
            r = rr + top - un * dm / dym; c = cc + left + ue * dm / dxm
            hk = ndimage.map_coordinates(he, [r, c], order=1, mode='nearest')
            ok = ndimage.map_coordinates(vf, [r, c], order=0, mode='constant', cval=0.0) > 0.5
            miss |= ~ok
            ang = (hk - h - dm * dm / (2 * R_MOON_M)) / dm
            ang = np.where(ok, ang, -1.0)               # missing terrain cannot raise the horizon (flagged)
            np.maximum(hor, ang, out=hor)
        hor = np.arctan(hor)
        sun_r = math.radians(0.53 / 2)
        self.shadow_info['ray_missing_terrain_fraction'] = float(miss.mean())
        self.shadow_info['extension_cells'] = dict(top=top, bottom=bot, left=left, right=right)
        return np.clip((el - hor) / (2 * sun_r) + 0.5, 0, 1).astype(np.float32)

    def sampler(self, field):
        f = np.asarray(field, np.float32)

        def sample(lat, lon):
            r = (self.lat_top - lat) / self.res - 0.5
            dl = (lon - self.lon_left) % 360.0
            c = dl / self.res - 0.5
            return ndimage.map_coordinates(f, [r, c], order=1, mode='nearest')
        return sample
