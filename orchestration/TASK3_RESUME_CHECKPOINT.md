# Task 3 execution checkpoint

Last checked November 11, 2026. Luna worker `01a1caad-6c46-7780-8526-e46ca2919328` previously returned: "You hit your spend cap set by the owner of your workspace. Ask an owner to increase your spend cap to continue." This is a tool-reported error, NOT verified account billing state; the user owns a personal account and reports no cap. No reset time is established. A fresh continuation was sent; the latest poll timed out without a terminal status, so re-poll the same worker before drawing conclusions or restarting. User requires execution to remain on Luna.

Current solution SHA256: `362315dcf77d778323d090dc40088382da29820a93f2a84e7591fad209020975`. Latest change reduces outside-zone bend slowdown coefficient from .15 to .05. Saved `runtime-finish-regression.out` reports 59 tests passed in .631 seconds; this change has no live validation yet. Prior source `7c822c747a5038ba0e4ebdf831ff26874bd04ad42e9a3095f9c0b24194cab7ae` removed irrelevant filtered-range braking delay while retaining frame delay: `runtime-braking-hard-1` parked at 179.40 s and `runtime-braking-hard-2` at 180.20 s. Consistent <=180 s remains unproven. Pure pursuit remains a temporary diagnostic candidate and was not applied: paired tests showed no timing improvement.

Continue `TASK3_RUNTIME_FINISH_WORK_ORDER.md`, not a fresh investigation. Relevant evidence is under `/private/tmp/task3-followup.ZNTHv6/`:

- `lane_bend_opportunity.txt`: fixed-trajectory estimate of 1.401 s saved by reducing outside-zone bend slowdown coefficient from .15 to .05; 2.155 s if also using exact global 3.0 cap. These are counterfactual estimates, not live results or safety certification.
- `runtime_opportunity.txt`: forward pose uses raw range but braking still adds smoothed-range lag; inspect and remove only the irrelevant delay while preserving actual frame/command delay, braking bounds and strict stop checks.
- `yaw-recovery-hard-merge-repeat-1/`: successful 184.20 s baseline, full source, camera-state and diagnostic truth.

Next execution after the workspace owner clears the spend cap: validate the existing bend-speed patch with actual full Hard harness runs; do not reapply the already implemented braking correction or repeat the old diagnosis. Use `/Users/aryanachary/.venv/bin/python`; all simulator API/harness commands require elevated localhost access. Invoke full `rehearse.py Hard UNIQUE_TAG` without `--controller`. A prior controller-only invocation produced no frames and is not a run. Restart an identified stalled simulator without saving if necessary (already authorized), preferably fresh process per trial. Keep workspace scene edits untouched; use clean committed scenes copied into temporary diagnostics.

Final validation still required: repeated Hard <=180 s, Medium twice, Easy once, strict parked pose/stillness, independent >=5 s Hospital stationary evidence, command limits and available collision/road evidence. Official encrypted recording/video remain for the friend's supported Windows/Ubuntu machine after code is finalized. No official score, submission ZIP, or readiness claim is supported yet. No push or portal submission authorized.

## Current Luna handoff — November 12, 2026

Owner remains Luna; Sol is orchestrating review via parent relay. Current source
SHA256 is `b3610f6753516a375832d24c8bedd411637d0c523be40f5336d7f15f3bf13a3f`.
It retains raw-range braking delay correction and outside-zone bend slowdown
0.05, plus a new parking guard: when heading is unobserved and bearing margin
is under 15 degrees, command zero until heading is observed. Offline Task 3
suite: 59 tests passed (`/private/tmp/task3-followup.ZNTHv6/runtime-marker-edge-regression.out`).
No live validation exists for this hash.

### Latest actual runs and process state

- `runtime-finish-bend-hard-1`, source `362315dcf77d778323d090dc40088382da29820a93f2a84e7591fad209020975`: full harness ended at 300.15 s with `finished=false`, `failed=false`, parking active, command zero, and `pose=null`; no parked log. It is a failed completion, not a timing pass. Final diagnostic truth was x=+0.22928 m, y=-0.78823 m, yaw=-1.57733 rad; the vehicle was stopped.
- Focused saved-frame review: at 167.20 s marker ID 1 PnP yaw/range were +0.455/0.6001 m and bbox x=213..248; at 167.80 +0.5425/0.5767 m and x=152..196; at 168.40 +0.7096/0.5522 m and x=85..141. At 168.40 the fused internal yaw was +0.3516 rad (`pose.heading=-0.3516`) and `heading_observed=false`; center bearing was +0.5894 rad. By 168.70 marker ID 1 was not detected and pose remained null. Diagnostic truth yaw from 167.20 to 168.70 stayed near -1.58 rad, while estimated lateral changed from +0.1228 to -0.1345 m over 1.20 s. This indicates a large image/PnP-versus-fused-pose inconsistency as the marker moved left and then disappeared; it is not evidence of comparable physical lateral travel. Truth was diagnostic only.
- The new edge-stop branch is intended to stop before another movement interval when yaw is unobserved near the image edge. Existing focused test checks zero speed at 14-degree center margin and positive speed when yaw is observed, but persistent ambiguity/recovery/resumption and no-false-success coverage still need explicit tests. Immediate marker-loss stop tests remain in the suite.
- `runtime-marker-edge-hard-1` did not load a scene: bounded `zmqRemoteApi.info` timed out. The tool-side shell PID 91679 is a stuck startup process; its output directory is empty. Older failed startup PID 90183 (`runtime-finish-bend-hard-2b`) is likewise not a run. CoppeliaSim PID 89683 and launcher PID 89702 are still listed, but remote API requests time out. No controller/simulator run is active. Do not interrupt/restart a live run; no live run is pending.

Next: complete focused ambiguity/recovery tests and record report/checkpoint updates. Do not start a new live run until Sol/parent coordinates takeover and simulator access. Keep all full-harness calls elevated and bounded; use full harness without top-level `--controller`. Hard 1 remains failed and b361 remains unvalidated. Existing 179.40 s and 180.20 s runs belong to prior source hash `7c822c...`, not current code. Final Hard/Medium/Easy acceptance and official external recording remain outstanding.

## Newest evidence update — November 12, 2026

The live run `runtime-marker-edge-hard-1b` on exact hash
`b3610f6753516a375832d24c8bedd411637d0c523be40f5336d7f15f3bf13a3f` completed
and parked at 181.25 s (finished true, failed false). Parking started 158.55 s;
final camera pose 0.208711 m / -0.001921 m / -4.785 deg, fresh heading observed.
Global/zone command maxima 2.95 / 1.20 rad/s. Independent truth confirms a
5.30 s stationary interval during Hospital hold (27.60–32.90 s, net under
0.00002 m). ArUco marker detected in 39/39 saved parking images, min edge margin
61 px, p10 87 px. This meets parking/hold/command checks but misses 180 s by
1.25 s. The high-uncertainty edge-stop condition did not trigger in this run.

