# Luna results — Task 3 TEST v2

## Status and scope

Implemented `orchestration/TASK3_V2_WORK_ORDER.md` as Luna. Ready for parent Astra's diff/evidence review; **no live simulator/evaluator validation and no official submission**. No commits, push, installs, scene edits or root-file replacements.

Exactly five implementation/package paths:

1. `task3/task3.py` — modified controller.
2. `orchestration/check_task3.py` — modified offline checker.
3. `orchestration/TASK3_V2_RESULTS.md` — new evidence report.
4. `submission_packages/NV_Task3_TEST_v2.zip` — new single-file test archive.
5. `submission_packages/NV_Task3_TEST_v2_README.md` — new test instructions.

The user-provided untracked v2 work order and untracked root source/logs were not modified. HEAD remains `0694ac9`; the explicit comparison baseline is **`28d3395`**, not HEAD/v1.

## Policy basis and unresolved live risk

Astra's freshly fetched official page, quoted in the work order:

https://themes.e-yantra.org/Niti-Vahan_2627/stage_1/task_3/instruction/

> First Speed 40 sign: slow down. As soon as your code sees the first Speed 40 sign, slow down to 1.2 rad/s or below.

> Second Speed 40 sign: speed up again. When your code sees a Speed 40 sign for the second time, you can go back up to 3.0 rad/s.

These are the work order's fetched excerpts, not a claim of an independent Luna network fetch. They require immediate first-sight entry and permit confirmed second-sighting release. Delaying entry is not implemented.

Historical source comments report an earlier **~24.6 s speed penalty** on immediate sighting release. That conflicts with the documented permission and remains an unresolved **evaluator-versus-policy / sign-identity risk**. Offline identity safeguards cannot establish which physical object or evaluator boundary was seen in a past run. A new official-procedure live run must check the **speed-zone result first**, then timing. There is no speed-score, collision, parking, under-180 s or actual timing guarantee.

Per the work order, `task3_debug-3.log` is v1 evidence: entry 49.70, second encounter 136.60, parking handover 204.85, parked 237.05; no passage candidate/release. Its post-exit hold lasted 68.25 s. V1 parking took 32.20 s versus baseline 29.90 s; that is not proof of causality. Portal ~234 s, footer ~236 s and parked 237.05 s are different measurements and are not equated here.

Idealized fixed-trajectory illustration only:

```text
68.25 * (1 - 1.2/3.0) = 40.95 s
237.05 - 40.95 = 196.10 s
```

That estimate is **before other changes**, does not model curves, caps, commands, observations or closed-loop motion, and cannot promise 180 s or a score.

## Controller implementation

- First valid normal Speed40 sight immediately sets the zone and hold, even when multiple initial valid signs are visible. The final `Mission.step` cap enforces <=1.2 rad/s while unconfirmed.
- Retained near-approach (`ZONE_NEAR_RANGE`), disappearance-time and >=0.08 m supporting commanded-travel rearm, farther-range distinction (>=0.15 m), and two-observation confirmation. Commanded travel is not measured motion.
- Reused the existing `WeakBoardTracker` spatial-consistency rule inside `SignTracker` so alternating normal-object positions cannot form a two-frame encounter. Competition and missing evidence reset this streak; pause/invalid images reset identity, and repeated/long observation gaps cannot join confirmations.
- Retained oblique tentative/strong gates and spatial support. A tentative frame can support continuity but cannot itself confirm release. School, absence, weak-only boards, same near first sign and multiple distinct candidates cannot release.
- Retained same-object normal/oblique deduplication **before** the competing-object tracker gate. A duplicate pair is not mistaken for two signs.
- On confirmed distinct second sight, immediately set `zone=False`, `zone_done=True`, `zone_speed_hold=False` in that frame, before choosing its cap. Always log `second Speed 40 confirmed: cap released` with normal/oblique source, bbox, estimated range, count, rearm and streak evidence.
- Removed `ExitPassageTracker`, its state/reset/candidate/clearance integration and v1-only post-exit oblique detection. No late release latch, passage timers or edge heuristic remain. The compatibility hold flag never relatches after completed exit.
- If exit is unconfirmed, retained original capped School/marker parking fallback. Clearing the hold at that handover does not clear `zone`; final zone cap remains. After confirmed exit, normal parking handover gates remain and the controller can use the unchanged global cap.
- Restored **exact baseline `PoseEstimator` source** from `28d3395`. `Parker` is also exactly baseline source: no speculative parking tuning, speed-cap increase or guard weakening.
- Preserved production detector latency optimizations and shared HSV/red/blue input reuse.
- Startup now prints `Task 3 TEST v2`, resolved absolute `__file__`, and SHA-256 of the running source **before connecting**. Only new import is standard-library `hashlib`; import allowlist updated. Unreadable source reports hash unavailable without aborting runtime or printing the exception/path contents beyond the task source identity.

