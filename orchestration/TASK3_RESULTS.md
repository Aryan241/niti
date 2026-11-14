# Task 3A results (local, unofficial)

> Historical results below describe the November 5 controller. The November 6
> review section appended below supersedes its behaviour and reliability claims.

Date: 2026-11-05. Solution: `task3/task3.py` (single file; imports only os/sys/time, cv2, numpy, ZMQ client).
`task3/reference_images/` (copied from 2B) is used at run time but must NOT go in the zip.

## Arena facts used (from the scenes and portal Figure 4)
- Lap is clockwise from spawn; start in the inner lane.
- Hard obstacles: left straight outer lane (ignore), top straight inner lane (change to outer),
  right lobe outer lane (change back to inner). Medium's third obstacle is hidden (layer 0).
- Hospital pickup: inner lane beside the red cross, ~0.565 m before the far Hospital sign.
- Parking: ArUco ID 1, spot centre ~0.20 m from the marker on the bay centre line.

## Behaviour
- Lane following: 2A detector + lane preference (yellow left/right of divider); lane change = flip preference.
- Obstacles: 2B red detector (strict white test), in-lane test against the divider, triggers only while ahead.
- Speed: 2.90 rad/s outside, 1.19 rad/s from the first Speed 40 sign (range <= 0.32 m, or seen within
  0.65 m then lost) to the end of the run (the second sign is not reliably visible clockwise).
- Halt: armed by a Hospital sign first seen > 0.75 m away; frame-rate-aware predicted stop; holds
  5.0 + 0.8 s of simulation time after rest is detected from frame differences.
- Parking: 2C pose estimator + smootherstep lateral path; stops at 0.20 m; script exits after 1 s settle.

## Local monitor results (dev-only scorer in scratchpad, ground truth from the sim)
Final version, Hard arena:
| Run | Off-road | Collisions | Over limit | Halt (s, along error) | Parked error | Min wheel margin | Time |
|---|---|---|---|---|---|---|---|
| normal x4 | 0 | 0 | 0 s | 5.9–6.4, ~1.5 cm | ~2 cm | ~1.9 cm | 224–227 s |
| +20 ms/frame (~0.36 s/frame) | 0 | 0 | 0 s | 6.7, 1.4 cm | 1.4 cm | 2.2 cm | 231 s |
| +30/40 ms (~0.65–0.7 s/frame) | 0–1 | 0 | 0 s | ~2 cm | parking fails | – | 290–300 s |

Easy 217 s and Medium 255 s complete (earlier build of the same logic).
Expected Hard score by the published scheme: ~100 − 23 (time) ≈ 77/100 ≈ 62/80. Not portal-graded.

Time budget (normal run): Speed 40 zone ~118 s at 1.19 rad/s (fixed); parking ~30 s at 1.19
(second sign not visible clockwise, so the zone cap is held); halt 6 s; rest at <= 2.9 rad/s.

## Remaining risks
- Graded run needs Ubuntu_eval or Windows_eval.exe (no macOS tool). Reliable up to ~0.36 s of sim time per
  processed frame (printed in the halt message); beyond ~0.6 s/frame parking degrades.
- Zone start position assumed "just before" the first sign; we slow ~0.25 m before it.
- `NV_VERBOSE=1` enables debug prints; off by default.

## 2026-11-06 — Luna review and corrections (supersedes November 5)

Handoff: [WORK_ORDER.md](WORK_ORDER.md), pointing to
[TASK3_REVIEW_WORK_ORDER.md](TASK3_REVIEW_WORK_ORDER.md). Both are Astra-owned
instructions, not Luna changes. The complete user-supplied pasted Task 3
instructions were read. This section records new evidence independently of
the historical claims above.

### Changes and regression findings

- Speed 40 caps the command on its first detected frame, however distant.
  The cap survives sign loss. Release requires a distinct encounter: prior near
  approach, sustained absence with commanded travel, then consecutive detections
  of a farther sign. A same-size/near sign reacquired after flicker cannot release
  it. An unconfirmed exit keeps the cap, including parking; a confirmed exit
  releases it. No second Speed 40 encounter was detected in the rehearsals.
- Hospital hold starts only after two still image comparisons and resets on
  movement or missing images. The timeout-based rest fallback is removed. Its
  pickup approach constants are unchanged: 0.565 m sign range, 0.013 m coast,
  1.5-frame lag, and arming only after a sign is seen beyond 0.75 m. These are
  calibrated scene/camera assumptions; a first detection too close can miss the
  stop. Visual stillness is an observation, not a wheel-speed measurement.
- Parking requires Hospital completion and route progress, an unresolved-obstacle
  check, and three consecutive valid ArUco ID 1 entry poses. When the exit sign
  cannot be confirmed, route progress uses a near School approach and subsequent
  disappearance/travel after Hospital and Speed 40 entry, followed by the target
  marker at the existing entry pose gate. School never causes a halt. This
  camera-observed sequence fixes the initial strict-exit-gate timeout without a
  fixed obstacle count, layout coordinate, or elapsed-lap timer.
- Obstacle encounter clearance uses near-image evidence, disappearance, and
  commanded travel. Far red building trim detected by the existing 2B detector
  does not block parking. The field `obstacles_passed` and harness field `passed`
  count cleared visual encounters, **not unique physical obstacles**: Hard traces
  show four despite three physical obstacles, and Easy can show a false encounter.
  These counters never enforce a fixed count or certify all obstacles were passed.
- Parking success requires a finite valid pose within 0.015 m forward error,
  0.025 m lateral error, and 5 degrees heading error, plus at least three stable
  zero-command visual comparisons spanning 0.5 simulation seconds. Movement,
  missing markers/images, or invalid PnP resets the evidence. Fresh usable visual
  yaw evidence is required; the zero-initialized yaw prior alone cannot certify
  alignment. The estimator/handover still assumes a locally near-parallel
  approach; arbitrary initial heading is not validated.
- Marker loss commands zero immediately; allowed blind motion is zero. Command
  integration cannot establish success and records the actual command after
  mission/zone/frame-rate caps. Malformed/empty/nonfinite/behind-camera PnP results
  reject parking motion. Wheel commands are finite and bounded. Path derivatives
  explicitly return zero outside the active interval. Inspection found the old
  quintic already evaluated derivatives at clipped `r`, so a nonzero extrapolated
  baseline curvature defect was not reproduced; the new guard makes it explicit.
- Medium exposed an outer-path/controller conflict: the quintic demanded about
  55 degrees, while the fixed heading guard opposed turns beyond 37 degrees.
  At that checkpoint the planned-heading allowance covered only the outer merge;
  it was later generalized to both paths. The marker-bearing guard, merge corridor
  and steering limits remain. A second issue was failing immediately
  at the front of the valid forward window. A slow correction (at most 0.25 rad/s)
  now uses direct heading/lateral errors inside that window only when remaining
  steering distance and lateral clearance support it. This avoids the old
  terminal heading cancellation (`4 - 30*0.12 = 0.4` effective small-angle gain).
  Unsafe correction or overshoot fails and stops. Success tolerances are unchanged.
