#!/usr/bin/env bash
# Regenerates every stored result of the event-stream model with the code of 11 Nov 2026 (exact charge impulses,
# McEwen lunar-Lambert L, stars, entering particle tracks, match() fix), on a job pool instead of three serial parts.
#   ./run_regenerate_parallel_2026-11-11.sh            (PAR jobs at a time, NUMBA_NUM_THREADS threads each)
# Same scene/stress/validation commands as run_regenerate_2026-11-11.sh, plus V2 (background activity), the full
# jitter sweep (run_jitter_sweep_2026-11-11.sh: base + ext) and the star runs (limb without stars, limb with test
# stars of V = 1..5). Order: the two calibrations and the calibration-independent validations start together; scene
# runs, stress runs and the remaining validations start when both calibrations exist; long jobs first.
# Logs: data/logs/ (jitter: logs/jitter/, stars: logs/stars/).
cd "$(dirname "$0")"
D=../../data; L=$D/logs; mkdir -p $L $L/jitter $L/stars $D/jitter $D/stars
export NUMBA_NUM_THREADS=${NUMBA_NUM_THREADS:-3}
PAR=${PAR:-7}
R="python3 run_sim.py run"
submit() { while (( $(jobs -rp | wc -l) >= PAR )); do wait -n; done; ( eval "$1" ) & }
rm -f $L/.calib_done_imx636 $L/.calib_done_imx646
# --- stage 1: calibrations and validations that do not use the stored correction ---
submit "python3 run_sim.py calibrate --sensor imx636 > $L/calibrate_imx636.log 2>&1 && touch $L/.calib_done_imx636"
submit "python3 run_sim.py calibrate --sensor imx646 > $L/calibrate_imx646.log 2>&1 && touch $L/.calib_done_imx646"
for v in texture refractory realistic particle_timestep texture_prehistory s10 ba shadow; do
  submit "python3 validate.py $v > $L/validate_$v.log 2>&1"
done
while [[ ! -f $L/.calib_done_imx636 || ! -f $L/.calib_done_imx646 ]]; do
  if (( $(jobs -rp | wc -l) == 0 )); then echo "CALIBRATION FAILED"; exit 1; fi
  sleep 10
