# Task 3 perception timing — Luna handoff

## Scope and invariants

Changed only `task3/task3.py`, `orchestration/check_task3.py`, and this report.
No simulator/evaluator launched, dependencies changed, portal upload, or submission performed.
The pre-existing untracked `orchestration/TASK3_TIMING_WORK_ORDER.md` was left untouched.

Production changes:
- `_oblique_speed40_candidates(frame, hsv=None, red=None, blue=None)` retains standalone use and accepts read-only precomputed HSV/uint8 color masks. Mission passes its existing arrays.
- White/dark masks and blue boolean conversion operate on component ROIs rather than full frames; the morphology kernel is reused within each call.
- A lazily allocated full-frame support canvas is reused across components, clearing only the preceding ROI. The redundant full-frame `astype` copy is removed. Global warp coordinates remain unchanged to avoid nearest-neighbor rounding differences from a crop-relative transform.
- Both warps share the same perspective matrix. Classifier thresholds, candidate ordering and `strong` computation are unchanged.

AST comparison against HEAD confirms the entire production program is identical outside this detector's implementation and its added caller arguments. Driving policy, `zone_speed_hold`, caps, hospital/parking behavior, and simulator API calls are unchanged. Submission remains one file.

## Baseline and environment

- Baseline commit: `28d3395b699d24b206132921e5e4ae6d9f1a9217`.
- Baseline SHA256: `fcbb86ae9dca2a6716fbd35ed58ab1dd302b870adce0cbc2717e7ff33bf41b17`.
- Final production SHA256: `e4ce6e7439a28ff761b75e4406086cd43385d87fb2d9fe597b6584cb1f41c62a`.
- Linux x86_64, AMD Ryzen 5 5500U, Python 3.10.12, OpenCV 5.0.0, NumPy 2.2.6.
- The unchanged production source was benchmarked before editing: 93-frame corpus, baseline median **9.4412 ms/frame** (range 8.8239–9.9340); all original **90 regressions passed**. Identical-source control medians were 9.1115 and 9.3474 ms/frame, illustrating timing variability. Do not compare this earlier run directly with final timings below.
- Baseline source is read using `git show HEAD:task3/task3.py` inside the benchmarking process, checked by its printed hash, and compiled in memory. No baseline copy or generated timing artifact enters submission files. If HEAD changes, restore this baseline revision for a comparable benchmark.

## Equivalence and tests

- Final **92/92 offline regressions pass** (`Ran 92 tests in 7.427s`, `OK`). No existing assertions relaxed.
- New tests check standalone, fully precomputed, HSV-only, and masks-only equivalence across the corpus; arrays are read-only and compared byte-for-byte afterwards. The fully precomputed path is checked not to recreate color masks or perform full-frame HSV conversion. Mission input identity is checked against its existing HSV/red/blue arrays.
- Final benchmark asserts exact Python list/dict equality against baseline for standalone and reused-input paths on **94 frames**: all embedded recorded PNGs, centered and border-clipped crops, recorded full frames, 24 seeded generated clutter/multiple-rim frames, a blank frame, and two recorded positive signs in one frame. There are **6 positive frames, 6 strong candidates, and 1 multi-candidate frame**. List equality checks candidate order and every field, including `strong`.
- Additionally, all **15 original perception tests** pass while comparing all **9 actual detector calls** directly against baseline at their original regression placements. This includes recorded positive/weak observations and negative roof/parking images.
- AST parsing and `compile(source, path, 'exec')` pass for both Python files, without creating pyc files. Structural AST comparison passes for the production invariants described above.
- Scoped `git diff --check` passes.

The harness stubs **only** an absent top-level `coppeliasim_zmqremoteapi_client` package. Missing transitive dependencies and unrelated import errors still propagate. Its stub constructor raises an explicit offline-I/O error. These tests do **not** validate a real remote API connection or simulator behavior; production imports are unchanged.

## Reproducible benchmark

From repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 orchestration/check_task3.py --benchmark
PYTHONDONTWRITEBYTECODE=1 python3 orchestration/check_task3.py
python3 -c "from pathlib import Path; import ast; paths = ('task3/task3.py', 'orchestration/check_task3.py'); [(ast.parse(Path(p).read_text(), filename=p), compile(Path(p).read_text(), p, 'exec')) for p in paths]; print('AST/compile OK')"
git --no-pager diff --check -- task3/task3.py orchestration/check_task3.py orchestration/TASK3_TIMING_RESULTS.md
sha256sum task3/task3.py
```

The benchmark runs baseline and candidate in the **same process**, sets OpenCV to **one thread** for both (no production thread-setting change), prepares the same ordered 94-frame corpus, warms both paths with **two complete sweeps**, and collects **nine samples**, reversing variant execution order on alternate samples. Each sample is total `perf_counter_ns` elapsed time over the corpus divided by frame count. No CPU affinity/frequency lock; normal host load and thermal variation remain. The standalone and reused-input rows exclude common caller preparation. The final two rows explicitly include the same existing HSV/red/blue preparation for both versions; baseline then repeats that work internally. Neither row measures full Mission latency or simulation time.

Final paired run, milliseconds/frame:

| Path | Median | Min–max |
| --- | ---: | ---: |
| Baseline detector standalone | 8.2814 | 7.8820–9.2413 |
| Candidate detector standalone | 5.4905 | 5.3343–6.9347 |
| Candidate detector with caller inputs | 4.2722 | 4.0048–5.6761 |
| Baseline shared preparation + detector | 10.6244 | 9.8943–12.9972 |
| Candidate shared preparation + detector | 5.7219 | 5.3870–6.7405 |

Measured median reductions: **33.7% standalone**, **48.4% detector marginal latency with reused inputs**, and **46.1% including shared preparation** on this corpus. This is an offline perception improvement, not a total-run speedup claim.

Nine samples, in collection order:

```text
baseline standalone: 7.9546,8.3551,7.8820,7.9947,8.2267,8.3213,8.2814,8.4318,9.2413
candidate standalone: 5.5838,5.4824,5.4905,5.3553,5.5911,5.3343,5.3823,6.9347,6.9144
candidate reused: 4.1807,4.4746,4.3355,4.2717,4.2722,4.0048,4.0294,5.6761,5.5764
baseline shared-prep + detector: 10.6244,10.5559,11.0932,9.8943,10.2928,10.4188,12.0429,12.9972,10.6830
candidate shared-prep + detector: 5.4338,5.5810,5.3870,5.3891,5.7219,5.7544,5.9064,6.7405,6.0457
```

Baseline cProfile on the final corpus: detector cumulative 0.789 s; connected components 0.308 s, `inRange` 0.112 s, dilation 0.073 s, HSV conversions 0.057 s. Profile time is diagnostic, separate from the timing samples. Connected-component labeling remains the largest unchanged cost.

## Outstanding official-run blocker

User-supplied feedback is **231.5 s**, Hospital **50/50**, speed **20/20**, collision **20/20**, parking **10/10**, late/not eligible. The exact submitted source and run log are unavailable. This baseline must **not** be identified as that submission. No supported simulator is installed on PATH and the remote API package is absent here.

Live timing remains **unverified**. The detector is conditional on an active/rearmed zone, so these measurements cannot explain or recover the **51.5 s** excess, prove eligibility, or establish a sub-180 s run. Diagnosis needs the exact submitted source/hash plus timestamped run log and preferably video, followed by a supported live run to distinguish wall-clock perception cost, simulated travel time, holds, and parking. Astra should review this diff and evidence before the team deliberately performs any submission.
