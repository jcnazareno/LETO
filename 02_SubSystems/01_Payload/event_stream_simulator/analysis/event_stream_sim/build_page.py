"""Build the self-contained interactive page from stored runs (no simulation is rerun).

  python build_page.py            -> outputs/event_stream_sim.html
Inputs: data/<tag>_events.npz, <tag>_truth.json, <tag>_keyframes.npz for the tags in SCENES.
Events are embedded as base64 little-endian uint32 pairs (t in us; x | y << 11 | ON << 22), background keyframes
as 8-bit PNG data URIs (log10 rate scale), ground truth as JSON. Size limit 12 MB (events are truncated in time
for a scene whose stream would exceed its budget; the page says so).
"""
from __future__ import annotations
import base64
import io
import json
import math
import sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DATA = ROOT / 'data'
OUT = ROOT / 'outputs'

SCENES = [
    dict(id='nearside', tags=['nearside_imx636'], title='Near side', budget=2.2e6,
         note='Copernicus region in earthshine. WAC 643 nm albedo with Lunar-Lambert shading of LOLA slopes, drifting along track with the orbit. Texture produces ON and OFF events as albedo edges move; the trigger thresholds follow the local background.'),
    dict(id='farside', tags=['farside_imx636'], title='Far side', budget=1.6e6,
         note='Dark far side: dark current only. Background activity, rare particle hits and the injected flashes are the only sources of events.'),
    dict(id='particles', tags=['particles_imx636'], title='Particles', budget=1.8e6,
         note='Far side during an assumed solar-particle event (100 pfu above 10 MeV, about 314 particles per cm2 per s before shielding), with hot pixels. Deposits are instantaneous; the one-count-per-step rule keeps them from triggering.'),
    dict(id='particles_crater', tags=['particles_gcrmin_x100_imx636'], title='Particles (CRaTER GCR)', budget=1.8e6,
         note='Far side with galactic cosmic rays from the LRO CRaTER spectrum at solar minimum (4 Nov 2026 update): 4.05 hits per cm2 per s at 3000 km, here multiplied by 100 for statistics (equivalent to 100 crop runs). Charge per pixel from the measured LET through a 3 um layer; tracks cover 1-3 pixels. None of the 102 hits triggers.'),
    dict(id='terminator', tags=['terminator_imx636'], title='Terminator', budget=2.6e6,
         note='Montes Apenninus at sunrise: sunlit surface at the east edge and lit peaks in the dark. Sunlit pixels drift through the view and fire many events; groups above 1e5 e-/s are excluded from the trigger by the illumination mask.'),
    dict(id='terminator_far', tags=['terminator_far_imx636'], title='Far-side terminator', budget=2.6e6,
         note='Tsiolkovsky (20.4 S, 129.1 E) at sunrise, from the far-side WAC and LOLA maps added on 4 Nov 2026. Sunlit rim and central peak in dark, earthshine-free surroundings; groups above 1e5 e-/s are excluded from the trigger by the illumination mask.'),
    dict(id='limb', tags=['limb_imx636'], title='Limb', budget=1.6e6,
         note='Outer head of the 2 x 3 mosaic, crop at the corner where the line of sight passes the limb (about 21.5 deg off nadir). Ground pixels near the limb are 5 km across and the limb itself barely moves.'),
    dict(id='compare', tags=['compare_nearside_imx636', 'compare_nearside_imx646'], title='IMX636 vs IMX646', budget=1.4e6,
         note='The same near-side scene (Copernicus under a nearly full Earth, about 2.3e4 e-/s), faint slow flashes and random seed for the measured-data IMX636 profile and the IMX646 surrogate (half the photoreceptor time constant; no published low-light data).'),
]


def b64(a):
    a = np.ascontiguousarray(a)
    if a.size and (int(a.min()) < 0 or int(a.max()) > 2 ** 32 - 1):
        raise ValueError('value outside uint32 (event times above 4295 s cannot be packed for the page)')
    return base64.b64encode(a.astype('<u4').tobytes()).decode('ascii')


def png_uri(img8):
    bio = io.BytesIO()
    Image.fromarray(img8).save(bio, format='PNG', optimize=True)
    return 'data:image/png;base64,' + base64.b64encode(bio.getvalue()).decode('ascii')


def bits_b64(mask):
    return base64.b64encode(np.packbits(mask.ravel().astype(np.uint8)).tobytes()).decode('ascii')


