# Task 3 official-feedback timing follow-up

Objective:
Produce a measured, behavior-preserving perception latency improvement for the current Task 3 controller. Official feedback supplied by user: 231.5 s total, Hospital 50/50, speed 20/20, collision 20/20, parking 10/10, late/not eligible. Exact submitted source and run log are unavailable; do not claim this source produced that run or that an offline optimization achieves <180 s.

Files:
- task3/task3.py: perception implementation only
- orchestration/check_task3.py: focused regression coverage and portable offline import
- orchestration/TASK3_TIMING_RESULTS.md: concise evidence

Constraints:
Luna owns implementation and verification. Preserve all driving decisions, speed caps (including zone_speed_hold), thresholds, parking/hospital behavior, simulator API calls and one-file submission. Do not edit scenes, historical results/work orders, dependencies or portal artifacts. No simulator installed on PATH and remote API package absent here. Offline tests may explicitly stub only missing remote API import in test harness (never production); do not hide unrelated import errors. Keep generated artifacts out of submission. No portal upload.

Acceptance criteria:
1. Profile oblique-sign detector. Eliminate redundant conversions/masks by reusing Mission's already-created HSV/red/blue inputs; retain standalone detector compatibility. Consider other exact-output allocation reductions only if supported by equivalence checks.
2. Demonstrate identical candidate dicts/order and strong flags for existing positive and negative regression images and representative generated frames, including clipped shapes. No classifier or driving-policy retuning.
3. Add tests for precomputed-input equivalence, caller reuse and input immutability. Make normal python3 orchestration/check_task3.py run offline without requiring remote API installation, explicitly documenting stub limitation.
4. Benchmark unchanged versus candidate with same process/thread settings, warmup and repeated samples. If no measured gain, do not claim speedup. Save concise reproducible commands/method and timings.
5. Run full regression suite, syntax compilation without modifying tracked pyc files, scoped diff check. Provide final source hash and full test result. Explain live timing remains unverified and exact submitted source/log/video needed for 51.5 s diagnosis.

Verification commands:
PYTHONDONTWRITEBYTECODE=1 python3 orchestration/check_task3.py
python3 AST/compile checks using compile(source, path, 'exec') (no pyc)
git --no-pager diff --check -- task3/task3.py orchestration/check_task3.py orchestration/TASK3_TIMING_RESULTS.md

Expected evidence:
Focused diff, regression count/results, baseline/candidate equivalence evidence and median benchmark timings, final source hash, and explicit outstanding official-run blocker. Do not launch simulator or evaluator without installed supported simulator or manufacture a timing/score claim.
