# Task 3 review work order

Objective: Critique and fix the existing integrated Task 3 controller against the user-supplied Task 3 instructions. Astra reviews; Luna implements and verifies. Preserve working perception and driving behavior unless a concrete defect requires change.

Files: `task3/task3.py`, `orchestration/check_task3.py`, and append a clearly dated review section to `orchestration/TASK3_RESULTS.md`. Record evidence separately from earlier agent claims.

Constraints: All submitted logic stays in `task3.py`, importing no other team scripts. Only images, simulation state/time and commanded actuator history may inform decisions. No privileged scene/vehicle pose or speed reads, vehicle teleportation, scene edits, or starting/stopping simulation in the solution. Preserve all dirty scene and Task 2 files. Do not push or submit. Test helpers and reports stay out of submission.

Findings to fix:
- Speed-zone onset currently waits for a close sign despite the rule to slow on first sight. Debounce distinct sign encounters so one sign cannot immediately toggle the zone off on a flicker. Current `zone_done` permanently keeps the cap and parking always caps at 1.19; implement correct release after a distinct second sign, retaining a conservative cap if exit remains unconfirmed.
- Hospital stationary timer currently starts on a timeout even without rest evidence, and never resets if movement resumes. Require continuous visual stillness for the full simulation-time hold; reset accumulated hold on movement. Retain pickup approach logic unless evidence justifies change; report its scene-specific calibration and fragile far-only arming assumption.
- Parker reports success based solely on forward distance or blind commanded-speed integration, even if lateral/heading are grossly wrong. Gate success on valid finite pose, lateral/heading/forward tolerances and stable stopped visual observations; overshoot without alignment is failure, not success. Bound marker-loss motion by elapsed simulation time/distance; never claim parked from odometry alone. Account for actual capped command (including mission frame-rate/zone caps) in parking integration.
- Clamp path derivatives outside the active path interval: clamped position with nonzero extrapolated curvature is inconsistent. Handle malformed pose/PnP failures without motion or false success.
- Prevent parking before earlier tasks are complete. Use evidence of zone traversal and obstacle encounter/pass state where feasible; do not hardcode obstacle count/layout/times to force a mission sequence. Report remaining perception limitations. Reset parking streak on invalid or absent markers.
- Fail safely on absent images and propagate runtime errors with nonzero exit. Handle pause/resume without confusing pause with simulation termination; exit on stop; no stale moving command during invalid images.

Acceptance criteria: Focused deterministic regression tests reproduce major baseline defects and pass after fixes; include first sight speed cap, retained cap, distinct second sign release, flicker protection, Hospital movement reset, rejected misaligned/overshot parking, stable aligned parking, marker loss, capped speed history, PnP edge cases, missing frames, runtime failure handling. Verify finite bounded wheel/speed outputs, single-file imports and forbidden API absence. Do not claim full lap, scoring or submission readiness from offline tests.

Verification: Use `/Users/aryanachary/.venv/bin/python` after checking installed packages; unittest or an equivalent standard-library helper, syntax compile and `git diff --check`. Coordinate simulator access with Astra, who is checking availability separately; do not run simultaneous controllers. Document exact checks and limitations.

Expected evidence: Changed paths, concise defect explanations, baseline repros if possible, test counts/outcomes, self-reviewed diff, and explicit simulator/official evaluation status. Return a final report; Astra performs a final review and requests only focused corrections if necessary.
