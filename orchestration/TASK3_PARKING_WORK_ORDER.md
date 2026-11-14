Objective:
Fix intermittent parking and the remaining Hard runtime penalty. Preserve the verified exit-sign improvement. This is implementation work, not another closeout. Target repeatable Hard completion within 180 simulation seconds, without weakening halt, speed or parking checks.

Files:
task3/task3.py; orchestration/check_task3.py; orchestration/TASK3_RESULTS.md. Diagnostic scripts/data belong in /private/tmp. Preserve unrelated changes and all scene files.

Constraints:
Luna model executes; Astra reviews. Read AGENTS.md, LUNA.md and supplied Task3 instructions. Camera-only submitted controller, single file, no simulator ground truth/start/stop/scene edits. Diagnostic harness may read geometry and control simulation, but must never supply ground truth to the solution. No hardcoded route timing/coordinates, fabricated exit, tolerance relaxation, commit/push/submission. Keep baseline 9db627 and failed-trial evidence. User explicitly permits restarting the stalled simulator without saving; no repeated approval needed. Keep diagnostics focused to conserve credits.

Investigation and implementation:
1. Reuse existing traces in /private/tmp/task3-followup.ZNTHv6. Do not repeat prior failed acceleration-only tuning or assume initial yaw is the cause: saved-frame comparison did not support it.
2. Test coordinate consistency first. PoseEstimator returns front-axle lateral offset but vehicle-centre forward distance. Parker subtracts WHEELBASE*sin(heading) from lateral to control a rear-axle point, while path/reference derivatives use centre-forward distance. Derive/test a consistent rear-axle state and path: rear_lateral = front_lateral - WHEELBASE*sin(heading); rear_forward = centre_forward + WHEELBASE/2*cos(heading). Shift goal/merge geometry consistently rather than changing the physical parking target. Confirm signs with synthetic projected marker poses and a bicycle-model closed-loop check before live tuning. Treat this as a hypothesis until measurements establish its effect.
3. Check path feasibility and guard conflicts. Outer path's planned heading may be allowed by heading_limit but still opposed by fixed bearing guard .55 rad. Compare planned curvature against actuator limit and actual marker image-edge margin. Any guard change must keep the marker visible; use evidence, not blanket removal.
4. Diagnose estimator/control lag with frame timestamps and actual capped command history. The .01m visual-distance increment cap and .6/.4 range filter must be accounted for at higher speed. Do not blindly trust raw ambiguous PnP yaw. Diagnostic camera/marker matrices can establish pose error; car Euler yaw alone is not a reliable reference without coordinate calibration.
5. Implement the smallest supported geometric/controller correction. Use a speed schedule constrained by measured tracking error, remaining correction distance, marker visibility, frame delay and braking distance. A fixed high speed plus a late slow ramp already failed. Do not wait until entering the final window to address substantial lateral/heading error.

Acceptance criteria:
- Preserve first-sight speed cap, distinct exit confirmation, continuous Hospital rest >=5 simulation seconds, strict parked pose/stillness checks and immediate zero on marker loss.
- Focused offline tests must demonstrate the identified defect and correction, not just repeat implementation formulas. Existing regression suite must pass; no reading huge embedded base64 fixture dumps unnecessarily.
- Validate final source on Hard twice and Medium twice (intermittency), plus Easy once. Record exact hash, exit/hold times, final errors and completion. Retain all failures. Target Hard <=180; if still above, report measured residual without claiming success or silently ending with known failed code.
- Inspect live camera trajectory and available diagnostic collision/road evidence; never equate a parked flag with official penalty-free certification.

Verification commands:
/Users/aryanachary/.venv/bin/python orchestration/check_task3.py
Compile changed Python; scoped git diff --check.
Reuse /private/tmp/task3-followup.ZNTHv6/rehearse.py ARENA TAG WITHOUT --controller. The full harness loads/starts/stops; --controller alone waits indefinitely. Use require_escalated for localhost API. Set zmq.RCVTIMEO=3000 before getObject for health queries. If stalled, restart the identified Coppelia process and reopen isolated clean scene; installed app /Users/aryanachary/Documents/coppeliaSim.app. Avoid CUA calls that previously hung.

Expected evidence:
One concise causal finding before a new tuning sweep, implementation diff, offline checks and exact final live evidence in TASK3_RESULTS.md. Own the full debug/verification loop without routine approvals. Report material milestones rather than leaving the parent to poll blindly.
