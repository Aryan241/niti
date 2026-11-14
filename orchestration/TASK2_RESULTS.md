# Task 2 results

Date: 2026-10-19

## Scope and files

Implemented or preserved the allowed implementation blocks in:

- `task2a/task2a.py`
- `task2b/sign_obstacle_detection.py`
- `task2c/task2c.py`

Also restored `orchestration/WORK_ORDER.md` and created this report. The commented Task 2B copy at `task2b/sign_obstacle_detection_with_comments.py` was preserved. No portal upload was performed.

## Implementation summary

Task 2A detects yellow outer and white dashed lane boundaries from the BGR image, fits lane-line models, chooses the current lane without hard-coding its side, and tracks the lane midpoint at near and far image rows. Control uses one virtual centre steering angle, clamps it before the Ackermann split, and uses the provided geometry with an effective kingpin width of 0.055 m. The virtual limit is approximately 39.1 degrees, keeping both wheel angles within the 45-degree limit. Stop handling is level-based and returns zero speed on every held stop frame. Invalid detections use a bounded speed fallback and stop after eight consecutive invalid frames.

Task 2B retains the colour/component and template-based detector. It returns the required sign labels and integer pixel areas, supports mixed sign/obstacle images, and leaves the primary file without added explanatory comments as requested.

Task 2C uses only the supplied pose dictionary. It plans a smooth lateral transition whose endpoint is 0.43 m, ahead of the 0.37 m bay mouth, then approaches the 0.19 m parking target straight. It requires lateral and heading alignment, a conservative vehicle-footprint check, and eight stable good frames before returning `parked=True`. Intermittent marker loss is tolerated without resetting a recently confirmed parking state; a much longer bounded loss still falls back to a full hold. The larger documented lateral start receives a modest steering-scale reduction. The front-axle lateral convention and vehicle-centre forward convention are kept separate.

## Commands and offline outcomes

Passed:

```text
/Users/aryanachary/.venv/bin/python -m py_compile task2a/task2a.py task2b/sign_obstacle_detection.py task2c/task2c.py
git diff --check
```

Task 2A smoke test over all 20 public Task 1C clips, sampling 10 frames per clip:

```text
clips 20 samples 200 valid 200 finite+immutable 200
```

Task 2A controller checks passed for right/left upcoming-curve signs, finite Ackermann outputs below 45 degrees, held stop speed zero, and invalid-frame fallback stopping after eight frames:

```text
2A controls: PASS; right/left sign, Ackermann bound, held stop, bounded invalid fallback
```

Task 2C forward-kinematic checks used documented approximate starts `(lateral, forward) = (0.22, 1.04)` and `(0.44, 1.04)`, heading zero, and the supplied pose convention. Both reached the target. At the mouth, footprint error was 0.0067 m and 0.0158 m respectively, below the conservative 0.016 m threshold; final poses were within the lateral, heading, and forward acceptance bounds. The bounded initial marker-loss check also passed:

```text
2C (0.22, 1.04) PASS (-0.0064, 0.0027, 0.3695, 0.0067) (-0.0049, 0.0091, 0.202) 1000
2C (0.44, 1.04) PASS (-0.015, 0.0067, 0.3697, 0.0158) (-0.0115, 0.0215, 0.2019) 1152
2C bounded loss PASS
```

These are controller-model checks, not a substitute for the private portal score.

## Official local evaluator outcomes

Task 2B was run with:

```text
cd task2b
/Users/aryanachary/.venv/bin/eyantra-autoeval evaluate --year 2026 --theme NV --task 2b
```

All 11 public images ran cleanly. The evaluator reported:

```text
40_1.png Speed40 1357 N 0
40_2.png Speed40 4856 N 0
40_P_1.png Parking 2552 N 0
40_P_1.png Speed40 1238 N 0
Blank_1.png (none) - N 0
H_1.png Hospital 3956 N 0
Obs_1.png (none) - Y 12452
Obs_H_1.png Hospital 6168 Y 4536
Obs_H_2.png Hospital 1152 Y 1460
P_1.png Parking 1259 N 0
Sc_1.png School 2622 N 0
Sc_2.png School 1601 N 0
```

The tool explicitly states that this is a public detection record and does not compute marks; the private portal grader determines Task 2B marks.

Task 2A was run after loading `task2a/Task_2A.ttt` into the local CoppeliaSim instance on port 23000:

```text
/Users/aryanachary/.venv/bin/python -c '...sim.loadScene(".../task2a/Task_2A.ttt")'
cd task2a
/Users/aryanachary/.venv/bin/eyantra-autoeval evaluate --year 2026 --theme NV --task 2a
```

