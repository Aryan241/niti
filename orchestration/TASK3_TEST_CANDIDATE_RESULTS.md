# Task 3 experimental timing candidate — Luna results

## Handoff

Implemented `orchestration/TASK3_TEST_CANDIDATE_WORK_ORDER.md` as Luna. Ready for **Astra's diff review and exact-source candidate ZIP packaging**, not live acceptance or submission. No ZIP was created by Luna: packaging/review belongs to the parent Astra under this handoff. No simulator, scene changes, installs, network calls, portal actions, Git commits, or root submission/log edits.

Write scope used:
- `task3/task3.py`
- `orchestration/check_task3.py`
- this new `orchestration/TASK3_TEST_CANDIDATE_RESULTS.md`

Preserved the intentional pre-existing latency edits: shared HSV/red/blue inputs, ROI-local detector work and reusable support canvas, plus the parking perception shortcut. The working tree already contained source/checker modifications and timing reports before this task; a Git diff against HEAD includes those earlier changes as well as this implementation.

### Exact source identity

SHA-256 of final candidate `task3/task3.py`:

```text
502a5b2fc34158fe55ebb48d2604dd496f2634afeac2771fde9b4efff20f6886
```

Pre-existing optimized candidate at start: `e4ce6e7439a28ff761b75e4406086cd43385d87fb2d9fe597b6584cb1f41c62a`.

Protected root files, hashes checked before and after:

```text
task3.py        fcbb86ae9dca2a6716fbd35ed58ab1dd302b870adce0cbc2717e7ff33bf41b17
task3_debug.log 43d02958462c6460210ed8db056270975749573020e2a811daaa3f4e915cf199
```

Astra should package the candidate source above, not the unchanged root `task3.py`, and verify the packaged source hash. Keep this report/checker out of the submission source.

## Changed behavior

### Experimental exit clearance, never release on first exit sighting

`ExitPassageTracker` arms only after the existing distinct-second-Speed40 encounter logic completes. The first sign, same-sign flicker, School progress, or absence by itself cannot arm it. Route progress still changes at the second encounter, but the speed hold does not immediately release.

While held, normal detections and spatially confirmed strong oblique candidates continue to be observed, including after `zone_done`. Overlapping normal/oblique observations are deduplicated conservatively; separate competing candidates invalidate readiness. The distinct encounter tracker rejects multiple candidates only after entry, to prevent competing-second confirmation. At count zero, any valid Speed40 range immediately enters and caps the zone, even with multiple normal detections visible; the nearest valid range initializes the first encounter.

Passage evidence requires:

1. One confirmed near Speed40 object, image-derived forward range at most 0.65 m, with its centre in the outer 12% of either image edge.
2. At least three spatially consistent same-side observations spanning at least 0.20 s. Consecutive centres must stay within 28 px, width/height ratios within 0.75–1.33, and range changes within 0.06 m.
3. Subsequent detection loss from that established edge history, for at least two frames.
4. **Additional commanded travel after the last observation**, at least its latest image-derived forward range plus a conservative 0.322 m allowance: full wheelbase (0.120), twice wheel-offset envelope (0.055), camera offset (0.047), and noise margin (0.100). Camera offset is deliberately overcounted although the range function is already centre-referenced. This is a conservative geometry allowance, not a measured body bounding box or evaluator boundary.

Travel uses the previous **final bounded command**, after all Mission caps, times wheel radius and actual elapsed simulation time. Zero commands provide no clearance. Nonpositive/nonfinite timing, gaps over 0.75 s, invalid frames and pause invalidation discard readiness. Weak, competing, interior/far, inconsistent or returning observations cannot count as edge loss; a returning observation starts new history and discards accumulated clearance. Once a second encounter has armed the tracker, invalidation retains eligibility to reacquire it, but no old passage evidence survives.

The original parking handover fallback remains unchanged: without sufficient passage evidence, the cap stays latched until parking handover. Global 3.0 rad/s and zone 1.2 rad/s limits are unchanged. No scene position or fixed route-time release was introduced. The 0.20 s threshold is observation confirmation, not a release timer.

Startup identifies `Task 3 EXPERIMENTAL timing candidate v1`. Concise candidate/release logs include last image range, required clearance and accumulated command travel. `VERBOSE` remains disabled by default.

### Bounded parking yaw fusion

Normal and three-clear-frame recovery corrections now share this per-observation limit:

