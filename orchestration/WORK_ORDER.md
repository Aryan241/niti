# Current handoff — Astra Task 3 completion

Immediate execution: Luna Sagan (`01a1d198-1afa-7191-a8c3-b61fecc656bf`) owns
[TASK3_OBLIQUE_FIX_WORK_ORDER.md](TASK3_OBLIQUE_FIX_WORK_ORDER.md). Prior worker
Zeno is closed. The latest confirmed driving run parked at237.65s; no production
sign fix is validated. Use saved954frame evidence, not another dense run.
November13 checkpoint: Sagan reports no live processes and no source changes;
complete-stream candidate/tracker replay is still pending. Usage error occurred
earlier, but latest checkpoint reports offline tools executed. Do not assume
the limit remains active without a fresh failure.

Astra owns orchestration and review; Luna executes the full [TASK3_ASTRA_FINISH_WORK_ORDER.md](TASK3_ASTRA_FINISH_WORK_ORDER.md). Read the latest [TASK3_RESUME_CHECKPOINT.md](TASK3_RESUME_CHECKPOINT.md). The original [TASK3_FINAL_WORK_ORDER.md](TASK3_FINAL_WORK_ORDER.md) scope and acceptance remain intact. Earlier work orders are historical evidence, not repeated phase barriers. Preserve the earlier Task 2 handoff below.

# Earlier work order — Task 2A, 2B, and 2C

## Handoff

Role: Luna executor. Astra owns the final diff and evidence review after Luna completes the implementation and verification loop.

Objective: implement, debug, and verify all Niti Vahan Task 2 subtasks:

- Task 2A: image-only lane perception, centered lane tracking, Ackermann steering, and level stop handling.
- Task 2B: sign and obstacle detection from BGR images.
- Task 2C: marker-pose-based parking into both bays.

No portal upload is authorized. Submission remains a deliberate team action.

## Allowed files and preservation rules

Implementation changes are limited to the allowed implementation blocks of:

- `task2a/task2a.py`
- `task2b/sign_obstacle_detection.py`
- `task2c/task2c.py`

Luna may update this work order and create/update `orchestration/TASK2_RESULTS.md`, plus concise local test helpers under `orchestration/`.

Preserve the supplied boilerplate, harness, scenes, input datasets, scoring logic, and unrelated tasks. Preserve the user’s commented Task 2B backup at `task2b/sign_obstacle_detection_with_comments.py`. Do not add explanatory comments to the primary Task 2B file; the user intentionally removed them. Keep generated reports and temporary outputs outside submission source files.

## Sources and portal evidence

- Read `AGENTS.md`, `orchestration/LUNA.md`, all three Task 2 READMEs, the three task templates, installed evaluator sources, `task1a/ackermann_steering.py`, `task1c/README.md`, and the Task 1C public clips.
- The logged-in portal dashboard is readable and confirms Task 2A = 40 marks, Task 2B = 40 marks, Task 2C = 20 marks, one shared team solution, and leader-only submission.
- Direct live instruction pages rendered blank in the current Chrome session. Use local official files and evaluator source for technical requirements and report this limitation.

## Task 2A

Implement only `detect_lane(frame)` and `compute_control(detection, stop_requested)`.

- Input is a corrected BGR camera frame. Both outer and inner lanes are evaluated and the arena is mirrored; infer the lane from the image.
- Track the middle of the current lane, not just the correct side of the dashed divider. Use Task 1C clips as rendered perception smoke samples, not ground-truth simulator accuracy.
- Use image-only state. Do not query simulator pose, move the vehicle, or start/stop simulation.
- `stop_requested` is a level: while true, speed must remain exactly zero every loop iteration while frame processing continues.
- Handle temporarily unusable frames with bounded fallback steering and reduced speed.
- Compute one bounded virtual centre steering angle, then apply Task 1A Ackermann geometry. With `L=.120`, effective kingpin width `.055`, the virtual centre bound implied by both wheel angles staying within 45 degrees is about `atan(.120/(.120+.055/2)) = 39.1°`; clamp before the split and preserve geometry.
- Return finite floats for both wheel angles and speed, with bounded speed.
- Do not modify the provided simulator loop or forbidden calls.

## Task 2B

Keep the valid existing implementation unless evidence requires a correction.

- Allowed labels: `School`, `Speed40`, `Parking`, `Hospital`.
- Return one dictionary per visible sign with integer pixel area; obstacle area is zero when absent.
- Support zero, one, multiple, mixed sign/obstacle, and obstacle-only images.
- Grader supplies reference images beside the script. Review existing hard y/ratio/size thresholds for overfitting but do not change them without evidence.
- Public expected labels: `40_1`/`40_2` Speed40; `40_P_1` Parking plus Speed40; `Blank_1` none; `H_1` Hospital; `Obs_1` obstacle only; `Obs_H_1`/`Obs_H_2` Hospital plus obstacle; `P_1` Parking; `Sc_1`/`Sc_2` School.
- The public evaluator checks structure/runtime but does not calculate marks. Confirm area definition from local requirements and report hidden-image area uncertainty.
- No print/display/write calls inside detector functions.

## Task 2C

Implement only `parking_manoeuvre(pose)`.

- `pose` is `None` or contains `lateral`, `heading`, `forward`, and `bearing`.
- Use only this supplied pose. Do not query privileged simulator pose or objects from the controller.
- `lateral` is front-axle offset from bay centre, positive left. `heading` is relative heading, positive left. `forward` is vehicle-centre distance to marker line. `bearing` is marker direction, positive left.
- Bays are `.22 m` wide, vehicle `.18 m` wide. Align lateral and heading before the `.37 m` mouth, then settle near `.19 m` and stop.
- Handle transient marker loss with bounded memory/fallback. Avoid one-frame parked decisions; use stable convergence/hysteresis.
- Work for both bay IDs, finite bounded steering/speed, and approximately 95° camera FOV. The supplied estimator primarily models forward distance; do not assume unavailable reverse-distance data.
- Clamp virtual steering before the provided Ackermann split using the same physical bound as Task 2A.
- No print, plot, input, or simulator calls inside `parking_manoeuvre`.

## Verification

1. Syntax/import checks, `git diff --check`, and marker-boundary review with `git show HEAD:<file>`.
2. Run the installed official evaluator from each task directory using `/Users/aryanachary/.venv/bin/eyantra-autoeval evaluate --year 2026 --theme NV --task 2a/2b/2c` where supported. The 2A/2C evaluator records and does not score locally.
3. Inspect CoppeliaSim with bounded `/Applications` inventory/executable/open checks. If scenes can run, own the simulator serially: both Task 2A laps and both Task 2C bays. If not, report the exact blocker; do not claim simulator success from synthetic checks.
4. Run meaningful offline checks: both-side lane samples, finite Ackermann outputs and pre-split bounds, held stop and resume, Task 2B all public images/validators/immutability/perturbations, and Task 2C both-bay pose perturbations, marker loss, hysteresis, finite bounds, and immutability.

## Prior Task 2B evidence

The earlier baseline passed the installed public evaluator on all 11 public images:

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

## Report

Create `orchestration/TASK2_RESULTS.md` with changed files, decisions, exact commands/outcomes, portal/source evidence, simulator availability/blockers, public/offline results, area/trajectory uncertainty, and final self-review. Never state full marks unless the portal has graded them.