Focused regression suite now passes 61 tests at
`/private/tmp/task3-followup.ZNTHv6/runtime-marker-edge-regression-final.out`.
New tests cover repeated unobserved near-edge poses staying stopped without
false success and three consistent clear-yaw observations recovering heading
and resuming parking. Existing marker-loss-immediate-stop test remains. A
frozen-image replay of the 168.40 s failure frame yielded raw PnP
(+0.709591 rad, 0.552150 m); repeated frozen pixels caused 2 stopped/unobserved
frames, fresh heading on frame 3, and resume at 1.18 rad/s. This replay is
not live proof of physical/estimator correctness.

Full-harness startup failures `runtime-marker-edge-hard-1` and
`runtime-finish-bend-hard-2b` stopped before scene load and had no controller
or camera/truth output; their startup processes were closed. A fresh simulator
restart then enabled `runtime-marker-edge-hard-1b`. That full run is finished;
no live controller remains. Collision/off-road contact sensors are not captured
by this harness; available video frames/truth path cannot certify no contact.

Next action: use the recorded 1.25 s overrun to justify one bounded runtime
adjustment, then validate with full harness. Existing 179.40/180.20 s results
belong to prior hash `7c822c...`, and 300.15 s failure belongs to hash
`362315dc...`. Do not conflate them with b361. Acceptance still requires at
least two Hard runs <=180 s, Medium twice, Easy once, plus supported official
Windows/Ubuntu recording by the team. No portal, push, or submission occurred.

## Luna handoff — November 12, 2026 (latest authoritative state)

- Current `task3/task3.py` SHA256:
  `fd2acd30c041ecf2a2a3bd50e7ba6b05a6e0644e1fefb6ad271d1d26d65e8d11`.
  It retains raw-range braking, outside-zone bend factor 0.05, global ceiling
  3.0, zone ceiling 1.2, strict parking/hold checks and zero-on-marker-loss.
  New edge prelimit: observed heading plus bearing margin under 15 degrees
  caps speed at 1.2; the unobserved-heading zero-stop threshold remains 15.
- 62 tests passed (`/private/tmp/task3-followup.ZNTHv6/runtime-edge-prelimit-tests.out`);
  syntax and scoped diff checks passed. No further controller edits followed.
- No live harness/controller is active. The attempted
  `runtime-edge-prelimit-hard-1` stopped at bounded `loadScene()` timeout before
  creating a controller. Parent confirms CoppeliaSim PID 99503 and launcher
  99512 remain open. A subsequent bounded API check returned stopped state and
  the clean Hard reset positions. The user interrupted the next command for
  handoff; it was not a run failure. Do not restart the simulator.
- Diagnostic-only harness:
  `/private/tmp/task3-followup.ZNTHv6/rehearse_groundheading.py`. It records
  root/camera matrices, `/ID_1` and `/ID_2` world transforms, per-frame raw PnP,
  steering positions and edge frames; diagnostic values never enter control.
  Its `--reuse-verified-hard-scene` option verifies stopped state, clean Hard
  reset positions and zero wheel targets before reusing the loaded scene.
- Pending next command, full harness and no top-level `--controller`:
  `/Users/aryanachary/.venv/bin/python /private/tmp/task3-followup.ZNTHv6/rehearse_groundheading.py Hard runtime-edge-prelimit-hard-2 --reuse-verified-hard-scene`
  Run with elevated localhost access and bounded API timeouts. This command has
  not been executed. If verification refuses reuse, inspect state before any
  scene load/restart.
- Matrix probe `runtime-groundheading-hard-2` on prior source `287b1fc...`
  parked at 185.50 s, not a timing pass. Straight displacement calibrates
  physical forward as root local +Z; camera local +Z aligns; ID_1 normal is
  +X. Actual vehicle turns, so old Euler-Z-based “straight vehicle” inference
  is invalid. Failed `runtime-terminal-approach-hard-2b` stopped at 300.75 s:
  ID 1 moves from image x=110–159 at 172.30 s to x=38–103 at 172.85 s and is
  absent at 173.25 s. Although commanded speed is zero, world XY changes about
  1.9 cm before 173.25 s, consistent with coasting. Reassess using the pending
  matrix/PnP run; do not claim the edge prelimit works until live evidence.
- The terminal 0.35 rad/s experiment was reverted. Hard <=180 repeats,
  Medium/Easy runs, collision/off-road evidence and official Windows/Ubuntu
  recording remain outstanding. No portal or push.

## Diagnostic attempt — November 12, 2026

Executed the pending command once against source
`fd2acd30c041ecf2a2a3bd50e7ba6b05a6e0644e1fefb6ad271d1d26d65e8d11`:
`/Users/aryanachary/.venv/bin/python /private/tmp/task3-followup.ZNTHv6/rehearse_groundheading.py Hard runtime-edge-prelimit-hard-2 --reuse-verified-hard-scene`.
The harness verified the clean Hard reset scene and recorded evidence under
`/private/tmp/task3-followup.ZNTHv6/runtime-edge-prelimit-hard-2/`, but the
controller exited with rc 1 at sim time 0 before processing any frames:
`Again: Resource temporarily unavailable`; stop calls also reported invalid
state. This is a failed startup, not a completed full run. The harness's
optional external `timeout` wrapper was unavailable (`command not found`); the
actual run used its own bounded API timeouts and completed in about 12 seconds.

Post-run bounded API probe found simulation stopped, root at reset
`(-0.300000, -0.935740, 0.075000)`, and both wheel targets zero. No controller
remained; CoppeliaSim PID 99503 / launcher PID 99512 remained present. Correct
matrix indexing uses the local +Z column `(m[2], m[6], m[10])` of the row-major
3x4 matrix: root planar heading `atan2(m[6],m[2])` is approximately -179.9997
degrees (equivalent to +180.0003 degrees), not -90 degrees. Camera local +Z
projects to approximately -179.998 degrees, within about 0.002 degrees of
root heading. This is reset-state geometry only. There are no
camera frames, controller pose, mission status, Hospital hold evidence, speed
maxima, marker-image margins/misses, or coasting measurements in this attempt.
No simulator restart was made because the post-run API and stopped reset scene
were healthy. The requested live diagnostic remains uncompleted; inspect the
startup `Resource temporarily unavailable` cause before scheduling another
run. No source changes were made.

## Corrected-readiness Hard runs — November 12, 2026

The startup trace in `runtime-edge-trace-hard-1` showed the child controller's
last successful RPCs were `drive()` calls, followed by a 3-second timeout on
`sim.getSimulationState` while the parent concurrently called
`sim.startSimulation`. The parent start call also timed out during the
transition, although the engine had entered running state with zero wheel
targets. The temporary harness was corrected outside the submission source:
it starts the engine with zero targets, waits for `simulation_advancing_running`
before spawning the controller, and bounds the parent startup client at 15 s
(controller API calls remain bounded at 3 s). The source `task3.py` was not
changed; its hash remains
`fd2acd30c041ecf2a2a3bd50e7ba6b05a6e0644e1fefb6ad271d1d26d65e8d11`.

Two same-source full Hard runs then completed:

- `runtime-edge-prelimit-hard-3`: engine ready at sim 0.05; controller parked
  at absolute sim 179.70 (parking phase 160.35–179.70, 19.35 s); recorder ended
  at 181.05. Controller rc 0, 718 frames, finished true / failed false. Final
  image pose: forward 0.206201 m, lateral -0.004580 m, heading -0.059330 rad
  (-3.40 deg), fresh heading observed. Correct marker-frame analysis: ID_1
  center is at world x=-0.35, bay centerline y=-0.73, and desired vehicle +Z
  heading is 180 deg. Matrix root center-forward `rootX-markerX` was 0.213943 m
  (13.943 mm from 0.20 m, inside the original +/-15 mm bound by 1.057 mm).
  The front point `root + 0.06*unit(root +Z)` was
  (-0.195922,-0.727293), giving bay-left lateral -0.002707 m. Matrix heading
  was 176.148 deg (error -3.852 deg, inside +/-5 deg). Image pose differed by
  -7.742 mm forward, -1.872 mm front-lateral, and +0.452 deg heading. The
  selected saved-image PnP reprojection RMS was 0.270 px. Camera and root
  matrix headings differed by 0.0044 deg. Hospital stop/rest/complete logs:
  28.20/29.05/34.35 s;
  independent truth samples span 28.85–34.35 s (5.50 s), net displacement
  2.97 micrometres and maximum excursion 5.71 micrometres. Global/zone command
  maxima 2.99994/1.20 rad/s. Parking marker visible in 83/83 PnP frames, zero
  misses, minimum full-quad image-border margin 48 px. Minimum camera bearing
  margin was 9.52 deg; the observed-heading 1.2 rad/s prelimit ran on 6 frames
  and the unobserved-heading zero-stop ran on 2 frames. Truth snapshots bracket
  these brief zero commands too sparsely to isolate coasting; the parked
  recorder tail 179.90–181.05 moved 1.8 micrometres.
- `runtime-edge-prelimit-hard-4`: engine ready at sim 0.70; controller parked
  at absolute sim 186.45 (parking phase 164.50–186.45, 21.95 s); recorder ended
  at 187.15. Controller rc 0, 705 frames, finished true / failed false. It is
  6.45 s over the 180 s target. Final image pose: forward 0.210741 m, lateral
  -0.006317 m, heading -0.085544 rad (-4.90 deg), fresh heading observed.
  Correct marker-frame analysis gives root center-forward 0.219022 m
  (19.022 mm from 0.20 m), 4.022 mm beyond the original +15 mm bound. Front
  point was `(-0.190704,-0.725825)`, bay-left lateral -0.004175 m (inside
  +/-25 mm). Matrix heading was 174.524 deg, or -5.476 deg from the desired
  180 deg, 0.476 deg outside the original +/-5 deg limit. Thus the image pose
  passed its former gates while physical center-forward and heading did not.
  Image-vs-matrix differences were -8.281 mm forward, -2.142 mm front-lateral,
  and +0.575 deg heading; selected saved-image PnP reprojection RMS was
  0.408 px. Camera and root matrix headings differed 0.0003 deg.
  Hospital stop/rest/complete logs: 32.00/32.90/38.25 s; independent truth
  spans 32.75–38.25 s (5.50 s), net displacement 8.63 micrometres. Global/zone
  command maxima 2.99986/1.20 rad/s. Parking marker visible in 89/89 PnP
  frames, zero misses, minimum full-quad image-border margin 58 px. Minimum
  camera bearing margin 10.70 deg; observed-heading prelimit ran on 6 frames;
  no unobserved under-15-degree stop frame occurred.

Evidence directories are
`/private/tmp/task3-followup.ZNTHv6/runtime-edge-prelimit-hard-3/` and
`/private/tmp/task3-followup.ZNTHv6/runtime-edge-prelimit-hard-4/`. The corrected
reset heading supersedes the earlier erroneous -90-degree report. Harness
evidence does not certify collision or off-road contact. Earlier failed
startup and timeout artifacts remain preserved. Medium/Easy validation and
official supported-platform recording remain outstanding; no portal or push.

## Symmetric terminal margin and startup-ready validation — November 12, 2026

Hard 3/4 marker-frame reanalysis corrected the vehicle-frame projections above.
Hard 3 matrix center-forward was 0.213943 m (within the original 0.20 +/-
0.015 m bound by 1.057 mm), front-point bay-left lateral -0.002707 m, and
heading error -3.852 deg. Hard 4 center-forward was 0.219022 m (4.022 mm
outside the +15 mm bound), front-point lateral -0.004175 m, and heading error
-5.476 deg (0.476 deg outside +/-5). Hard 4's image estimate had passed its
former gates. Selected saved-image PnP reprojection RMS was 0.270 px / 0.408 px
for Hard 3/4; this is fit residual, not a bound on systematic pose error.

The harness was then changed to gate the controller locally after its import,
connection and handle lookup, while the simulator is still stopped. Parent
starts the engine only after that ready signal, waits for
`simulation_advancing_running`, then releases the child; no controller RPC or
motor command occurs during engine transition. Startup RPC bound is 15 s,
controller RPC bound 3 s, and simulation/runtime limits remain bounded. Hard
calibrated run `runtime-edge-calibrated-hard-1` used source
`2deace445148d273902a7b73533548a27554939959b4868e8e82b5ea9e04713d` (the
version before the later signed-bias removal). Controller was ready before
engine start; engine ready at absolute sim 0.10, first camera/control frame at
0.30. Parking began at 158.75, parked at 192.55, and recorder ended 193.05:
33.80 s parking phase and 12.55 s over the 180 s target. Controller rc 0,
finished true / failed false, 813 frames.

At parking completion, matrix marker-frame measurements were center-forward
0.205687 m, front-point bay-left lateral about -0.000905 m, and physical
heading error -0.7774 deg against the 180 deg bay direction. All satisfy the
original +/-0.015 m center-forward, +/-0.025 m front-lateral, and +/-5 deg
heading bounds. The raw image estimate was forward 0.197211 m, lateral
+0.001333 m, heading -1.8194 deg. Compared with marker-frame ground truth, the
forward under-report was +8.476 mm, while lateral and heading residual signs
reversed from Hard 3/4. Therefore the fixed signed lateral/yaw biases were
removed after this run. Forward correction +0.0083 m remains supported by all
three runs. Current source hash after the correction is
`a45b3001789e4dbcdd4bd881e725fae6981ca1b7df0cb61a3ad2d8a4175a4b38`; this
post-run version has not had a full live Hard run.

Current terminal gates keep the original physical bounds unchanged and use
calibrated image center-forward plus symmetric internal windows: +/-0.010 m
forward, +/-0.015 m front-lateral, and +/-3.5 deg raw heading. Fresh observed
heading and the existing stillness/settle checks remain required. Added
regressions reject the former Hard 4 image pose and exercise both signs of
heading/lateral errors. Regression suite: 65 passed; syntax compile passed.