## Regression and verification loop

Commands executed:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 orchestration/check_task3.py
PYTHONDONTWRITEBYTECODE=1 python3 orchestration/check_task3.py --benchmark
git --no-pager diff --check -- task3/task3.py orchestration/check_task3.py
```

Also executed standard-library verification scripts for `compile()`/AST, exact source comparisons against `git show 28d3395:...`, SHA-256, ZIP name/content/CRC and preservation checks. No `.pyc` was generated by these checks; the existing cache directory was not removed.

### Test results

- Initial run: 93 tests, one failure. Restoring `PoseEstimator` exposed the v1-modified `ParkerTests.test_fresh_consistent_yaw_recovery_resumes_near_edge_parking` expectation. Restored this method to baseline rather than changing parking behavior or weakening its original assertions.
- Added identity, release, parking-handover and runtime identity regressions, then full suite: **108 tests passed**, 15.334 s.
- Final sequential source rerun: **108 tests passed**, **14.318 s**, followed by the benchmark below. No remaining failures.
- Reopened and extracted the final ZIP into a temporary directory, set `TASK3_SOLUTION` to its extracted `task3.py`, and ran the full checker: **108 tests passed**, **13.597 s**. Temporary extraction was automatically removed; root/v1 files were not touched.
- Removed the 15 obsolete v1 passage tests and five bounded-yaw tests, replaced obsolete latch expectations with immediate-release behavior, and restored **all `PoseTests` and `ParkerTests` exactly** to baseline. General Hospital, lane, obstacle, missing-frame, cap, marker-loss, parking, detector and same-first-sign tests remain.
- Explicit new/updated coverage: immediate first sight, multiple initial signs maintained, first second-sign frame still capped, confirmed second frame released, absent/invalid frames after release never recap, one-frame dropout cannot release, no travel/no near approach cannot rearm, alternating normal positions cannot confirm, multiple normal or normal/oblique competing objects reject, duplicate normal/oblique confirms correctly, strong oblique pair releases with evidence, tentative oblique never releases, School/absence never release, interrupted observation streak resets, parking after confirmed exit uses global cap, source path/hash and nonfatal hash read failure.

### Exact baseline and syntax checks

Both Python files passed `compile(source, filename, 'exec')` without bytecode generation.

For each class below, both `ast.dump()` equality (no source-location attributes) and `ast.get_source_segment()` exact textual equality passed against **`28d3395`**:

- Production `PoseEstimator`.
- Production `Parker`.
- Checker `PoseTests`.
- Checker `ParkerTests`.

Scoped diff/whitespace checks passed. Source search found no `ExitPassageTracker`, `exit_passage`, v1 `observation_dt` or bounded-yaw constants in production. Final source diff reviewed: edits confined to imports/startup, requested yaw restoration, sign identity/release and obsolete passage removal.

### Detector baseline equivalence and benchmark

Environment: Python **3.10.12**, OpenCV **5.0.0**, NumPy **2.2.6**, single OpenCV thread. Original remote-API dependency is stubbed only when absent; no simulator I/O is exercised.

Benchmark explicitly loads `git show 28d3395:task3/task3.py` in the same process. Baseline SHA-256: `fcbb86ae9dca2a6716fbd35ed58ab1dd302b870adce0cbc2717e7ff33bf41b17`.

- **94 frames** matched exactly as ordered detector output dictionaries, standalone and precomputed paths: 6 positive frames, 6 strong candidates, 1 multi-candidate frame. Corpus includes recorded pixels, clipped placements and deterministic generated clutter.
- **15 original perception tests passed**, 0.642 s, with **9 detector calls** compared exactly to the baseline at the original placements.
- Existing optimization tests verify optional argument variants, read-only inputs/no mutation and Mission reuse of existing masks/HSV.
- Two warmup sweeps and nine paired samples, alternating job order. Final sequential-run timings:

| Path | Median ms/frame | Min | Max |
| --- | ---: | ---: | ---: |
| Baseline standalone | 9.1635 | 8.9535 | 9.7198 |
| Candidate standalone | 8.0697 | 7.8022 | 8.5746 |
| Candidate reused inputs | 4.8398 | 4.6045 | 6.0044 |
| Baseline shared-prep + detector | 12.0406 | 11.0612 | 12.8058 |
| Candidate shared-prep + detector | 8.3097 | 7.9084 | 9.0091 |

Final shared-prep median reduction is 3.7309 ms/frame (~31.0%). Timings vary with host load; an earlier parallel verification run also passed equivalence but is not the table's source. These microbenchmarks are not simulator lap-time predictions. Profiling baseline: 29,861 calls in 0.923 s; connected components, colour thresholding and dilation dominate.

## Package and reproducibility identity

ZIP: `submission_packages/NV_Task3_TEST_v2.zip`.

```text
production / archived task3.py SHA256
 a4f402ef63e4c3282a186ea046c90293a5a2f0e2d1227d2722986149ec32c4cb
