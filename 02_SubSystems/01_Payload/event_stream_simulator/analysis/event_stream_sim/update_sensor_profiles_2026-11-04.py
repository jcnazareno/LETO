"""Stage 3 of the 4 Nov 2026 update: sensor values from data/external/sensor_values/ (applied once; idempotent).

References read:
  [T] G. Hahmeyer, Event Camera Observation and Tracking Strategies for the EventSat Mission, Bachelor thesis,
      TU Munich, 7 Dec 2025. Prophesee EVK4 (IMX636), indoor LCD test box, room temperature (not reported),
      recording durations not stated. Sect. 3.2 (p. 17), Fig. 3.2 (p. 18), Table 2.1 (p. 9) and Table 3.2 (p. 15).
  [W] S. Dolan, A. Golkar, Sun-E: Dataset and Benchmark for Event-Based Sun Sensing (WACV). High-illumination sun
      simulator; no low-light, dark-current or temperature values for the profile keys.
Only one value is replaced (baseline hot-pixel fraction at default biases). Other findings widen uncertainty
ranges or add notes; they are not replacements, because conditions (illuminance, temperature, duration) are not
stated. Prints the old-vs-new table that event_stream_sim.md reproduces.
"""
from __future__ import annotations
import json
from pathlib import Path

PROF = Path(__file__).resolve().parent / 'profiles'
T = 'Hahmeyer 2025 (EventSat bachelor thesis, TUM)'
rows = []


def edit(fname, key, **kw):
    p = PROF / fname
    d = json.loads(p.read_text())
    P = d['params']
    old = dict(P.get(key, {}))
    new = dict(old)
    if 'value' in kw and old.get('value') != kw['value']:
        new['previous'] = dict(value=old.get('value'), source=old.get('source'), status=old.get('status'), replaced='2026-11-04')
    new.update(kw)
    P[key] = new
    p.write_text(json.dumps(d, indent=2, ensure_ascii=False) + '\n')
    rows.append((fname, key, old.get('value'), new.get('value'), new.get('status'), 'value' in kw and old.get('value') != kw['value']))


# 1. baseline (default biases): hot-pixel fraction -- the 2% came from McReynolds' tuned-bias measurement
edit('sensor_imx636.json', 'hot.fraction', value=1.1e-5, unit='share of pixels', status='measured',
     uncertainty='1e-5 to 2e-2: [T] finds 1 defective pixel plus 9 consistently most active of 921,600 (99.999th-percentile cut, so the 9 follow from the cut); upper end = tuned-bias value (McReynolds et al. 2025)',
     source=f'{T}, Sect. 3.2 p. 17 and Fig. 3.2a-b p. 18: at default biases one defective pixel (~4.5e7 events per recording) and otherwise no hot tail (no pixel above ~50 events per recording after its removal). EVK4, LCD test box, room temperature, recording length not stated')
# tuned biases keep the 2% population explicitly (no longer inherited from the baseline)
edit('sensor_imx636_tuned.json', 'hot.fraction', value=0.02, unit='share of pixels', status='measured',
     uncertainty='0.5-5%; [T] Fig. 3.2c-f (p. 18) shows a broad per-pixel tail at the same low-light bias set (IMX-6/IMX-7) that needs a 1% mask',
     source='McReynolds et al. 2025 (~2% hot pixels at tuned biases); consistent with [T] Fig. 3.2c-f')
# IMX646 surrogate follows the IMX636 default-bias value
edit('sensor_imx646.json', 'hot.fraction', value=1.1e-5, unit='share of pixels', status='surrogate',
     uncertainty='not published for the IMX646; 1e-5 to 2e-2 as for the IMX636',
     source=f'IMX636 default-bias value ({T}) used as surrogate')
# 2. background activity: no replacement; ranges widened
edit('sensor_imx636.json', 'ba.rate_hz',
     uncertainty='0.003-0.1; [T] Sect. 3.2 p. 17: 2.6 kev/s over the array (2.8e-3 ev/s/px) with the camera in the closed test box and the monitor off, default biases, illuminance and temperature not reported',
     note='[T] dark-box rate is 10x below the adopted McReynolds value; kept McReynolds (calibrated light level) as the conservative value')
edit('sensor_imx636_tuned.json', 'ba.rate_hz',
     uncertainty='1-3.5; [T] Sect. 3.2 p. 17: 3197 kev/s (3.5 ev/s/px) for bias set IMX-6 and 1887 kev/s (2.0 ev/s/px) for IMX-7, monitor off; IMX-6 is the McReynolds low-light bias set ([T] Table 3.2, p. 15)')
# 3. refractory period: the low-light bias set lengthens it
edit('sensor_imx636_tuned.json', 'events.refractory_s', value=1e-05, unit='s', status='assumed',
     uncertainty='longer than default: the low-light bias set uses bias_refr = -20 ([T] Table 3.2 p. 15; Table 2.1 p. 9: increasing bias_refr shortens the refractory period); absolute value not published',
     source='assumption; see note',
     note='conflicts with the proposed requirement refractory <= 10 us (V6) unless bias_refr is reset; flagged for the team')
# 4. temperature: qualitative only -> no warm/cold profile
edit('sensor_imx636.json', 'dark.doubling_temperature_C',
     note=f'{T} Sect. 2.1 (p. 9) cites Schuberth et al. (IAC 2025): fewer but more active hot pixels at higher temperature and a sharp rise of OFF events below -4 degC; qualitative, no dark-current law, so no warm/cold profile was derived')

if __name__ == '__main__':
    print('| Profile | Key | Old | New | Status | Replaced |')
    print('|---|---|---|---|---|---|')
    for f, k, o, n, s, r in rows:
        print(f'| {f} | {k} | {o} | {n} | {s} | {"yes" if r else "note/range only"} |')
