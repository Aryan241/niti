# Task 3 TEST v4 — Luna execution results

Implemented `orchestration/TASK3_V4_WORK_ORDER.md`; ready for parent Astra review. Changes are unpublished. No live simulator/evaluator validation, commits, push, ZIP creation, or portal submission.

## Exact changes and policy

- `task3/task3.py`: restored owned v2 production from `5f206bb`, changing only the startup banner to `Task 3 TEST v4: first-sight slowdown; confirmed distinct second-Speed40 release as requested.` Running absolute source path and SHA-256 reporting remain.
- `orchestration/check_task3.py`: restored the v2 checker from `5f206bb`, changing only the startup identity assertion to require the exact v4 banner. Benchmark baseline remains `28d3395`, not HEAD/v3.
- `orchestration/TASK3_V4_RESULTS.md`: this new report. No other files changed.

First Speed40 sight immediately caps at <=1.2 rad/s, including multiple initial signs. Near approach, sustained absence, supporting commanded travel, and two spatially consistent distinct-second observations remain required. Tentative oblique evidence alone, first-sign reacquisition, dropout, competing signs, and School do not release. A confirmed distinct second Speed40, including strong oblique confirmation, immediately clears both zone and hold, allowing commands up to the unchanged 3.0 rad/s global cap. Exit logs identify `cap released`, source, bbox, range, count, rearm, and streak. No v3 readable-exit gates, helper, rejection logging, or unused readable state remain. Shared perception optimization, baseline parking/pose logic, and unconfirmed capped parking fallback are preserved.

**v4 deliberately uses the same exit policy as v2, as explicitly requested. It may reproduce the known historical approximately 24.6 s overspeed penalty. Offline success does not establish live compliance, a new validated fix, full speed marks, or a sub-180 s run.**

## Offline validation evidence

Commands completed successfully:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 orchestration/check_task3.py
PYTHONDONTWRITEBYTECODE=1 python3 orchestration/check_task3.py --benchmark
git --no-pager diff --check -- task3/task3.py orchestration/check_task3.py
```

- Full suite: **108 tests passed, 13.206 s**. Includes immediate first cap, distinct normal/strong-oblique second-pair release, no lingering hold/recap, identity/rearm rejection cases, School/dropout, caps, invalid/discontinuous observations, parking, and runtime identity.
- Benchmark: **94 frames exactly equivalent** as ordered detector dictionaries; 6 positive frames, 6 strong candidates, 1 multi-candidate frame. **15 original perception tests passed, 0.604 s**, with 9 original detector calls exactly compared.
- Benchmark median ms/frame: baseline standalone 9.1267; candidate standalone 6.1090; candidate reused inputs 4.5854; baseline shared-prep + detector 11.7239; candidate shared-prep + detector 6.6480. Python 3.10.12, OpenCV 5.0.0, NumPy 2.2.6; single OpenCV thread. These are host microbenchmarks, not live lap-time evidence.
- Both Python files passed in-memory `compile()` without generating bytecode.
- Exact full-file comparisons against `5f206bb` passed after only the two identity substitutions above. This is stronger than policy-only semantic equivalence; no additional heuristic or test changes were introduced.
- `PoseEstimator`, `Parker`, `PoseTests`, and `ParkerTests` passed exact source-text and location-independent AST equality against `28d3395`.
- Scoped whitespace check passed; diff against `5f206bb` contains only the banner and its assertion. Against current HEAD, only the two authorized tracked source/checker paths changed (36 insertions, 308 deletions).

## Identity and preservation

```text
HEAD unchanged: c10d5f5
production SHA256:
796de2ea9317e4ddfa37da1c628d07d1dec112e56b3ab0fab80beb34b38531d5
checker SHA256:
9d4169676d68df0c3d2b342b3f2aaeb9c255355b5c33a37d864ec5a1bf2740f9
protected-file manifest SHA256 (141 files):
1bca474e74173d8dd0d950fc2c9ce24be4c53f9c325846fca508ccbee1ec94c5
```

The protected-file manifest hashes sorted `(relative path, content SHA256)` pairs for every project file outside `.git`, excluding only the three authorized paths. Before/after counts and digest match: all other files, including existing reports, packages, CSVs, logs, root source, work orders, and existing bytecode caches, are preserved byte-for-byte. No new package or temporary project output was created. Parent Astra's final review remains pending; any live run and submission remain deliberate manual team actions.