```text
abs(measurement correction) <= radians(20) * valid_elapsed_seconds + radians(0.5)
```

The 0.5-degree finite noise allowance is per valid observation; the effective convergence therefore has some frame-rate dependence. No measurement correction invents elapsed time on the first observation or when timestamps are missing/invalid, nonpositive, or excessively separated. This is an observation-clock rule, not a rule forbidding correction after missing image corners: a missing/invalid-corners frame with a valid timestamp still advances that clock (and can predict the preceding command), but applies no measurement correction and resets the recovery streak. A subsequent valid measurement may use the elapsed interval since that frame. Commanded-turn prediction remains separate and uses actual elapsed time and previous bounded speed/steering.

The original normal exponential blend and recovery blend still request corrections, but neither can inject a large instantaneous heading jump. Large-residual recovery still needs three consistent clear-yaw frames; ambiguous/missing measurements break that recovery streak. Sustained clear measurements continue correcting and recover rather than remaining gated out forever.

A correction/recovery streak is not fresh heading proof: `heading_observed` now requires the current clear measurement's post-correction wrapped residual to be within **3 degrees**, rather than marking every normal correction fresh or accepting recovery merely within the 15-degree normal/recovery gate. Current raw range and bearing still determine returned geometry; returned poses are not clipped or smoothed to hide the jump. Final parking completion, stillness, uncertainty, overshoot and heading guards are unchanged.

The pre-existing recovery tests were deliberately updated to allow bounded convergence over sustained observations instead of expecting immediate proof on frame three/four. They now assert the tighter convergence threshold, unproven early recovery, and stopped behavior while heading remains unproven. The small-bias multi-frame-rate test retains its <0.1-degree final-error requirement and allows <0.05-degree spread instead of exact exponential equality once the new cap binds. No completion/uncertainty safety assertion was relaxed.

## Actual offline verification

Environment: Python 3.10.12, OpenCV 5.0.0, NumPy 2.2.6. Simulator API access is unavailable; checker uses its existing offline import mechanism and never connects to CoppeliaSim.

### Full regressions

```sh
PYTHONDONTWRITEBYTECODE=1 python3 orchestration/check_task3.py
```

**113 tests passed**, final post-review-correction run 16.955 s (92 tests existed at start; 21 new tests). New cases cover both-edge valid passage, minimum history, high-frame-rate candidate logging, insufficient/absent travel, reappearance, range/spatial jumps, far/interior loss, ambiguity/competition, duplicate observations, normal and continued strong oblique tracking after the second encounter, invalid frames/pause/timestamp gaps, actual variable-dt final-command integration, School/absence non-arming, bounded normal/recovery corrections, sustained recovery, and genuine turns in both directions. The focused review regression additionally covers two normal Speed40 signs on the first `Mission.step`: immediate zone entry and <=1.2 rad/s cap, count exactly one, no completed exit, and no armed passage tracker. Existing competing-second no-release checks, sign variants, hospital, lane, runtime, cap, parking fallback/completion and import/API allowlist checks pass.

Initial verification failed on the old instantaneous-recovery/proof expectations, addressed by the focused test changes described above. It also reported a single-element read-only-input equality mismatch on `generated-3`; the detector was not modified for this candidate. That perception test passed on its immediate isolated rerun and both subsequent full-suite runs; both benchmark equality runs passed too. The one transient mismatch remains unexplained rather than silently characterized as fixed.

### Focused Astra review correction

Astra found that the new multiple-detection early return suppressed first-sight zone entry. Added `MissionTests.test_two_normal_speed40_signs_immediately_enter_and_cap_zone` and ran it before changing the implementation: it failed at `self.assertTrue(self.m.zone)`, reproducing the regression. Restricted that early return to `self.count > 0`, preserving immediate entry on any valid first Speed40 while retaining the competing-second rejection. No other candidate control behavior was changed in this correction. The full 113-test suite, `compile()` of both Python files and scoped diff checks passed afterward. Root source/log hashes still match those above.

The pre-correction candidate source hash was `9be77b514c07d48e451f2201eeccdf5011bc3e31b046e514e11fae13864174a5`; use the updated exact-source hash in the handoff section for packaging. The observation-clock explanation above was clarified without changing yaw implementation.

### Synthetic end-to-end passage evidence

Executed the new Mission regression through actual `Mission.step`, with detector/lane observations mocked but real mission command limiting and integration:

