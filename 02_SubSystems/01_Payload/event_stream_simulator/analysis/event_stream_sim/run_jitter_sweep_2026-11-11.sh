#!/usr/bin/env bash
# Pointing-jitter sensitivity (handoff 2026-11-11, item 3.5). Only env.attitude.* overrides and --jitter-seed.
#   ./run_jitter_sweep_2026-11-11.sh [base|ext|all]     (default all), then jitter_sweep.py (data + figures)
# base: terminator and near side, 320 x 180 crop, 20 s, 8 flashes, default seeds, jitter 0.2-60 arcsec rms
#       (tau_c 0.5 s) plus tau_c 0.1 s and 2 s at 10 arcsec (16 runs).
# ext:  terminator onset refinement (11 Nov 2026): 12, 14, 17 arcsec with jitter seed 11, and jitter seeds 12-15 at
#       5, 10, 14, 20 arcsec (19 runs). The flash and pixel seed stays fixed, so seeds isolate the jitter path.
# 1 px = 62.7 arcsec. Runs go PAR at a time (NUMBA_NUM_THREADS each; results do not depend on the thread count).
# Tags: <scene>_imx636_jitter<rms>[_tc<corr>][_js<seed>]. run_sim.py writes to data/; each run's
# files are then moved to data/jitter/, logs go to data/logs/jitter/.
set -e
cd "$(dirname "$0")"
D=../../data; J=$D/jitter; L=$D/logs/jitter; mkdir -p $J $L
export NUMBA_NUM_THREADS=${NUMBA_NUM_THREADS:-4}
PAR=${PAR:-4}
stage=${1:-all}
jobs_list=()   # "scene rms tau_c jitter_seed"
if [[ $stage == base || $stage == all ]]; then
  for scene in terminator nearside; do
    for j in 0.2 2 5 10 20 60; do jobs_list+=("$scene $j 0.5 11"); done
    for tc in 0.1 2.0; do jobs_list+=("$scene 10 $tc 11"); done
  done
fi
if [[ $stage == ext || $stage == all ]]; then
  for j in 12 14 17; do jobs_list+=("terminator $j 0.5 11"); done
  for js in 12 13 14 15; do
    for j in 5 10 14 20; do jobs_list+=("terminator $j 0.5 $js"); done
  done
fi
run_one() {
  local scene=$1 j=$2 tc=$3 js=$4
  local tag=${scene}_imx636_jitter${j/./p}
  [[ $tc != 0.5 ]] && tag=${tag}_tc${tc/./p}
  [[ $js != 11 ]] && tag=${tag}_js${js}
  python3 run_sim.py run --scene $scene --duration 20 --flashes 8 --jitter-seed $js \
    --set env.attitude.jitter_rms_arcsec=$j --set env.attitude.jitter_corr_s=$tc \
    --tag $tag --no-h5 > $L/run_jitter_${tag}.log 2>&1
  mv $D/${tag}_truth.json $D/${tag}_events.npz $D/${tag}_keyframes.npz $J/
  echo "done $tag"
}
for item in "${jobs_list[@]}"; do
  while (( $(jobs -rp | wc -l) >= PAR )); do wait -n; done
  run_one $item &
done
wait
python3 jitter_sweep.py > $L/jitter_sweep.log 2>&1
echo JITTER_SWEEP_DONE
