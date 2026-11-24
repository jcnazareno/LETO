"""Scenes: per-pixel photo-electron rate (excluding dark current) of one camera-head crop versus time.

All scenes return rates in detected e-/s per pixel, after the lens PSF, pixel integration, vignetting and the
optional stray-light term. Dark current is added per pixel by the simulator.
  * flat      : uniform or per-cell background (validation lattice; far side without geometry)
  * nearside  : WAC 643 nm albedo x Lunar-Lambert shading of LOLA slopes for the Earth direction, drifting with
                the orbit (ray-cast through the head's pinhole geometry), Earth phase from the Sun direction
  * farside   : dark surface (no earthshine), geometry kept for range, drift and stray light
  * terminator: as nearside plus sunlight (Lunar-Lambert, cast shadows with curvature, solar penumbra) for a
                subsolar point that puts the terminator inside or near the crop
  * terminator_far: far-side terminator (Tsiolkovsky at sunrise, WAC E350S1350 + LOLA 90-270 E; added 4 Nov 2026);
                no earthshine (the Earth is below the horizon), sunlight only
  * limb      : outer head of the mosaic, crop at its corner beyond the limb (space = no radiance)
Sub-pixel motion is handled by ray casting an oversampled grid (os x os rays per pixel) every keyframe and
box-averaging after the PSF blur; the simulator interpolates linearly between keyframes (50 ms default,
0.02 px of drift).
"""
from __future__ import annotations
import math
import numpy as np
from scipy import ndimage
from . import geometry as geo
from .radiometry import Radiometry, earth_phase_lambert, dark_e_s

EARTH_DIR = np.array([1.0, 0.0, 0.0])     # sub-Earth point 0 N 0 E, no libration


def _pct(a):
    """5/50/95th percentiles of a map (phase angle, deg) for the scene metadata."""
    q = np.nanpercentile(np.asarray(a, float), [5, 50, 95])
    return dict(p05=float(q[0]), p50=float(q[1]), p95=float(q[2]))


class StrayLight:
    def __init__(self, env, crop, frame=(1280, 720)):
        """frame: sensor array (width, height) in px; the gradient is measured from its edges."""
        self.mode = env['straylight.mode']
        self.env = env
        x0, y0, w, h = crop
        self.X, self.Y = np.meshgrid(np.arange(x0, x0 + w) + 0.5, np.arange(y0, y0 + h) + 0.5)
        self.W, self.H = int(frame[0]), int(frame[1])

    def rate(self, t):
        if self.mode == 'none':
            return 0.0
        e = self.env
        out = np.zeros(self.X.shape, np.float32)
        ramp = 1.0 + e['straylight.ramp_per_s'] * t
        if self.mode in ('gradient', 'both'):
            edge = e['straylight.gradient_edge']
            d = {'left': self.X, 'right': self.W - self.X, 'top': self.Y, 'bottom': self.H - self.Y}[edge]
            out += e['straylight.gradient_e_s'] * np.exp(-d / e['straylight.gradient_scale_px']) * ramp
        if self.mode in ('ghost', 'both'):
            fx, fy = e['straylight.ghost_pos_frac']
            gx = self.X.min() + fx * (self.X.max() - self.X.min()); gy = self.Y.min() + fy * (self.Y.max() - self.Y.min())
            R = e['straylight.ghost_radius_px']
            r = np.hypot(self.X - gx, self.Y - gy)
            out += e['straylight.ghost_e_s'] * np.exp(-0.5 * ((r - 0.6 * R) / (0.35 * R)) ** 2) * ramp   # annular ghost
        return out


class FlatScene:
    kind = 'flat'

    def __init__(self, w, h, photo, range_km, env, label='flat', crop=None):
        self.w, self.h = w, h
        self.photo = np.broadcast_to(np.asarray(photo, np.float32), (h, w)).copy()
        self.range_km = np.broadcast_to(np.asarray(range_km, np.float64), (h, w)).copy()
        self.vignette_map = np.ones((h, w))
        self.point_gain_map = self.vignette_map     # flat scenes: one field gain (same array; the lattice sets it)
        self.label = label
        self.crop = crop or (0, 0, w, h)
        self.stray = StrayLight(env, self.crop)
        self.meta = dict(scene=label, type='flat')

    def photo_rate(self, t):
        return self.photo + self.stray.rate(t)

    def flash_velocity(self, x, y, t):
        return np.zeros_like(np.asarray(x, float)), np.zeros_like(np.asarray(x, float))

    def lit_map(self):
        return np.zeros((self.h, self.w), bool)