```text
[6.4] experimental exit candidate: image_forward=0.488 m required=0.810 m command_travel=0.000 m
[38.4] experimental exit release: image_forward=0.488 m required=0.810 m command_travel=0.818 m
```

These are synthetic timestamps, not route timings or a fixed release duration. Every prior command stayed at or below 1.2 rad/s; release occurred only after accumulated command clearance exceeded the requirement. The variable-dt test also verified integration of an actual reduced 0.3 rad/s command rather than nominal cruise/zone speed.

### Synthetic log-like discontinuity evidence

With persistent clear yaw -0.56 rad, raw range 0.90 m, and bearing changing by only 0.012 rad over 0.10 s, a preconfirmed recovery gave:

| Quantity | Before | After |
| --- | ---: | ---: |
| Returned heading | 0.0292173 rad | 0.0728505 rad |
| Returned lateral | 0.2926848 m | 0.2661830 m |
| Fresh heading proof | false | false |

Yaw change was **0.0436332 rad** (2.5 degrees), not the historical ~0.326 rad step. Lateral change was **0.0265018 m**, with no abrupt lateral sign flip. This is a controlled, log-inspired regression, **not a replay/reconstruction of recorded images or actual vehicle motion**. Sustained +/-0.60 rad observations converge and eventually regain proof; commanded turns of both signs remain tracked.

### Detector equality and timing

```sh
PYTHONDONTWRITEBYTECODE=1 python3 orchestration/check_task3.py --benchmark
```

The pre-review-correction candidate benchmark passed exact ordered detection-dictionary equality against HEAD on **94 frames** (6 positive frames, 6 strong candidates, 1 multi-candidate frame). Its 15 original perception regressions passed; 9 original detector calls were also exactly compared. This verifies preservation of detector outputs, **not full-policy equality**; intentional policy changes make the old full-policy equivalence claim inapplicable.

Pre-review-correction same-process, one-OpenCV-thread synthetic medians, ms/frame:

| Path | Median |
| --- | ---: |
| Baseline standalone detector | 9.7049 |
| Candidate standalone detector | 6.2643 |
| Candidate reused-input detector | 4.9356 |
| Baseline shared preparation + detector | 11.9296 |
| Candidate shared preparation + detector | 6.5794 |

These retain the earlier detector optimization; they are machine/corpus timings, not simulator lap savings. This benchmark was run on the pre-correction source hash recorded above; it was not rerun for the focused first-entry correction, which changes no detector code. The full suite, including detector regressions, was rerun on the updated source. Full-policy runtime after enabling continued post-exit detection was not benchmarked against live operation.

### Static and scope checks

- `compile()` of both Python files passed with `PYTHONDONTWRITEBYTECODE=1`, without writing bytecode.
- `git --no-pager diff --check -- task3/task3.py orchestration/check_task3.py orchestration/TASK3_TEST_CANDIDATE_RESULTS.md` passed.
- AST comparisons against HEAD confirmed unchanged `lane_control`, `Parker`, `detect_lane`, `detect_signs`, `detect_obstacles`, and `Mission._hospital`, `_observe_school`, `_observe_obstacles`, `_drive_parking`.
- Protected root source/log SHA-256 values remained unchanged.

## Limitations and risks for Astra/user testing

- **Experimental, not certified official-zone compliance.** Visual sign passage is not the evaluator's boundary. Releasing by this heuristic can regress the speed score if the official zone extends beyond the visually inferred exit plus clearance.
- Wheel-command travel is not measured motion. Slip, stalls, steering/curves, sign orientation/clipping, image range error, and unknown zone geometry can invalidate its physical interpretation. The extra allowance reduces risk but cannot prove clearance.
- The strict edge/range/history criteria may never be met in a real run; the candidate may retain the original capped-parking behavior and deliver no exit timing improvement. Continued oblique perception while held also adds processing work after route exit.
- Slower, stricter yaw convergence can delay parking or hold the vehicle stopped while fresh proof is unavailable. It avoids the tested discontinuity but does not establish closed-loop stability for unrecorded views or real vehicle dynamics.
- No live camera/command transport, official score, hospital evaluator result, complete route, final physical parking pose, or lap duration was validated. **No claim of recovering 51.5 seconds or finishing under 180 seconds.**
- User testing should retain the startup/event messages and return the full new run log and portal metrics to Astra. In particular compare speed-zone score, release timing (if any), parking yaw/lateral evolution and completion. Submission remains a deliberate manual team action after review.
