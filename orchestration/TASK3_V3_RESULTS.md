# Luna results — Task 3 TEST v3

## Handoff status

Implementation, offline tests and packaging complete for `orchestration/TASK3_V3_WORK_ORDER.md`; **ready for parent Astra's final review**. No live simulator/evaluator run, no portal submission, no commits/push/branch changes. HEAD/main remains `5f206bb`.

Exactly five authored paths:

1. `task3/task3.py`
2. `orchestration/check_task3.py`
3. `orchestration/TASK3_V3_RESULTS.md`
4. `submission_packages/NV_Task3_TEST_v3.zip`
5. `submission_packages/NV_Task3_TEST_v3_README.md`

The existing untracked work order, root logs/CSV and archives were not edited. No dependencies, scene changes, world-pose gates, fixed overspeed-duration delay, new parking parameters or global state were added.

## Supported defect and policy limits

Baseline source SHA-256 verified against `git show HEAD:task3/task3.py`:

```text
a4f402ef63e4c3282a186ea046c90293a5a2f0e2d1227d2722986149ec32c4cb
```

`task3_debug-4.log` records at 137.50 s:

```text
second Speed 40 confirmed: cap released; source=oblique bbox=(606, 39, 33, 52) range=0.548 m count=2 rearmed=True streak=2
```

User/work-order feedback: SPEED 0/20, 24.6 s overspeed; HALT 50/50, collision 20/20, parking 10/10; portal ~182 s versus 185.10 s log. These are supplied historical results, not outcomes of v3. The supported defect is that an oblique-only encounter authorized acceleration. The evidence does **not** establish whether the object was false, an early view of the real sign, or where the evaluator's boundary lies. Historical evaluator penalty versus policy wording remains unresolved.

V3 is a stricter image-based release policy, not proof of glyph identity, physical passage or official boundary. It may never see a qualifying second readable face and may revert entirely to the original capped parking fallback and old slow timing. No full-speed score or under-180-second promise is made.

## Implementation

- Kept the original first normal-sign entry path and immediate final-command cap, including small and multiple initial normal detections. The readable filter cannot suppress entry.
- Kept the original `speed40` route `SignTracker`: near approach, absence/travel rearm, farther encounter, raw two-frame consistency and normal/oblique deduplication/weak confirmation gates. Route confirmation sets `zone=False`, `zone_done=True` **without clearing `zone_speed_hold`**.
- Added an independent `readable_exit = SignTracker(ZONE_NEAR_RANGE, frames_needed=3)`. It receives only unmodified normal `detect_signs` Speed40 observations, never strong/tentative oblique candidates.
- Clear-face thresholds are unchanged from the work order: width >=24, height >=24, width/height 0.75..1.33 inclusive, detected `area` >=400. No evidence-based threshold tuning was attempted.
- The readable verifier establishes its own first encounter and near approach, absence with supporting commanded travel, then a distinct farther encounter with three consecutive spatially consistent normal observations. It updates at most once per processed frame.
- Multiple normal candidates are rejected as a whole, not filtered into one eligible candidate. Too-small/thin/low-area observations reset readable streak/rearm and are not mistaken for clear-road absence. First-sight route entry remains intact.
- Only readable count 2 or original parking handover clears the hold. The final command remains <=1.2 rad/s after a weak route exit while readable count <2, including later dropout/travel/School. Parking handover still clears only the hold: an active `zone` continues to cap parking.
- Normal perception continues after weak route completion while hold remains. Oblique detection stops when route completion clears `zone`; no post-route oblique/passage framework was added. The parking shortcut cannot bypass an unverified hold, and final `Mission.step` caps still apply.
- Invalid frames and pause invalidation reset readable identity/rearm/travel evidence; repeated or long timestamp gaps reset its spatial streak, matching the existing tracker timing policy. No pose-estimator or parking-controller changes.
- Startup prints `Task 3 TEST v3`, resolved source path and SHA-256 before connecting. Route confirmation logs exact source/bbox/range/count/streak and `cap retained: readable exit unverified`. Readable activation/second confirmation logs normal bbox/range/streak/count. Release text is `readable second Speed40 confirmed: cap released`. Rejection reasons are verbose-only and change-only; original parking release message is preserved.

## Regression coverage and verification loop