The calibrated run had a 5.25 s independent-truth stationary Hospital interval
(28.15–33.40 s), net displacement 8.63 micrometres. Global/zone command maxima
were 2.99954/1.20 rad/s. ID 1 was detected in 134/134 parking PnP frames, with
zero misses, 5 px minimum full-quad image-border margin and 5.17 deg minimum
bearing margin; the observed-heading prelimit ran on 34 frames and unobserved
near-edge zero-stop on 5 frames. No collision/off-road certification is
available.

Saved parking trace: calibrated forward first crossed the original physical
upper window at 191.20; the tight forward window and symmetric lateral/heading
gates first all passed at 191.35. The 0.25 rad/s terminal correction lasted
about 0.15 s, then command stayed zero through park at 192.55. Thus that crawl
does not explain the 33.80 s phase: 32.45 s elapsed before reaching the
physical forward window. Keep speed and physical limits unchanged; timing work
should analyze the earlier merge/edge-limited segment rather than raise the
terminal crawl or weaken acceptance. No additional full run was made after the
signed-bias removal. Evidence is under
`/private/tmp/task3-followup.ZNTHv6/runtime-edge-calibrated-hard-1/`.

## Rear-frame consistency run — November 12, 2026

Exact current `task3/task3.py` SHA256:
`f47462a64c25347d12addd49b9d9c7cc73d747b155ffc1ba90e2312118bbe39e`.
Rear-frame change is implemented and tested: pose lateral is the signed front
axle offset, forward is center-to-marker distance, and heading is bay-relative.
Quintic handoff/progress/error now use `(lateral - L*sin(heading),
forward + L/2*cos(heading))`; center-frame `MERGE_END=0.26 m` translates to rear
endpoint `0.32 m`. The calibrated terminal completion, braking and stillness
paths remain on their original pose conventions. Steering gains, caps, guards,
physical limits, forward calibration and holds were not tuned.

`/Users/aryanachary/.venv/bin/python orchestration/check_task3.py`: 67 passed.
Syntax compilation and scoped `git diff --check` passed. Regression output:
`/private/tmp/task3-followup.ZNTHv6/rear-frame-tests.out`.

One full Hard run used the controller-ready harness and verified stopped/reset
scene; no concurrent controller existed. Command:
`/Users/aryanachary/.venv/bin/python /private/tmp/task3-followup.ZNTHv6/rehearse_groundheading.py Hard rear-frame-consistency-hard-1 --reuse-verified-hard-scene`.
Absolute sim startup 0.10 s; first nonzero drive 0.30 s; parking entry 158.20 s;
parked 183.90 s (25.70 s parking); controller rc 0, 766 frames,
finished=true/failed=false. The run misses 180 s by 3.90 s.

Marker-frame interpolated diagnostic pose at completion: center-forward
0.193756 m, front lateral -0.002530 m, heading error -2.433°. Final image pose:
forward 0.187022 m (calibrated 0.195322 m), lateral -0.003724 m, heading
-2.082°. Hospital logged 5.30 s stationary hold; independent truth samples span
4.75 s (27.70–32.45 s) with 6.4 µm net displacement. Command maxima: global
2.99987 rad/s, active zone 1.20 rad/s, parking 2.95 rad/s. Marker PnP visible
118/119 parking diagnostic observations (1 missing); 1 invalid pose among 120
control frames; 22 frames had unobserved heading; minimum bbox border margin
4 px. No collision/off-road sensor evidence is recorded. Full evidence and
method details are in the latest rear-frame section of `TASK3_RESULTS.md` and
`/private/tmp/task3-followup.ZNTHv6/rear-frame-consistency-hard-1/`.

Remaining acceptance: repeated Hard <=180 s, Medium twice, Easy once, and the
team's supported-platform official artifacts. No portal submission or push.

### Time-aligned yaw prediction — November 12, 2026

Current `task3/task3.py` SHA256:
`6e2111c1b360f88c065127704f369da176313e7171706e4eb689ad9da603700c`.
Pose prediction integrates the previous final bounded steering/speed command
over valid sim dt; no filtered-range-derived yaw travel or fixed 1 cm clipping.
First-observation and invalid-time intervals do not invent movement. PnP gates,
recovery, observation freshness and physical caps were retained. The harness
wrapper accepts and forwards `last_speed`. `/Users/aryanachary/.venv/bin/python
orchestration/check_task3.py`: **72 tests passed**; syntax compilation passed.

Saved raw-PnP replay evidence is diagnostic only: maximum fused yaw error
32.80° -> 22.16°, bad normal updates 1 -> 0, p90 error 4.243° -> 4.245°.
Baseline replay matches logged yaw for the first two timed frames, then diverges
up to 4.494° (p90 1.076°); no timing savings are inferred. Replay seed is the
final untimed handoff at 158.2 s; first timed observation is 158.4 s.

One full Hard run used the verified stopped/reset scene and ready-before-start
harness, command:
`/Users/aryanachary/.venv/bin/python /private/tmp/task3-followup.ZNTHv6/rehearse_groundheading.py Hard yaw-prediction-hard-1 --reuse-verified-hard-scene`.
Startup 0.10 s; first drive 0.25 s; Hospital halt/rest/departure
26.85/27.70/33.15 s; parking entry 159.65 s; parked 182.35 s; harness end
182.80 s; controller rc 0, finished=true, failed=false, 699 frames. This is
2.35 s over 180 s. Image completion pose: forward 0.199457 m, calibrated
0.207757 m, lateral -0.005393 m, heading +0.241°. Marker-frame truth
interpolated over 182.15–182.80 s: center-forward 0.208027 m, front lateral
-0.005311 m, heading error +0.153° (diagnostic-only truth). Limits: 2.99993
rad/s global, 1.20 zone, 2.95 parking, max steering 0.682 rad. Zero motor target
samples span 27.20–33.15 s; visual rest confirmation spans 27.70–33.15 s.
Parking: 93/93 valid image poses, five frames without fresh heading, no invalid
poses; 40/40 saved screenshots show full marker, minimum quad border margin
60 px. Replay reproduces all parking commands. Visibility was dominant cap
exposure (8.70 s). Full diagnostics:
`/private/tmp/task3-followup.ZNTHv6/yaw-prediction-hard-1/`.

Next: Sol review. This run does not establish <=180 s. Repeated Hard <=180 s,
Medium twice, Easy once, and official supported-platform evidence remain open.

## Visibility path audit — November 12, 2026 (latest authoritative state)

Continue only `TASK3_VISIBILITY_PATH_WORK_ORDER.md`; Sol review is next.
Current and exact live-run source SHA256:
`ee5f7a1407a328766e8ef115294d6ef8567508dcea615f7f57c221dd2358f387`.
Parker selects cubic once at handoff only with >=3-degree planned-bearing
improvement, a 5-degree reserve below the 32.5-degree speed prelimit, and
curvature <=90% of the physical bound; otherwise quintic remains. Endpoint,
rear-frame conversion, guards, gains, estimator, holds, speeds, braking and
terminal behavior were preserved. Latest audit made no controller changes.

Final suite: **74 tests passed in 0.925 s**; syntax and scoped diff checks
passed. Initial new endpoint assertion failure was fixed by sampling the
one-sided active interval. Whole-repository whitespace check encountered
pre-existing task2a CSV CRLF/trailing whitespace; it was left untouched.

