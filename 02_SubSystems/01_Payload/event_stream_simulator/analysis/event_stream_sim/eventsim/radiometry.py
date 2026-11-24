"""Radiometric chain: scene radiance and flash energy -> detected photo-electrons per pixel.

Conventions are those of S10/S13: detected photons are counted at an effective 750 nm in the 600-900 nm band,
flash light energy E_L is hemispheric-equivalent (uniform emission into 2 pi sr), and a Lambertian surface of
reflectance rho under irradiance E has radiance rho * E * f_band / pi.
"""
import math

H, C_LIGHT, Q_E = 6.62607015e-34, 2.99792458e8, 1.602176634e-19


class Radiometry:
    def __init__(self, sensor, optics, env):
        self.lam = optics['lambda_eff_nm'] * 1e-9
        self.e_ph = H * C_LIGHT / self.lam
        self.D = optics['aperture_m']
        self.f = optics['focal_length_m']
        self.T = optics['transmission']
        self.qe = sensor['qe.effective_750nm']
        self.pitch = sensor['array.pixel_pitch_um'] * 1e-6
        self.A_ap = math.pi * (self.D / 2) ** 2
        self.omega_pix = (self.pitch / self.f) ** 2
        self.ifov = self.pitch / self.f
        self.env = env

    # --- point source (flash) ---
    def flash_electrons_per_J(self, d_km):
        """Detected electrons per joule of hemispheric-equivalent band light at range d_km (S10 flash_electrons)."""
        return 1.0 / self.e_ph * self.A_ap / (2 * math.pi * (d_km * 1e3) ** 2) * self.T * self.qe

    # --- extended sources ---
    def radiance_to_e_s(self, L_W_m2_sr):
        return L_W_m2_sr * self.A_ap * self.omega_pix * self.T * self.qe / self.e_ph

    def lambert_e_s(self, irradiance_W_m2, rho):
        return self.radiance_to_e_s(rho * irradiance_W_m2 * self.env['band.solar_fraction'] / math.pi)

    def earthshine_full_e_s(self):
        """Full Earth at zenith on the mean-reflectance surface (S13: 1.85e4 e-/s for the 16 mm f/1 head)."""
        return self.lambert_e_s(self.env['earthshine.reflected_irradiance_W_m2'], self.env['surface.reflectance_mean'])

    def sunlit_e_s(self):
        """Sun at zenith on the mean-reflectance surface."""
        return self.lambert_e_s(self.env['sun.irradiance_W_m2'], self.env['surface.reflectance_mean'])


def dark_e_s(fA):
    return fA * 1e-15 / Q_E


def earth_phase_lambert(alpha_rad):
    """Lambert-sphere phase law of the Earth (1 at full Earth), as in S13."""
    a = alpha_rad
    return (math.sin(a) + (math.pi - a) * math.cos(a)) / math.pi
