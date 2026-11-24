"""Orbit, attitude and camera-head geometry: pixel rays onto a spherical Moon.

Moon-fixed frame (x towards 0 N 0 E, z north). The spacecraft is on a circular polar orbit whose node longitude
drifts west with the Moon's sidereal rotation; it points one axis to nadir and its 'up' image axis along the
flight direction, so the scene drifts towards increasing row number. Each head of the 2 x 3 mosaic is a pinhole
camera tilted by the coverage.py mosaic offsets (cross-track cx, along-track cy). Pixel (c, r) of the full
1280 x 720 sensor has centre (c + 0.5, r + 0.5); x (columns) is cross-track, y (rows) along-track.
Attitude jitter is a first-order Gauss-Markov process in both image axes.
Not modelled: terrain parallax (rays hit the 1737.4 km sphere), orbit eccentricity, libration.
"""
import math
import numpy as np


def _norm(v):
    return v / np.linalg.norm(v, axis=-1, keepdims=True)


def mosaic_offsets(optics, sensor):
    f = optics['focal_length_m']; p = sensor['array.pixel_pitch_um'] * 1e-6
    W, H = sensor['array.width_px'], sensor['array.height_px']
    hw = math.atan(W * p / (2 * f)); hh = math.atan(H * p / (2 * f))
    cols, rows, ov = optics['mosaic.cols'], optics['mosaic.rows'], optics['mosaic.overlap']
    cen = {}
    for i in range(cols):
        for j in range(rows):
            cen[(i, j)] = ((i - (cols - 1) / 2) * 2 * hw * (1 - ov), (j - (rows - 1) / 2) * 2 * hh * (1 - ov))
    return cen, hw, hh