Exactly one existing run: `visibility-cubic-hard-1`. Ready-before-engine
startup 0.15 s, first drive 0.40 s, parking entry 158.75 s, park 181.05 s,
recorder end 181.75 s; cubic selected, rc 0, 665 frames, finished=true,
failed=false. Absolute park time is 1.05 s above target. Interpolated physical
completion (180.65–181.20 s bracket): center-forward .205674 m, front lateral
-.005138 m, heading -1.954 degrees, within the original physical bounds.
Final image: .197662 m raw / .205962 m calibrated forward, -.005407 m front
lateral, -1.894-degree fresh heading. Confirmed Hospital rest samples span
27.70–33.10 s (5.40 s), net 6.10 micrometres. Commands respect global/zone/
parking maxima 2.99999824/1.20/2.95 rad/s and .68195431 rad steering.

Parking: 87/87 valid poses, 14 unobserved-heading frames, no marker loss;
80/80 saved regular+edge images contain the complete ID 1 marker, min margin
64 px (37/37 regular images, min 73 px). Exact replay matches every parking
command. Binding visibility cap 5.05 s versus baseline 8.70 s; uncertain-edge
stop .90 s versus .25 s. Bearing >32.5 degrees lasts 2.55 s. Parking phase
22.30 s versus baseline 22.70 s; total improvement 1.30 s includes .90 s
earlier entry and is not causal proof from an unpaired run. Image-derived
maximum rear tracking error 140.34 mm is not physical travel: interpolated
physical rear lateral error against the same commanded reference is at most
30.04 mm. Physical heading tracking error reaches 17.034 degrees during the
merge; final heading is within bounds. Truth remains diagnostic only.

Authoritative audit: `/private/tmp/task3-followup.ZNTHv6/visibility-cubic-audit/REPORT.md`,
`audit.out`, `summary.json`, `tests.out`, `source.diff`, `geometry-audit.txt`.
Raw run: `/private/tmp/task3-followup.ZNTHv6/visibility-cubic-hard-1/`.
The provisional summary script's wrong cap/pose conversion was superseded;
do not reuse its 11 s cap or near-180-degree heading result. The simplified
lag/noise model is assumption-based and does not certify post-merge actuator
settling. Full methodology and limitations are in `TASK3_RESULTS.md`.

Post-run read-only process/API check: no active task controller, simulator
stopped at sim time 182.05 s, both motor targets zero. No further tuning or
live run occurred in this continuation. Preserve all dirty scenes and failed
artifacts. No push, portal or readiness claim. Acceptance remains repeated
Hard <=180 s, Medium twice, Easy once, physical behavior and official
supported-platform artifacts. Collision/off-road sensor certification is absent.

## Reproducibility work order — November 12, 2026 (latest authoritative state)

`TASK3_REPRODUCIBILITY_WORK_ORDER.md` is executed; Sol review is next. No further
run or tuning is pending. Exact controller and both recorded-run SHA256:
`ee5f7a1407a328766e8ef115294d6ef8567508dcea615f7f57c221dd2358f387`.
Controller/tests unchanged; previous 74 passing tests retained, not rerun.
Dirty workspace scenes were hash-verified unchanged. One successful startup
attempt per arena, no restart; Medium temporary scene matches clean HEAD blob
`4a33232ee583c654c9ae69589f1a4bd3b282a4e7`.

- Hard repeat `visibility-cubic-hard-2`: engine .05, first drive .20, Hospital
  stop/rest/depart 26.65/27.60/33.00, zone enter/exit 45.35/128.85, parking
  entry 159.15, park 182.10, end 183.75 s. Cubic; rc 0, finished=true/failed=false,
  705 frames. Physical completion .201955 m center-forward, -.000854 m front
  lateral, -1.389 degrees, bracket 181.85–182.55 s: within original bounds.
  Hard 1/2 park times 181.05/182.10 are both over 180; entry differs .40 s and
  parking phase .65 s. Full marker 84/84 captured images, min 93 px; no loss.
  Binding visibility 4.80 s, yaw 4.20, frame 4.15, settle 2.40, edge-stop zero.
- Medium `visibility-cubic-medium-1`: engine .50, first drive .70, Hospital
  34.65/36.00/41.40, Speed40 entry 53.60, no zone-exit event, parking entry
  221.50, park 266.10, end 266.60 s. Quintic fallback; rc 0,
  finished=true/failed=false, 941 frames. Physical .204269 m / +.002921 m /
  -1.377 degrees, bracket 266.00–266.60 s: within original bounds. Full marker
  160/160 captured images, min 23 px; no loss. Visibility 21.20 s, frame 11.45,
  yaw 4.55, edge-stop .40. Zone stays active through all 44.60 s of parking;
  final Mission zone cap further reduces speed for 19.15 s. Exact saved-pose
  replay with final Mission caps matches all commands in both new runs.
- Hospital visual rest is 5.40 s in each. Hard zero-target samples span 6.15 s,
  max excursion 16.68 micrometres; samples strictly within visual rest span
  only 4.60 s. Medium confirmed-rest truth samples span 5.05 s, net 5.87
  micrometres. Pickup-patch location is UNVERIFIED: no patch transform/bounds
  were recorded. Duration alone does not prove rest within the required
  approximately 10 cm across by 20 cm along patch.
- Commands respect limits: Hard global/zone/parking 2.99998278/1.20/2.95 rad/s;
  Medium 2.99980275/1.20/1.20; steering .68195431 rad both.

Focused next correction: Medium second-sign perception from preserved frames.
All 146 logged normal Speed40 records are the first encounter (53.60–90.15 s);
none later. Current weak-board detector produces zero candidates on all 437
saved regular frames. Captures cover the oblique board: at 126.30/130.00 s its
thin white component fails pixel/aspect gates; at 135.15 s bbox [458,46,14,44]
has 34 blue but zero red pixels, failing rim evidence. Comparable Hard exit
frame 128.85 s passes with 57 blue/11 red. Saved 120–145 s window: 45 frames,
max gap .70 s. Live weak candidates/tracker state were not logged, so do not
invent exact unsaved-frame behavior or assume heuristic sign identity is proved.
Use these frames for sign-specific evidence before any gate correction; preserve
distinct-encounter/rearm and conservative zone behavior. No correction was made.

Evaluator scoring is not certified: collision is 9 cm square overlap, off-road
is a wheel >1 cm outside allowed road including yellow. Harness has no matching
square-overlap, wheel-boundary or official penalty records; physics contact
would not substitute for these evaluator criteria. Hospital location also open.

Full results: latest section of `TASK3_RESULTS.md` and
`/private/tmp/task3-followup.ZNTHv6/reproducibility-audit/REPORT.md`.
Raw logs/frames remain in both run directories. Exit-frame manifest and component
measurements are in the audit directory. Final status: no task controller,
simulator stopped at 266.85 s, motors zero. No new child, tuning, push, portal,
score claim or official artifacts. Acceptance remains repeated Hard <=180 s,
Medium twice, Easy once, scored physical compliance and supported-platform artifacts.

