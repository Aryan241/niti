# Sol orchestration handoff — 2026-11-12

Objective:
Finish Task 3 under Sol orchestration/review and Luna implementation/testing. Worker nickname is incidental. Prefer existing worker `01a1caad-6c46-7780-8526-e46ca2919328` when authoritative status supports reuse; avoid duplicate simulator ownership and never restart live work solely because a wait timed out.

Files:
Implementation remains scoped to `task3/task3.py`, `orchestration/check_task3.py`, `orchestration/TASK3_RESULTS.md`, and the resume checkpoint; temporary diagnostics belong in `/private/tmp/task3-followup.ZNTHv6`. Read the runtime-finish and final work orders as the governing scope.

Constraints:
Preserve dirty scenes and unrelated files. No simulator truth in control, weakened parking tolerances, scene edits, portal submission, or push. Identified simulator restart without saving is authorized when needed. All implementation and testing stay with Luna. Supported Windows/Ubuntu official recording remains external.

Current review:
Latest evidence supersedes the original review below. Source `287b1fc860a30b4b3873dcf49260b0be5bbe392d091bd172b28ea785b1378f03` uses the effective global 3.0 cap, zone 1.2 cap, and uncertain-heading edge stop. `runtime-global3-effective-hard-1` parked at 182.60 s; recorded command maxima were 2.9998706 globally and 1.2 in-zone. The terminal .35 rad/s cap below .24 m (source d7e99...) parked once at 183.10 s, then `runtime-terminal-approach-hard-2b` lost pose and remained unfinished at 300.75 s. That experiment was reverted. Earlier edge-stop source b361... parked at 181.25 s, but repeat reliability is unproven; an isolated successful park does not resolve the recurring marker loss. Regression count was 61 after the revert; the temporary terminal-cap branch had 62.

Critical diagnostic correction: the old harness records root Euler Z as yaw, but the root is tilted about 90 degrees. Near-constant Euler Z is not proof of constant ground heading. `rehearse_groundheading.py` now records raw root/camera matrices, target marker matrices, PnP observations, steering positions and edge frames, all diagnostic-only. `runtime-groundheading-hard-2`, source 287b..., parked at 185.50 s. Projected root local-Z and camera local-Z into XY agree: actual internal-sign heading reaches about 44.6 degrees at t=175 s, with fused estimate 43.6 degrees. Thus the vehicle genuinely turns; previous straight-vehicle/estimator-inconsistency claims based on Euler Z need correction. There are rejected raw-PnP outliers. Final image forward .20877 m versus root-to-marker-normal distance .21563 m requires reference-point/calibration review before independent strict-pose certification.

Next critical path: Luna must use the valid transform/PnP/steering records to diagnose actual path and visibility, address recurring edge loss, and establish reliable completion before further runtime tuning. Existing zero-on-loss protection and strict parking/hold/speed requirements remain. Do not add blind guard margins or terminal speed knobs. Preserve failed runs and distinguish diagnostic truth from camera-only control. No final-source Hard repeat pair <=180 s or Medium/Easy acceptance exists yet.

The edge-stop branch in `_adaptive_speed` returns zero when heading is unobserved and angular bearing margin is below 15 degrees. This is a safety guard, not evidence of recovery or completion. Persistent ambiguous observations at a stationary pose may leave the condition unchanged indefinitely; establish the actual behavior rather than assuming a stop fixes the prior stall. The saved `runtime-marker-edge-regression.out` has 59 passing tests, with no focused edge-stop test listed. `runtime-marker-edge-hard-1` was empty at this review. Neither is live completion evidence. The checkpoint and results document predate the latest failure and patch.

Acceptance criteria:
1. Return an immediate factual worker/run status and diagnosis from saved 168.10–168.70 s frames of `runtime-finish-bend-hard-1`. Distinguish raw marker/PnP observations, filtered yaw, and independent diagnostic truth. That run failed with permanent pose loss and no completion through 300.15 s.
2. Add focused behavioral coverage for uncertain near-edge stopping, fresh-yaw recovery/resumption where supported, persistent ambiguity without false success, and retained immediate marker-loss stop. Demonstrate how the established failure is prevented without merely replacing motion with an indefinite stall. Implement the smallest evidence-supported correction.
3. Complete at least two Hard runs at or below 180 simulation seconds, two Medium runs and one Easy run on the exact final source. Preserve failures and empty startup attempts. Verify strict fresh-camera parking/stillness, actual Hospital rest >=5 s, commands <=3 globally and <=1.2 in the zone, and available collision/offroad evidence with explicit limits.
4. Update results and checkpoint with source SHA256, exact commands, run tags, final poses/times, holds, command maxima, limitations and remaining official-recording requirements. No readiness claim until criteria are met.

Verification commands (Luna only):
Use `/Users/aryanachary/.venv/bin/python orchestration/check_task3.py`, syntax checks and scoped diff checks. Full live harness invocation is `/Users/aryanachary/.venv/bin/python /private/tmp/task3-followup.ZNTHv6/rehearse.py Hard UNIQUE_TAG`, with corresponding Medium/Easy runs; never use top-level `--controller`. Simulator API calls require elevated localhost access and bounded 3 s send/receive timeouts. Serialize simulator ownership and copy clean scenes from HEAD into temporary storage only.

Expected evidence:
Focused diagnosis and regression names/results, exact tested source hash, complete run summaries and artifact paths, scoped diff, and an honest remaining-blocker list. Sol reviews that evidence before accepting completion.

Dispatch status:
The parent chat is now Sol and has dispatched this work to existing Luna worker `01a1caad-6c46-7780-8526-e46ca2919328`. It remains pending on the latest poll; no duplicate executor was started. Earlier child-Sol session lacked dispatch tools and returned its written review; that historical limitation no longer blocks parent orchestration. Worker nickname is not a user constraint. Parent does not implement or run the simulator. Luna owns the execution loop; Sol reviews saved evidence.