Commands run:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 orchestration/check_task3.py
PYTHONDONTWRITEBYTECODE=1 python3 orchestration/check_task3.py --benchmark
git --no-pager diff --check -- task3/task3.py orchestration/check_task3.py submission_packages/NV_Task3_TEST_v3_README.md
```

Also ran `python3 -B -c ...` standard-library validation scripts for AST/`compile`, exact v2 source equality, hashes, ZIP generation/content/CRC, artifact preservation, and extraction into an automatically removed temporary directory. The extracted script was tested via `TASK3_SOLUTION=<temporary-directory>/task3.py` and `PYTHONDONTWRITEBYTECODE=1` using the complete checker. No simulator API was exercised.

Results:

- Initial full run: 122 tests; one test assertion failure. The new first-readable activation test incorrectly assumed that activation was the final message, but lane-start logging follows it. Fixed only that assertion to search the log calls; no controller safety failure was hidden or patched around.
- Added an independent no-near-readable-first/travel regression. Full rerun: **123 tests passed**, 37.788 s.
- Final logging-complete production rerun: **123 tests passed**.
- Final ZIP extracted-source full rerun: **123 tests passed**, 41.553 s. This tests the exact archived source, not an older root script.
- AST parsing and `compile(source, path, 'exec')`: passed for both Python files without generating bytecode.
- All 12 pre-existing `.pyc` paths and hashes were checked before/after and remained identical; none created or removed.
- Scoped `git diff --check`: passed. Reviewed the production/checker diff; original Hospital, lane, obstacle, pose and parking test bodies were retained except speed-release-dependent mission expectations.

Explicit regressions include:

- Snapshot of the exact failed **oblique source branch**, bbox `(606, 39, 33, 52)` and estimated range 0.548 m. It completes route count 2 but retains the hold and commands <=1.2 through subsequent dropout and supporting travel to 60 s; oblique detector runs only twice. This is a synthetic replay of logged detection metadata, **not a reconstruction of uncaptured pixels or a live trajectory**.
- First small normal still caps; multiple mixed-size normals never suppress entry; readable first count is not double-updated in one frame.
- Three normal observations required, including first two bounded commands and released command <=global limit; duplicates with weak evidence do not shorten the readable streak.
- Mirrored image placements, size boundaries, aspect boundaries and detected-area rejection. Alternating readable objects cannot confirm.
- Multiple normals, including eligible/ineligible mixtures plus a weak duplicate, cannot be filtered into a unique readable exit.
- Independent near/absence/travel requirements; same-first-sign reacquisition; strong/tentative oblique-only candidates never feed readable verification even with nominally clear-face dimensions.
- Invalid image, pause, repeated timestamps and long gaps break readable identity. Original weak/tentative/parking-board/roof regressions remain.
- Normal verification continues after weak route completion; missing readable exit uses original parking handover; parked shortcut preserves an unverified hold; original active-zone parking cap remains tested.
- Source identity/runtime behavior, detector input reuse/read-only checks and original perception corpus remain covered.

### Unchanged v2 components

For each item below, both location-independent `ast.dump` equality and exact `ast.get_source_segment` text equality passed against **`5f206bb`** on the final source:

- Production `PoseEstimator`, `Parker`, `detect_signs`, `_oblique_speed40_candidates`.
- Checker `PoseTests`, `ParkerTests`.

### Detector baseline equivalence and timing

Existing benchmark compares to `28d3395` (SHA-256 `fcbb86ae9dca2a6716fbd35ed58ab1dd302b870adce0cbc2717e7ff33bf41b17`), not HEAD. Python 3.10.12, OpenCV 5.0.0, NumPy 2.2.6, one OpenCV thread.

- **94 frames**: exact ordered dictionary equivalence, standalone and reused-input paths; 6 positive frames, 6 strong candidates, 1 multi-candidate frame.
- **15 original perception tests passed**, 0.802 s; 9 original detector calls compared exactly.
- Two warmup sweeps, nine paired alternating-order samples:

| Path | Median ms/frame | Min | Max |
| --- | ---: | ---: | ---: |
| Baseline standalone | 13.3181 | 11.1887 | 14.4285 |
| Candidate standalone | 11.2927 | 10.5604 | 11.5780 |
| Candidate reused | 6.4663 | 5.6186 | 7.2253 |
| Baseline shared-prep + detector | 15.2017 | 14.4120 | 17.8650 |
| Candidate shared-prep + detector | 10.9297 | 10.2482 | 12.8964 |

This benchmark was run before the final diagnostic-only rejection-message completion (then source SHA `2619643415a5e8099f5ead243997e9f43f8d050a17a1af31062d9296dd0b49a5`). Final detector source is exactly unchanged, as verified above; the final full suite also passes. These are host microbenchmarks, not a lap-time prediction.

## Candidate archive identity

```text
production / archived task3.py SHA-256
f8f3c58af93da54ef389b18d16c063af2e3a0a35254fa13445ed8292ba33dd2a
checker SHA-256
762c6580ab013f0a029bf805e288b4131371bf25386b76d0392c89e0c8a81735
NV_Task3_TEST_v3.zip SHA-256
54b1132b35674afbb49b94ca3fa31f7997260b51a2467f5f16481ce437f5b7c0
archived CRC32: a2783324
source bytes: 84277
ZIP bytes: 23453
```

Reopened ZIP name list is exactly `['task3.py']`; `ZipFile.testzip()` returns `None`; archived bytes match production and CRC32 matches `zlib.crc32`. One top-level file, fixed timestamp 2026-11-16 00:00:00, mode 0644. No CSV, logs or generated reports in the archive. No official submission ZIP was created or overwritten.

## Preservation and next step

Before/after aggregate SHA-256, computed by concatenating each sorted path's UTF-8 name and bytes for all root `*.log`, root `*.csv`, and all pre-existing `submission_packages/*` files:

```text
4d24ca9089da4dcc3c9a23abbd4463462863a47c1c15de4f14dc45d3faf388c9
```

Both snapshots match, covering all root evidence, v1/v2 ZIPs and READMEs, and existing submission archives. No old CSV reuse. Git status shows only the two allowed tracked modifications, new allowed v3 files and the original untracked user artifacts/work order.

**Parent Astra review is next.** Then the team must run the extracted candidate and obtain a new CSV + full log + feedback, checking SPEED/overspeed first. No live validation or time-goal completion is claimed. If a second readable exit never appears, video/captured frames are still required before further changes; do not infer identity from an oblique-only log or introduce blind timing/parking tuning.