class MapScene:
    """Ray-cast scene for one head crop. maps=None gives a dark (far-side) surface."""

    def __init__(self, sensor, optics, env, crop, head, label, target_latlon=None, subsat_latlon=None,
                 subsolar_latlon=(0.0, 180.0), maps_margin_deg=1.0, oversample=2, duration=20.0,
                 use_maps=True, earthshine='physical', I0_target=None, sun=False, t_ref=None, jitter_seed=11):
        self.sensor, self.optics, self.env = sensor, optics, env
        self.label = label
        self.crop = crop
        x0, y0, w, h = crop
        self.w, self.h = w, h
        self.rad = Radiometry(sensor, optics, env)
        t_ref = duration / 2 if t_ref is None else t_ref
        self.cam = geo.Camera(sensor, optics, env, head=head, crop=crop, target_latlon=target_latlon, t_ref=t_ref,
                              jitter_seed=jitter_seed, duration=duration)
        if subsat_latlon is not None and target_latlon is None:
            self.cam.lam_n0 = math.radians(subsat_latlon[1]); self.cam.u0 = math.radians(subsat_latlon[0]) - self.cam.n * t_ref
        self.os = int(oversample)
        s1 = optics['psf.sigma_px']; s2 = optics['psf.halo_sigma_px']; hf = optics['psf.halo_fraction']
        self.psf = (s1, s2, hf)
        self.margin = int(math.ceil(3 * (s2 if hf > 0 else s1))) + 1
        m, o = self.margin, self.os
        cs = x0 - m + (np.arange((w + 2 * m) * o) + 0.5) / o
        rs = y0 - m + (np.arange((h + 2 * m) * o) + 0.5) / o
        self.CC, self.RR = np.meshgrid(cs, rs)
        pc, pr = np.meshgrid(np.arange(x0, x0 + w) + 0.5, np.arange(y0, y0 + h) + 0.5)
        self.pix_c, self.pix_r = pc, pr
        self.vignette_map = self.cam.vignette(pc, pr)          # extended sources (cos^4)
        self.point_gain_map = self.cam.point_gain(pc, pr)      # point sources / flashes (cos)
        self.stray = StrayLight(env, crop, (sensor['array.width_px'], sensor['array.height_px']))
        # light directions
        la, lo = map(math.radians, subsolar_latlon)
        self.sun_dir = np.array([math.cos(la) * math.cos(lo), math.cos(la) * math.sin(lo), math.sin(la)])
        alpha = math.acos(max(-1.0, min(1.0, -float(self.sun_dir @ EARTH_DIR))))
        self.earth_phase_deg = math.degrees(alpha)
        self.es_level = self.rad.earthshine_full_e_s() * earth_phase_lambert(alpha) if earthshine != 'off' else 0.0
        self.sun_level = self.rad.sunlit_e_s() if sun else 0.0
        self.use_maps = use_maps
        self.maps = None
        u, hit, s, cos_e = self.cam.cast(pc, pr, t_ref)
        self.range_km = np.where(hit, s, np.nan)
        self.hit_map = hit
        self.cos_e = cos_e
        if use_maps:
            from .lunar_maps import RegionMaps
            pts = []
            for tt in (0.0, duration):
                uu, hh, _, _ = self.cam.cast(self.CC[::4, ::4], self.RR[::4, ::4], tt)
                pts.append(uu[hh])
            P = np.concatenate(pts)
            lat, lon = geo.latlon_of(P)
            lon_c = np.degrees(np.arctan2(np.mean(np.sin(np.radians(lon))), np.mean(np.cos(np.radians(lon))))) % 360
            dlon = (lon - lon_c + 180) % 360 - 180
            lat0, lat1 = lat.min() - maps_margin_deg, lat.max() + maps_margin_deg
            lon0, lon1 = lon_c + dlon.min() - maps_margin_deg / max(math.cos(math.radians(np.abs(lat).max())), 0.2), \
                lon_c + dlon.max() + maps_margin_deg / max(math.cos(math.radians(np.abs(lat).max())), 0.2)
            # WAC spacing (0.4 km) for oversampled crops; half resolution for one ray per pixel (full frame, memory)
            self.maps = RegionMaps(max(lat0, -89.9), min(lat1, 89.9), lon0, lon1,
                                   res_deg=(1.0 / 76) if self.os >= 2 else (2.0 / 76))
            P_sc, *_ = self.cam.state(t_ref)
            L = env['surface.lunar_lambert_L']
            ll_e, _ = self.maps.lunar_lambert(EARTH_DIR, P_sc, L)
            self.phase_stats = dict(earth=_pct(self.maps.last_phase_deg))
            self.F_es = self.maps.albedo * ll_e
            if sun:
                ll_s, _ = self.maps.lunar_lambert(self.sun_dir, P_sc, L)
                self.phase_stats['sun'] = _pct(self.maps.last_phase_deg)
                lit = self.maps.cast_shadow(self.sun_dir)
                self.shadow_info = dict(self.maps.shadow_info)
                self.F_sun = self.maps.albedo * ll_s * lit
            else:
                self.F_sun = None
            self.s_es = self.maps.sampler(self.F_es)
            self.s_sun = self.maps.sampler(self.F_sun) if sun else None
            self.s_valid = self.maps.sampler(self.maps.albedo_valid.astype(np.float32))
        # stars beyond the limb (11 Nov 2026): only pixels whose ray misses the Moon can show them
        self.stars = None
        if env.get('stars.enabled', False):
            from .stars import StarField
            self.stars = StarField(self.cam, self.rad, sensor, optics, env, crop, duration, subsolar_latlon,
                                   lambda c, r, t: self.cam.cast(c, r, t)[1])
            if self.stars.meta['n_in_field'] == 0:
                self.stars = None
        if earthshine == 'target_mean' and I0_target is not None:
            # scale the earthshine so that the crop-mean total background (photo + nominal dark) equals I0_target
            self.es_level = 1.0
            mean_photo = float(np.nanmean(self._render(0.0, stray=False)))
            dark = dark_e_s(sensor['dark.current_fA'])
            self.es_level = max(I0_target - dark, 0.0) / max(mean_photo, 1e-9)
        self.meta = dict(scene=label, type='map', head=list(head), crop=list(crop), subsolar_latlon=list(subsolar_latlon),
                         earth_phase_deg=self.earth_phase_deg, earthshine_level_e_s=self.es_level,
                         sun_level_e_s=self.sun_level, target_latlon=list(target_latlon) if target_latlon else None,
                         oversample=self.os, uses_wac_lola=bool(use_maps), ground=self.cam.ground_scale_km(t_ref),
                         lunar_lambert_L=env['surface.lunar_lambert_L'])
        if getattr(self, 'phase_stats', None):
            self.meta['phase_angle_deg'] = self.phase_stats
        if env.get('stars.enabled', False):
            self.meta['stars'] = self.stars.meta if self.stars is not None else dict(n_in_field=0)
        if getattr(self, 'shadow_info', None):
            self.meta['cast_shadow'] = self.shadow_info
        if use_maps:
            v = self.s_valid(*self._latlon(t_ref)[:2])
            self.meta['albedo_missing_fraction'] = float(1 - np.nanmean(v))
            from .lunar_maps import coverage
            self.meta['map_coverage'] = coverage()

    def _latlon(self, t):
        u, hit, s, _ = self.cam.cast(self.CC, self.RR, t)
        lat, lon = geo.latlon_of(u)
        return lat, lon, hit

    def _render(self, t, stray=True):
        if self.use_maps:
            lat, lon, hit = self._latlon(t)
            r = self.es_level * self.s_es(lat, lon)
            if self.s_sun is not None:
                r = r + self.sun_level * self.s_sun(lat, lon)
            r = np.where(hit, r, 0.0)
        else:
            r = np.zeros(self.CC.shape)
        s1, s2, hf = self.psf
        if hf > 0:
            r = (1 - hf) * ndimage.gaussian_filter(r, s1 * self.os) + hf * ndimage.gaussian_filter(r, s2 * self.os)
        elif s1 > 0:
            r = ndimage.gaussian_filter(r, s1 * self.os)
        o, m = self.os, self.margin
        H2, W2 = r.shape
        r = r.reshape(H2 // o, o, W2 // o, o).mean((1, 3))[m:m + self.h, m:m + self.w]
        r = r * self.vignette_map
        if stray:
            r = r + self.stray.rate(t)
            if self.stars is not None:
                r = r + self.stars.rate(t)          # point sources: PSF and cos theta gain inside StarField
        return r.astype(np.float32)

    def photo_rate(self, t):
        return self._render(t)

    def flash_velocity(self, x, y, t):
        """Image velocity [px/s] of ground-fixed points at crop coordinates (x, y) at time t."""
        x0, y0 = self.crop[0], self.crop[1]
        c = np.asarray(x, float) + x0; r = np.asarray(y, float) + y0
        u, hit, _, _ = self.cam.cast(c, r, t)
        c1, r1 = self.cam.project(u, t + 1.0)
        return np.where(hit, c1 - c, 0.0), np.where(hit, r1 - r, 0.0)

    def lit_map(self, threshold):
        return self._render(0.0, stray=False) > threshold


def _limb_crop(sensor, optics, env, p, w, h, duration, want=0.6):
    """Crop origin on the diagonal from the head centre to its outer corner where ~60% of the crop sees the Moon."""
    W, H = int(sensor['array.width_px']), int(sensor['array.height_px'])
    cam = geo.Camera(sensor, optics, env, head=p['head'], crop=(0, 0, W, H), duration=duration)
    lat, lon = p['subsat_latlon']
    cam.lam_n0 = math.radians(lon); cam.u0 = math.radians(lat) - cam.n * duration / 2
    best = None
    for f in np.linspace(0, 1, 81):
        x0 = int(round((W - w) / 2 + f * (W - w) / 2)); y0 = int(round((H - h) / 2 * (1 - f)))
        cc, rr = np.meshgrid(np.arange(x0, x0 + w, 8) + 0.5, np.arange(y0, y0 + h, 8) + 0.5)
        _, hit, _, _ = cam.cast(cc, rr, duration / 2)
        score = abs(hit.mean() - want)
        if best is None or score < best[0]:
            best = (score, x0, y0)
    return best[1], best[2]


# ---------------- presets ----------------
PRESETS = {
    'nearside': dict(scene='nearside', target_latlon=(9.6, 339.9), head=(0, 1), subsolar_latlon=(1.5, 159.9),
                     use_maps=True, sun=False, label='Near side in earthshine (Copernicus, WAC 643 nm + LOLA)'),
    'farside': dict(scene='farside', target_latlon=(20.0, 180.0), head=(0, 1), subsolar_latlon=(1.5, 0.0),
                    use_maps=False, sun=False, earthshine='off', label='Far side, dark (dark-current limited)'),
    'particles': dict(scene='particles', target_latlon=(-30.0, 160.0), head=(0, 1), subsolar_latlon=(1.5, 340.0),
                      use_maps=False, sun=False, earthshine='off', label='Far side with particle hits and hot pixels'),
    'terminator': dict(scene='terminator', target_latlon=(20.0, 356.0), head=(0, 1), subsolar_latlon=(1.5, 91.0),
                       use_maps=True, sun=True, label='Terminator: Montes Apenninus at sunrise, lit peaks in the dark'),
    # added 4 Nov 2026: far-side terminator; sunrise geometry as for 'terminator' (subsolar point 95 deg east of the
    # target, Sun about 5 deg below the horizon at the crater centre), Tsiolkovsky (20.4 S, 129.1 E), central peak
    'terminator_far': dict(scene='terminator_far', target_latlon=(-20.4, 129.1), head=(0, 1), subsolar_latlon=(1.5, 224.1),
                           use_maps=True, sun=True, earthshine='off',
                           label='Far-side terminator: Tsiolkovsky at sunrise, lit rim and peak, no earthshine'),
    'limb': dict(scene='limb', subsat_latlon=(-12.0, 332.0), head=(1, 2), subsolar_latlon=(0.0, 180.0),
                 use_maps=True, sun=False, crop_anchor='outer_corner', label='Limb at the corner of an outer head (earthshine)'),
}


def build(name, sensor, optics, env, crop_wh=(320, 180), duration=20.0, full_frame=False, oversample=None,
          crop_xy=None, earthshine=None, I0_target=None, jitter_seed=11, **kw):
    p = dict(PRESETS[name]); p.update({k: v for k, v in kw.items() if v is not None})
    W, H = int(sensor['array.width_px']), int(sensor['array.height_px'])
    if full_frame:
        crop = (0, 0, W, H)
    else:
        w, h = crop_wh
        if crop_xy is not None:
            x0, y0 = crop_xy
        elif p.get('crop_anchor') == 'outer_corner':
            x0, y0 = _limb_crop(sensor, optics, env, p, w, h, duration)
        else:
            x0, y0 = (W - w) // 2, (H - h) // 2
        crop = (int(x0), int(y0), int(w), int(h))
    os_ = oversample or (1 if full_frame else 2)
    es = earthshine or p.get('earthshine', 'physical')
    sc = MapScene(sensor, optics, env, crop, p['head'], p['label'], target_latlon=p.get('target_latlon'),
                  subsat_latlon=p.get('subsat_latlon'), subsolar_latlon=p['subsolar_latlon'], oversample=os_,
                  duration=duration, use_maps=p['use_maps'], earthshine=es, I0_target=I0_target, sun=p['sun'],
                  jitter_seed=jitter_seed)
    sc.meta['preset'] = name
    return sc