def stream(tag, budget):
    z = np.load(DATA / f'{tag}_events.npz')
    tr = json.loads((DATA / f'{tag}_truth.json').read_text())
    t = z['t_us'].astype(np.int64); x = z['x'].astype(np.int64); y = z['y'].astype(np.int64); p = z['p']
    t_max = None
    if t.size * 8 * 4 / 3 > budget:
        n = int(budget * 3 / 4 / 8)
        t_max = float(t[n - 1]) / 1e6
        t, x, y, p = t[:n], x[:n], y[:n], p[:n]
    xyp = x | (y << 11) | ((p == 1).astype(np.int64) << 22)
    dets = [dict(t=d['t_trig'], ax=d['ax'], ay=d['ay'], s=d['size'], W=d['W'], label=d['label'], m=d['match'],
                 E=(d.get('energy') or {}).get('e_corr_J') or (d.get('energy') or {}).get('e_raw_J'))
            for d in tr['detections']]
    sm = tr['summary']; st = tr['stats']
    prof = tr['config']['profiles']['sensor']
    return dict(name=tr['config']['sensor'], t=b64(t), xyp=b64(xyp), n=int(t.size), t_max=t_max,
                masked=bits_b64(z['masked']), dets=dets,
                stats=dict(n_events=st['n_events'], ev_rate=st['n_events'] / tr['config']['duration_s'],
                           n_flashes=sm['n_flashes'], n_detected=sm['n_detected'], n_false=sm['n_false'],
                           n_part_trig=sm['n_particle_triggers'], n_hits=sm['n_particle_hits'], n_heavy=sm['n_heavy_hits'],
                           masked=int(z['masked'].sum()), hot=int(z['hot'].sum()), wall=st.get('wall_total_s')),
                per_flash=sm['per_flash'], profile_desc=prof['description'][:300]), tr, z


def build():
    scenes = []
    total = 0
    for S in SCENES:
        if not all((DATA / f'{t}_truth.json').exists() for t in S['tags']):
            print('skip', S['id'], '(missing run)'); continue
        streams = []
        for tag in S['tags']:
            st, tr, z = stream(tag, S['budget'] / len(S['tags']))
            streams.append(st)
        kf = np.load(DATA / f"{S['tags'][0]}_keyframes.npz")
        L = kf['log10_rate']
        lo = float(np.percentile(L, 0.5)) - 0.05
        hi = max(float(np.percentile(L, 99.7)) + 0.15, lo + 0.6)
        pngs = [png_uri(np.clip(np.round((l - lo) / (hi - lo) * 255), 0, 255).astype(np.uint8)) for l in L]
        fl = [dict(t=f['t_on'], x=f['x'], y=f['y'], vx=f['vx'], vy=f['vy'], E=f['E_J'], tau=f['tau_s'], kind=f['kind'],
                   el=f['electrons'] * f['norm'], d=f['range_km']) for f in tr['flashes']]
        hits = [dict(t=h['t'], px=h['pixels'], heavy=h['heavy'], e=max(h['deposits_e'])) for h in tr['particle_hits']]
        meta = tr['scene']
        g = meta.get('ground', {})
        scenes.append(dict(id=S['id'], title=S['title'], label=meta['scene'] if 'label' not in meta else meta['label'],
                           desc=S['note'], w=int(z['masked'].shape[1]), h=int(z['masked'].shape[0]),
                           duration=tr['config']['duration_s'], kf_t=kf['t'].tolist(), kf=pngs, lo=lo, hi=hi,
                           drift=[float(v) for v in kf['drift_px_s']], flashes=fl, hits=hits, streams=streams,
                           ground=dict(dx_km=g.get('dx_km'), dy_km=g.get('dy_km'), range_km=g.get('range_km')),
                           crop=tr['config']['crop'], head=meta.get('head'), earth_phase=meta.get('earth_phase_deg'),
                           psf=tr['config']['profiles']['optics']['params']['psf.sigma_px']['value']))
        print(S['id'], [s['n'] for s in streams])
    payload = json.dumps(scenes, separators=(',', ':'))
    html = TEMPLATE.replace('__DATA__', payload)
    path = OUT / 'event_stream_sim.html'
    path.write_text(html, encoding='utf-8')
    print(f'{path} {path.stat().st_size / 1e6:.2f} MB')
    return path


