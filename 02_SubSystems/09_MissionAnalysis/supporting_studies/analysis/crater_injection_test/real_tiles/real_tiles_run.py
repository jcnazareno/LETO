"""Crater-injection test on real LROC NAC tiles (3 November 2026).

Data: the 0.5 m/px NAC CDR tiles of the CraterDANet dataset (Yang et al., IEEE TGRS; GPL-3.0),
    git clone https://github.com/yizuifangxiuyh/Lunar_Crater_Detection_Data
Only the four test tiles whose source images have native pixels of 0.60-0.84 m are used (the others are
coarser than the 0.9 m crater camera or strongly oblique). Sun incidence: LROC observation pages.
Sun azimuth in tile coordinates: fitted to the dataset's labelled craters (`fit-az`), see sun_geometry.json.

Usage (run with an isolated interpreter, data outside this folder):
    python -I real_tiles_run.py fit-az  DATA_DIR            -> sun_geometry.json
    python -I real_tiles_run.py inject  DATA_DIR TILE OUT [depth rim halo]
Defaults: depth/diameter 0.14, rim 0.028, halo 0.075 (central case; Stopar et al. 2017 give 0.11-0.17 for
fresh craters below 400 m). The signal scales with cos(incidence) for the same 0.34 ms exposure.
"""
import sys, csv, json, math
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import crater_test as ct

TILES = {'M1305967189RE_cal_echo_11_2': 81.67, 'M1183658592LE_cal_echo_23_0': 67.47,
         'M1229577647LE_cal_echo_14_4': 65.87, 'M1303619844LE_cal_echo_26_2': 62.64}
GSD = 0.5


def fit_az(data_dir, n_max=250, step=20):
    rng = np.random.default_rng(0); cfg = dict(ct.DEFAULTS); out = {}
    for name, inc in TILES.items():
        img = ct.read_image(Path(data_dir) / f'{name}.png'); img = img / np.median(img)
        cr = [(float(r['CY']), float(r['C_X']), float(r['W'])) for r in csv.DictReader(open(Path(data_dir) / f'{name}.txt'))
              if 8 <= float(r['W']) <= 30]
        if len(cr) > n_max:
            cr = [cr[i] for i in rng.choice(len(cr), n_max, replace=False)]
        azs = np.arange(0, 360, step); sc = []
        for az in azs:
            s = 0.0
            for l, smp, w in cr:
                ratio, h = ct.render_ratio(w * GSD, GSD, inc, az, cfg, oversample=2)
                li, si = int(round(l)), int(round(smp))
                if li - h < 0 or si - h < 0 or li + h + 1 > img.shape[0] or si + h + 1 > img.shape[1]:
                    continue
                p = img[li - h:li + h + 1, si - h:si + h + 1]; t = ratio - ratio.mean(); q = p - p.mean()
                s += (t * q).sum() / (np.linalg.norm(t) * np.linalg.norm(q) + 1e-9)
            sc.append(s / max(len(cr), 1))
        sc = np.array(sc); i = int(np.argmax(sc))
        out[name] = dict(inc=inc, az_best=float(azs[i]), score_best=float(sc[i]), score_opposite=float(sc[(i + len(azs) // 2) % len(azs)]), n_craters=len(cr))
        print(name, out[name], flush=True)
    json.dump(out, open(HERE / 'sun_geometry.json', 'w'), indent=1)


def inject(data_dir, name, out, depth=0.14, rim=0.028, halo=0.075):
    g = json.load(open(HERE / 'sun_geometry.json'))[name]
    cfg = dict(ct.DEFAULTS, depth=depth, rim=rim, halo_amp=halo)
    cfg['signal_e'] = 300.0 * math.cos(math.radians(g['inc'])) / math.cos(math.radians(65.0))
    img = ct.read_image(Path(data_dir) / f'{name}.png').astype(np.float32)
    img = np.clip(img, 1, None) / np.median(img)
    ct.run_injection(img, None, GSD, g['inc'], g['az_best'], cfg, out, D_grid=[1.8, 2.2, 2.5, 2.8, 3.1, 3.4, 3.8, 4.4, 5.5, 8.0],
                     n_per_D=45, seed=13, label=name[:13])


if __name__ == '__main__':
    if sys.argv[1] == 'fit-az':
        fit_az(sys.argv[2])
    else:
        inject(sys.argv[2], sys.argv[3], sys.argv[4], *map(float, sys.argv[5:8]))
