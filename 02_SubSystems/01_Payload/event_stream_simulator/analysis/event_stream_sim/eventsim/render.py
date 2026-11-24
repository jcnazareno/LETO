"""Side-by-side MP4 rendering: input scene (left) and event output (right), synchronised.

Left: log10 of the photo-electron rate (background + dark + flash) in grey, with the flash excess tinted amber.
Right: ON (amber) and OFF (blue) events accumulated over the last `window` seconds.
Overlays: injected flashes (circle; dashed white before detection, green once detected), particle hits (cyan
crosses for 0.3 s), trigger detections (magenta box for flashes, red box for false triggers) shown for 1 s.
"""
from __future__ import annotations
import math
import os
import subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import matplotlib

_FONT_DIR = os.path.join(os.path.dirname(matplotlib.__file__), 'mpl-data', 'fonts', 'ttf')


def font(size, mono=False):
    try:
        return ImageFont.truetype(os.path.join(_FONT_DIR, 'DejaVuSansMono.ttf' if mono else 'DejaVuSans.ttf'), size)
    except OSError:
        return ImageFont.load_default(size=size)


ON_RGB = np.array([255, 176, 46], float)
OFF_RGB = np.array([70, 150, 255], float)
BG_EV = np.array([18, 20, 26], float)


def flash_image(s, t):
    """Flash photo-electron rate per pixel at time t (same PSF and profile as the kernel)."""
    from scipy.special import erf
    out = np.zeros((s.h, s.w))
    O = s.optics
    s1 = O['psf.sigma_px']
    for f in s.flashes:
        tt = t - f['t_on']
        if tt <= 0 or tt > s.t_cut:
            continue
        r = 1 - math.exp(-tt / 2e-3)
        if f['kind'] == 'exp':
            pr = r * math.exp(-tt / f['tau_s'])
        elif f['kind'] == 'double':
            tf = f['tau_s'] / 10
            pr = r * (0.3 / tf * math.exp(-tt / tf) + 0.7 / f['tau_s'] * math.exp(-tt / f['tau_s']))
        else:
            pr = r * (1 + tt / f['tau_s']) ** -2.5
        cx, cy = f['x'] + f['vx'] * tt, f['y'] + f['vy'] * tt
        x0, x1 = max(0, int(cx) - 4), min(s.w, int(cx) + 5); y0, y1 = max(0, int(cy) - 4), min(s.h, int(cy) + 5)
        if x1 <= x0 or y1 <= y0:
            continue
        xs = np.arange(x0, x1 + 1); ys = np.arange(y0, y1 + 1)
        fx = np.diff(0.5 * erf((xs - cx) / (s1 * 2 ** 0.5))); fy = np.diff(0.5 * erf((ys - cy) / (s1 * 2 ** 0.5)))
        out[y0:y1, x0:x1] += f['electrons'] * f['norm'] * pr * fy[:, None] * fx[None, :]
    return out


def particle_image(s, t, persist=0.03):
    out = np.zeros((s.h, s.w))
    for hh in s.hits:
        if 0 <= t - hh['t'] < persist:
            for (x, y), e in zip(hh['pixels'], hh['deposits_e']):
                out[y, x] += e / persist
    return out