The retained complete attempt completed the outer-lane run with 2945 samples over 343.95 s of simulation and both stops signalled/released. The inner-lane run reached 13,795 samples over 1,198.55 s of simulation but stalled near `x=-0.909, y=0.908`, raised no stops, and ended as `the simulation stopped unexpectedly`. A later rerun could not produce a new recording because the GUI instance stopped immediately after the harness handshake. Therefore Task 2A has partial simulator evidence only, not a complete passing local run result.

Task 2C was run after loading `task2c/Task_2C.ttt` into the same local instance:

```text
cd task2c
/Users/aryanachary/.venv/bin/eyantra-autoeval evaluate --year 2026 --theme NV --task 2c
```

The first complete attempt reported:

```text
bay 0: parked - 783 samples over 79 s of simulation
bay 1: timed out - 1225 samples over 120 s; script never reported parked
```

The recordings were written as `task2c/NV_Task2C_bay0.csv` and `task2c/NV_Task2C_bay1.csv`. Inspection of the bay-1 recording showed the vehicle near the longitudinal target but with heading approximately 0.32 rad; the forward guard then held it rather than falsely claiming success.

After the focused larger-start steering correction, a second bounded attempt again parked bay 0 (875 samples over 77 s), then was interrupted during bay 1 before files were written for that attempt. This does not establish that the correction fixes bay 1. The retained first-run recordings remain the authoritative complete Task 2C evidence; their script hash predates the current Task 2C file, so they are historical evidence rather than current-code evidence.

A later direct controller run with the current code parked bay 0 after 722 frames. A bay-1 run placed the vehicle visually in the bay, but the marker was seen in only 3,029 of 14,904 frames and the controller did not return `parked=True`. The current code now preserves good-frame evidence across short marker gaps and allows a longer bounded recovery window. A final official-evaluator retry could not be completed because the long-lived simulator's remote API became unresponsive during restart; no current-code Task 2C evaluator score is claimed.

## Simulator and portal limitations

CoppeliaSim was available at:

```text
/Users/aryanachary/Documents/coppeliaSim.app/Contents/MacOS/coppeliaSim
```

The local ZMQ Remote API on port 23000 accepted scene loads and evaluator connections during the earlier Task 2A/2C attempts. The application emitted an embedded Python-addon `cbor2`/`cbor` import warning during launch. During the final Task 2C retry the long-lived instance stopped responding on that port, so the evaluator reported `No response from CoppeliaSim on localhost:23000`. Long 2A/2C runs were bounded to avoid leaving an unattended evaluation running indefinitely.

The logged-in portal dashboard was readable and showed Task 2A = 40 marks, Task 2B = 40 marks, Task 2C = 20 marks, one shared team solution, and leader-only submission. Direct instruction pages rendered blank in the native browser session, so technical requirements were taken from the local official READMEs, templates, evaluator output, and the supplied task files. No full-mark claim is made.

## Boundary and diff review

`git diff --check` and compilation passed. The implementation diff is confined to the three named Task 2 implementation areas; the provided simulator harnesses and code below the implementation markers were not changed. No submission upload, scene edit, dataset edit, or scoring-logic edit was performed.

Remaining risk is the incomplete current-code simulator evidence for Task 2C bay 1: the first complete run timed out, and the later visual run stopped in the bay without returning `parked=True` before the simulator API became unavailable. Task 2A now has complete local two-lap evidence, while the offline checks pass for the remaining work.

## Final verification checkpoint

The 2A controller was corrected so `valid=True` detections with missing, malformed, or non-finite fields use the same eight-frame bounded invalid path as `valid=False` detections. A nine-call malformed and non-finite test ends at zero speed. The current Task 2B evaluator was rerun after the recorded Task 2A/2C attempts and still matched all public cases. No portal submission was made.

## Sharp-curve correction

The Task 2A detector was then tested against the supplied curve footage. On a sharp bend, the visible outer yellow boundary fragments and the stateless pairing briefly changed the lane estimate from about 205 px to 535 px, which reverses the steering direction and explains the vehicle leaving the road. The detector now keeps the lane identity fixed for the controller run; an opposite-side candidate is treated as uncertain and cannot reverse steering. During that ambiguity the controller holds the last geometrically valid estimate and caps speed at `0.28 rad/s`, allowing the lane evidence to recover instead of freezing the lap. The controller also uses stronger near/curvature gains and reduces speed at the strongest turns. The 20-clip smoke test still reports 200/200 valid, finite, immutable samples. The official local evaluator then completed both laps with the current code: outer `2,838` samples and inner `4,034` samples, with `2/2` stop signals on each lap. The recorder writes evidence only; it does not calculate the portal score.