class Camera:
    def __init__(self, sensor, optics, env, head=(1, 1), crop=None, target_latlon=None, t_ref=0.0,
                 jitter_seed=11, duration=30.0, anchor_px=None):
        self.R = env['moon.radius_km']
        self.r = self.R + env['orbit.altitude_km']
        self.n = math.sqrt(env['moon.mu_km3_s2'] / self.r ** 3)      # rad/s
        self.w_moon = env['moon.rotation_rad_s']
        self.f = optics['focal_length_m']; self.pitch = sensor['array.pixel_pitch_um'] * 1e-6
        self.W, self.H = int(sensor['array.width_px']), int(sensor['array.height_px'])
        self.k1 = optics['distortion.k1']
        self.vignetting = optics['vignetting.model']
        cen, self.hw, self.hh = mosaic_offsets(optics, sensor)
        self.head = tuple(head)
        self.cx, self.cy = cen[self.head]
        self.crop = crop or (0, 0, self.W, self.H)            # x0, y0, w, h in sensor pixels
        # jitter (Gauss-Markov) on a 10 ms grid
        sig = env['attitude.jitter_rms_arcsec'] / 206264.806
        tc = env['attitude.jitter_corr_s']
        rng = np.random.default_rng(jitter_seed)
        self.jt = np.arange(-1.0, duration + 2.0, 0.01)
        a = math.exp(-0.01 / tc) if tc > 0 else 0.0
        jx = np.zeros(len(self.jt)); jy = np.zeros(len(self.jt))
        e = rng.normal(0, sig * math.sqrt(1 - a * a), (len(self.jt), 2))
        jx[0], jy[0] = rng.normal(0, sig, 2)
        for k in range(1, len(self.jt)):
            jx[k] = a * jx[k - 1] + e[k, 0]; jy[k] = a * jy[k - 1] + e[k, 1]
        self.jx, self.jy = jx, jy
        self.lam_n0, self.u0 = 0.0, 0.0
        if target_latlon is not None:
            ax = anchor_px or (self.crop[0] + self.crop[2] / 2, self.crop[1] + self.crop[3] / 2)
            self.solve_target(target_latlon, ax, t_ref)

    # ----- orbit and attitude -----
    def state(self, t):
        u = self.u0 + self.n * t
        lam = self.lam_n0 - self.w_moon * t
        cu, su, cl, sl = math.cos(u), math.sin(u), math.cos(lam), math.sin(lam)
        rad = np.array([cu * cl, cu * sl, su])
        T = np.array([-su * cl, -su * sl, cu])                 # flight direction (north when ascending)
        N = -rad
        Rr = np.cross(N, T)                                    # image right
        z = _norm(math.tan(self.cx) * Rr + math.tan(self.cy) * T + N)
        up = _norm(T - np.dot(T, z) * z)
        right = np.cross(z, up)
        return rad * self.r, z, up, right

    def jitter(self, t):
        return np.interp(t, self.jt, self.jx), np.interp(t, self.jt, self.jy)

    # ----- pixel <-> normalised image coordinates -----
    def pix_to_norm(self, c, r):
        xd = (c - self.W / 2) * self.pitch / self.f
        yd = -(r - self.H / 2) * self.pitch / self.f
        if self.k1:
            xu, yu = xd, yd
            for _ in range(3):
                s = 1 + self.k1 * (xu * xu + yu * yu)
                xu, yu = xd / s, yd / s
            return xu, yu
        return xd, yd

    def norm_to_pix(self, xu, yu):
        if self.k1:
            s = 1 + self.k1 * (xu * xu + yu * yu); xu, yu = xu * s, yu * s
        return xu * self.f / self.pitch + self.W / 2, -yu * self.f / self.pitch + self.H / 2

    def vignette(self, c, r):
        if self.vignetting != 'cos4':
            return np.ones(np.shape(c))
        xu, yu = self.pix_to_norm(c, r)
        return 1.0 / (1 + xu * xu + yu * yu) ** 2

    def point_gain(self, c, r):
        """Relative response to a POINT source (flash) at field angle theta. Under the 'cos4' natural fall-off only
        the foreshortening of the entrance pupil applies (cos theta): all light of a point source lands in its PSF,
        so the cos^3 theta shrinkage of the pixel footprint, which dims extended scenes, does not act on it
        (10 Nov 2026; before, flashes were scaled by the extended-source cos^4 theta)."""
        if self.vignetting != 'cos4':
            return np.ones(np.shape(c))
        xu, yu = self.pix_to_norm(c, r)
        return 1.0 / np.sqrt(1 + xu * xu + yu * yu)

    # ----- ray casting -----
    def cast(self, c, r, t):
        """c, r: arrays of sensor pixel coordinates (centre = +0.5). Returns surface unit vectors, hit mask,
        slant range [km] and cos(emission)."""
        P, z, up, right = self.state(t)
        xu, yu = self.pix_to_norm(np.asarray(c, float), np.asarray(r, float))
        jx, jy = self.jitter(t)
        xu = xu + jx; yu = yu + jy
        d = xu[..., None] * right + yu[..., None] * up + z
        d = _norm(d)
        b = d @ P
        disc = b * b - (P @ P - self.R ** 2)
        hit = disc >= 0
        s = -b - np.sqrt(np.where(hit, disc, 0.0))
        pts = P + s[..., None] * d
        u = pts / self.R
        cos_e = np.einsum('...i,...i->...', -d, u)
        s = np.where(hit, s, np.nan)
        return u, hit, s, cos_e

    def project(self, u, t):
        """Surface unit vectors -> sensor pixel coordinates at time t (no visibility test)."""
        P, z, up, right = self.state(t)
        v = u * self.R - P
        zc = v @ z
        xu = (v @ right) / zc; yu = (v @ up) / zc
        jx, jy = self.jitter(t)
        return self.norm_to_pix(xu - jx, yu - jy)

    def solve_target(self, latlon, anchor_px, t_ref):
        lat_t, lon_t = map(math.radians, latlon)
        self.lam_n0, self.u0 = lon_t, lat_t
        for _ in range(12):
            u, hit, _, _ = self.cast(np.array([anchor_px[0]]), np.array([anchor_px[1]]), t_ref)
            if not hit[0]:
                raise ValueError('target anchor pixel does not see the Moon')
            lat, lon = latlon_of(u)
            dlon = (lon_t - math.radians(lon[0]) + math.pi) % (2 * math.pi) - math.pi
            self.lam_n0 += dlon
            self.u0 += lat_t - math.radians(lat[0])

    def ground_scale_km(self, t=0.0):
        x0, y0, w, h = self.crop
        c, r = x0 + w / 2, y0 + h / 2
        u0, _, s, _ = self.cast(np.array([c, c + 1, c]), np.array([r, r, r + 1]), t)
        dx = np.linalg.norm(u0[1] - u0[0]) * self.R; dy = np.linalg.norm(u0[2] - u0[0]) * self.R
        u1, _, _, _ = self.cast(np.array([c]), np.array([r]), t + 1.0)
        cc, rr = self.project(u1, t)
        u2, _, _, _ = self.cast(np.array([c]), np.array([r]), t)
        c2, r2 = self.project(u2, t + 1.0)
        return dict(dx_km=float(dx), dy_km=float(dy), range_km=float(s[0]),
                    drift_px_s=[float(c2[0] - c), float(r2[0] - r)])


def latlon_of(u):
    lat = np.degrees(np.arcsin(np.clip(u[..., 2], -1, 1)))
    lon = np.degrees(np.arctan2(u[..., 1], u[..., 0])) % 360.0
    return lat, lon


def enu_basis(lat_deg, lon_deg):
    la, lo = np.radians(lat_deg), np.radians(lon_deg)
    up = np.stack([np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)], -1)
    east = np.stack([-np.sin(lo), np.cos(lo), np.zeros_like(lo)], -1)
    north = np.stack([-np.sin(la) * np.cos(lo), -np.sin(la) * np.sin(lo), np.cos(la)], -1)
    return east, north, up


def direction_from_subpoint(lat_deg, lon_deg):
    la, lo = math.radians(lat_deg), math.radians(lon_deg)
    return np.array([math.cos(la) * math.cos(lo), math.cos(la) * math.sin(lo), math.sin(la)])
