# Task 3 — consistent rear-axle path coordinates

Objective: remove the parking planner's mixed reference points, then measure one full Hard run. Sol reviews; Luna implements and tests. Keep the full final acceptance in TASK3_SOL_HANDOFF.md.

Evidence: current source a45b3001789e4dbcdd4bd881e725fae6981ca1b7df0cb61a3ad2d8a4175a4b38 passes 65 tests but has no live run. Prior calibrated source parked accurately at 192.55 s. Terminal crawl accounted for only .15 s; about 32.45 s elapsed before the physical forward window. Do not tune the crawl or speed caps from that result.

Files: task3/task3.py, orchestration/check_task3.py, TASK3_RESULTS.md and latest resume checkpoint. Temporary harness/analysis under /private/tmp/task3-followup.ZNTHv6. Preserve all scenes, unrelated changes and failed evidence.

Focused change:
1. Confirm pose conventions from the existing code/instructions: lateral is front-axle bay offset; forward is vehicle-centre distance to marker plane; heading is relative to bay. Steering currently uses rear lateral `lateral - WHEELBASE*sin(heading)`, but start_lateral is front lateral and reference progress uses centre forward. Establish the equations/signs before editing; report any contrary evidence.
2. Use one rear-axle coordinate frame for quintic initialization, progress and error: rear_lateral = front_lateral - L*sin(heading); rear_forward = centre_forward + L/2*cos(heading). Initialize both reference coordinates from the same first valid pose. Keep MERGE_END's existing physical centre-forward meaning by translating its rear-axle endpoint to MERGE_END + L/2 for the aligned endpoint. Do not merely shift all thresholds or use simulator/world coordinates. Keep terminal completion/braking on the existing centre/front pose convention; do not accidentally apply the rear offset twice.
3. Preserve the quintic shape, steering gains, yaw/frame/speed caps, edge prelimit, symmetric completion margins, forward calibration, Hospital hold, marker-loss zero and fresh-pose stillness checks. No extra gain/threshold experiments. If derivation shows this change is not valid, return that specific evidence rather than applying it blindly.

Verification: meaningful geometric regressions using both signs and nonzero initial headings; the first reference equals actual rear position, the aligned endpoint corresponds to centre MERGE_END, left/right reflection is consistent, and final completion semantics remain unchanged. Run the full existing regression suite, syntax and scoped diff checks.

Live: one full diagnostic Hard run on the exact patched source using the current controller-ready-handshake version of rehearse_groundheading.py, no top-level --controller. Verify scene/process state first; serialize ownership. Use /Users/aryanachary/.venv/bin/python with elevated localhost access and bounded timeouts. At most two bounded startup attempts; preserve them. An identified stalled simulator may be restarted without saving, but do not restart a responsive stopped scene unnecessarily. Do not subtract startup simulation time.

Evidence: exact diff/hash/checks, first-driving/parking-entry/parked absolute times, marker-frame physical centre-forward/front-lateral/heading versus image pose, actual Hospital rest, command maxima, full marker visibility/misses and path-tracking timing. Separate physical bay-frame coordinates from vehicle-frame bearing components. Root forward is local +Z, columns 2/6/10 in the row-major 3x4 matrix; target direction is opposite marker outward normal. Simulator data is diagnostic only. Report collision/off-road evidence limitations.

Return after this correction and one run, or a concrete bounded blocker. No portal, push, official-score or submission-readiness claim. Final completion still requires repeated Hard <=180 s, Medium twice, Easy once and supported-platform official artifacts.