TEMPLATE = r"""<title>Event Stream Simulator</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow+Semi+Condensed:wght@500;600&family=Barlow:wght@400;500&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
/* Layout: an instrument console. Scene tabs, then the two synchronised displays (input | events), a transport
   bar, and the run's ground-truth tables underneath. Displays stay dark in both themes, like a monitor. */
:root {
  --bg: #eef0f2; --surface: #ffffff; --ink: #1b1f24; --muted: #5b6470; --line: #d3d8de;
  --accent: #b86a00; --on: #ffb02e; --off: #4696ff; --display: #12141a; --display-ink: #e6e8ec;
  --ok: #1f8a4c; --bad: #c43c3c; --trig: #b03ab0; --chip: #e3e7eb;
  --f-display: "Barlow Semi Condensed", "Arial Narrow", system-ui, sans-serif;
  --f-body: "Barlow", system-ui, -apple-system, "Segoe UI", sans-serif;
  --f-mono: "IBM Plex Mono", ui-monospace, "SFMono-Regular", Menlo, monospace;
}
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {
  --bg: #0d1014; --surface: #161a20; --ink: #e4e7eb; --muted: #98a1ad; --line: #2a3038;
  --accent: #ffb02e; --ok: #4fc27f; --bad: #ff6b6b; --trig: #e07ae0; --chip: #222831; color-scheme: dark } }
:root[data-theme="dark"] {
  --bg: #0d1014; --surface: #161a20; --ink: #e4e7eb; --muted: #98a1ad; --line: #2a3038;
  --accent: #ffb02e; --ok: #4fc27f; --bad: #ff6b6b; --trig: #e07ae0; --chip: #222831; color-scheme: dark }
* { box-sizing: border-box }
body { background: var(--bg); color: var(--ink); font-family: var(--f-body); font-size: 15px; line-height: 1.45; margin: 0 }
.wrap { max-width: 1240px; margin: 0 auto; padding-block: 20px 40px;
  padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px));
  display: grid; gap: 16px }
header { display: grid; gap: 4px }
h1 { font-family: var(--f-display); font-weight: 600; font-size: 1.9rem; margin: 0; letter-spacing: .01em; text-wrap: balance }
.sub { color: var(--muted); max-width: 72ch; margin: 0 }
h2 { font-family: var(--f-display); font-weight: 600; font-size: 1.15rem; margin: 0 0 6px; letter-spacing: .02em }
.tabs { display: flex; flex-wrap: wrap; gap: 6px }
.tabs button { font: 500 .95rem var(--f-display); letter-spacing: .03em; padding: 6px 12px; border-radius: 4px;
  border: 1px solid var(--line); background: var(--surface); color: var(--ink); cursor: pointer }
.tabs button[aria-pressed="true"] { background: var(--ink); color: var(--bg); border-color: var(--ink) }
button:focus-visible, input:focus-visible, select:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px }
.desc { color: var(--muted); margin: 0; max-width: 90ch }
.displays { display: grid; grid-template-columns: 1fr 1fr; gap: 8px }
.displays.three { grid-template-columns: 1fr 1fr 1fr }
.disp { background: var(--display); border-radius: 6px; overflow: hidden; min-width: 0; display: grid }
.disp .cap { color: var(--display-ink); font: 500 .8rem var(--f-mono); padding: 6px 10px; display: flex; justify-content: space-between; gap: 8px; flex-wrap: wrap }
.disp .cap span:last-child { color: #9aa3ad }
.stage { position: relative; width: 100%; aspect-ratio: var(--ar, 16/9); max-width: 100% }
.stage canvas { position: absolute; inset: 0; width: 100%; height: 100% }
.stage canvas.px { image-rendering: pixelated }
.transport { display: grid; grid-template-columns: auto 1fr auto; gap: 10px 14px; align-items: center;
  background: var(--surface); border: 1px solid var(--line); border-radius: 6px; padding: 10px 12px }
.transport .row2 { grid-column: 1 / -1; display: flex; flex-wrap: wrap; gap: 8px 18px; align-items: center }
.play { font: 600 .95rem var(--f-display); letter-spacing: .04em; min-width: 76px; padding: 7px 12px; border-radius: 4px;
  border: 0; background: var(--accent); color: #1b1f24; cursor: pointer }
.time { font: 500 1rem var(--f-mono); font-variant-numeric: tabular-nums; white-space: nowrap }
input[type=range] { width: 100%; accent-color: var(--accent) }
label.ctl { display: inline-flex; gap: 6px; align-items: center; font-size: .9rem; color: var(--muted) }
label.ctl select, label.ctl input[type=range] { width: auto }
#win { width: 130px }
.chk { display: inline-flex; gap: 5px; align-items: center; font-size: .9rem }
.legend { display: flex; flex-wrap: wrap; gap: 6px 14px; font-size: .82rem; color: var(--muted) }
.legend i { display: inline-block; width: 11px; height: 11px; border-radius: 2px; margin-right: 5px; vertical-align: -1px }
.spark { width: 100%; height: 46px; display: block }
.grid2 { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1.4fr); gap: 16px }
.card { background: var(--surface); border: 1px solid var(--line); border-radius: 6px; padding: 12px 14px; min-width: 0 }
.kv { display: grid; grid-template-columns: auto 1fr; gap: 3px 14px; font-size: .9rem; margin: 0 }
.kv dt { color: var(--muted) } .kv dd { margin: 0; font-family: var(--f-mono); font-variant-numeric: tabular-nums }
.tbl { overflow-x: auto }
table { border-collapse: collapse; width: 100%; font-size: .85rem }
th, td { text-align: right; padding: 4px 8px; border-bottom: 1px solid var(--line); white-space: nowrap; font-variant-numeric: tabular-nums }
th { font: 600 .85rem var(--f-display); letter-spacing: .03em; color: var(--muted) }
td:first-child, th:first-child { text-align: left }
td { font-family: var(--f-mono) }
.pill { display: inline-block; padding: 0 7px; border-radius: 10px; font: 500 .75rem var(--f-body); background: var(--chip) }
.pill.ok { color: var(--ok) } .pill.bad { color: var(--bad) }
td button { font: 500 .78rem var(--f-body); border: 1px solid var(--line); background: transparent; color: var(--ink); border-radius: 3px; cursor: pointer; padding: 1px 6px }
.note { font-size: .82rem; color: var(--muted); max-width: 95ch; margin: 0 }
@media (max-width: 760px) {
  .displays, .displays.three { grid-template-columns: 1fr }
  .grid2 { grid-template-columns: 1fr }
  h1 { font-size: 1.5rem }
  .transport { grid-template-columns: auto 1fr }
  .transport .time { grid-column: 1 / -1 }
}
@media (prefers-reduced-motion: reduce) { * { scroll-behavior: auto } }
</style>
<div class="wrap">
  <header>
    <h1>Event Stream Simulator</h1>
    <p class="sub">Simulated IMX636 event output for one camera head on the 3000 km lunar monitor: the scene photocurrent on the left, the ON/OFF events on the right, with injected flashes, particle hits and on-board trigger detections. Model results, not sensor measurements. The page replays stored runs (long streams are cut in time, as labelled); flash, particle and false/flash labels on detections come from the simulation's ground truth, not from an on-board classifier.</p>
  </header>
  <nav class="tabs" id="tabs" aria-label="Scene"></nav>
  <p class="desc" id="desc"></p>
  <section class="displays" id="displays"></section>
  <div class="transport">
    <button class="play" id="play" type="button">Play</button>
    <input type="range" id="scrub" min="0" max="1000" value="0" step="1" aria-label="Time">
    <span class="time" id="tlabel">0.000 s</span>
    <div class="row2">
      <label class="ctl" for="speed">Speed
        <select id="speed"><option value="0.1">0.1×</option><option value="0.25">0.25×</option><option value="0.5">0.5×</option><option value="1" selected>1×</option><option value="2">2×</option><option value="4">4×</option></select></label>
      <label class="ctl" for="win">Accumulate <input type="range" id="win" min="0" max="100" value="66"> <span class="time" id="winlabel">33 ms</span></label>
      <label class="chk" for="o_fl"><input type="checkbox" id="o_fl" checked> Flashes</label>
      <label class="chk" for="o_tr"><input type="checkbox" id="o_tr" checked> Triggers</label>
      <label class="chk" for="o_pa"><input type="checkbox" id="o_pa" checked> Particles</label>
      <label class="chk" for="o_ma"><input type="checkbox" id="o_ma"> Masked pixels</label>
    </div>
    <div class="row2"><canvas class="spark" id="spark" aria-label="Event rate over the run"></canvas></div>
    <div class="row2 legend">
      <span><i style="background:var(--on)"></i>ON event</span><span><i style="background:var(--off)"></i>OFF event</span>
      <span><i style="background:#e8e8e8"></i>injected flash (dashed until detected)</span><span><i style="background:#5ae67a"></i>detected flash</span>
      <span><i style="background:#f050f0"></i>trigger</span><span><i style="background:#50e6ff"></i>particle hit</span>
      <span><i style="background:#ff3c3c"></i>false trigger</span><span><i style="background:#963c3c"></i>masked pixel</span>
    </div>
  </div>
  <section class="grid2">
    <div class="card"><h2>Run</h2><dl class="kv" id="kv"></dl></div>
    <div class="card"><h2>Injected flashes</h2><div class="tbl"><table id="ftab"></table></div>
      <p class="note">E_L is band light energy (600–900 nm, hemispheric-equivalent). Energy estimates are event-only, corrected with the regression trained on this simulator (S11 style) where a calibration exists, otherwise raw.</p></div>
  </section>
  <p class="note">Sources: event model in analysis/event_stream_sim (README); scenes from LRO WAC 643 nm and LOLA LDEM_64; trigger thresholds from event_response.py (S10). Sensor values for the IMX646 are surrogates.</p>
</div>
<script>
const SCENES = __DATA__;
const $ = id => document.getElementById(id);
const st = { scene: 0, t: 0, playing: false, speed: 1, win: 0.033, last: null, ov: { fl: true, tr: true, pa: true, ma: false } };
let cur = null;

function dec(b64) { const s = atob(b64); const u = new Uint8Array(s.length); for (let i = 0; i < s.length; i++) u[i] = s.charCodeAt(i); return u; }
function u32(b64) { const u = dec(b64); return new Uint32Array(u.buffer, 0, u.length >> 2); }
function bsearch(a, v) { let lo = 0, hi = a.length; while (lo < hi) { const m = (lo + hi) >> 1; if (a[m] < v) lo = m + 1; else hi = m; } return lo; }
function fmtE(e) { if (e == null) return '–'; const p = Math.floor(Math.log10(e)); return (e / 10 ** p).toFixed(1) + 'e' + p; }

function prepare(i) {
  const S = SCENES[i];
  if (!S._ready) {
    S.streams.forEach(s => {
      s._t = u32(s.t); s._xyp = u32(s.xyp);
      const mb = dec(s.masked); s._mask = new Uint8Array(S.w * S.h);
      for (let k = 0; k < S.w * S.h; k++) s._mask[k] = (mb[k >> 3] >> (7 - (k & 7))) & 1;
      // event-rate series (50 ms bins)
      const nb = Math.ceil(S.duration / 0.05); const r = new Float32Array(nb);
      for (let k = 0; k < s._t.length; k++) { const b = Math.min(nb - 1, Math.floor(s._t[k] / 5e4)); r[b]++; }
      s._rate = r;
      s._found = {}; s.dets.forEach(d => { if (d.label === 'flash' && !(d.m in s._found)) s._found[d.m] = d; });
    });
    S._kf = S.kf.map(u => { const im = new Image(); im.src = u; return im; });
    S._kfdata = new Array(S.kf.length).fill(null);
    S._ready = true;
  }
  return S;
}

function kfData(S, k) {
  if (S._kfdata[k]) return S._kfdata[k];
  const im = S._kf[k]; if (!im.complete || !im.naturalWidth) return null;
  const c = document.createElement('canvas'); c.width = S.w; c.height = S.h;
  const x = c.getContext('2d'); x.drawImage(im, 0, 0);
  S._kfdata[k] = x.getImageData(0, 0, S.w, S.h).data; return S._kfdata[k];
}

function buildDisplays() {
  const S = cur; const box = $('displays'); box.innerHTML = '';
  box.className = 'displays' + (S.streams.length > 1 ? ' three' : '');
  const mk = (cap, right) => {
    const d = document.createElement('div'); d.className = 'disp';
    d.innerHTML = `<div class="cap"><span>${cap}</span><span>${right || ''}</span></div><div class="stage" style="--ar:${S.w}/${S.h}"><canvas class="px"></canvas><canvas></canvas></div>`;
    box.appendChild(d); const cs = d.querySelectorAll('canvas'); cs[0].width = S.w; cs[0].height = S.h;
    return { base: cs[0], ov: cs[1], cap: d.querySelector('.cap span:last-child') };
  };
  S._in = mk('input · photo-electron rate (log)', `10^${S.lo.toFixed(2)}–10^${S.hi.toFixed(2)} e⁻/s`);
  S._ev = S.streams.map(s => mk('events · ' + s.name, ''));
}

function drawInput(t) {
  const S = cur, cv = S._in.base, ctx = cv.getContext('2d');
  let k = 0; while (k < S.kf_t.length - 1 && S.kf_t[k + 1] <= t) k++;
  const dtk = t - S.kf_t[k];
  const im = S._kf[k];
  ctx.fillStyle = '#000'; ctx.fillRect(0, 0, S.w, S.h);
  if (im.complete) { ctx.imageSmoothingEnabled = true; ctx.drawImage(im, S.drift[0] * dtk, S.drift[1] * dtk); }
  // flash light: amber tint of the log excess, white at saturation
  const data = kfData(S, k); if (!data) return;
  const span = S.hi - S.lo; const sg = S.psf;
  S.flashes.forEach(f => {
    const tt = t - f.t; if (tt <= 0 || tt > 4) return;
    const r = 1 - Math.exp(-tt / 2e-3);
    let pr = f.kind === 'exp' ? r * Math.exp(-tt / f.tau) : f.kind === 'double' ? r * (0.3 / (f.tau / 10) * Math.exp(-tt / (f.tau / 10)) + 0.7 / f.tau * Math.exp(-tt / f.tau)) : r * Math.pow(1 + tt / f.tau, -2.5);
    const cx = f.x + f.vx * tt, cy = f.y + f.vy * tt;
    const x0 = Math.max(0, Math.floor(cx) - 3), x1 = Math.min(S.w - 1, Math.floor(cx) + 3), y0 = Math.max(0, Math.floor(cy) - 3), y1 = Math.min(S.h - 1, Math.floor(cy) + 3);
    const img = ctx.getImageData(x0, y0, x1 - x0 + 1, y1 - y0 + 1);
    for (let y = y0; y <= y1; y++) for (let x = x0; x <= x1; x++) {
      const g = Math.exp(-((x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2) / (2 * sg * sg)) / (2 * Math.PI * sg * sg);
      const F = f.el * pr * g; const v = data[(y * S.w + x) * 4];
      const lb = S.lo + v / 255 * span; const B = 10 ** lb; const lt = Math.log10(B + F);
      const ex = Math.min(1, Math.max(0, (lt - lb) / 1.2)), sat = Math.min(1, Math.max(0, (lt - S.hi) / 1.5));
      const o = ((y - y0) * (x1 - x0 + 1) + (x - x0)) * 4;
      for (let c = 0; c < 3; c++) { let val = img.data[o + c] * (1 - ex) + [255, 190, 80][c] * ex; val = val * (1 - sat) + 255 * sat; img.data[o + c] = val; }
    }
    ctx.putImageData(img, x0, y0);
  });
  S.hits.forEach(h => { if (t - h.t >= 0 && t - h.t < 0.03) { ctx.fillStyle = '#bfefff'; h.px.forEach(p => ctx.fillRect(p[0], p[1], 1, 1)); } });
}

function drawEvents(t) {
  const S = cur; const n = S.w * S.h;
  S.streams.forEach((s, i) => {
    const cv = S._ev[i].base, ctx = cv.getContext('2d');
    const img = ctx.createImageData(S.w, S.h), d = img.data;
    const on = new Uint8Array(n), off = new Uint8Array(n);
    const t1 = t * 1e6, t0 = (t - st.win) * 1e6;
    const a = bsearch(s._t, t0), b = bsearch(s._t, t1);
    for (let k = a; k < b; k++) { const v = s._xyp[k]; const p = (v & 2047) + ((v >> 11) & 2047) * S.w; if (v >> 22) { if (on[p] < 255) on[p]++; } else if (off[p] < 255) off[p]++; }
    for (let p = 0; p < n; p++) {
      const ao = Math.pow(Math.min(1, on[p] / 2), 0.6), af = Math.pow(Math.min(1, off[p] / 2), 0.6) * (1 - ao);
      const m = Math.max(ao, af); let r = 18 * (1 - m) + 255 * ao + 70 * af, g = 20 * (1 - m) + 176 * ao + 150 * af, bl = 26 * (1 - m) + 46 * ao + 255 * af;
      if (st.ov.ma && s._mask[p]) { r = r * 0.4 + 150 * 0.6; g = g * 0.4 + 60 * 0.6; bl = bl * 0.4 + 60 * 0.6; }
      d[p * 4] = r; d[p * 4 + 1] = g; d[p * 4 + 2] = bl; d[p * 4 + 3] = 255;
    }
    ctx.putImageData(img, 0, 0);
    const rate = (b - a) / st.win;
    S._ev[i].cap.textContent = (rate / 1e3).toFixed(1) + ' kev/s' + (s.t_max && t > s.t_max ? ' · stream truncated' : '');
  });
}

function drawOverlay(cv, t, s) {
  const S = cur; const dpr = window.devicePixelRatio || 1; const W = cv.clientWidth, H = cv.clientHeight;
  if (cv.width !== Math.round(W * dpr)) { cv.width = Math.round(W * dpr); cv.height = Math.round(H * dpr); }
  const ctx = cv.getContext('2d'); ctx.setTransform(dpr, 0, 0, dpr, 0, 0); ctx.clearRect(0, 0, W, H);
  const k = W / S.w; ctx.lineWidth = 1.6; ctx.font = '11px "IBM Plex Mono", monospace';
  if (st.ov.fl) S.flashes.forEach((f, i) => {
    const tt = t - f.t; if (tt < -0.2 || tt > 3 * f.tau + 0.6) return;
    const q = Math.max(tt, 0), cx = (f.x + f.vx * q) * k, cy = (f.y + f.vy * q) * k, r = Math.max(7, 4.5 * k);
    const det = s && s._found[i] && t >= s._found[i].t;
    ctx.strokeStyle = det ? '#5ae67a' : '#e8e8e8'; ctx.setLineDash(det ? [] : [3, 3]);
    ctx.beginPath(); ctx.arc(cx, cy, r, 0, 2 * Math.PI); ctx.stroke(); ctx.setLineDash([]);
    if (k >= 2) { ctx.fillStyle = ctx.strokeStyle; ctx.fillText(`${fmtE(f.E)} J ${Math.round(f.tau * 1e3)} ms`, cx + r + 3, cy - r); }
  });
  if (st.ov.pa) S.hits.forEach(h => {
    if (t - h.t < 0 || t - h.t > 0.3) return; const p = h.px[0]; const cx = (p[0] + 0.5) * k, cy = (p[1] + 0.5) * k, r = Math.max(4, 3 * k);
    ctx.strokeStyle = '#50e6ff'; ctx.beginPath(); ctx.moveTo(cx - r, cy - r); ctx.lineTo(cx + r, cy + r); ctx.moveTo(cx - r, cy + r); ctx.lineTo(cx + r, cy - r); ctx.stroke();
  });
  if (st.ov.tr && s) s.dets.forEach(d => {
    if (t - d.t < 0 || t - d.t > 1) return; const pad = Math.max(3, 3 * k);
    const col = d.label === 'flash' ? '#f050f0' : d.label === 'particle' ? '#50e6ff' : '#ff3c3c';
    ctx.strokeStyle = col; ctx.strokeRect(d.ax * k - pad, d.ay * k - pad, d.s * k + 2 * pad, d.s * k + 2 * pad);
    ctx.fillStyle = col; ctx.fillText((d.label === 'flash' ? 'trigger' : d.label === 'particle' ? 'particle trigger' : 'false trigger') + (d.E ? ` E≈${fmtE(d.E)} J` : '') + ` W=${d.W}s`, (d.ax + d.s) * k + pad + 2, (d.ay + d.s) * k + pad);
  });
}

function drawSpark(t) {
  const S = cur, cv = $('spark'), dpr = window.devicePixelRatio || 1, W = cv.clientWidth, H = cv.clientHeight;
  if (cv.width !== Math.round(W * dpr)) { cv.width = Math.round(W * dpr); cv.height = Math.round(H * dpr); }
  const ctx = cv.getContext('2d'); ctx.setTransform(dpr, 0, 0, dpr, 0, 0); ctx.clearRect(0, 0, W, H);
  const css = getComputedStyle(document.documentElement);
  const cols = [css.getPropertyValue('--accent'), css.getPropertyValue('--off')];
  let mx = 1; S.streams.forEach(s => s._rate.forEach(v => { if (v > mx) mx = v; }));
  const lm = Math.log10(mx + 1);
  S.streams.forEach((s, i) => {
    ctx.strokeStyle = cols[i % 2]; ctx.lineWidth = 1.2; ctx.beginPath();
    s._rate.forEach((v, j) => { const x = j / s._rate.length * W, y = H - 4 - Math.log10(v + 1) / lm * (H - 10); j ? ctx.lineTo(x, y) : ctx.moveTo(x, y); }); ctx.stroke();
  });
  ctx.fillStyle = css.getPropertyValue('--muted'); ctx.font = '10px "IBM Plex Mono", monospace';
  ctx.fillText(`events per 50 ms (log), peak ${Math.round(mx)}`, 4, 11);
  S.flashes.forEach(f => { ctx.fillStyle = '#e8e8e8'; ctx.fillRect(f.t / S.duration * W, H - 4, 1.5, 4); });
  const x = t / S.duration * W; ctx.strokeStyle = css.getPropertyValue('--ink'); ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke();
}

function render() {
  const S = cur, t = st.t;
  drawInput(t); drawEvents(t);
  drawOverlay(S._in.ov, t, S.streams[0]);
  S.streams.forEach((s, i) => drawOverlay(S._ev[i].ov, t, s));
  drawSpark(t);
  $('tlabel').textContent = t.toFixed(3) + ' s / ' + S.duration.toFixed(0) + ' s';
  $('scrub').value = Math.round(t / S.duration * 1000);
}

function tables() {
  const S = cur, s0 = S.streams[0];
  const kv = [['Scene', S.label], ['Crop', `${S.w} × ${S.h} px at sensor (${S.crop[0]}, ${S.crop[1]}), head ${S.head ? S.head.join(',') : '–'}`],
    ['Ground pixel', S.ground.dx_km ? `${S.ground.dx_km.toFixed(2)} × ${S.ground.dy_km.toFixed(2)} km, range ${Math.round(S.ground.range_km)} km` : '–'],
    ['Drift', `${S.drift[0].toFixed(3)}, ${S.drift[1].toFixed(3)} px/s`], ['Earth phase', S.earth_phase != null ? S.earth_phase.toFixed(0) + '°' : '–']];
  S.streams.forEach(s => {
    const x = s.stats;
    kv.push(['Sensor', s.name]);
    kv.push(['  flashes detected', `${x.n_detected} / ${x.n_flashes}`]);
    kv.push(['  false triggers', `${x.n_false}`]);
    kv.push(['  particle hits / triggers', `${x.n_hits} (${x.n_heavy} heavy) / ${x.n_part_trig}`]);
    kv.push(['  event rate', `${(x.ev_rate / 1e3).toFixed(1)} kev/s (${(x.ev_rate / (S.w * S.h)).toFixed(3)} per px per s)`]);
    kv.push(['  hot / masked pixels', `${x.hot} / ${x.masked}`]);
    if (s.t_max) kv.push(['  embedded stream', `first ${s.t_max.toFixed(1)} s (page size limit)`]);
  });
  $('kv').innerHTML = kv.map(([a, b]) => `<dt>${a}</dt><dd>${b}</dd>`).join('');
  const hdr = '<tr><th>t_on [s]</th><th>E_L [J]</th><th>τ [ms]</th><th>range [km]</th>' + S.streams.map(s => `<th>${s.name}</th><th>lag [ms]</th><th>E est [J]</th>`).join('') + '<th></th></tr>';
  const rows = S.flashes.map((f, i) => '<tr>' + `<td>${f.t.toFixed(3)}</td><td>${fmtE(f.E)}</td><td>${Math.round(f.tau * 1e3)}</td><td>${Math.round(f.d)}</td>` +
    S.streams.map(s => { const r = s.per_flash[i]; const e = r.detected ? (r.ln_err_corr != null ? Math.exp(r.ln_err_corr) * f.E : r.e_raw_J) : null;
      return `<td><span class="pill ${r.detected ? 'ok' : 'bad'}">${r.detected ? 'detected' : 'missed'}</span></td><td>${r.detected ? Math.round(r.lag_s * 1e3) : '–'}</td><td>${fmtE(e)}</td>`; }).join('') +
    `<td><button type="button" data-t="${f.t}">Go to</button></td></tr>`).join('');
  $('ftab').innerHTML = hdr + rows;
  $('ftab').querySelectorAll('button').forEach(b => b.onclick = () => { st.t = Math.max(0, +b.dataset.t - 0.15); st.playing = true; st.speed = 0.25; $('speed').value = '0.25'; $('play').textContent = 'Pause'; });
}

function select(i) {
  st.scene = i; cur = prepare(i); st.t = Math.min(st.t, cur.duration);
  [...$('tabs').children].forEach((b, j) => b.setAttribute('aria-pressed', j === i ? 'true' : 'false'));
  $('desc').textContent = cur.desc;
  buildDisplays(); tables();
  let tries = 0; const go = () => { if (cur._kf.every(im => im.complete) || tries++ > 40) render(); else setTimeout(go, 50); }; go();
}

function loop(ts) {
  if (st.playing) {
    if (st.last != null) { st.t += (ts - st.last) / 1000 * st.speed; if (st.t >= cur.duration) { st.t = cur.duration; st.playing = false; $('play').textContent = 'Play'; } }
    st.last = ts; render();
  } else st.last = null;
  requestAnimationFrame(loop);
}

SCENES.forEach((S, i) => { const b = document.createElement('button'); b.type = 'button'; b.textContent = S.title; b.onclick = () => select(i); $('tabs').appendChild(b); });
$('play').onclick = () => { st.playing = !st.playing; if (st.playing && st.t >= cur.duration) st.t = 0; $('play').textContent = st.playing ? 'Pause' : 'Play'; };
$('scrub').oninput = e => { st.t = e.target.value / 1000 * cur.duration; render(); };
$('speed').onchange = e => { st.speed = +e.target.value; };
const winOf = v => Math.round(Math.pow(10, v / 100 * 2.3)) / 1000;  // 1 ms ... 200 ms
$('win').oninput = e => { st.win = winOf(+e.target.value); $('winlabel').textContent = Math.round(st.win * 1000) + ' ms'; render(); };
[['o_fl', 'fl'], ['o_tr', 'tr'], ['o_pa', 'pa'], ['o_ma', 'ma']].forEach(([id, k]) => $(id).onchange = e => { st.ov[k] = e.target.checked; render(); });
window.addEventListener('resize', () => render());
st.win = winOf(66); $('winlabel').textContent = Math.round(st.win * 1000) + ' ms';
const first = SCENES[0].flashes.length ? Math.max(0, SCENES[0].flashes[0].t - 0.2) : 0;
select(0); st.t = first; render();
requestAnimationFrame(loop);
</script>
"""

if __name__ == '__main__':
    build()