class Renderer:
    def __init__(self, sims, labels, title, window=0.033, fps=30, speed=1.0, panel_w=None, lo_hi=None,
                 overlays=True):
        self.sims = sims
        self.s0 = sims[0]
        self.labels = labels
        self.title = title
        self.window, self.fps, self.speed = window, fps, speed
        w, h = self.s0.w, self.s0.h
        npan = 1 + len(sims)
        target = panel_w or (960 if npan == 2 else 640)
        self.scale = max(1, int(round(target / w))) if w <= target else target / w
        self.pw = int(round(w * self.scale)); self.ph = int(round(h * self.scale))
        self.pw -= self.pw % 2; self.ph -= self.ph % 2
        self.head, self.foot, self.gap = 64, 36, 8
        self.W = npan * self.pw + (npan - 1) * self.gap
        self.H = self.head + self.ph + self.foot
        self.W += self.W % 2; self.H += self.H % 2
        bg = np.mean(self.s0.bg_chunks, 0)
        if lo_hi is None:
            lb = np.log10(np.maximum(bg, 1))
            lo = float(np.percentile(lb, 0.5)) - 0.05
            hi = max(float(np.percentile(lb, 99.7)) + 0.15, lo + 0.6)
            self.lo, self.hi, self.hi_flash = lo, hi, hi + 1.5
        else:
            self.lo, self.hi = lo_hi; self.hi_flash = self.hi + 1.5
        self.f_title = font(20); self.f_txt = font(15); self.f_mono = font(15, True); self.f_small = font(12)
        self.overlays = overlays
        self.ev_idx = [None for _ in sims]

    def _up(self, img):
        if isinstance(self.scale, int):
            return np.repeat(np.repeat(img, self.scale, 0), self.scale, 1)[:self.ph, :self.pw]
        im = Image.fromarray(img.astype(np.uint8))
        return np.asarray(im.resize((self.pw, self.ph), Image.NEAREST if self.scale >= 1 else Image.BOX))

    def input_panel(self, t):
        s = self.s0
        bg = s.scene.photo_rate(t).astype(np.float64) + s.dark_nominal      # per-pixel dark spread not shown
        fl = flash_image(s, t) + particle_image(s, t)
        lb = np.log10(np.maximum(bg, 1)); lt = np.log10(np.maximum(bg + fl, 1))
        g = np.clip((lb - self.lo) / (self.hi - self.lo), 0, 1) ** 0.9
        rgb = np.repeat((40 + 200 * g)[..., None], 3, -1)
        ex = np.clip((lt - lb) / 1.2, 0, 1)
        tint = np.array([255, 190, 80], float)
        rgb = rgb * (1 - ex[..., None]) + tint * ex[..., None]
        sat = np.clip((lt - self.hi) / (self.hi_flash - self.hi), 0, 1)
        rgb = rgb * (1 - sat[..., None]) + 255 * sat[..., None]
        return rgb.astype(np.uint8)

    def event_panel(self, k, t):
        s = self.sims[k]
        ev = s.events
        i0 = np.searchsorted(ev['t'], t - self.window); i1 = np.searchsorted(ev['t'], t)
        on = np.zeros(s.h * s.w); off = np.zeros(s.h * s.w)
        p = ev['p'][i0:i1]; pol = ev['pol'][i0:i1]
        np.add.at(on, p[pol == 1], 1); np.add.at(off, p[pol == -1], 1)
        a_on = np.clip(on / 2.0, 0, 1).reshape(s.h, s.w)[..., None] ** 0.6
        a_off = np.clip(off / 2.0, 0, 1).reshape(s.h, s.w)[..., None] ** 0.6
        rgb = BG_EV * (1 - np.maximum(a_on, a_off)) + ON_RGB * a_on + OFF_RGB * a_off * (1 - a_on)
        m = s.masked.reshape(s.h, s.w)
        rgb[m] = rgb[m] * 0.4 + np.array([60, 30, 30]) * 0.6
        return np.clip(rgb, 0, 255).astype(np.uint8), (i1 - i0) / self.window

    def _overlay(self, d, ox, t, sim):
        if not self.overlays:
            return
        sc = self.scale
        found = {}
        for det in sim.detections:
            if det['label'] == 'flash' and det['match'] not in found:
                found[det['match']] = det['t_trig']
        for i, f in enumerate(sim.flashes):
            tt = t - f['t_on']
            if -0.2 < tt < 3 * f['tau_s'] + 0.6:
                cx = ox + (f['x'] + f['vx'] * max(tt, 0)) * sc; cy = self.head + (f['y'] + f['vy'] * max(tt, 0)) * sc
                r = 4.5 * sc if sc >= 1 else 6
                det = i in found and t >= found[i]
                col = (90, 230, 120) if det else (235, 235, 235)
                if det:
                    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=col, width=2)
                else:
                    for a in range(0, 360, 30):
                        d.arc([cx - r, cy - r, cx + r, cy + r], a, a + 15, fill=col, width=2)
                if sc >= 2:
                    d.text((cx + r + 3, cy - r - 2), f"{f['E_J']:.0e} J, {f['tau_s'] * 1e3:.0f} ms", fill=col, font=self.f_small)
        for hh in sim.hits:
            if 0 <= t - hh['t'] < 0.3:
                for (x, y) in hh['pixels'][:1]:
                    cx = ox + (x + 0.5) * sc; cy = self.head + (y + 0.5) * sc; r = 3 * max(sc, 1.5)
                    d.line([cx - r, cy - r, cx + r, cy + r], fill=(80, 230, 255), width=2)
                    d.line([cx - r, cy + r, cx + r, cy - r], fill=(80, 230, 255), width=2)
        for det in sim.detections:
            if 0 <= t - det['t_trig'] < 1.0:
                x0 = ox + det['ax'] * sc; y0 = self.head + det['ay'] * sc; x1 = x0 + det['size'] * sc; y1 = y0 + det['size'] * sc
                pad = 3 * max(sc, 1)
                col = (240, 80, 240) if det['label'] == 'flash' else ((80, 230, 255) if det['label'] == 'particle' else (255, 60, 60))
                d.rectangle([x0 - pad, y0 - pad, x1 + pad, y1 + pad], outline=col, width=2)
                lab = 'TRIGGER' if det['label'] == 'flash' else ('PARTICLE TRIGGER' if det['label'] == 'particle' else 'FALSE TRIGGER')
                e = det.get('energy') or {}
                if e.get('e_corr_J') or e.get('e_raw_J'):
                    lab += f"  W={det['W']:g}s  E~{e.get('e_corr_J', e.get('e_raw_J')):.1e} J"
                d.text((x1 + pad + 2, y1 + pad - 12), lab, fill=col, font=self.f_small)

    def frame(self, t):
        img = np.zeros((self.H, self.W, 3), np.uint8)
        img[:] = (12, 14, 18)
        panels = [self.input_panel(t)]
        rates = []
        for k in range(len(self.sims)):
            pnl, r = self.event_panel(k, t)
            panels.append(pnl); rates.append(r)
        for i, pnl in enumerate(panels):
            x0 = i * (self.pw + self.gap)
            img[self.head:self.head + self.ph, x0:x0 + self.pw] = self._up(pnl)
        im = Image.fromarray(img); d = ImageDraw.Draw(im)
        d.text((12, 8), self.title, fill=(236, 238, 242), font=self.f_title)
        d.text((12, 38), f"t = {t:7.3f} s", fill=(255, 210, 120), font=self.f_mono)
        d.text((150, 38), f"accumulation {self.window * 1e3:.0f} ms", fill=(190, 195, 205), font=self.f_txt)
        for i, lab in enumerate(['input: photo-electron rate (log)'] + self.labels):
            x0 = i * (self.pw + self.gap)
            txt = lab if i == 0 else f"{lab}   {rates[i - 1] / 1e3:7.1f} kev/s"
            d.text((x0 + 8, self.head + 6), txt, fill=(236, 238, 242), font=self.f_txt)
        if self.overlays:
            for i in range(len(self.sims) + 1):
                self._overlay(d, i * (self.pw + self.gap), t, self.sims[max(i - 1, 0)])
        y = self.head + self.ph + 10
        leg = [((255, 176, 46), 'ON event'), ((70, 150, 255), 'OFF event'), ((235, 235, 235), 'injected flash'),
               ((90, 230, 120), 'flash detected'), ((240, 80, 240), 'trigger'), ((80, 230, 255), 'particle hit'),
               ((255, 60, 60), 'false trigger'), ((150, 70, 70), 'masked pixel')]
        x = 12
        for col, txt in leg:
            d.rectangle([x, y + 2, x + 12, y + 14], fill=col)
            d.text((x + 17, y), txt, fill=(200, 204, 212), font=self.f_small)
            x += 22 + int(d.textlength(txt, font=self.f_small)) + 14
        lo, hi = self.lo, self.hi
        d.text((self.W - 330, y), f"input grey scale: 10^{lo:.2f} to 10^{hi:.2f} e-/s", fill=(160, 165, 175), font=self.f_small)
        return np.asarray(im)

    def write_mp4(self, path, t0=0.0, t1=None):
        t1 = t1 if t1 is not None else self.s0.duration
        n = int((t1 - t0) * self.fps / self.speed)
        cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{self.W}x{self.H}',
               '-r', str(self.fps), '-i', '-', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '23', '-preset', 'medium',
               '-movflags', '+faststart', path]
        pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        for k in range(n):
            t = t0 + (k + 1) * self.speed / self.fps
            pr.stdin.write(self.frame(min(t, t1)).tobytes())
        pr.stdin.close(); pr.wait()
        return n

    def still(self, path, t):
        Image.fromarray(self.frame(t)).save(path)
