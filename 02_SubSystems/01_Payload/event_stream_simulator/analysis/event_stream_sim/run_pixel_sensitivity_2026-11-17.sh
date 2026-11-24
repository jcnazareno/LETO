#!/usr/bin/env bash
# Pixel-parameter sensitivity (17 Nov 2026): refractory period 79 us (EVK4 camera-reported at default biases) and
# 200 us, and contrast threshold C = 0.15, 0.20, 0.30, 0.35 (baseline 0.25, both polarities) with the trigger table
# re-tuned to the changed C. For each variant: its own energy calibration (calibrate --tag) and four scenes (near side,
# far side, terminator, GCR solar min x100 particles). Scene runs use the default correction; pixel_sensitivity.py
# re-applies each variant's correction from the recorded energy features. Outputs go to
# data/pixel_sensitivity/, logs to data/logs/pixel_sensitivity/.
#   ./run_pixel_sensitivity_2026-11-17.sh     then   python pixel_sensitivity.py
cd "$(dirname "$0")"
D=../../data; O=$D/pixel_sensitivity; L=$D/logs/pixel_sensitivity; mkdir -p $O $L
export NUMBA_NUM_THREADS=${NUMBA_NUM_THREADS:-2}
PAR=${PAR:-9}
submit() { while (( $(jobs -rp | wc -l) >= PAR )); do wait -n; done; ( eval "$1" ) & }
declare -A SETS
SETS[refr79us]="--set sensor.events.refractory_s=7.9e-5"
SETS[refr200us]="--set sensor.events.refractory_s=2e-4"
for c in 0.15 0.20 0.30 0.35; do
  SETS[C${c/./p}]="--set sensor.threshold.C_on=$c --set sensor.threshold.C_off=$c --threshold-model retuned"
done
# calibrations first (longest jobs)
for v in "${!SETS[@]}"; do
  submit "python3 run_sim.py calibrate --sensor imx636 ${SETS[$v]} --tag imx636_$v > $L/calibrate_$v.log 2>&1 && mv $D/energy_calibration_imx636_$v.json $O/"
done
for v in "${!SETS[@]}"; do
  for sc in nearside farside terminator particles; do
    extra=""; [[ $sc == particles ]] && extra="--particles gcr_min_x100 --flashes 4" || extra="--flashes 8"
    tag=${sc}_imx636_$v
    submit "python3 run_sim.py run --scene $sc --duration 20 $extra ${SETS[$v]} --tag $tag --no-h5 > $L/run_$tag.log 2>&1 && mv $D/${tag}_truth.json $D/${tag}_events.npz $D/${tag}_keyframes.npz $O/"
  done
done
wait
python3 pixel_sensitivity.py > $L/pixel_sensitivity.log 2>&1
echo PIXEL_SENSITIVITY_DONE
