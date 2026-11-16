# Task 3 TEST v3 — test only, pending Astra review and live validation

Candidate: `submission_packages/NV_Task3_TEST_v3.zip`. This is not an official submission. Do not overwrite the v1/v2 archives or pair any candidate with an old CSV.

## Run the correct script

1. Extract this ZIP into a separate test folder. It contains exactly one top-level file, `task3.py`.
2. Follow the unchanged official simulator/evaluator launch procedure, using **that extracted script**, not an older source elsewhere. Optional `NV_VERBOSE=1` adds readable rejection reasons and existing perception diagnostics.
3. Before connecting, startup must print `Task 3 TEST v3`, the absolute running source path, and this exact source SHA-256:

   ```text
   f8f3c58af93da54ef389b18d16c063af2e3a0a35254fa13445ed8292ba33dd2a
   ```

   Stop and resolve an incorrect path/hash before testing. Hash unavailable is not sufficient to identify a valid test run.
4. Generate a **new CSV, complete log and evaluator feedback** from the same run. Keep them with the source hash and candidate version. Check **SPEED first**, including overspeed duration, then HALT/collision/parking/time. Do not reuse `NV_Task3_run-4.csv` or previous feedback.
5. Return that evidence to Astra/team for review. Any portal submission remains a deliberate manual team action.

ZIP SHA-256: `54b1132b35674afbb49b94ca3fa31f7997260b51a2467f5f16481ce437f5b7c0`.

## What changed and what to look for

- The first normal Speed40 still caps immediately, even if too small for readable verification.
- An oblique-only second encounter may finish route progress but **cannot authorize acceleration**. Its log includes source, bbox, range and `cap retained: readable exit unverified`.
- A separate normal-only verifier accepts width and height >=24 px, aspect 0.75..1.33, detected area >=400. It requires its own near first encounter, absence with supporting commanded travel, and a distinct farther normal object across **three spatially consistent observations**.
- Logs include `readable Speed40 verifier activated` and, only on verified second encounter, `readable second Speed40 confirmed: cap released`. These are image-policy observations, **not proof of glyph identity, physical passage or official zone boundary**.
- Without readable verification, the hold remains through route progress, School, dropout and travel until the original parking handover. An active zone still enforces its cap during parking. No pose/parking retuning was done.

The strict readable exit may never appear in this camera view. The capped parking fallback can therefore restore old slow timing. There is **no fixed 24.6-second delay**, scene/world-pose dependency, predicted lap-time reduction, under-180-second promise, full-speed-score promise or live validation claim. Historical evaluator penalty versus policy wording remains unresolved. If the readable exit never appears, obtain video/captured frames before further perception changes rather than guessing timing or parking parameters.

Offline checks passed: 123 tests on production and extracted archive; exact failed oblique-bbox regression; original detector equivalence; AST/compile and package CRC/content checks. See `orchestration/TASK3_V3_RESULTS.md` for evidence and limitations.