done
echo CALIBRATIONS_DONE
# --- stage 2: everything that uses the correction, longest first ---
J=()
J+=("$R --scene nearside --full-frame --duration 6 --flashes 6 --tag nearside_imx636_full --video > $L/run_fullframe.log 2>&1")
J+=("python3 validate.py hpf_retrained > $L/validate_hpf_retrained.log 2>&1")
J+=("$R --scene terminator --duration 20 --flashes 8 --video > $L/run_terminator.log 2>&1")
J+=("python3 run_sim.py compare --scene nearside --sensors imx636,imx646 --duration 20 --flashes 8 --flash-spec '2e4:0.3,4e4:1.0,1e4:0.03,2e4:0.1,4e4:0.3,2e4:1.0,1e5:1.0,1e4:0.1' > $L/run_compare.log 2>&1")
J+=("$R --scene terminator_far --duration 20 --flashes 8 --video > $L/run_terminator_far.log 2>&1")
J+=("$R --scene terminator --duration 20 --flashes 8 --lit-limit 1e12 --tag terminator_imx636_nolitmask --no-h5 > $L/run_terminator_nolitmask.log 2>&1")
J+=("$R --scene limb --duration 20 --flashes 6 --set env.straylight.mode=ghost --video > $L/run_limb.log 2>&1")
J+=("$R --scene terminator --duration 20 --flashes 8 --map-shift=3,0 --tag terminator_imx636_mapshift_p3 --no-h5 > $L/run_terminator_mapshift_p3.log 2>&1")
J+=("$R --scene nearside --duration 20 --flashes 8 --video > $L/run_nearside.log 2>&1")
J+=("$R --scene terminator_far --duration 20 --flashes 8 --lit-limit 1e12 --tag terminator_far_imx636_nolitmask --no-h5 > $L/run_terminator_far_nolitmask.log 2>&1")
J+=("$R --scene terminator --duration 20 --flashes 8 --map-shift=-3,0 --tag terminator_imx636_mapshift_m3 --no-h5 > $L/run_terminator_mapshift_m3.log 2>&1")
J+=("python3 validate.py substep > $L/validate_substep.log 2>&1")
J+=("$R --scene particles --duration 20 --flashes 4 --particles gcr_min_x100 --tag particles_gcrmin_x100_imx636 --video > $L/run_particles_gcrmin_x100.log 2>&1")
J+=("$R --scene farside --duration 20 --flashes 8 --video > $L/run_farside.log 2>&1")
J+=("$R --scene particles --duration 20 --flashes 4 --particles sep100 --video > $L/run_particles.log 2>&1")
J+=("$R --scene nearside --duration 20 --flashes 8 --map-scale-err 0.2 --tag nearside_imx636_bgerr_p20 --no-h5 > $L/run_nearside_bgerr_p20.log 2>&1")
J+=("$R --scene nearside --duration 20 --flashes 8 --set sensor.ba.rate_hz=0.3 --threshold-model retuned --tag nearside_imx636_ba03_retuned --no-h5 > $L/run_nearside_ba03_retuned.log 2>&1")
J+=("$R --scene nearside --duration 20 --flashes 8 --set sensor.ba.rate_hz=0.3 --threshold-model fixed --tag nearside_imx636_ba03_fixed --no-h5 > $L/run_nearside_ba03_fixed.log 2>&1")
J+=("$R --scene nearside --duration 20 --flashes 8 --map-scale-err -0.2 --tag nearside_imx636_bgerr_m20 --no-h5 > $L/run_nearside_bgerr_m20.log 2>&1")
J+=("$R --scene nearside --duration 20 --flashes 8 --group-bg geomean --tag nearside_imx636_geomean --no-h5 > $L/run_nearside_geomean.log 2>&1")
J+=("$R --scene particles --duration 20 --flashes 4 --particles gcr_min_x100 --set sensor.mask.fraction=0.0 --set sensor.hot.fraction=0.02 --tag particles_gcrmin_x100_imx636_nomask --no-h5 > $L/run_particles_gcrmin_x100_nomask.log 2>&1")
J+=("$R --scene particles --duration 20 --flashes 4 --particles sep100 --set sensor.mask.fraction=0.0 --set sensor.hot.fraction=0.02 --tag particles_imx636_nomask --no-h5 > $L/run_particles_nomask.log 2>&1")
J+=("$R --scene particles --duration 20 --flashes 4 --particles gcr_min_x100 --set sensor.mask.fraction=0.0 --tag particles_gcrmin_x100_imx636_nomask_measuredhot --no-h5 > $L/run_particles_gcrmin_x100_nomask_measuredhot.log 2>&1")
J+=("python3 validate.py sensitivity > $L/validate_sensitivity.log 2>&1")
J+=("$R --scene particles --duration 20 --flashes 4 --particles gcr_max_x100 --tag particles_gcrmax_x100_imx636 --no-h5 > $L/run_particles_gcrmax_x100.log 2>&1")
J+=("$R --scene particles --duration 20 --flashes 4 --particles gcr_min_x100 --particle-diffusion-px 0.5 --particle-collection-tau 1e-3 --tag particles_gcrmin_x100_imx636_diff05_coll1ms --no-h5 > $L/run_particles_diff05_coll1ms.log 2>&1")
J+=("$R --scene particles --duration 20 --flashes 4 --particles gcr_min_x100 --particle-collection-tau 5e-3 --tag particles_gcrmin_x100_imx636_coll5ms --no-h5 > $L/run_particles_coll5ms.log 2>&1")
J+=("$R --scene particles --duration 20 --flashes 4 --particles sep1000 --tag particles_sep1000_imx636 --no-h5 > $L/run_particles_sep1000.log 2>&1")
J+=("$R --scene particles --duration 20 --flashes 4 --particles gcr_min_x100 --particle-diffusion-px 0.5 --tag particles_gcrmin_x100_imx636_diff05 --no-h5 > $L/run_particles_diff05.log 2>&1")
J+=("python3 validate.py field_gain > $L/validate_field_gain.log 2>&1")
# stars: limb without stars, and with one test star of each magnitude (files moved to data/stars/)
st() { local tag=$1; shift; echo "$R --scene limb --duration 20 --flashes 6 --set env.straylight.mode=ghost $* --tag $tag --no-h5 > $L/stars/run_$tag.log 2>&1 && mv $D/${tag}_truth.json $D/${tag}_events.npz $D/${tag}_keyframes.npz $D/stars/"; }
J+=("$(st limb_imx636_nostars --set env.stars.enabled=false)")
for m in 1 2 3 4 5; do J+=("$(st limb_imx636_teststar_V$m --set "'env.stars.test_mags=[$m]'")"); done
for m in 1 2 3 4 5; do J+=("$(st limb_imx636_teststar_limb_V$m --set "'env.stars.test_mags=[$m]'" --set env.stars.test_place='"limb"')"); done
# jitter sweep (base + ext), files moved to data/jitter/
jt() { local scene=$1 j=$2 tc=$3 js=$4; local tag=${scene}_imx636_jitter${j/./p}
  [[ $tc != 0.5 ]] && tag=${tag}_tc${tc/./p}; [[ $js != 11 ]] && tag=${tag}_js${js}
  echo "$R --scene $scene --duration 20 --flashes 8 --jitter-seed $js --set env.attitude.jitter_rms_arcsec=$j --set env.attitude.jitter_corr_s=$tc --tag $tag --no-h5 > $L/jitter/run_jitter_$tag.log 2>&1 && mv $D/${tag}_truth.json $D/${tag}_events.npz $D/${tag}_keyframes.npz $D/jitter/"; }
for scene in terminator nearside; do
  for j in 0.2 2 5 10 20 60; do J+=("$(jt $scene $j 0.5 11)"); done
  for tc in 0.1 2.0; do J+=("$(jt $scene 10 $tc 11)"); done
done
for j in 12 14 17; do J+=("$(jt terminator $j 0.5 11)"); done
for js in 12 13 14 15; do for j in 5 10 14 20; do J+=("$(jt terminator $j 0.5 $js)"); done; done
for c in "${J[@]}"; do submit "$c"; done
wait
echo STAGE2_DONE
# --- stage 3: exports, page, summaries, sweep analyses ---
python3 run_sim.py export-v2e --tag nearside_imx636 > $L/export_v2e.log 2>&1
python3 build_page.py > $L/build_page.log 2>&1
python3 summarize.py  > $L/summarize.log 2>&1
python3 jitter_sweep.py > $L/jitter/jitter_sweep.log 2>&1
python3 star_survey.py > $L/stars/star_survey.log 2>&1
python3 star_runs.py > $L/stars/star_runs.log 2>&1
echo ALL_DONE
