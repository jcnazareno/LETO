"""Cut before/after windows around each catalogued new crater from the full NAC CDR images (team computer).

Input:  data/external/NAC_CDR/<product>C.IMG (PDS3, LSB int16 scaled I/F, 5064 samples, 2 label records of 5064
        bytes) for the products in nac_pairs.json.
Output: tmp/nac_chips/windows/win_<id>b.npz and win_<id>a.npz (raw DN, window origin, predicted crater position,
        pixel scale, incidence, product ID). The window is +-1500 before pixels around the position predicted from
        the image corners (bilinear in lat/lon; accurate to about 0.1-0.7 km) and covers the same ground in the after
        image plus a margin.
Usage:  python cut_windows.py C1 C2 ...      (all craters if no IDs are given)
"""
import json, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
CDR = os.path.join(ROOT, 'data', 'external', 'NAC_CDR')
OUT = os.path.join(ROOT, 'tmp', 'nac_chips', 'windows')
S = 5064                         # samples per line (one line = two 5064-byte records)


def label_bytes(path):
    """Offset of the image in bytes: ^IMAGE pointer (records) x RECORD_BYTES from the attached label."""
    head = open(path, 'rb').read(20000).decode('latin-1')
    import re
    rb = int(re.search(r'RECORD_BYTES\s*=\s*(\d+)', head).group(1))
    m = re.search(r'\^IMAGE\s*=\s*(\d+)', head)
    return (int(m.group(1)) - 1) * rb if m else rb


def line_sample(img, lat, lon, g):
    C = np.array(g[img]['c']); lon = lon % 360; u, v = 0.5, 0.5
    for _ in range(50):
        P = (1 - u) * (1 - v) * C[0] + u * (1 - v) * C[1] + (1 - u) * v * C[2] + u * v * C[3]
        Pu = -(1 - v) * C[0] + (1 - v) * C[1] - v * C[2] + v * C[3]
        Pv = -(1 - u) * C[0] - u * C[1] + (1 - u) * C[2] + u * C[3]
        d = np.linalg.solve(np.array([Pu, Pv]).T, np.array([lat, lon]) - P); u += d[0]; v += d[1]
    return v * g[img]['L'], u * S


def main(ids):
    meta = json.load(open(os.path.join(HERE, 'nac_pairs.json')))
    g = meta['images']
    os.makedirs(OUT, exist_ok=True)
    for c in meta['craters']:
        if ids and c['id'] not in ids:
            continue
        for img, tag in ((c['before'], 'b'), (c['after'], 'a')):
            path = os.path.join(CDR, img + 'C.IMG')
            l, s = line_sample(img, c['lat'], c['lon'], g); L = g[img]['L']
            mm = np.memmap(path, dtype='<i2', mode='r', offset=label_bytes(path), shape=(L, S))
            half = 1500 if tag == 'b' else int(1500 * g[c['before']]['res'] / g[img]['res']) + 150
            l0, l1 = int(max(0, l - half)), int(min(L, l + half)); s0, s1 = int(max(0, s - half)), int(min(S, s + half))
            np.savez_compressed(os.path.join(OUT, f"win_{c['id']}{tag}.npz"), dn=np.array(mm[l0:l1, s0:s1]), origin=[l0, s0],
                                pred=[l, s], res=g[img]['res'], inc=g[img]['inc'], img=img)
            print(c['id'], tag, img, l1 - l0, s1 - s0, flush=True)


if __name__ == '__main__':
    main(sys.argv[1:])