## Oblique exit safety correction — November 12, 2026 (latest authoritative state)

`TASK3_OBLIQUE_EXIT_WORK_ORDER.md` bounded offline work is complete; Sol review
is next. Current source SHA256:
`ea3a4954d97dcced427beac4cf379b6a6bce64b6c20e0a732a4602135f6a7da8`.
Only `_whiteboard_speed_candidates` changed: unsafe white/blue hull fallback
returns no candidates. Normal Speed40 detection, first entry, distinct second
encounter/rearm, 1.2 cap, gains, parking and estimator are unchanged. No scene
or unrelated source edits. 77 tests passed in .746 s; syntax/scoped diff checks
passed. New recorded Parking regressions fail against the previous source,
including false zone release. Reference-absent readable Speed40 examples pass.

Identity correction: the x458 blue strip at Medium 135.15 is associated with
Parking shape 54, not Speed40. Read-only static mesh projection puts actual
Speed40 shape 47 at x384.6–393.6, and Parking at x455.5–475.5. At Hard 128.85,
actual Speed40 is x414.7–427.0, Parking x492.2–519.1. Old accepted weak bbox
[496,44,19,47] is Parking-associated; its 11 red samples at x498–505 are not
a rim around the actual Speed40. Exact red surface/texel owner is not proved,
but the semantic red/blue hull fusion is unsafe. Prior accepted Hard weak
exit images are now negative examples, not true-exit semantic evidence.

Actual second Speed40 is the separate red/white sliver; its 40 glyph is not
reliably observable in the saved oblique sequence. No supported replacement
true-exit detector was built. Therefore **no Medium or Hard live run** was
started, as directed. Normal-only frozen replay retains zone count 1 for both
old logs; old Hard exit disappears. Keeping <=1.2 may worsen timing, and no new
runtime is claimed. Old 181.05/182.10/266.10 results do not validate this hash.

Next concrete milestone: labeled discriminative original pixels for actual
Speed40, plus positive/negative detector proof before any new live run. Do not
broaden generic blue/white or drop red evidence; preserve distinct encounter
semantics. Existing Hard timing/official acceptance remain open independently.

Audit/report: `/private/tmp/task3-followup.ZNTHv6/oblique-exit-audit/REPORT.md`
and latest `TASK3_RESULTS.md` section. Audit has original-pixel comparison,
45-frame chronological sheets/manifests, static sign meshes/projections,
per-pixel red coordinates, semantic comparisons, embedded regression crops,
source diff, 77-test output and expected baseline failures. Scene projection
is diagnostic only and not exact pixel-ID segmentation; no geometry entered
control. All user-dirty scenes and original frames preserved.

Last final check: simulator stopped at 266.85 s, motor targets zero. Only
bounded read-only stopped-scene inspection occurred; no new run/controller/child.
Hospital patch location, evaluator square-overlap and wheel-road boundaries,
reliable Hard <=180, Medium twice, Easy once and official Windows/Ubuntu
artifacts remain unverified. No portal/push/readiness claim.

### November 12 — bounded red-rim shape candidate gate

Luna reviewed the saved original-pixel comparison, appearance diagnostics,
regression ROIs and static projections for the single red-rim shape candidate.
The true oblique Speed40 projects to only 9.0 x 60.4 px in Medium 135.15 and
12.2 x 63.2 px in Hard 128.85. In the original-pixel comparison its red/white
edge is fragmented; a closed rim and a measurable enclosed interior are not
visible. The existing normal detector uses component area >=150, solidity
>=0.88, bbox aspect >=0.45, circularity >=0.55 and dark-interior ratio >=0.01.
These gates operate on a coherent red component; the oblique fragment supplies
no evidence for defensible relaxed thresholds or a normalized ellipse/rim
residual. A narrow red/white strip is compatible with unrelated trim, and the
separate blue/white component is Parking-associated. The saved earlier/later
sequence and 45-frame audit do not establish a class-specific curved rim.

Outcome: original pixels are insufficient for this bounded classifier. No
controller or regression-test edits were made, no synthetic shape rule was
invented, and no live Medium/Hard run was authorized by the evidence gate.
The <=1.2 zone cap and disabled weak white/blue fallback remain unchanged.
Source SHA256 remains
`ea3a4954d97dcced427beac4cf379b6a6bce64b6c20e0a732a4602135f6a7da8`; no
verification suite was rerun because implementation was not supported. The
specific next evidence needed is a higher-resolution, unoccluded view of the
actual red face that resolves either coherent rim curvature or discriminative
interior structure, followed by recorded positive/negative regressions before
any live run.

### November 12 — whole-route best-original-view review

Correction to the preceding suggestion: do not seek or create a higher-resolution
view. Camera resolution, FOV and pose settings must stay unchanged under the
official rules. The earlier two-crop conclusion was too broad. A bounded
projection ranking used existing sign mesh handle 47, validated camera/image
conventions and saved world/camera matrices from
`visibility-cubic-medium-1` and `visibility-cubic-hard-2`; ten temporally
distinct pre-parking views per run were ranked and inspected in original
pixels. No scene, source or camera was changed. Report and temporary
crops/contact sheets:
`/private/tmp/task3-followup.ZNTHv6/oblique-exit-audit/BEST_VIEW_REPORT.md`.

The first projected in-frame edge appears near Hard 96.35 s and Medium 103.10 s
(matrix gaps .30/.15 s); these are edge slivers, not proof of visible sign
pixels. Medium's best reviewed original views are 140.65 s (17x37 px, 87.5°
edge-on) and 141.25 s (19x39 px, 88.3°). Their projected-rectangle HSV counts
are 8/155 and 4/141 red/white; the crop shows an interrupted rim beside gray
occlusion, with no readable 40 or closed circle. Hard's best genuine candidate
before parking at 131.20 s projects 17x37 px at 87.8° but has zero red/white
pixels in its projected rectangle. At 128.85 s the 9x30 px projected face is
also occluded and has zero red/white pixels. Hard 143.10 s projects 54x61 px
at 54.1°, but the original pixels are building awning/trim; it is a
confuser/occlusion, not a Speed40 observation. Projection bounds and rectangle
color counts are not object-ID segmentation or recognition proof. Selected
frame-to-matrix gaps were up to .30 s Medium and .35 s Hard; sparse frames
leave intermediate visibility unexcluded.

No supported classifier change follows: the normal red-component area,
solidity, aspect, circularity and dark-interior gates have no coherent sign
evidence to act on in these candidates. Legitimate future evidence could come
from already-recorded sparse-frame gaps or an ordinary saved frame when the
vehicle naturally has a less edge-on view from its existing lane with the
unchanged camera. No camera movement, non-obstacle lane change, route-progress
release, implementation or live run is recommended by this audit. Prior
timing/scoring/official-artifact acceptance remains open.

### November 12 — dense-camera Hard run completed

