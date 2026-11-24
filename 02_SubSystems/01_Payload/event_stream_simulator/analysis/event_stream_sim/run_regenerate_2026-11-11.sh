#!/usr/bin/env bash
# Regenerates every stored result of the event-stream model with the 10 Nov 2026 code (full rerun, 11 Nov 2026).
# For the complete recorded suite, use run_regenerate_parallel_2026-11-11.sh.
#   ./run_regenerate_2026-11-11.sh A   calibrations and the scene runs (about 80 min on 2 cores)
#   ./run_regenerate_2026-11-11.sh B   stress runs: map errors, threshold models, particle deposits (about 30 min)
#   ./run_regenerate_2026-11-11.sh C   validations V1-V10, v2e export, page, summary (about 60 min)
# V2 (validate.py ba) uses no trigger and is not rerun here; run it separately if the pixel kernel changes.
set -e
cd "$(dirname "$0")"
L=../../data/logs; mkdir -p $L
part=${1:-ABC}
R="python3 run_sim.py run"
if [[ $part == *A* ]]; then
python3 run_sim.py calibrate --sensor imx636 > $L/calibrate_imx636.log 2>&1
python3 run_sim.py calibrate --sensor imx646 > $L/calibrate_imx646.log 2>&1
$R --scene nearside   --duration 20 --flashes 8 --video > $L/run_nearside.log 2>&1
$R --scene farside    --duration 20 --flashes 8 --video > $L/run_farside.log 2>&1
$R --scene particles  --duration 20 --flashes 4 --particles sep100 --video > $L/run_particles.log 2>&1
# no-mask runs keep the former 2% hot population explicitly (tuned-bias level, Hahmeyer 2025 Fig. 3.2c-f)
$R --scene particles  --duration 20 --flashes 4 --particles sep100 --set sensor.mask.fraction=0.0 --set sensor.hot.fraction=0.02 --tag particles_imx636_nomask --no-h5 > $L/run_particles_nomask.log 2>&1
$R --scene terminator --duration 20 --flashes 8 --video > $L/run_terminator.log 2>&1
$R --scene terminator --duration 20 --flashes 8 --lit-limit 1e12 --tag terminator_imx636_nolitmask --no-h5 > $L/run_terminator_nolitmask.log 2>&1
$R --scene terminator_far --duration 20 --flashes 8 --video > $L/run_terminator_far.log 2>&1
$R --scene terminator_far --duration 20 --flashes 8 --lit-limit 1e12 --tag terminator_far_imx636_nolitmask --no-h5 > $L/run_terminator_far_nolitmask.log 2>&1
$R --scene limb       --duration 20 --flashes 6 --set env.straylight.mode=ghost --video > $L/run_limb.log 2>&1
python3 run_sim.py compare --scene nearside --sensors imx636,imx646 --duration 20 --flashes 8 \
   --flash-spec "2e4:0.3,4e4:1.0,1e4:0.03,2e4:0.1,4e4:0.3,2e4:1.0,1e5:1.0,1e4:0.1" > $L/run_compare.log 2>&1
# full frame: 6 s, so that every 4 s energy record lies inside the stream
$R --scene nearside --full-frame --duration 6 --flashes 6 --tag nearside_imx636_full --video > $L/run_fullframe.log 2>&1
$R --scene particles --duration 20 --flashes 4 --particles gcr_min_x100 --tag particles_gcrmin_x100_imx636 --video > $L/run_particles_gcrmin_x100.log 2>&1
$R --scene particles --duration 20 --flashes 4 --particles gcr_min_x100 --set sensor.mask.fraction=0.0 --set sensor.hot.fraction=0.02 --tag particles_gcrmin_x100_imx636_nomask --no-h5 > $L/run_particles_gcrmin_x100_nomask.log 2>&1
$R --scene particles --duration 20 --flashes 4 --particles gcr_min_x100 --set sensor.mask.fraction=0.0 --tag particles_gcrmin_x100_imx636_nomask_measuredhot --no-h5 > $L/run_particles_gcrmin_x100_nomask_measuredhot.log 2>&1
$R --scene particles --duration 20 --flashes 4 --particles gcr_max_x100 --tag particles_gcrmax_x100_imx636 --no-h5 > $L/run_particles_gcrmax_x100.log 2>&1
echo PART_A_DONE
fi
if [[ $part == *B* ]]; then
# on-board background/mask map errors
$R --scene terminator --duration 20 --flashes 8 --map-shift=3,0 --tag terminator_imx636_mapshift_p3 --no-h5 > $L/run_terminator_mapshift_p3.log 2>&1
$R --scene terminator --duration 20 --flashes 8 --map-shift=-3,0 --tag terminator_imx636_mapshift_m3 --no-h5 > $L/run_terminator_mapshift_m3.log 2>&1
$R --scene nearside --duration 20 --flashes 8 --map-scale-err 0.2  --tag nearside_imx636_bgerr_p20 --no-h5 > $L/run_nearside_bgerr_p20.log 2>&1
$R --scene nearside --duration 20 --flashes 8 --map-scale-err -0.2 --tag nearside_imx636_bgerr_m20 --no-h5 > $L/run_nearside_bgerr_m20.log 2>&1
$R --scene nearside --duration 20 --flashes 8 --group-bg geomean --tag nearside_imx636_geomean --no-h5 > $L/run_nearside_geomean.log 2>&1
# an overridden detector with fixed versus re-tuned trigger thresholds
$R --scene nearside --duration 20 --flashes 8 --set sensor.ba.rate_hz=0.3 --threshold-model fixed   --tag nearside_imx636_ba03_fixed --no-h5 > $L/run_nearside_ba03_fixed.log 2>&1
$R --scene nearside --duration 20 --flashes 8 --set sensor.ba.rate_hz=0.3 --threshold-model retuned --tag nearside_imx636_ba03_retuned --no-h5 > $L/run_nearside_ba03_retuned.log 2>&1
# extended / delayed particle deposits and high load
$R --scene particles --duration 20 --flashes 4 --particles gcr_min_x100 --particle-diffusion-px 0.5 --tag particles_gcrmin_x100_imx636_diff05 --no-h5 > $L/run_particles_diff05.log 2>&1
$R --scene particles --duration 20 --flashes 4 --particles gcr_min_x100 --particle-diffusion-px 0.5 --particle-collection-tau 1e-3 --tag particles_gcrmin_x100_imx636_diff05_coll1ms --no-h5 > $L/run_particles_diff05_coll1ms.log 2>&1
$R --scene particles --duration 20 --flashes 4 --particles gcr_min_x100 --particle-collection-tau 5e-3 --tag particles_gcrmin_x100_imx636_coll5ms --no-h5 > $L/run_particles_coll5ms.log 2>&1
$R --scene particles --duration 20 --flashes 4 --particles sep1000 --tag particles_sep1000_imx636 --no-h5 > $L/run_particles_sep1000.log 2>&1
echo PART_B_DONE
fi
if [[ $part == *C* ]]; then
for v in s10 realistic texture texture_prehistory substep refractory sensitivity hpf_retrained field_gain shadow particle_timestep; do
  python3 validate.py $v > $L/validate_$v.log 2>&1
done
python3 run_sim.py export-v2e --tag nearside_imx636 > $L/export_v2e.log 2>&1
python3 build_page.py > $L/build_page.log 2>&1
python3 summarize.py  > $L/summarize.log 2>&1
echo PART_C_DONE
fi
