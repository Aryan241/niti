Objective:
Verify whether the current visibility-path candidate is repeatable before further tuning. This is intermediate verification; the full TASK3_FINAL_WORK_ORDER.md acceptance remains open.

Files:
Read task3/task3.py and latest TASK3_RESULTS.md/checkpoint. Do not change controller/tests. Update only results/checkpoint and temporary diagnostic harness/helpers when required for safe scene initialization or recording. Preserve all user-dirty scenes and unrelated files.

Baseline:
Source ee5f7a1407a328766e8ef115294d6ef8567508dcea615f7f57c221dd2358f387, 74 passing tests. visibility-cubic-hard-1 parked181.05, entry158.75; physical forward.205674m/front-lateral-.005138m/heading-1.954deg, Hospital rest5.40s, full-marker80/80 min64px. Visibility cap5.05s, uncertain-edge stop.90s. This is one unpaired run, not evidence of causal timing improvement or readiness.

Constraints:
Luna executes; Sol reviews. No source tuning, relaxed guards, scene mutation, clock subtraction, portal, push, or fabricated official artifacts. Simulator restart without saving is authorized only for the identified task instance. Serialize ownership; bounded socket timeouts before initial API request, discard timed-out REQ clients. Current ready-before-engine harness is /private/tmp/task3-followup.ZNTHv6/rehearse_groundheading.py. Never invoke top-level --controller. Temp truth is diagnostic only. Preserve failed artifacts. At most two startup attempts per arena; return a bounded blocker on failure instead of repeated restarts.

Execution:
1. Verify exact source hash and current stopped/reset/zero-target ownership. Run one unchanged Hard repeat with a new tag and --reuse-verified-hard-scene via /Users/aryanachary/.venv/bin/python, elevated localhost. Use absolute sim time and the existing 300s bound. Compare entry/park times and adaptive-cap exposures, physical terminal pose, marker misses/margins and Hospital rest with the baseline. Do not rerun the unchanged regression suite unnecessarily.
2. If Hard completes without a new safety/physical failure, run one clean Medium diagnostic on the same hash. Inspect current harness's scene selection first; load a clean HEAD Medium scene into the identified simulator without modifying workspace scenes. Use the controller-ready handshake and capture the same evidence. If clean loading requires restarting the identified simulator, do so without saving. No scripted world-pose input to control.
3. Check whether the existing diagnostic harness captures meaningful collision/off-road evidence. Report exactly what is captured or missing; do not equate successful parking with no penalties. Do not introduce guessed collision pairs or modify physics/scene to manufacture certification.

Expected evidence:
Exact hash, full commands, run artifact paths, absolute startup/drive/Hospital/zone/entry/park times, physical terminal pose with matrix interpolation uncertainty, command maxima, full-marker coverage, dominant caps, failures, simulator final stopped/zero status. Compare route-arrival versus parking-phase variability. Return a focused next recommendation supported by these runs; do not start another tuning cycle. Final acceptance still requires repeated Hard<=180, Medium twice, Easy once, rule compliance and official supported-platform artifacts.