Authoritative run artifacts/report:
`/private/tmp/task3-dense-camera/dense-hard-ea3a4954/` and
`DENSE_CAMERA_REPORT.md`. Source hash remains
`ea3a4954d97dcced427beac4cf379b6a6bce64b6c20e0a732a4602135f6a7da8`; clean
HEAD Hard scene Git blob `370d8299033e8b14384eea1d49781b26a2c61434` was
extracted to temporary storage; workspace scenes/source unchanged. Elevated
preload API: `{"state":0,"time":266.8500000000264}`. One ready-before-engine
Hard run, engine .15 s, parked 238.25 s, harness end239.10 s, controller and
harness rc0, finished=true/failed=false. Post-run API: stopped at239.45 s,
both motor targets0. No restart or second run.

Captured 840/840 consumed pre-parking BGR frames, .35–199.55 s, max gap .40 s,
0 dropped/write errors; async copy/enqueue mean/max .138/.372 ms. In-run normal
detection telemetry had a temporary logger shadowing defect; exact detector
replay on all saved images found 144 first Speed40 detections 45.55–83.30 s
and none after tracker rearm87.35 s. Tracker count1/rearmed=true, zone never
exited. Best actual pixel candidate 159.85 s is mostly clipped and overlaps
storefront/awning; red/white ROI counts do not prove board identity. No
discriminative Speed40 face/glyph established. See report for measurements.

Hospital rest note27.90 s, halt complete33.35 s; zero target samples27.30–33.35
s (6.05 s, 0.025 mm max root displacement), pickup patch location unverified.
Zone entry45.55/no exit; parking entry199.55, park238.25 (38.70 s). Max speed
2.99985 rad/s outside and1.2 in zone. Physical terminal pose: center-forward
.20616 m, front-lateral-.00378 m, heading error+1.769°, .50 s matrix bracket.
Hard completion exceeds180 s; collision/off-road scoring, repeated Hard,
Medium twice, Easy once and supported-platform artifacts remain open. Source
unchanged; no tests rerun. Next classifier experiment is parent decision.

Projection-review correction: marker-validated mapping (horizontal flip) has ID1 corner RMS 4.99–5.18 px. The first readable board at 80.20–83.30 s corresponds spatially to saved Medium Speed40 handle49; handle47 is the other placement and projects at x581–622 at 134.45 s, away from the separate x≈445 feature. Do not treat handle47 ROI/projection as a labeled sign or treat x445 as identified. Stopped Hard scene has one queried named Speed40 alias with differing transform/mesh, so it cannot label historical pixels. Marker and Parking anchors match. No evidence here proves second-sign usability or impossibility. Report: `/private/tmp/task3-dense-camera/dense-hard-ea3a4954/PROJECTION_REVIEW_REPORT.md`; source/tests/scenes unchanged.

Parent saved-data cross-check: camera45.40 + Medium Speed40 handle49 center projects with horizontal flip to `(624.775,65.980)`; observed first board bbox at45.55 center `(622,65.5)`, ~2.8px over0.15s. Unflipped x≈15 is inconsistent. Global horizontal flip and first-sign correspondence supported; x445 at134.45 could be storefront decoration, still unidentified. No ID2 image corners detected in saved images; only ID1 supports measured multi-frame ArUco anchor validation. Hard/Medium transforms/mesh deltas remain in projection report.

### November 13 — Astra reviewed startup proof; Luna continuation limited

Read `/private/tmp/task3-dense-camera/startup-handshake-proof/proof-report.json`
and `cleanup.json`. Short zero-motor proof PASS: start RPC returned normally,
state17 at0.70s, same child acknowledged at1.10–2.10s with both targets0.
Cleanup stopped at2.90s; report records clean isolated Hard reloaded at0s,
both targets0. This proves the normal handshake path, NOT recovery from a
timed-out start RPC. No new driving run or controller improvement follows
from this proof. Current live simulator state must be checked before reuse.

Existing Luna worker `01a1d065-7e28-7812-873b-39830228d74e` returned a usage-limit
error. Resume plus a fresh continuation message returned the same error on
November13; tool suggested retry after02:01AM. This is a tool execution result,
not an assertion about account ownership or billing. Keep execution assigned
to Luna under user's explicit preference; do not spawn duplicate work merely
to bypass the limit. Next: resume this worker when available, integrate/test
bounded timeout recovery in the actual dense harness, then proceed with the
existing consolidated finish work order. Controller timing/sign/scoring and
official artifact gates remain open. Goal not complete.

### November 13 — Luna integrated oblique candidate, run result

Source hash `d3322413c3261e12935970692144b8eced8457daa800b297d8c739cff38fc2b2`. Corrected ellipse axes retain OpenCV angle/radius pairing. Embedded original-camera crop regression replaced the invalid already-warped fixture; 79 tests passed, compilation and scoped diff whitespace checks passed. Valid-travel integrated replay consumed all 954 frames, entered45.75 and exited132.20; recorded wheel-velocity integration approximates commanded travel. Artifact: `/private/tmp/task3-luna-sagan-v4/integrated_valid_replay.json`.

Live clean Hard finished rc0: entry45.00, exit131.70, Hospital rest27.65–32.90, parking start160.45, parked180.90, harness end181.70. Camera terminal estimate forward0.198611m, lateral−0.005091m, heading−0.019798rad; these are camera estimates, not independently verified physical parking measurements. Evidence `/private/tmp/task3-dense-camera/oblique-structural-final/`. Post-run saved API check stopped182.15, both motors0. Source unchanged since replay. Timing exceeds180 by0.90s; no acceptance/readiness claim.

Execution deviation: selected resilient harness retained dense capture (663 frames, zero drops), despite the requested LIGHT/no-new-dense constraint. This run must not be described as light instrumentation. No further run launched. Physical parking, scored Hospital patch/collision/off-road evidence and repeated arena acceptance remain unverified.

### November 13 — genuine light harness verification

Unchanged d3322413c3261e12935970692144b8eced8457daa800b297d8c739cff38fc2b2. Saved prior-run physical audit (`oblique-structural-final/physical-audit.json`) uses root local +Z: center-forward0.20645m, front-lateral−0.00591m, heading−0.748deg; all original bounds pass, completion bracket0.50s. Hospital27.65–32.90 duration5.25s; pickup patch unknown.

Temporary `rehearse_light.py` removes dense capture/thread, periodic screenshots, scene identity queries, per-frame geometry, and redundant perception. Saves only confirmation-frame copies after control ends, per-frame commands/events, and one terminal truth snapshot. Config saved before run. Clean reset-pose/zero-motor handshake verified. Actual light run `/private/tmp/task3-dense-camera/oblique-light-1`: entry45.45, NO exit, parking200.55, parked240.40, harness end241.40, controller rc0. Hold27.85–33.15. This is a perception/temporal robustness failure; do not tune speed to compensate or claim reliable180s. Initial cleanup timed out (`Again: Resource temporarily unavailable`); fresh bounded recheck confirmed stopped241.75, motors0 (`cleanup-recheck.json`). No duplicate controller or further run.

## Luna active robustness continuation — November 13

