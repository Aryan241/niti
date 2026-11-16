# Task 3 TEST v2 — local-test candidate

**Local testing only; not an official submission.** No live simulator/evaluator run was performed during preparation. Keep v1 and the original submitted source/logs unchanged.

## Package identity

- ZIP: `submission_packages/NV_Task3_TEST_v2.zip`
- ZIP SHA-256: `0c450e02c3aed8300fbfed996048728e316f7bd1904ff6f3ebe19dfc9d246c8f`
- Contents: exactly one top-level `task3.py`, copied byte-for-byte from `task3/task3.py`.
- Source SHA-256: `a4f402ef63e4c3282a186ea046c90293a5a2f0e2d1227d2722986149ec32c4cb`
- Archived CRC32: `f1c12d8f`; ZIP reopened, CRC tested, names and source bytes verified.
- No CSV, logs, references, scenes or reports are inside the ZIP.

## Run the correct file

1. Extract the ZIP into a **separate test folder**, for example `task3_test_v2`, without overwriting the repository-root `task3.py` or prior outputs. Use the extracted controller, **not the root baseline**. Arrange official evaluator/scenes/reference resources in the layout required by the existing official procedure; those resources are not included here.
2. Follow the existing official launch/evaluation procedure. Do not start a duplicate controller if the evaluator starts it. No new evaluator arguments are required or suggested here.
3. Confirm startup says `Task 3 TEST v2`, shows the resolved absolute running-source path, and prints the source SHA-256 above. Stop and check file selection if these do not match. An unreadable source produces an explicit `unavailable` hash message, not a crash.
4. Only when that procedure requires starting the controller directly, optional detailed logging from the separate test folder is:

   ```sh
   NV_VERBOSE=1 python3 task3.py > task3_debug_test_v2.log 2>&1
   ```

   `NV_VERBOSE` is optional. Startup identity and second-sign release evidence are always printed. Use fresh output names for subsequent runs.
5. Preserve this run's new evaluator CSV, full log, exact tested source/hash and screenshots/video together. Do not reuse an old CSV. Review **speed-zone score/penalty first**, then timing, Hospital hold, collisions/lane changes and parking alignment/completion. Return both portal and controller timing if they differ, plus second-sign `source`, `bbox`, `range`, `count`, `rearmed` and `streak` evidence.

## Behavior and risks

First valid Speed 40 sight immediately caps at 1.2 rad/s or below, including multiple initial signs. A distinct second encounter requires near approach, disappearance plus supporting commanded travel, spatially consistent consecutive observations, and normal/strong-oblique confirmation. Confirmation immediately clears the zone and speed hold; it does **not** wait for v1's edge/clearance heuristic. Weak/tentative/School/absence/same-first-sign/competing evidence cannot release. If no exit is confirmed, the original capped parking fallback remains. Pose/yaw and parking controller are restored/unchanged relative to baseline `28d3395`; perception optimizations remain.

The official Task 3 instruction excerpts recorded by Astra explicitly allow second-sighting acceleration, but historical source comments report a conflicting ~24.6 s speed penalty. Evaluator-versus-policy and sign-identity risk remain unresolved until a fresh live run. No score, physical clearance, collision-free run or under-180 s guarantee is made. The illustrative fixed-trajectory saving is only 40.95 s from the old 68.25 s hold, giving roughly 196.1 s from 237.05 s before other changes—not a prediction.

Offline verification: **108 tests passed**; detector benchmark/equivalence used **28d3395, not HEAD**, matching 94 corpus frames and nine original detector calls; baseline pose/parking source and test comparisons, syntax compile, scoped whitespace and archive integrity checks passed. Details: `orchestration/TASK3_V2_RESULTS.md` (not in ZIP). Final submission remains a deliberate manual team action after review and live validation.