ZIP SHA256
 0c450e02c3aed8300fbfed996048728e316f7bd1904ff6f3ebe19dfc9d246c8f
checker SHA256
 a089254f164c8ece452377c9797912848541124bcb8a9fd396db0771551e422e
archived CRC32  f1c12d8f
source bytes   81644
ZIP bytes      22924
```

Archive was reopened: exact name list `['task3.py']`; `ZipFile.testzip()` returned `None`; archived bytes and SHA-256 equal current `task3/task3.py`; CRC32 agrees with `zlib.crc32`. ZIP has one top-level file with fixed timestamp 2026-11-16 00:00:00 and mode 0644. No old evaluator CSV or other artifact included. README tells the team to extract into a separate test folder, follow the unchanged official launch procedure, use the extracted source rather than the root baseline, verify startup identity, optionally enable `NV_VERBOSE`, and return a newly generated CSV/log/source-hash set.

## Preserved artifacts

Before/after SHA-256 preservation values for user root source/logs and v1 package/report:

```text
task3.py
 fcbb86ae9dca2a6716fbd35ed58ab1dd302b870adce0cbc2717e7ff33bf41b17
task3_debug.log
 43d02958462c6460210ed8db056270975749573020e2a811daaa3f4e915cf199
task3_debug-2.log
 ac6a6c97a5d899347c89a82037d470a62d5f59c2e1cd850d62e778f8d7453447
task3_debug-3.log
 741442aac4a34b4888ce988aa4b055a34a78e731b4769049db06ff8f1f7974d5
task3_debug-v1.log
 faf079834d4f3f9a6db2665946c5112f38941dfce372b86364655bebd9473a37
submission_packages/NV_Task3_TEST_v1.zip
 dc29b38ca12d890146244e198782893e01ac24e0b9b71495d248e812dd787e39
submission_packages/NV_Task3_TEST_v1_README.md
 279f72516ff74846b9074f0a737d5f9fa407d5d0f7f35ae941c1054c3cb440a5
orchestration/TASK3_TEST_CANDIDATE_RESULTS.md
 0928f69c1883bdf40fb16b39e6a38cecb273aa2f6d6609f96d9b53146ed83b7f
```

All other tracked files remain unchanged versus HEAD. Root `.DS_Store` and `AGENTS.md` were also hashed before/after and preserved. V1 historical results and package are not rewritten to describe v2. Parent Astra owns final review; live evaluation and any portal submission remain manual team actions.