- Parallel raw observation / gated confirmation source `833cbe71336ef685a9b30340c9d34288bea936953bfb6476b3945a22aace61d9`: 954-frame replay entered45.75/exited132.00; 81 tests passed. LIGHT `oblique-parallel-light-1` entered45.70/exited132.65/parked183.15. Two actual raw observations132.00 `[589,40,31,51]`,132.65 `[616,40,24,52]`; confirmed only second. Exact audit and saved images in run directory. Terminal184.90 forward.204881/frontlat.009071/heading-.431deg passes; stopped185.15/motors0. Hospital hold28.00–33.45; patch location unverified.
- ROI morphology optimization `da03aeaab043db788d2c5366150c432bde51afb9b0e62cbd717f3f82284b20bf`: 979-frame exact output equivalence, detector3.52→1.96s. LIGHT `oblique-roi-light-1` parked188.35, terminal190.10 forward.204855/frontlat.002748/heading-.165deg; stopped190.50/motors0. Startup delay included, never subtracted. Command caps pass both runs. Not timing acceptance.
- Self-contained raw LIGHT edge fixtures added: 82 tests pass, including single observation, dropout, inconsistent box rejection. Corrected frozen validation now counts failed checks independently of saved patches and rejects other accepted proposals on positive frames. Older Medium unreadable sliver excluded from semantic-positive claim. `/private/tmp/task3-luna-sagan-v4/frozen_gate_validation.json`.
- Parking profile replay reproduces commands exactly. ROI run chose quintic: predicted cubic27.575deg narrowly misses27.5deg reserve; quintic33.982deg is worse. Added constrained merge extension leaving2cm aligned distance before nominal bay center, only if original curvature/bearing reserves both pass; all completion/stop/hold/caps unchanged. 82 tests + full replay pass. LIVE verification session54484, `/private/tmp/task3-dense-camera/oblique-path-light-1/`; result pending at this checkpoint.
- No dense capture or other controller launched. Full repeated-arena acceptance, physical Hospital location/collision/offroad evidence and official supported-OS recording remain unfulfilled. Do not label ready.

November14 follow-up: path-light-1 finished181.55, terminal pose passed; cleanup-recheck stopped182.90/motors0. Persistent handoff estimator candidate FAILED and was rolled back exactly; see oblique-handoff-light-1 rc1, cleanup stopped193.45/motors0. Current experiment retains original entry estimator and chooses longer cubic only when predicted curvature AND bearing improve within unchanged bounds.82tests pass. Active LIGHT session98297, artifacts oblique-safer-curve-light-1. No final timing/arena acceptance yet.

## Authoritative current checkpoint — November14 scored audit

NO ACTIVE CONTROLLER/SESSION. Historical session98297 and all later trials have completed. Source restored to conservative724e980bd947d073aac7c52160a72eabc07b486083bafc0f29328c94e0670497; 82 current tests pass. Rejected persistent-handoff and prediction-speed policies are absent. Always-extended cubic experiment also rolled back (no demonstrated benefit).

Read-only scored audit assets: `/private/tmp/task3-luna-scored-audit/` contains floor mesh/UV JSON, visually inspected2048px floor texture, scoring-target inventory, reproducible sparse harness builder and sampled scoring analysis. No named pickup patch found; Hospital containment remains unverified.

Baseline repeat with sparse parent-only geometry audit finished: `/private/tmp/task3-dense-camera/baseline-scored-audit-1/`. SAME724 source missed zone exit, parked236.25, terminal239.15 physicalforward.206222/frontlat.004165/heading.112deg passes. Stopped239.50/motors0 in final-state.json. This is a robustness failure, not timing acceptance. Geometry instrumentation affects frame pacing; no dense camera capture.

112 samples: max RPC span.10s, max gap2.70s. Minimum sampled9cm-square obstacle clearances.10121/.08519/.10100m; no sampled overlaps. Minimum sampled wheel-center road clearance-.003662m (centers only, not tire-envelope certification). No sampled center >1cm outside; continuous offroad/collision unresolved. Controller-rest interval28.85–33.90; pickup containment unverified. Exact limitations in sampled-scoring-summary.json. Next: inspect overlay and available exit observations, strengthen offline physical audit where possible before another run. No claim full acceptance.

## Current v6 candidate — supersedes prior active-state entries

Source3834422e0658805810f0e261e12b63e01995e158cc17014e7f99993be19dce0a. V5 failed unseen repeat (239.45/noexit); two retained roof negatives localized and embedded as full-frame regression. Actual early upright face IS proposed, not absent; feature coverage/white denominator rejected it. Composite v6 uses rim fit/aspect + white support + white/dark interior occupancy + glyph fragments; no largest-component cutoff. Tentative coverage.60, release remains currentcoverage.80 andwhite_inside.25, two spatial observations and distinct rearm unchanged; ambiguous131.70 stays tentative.

84tests pass, compile/diff pass, exact-hash15 development checks zero failures, integrated/prototype agreement; full954 replay entry45.75/exit132.00. All saved data development-only, not blind heldout. Artifacts `/private/tmp/task3-luna-robust-v5/v6-validation-final.json`, `v6-replay.json`, `v6-tests.log`, `failure-comparison.json`, `rim-support-measurements.json`. First NEW live v6 session6499 currently running, `/private/tmp/task3-dense-camera/robust-v6-unseen-1/`. No acceptance yet.

Scoring refinement `/private/tmp/task3-dense-camera/baseline-scored-audit-1/tire-footprint-audit.json`: conservative front tire disk possible15.87mm outside at207.50; rear projected mesh12.21mm at214.50. These are possible parking-edge excursions, not certified violations (phase/RPC/raster uncertainty), and prohibit zero-penalty claim. Hospital exact boundary still unknown. Official instruction page located https://themes.e-yantra.org/Niti-Vahan_2627/stage_1/task_3/instruction/ ; text accessible via search, figure direct retrieval not yet available.

## Latest completed current-hash audit — no live sessions

v6 source3834422 unchanged. Two unseen LIGHT runs exited correctly and parked180.80/180.60, terminal bounds/caps passed; still over180. Session6499/16060 completed. Current-hash phase audit session76303 completed parked182.25; stopped184.20/motors0. No active controller.

`robust-v6-phase-audit/current-tire-audit.json` reproduces rear-right excursion with actual wheel matrices: five samples beyond10mm, worst23.193mm outside at169.10.83phase samples,73parking, maxgap.40s/maxRPCspan.10s. Cylinder tire envelope eliminates rolling-phase/front-disk approximation. Do NOT dismiss parking exemption or claim no offroad penalty. Current-hash hold27.95–33.10, ten samples, center[-.940894,.099079], maximum sampled displacement5.73micrometers. Figure registration only establishes location correspondence; exact official boundary unknown.

Next diagnostic `/private/tmp/task3-luna-scored-audit/compare_merge.py`, run artifact merge-comparison.json: diagnostic marker lateral/heading basis explicitly negated to match controller coordinate convention. Actual rear path runs inward of reference while image lateral estimates fluctuate. Need isolate pose/tracking/entry clearance cause before correction. All world matrices remain diagnostics only. No acceptance claim, repeated arenas and official recording still outstanding.