- Missing/malformed images command zero; runtime/connection failures return
  nonzero and attempt to stop both motors independently. Pause and pre-pause
  states command zero and reset observation holds; resume/start intermediate
  states are accepted, and stopping states exit. The solution never starts or
  stops simulation. State handling was checked against the
  [official state documentation](https://manual.coppeliarobotics.com/en/apiConstants.htm#simulationstate);
  PnP result handling against the
  [OpenCV interface](https://docs.opencv.org/4.12.0/d9/d0c/group__calib3d.html).

### Deterministic checks

Interpreter checked before execution: `/Users/aryanachary/.venv/bin/python`,
Python 3.10.20, OpenCV 5.0.0 (ArUco available), NumPy 2.2.6 and ZMQ client installed.
No simulator was accessed until Astra explicitly handed over ownership.

The saved HEAD baseline `/private/tmp/task3_review_baseline.py` failed all 11
focused defect checks (10 failures, one empty-PnP error); full traces and method
names are in `baseline-focused.out` in the evidence directory below. The original
34-method broad baseline run also reproduced malformed-pose/corner, missing-image,
pause, and failure-exit problems. Tests using newly added helper methods were not
treated as evidence of baseline defects by themselves.

Final regression helper: **38 tests pass**, including sign first sight/release/
flicker, Hospital movement reset, School progress with retained zone cap, pending
obstacles, marker streak reset, aligned/misaligned/overshot parking, bounded terminal
correction, outer heading-reference conflict, marker loss, actual capped command
history, PnP edge cases, invalid images, runtime failure, pause/resume, finite
Ackermann outputs, import restrictions and a simulator API allowlist.

Commands/checks:

```text
/Users/aryanachary/.venv/bin/python orchestration/check_task3.py
/Users/aryanachary/.venv/bin/python -c "from pathlib import Path; [compile(Path(p).read_text(), p, 'exec') for p in ['task3/task3.py', 'orchestration/check_task3.py']]"
git diff --check -- task3/task3.py orchestration/check_task3.py orchestration/TASK3_RESULTS.md
```

The regression log is `regression-final.out`. The untracked helper was also checked
directly for trailing whitespace/newline; scoped tracked diff checks are clean.
The global CSV diff has pre-existing Task 2 CRLF noise and was not rewritten.
Self-review covered the full source diff, every return/state transition, finite
actuator bounds, single-file imports, absent privileged pose/speed APIs and
simulation/scene mutation APIs, and preservation of unrelated changes.

### Clean-scene simulator evidence

DEV-only harness and all images/logs/raw traces are preserved at
`/private/tmp/task3-review.5AMtFI/`. `rehearse.py` loads scenes extracted with
`git archive HEAD ... | tar -x -C /private/tmp/task3-review.5AMtFI`, runs one controller
at a time, logs camera-only controller state to `camera-state.jsonl`, raw truth
to `truth.csv`, terminal output to `controller.out`, and event/periodic PNGs.
Privileged reads and simulation start/stop exist only in that temporary harness,
never in `task3.py` or the regression helper. No scene was saved.

Final solution SHA256: `c6bd5aefbfad5eec4d8893ecf185795e256ff0339aeaa2c9d3ad7ab406303f8c`.
An exact copy is `tested-task3-final.py` in the evidence directory. Medium3/4,
Hard4/5 and Easy2 used this exact source. Earlier Hard2/3 and Easy1 used
`15bee11c3debe678e09c9a149ab1b9f05c9d7c5001de71052deeab9997d0b1a7`;
Medium2 used `7648087d61021e940bb73553c145978a216bc9f15b2c031ca0e7ed56dfae4c2d`.

| Run | Result / simulation time | Final marker forward / lateral / heading |
|---|---|---|
| Hard1, initial review patch | Timed out at 300 s; strict exit-sign gate blocked parking | No parking commitment; failure frames retained |
| Hard2, School progress gate | Parked 244.50 s, exit 0 | 0.21271 m / +0.00081 m / -1.59 deg |
| Hard3, repeat | Parked 246.30 s, exit 0 | 0.21389 m / -0.00086 m / -0.44 deg |
| Easy1, before outer correction | Parked 231.50 s, exit 0 | 0.21397 m / +0.00110 m / -3.39 deg |
| Medium1, before outer correction | Stopped/failure 271.70 s, exit 1 | 0.21470 m / +0.01634 m / -23.89 deg |
| Medium2, outer heading guard only | Stopped/failure 273.05 s, exit 1 | 0.21481 m / +0.00337 m / -10.91 deg |
| Medium3, final correction | Parked 286.55 s, exit 0 | 0.18589 m / +0.01495 m / -4.30 deg |
| Medium4, final repeat | Parked 283.05 s, exit 0 | 0.18744 m / +0.01406 m / -4.02 deg |
| Hard4, final regression | Parked 243.65 s, exit 0 | 0.21259 m / -0.00021 m / -1.44 deg |
| Hard5, final repeat | Parked 246.20 s, exit 0 | 0.21280 m / -0.00080 m / -2.51 deg |
| Easy2, final regression | Parked 232.85 s, exit 0 | 0.21259 m / -0.00004 m / -1.39 deg |

The 300-second Hard1 harness stop produced controller exit 0 on simulator stop;
that is **not** a completion claim (`finished` remained false). Later successes
require `finished=true` in the camera log as well as zero commands and normal exit.

Final-source Hospital visual holds: Medium3 36.30–42.20 s (5.90 s), Hard4
28.30–34.15 s (5.85 s), Hard5 28.35–34.20 s (5.85 s). Independently sampled raw
truth within the holds spans 5.35 s for Medium3 and 5.05 s for Hard4 with both
commands zero; coordinate peak-to-peak motion was respectively below 8 micrometres
and 9 micrometres. This does not certify the pickup area's scoring boundaries.
Raw final world positions: Medium3 (-0.15558, -0.74788) m; Hard4
(-0.13083, -0.73193) m. Both have zero sampled displacement in the final half-second.
Marker-relative errors above come from images; no guessed world parking/pickup
coordinates were used for scoring. All completed runs command at most 1.19 rad/s
after their observed Speed 40 entry and below 2.90 rad/s globally. This checks
observed-command history, not a separately verified evaluator zone boundary.

### Limitations and preservation

- Missed second Speed 40 detection remains a perception limitation. The cap is
  retained deliberately; no claim of visually confirmed zone exit is made.
- Existing permissive blue template cutoffs (Parking 0.045, Hospital 0.075) produce
  many false positives on blue objects in live frames. These thresholds were not
  broadly retuned. Route fallback relies on School plus ArUco, not blue P alone.
- Obstacle pass evidence is imperfect under occlusion, false detections or wheel
  slip. No unique-object proof, collision/off-road count or evaluator score is
  claimed from the raw harness. The old monitor's guessed zone and pickup/parking
  coordinates were not used to certify safety or marks.
- Runs exceed 180 simulation seconds and therefore incur time penalties under
  the supplied rules. Medium's final correction has little remaining forward
  margin; two successful repeats do not establish general robustness.
- Official grading was not run: `file` identifies Linux x86-64 ELF and Windows
  x86-64 PE tools, unavailable natively on this Mac. No encrypted recording,
  submission package, portal submission or score claim was made. Astra owns
  the final diff/evidence review and external requirements.

Workspace scene hashes are preserved (including the pre-existing dirty Hard):

```text
Hard   b7d6c0c164efce53aba6e8e7b9c79e6cedc3a0fd9c529aad533f693cc22d90fe
Easy   8080cb766fcde80525807a07a488ed2ea133c41f495cc68e419e8392bd7f7826
Medium a33be535dae9f463adfe538d168660eb7d8dad6a99010a2368996eb102aed7e3
```

Task 2 CSV/scene changes were left untouched. Luna changed only `task3/task3.py`,
added `orchestration/check_task3.py`, and added the historical notice and this
review section to `orchestration/TASK3_RESULTS.md`; temporary evidence stays
outside submission files.

Final handoff: Astra reviewed the exact `c6bd5aef...` source diff, the 38-test log,
Hard4/5 and Medium3 evidence, and unchanged scene hashes, and requested no further
code corrections. Medium4 and Easy2 subsequently completed on the same source.
The simulator was left stopped with the original workspace
`/Users/aryanachary/eYRC_26-27_Niti-Vahan/task3/Task_3_Hard.ttt` reloaded, without saving.

### November 8 narrow closeout

Current `task3/task3.py` SHA256: `127a307e79c8505f6b5d380ad6613093927afaef1d9e8c38d3e140c3cbca3b17`.
The saved `hard-final-2`, `hard-final-4`, and `medium-final-1` evidence each
records this exact source hash. Terminal camera state reports `finished=true`,
`failed=false`, and `[0.0, 0.0]` commands:

| Run | Time | Terminal marker forward / lateral / heading |
|---|---:|---|
| Hard final 2 | 245.90 s | 0.20916 m / +0.00501 m / -0.69 deg |
| Hard final 4 | 245.65 s | 0.21141 m / +0.00205 m / -0.84 deg |
| Medium final 1 | 278.90 s | 0.19956 m / +0.01985 m / -4.44 deg |

The terminal `forward`/`lateral`/`heading` values above are the controller's
camera-derived marker pose, not ground-truth position. Existing regressions
cover true quadrilateral blue-sign rectification, stronger interior-glyph
classification and real positive/negative crops (including absent reference
images), bounded late Hospital arming, the spawn-without-false-halt regression,
and increased terminal-parking heading gain. The previously recorded 42-test
regression run passed.

The second Speed 40 remains undetected. Saved frames show the oblique,
overlapping blue/red sign without reliable visual exit confirmation, so the
speed cap remains in force. No claim is made that the remaining second-Speed40
miss or its time penalty is solved. Earlier `hard-final-1` failed at the
wrong Hospital spawn and `hard-final-3` was incomplete; neither is counted as a
successful run. No new Easy rehearsal was attempted: process inspection failed
with `pgrep: Cannot get process list`, so simulator availability and exclusive
ownership could not be confirmed safely. Official grading was not run, and
these simulator results are not an official score.

### November 9 focused exit detector follow-up (not live validated)

Starting source was preserved at
`/private/tmp/task3-followup.ZNTHv6/task3-before-focused-implementation.py`
with the baseline SHA256 above. The saved native PNG scan covered all 424
captured frames for ordinary Speed 40 detections and found only the first sign
(first seen at 47.70 s, estimated range 0.73 m); no sparse-timestamp
`Mission.step()` replay was used. The accompanying `camera-state.jsonl` records
the per-frame commands and `frame_dt`. It shows the 130.40–134.65 s board
sequence while the vehicle remains capped at 1.19 rad/s. The weak-board detector
recognizes eight native frames in that sequence; current image-range estimates
move from 0.63 m to 0.50 m. The 92–98 s School red feature has no internal blue
board evidence, and the 203 s red-only Parking feature is rejected.

`task3.py` now groups red fragments inside a white board hull and requires
internal blue, white and red evidence in separated upper/lower regions. These
weak candidates are considered only after the ordinary Speed 40 tracker is
rearmed, and require three consecutive spatially consistent board observations
before entering the existing distinct-sign tracker. Missing, multiple, distant
or invalid observations reset that weak track. The regular Speed 40 detector
still uses its original two-frame confirmation. The focused offline suite has
44 passing tests, including board evidence and alternating-board rejection;
compile and scoped whitespace checks pass.

The exact `camera-state.jsonl` detections, commands and per-frame timestamps
were replayed through the ordinary Speed 40 tracker (without calling
`Mission.step()` on sparse captures). It records the first sign reaching an
estimated 0.294 m range and tracker rearm at 89.8 s after 0.103 m commanded
travel and the required absence. Thus the near-passed/rearmed gate is supported
by the full state history. The weak-board candidate's sampled estimated range
at three-frame confirmation is about 0.607 m, over 0.15 m beyond the stored
nearest range, so the original distinct-range requirement is retained
unchanged. Sparse PNG timestamps were not treated as a faithful full mission
replay or proof of consecutive live frames.

A CoppeliaSim process was already present, and the bounded API state query did
not return; no harness/controller was started and no simulator run or
180-second result is claimed. Live validation must confirm consecutive-frame
weak tracking, correct release, and safe completion. Parking speed scheduling
and acceptance tolerances were not changed.

Focused source SHA256 after this offline-only detector change:
`9db627e54ce6275549ef48a629266d19f17f845f72c9e707bbb2de6b9e20a58c`.

### November 10 verification closeout

The working controller was restored byte-for-byte from
`/private/tmp/task3-followup.ZNTHv6/exit-live-1/source.py`, SHA256
`9db627e54ce6275549ef48a629266d19f17f845f72c9e707bbb2de6b9e20a58c`.
The alternative `315dec64...` added only an early parking branch that skips
sign and obstacle scans. Its Hard run 7 parked at 199.25 s, but run 8 failed
parking alignment at 209.50 s (camera-derived pose forward 0.20760 m, lateral
+0.02265 m, heading -0.18206 rad). That candidate was rolled back.

Saved live runs, with final poses from the controller's marker-based camera
estimate (forward / lateral / heading):

| Run/source | Result | Time | Final pose (m / m / rad) |
|---|---|---:|---|
| Hard exit-live-1, 9db | Parked | 202.10 s | 0.21071 / -0.00010 / -0.02392 |
| Hard exit-live-2, fe4ec8 | Parking alignment failed | 178.15 s | 0.19086 / -0.04695 / -0.09683 |
| Hard exit-live-3, ba7b28 | Parking alignment failed | 202.95 s | 0.21217 / +0.05932 / -0.09922 |
| Hard exit-live-4, 64362c | Parked | 207.40 s | 0.21257 / +0.00228 / -0.02311 |
| Hard exit-live-5, 9db | Parked | 200.15 s | 0.21023 / +0.00117 / +0.00246 |
| Hard exit-live-6, 9db | Parked | 200.55 s | 0.21071 / +0.00059 / -0.00595 |
| Hard exit-live-7, 315dec | Parked | 199.25 s | 0.21173 / +0.00166 / -0.00379 |
| Hard exit-live-8, 315dec | Parking alignment failed | 209.50 s | 0.20760 / +0.02265 / -0.18206 |
| Easy exit-live-easy-final, 9db | Parked | 233.50 s | 0.20805 / +0.00457 / -0.01240 |
| Medium exit-live-medium-final, 9db | Parking alignment failed | 278.10 s | 0.19207 / +0.02741 / -0.07785 |
| Medium exit-live-medium-repeat, 9db | Parked | 282.75 s | 0.18936 / +0.02284 / -0.07247 |

The 9db Hard runs recorded the second Speed 40 zone ending at 130.40–131.70 s.
Successful Hard 9db completions were 20.15–22.10 s beyond the 180 s target;
the target was not met. Medium parking remains intermittent across the saved
pair. No new simulator run was started for this closeout.

Offline yaw diagnosis used saved marker corners, not simulator Euler angles.
At exit-live-1 parking entry (163.05 s), raw PnP yaw was -0.564 rad while the
estimator began at zero and rejected the observation under its 15-degree gate.
That run later parked successfully. At exit-live-8 entry (163.50 s), raw PnP
yaw was -0.036 rad and was accepted. At its failure frame (209.50 s), raw PnP
yaw was +0.202 rad and the estimator's internal heading was +0.182 rad, a
0.020 rad difference. The initial-yaw gate can reject a large entry observation,
but these samples do not establish it as the cause of intermittent parking:
the successful run had the larger entry mismatch, and the failure estimate
tracked the raw observation closely. No yaw initialization change is justified
by this evidence; projected-pose validation was therefore not undertaken.

Verification on the restored 9db source: the checker now contains 45 tests,
which passed. The single removed test required the early parking perception-skip
branch from the rolled-back 315dec candidate; existing behavioral zone-cap
tests remain. Python compilation and scoped `git diff --check` passed. These are
simulator/harness observations only; official grading and collision
certification were not run.

### November 10 — focused parking guard and speed follow-up

The live parking traces showed that the fixed 0.55 rad marker-bearing guard
sometimes commanded steering against the path even while the marker had ample
image margin. In the failed Medium trace it opposed the path command 42 times;
checked frames had at least 77 px marker margin. A direct-pose bicycle comparison
from saved Medium and Hard entry poses compared the original path, a consistent
rear-axle path reference, and a 0.65 rad bearing guard. Rear-reference geometry
changed simulated parking time by at most 0.45 s and did not materially improve
pose. The 0.65 guard reduced simulated Medium time by about 2 s and improved its
final lateral/heading errors; projected marker margin stayed at least 60 px. The
focused live checkpoint therefore changes only the bearing guard to 0.65 rad.
It preserves the 1.19 rad/s parking cap, all stop/pose limits, marker-loss stop,
and the exit-detection logic.

Five simulator rehearsals using clean scenes on exact source SHA256
`c716926a88b8e58b27cd6c326ac6c58aa16b62cea0d0faff6be340c6bf0b3806` completed:

| Arena/run | Result time | Final camera-derived forward / lateral / heading |
|---|---:|---|
| Medium `medium-065-1` | Parked 284.30 s | 0.19922 m / +0.01714 m / -4.26 deg |
| Medium `medium-065-2` | Parked 279.75 s | 0.20797 m / +0.00891 m / -3.21 deg |
| Hard `hard-065-1` | Parked 200.60 s | 0.21171 m / -0.00142 m / +0.60 deg |
| Hard `hard-065-2` | Parked 205.00 s | 0.21160 m / +0.00042 m / +0.02 deg |
| Easy `easy-065-1` | Parked 234.30 s | 0.20871 m / +0.00219 m / -0.84 deg |

The timing target is still missed: Hard is about 21–25 s over 180 s and Medium
is about 100 s over. No time-penalty-free claim is supported. The second Speed
40 sign was confirmed in both Hard runs (at 131.15 s and 131.10 s). It was not
reliably confirmed in Easy or Medium, so the 1.19 rad/s cap remained active in
those runs.

A measured fast-parking trial raised the nominal parking cap to 2.95 rad/s while
retaining the original high-steering slowdown (speed <=0.65 rad/s above 80% of
the steering limit). In `hard-fast-1` it cut parking time from 37.35 s to 22.50 s,
but at 185.90 s the strict target check stopped the vehicle at forward 0.21341 m,
lateral +0.12805 m and heading -29.52 deg. Across its 84 parking updates,
commanded travel averaged 8.2 mm/frame and exceeded the estimator's 10 mm
integration cap in 30 frames. Raising that cap to the existing 25 mm/frame
motion-safety bound did not resolve tracking: `hard-fast-ds025-1` stopped at
182.25 s with forward 0.21419 m, lateral +0.22414 m and heading -37.24 deg.
Both failed trials are retained in `/private/tmp/task3-followup.ZNTHv6/`; neither
fast variant is in the submission source. This shows that higher speed saves
parking time but loses lateral/heading tracking under the observed camera update
lag; the travel-cap increase alone is insufficient. No additional speed tuning
was applied after this result.

The final working source is restored to the tested `c716926a...` checkpoint.
`/Users/aryanachary/.venv/bin/python orchestration/check_task3.py` passed all 45
checks on the final source; `py_compile` and scoped `git diff --check` also pass.
These simulator rehearsals used clean scenes and are local macOS CoppeliaSim
checks, not official evaluator runs. Collision/off-road penalties and official
score remain unverified. Raw traces,
source copies and per-run logs are in `/private/tmp/task3-followup.ZNTHv6/`.

### November 10 — consecutive-yaw recovery checkpoint

The c716 source was preserved before edits at
`/private/tmp/task3-followup.ZNTHv6/task3-c716-checkpoint.py` (SHA256
`c716926a88b8e58b27cd6c326ac6c58aa16b62cea0d0faff6be340c6bf0b3806`). The
observer now requires three consecutive clear, temporally consistent yaw
observations before recovering an estimate outside the existing 15-degree gate.
Frame-to-frame consistency uses a physical yaw-rate bound derived from the
vehicle speed and steering limit plus a 2-degree noise allowance. Missing,
ambiguous, malformed, nonfinite, or nonconvex observations reset recovery;
nonpositive and >0.75 s timestamp gaps also reset it. The existing ambiguity
ratio, marker-loss stop, and strict parking success checks are unchanged.

The regression suite now passes **50 tests** (45 previously existing plus five
focused observer cases), including 20- and 35-degree sustained drift, one
discordant observation, ambiguity, invalid/missing frames, and timestamp-gap
resets. Source and test files compile; scoped `git diff --check` passes. Current
Task 3 source SHA256: `891a82771ff7140b6b218bde9e6737975ba99cc9259c2db6c1f073dd980c5c3f`.

An offline replay processed all 40 saved parking PNGs from `hard-fast-1`; 37
frames supplied clear same-frame PnP yaw. Compared with those repeated visual
observations (not treated as absolute ground truth), median disagreement fell
from 11.46 to 8.28 degrees and maximum from 44.75 to 36.56 degrees. At 180.70 s,
the preserved estimator disagreed by 22.92 degrees while the updated estimator
disagreed by 9.57 degrees and accepted the recovered heading. PNG timestamps
matched the nearest JSONL row to 0.001 s. This is a saved-frame observer replay,
not a trajectory or simulator result. Full per-frame evidence is in
`/private/tmp/task3-followup.ZNTHv6/yaw-replay-checkpoint.txt`.

The first API timeout used the default sandbox; loopback isolation was a plausible
explanation, not a proven cause. An elevated bounded probe later succeeded and
reported stopped state `0` at sim time `0.0`. A subsequent elevated probe also
timed out with send/receive timeouts set before `getObject`, confirming that the
then-current CoppeliaSim process was unresponsive. After a no-save restart, an
elevated bounded probe succeeded again. The isolated clean Hard scene used by the
harness had the same SHA256 as committed `HEAD:task3/Task_3_Hard.ttt`
(`8082c50a967a548bf9b7ea82e718ada6f4a41cae84ebb4f340d64c9238972f75`).

Safe-speed live run `yaw-recovery-hard-safe-1` used exact source SHA256
`891a82771ff7140b6b218bde9e6737975ba99cc9259c2db6c1f073dd980c5c3f` and
completed with `finished=true`, `failed=false`, parked at 200.10 s (harness
stopped at 201.10 s). Parking began at 163.85 s, took 36.25 s, and ended at
forward 0.20922 m, lateral +0.00199 m, heading -0.47 degrees with fresh yaw
observed. The run logged a 5.90 s Hospital hold, Speed 40 entry at 48.00 s and
exit at 131.25 s, and both obstacle-triggered lane changes. Maximum commanded
speed was 2.900 rad/s globally and 1.190 rad/s while the zone flag was active;
all 760 command rows are retained in `/private/tmp/task3-followup.ZNTHv6/yaw-recovery-hard-safe-1/`.
This is local harness evidence, not official scoring or collision/off-road
certification. A speed-control candidate is being evaluated next; this exact
safe source and run remain preserved as the rollback baseline.

### November 11 — lag-aware speed trial and final-pose diagnosis

The candidate with adaptive speed, current-frame raw range geometry, lag-aware
braking and bearing visibility cap used source SHA256
`0ae5b6aafd46449e5e6d3927f667167d9b6c9f13b901b95587673eb9b62afb26` in
`yaw-recovery-hard-lag-aware-1/`. On the committed clean Hard scene it began
parking at 163.70 s and stopped with controller exit 1 at 192.55 s after the
strict target check failed. Final camera pose was forward `0.21444 m`, lateral
`+0.02859 m`, heading `-5.895 deg`; lateral and heading were outside their
existing 0.025 m / 5 degree limits. It was not parked and did not meet 180 s.
Commands stayed at or below 2.900 rad/s globally and 1.190 rad/s in the zone.

The final five saved marker frames are timestamp matched to JSONL within the
reported 0.001 s precision. Raw PnP yaw / estimated internal yaw / residual were:
190.50 s `-5.50 / -1.16 / -4.34 deg`; 191.00 s `-7.21 / +4.17 / -11.38 deg`;
191.50 s `-4.01 / +6.63 / -10.64 deg`; 192.00 s `-2.12 / +6.65 / -8.77 deg`;
192.55 s `-2.30 / +5.90 / -8.20 deg`. All five PnP yaws were clear. Over these
frames lateral moved `+0.0251, +0.0454, +0.0431, +0.0383, +0.0286 m` while the
estimate reported heading `-1.16, +4.17, +6.63, +6.65, +5.90 deg` (pose heading
is the negative of the estimator's internal yaw). The clear-yaw residual
remained within the 15-degree gate, so the fixed 0.12 normal blend responded
too slowly; path tracking also left 2.9 cm lateral error at the strict stop.
These visual comparisons diagnose observer bias and tracking; raw PnP is not
treated as absolute ground truth. Per-frame details and the failed trace remain
in `/private/tmp/task3-followup.ZNTHv6/yaw-recovery-hard-lag-aware-1/`.

The first adaptive candidate was interrupted before the harness printed its
scene-loaded/controller-start message; its PID disappeared during identity
recheck and no KILL was sent. Its attempted source/hash and status are retained
in `yaw-recovery-hard-adaptive-1/`; it is not counted as a run.

### November 11 — time-aware normal yaw fusion checkpoint

After preserving the failed lag-aware source and its five-frame comparison,
normal clear-yaw fusion now uses `alpha = 1 - exp(-dt / 0.20 s)`. This responds
to small in-gate bias on simulation time while retaining the existing 15-degree
gate, three-clear-observation recovery for larger residuals, temporal
consistency bound, and ambiguity/missing-frame resets. The speed controller,
braking, bearing visibility cap, current-frame raw range pose, and range-filter
odometry are restored unchanged from the failed lag-aware trial so the next
Hard run isolates this normal-fusion change.

Regression suite: **53 tests passed**, including the prior recovery/outlier,
ambiguity, invalid-frame, timestamp-gap, strict parking and speed-bound checks,
plus convergence of an 8-degree clear-yaw bias at 0.1 s, 0.25 s, and mixed
0.3/0.4 s frame intervals. Both Python files compile and scoped `git diff
--check` passes. Candidate source SHA256:
`f3944574f9637c9da31f4c0a2dbbdf7c7d500ba4792a6ad1c334f699f10fce73`.
One fresh Hard harness result is pending; no parking or timing claim is made
from the synthetic regression.

### November 11 — time-aware fusion Hard result and parking fast-path candidate

The `yaw-recovery-hard-fusion-1` run used source SHA256
`f3944574f9637c9da31f4c0a2dbbdf7c7d500ba4792a6ad1c334f699f10fce73` on the
isolated committed Hard scene (scene SHA256
`8082c50a967a548bf9b7ea82e718ada6f4a41cae84ebb4f340d64c9238972f75`). The
harness completed with `finished=true`, `failed=false`, and parked at 186.00 s.
Parking began at 163.90 s and took 22.10 s. Final camera pose was forward
0.20720 m, lateral -0.00420 m, heading -3.37 degrees, with fresh yaw observed;
strict parking bounds passed. The last five clear PnP yaw / estimated internal
yaw / residual samples were: 183.60 s `-7.05 / -2.21 / -4.83 deg`; 184.20 s
`-2.51 / -2.24 / -0.27`; 184.80 s `+1.88 / +0.97 / +0.90`; 185.40 s
`+3.37 / +3.49 / -0.13`; 186.00 s `+3.37 / +3.37 / -0.01`. Maximum command
was 2.90 rad/s overall and 1.19 rad/s in the active zone. Frame interval p50/p90/
max was 0.217/0.353/0.440 s overall and 0.224/0.283/0.319 s while parking.
Parking commands had p10/median/p90 0.476/1.71/2.90 rad/s (20 of 97 at or below
0.65; 39 of 97 at or below 1.19). These observed low speed intervals and
braking/tracking caps are candidates for profiling; the trace does not establish
which cap was the dominant cause of the remaining six seconds.

A focused candidate now bypasses route perception after parking starts and the
Speed 40 zone is inactive. Invalid-frame handling remains in `Mission.step`,
and sign detection remains enabled while the zone is active so its exit can be
recognized. The speed caps are unchanged for this isolation trial. The
regression suite passes 55 tests, including both bypass and active-zone cases.
A fresh Hard live result for this candidate is pending.

### November 11 — perception-skip and legal-headroom Hard runs

The perception-skip candidate (source SHA256
`4d92528a377917ee912c3f82f1b46c2820a5834ee421095ae5db0618a8d68cc8`) completed
Hard with `finished=true`, `failed=false`, parked at 182.15 s. Final pose was
forward 0.20923 m, lateral -0.00241 m, heading -2.66 degrees, with fresh yaw
observed. Parking started at 163.55 s and took 18.60 s. With unchanged caps
2.90/1.19 rad/s, parking frame interval p50/p90/max was 0.175/0.205/0.271 s;
command median was 2.215 rad/s. This was 3.85 s faster than the 186.00 s fusion
run, though still above 180 s.

The following headroom candidate used 2.95 rad/s global cruise (0.05 below the
3.0 task limit), 1.20 rad/s in the zone (the task cap), and a 5.25 s Hospital
hold. It completed and parked at 183.35 s, with final pose forward 0.20885 m,
lateral +0.00394 m, heading -4.51 degrees; parking began at 161.70 s from
lateral +0.25647 m and forward 0.85070 m and took 21.65 s. The different route
and parking handoff mean this run does not establish a timing regression from
the headroom changes. Independent `truth.csv` positions show the car stationary
from 28.35 to 33.70 s (5.35 s): net displacement 0.000011 m and maximum sampled
position step 0.000015 m before the controller reported departure at 33.70 s.
The controller used the 5.25 s source threshold; this evidence supports that
reduction with 0.25 s added hold beyond the five-second requirement.

An offline arithmetic replay of the saved headroom pose trace identified the
pre-tracking limiting cap for 110 timed parking samples: yaw 7.20 s/41 samples,
maximum speed 5.45 s/31, visibility 3.70 s/18, braking 2.90 s/17, and frame
interval 1.50 s/3. The tracking factor was below 0.8 for 5.85 s and below 0.6
for 2.30 s. Median tracking factor was 0.974. This replays estimated poses and
is diagnostic, not an independent trajectory. Full calculations are in
`/private/tmp/task3-followup.ZNTHv6/parking-cap-breakdown.txt`.

A separate replay of the same trace confirmed the inner-start planned heading
reached 42.70 degrees while the fixed 0.65 rad heading guard opposed the desired
heading correction in four samples. Saved marker detections were present in
38/38 parking images; minimum horizontal image margin was 12 px and the 10th
percentile was 24.7 px. The heading guard now follows
`max(0.65 rad, abs(planned_heading))` on both path types. The independent marker
bearing steering guard and visibility speed cap remain in force. Added tests
cover the inner planned turn and retained marker-bearing guard; 57 tests passed
at that checkpoint.

### November 11 — handoff-based parking path and yaw-cap comparison

The inner merge now starts its quintic at each run's measured parking hand-off
forward distance, as the outer merge already did. For the preserved headroom
run's 0.85070 m / +0.25647 m hand-off, this gives a 0.59070 m span instead of
the fixed 0.52000 m span. The analytic peak planned heading falls from 42.76 to
39.15 degrees; at 0.78 m the path has shifted laterally only 3.65 mm. Peak path
curvature falls from 4.69 to 3.73 m^-1. Regression tests verify the hand-off
boundary, the early lateral shift, reduced curvature, and heading guard behavior.

One clean Hard run with that path, the generalized planned-heading guard, 2.95 /
1.20 speed caps, 5.25 s hold, and the retained 0.30 rad/s yaw cap completed at
182.15 s. Parking began at 160.95 s and took 21.20 s. Final pose was forward
0.20898 m, lateral -0.00225 m, heading -1.19 degrees, with fresh yaw observed.
The marker was detected in 38/38 saved parking frames; measured horizontal
image-edge margin was at least 22 px (10th percentile 69.9 px). Parking command
median was 1.666 rad/s. The isolated scene hash remained the committed Hard hash.

Projection replay of the earlier fixed-start trace tested both signs of a camera
yaw transform. Source convention gives physical positive-left yaw an inverse
scene rotation in camera coordinates (the sign that predicted clipping), but the
counterfactual assumes the vehicle exactly follows the reference-heading delta.
The live handoff-based Hard run did not clip and measured a 22 px minimum margin;
the saved-frame projection is therefore labeled **inconclusive**, not used as a
safety claim. Details are in
`/private/tmp/task3-followup.ZNTHv6/merge-projected-marker-diagnosis.txt`.

The bounded 0.38 rad/s yaw-cap trial used the same path and other caps. It also
parked, but at 187.25 s after a 25.85 s parking phase. Its offline replay showed
tracking factor below 0.8 for 13.15 s and below 0.6 for 11.25 s, versus 6.70 s
and 3.55 s on the 0.30 run; visibility cap time rose from 5.20 to 9.05 s. This
candidate is rejected and the source cap is restored to 0.30 rad/s. The 0.38
cap was below the 0.425 rad/s kinematic bound, but the live trace shows worse
tracking/visibility behavior. Both run traces remain preserved.

### November 11 — rear-axle pure-pursuit paired model diagnostics

The reviewed paired runner starts from the first parking pose in
`/private/tmp/task3-followup.ZNTHv6/yaw-recovery-hard-merge-repeat-1/camera-state.jsonl`:
centre-forward 0.878746 m, front-lateral +0.261546 m, heading 0 degrees. Its
rear start is forward 0.938746 m / lateral +0.261546 m, asserted above 0.7 m.
The path anchor is frozen at that initial rear pose. The candidate shifts the
merge endpoint by half-wheelbase, and its target continues on the virtual
straight past the endpoint. It changes only path-coordinate and steering
calculations in a temporary source variant; adaptive speed, strict stopping,
marker-loss handling, and Parker bookkeeping stay source-identical. The model
adds one-observation lag to both speed and steering, exact constant-curvature
arcs, range noise at 0.5% of forward distance, lateral noise 2.5 mm, heading
noise 1 degree, and a camera-bearing visibility stop. This lag and noise are
model assumptions, not measured simulator actuator behavior. Visibility margin
is reported as `47.5 deg - abs(bearing)` (center-only angular margin; it does
not certify the full marker image margin). Every parked outcome asserts truth
centre-forward, front-lateral, and heading against the strict parking bounds.

The 12 paired cases (three starts × two observed interval profiles × two noise
seeds) all parked within truth bounds under both controllers. Per-pair times
were identical to 0.01 s resolution and ranged from 13.68 to 22.63 s. The
observed interval profiles were 0.151–0.209 s and 0.210–0.280 s. The minimum
center-bearing margins ranged 7.48–15.87 degrees for feedback and 8.20–17.20
degrees for pure pursuit. On 106 identical camera-pose inputs from the saved
trace, mean/max absolute steering differences were 0.177281 / 0.934947 rad;
speed differences were 0.127451 / 0.854903 rad/s. The modules have distinct
Parker classes and global namespaces. Across matched paired trajectories,
rear-position RMS difference averaged 5.032 mm (maximum per-pair RMS 9.565 mm);
maximum pointwise separation averaged 8.435 mm and reached 16.605 mm. Thus the
candidate was exercised, but did not reduce model parking time. It was not
applied to `task3.py`.

Full case table and command-difference output:
`/private/tmp/task3-followup.ZNTHv6/paired_tracking_reviewed.stdout`. Runner:
`/private/tmp/task3-followup.ZNTHv6/paired_tracking_reviewed.py`. The unchanged
source hash is `0fe1e318cc37b359d04847b8a397079c4d1c3350be8cf0e8a8958470b6d92ff8`.
The existing Task 3 regression suite passes all 58 tests.

A live validation attempt invoked the harness's controller-only mode against a
stopped simulator, so Task 3 correctly reported that simulation never started;
there were zero camera/truth frames and no run result. The bounded API health
check then returned stopped state 0 at sim time 185.50 s. No new baseline was
launched. Existing same-hash Hard evidence remains the prior 182.15 s and the
preserved 184.20 s run in `yaw-recovery-hard-merge-repeat-1/`.

### November 12 — bend patch and marker-edge failure review

Current bend-patch source `362315dcf77d778323d090dc40088382da29820a93f2a84e7591fad209020975`
completed a full Hard harness attempt, but did not park: `runtime-finish-bend-hard-1`
reached parking at 158.50 s and timed out at 300.15 s with `finished=false`,
`failed=false`, pose unavailable, and zero command. It must not be counted as a
successful timing run. Final diagnostic truth showed the car stationary at
x=+0.22928 m, y=-0.78823 m, yaw=-1.57733 rad.

Saved-frame re-detection localizes the loss. ArUco ID 1 was found at 167.20 s
(PnP yaw +0.455 rad, range 0.6001 m, bbox x=213..248), 167.80 s (+0.5425 rad,
0.5767 m, x=152..196), and 168.40 s (+0.7096 rad, 0.5522 m, x=85..141). The
168.40 fused pose had internal yaw +0.3516 rad, `heading_observed=false`,
front-lateral -0.1345 m, and bearing +0.5894 rad. At 168.70 s marker detection
was absent and the controller correctly stopped. Independent truth yaw stayed
near -1.58 rad over the interval while reported lateral moved from +0.1228 to
-0.1345 m; the lateral jump is inconsistent with the small diagnostic-truth
motion and is evidence of estimator inconsistency near the marker edge. Truth
was not used by control.

The current `b3610f6753516a375832d24c8bedd411637d0c523be40f5336d7f15f3bf13a3f`
source adds a 15-degree bearing-margin stop when heading is unobserved. Its
offline suite reports 59 passing tests, but it has no live completion evidence.
A full harness attempt, `runtime-marker-edge-hard-1`, timed out at
`zmqRemoteApi.info` before scene load; its evidence directory is empty. A second
startup attempt `runtime-finish-bend-hard-2b` also timed out before scene load.
No timing, parking, or safety result is inferred from either attempt.

### November 12 — focused near-edge recovery and Hard validation

Source `b3610f6753516a375832d24c8bedd411637d0c523be40f5336d7f15f3bf13a3f`
contains the outside-zone bend factor 0.05, raw-range braking delay correction,
and the 15-degree stop when heading is unobserved near the marker edge. The
focused suite now passes 61 tests, including persistent near-edge ambiguity
(no movement and no parked success), fresh consistent-yaw recovery with motion
resumption, and the existing immediate marker-loss stop tests. Compile and
scoped diff checks pass. Test output:
`/private/tmp/task3-followup.ZNTHv6/runtime-marker-edge-regression-final.out`.

A separate frozen-image replay used the saved `camera-00168.40.png` from the
failed `362315dc` run. OpenCV re-detected ArUco ID 1 at bbox x=85..141 and PnP
yaw/range +0.709591 rad / 0.552150 m. Replaying this same image four times
with the estimator initialized at the recorded fused yaw showed two zero-speed
unobserved frames, fresh heading on the third, then 1.18 rad/s command and
continued motion. This is deterministic replay from repeated frozen pixels;
it does not establish physical stationarity, scene dynamics, future detection
quality, or live recovery.

Full harness run `runtime-marker-edge-hard-1b`, no `--controller`, completed
with `finished=true`, `failed=false` and parked at 181.25 s. Parking began at
158.55 s (22.70 s phase). Final camera pose was forward 0.208711 m, lateral
-0.001921 m, heading -0.083509 rad (-4.785 degrees), with fresh heading
observed. The final heading is inside, but near, the strict 5-degree limit.
Global and active-zone command maxima were 2.95 and 1.20 rad/s. Hospital hold
commands began at 27.70 s and departure was logged at 33.05 s. Independent
truth was stationary from 27.60 to 32.90 s (5.30 s), with net displacement
under 0.00002 m and maximum sample step under 0.00002 m. Saved parking images
detected the marker in 39/39 images; minimum quadrilateral edge margin was
61 px (10th percentile 87 px). The guarded unobserved-heading/under-15-degree
case did not occur in this particular live run. The run is a successful park,
but misses the 180 s target by 1.25 s and does not meet timing acceptance.

The harness records no collision sensor or road-boundary contact state. Saved
camera views and truth path are available for review, but they cannot certify
absence of collision or off-road contact. The run artifacts are under
`/private/tmp/task3-followup.ZNTHv6/runtime-marker-edge-hard-1b/`. Previous
failed completions and empty startup attempts remain preserved. No Hard-repeat,
Medium, Easy, official score or submission-readiness claim is made from this
single over-target run.

### November 12 — same-source Hard runs after startup-order correction

The `runtime-edge-trace-hard-1` RPC log localized the earlier startup race:
the child controller's `sim.getSimulationState` request timed out during the
parent's concurrent `sim.startSimulation` transition. Initial `drive()` RPCs
had succeeded. The temporary diagnostic harness was changed outside the
submission source to start the engine at zero wheel targets, wait for
`simulation_advancing_running`, and only then spawn the controller. Parent
startup RPCs have a bounded 15 s timeout; controller RPCs remain bounded at
3 s. `task3.py` was not changed and remains SHA256
`fd2acd30c041ecf2a2a3bd50e7ba6b05a6e0644e1fefb6ad271d1d26d65e8d11`.

Two full Hard runs used that exact source hash and the corrected readiness
harness:

| Run | Engine ready | Parked (absolute sim time) | Recorder end | Parking phase | Result |
|---|---:|---:|---:|---:|---|
| `runtime-edge-prelimit-hard-3` | 0.05 s | 179.70 s | 181.05 s | 160.35–179.70 s (19.35 s) | `finished=true`, `failed=false`, rc 0, 718 frames; within 180 s by 0.30 s |
| `runtime-edge-prelimit-hard-4` | 0.70 s | 186.45 s | 187.15 s | 164.50–186.45 s (21.95 s) | `finished=true`, `failed=false`, rc 0, 705 frames; 6.45 s over 180 s |

The controller's parking completion time and the later harness recorder-end
time are distinct; the absolute simulation times above include startup. Both
runs logged a successful Hospital halt and a stationary independent-truth
interval of 5.50 s. Hard 3 truth displacement over the interval was 2.97 µm
(maximum excursion 5.71 µm); Hard 4 net displacement was 8.63 µm. Both runs
stayed within command limits: Hard 3 global/zone maxima 2.99994/1.20 rad/s;
Hard 4 2.99986/1.20 rad/s.

Hard 3 final image pose was forward 0.206201 m, lateral -0.004580 m, heading
-0.059330 rad (-3.40°), with fresh heading observed. In the ID_1 marker frame,
matrix root center-forward `rootX-markerX` was 0.213943 m (13.943 mm from the
0.20 m target, inside the original +/-15 mm physical bound by 1.057 mm). The
front axle point `root + 0.06*unit(root +Z)` was (-0.195922,-0.727293), giving
bay-left lateral -0.002707 m. Matrix ground heading was 176.148° against the
180° bay heading (error -3.852°, inside +/-5°). Image-minus-matrix differences
were -7.742 mm forward, -1.872 mm front-lateral and +0.452° heading; selected
final-image PnP reprojection RMS was 0.270 px. Root/camera matrix headings
differed by 0.0044°.

Hard 4 final image pose was forward 0.210741 m, lateral -0.006317 m, heading
-0.085544 rad (-4.90°), fresh heading observed. Marker-frame matrix
center-forward was 0.219022 m, 4.022 mm beyond the original +15 mm forward
limit. Front axle point `(-0.190704,-0.725825)` gave bay-left lateral
-0.004175 m (inside +/-25 mm). Matrix ground heading was 174.524°, an error of
-5.476° from the 180° bay heading and 0.476° outside the original +/-5° limit.
Thus Hard 4's image pose passed its former gates while physical forward and
heading did not. Image-minus-matrix differences were -8.281 mm forward,
-2.142 mm front-lateral and +0.575° heading; selected final-image PnP
reprojection RMS was 0.408 px. Root/camera matrix headings differed 0.0003°.

During Hard 3 parking, ID 1 was detected in 83/83 PnP frames (zero misses),
with 48 px minimum full-quad image-border margin and 9.52° minimum camera
bearing margin. The observed-heading 1.2 rad/s edge prelimit was exercised in
6 frames; the unobserved-heading zero-stop was exercised in 2. Hard 4 detected
ID 1 in 89/89 frames (zero misses), with 58 px minimum border margin and
10.70° minimum bearing margin; its observed-heading prelimit ran in 6 frames,
with no unobserved under-15° frame. Truth sampling is too sparse and offset
from camera-command timestamps to isolate coasting during the brief edge-stop
frames; it should not be inferred from the bracketing displacements. After
Hard 3 parked, truth moved 1.8 µm over the 179.90–181.05 s recorder tail.

Correct matrix indexing for Coppelia's row-major 3x4 transform uses local +Z
column `(m[2],m[6],m[10])`; planar heading is `atan2(m[6],m[2])`. This corrects
the earlier erroneous reset heading near -90°: Hard reset heading is about
-179.9997° (equivalent to +180°), and camera projected +Z is about -179.998°.
Earlier failed startup records, including `runtime-edge-prelimit-hard-2`, remain
preserved. Evidence is in
`/private/tmp/task3-followup.ZNTHv6/runtime-edge-prelimit-hard-3/` and
`/private/tmp/task3-followup.ZNTHv6/runtime-edge-prelimit-hard-4/`. Neither run
provides collision/off-road contact certification. Hard 4 misses the timing
target, so two Hard runs within 180 s are not yet established. Medium/Easy and
official supported-platform recording remain outstanding; no portal or push.
### November 12 — calibrated Hard run and symmetric parking margins

The corrected temporary harness waits for the controller to import, connect,
and locate handles before starting the engine. It releases the controller only
after simulation-running is confirmed, with wheel targets at zero beforehand.
The parent startup RPC timeout is bounded at 15 s; controller RPC and runtime
remain bounded. The run began at absolute sim time 0.10 s and first drove at
0.30 s.

`runtime-edge-calibrated-hard-1` ran source
`2deace445148d273902a7b73533548a27554939959b4868e8e82b5ea9e04713d` before
removal of signed heading/lateral image biases. It parked at 192.55 s (parking
entry 158.75 s; 33.80 s parking phase), recorder ended 193.05 s, and the 180 s
target was missed by 12.55 s. The controller finished successfully (813
frames, rc 0). Correct marker-frame matrix analysis measured center-forward
0.205687 m, front-point bay-left lateral about -0.000905 m, and heading error
-0.7774 deg; all satisfy the original physical bounds of +/-0.015 m,
 +/-0.025 m, and +/-5 deg. Raw image pose was 0.197211 m forward,
+0.001333 m lateral, and -1.8194 deg heading. The forward image under-report
was 8.476 mm. Lateral and heading residual signs reversed relative to Hard
3/4, so current code retains only the repeatedly supported +0.0083 m forward
image correction and uses symmetric internal gates: +/-0.010 m corrected
forward, +/-0.015 m lateral, and +/-3.5 deg raw heading. Physical limits are
unchanged; fresh heading and stillness checks remain required.

Behavioral regressions reject the former premature Hard 4 image pose and test
both signs of heading and lateral error. `/Users/aryanachary/.venv/bin/python
orchestration/check_task3.py` passed 65 tests; syntax compilation and scoped
diff whitespace check passed. Current source SHA256 is
`a45b3001789e4dbcdd4bd881e725fae6981ca1b7df0cb61a3ad2d8a4175a4b38`. This
source has not had a full live Hard run.

The Hard run had a 5.25 s stationary Hospital interval (28.15–33.40 s),
8.63 micrometres net displacement, and maximum global/zone commands
2.99954/1.20 rad/s. ID 1 was visible in 134/134 parking PnP frames with no
misses; minimum full-quad image-border margin was 5 px and camera-bearing
margin 5.17 deg. Prelimit ran on 34 observed-heading frames and the
unobserved near-edge zero-stop on 5. No collision/off-road certification is
provided.

Trace review places the 0.25 rad/s terminal correction at only about 0.15 s:
the corrected forward estimate first entered the original physical forward
window at 191.20 s, all tighter internal gates first passed at 191.35 s, and
the controller then held zero until 192.55 s. About 32.45 s of parking elapsed
before reaching that physical forward window. The terminal crawl is not the
timing bottleneck; preserve speed and physical bounds and inspect the earlier
merge/edge-limited trajectory before proposing a timing change. No additional
full run was made after the symmetric-bias correction. Evidence is under
`/private/tmp/task3-followup.ZNTHv6/runtime-edge-calibrated-hard-1/`.

### November 12 — rear-axle reference consistency

Confirmed from `PoseEstimator.update`: `lateral` is signed front-axle bay offset,
`forward` is center-to-marker-plane distance, and `heading` is relative to the bay
(the estimator returns the negated fused camera yaw). The existing steering
expression `lateral - WHEELBASE*sin(heading)` is the rear-axle lateral coordinate.
The planner now initializes and advances its quintic in the matching rear frame:
`rear_lateral = lateral - L*sin(heading)` and
`rear_forward = forward + L/2*cos(heading)`. The center-forward
`MERGE_END = 0.26 m` is translated once to aligned rear endpoint
`MERGE_END_REAR = 0.32 m`. Quintic smootherstep shape and steering gains remain
unchanged. Braking and terminal completion/calibration/stillness continue to use
the existing pose convention; no rear offset is applied to those checks.

Regression command `/Users/aryanachary/.venv/bin/python
orchestration/check_task3.py` passed **67 tests**. New geometry cases cover both
heading signs, nonzero heading at handoff, initial reference equality, aligned
endpoint translation, normalized quintic shape and left/right reflection. Existing
completion, calibration, marker-loss, hold, edge, speed and steering checks remain
in the suite. Syntax compilation and `git diff --check -- task3/task3.py
orchestration/check_task3.py orchestration/TASK3_RESULTS.md` passed. Test log:
`/private/tmp/task3-followup.ZNTHv6/rear-frame-tests.out`.

Exact source SHA256:
`f47462a64c25347d12addd49b9d9c7cc73d747b155ffc1ba90e2312118bbe39e`.
Full diagnostic command:
`/Users/aryanachary/.venv/bin/python /private/tmp/task3-followup.ZNTHv6/rehearse_groundheading.py Hard rear-frame-consistency-hard-1 --reuse-verified-hard-scene`.
The harness verified the stopped clean Hard reset scene and zero wheel targets,
connected/located the controller before engine start, then started at absolute
simulation time 0.10 s. First nonzero drive command was at 0.30 s. Controller
finished successfully (`finished=true`, `failed=false`, rc 0; 766 frames). Parking
entry was 158.20 s and park completion 183.90 s, absolute simulation times
including startup; parking phase was 25.70 s. The 180 s target was missed by
3.90 s. Evidence directory:
`/private/tmp/task3-followup.ZNTHv6/rear-frame-consistency-hard-1/`.

At 183.90 s, final camera pose was center-forward 0.187022 m, front lateral
-0.003724 m and heading -2.082°; calibrated completion forward was 0.195322 m.
The nearest two matrix samples bracket 183.90 s at 183.75 and 184.30; linear
position and wrapped-heading interpolation in the ID_1 marker frame gives
center-forward 0.193756 m, front lateral -0.002530 m and ground heading error
-2.433° from the desired 180° bay direction. These are within existing physical
bounds (+/-0.015 m center-forward, +/-0.025 m front lateral, +/-5° heading).
This interpolation is simulator diagnostic evidence only; camera pose remains
the controller input.

Hospital stop/hold/departure logs were 27.30/27.30/32.60 s (5.30 s hold).
Independent truth samples over 27.70–32.45 s span 4.75 s; net displacement was
6.4 micrometres. Global command maximum was 2.99987 rad/s, active-zone maximum
1.20 rad/s, and parking maximum 2.95 rad/s. During parking, the marker was
present in 118 of 119 PnP diagnostic observations, with one missing observation;
one of 120 controller frames had an invalid pose and 22 had heading unobserved.
The minimum observed PnP bounding-box border margin was 4 px. The harness does
not record collision sensors or road-boundary contacts, so no collision/off-road
absence claim is supported. One successful Hard run does not satisfy repeated
Hard <=180 s, Medium, Easy or official recording acceptance.

### November 12 — time-aligned yaw prediction

`PoseEstimator.update` now predicts yaw from the preceding final bounded
steering and speed command integrated over valid elapsed simulation time. It no
longer derives yaw travel from filtered range differences or a fixed 1 cm per
frame cap. First observations and invalid, nonpositive, or overlong intervals
do not invent travel; the default yaw blend interval remains separate. Both
handover priming calls pass zero motion, while parking and invalid-frame paths
pass the prior bounded command. The harness wrapper forwards the new speed
argument. PnP acceptance/recovery gates and physical caps were retained.

The saved open-loop raw-PnP replay, seeded by the final untimed handoff
observation at 158.2 s (the first timed PnP observation is 158.4 s), compares
legacy versus command/time prediction as follows: maximum fused yaw error
32.80° to 22.16°, bad normal updates with raw error above 15° 1 to 0, and p90
absolute error 4.243° to 4.245°. The improvement is localized and does not
support a timing-savings claim. The old replay matches logged fused yaw on the
first two timed observations, then diverges by up to 4.494° (p90 1.076°); later
exact framewise equivalence is unverified. The diagnostic wrapper's extra `_pnp`
call is one unconfirmed source of divergence. Matrix-heading truth uses
interpolation brackets up to 0.75 s, so these are diagnostic estimates.
Replay evidence: `/private/tmp/task3-followup.ZNTHv6/rear-frame-analysis/`.

The focused suite passed **72 tests** and syntax compilation passed. One full
Hard run on source SHA256
`6e2111c1b360f88c065127704f369da176313e7171706e4eb689ad9da603700c` used the
controller-ready harness on the stopped reset-verified scene. Startup was
0.10 s; first nonzero drive was 0.25 s; Hospital stop/rest/departure were
26.85/27.70/33.15 s; parking entry was 159.65 s; parked was 182.35 s; harness
ended at 182.80 s. Controller exit was 0, finished=true, failed=false, and
699 frames were processed. This run misses the 180 s target by 2.35 s.

At completion the image pose was center-forward 0.199457 m (calibrated
0.207757 m), front lateral -0.005393 m, and heading +0.241°. Interpolated
marker-frame truth at 182.35 s (matrix samples 182.15 and 182.80) was
center-forward 0.208027 m, front lateral -0.005311 m, and heading error
+0.153°. Interpolated truth is diagnostic only. Command maxima were 2.99993
rad/s globally, 1.20 rad/s in the zone, 2.95 rad/s in parking, and 0.682 rad
steering. Hospital zero motor targets span sampled 27.20–33.15 s (5.95 s);
visual rest confirmation spans 27.70–33.15 s (5.45 s). Adjacent truth samples
show at most 10.4 μm movement and 15.1 μm total excursion during the zero-target
interval.

Parking had 93/93 valid image poses and zero invalid-pose frames; fresh heading
was unobserved on five frames. All 40 captured parking screenshots showed the
full marker, with minimum quadrilateral border margin 60 px. Truth-aligned
heading estimation error was p90 4.89°, maximum 8.14°; lateral pose discrepancy
was p90 5.57 cm, maximum 10.94 cm. Replayed path commands match every logged
parking command exactly. Parking cap exposure was visibility 8.70 s, global
4.95 s, frame travel 3.25 s, braking 2.35 s, yaw 1.90 s, with a 0.25 s
uncertain-edge stop. Evidence and raw logs:
`/private/tmp/task3-followup.ZNTHv6/yaw-prediction-hard-1/`.

This is one successful but over-target Hard run; repeated Hard <=180 s, Medium
twice, Easy once, and supported-platform official artifacts remain outstanding.

### November 12 — bounded cubic visibility path, audited completion

Current and recorded-run source SHA256:
`ee5f7a1407a328766e8ef115294d6ef8567508dcea615f7f57c221dd2358f387`.
The source delta from `6e2111c1b360f88c065127704f369da176313e7171706e4eb689ad9da603700c`
adds only Parker profile constants/state and profile-reference selection. At
handoff, 201 rear-frame samples select cubic only if its peak planned bearing
is <=27.5 degrees (5 degrees below the unchanged 32.5-degree speed prelimit),
its improvement over quintic is >=3 degrees, and peak curvature is <=90% of
the physical limit (6.089 versus 6.766 /m). Otherwise the original quintic is
retained. The aligned rear endpoint stays 0.32 m, corresponding exactly once
to the existing center-forward MERGE_END of 0.26 m. No controller edits were
made during this final audit.

Offline geometry, at zero initial heading (forward/lateral in metres):

| Start | Peak bearing quintic -> cubic | Nominal prelimit exposure quintic -> cubic | Selection |
| --- | --- | --- | --- |
| .85 / .27 | 35.99 -> 29.47 degrees | 1.117 -> 0 s | quintic: 5-degree reserve fails |
| .90 / .23 | 29.93 -> 23.87 degrees | 0 -> 0 s | cubic |
| .90 / .21 | 27.98 -> 22.15 degrees | 0 -> 0 s | cubic |
| .856 / .238 | 32.84 -> 26.51 degrees | .361 -> 0 s | cubic |

These exposure figures divide rear-forward distance above 32.5 degrees by an
assumed constant 0.12 m/s; they are model units, not measured runtime. Across
+/-5-degree initial headings the observed-start cubic peak bearing ranges
21.22–30.31 degrees and peak curvature reaches 4.838 /m. Mirroring both lateral
and initial heading gives exactly opposite lateral, heading, bearing and
curvature arrays (maximum antisymmetry residual zero). A wider .82/.31 start
fails the visibility reserve; a short .45/.27 start reaches 18 /m cubic
curvature and fails geometric feasibility. A narrower .96/.17 start qualifies.
The actual run handoff (.880487/.242077, image heading zero) has ideal peak
bearing 31.980 -> 25.724 degrees and cubic curvature 3.773 /m; both ideal paths
are below the speed prelimit at this particular start.

Cubic has nonzero one-sided endpoint curvature, not C2 continuity with the
straight segments. The nominal observed-start feedforward steering step is
20.26–29.18 degrees, reaching 30.14 degrees under the sampled heading offsets.
The saved simplified kinematic stress check uses 10 Hz updates, a nominal
one-update command delay, 0.10 s first-order steering lag, 0.12 m/s progress,
+/-5 mm lateral and +/-2-degree heading perturbations, and 20 seeds. Worst
modeled lateral error over the four starts falls from 33.81 to 22.23 mm;
for the qualifying .856/.238 start, peak modeled bearing falls from 37.02 to
29.84 degrees. The .85/.27 cubic case still reaches 33.17 degrees and is
excluded by the reserve selector. This model uses simplified rear-forward
progress, omits adaptive speed and terminal dynamics, applies the first
command immediately, and ends at the merge endpoint. It does not establish
post-merge servo settling or live feasibility. The separate steering-step
lag calculation is a small-angle sensitivity estimate, not a strict bound.

Verification: the final full suite passed **74 tests in 0.925 s**. Syntax
compilation and scoped whitespace checks passed. The first added regression
initially failed because it sampled curvature exactly at the existing inactive
endpoint; the assertion was corrected to sample the nonzero one-sided cubic
curvature just inside the interval, then all tests passed. An earlier whole-repo
`git diff --check` reported existing task2a CSV trailing whitespace/CRLF; those
unrelated dirty files were preserved. Source diff and final check output are
saved in the audit directory.

Exactly one Hard rehearsal, `visibility-cubic-hard-1`, used the stopped,
reset-pose/zero-target verified scene with no concurrent task controller.
Command: `/Users/aryanachary/.venv/bin/python /private/tmp/task3-followup.ZNTHv6/rehearse_groundheading.py Hard visibility-cubic-hard-1 --tmax 300 --reuse-verified-hard-scene`.
The controller was imported/connected before engine startup, engine-ready sim
time was 0.15 s, first nonzero drive 0.40 s, parking entry 158.75 s, parked
181.05 s, and recorder end 181.75 s. Cubic was selected. Controller rc 0,
finished=true, failed=false, 665 frames; parking phase 22.30 s. All times are
absolute simulator times. The 181.05 s park misses the 180 s target by 1.05 s.

Completion truth uses the chassis local +Z ground direction against the bay's
pi direction, and the front point at center +L/2 along that direction; chassis
lateral is not substituted for front lateral. Matrix/truth interpolation over
180.65–181.20 s (0.55 s bracket) gives center-forward **0.205674 m**, front
lateral **-0.005138 m**, heading **-1.954 degrees**. These satisfy the original
physical +/-15 mm, +/-25 mm and +/-5-degree bounds. The final image pose is
forward 0.197662 m (calibrated 0.205962 m), front lateral -0.005407 m, heading
-1.894 degrees, with fresh heading observed. Raw image forward under-reports
truth by 8.012 mm; the calibrated residual is +0.288 mm. Interpolated truth
remains diagnostic evidence, not a new success input to the controller.

Hospital stop/rest/departure logs are 26.80/27.70/33.10 s: visual rest spans
5.40 s. Zero-target truth samples span 27.25–33.10 s. The 13 independent truth
samples during confirmed rest span 27.70–33.10 s (5.40 s), net movement
6.10 micrometres, maximum excursion 7.98 micrometres, largest adjacent movement
8.34 micrometres. Logged command maxima: global 2.99999824 rad/s, active zone
1.20 rad/s, parking 2.95 rad/s, virtual steering 0.68195431 rad. These respect
the existing command limits; the wheel numbers are targets, not encoders.

Parking has 87/87 valid controller poses, 14 without fresh heading, and zero
marker-loss frames. All 88 parking PnP records (including duplicate priming)
have a marker quadrilateral. Re-detection found ID 1 fully in 37/37 regular
parking screenshots (minimum border margin 73 px), and 80/80 regular plus edge
screenshots (minimum 64 px). Minimum margin in all recorded PnP bboxes is also
64 px, using pixel-coordinate borders 0..639 and 0..479.

Exact saved-pose replay reproduces every parking steering/speed command.
Forward-duration-weighted binding caps: visibility 5.05 s, frame travel 5.05 s,
global 4.60 s, braking 3.10 s, yaw 2.20 s, uncertain-edge stop 0.90 s, terminal
settle 1.40 s. Actual bearing exceeds 32.5 degrees for 2.55 s (peak 36.209
degrees). These are distinct from binding-cap exposure. The fixed-distance
proxy for removing the visibility cap is 2.501 s; it is arithmetic on the
recorded trajectory, not an intervention or permission to remove the guard.
Compared with the reported baseline, binding visibility exposure fell from
8.70 to 5.05 s, while uncertain-edge stopping rose from .25 to .90 s. Parking
phase fell from 22.70 to 22.30 s; 0.90 s earlier route arrival accounts for the
rest of the 1.30 s total park-time difference. This single unpaired run does
not prove that geometry caused those changes.

Against the exact replayed reference, image-derived rear lateral error is
p90 61.32 mm / max 140.34 mm; independently interpolated physical rear lateral
error against that same commanded reference is p90 22.82 mm / max 30.04 mm.
Image heading tracking error is p90 9.153 / max 13.005 degrees; physical
heading tracking error against the same reference is p90 11.861 / max 17.034
degrees. Matrix sampling gaps reach 0.75 s. Large image pose excursions must
not be described as equivalent physical lateral motion.

Evidence: `/private/tmp/task3-followup.ZNTHv6/visibility-cubic-hard-1/` and
`/private/tmp/task3-followup.ZNTHv6/visibility-cubic-audit/`; offline geometry
and assumptions: `compare_bounded_profiles.py` / `bounded-profile-comparison.txt`
in the parent temporary directory. The earlier provisional
`summarize_visibility_cubic_run.py` used incorrect pose axes and cap-condition
arithmetic; its reported 11 s cap figure and near-180-degree heading are
superseded by this audited exact-replay result, not physical failures.
Post-run read-only audit found no task controller, simulator stopped (state 0,
sim time 182.05 s), and both motor targets zero. No new live run was started.
All user-dirty scenes and unrelated files were preserved. Sol review is next;
repeated Hard <=180 s, Medium twice, Easy once and official Windows/Ubuntu
artifacts remain outstanding. Collision/off-road sensors were not captured;
no collision/off-road certification, readiness claim, push or portal action.

### November 12 — unchanged-source Hard repeat and clean Medium

Both new runs use exact `task3/task3.py` SHA256
`ee5f7a1407a328766e8ef115294d6ef8567508dcea615f7f57c221dd2358f387`.
Controller and tests were unchanged; the existing **74 passing tests** were
not rerun. Initial/final hashes also confirm the previously dirty workspace
scenes were preserved. One startup attempt per arena succeeded, with no
simulator restart or failed startup. Ownership checks found only the identified
CoppeliaSim PID 99503 and no active task controller before each run. Hard reused
the verified stopped/reset scene. Medium loaded only the isolated temporary
scene, whose Git blob `4a33232ee583c654c9ae69589f1a4bd3b282a4e7` matches HEAD.
Both used bounded sockets, the controller-ready-before-engine handshake, the
300 s simulation bound, and absolute simulator time without clock subtraction.

Commands:

- `/Users/aryanachary/.venv/bin/python /private/tmp/task3-followup.ZNTHv6/rehearse_groundheading.py Hard visibility-cubic-hard-2 --tmax 300 --reuse-verified-hard-scene`
- `/Users/aryanachary/.venv/bin/python /private/tmp/task3-followup.ZNTHv6/rehearse_groundheading.py Medium visibility-cubic-medium-1 --tmax 300`

| Absolute time / result | Prior Hard 1 | Hard repeat | Medium |
| --- | ---: | ---: | ---: |
| Engine ready | .15 | .05 | .50 |
| First drive | .40 | .20 | .70 |
| Hospital stop / visual rest / departure | 26.80 / 27.70 / 33.10 | 26.65 / 27.60 / 33.00 | 34.65 / 36.00 / 41.40 |
| Speed 40 entry / exit | 45.75 / 128.50 | 45.35 / 128.85 | 53.60 / no exit |
| Parking entry | 158.75 | 159.15 | 221.50 |
| Parked | 181.05 | 182.10 | 266.10 |
| Parking phase | 22.30 | 22.95 | 44.60 |
| Recorder end | 181.75 | 183.75 | 266.60 |
| Profile | cubic | cubic | quintic fallback |

Both new controllers exited 0 with finished=true/failed=false; Hard processed
705 frames, Medium 941. Hard repeat had no demonstrated new physical/marker
failure, so the authorized Medium proceeded. This decision did not certify
penalty-free driving. Hard 1/2 both miss 180 s, by 1.05/2.10 s. Their total
1.05 s difference splits into .40 s route-arrival difference and .65 s parking
phase difference. Thus repeatable <=180 s is not established.

Interpolated physical completion, using chassis local +Z ground heading
relative to the bay direction and the actual front-point offset:

| Completion quantity | Hard repeat | Medium |
| --- | ---: | ---: |
| Center-forward | .201955 m | .204269 m |
| Front-lateral | -.000854 m | +.002921 m |
| Heading error | -1.389 degrees | -1.377 degrees |
| Matrix interpolation bracket | 181.85–182.55 s (.70 s) | 266.00–266.60 s (.60 s) |
| Raw image forward / front lateral / heading | .194098 m / -.001347 m / -1.363 degrees | .195972 m / +.003008 m / -1.629 degrees |

Both physical terminal poses satisfy the original +/-15 mm forward, +/-25 mm
front-lateral and +/-5-degree heading tolerances. Final image heading is freshly
observed. Maximum matrix sampling gaps are 1.20 s Hard and .90 s Medium;
sequential RPCs are not simultaneous sensor samples, and interpolation bracket
sizes are disclosed rather than treated as rigorous pose-error bounds.

Both visual Hospital rest intervals are 5.40 s. Hard's 15 zero-target truth
samples span 26.90–33.05 s (6.15 s), net movement 10.39 micrometres and maximum
excursion 16.68 micrometres. Samples strictly inside the visually confirmed
27.60–33.00 s interval span only 28.00–32.60 s (4.60 s): sparse truth sampling
must not be described as a separate 5.40 s confirmed-rest sample span. Medium
has 12 confirmed-rest truth samples at 36.05–41.10 s (5.05 s), net/max excursion
5.87 micrometres, with all sampled motor targets zero.

Hospital scoring location remains **unverified**. The supplied instructions
require rest inside the approximately 10 cm across by 20 cm along pickup patch;
duration alone does not establish that. Logs contain sign boxes/range estimates,
chassis motion and visual-rest events, but no pickup-patch transform/bounds or
calibrated vehicle-to-patch containment test. This also qualifies earlier
references to a passed Hospital hold: rest duration is supported, full scored
location compliance is not proved.

Command maxima (rad/s): Hard global 2.99998278, active zone 1.20, parking 2.95;
Medium global 2.99980275, active zone 1.20, parking 1.20. Both maximum virtual
steering commands are .68195431 rad, within the source command limit. These
are command targets, not wheel encoders or evaluator penalty measurements.

Hard parking has 101/101 valid control poses, 18 without fresh heading, and
102/102 PnP records with marker boxes (including priming); all 39 regular and
84 regular+edge screenshots contain full ID 1, minimum border margin 93 px.
Medium has 135/135 valid control poses, 11 without fresh heading, and 136/136
PnP records with marker boxes; all 72 regular and 160 regular+edge screenshots
contain full ID 1, minimum margin 23 px. Neither run has a marker-loss frame.
Exact saved-pose replay including final Mission caps matches every logged
parking steering/speed command for both runs.

Binding Parker cap exposure (seconds):

| Cap | Prior Hard 1 | Hard repeat | Medium |
| --- | ---: | ---: | ---: |
| Visibility | 5.05 | 4.80 | 21.20 |
| Frame travel | 5.05 | 4.15 | 11.45 |
| Global | 4.60 | 4.15 | 1.45 |
| Yaw | 2.20 | 4.20 | 4.55 |
| Braking | 3.10 | 3.25 | 2.95 |
| Uncertain-edge stop | .90 | 0 | .40 |
| Terminal settle | 1.40 | 2.40 | 2.60 |

Hard repeat has no measured bearing over 32.5 degrees (peak 30.206 degrees);
its visibility exposure includes unobserved-heading speed limiting. Medium
exceeds 32.5 degrees for 17.85 s, peak 40.664 degrees. Medium's zone flag stays
true and zone_done false through parking. The final Mission zone cap is active
for all 44.60 s of parking and further reduces otherwise higher parking commands
for 19.15 s / 60 frames. That is an additional stage and overlaps the adaptive
cap intervals; these durations must not be added as independent delays.

Focused Medium exit-sign inspection:

- The full control log contains 146 normal Speed40 records at 53.60–90.15 s,
  all in the first encounter's continuous image-box progression. There is no
  later normal Speed40 detection or second-sign/zone-exit event through 266.10 s.
- Offline current-source weak-board detection returns **zero candidates on all
  437 saved regular frames**. The saved route window 120–145 s has 45 frames,
  maximum capture gap .70 s. Weak raw candidates and WeakBoardTracker/rearmed
  state were not logged at every live control frame, so zero saved candidates
  cannot prove zero candidates in unsaved frames or identify the exact live
  tracker transition that failed.
- The visually corresponding oblique board beside the house is preserved in
  `camera-00126.30.png`, `camera-00130.00.png`, and `camera-00135.15.png`.
  At 126.30 s the white component is [337,51,4,34], 73 pixels, width/height .118;
  at 130.00 s it is [350,50,5,36], 76 pixels, ratio .139. Both fail the current
  >=80 white-pixel and >=.24 aspect-ratio gates, and have no in-hull red/blue.
  At 135.15 s [458,46,14,44] has 148 white pixels, ratio .318 and 34 blue pixels,
  but **zero red pixels**, failing the >=4 red-pixel and separated-rim evidence.
  Other visible white/red strips do not supply the required blue evidence.
- The comparable accepted Hard exit frame `camera-00128.85.png` yields weak
  bbox [496,44,19,47], 263 white pixels, ratio .404, 57 blue and 11 red pixels.
  It is a supported offline comparison of the candidate geometry; a distinct
  physical sign's semantic identity is not established solely by that heuristic.

No scene or perception gates were changed. Original frames remain untouched;
selected-frame hashes, component measurements, normal detections and the complete
weak-frame scan are preserved under `reproducibility-audit/`. The focused next
correction should use these oblique-board frames to establish reliable,
sign-specific second-encounter evidence before changing the perception path.
Preserve distinct-encounter/rearm requirements and the conservative zone cap;
absence alone must not release the zone. The Hard pair also shows yaw/settle
variability, so a perception fix in Medium must not be represented as resolving
Hard's remaining timing deficit.

Evaluator collision/off-road compliance remains **unverified**. The supplied
collision criterion is overlap of the evaluator's 9 cm square, not simulator
physics contact. Off-road means a wheel more than 1 cm outside the allowed
road, including yellow boundaries. The harness captures RGB frames, perception
outputs, commands, chassis/camera/marker matrices and sampled chassis positions;
it does not record the evaluator square-overlap calculation, relevant obstacle
footprints, wheel-to-road-boundary distances or official penalty counters. It
also records no physics contact sensors. Neither absence of visible contact,
physical parking, nor an imagined collision pair certifies these criteria.

Final bounded check found no task controller, simulator stopped at absolute
266.85 s, and both motor targets zero. No additional tuning, live run, evaluator
execution, push or portal action occurred. Results remain intermediate: repeated
Hard <=180 s, Medium twice, Easy once, scored rule compliance and official
Windows/Ubuntu artifacts are still required.

Raw runs: `/private/tmp/task3-followup.ZNTHv6/visibility-cubic-hard-2/` and
`/private/tmp/task3-followup.ZNTHv6/visibility-cubic-medium-1/`.
Audit: `/private/tmp/task3-followup.ZNTHv6/reproducibility-audit/` contains
harness stdout, `analyze_repro.py`, per-run `repro-summary.json`, supplemental
cap/hold metrics, `medium-exit-frame-manifest.json`, `board-geometry.json`,
normal/weak detection scans, initial/preserved hashes and final process/API state.

### November 12 — oblique exit identity audit and conservative fallback disable

One bounded correction was made. Current `task3/task3.py` SHA256 is
`ea3a4954d97dcced427beac4cf379b6a6bce64b6c20e0a732a4602135f6a7da8`.
The only changed controller function is `_whiteboard_speed_candidates`, which
now returns no exit candidates. The white/blue convex-hull fallback is disabled
because it accepts Parking-associated imagery with incidental red pixels,
without proving Speed40 identity. Normal Speed40 classification, first-sight
entry, distinct-encounter/rearm logic, all motion/parking/observer logic, and
command limits remain unchanged. No scene-derived coordinates, templates or
identities were placed in the controller.

Identity evidence supersedes the earlier suggestion that the x458 blue strip
was a missed Speed40 board. All 45 saved Medium 120–145 s upper-image views
were reviewed chronologically, with full original earlier/later views at
110.15, 119.85, 124.05, 131.90, 138.90, 147.30, 155.20, 164.75 and 179.75 s.
Original normal Speed40, Hospital, Parking and School examples were compared.
Magnified crops use only nearest-neighbor repetition of original pixels.
The blue strip's median blue HSV [104,252,191] matches the known Parking
example; known Hospital is [113,250,166]. Medium 138.90 s has Parking-template
score .459 versus Hospital .265, but no usable normalized glyph. Color and
these scores alone are not semantic proof.

A bounded read-only inspection of the already-stopped clean Medium scene
provided named static sign meshes. Projecting those meshes through saved camera
matrices establishes the component separation (no simulator run or scene edit):

| Saved image | Actual Speed_40_Sign shape 47, projected bounds | Parking shape 54, projected bounds |
| --- | --- | --- |
| Medium 135.15 s | x384.6–393.6, y52.5–112.9 | x455.5–475.5, y45.5–119.4 |
| Hard 128.85 s | x414.7–427.0, y51.7–114.9 | x492.2–519.1, y43.8–122.9 |

The Medium observed red/white sliver [382,53,9,60] aligns with the actual
Speed40 shape; the blue [458,46,14,44] component aligns with Parking. The
first normal Speed40 encounter at Medium 80.30 s projects to the separate
shape 49, x397.3–455.9, matching the recorded first-sign image. Thus these are
spatially distinct first/second Speed40 objects, not a justification to treat
any later white/blue strip as an exit.

Hard's old weak acceptance bbox [496,44,19,47] lies on the Parking projection.
Its 11 accepted red pixels are x498–505, y51–78, mostly BGR [0,0,230]. These
pixels are over 70 image columns from the actual Speed40's right edge. The
filled white hull aggregates those red samples with 57 Parking-associated blue
samples. It does **not** demonstrate a coherent rim around the actual Speed40.
Exact red texel/surface ownership (Parking material, other surface or projection
contamination) is not proved by an object-ID render, which was not captured;
no specific background object is asserted. The semantic fusion/false-release
risk is nevertheless established: the accepted blue board is Parking-associated
and the real Speed40 is elsewhere. Adjacent Hard frames 128.15/129.35 s also
produce this weak heuristic acceptance. These are false-positive regression
examples, not verified Speed40 positives.

Projection is diagnostic only. Camera interpolation brackets are .60 s for
Medium 135.15 and .70 s for Hard 128.85; the nearest Hard camera sample is only
.05 s later. The static meshes were read from the unchanged Medium scene;
Hard attribution additionally relies on the matching static asset placement
and visible projection alignment. This is not exact per-pixel segmentation,
but the large separation of the distinct boards does not support fusing them.
No world coordinates or object identities feed control.

The actual second Speed40 is severely foreshortened in the saved sequence;
the printed 40 cannot be reliably read from its few-column interior. No
supported true oblique-exit classifier was produced. Removing the red gate,
accepting generic blue/white strips, or using route progress would admit
unrelated boards and was not implemented. The correction is solely to disable
the unsafe fallback. Under the work order and parent's latest direction,
**zero live runs were made**: a true exit detector is still an offline blocker.

Verification: **77 tests passed in .746 s**. Recorded Hard Parking hulls,
Medium oblique Parking, mirrored/distant/clipped variants, and an end-to-end
rearmed-zone/dropout/invalid-frame case are rejected or retain the <=1.2 cap.
Actual readable, distant/clipped and top-clipped Speed40 images still classify
through the normal detector with reference images absent. Existing Hospital,
Parking, School/background negatives, same-sign reacquisition, distinct second
encounter, command and terminal checks pass. The previous synthetic blue/red
whiteboard test was corrected: it supplied no discriminative 40 glyph and is
now a rejection test. Running the three focused rejection/zone tests against
the previous source produces the expected failures (10 assertion/subtest
failures across 3 tests), including actual false zone release. Syntax and scoped
whitespace checks passed. AST comparison confirms only the candidate helper
changed; source/test diffs and fixtures are preserved in the temporary audit.

Timing cost is not hidden. Normal-only replay on the frozen existing Hard and
Medium detection logs yields only first entries (45.35/53.60 s), final sign
count 1 and rearmed=true; no valid second normal encounter. The old Hard exit
at 128.85 s disappears under this evidence path. Commands after that point may
remain capped at 1.2 instead of reaching 3.0 rad/s; slower completion is a
likely cost. No new completion time is measured or predicted from this frozen
replay. Historical 181.05/182.10 Hard and 266.10 Medium runs belong to the old
hash; they do not validate timing or scored compliance of this correction.
Their physically valid parks remain evidence of those runs, but the Hard weak
exit is no longer accepted as semantic zone-exit proof.

Focused next milestone: obtain/label discriminative original pixels for the
actual red-rim Speed40 shape, then prove a sign-specific detector against the
now-embedded Parking false positives before any new live run. If its face
remains unobservable at the unchanged camera path, report that limitation rather
than release the conservative cap without evidence.

Evidence: `/private/tmp/task3-followup.ZNTHv6/oblique-exit-audit/` contains the
45-frame manifest/three chronological sheets, original-pixel comparison and
crop manifest, semantic reference/no-reference replay, sign aliases/meshes,
static projections, exact hull red-pixel coordinates, appearance measurements,
regression ROIs, before-source/tests, `source.diff`, `tests.out`, expected old
failures, and scope/hash checks. Original scenes/frames and failures are
preserved. Final read-only check: simulator stopped at 266.85 s, both motor
targets zero; no controller or child was started. No tuning, evaluator run,
portal, push or readiness claim. Hospital patch containment, evaluator 9 cm
collision-square overlap, wheel >1 cm off-road including yellow, reliable
Hard <=180, Medium twice, Easy once and official supported-platform artifacts
remain open. Physics contact does not substitute for evaluator criteria.

### November 12 — corrected-source dense-camera Hard baseline

One unchanged-source Hard rehearsal used SHA256
`ea3a4954d97dcced427beac4cf379b6a6bce64b6c20e0a732a4602135f6a7da8` and an
isolated HEAD Hard scene (Git blob `370d8299033e8b14384eea1d49781b26a2c61434`;
workspace scenes were not loaded or saved). Exact artifacts and full bounded
offline report: `/private/tmp/task3-dense-camera/dense-hard-ea3a4954/`
(`DENSE_CAMERA_REPORT.md`).

Elevated API health before load returned `{"state":0,"time":266.8500000000264}`.
The ready-before-engine handshake succeeded; one engine start at 0.15 s and one
run only. Parked at 238.25 s; harness ended at 239.10 s (controller/harness
exit 0, finished=true, failed=false). Post-run API confirmed stopped at 239.45 s
and both motor targets zero. This single Hard run is 59.10 s beyond 180 s.

Dense capture saved all 840/840 valid pre-parking BGR frames consumed by
`Mission.step` from 0.35–199.55 s: 0 drops, 0 write errors, queue peak 1/96,
max image gap 0.40 s (median 0.25 s). Async copy/enqueue mean/max were
0.138/0.372 ms. No additional image RPC or instrumentation PnP solve was used.
The temporary raw per-frame detection field is empty because of a logger
variable-shadowing error; the exact unchanged detector was replayed offline on
all 840 frames and merged with tracker telemetry. It found 144 repeated first
Speed40 detections from 45.55–83.30 s, and none after rearm at 87.35 s. Final
tracker count=1/rearmed=true; zone remained active through parking, with no
exit.

No verified second Speed40 face/glyph was found in the actually consumed
frames. Best candidate at 159.85 s projects 52.2x58.4 px but is 62.3% clipped;
its ROI contains 327 red/75 white pixels amid storefront/awning structure, so
surface ownership is unresolved. The fully in-frame 134.45 s candidate has no
red/white pixels. These are projection/ROI measurements, not sign recognition.
Frame paths and crops are in the report.

Timing: first nonzero drive .85 s; Hospital stop/rest/release 27.05/27.90/33.35
s; sampled zero motor targets 27.30–33.35 s (6.05 s, max root displacement
0.025 mm; pickup-patch location unverified); zone entry 45.55 s/no exit;
parking entry 199.55 s; parked 238.25 s (38.70 s parking phase). Maximum speed
command 2.99985 rad/s outside zone and 1.2 rad/s in-zone. Valid parking pose
131/131 frames; heading observed 111/131. Physical terminal pose interpolated
at 238.25 s: center-forward .20616 m, front-lateral -.00378 m, heading error
+1.769 degrees (matrix bracket .50 s). Collision/off-road scoring remains
unverified. No tests were rerun; controller source and workspace scenes were
not changed. No acceptance claim. Parent review of the two best original crops
is the next focused decision; no further tuning cycle is included.

### Bounded projection review (12 Nov 2026)

Corrected sign correspondence using existing dense frames and the stopped-scene named-object query. Three large ID1 marker anchors select the established 640x480/FOV95 mapping with horizontal image flip and give 4.99–5.18 px RMS corner residual (max 6.08–6.46 px). The first readable Speed40 board at 80.20–83.30 s is consistent with saved Medium Speed40 handle49; handle47 projects off-frame at 80.20 s. Thus previous handle47 projections describe the other placement, not the first sign. At 134.45 s handle47 still projects near x581–622, separate from the x≈445 red/white feature; that feature remains unidentified. Late storefront overlap remains semantically uncertain; this review does not establish second-sign visibility or impossibility.

Current stopped Hard query: state0/time239.4500000000202. ID1/ID2 and both Parking transforms match Medium; the only named Hard Speed40 alias is handle47 at `[.370,-.820,.100]`, delta `[-.210,-.015,0]` from Medium handle47 and `[+.175,-2.025,0]` from Medium handle49. Mesh hash differs from both Medium sign meshes. Its projected first-sign position is inconsistent with the recorded first board, so stopped Hard sign alias geometry is not a safe historical label. No source/test/scene changes; no tests rerun. Full measurements and inspected frame paths: `/private/tmp/task3-dense-camera/dense-hard-ea3a4954/PROJECTION_REVIEW_REPORT.md`.

Follow-up saved-data sanity check: parent projected first-sign Medium handle49 center `(0.195,1.205,.1775)` with camera t45.40 s to horizontal-flipped pixel `(624.775,65.980)`. Observed first-frame bbox at45.55 is `(604,49,36,33)`, center `(622,65.5)`, about2.8px residual over .15s; unflipped x≈15 is wrong. This independently supports the global flip and first-sign correspondence. Thus x445 at134.45 could be storefront decoration; identity remains unasserted. Offline dense images contain no detectable ID2 corners, so no second image-space marker anchor was available; ID1 remains the multi-frame marker validation. Exact Hard/Medium deltas remain as recorded above.

### Runtime identity and provenance correction (12 Nov 2026)

The dense Hard scene/run provenance was traced before any detector change. Its
recorded parent command passed `/private/tmp/task3-dense-camera/Task_3_Hard_HEAD.ttt`
to the harness `--scene-path`; the harness loads that path, records marker and
camera/world matrices, sets motor targets, and starts/stops simulation. The
controller source hash is `ea3a4954d97dcced427beac4cf379b6a6bce64b6c20e0a732a4602135f6a7da8`.
Both clean Hard files checked by the parent
(`/private/tmp/task3-dense-camera/Task_3_Hard_HEAD.ttt` and
`/private/tmp/task3-followup.ZNTHv6/task3/Task_3_Hard.ttt`) have SHA256
`8082c50a967a548bf9b7ea82e718ada6f4a41cae84ebb4f340d64c9238972f75` and Git
blob `370d8299033e8b14384eea1d49781b26a2c61434`. The dirty workspace Hard
scene was not loaded or saved.

The restarted task simulator API reported that exact isolated path and name
`Task_3_Hard_HEAD.ttt`. Relevant aliases/transforms were captured before start,
at 2.70 simulated seconds, and after stop at 2.95 s. These captured objects did
not move or appear/disappear. Case-insensitive enumeration found one alias
containing `speed` or `40`: handle47 `/Speed_40_Sign`, with no child objects;
the separate sign-named aliases were Hospital and School. This is an alias
inventory, not proof that no other physical Speed40 sign exists. Both motors
were zero at stop. The run-time identity snapshots are in
`/private/tmp/task3-dense-camera/runtime-identity/`.

Correction to the preceding projection correspondence: the 80.20–83.30 s Hard
images visibly contain a readable first Speed40 board, and offline replay of
the actual pixels finds 144 first-encounter detections at 45.55–83.30 s. The
association of that board with **Medium** handle49 was inferred by projecting
Medium geometry into Hard-run images; it does not identify a Hard scene object
and must not be used as runtime geometry. The 2.8 px projected-center match
only supports an image-space/camera mapping hypothesis. Hard handle47's
different transform does not label those pixels. No cause for the apparent
cross-scene geometric correspondence was established; its scene-object
identity remains unresolved. Accordingly, the older first-board semantic
pixel detection is retained, while its Medium-handle identity is withdrawn.
The later handle47 projections and red/white storefront ROIs remain candidates,
not object/pixel ownership evidence. No detector modification or live
controller run is justified by this identity audit.

Two follow-up preparations failed before processing any controller frame; neither
is behavioral evidence. The first exact command incorrectly invoked child mode:
`rehearse_groundheading_dense.py Hard runtime-identity-dense --controller
--tmax 300 --scene-path /private/tmp/task3-dense-camera/Task_3_Hard_HEAD.ttt`.
It waited for the parent-created `start-controller` file and exited 1 with
`TimeoutError: Harness did not release controller after engine startup`;
`capture-stats.json` reports attempted/accepted/written = 0. Its source copy,
hash and logs remain in `/private/tmp/task3-dense-camera/runtime-identity-dense/`.

The second used the correct parent entry point, without `--controller`, and
loaded the same isolated scene. The controller-ready handshake succeeded, but
the parent `sim.startSimulation()` RPC timed out after its 15 s socket timeout
with `zmq.error.Again: Resource temporarily unavailable`; the parent exited 1
before writing `start-controller`. The ready child then timed out waiting for
that signal and logged `0 frames processed`; its capture stats are all zero.
During the API timeout the engine did start and advanced unattended with both
motor targets zero. A fresh bounded client read state 17 at 616.50 s and both
targets zero; I stopped the simulation through the API. Final API state is
stopped at 616.65 s, both motor targets zero, scene still the isolated HEAD
Hard path. No process was killed and the dirty workspace scene was untouched.
Artifacts/source copy are preserved in
`/private/tmp/task3-dense-camera/runtime-identity-dense-parent/`.

No further launch was made after this second zero-frame preparation failure.
No task source or tests changed. The current source hash remains
`ea3a4954d97dcced427beac4cf379b6a6bce64b6c20e0a732a4602135f6a7da8`.
The simulator start/ready handshake failure and second-sign discrimination
remain open; the captured pre-start/runtime/stopped object snapshots remain the
only new runtime-identity evidence.

### November 13 — Luna integrated oblique candidate, run result

Source hash `d3322413c3261e12935970692144b8eced8457daa800b297d8c739cff38fc2b2`. Corrected ellipse axes retain OpenCV angle/radius pairing. Embedded original-camera crop regression replaced the invalid already-warped fixture; 79 tests passed, compilation and scoped diff whitespace checks passed. Valid-travel integrated replay consumed all 954 frames, entered45.75 and exited132.20; recorded wheel-velocity integration approximates commanded travel. Artifact: `/private/tmp/task3-luna-sagan-v4/integrated_valid_replay.json`.

Live clean Hard finished rc0: entry45.00, exit131.70, Hospital rest27.65–32.90, parking start160.45, parked180.90, harness end181.70. Camera terminal estimate forward0.198611m, lateral−0.005091m, heading−0.019798rad; these are camera estimates, not independently verified physical parking measurements. Evidence `/private/tmp/task3-dense-camera/oblique-structural-final/`. Post-run saved API check stopped182.15, both motors0. Source unchanged since replay. Timing exceeds180 by0.90s; no acceptance/readiness claim.

Execution deviation: selected resilient harness retained dense capture (663 frames, zero drops), despite the requested LIGHT/no-new-dense constraint. This run must not be described as light instrumentation. No further run launched. Physical parking, scored Hospital patch/collision/off-road evidence and repeated arena acceptance remain unverified.

### November 13 — genuine light harness verification

Unchanged d3322413c3261e12935970692144b8eced8457daa800b297d8c739cff38fc2b2. Saved prior-run physical audit (`oblique-structural-final/physical-audit.json`) uses root local +Z: center-forward0.20645m, front-lateral−0.00591m, heading−0.748deg; all original bounds pass, completion bracket0.50s. Hospital27.65–32.90 duration5.25s; pickup patch unknown.

Temporary `rehearse_light.py` removes dense capture/thread, periodic screenshots, scene identity queries, per-frame geometry, and redundant perception. Saves only confirmation-frame copies after control ends, per-frame commands/events, and one terminal truth snapshot. Config saved before run. Clean reset-pose/zero-motor handshake verified. Actual light run `/private/tmp/task3-dense-camera/oblique-light-1`: entry45.45, NO exit, parking200.55, parked240.40, harness end241.40, controller rc0. Hold27.85–33.15. This is a perception/temporal robustness failure; do not tune speed to compensate or claim reliable180s. Initial cleanup timed out (`Again: Resource temporarily unavailable`); fresh bounded recheck confirmed stopped241.75, motors0 (`cleanup-recheck.json`). No duplicate controller or further run.

### Luna robustness and timing continuation (November 14)

Parallel weak/spatial confirmation now observes the same raw sequence as SignTracker, with release explicitly gated on confirmation. This removes an accidental third-observation requirement without allowing a single raw observation to release. The complete954-frame replay uses timestamped approximate command-travel integration; entry45.75/exit132.00. `/private/tmp/task3-luna-sagan-v4/parallel_valid_replay.json` and timeline retain exact evidence. Raw light edge regressions include dropout and inconsistent-box rejection.

LIGHT runs (all failures retained; no dense capture):

| Run | Hash prefix | Entry / exit | Parked | Terminal physical forward / front lateral / heading | Outcome |
| --- | --- | --- | --- | --- | --- |
| oblique-parallel-light-1 |833cbe7|45.70 /132.65|183.15|.204881 /.009071 /-.431deg at184.90|Pose/caps pass, timing fails|
| oblique-roi-light-1 |da03aea|48.60 / see controller log|188.35|.204855 /.002748 /-.165deg at190.10|Pose/caps pass, timing fails|
| oblique-path-light-1 |724e980|45.80 /132.05|181.55|.206610 /.002879 /2.105deg at182.60|Pose/caps pass, timing fails|

All artifacts are under `/private/tmp/task3-dense-camera/<run>/`. Physical snapshots are after parked events; not exact instantaneous completion truth. Fresh bounded API recheck for path-light-1 found stopped182.90 and motors[0,0], saved cleanup-recheck.json. Hold location/collision/offroad remain unverified; these are development rehearsals, not official evaluation.

ROI morphology preserves outputs exactly on979 dense+light-window frames and reduces measured offline detector time3.52→1.96s. This does not establish live timing causality. Parking command replay matches saved commands exactly. Quintic fallback at one handoff predicted33.982deg marker bearing while cubic27.575deg narrowly missed27.5deg reserve. A bounded extended cubic is now considered only when it satisfies the original bearing/curvature reserves and leaves2cm aligned travel before nominal center. Final tolerances, stopping, heading confidence, hold and caps unchanged. Different handoff poses/frame pacing prevent attributing improvement to this alone.

Current additional correction preserves camera-derived estimator history across parking handoff, instead of rebuilding an assumed-parallel estimator each observation and discarding its state at commitment. A regression verifies nonzero yaw preservation, no duplicate solve, and that missing corners reset readiness even if an estimator returns stale valid data.83 tests passed. LIGHT handoff test is in progress; not acceptance. Remaining repeatedHard/Medium/Easy and official scoring/handoff scope is unchanged.

Handoff continuity candidate `288538e0fee5c1dfb9499397f1821cefe1e551368873cded8e8d5465bf157c6b` was rejected: LIGHT `oblique-handoff-light-1` entered parking164.80 atforward.60, then stopped with invalid alignment, rc1. It did not finish successfully. Cleanup stopped193.45/motors0. Restored original per-frame entry estimator from724e980; rejected source and83-test snapshot retained under temporary evidence. Current82 tests retain all baseline and accepted perception/path regressions. No readiness/pose tolerance was relaxed to rescue the failed candidate.

Next constrained path experiment selects the extended cubic only when it lowers both predicted peak curvature and bearing, while satisfying the unchanged safety reserves. It now considers that improvement even when the shorter cubic is already feasible. This specifically exercises the extension not triggered in path-light-1. Runtime file/hash and LIGHT outcome will be recorded in oblique-safer-curve-light-1. No successful timing claim yet.

### Scored-constraint audit, conservative baseline repeat

Rejected broader cubic selection and one-frame prediction-speed policy after no timing benefit; current source exactly724e980, conservative unknown-yaw cap restored. Baseline82tests pass. Sparse diagnostic rehearsal `baseline-scored-audit-1` missed the second sign and remained capped through parking: parked236.25, not acceptance. Terminal239.15 physicalforward.206222/frontlat.004165/heading.112deg passes; cleanup stopped239.50/motors0. This reveals continuing frame-pacing sensitivity. All failures preserved.

The independent sampled audit used no dense camera recording and no world information in controller.112 root/wheel samples, max temporal span.10s and max unsampled gap2.70s. No sampled9cm-square obstacle overlap; min clearances.10121/.08519/.10100m. Min wheel-center signed road clearance−.003662m; no sampled center exceeds1cm outside, but tire envelope and unsampled intervals remain uncertified. Hospital controller-rest samples28.85–33.90; no named pickup geometry, containment still unknown. These are limited diagnostics, NOT official scoring proof. Scripts and floor mesh/UV texture in `/private/tmp/task3-luna-scored-audit/`; reports/overlay in run directory.
