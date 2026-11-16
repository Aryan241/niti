# Task 3 v2: follow official sign-event policy

Objective:
User requests necessary fix after v1 live feedback preserved full behavior scores but ~234s portal/237.05s log. User hypothesizes delaying first slowdown. Official Task3 instruction page freshly fetched by Astra disproves delayed entry and explicitly permits second-sighting acceleration:
https://themes.e-yantra.org/Niti-Vahan_2627/stage_1/task_3/instruction/
"First Speed 40 sign: slow down. As soon as your code sees the first Speed 40 sign, slow down to 1.2 rad/s or below"; "Second Speed 40 sign: speed up again. When your code sees a Speed 40 sign for the second time, you can go back up to 3.0 rad/s."

Evidence/decision:
task3_debug-3.log definitely v1. entry49.70, second136.60, park204.85, parked237.05, no passage candidate/release at all. v1 hold persisted68.25s; parking32.20s vs baseline29.90s (not proof causality). Portal234/footer236/park237.05 differ; don't equate. Remove v1 hold heuristic, follow documented distinct-second sighting. Historical source comments report prior24.6s speed penalty; this conflicts and must be documented as unresolved evaluator-vs-policy/identity risk. No guarantee speed score/under180. Revert unproven v1 yaw policy to baseline, preserve accepted detector latency improvements. Preserve all user root files/logs and all v1 reports/ZIP exactly.

Luna write scope:
- task3/task3.py
- orchestration/check_task3.py
- NEW orchestration/TASK3_V2_RESULTS.md
- NEW submission_packages/NV_Task3_TEST_v2.zip
- NEW submission_packages/NV_Task3_TEST_v2_README.md
Parent Astra owns final review. Read role and AGENTS instructions. No commits/push/portal/scene edits/install.

Implementation:
1. Retain first-sight cap, including multiple valid initial signs; retain distinct encounter near approach, disappearance+supporting travel rearm, spatial confirmation and tentative/strong oblique gates; weak/School/absence/same-firstsign can't release. At CONFIRMED distinct second encounter clear zone and zone_speed_hold immediately and emit clear event incl second-sign evidence bbox/range/normal-vs-oblique so next log can audit identity. Remove ExitPassageTracker and v1-only continued postexit detector/clearance integration, not merely dead enable flags. Remove zone_speed_hold entirely if clean, or retain always false after confirmedexit for compatibility but no late latch. Original capped fallback while exit unconfirmed remains.
2. Restore PoseEstimator yaw policy EXACTLY to HEAD~1/main baseline (git show 28d3395:task3/task3.py class PoseEstimator) so v1 bounded-yaw/convergence change isn't silently kept. Preserve current production perception optimization and first-sign multi safety fix. No speed cap increases/no final guard weakening. Keep dedup of same-object normal/oblique before tracker so multi guard doesn't suppress valid duplicate confirmations.
3. Replace v1-specific obsolete tests with tests for documented intended behavior, do not delete general safety cases. Explicit immediate second-confirmation release, invalidframe after release doesn't recap, no secondconfirmation no release, same-firstsign/dropout/tentative/multiple distinct reject. Restore original yaw tests/assertions to baseline expectations (current checker in git show28d3395). Keep detector optimization tests. Ensure Mission.parking gating/caps remain sensible after second exit.
4. Startup visibly labels 'Task 3 TEST v2' and prints __file__ resolved absolute source path plus standard-library hashlib SHA256 OF running source, to end file-selection uncertainty. Add import hashlib (allowed standard library) and update import allowlist test accordingly. No external dependencies beyond originals. Runtime harness assertions adapt appropriately. If source hashing unavailable don't crash or expose secrets; path/hash are only task source.
5. Full offline regression loop, syntax via compile no pyc, scoped diff check, detector baseline equivalence benchmark (against28d3395 not current HEAD v1), semantic source comparison PoseEstimator baseline. Package zip containing exactly top-level task3.py; reopen compare bytes/hash/CRC. README short test instructions with hash, use extracted file not root baseline, optional NV_VERBOSE and same official procedure no invented evalargs. No old CSV in zip, no official submission claim. Results cite fetched official instructions and unresolved historical speed penalty. Quantify idealized fixed-trajectory saving 68.25*(1-1.2/3)=40.95s only illustrative, ~196.1s from237.05 BEFORE other changes; explicitly cannot promise180 or actual score. Need actual user test speed score first then timing. v2 reports preserve v1 historical artifacts.

Acceptance:
Run PYTHONDONTWRITEBYTECODE=1 python3 orchestration/check_task3.py; AST compile; git diff --check; zip/production/source hashes; protect original root submitted source/logs. Return changedfiles exacttestcount evidence archive path/hash and pending live risk. No speculative third tuning dimension, no route timers or positions. Return full implementation/package not recommendations.
