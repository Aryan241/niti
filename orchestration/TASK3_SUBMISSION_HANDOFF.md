# Task 3 submission handoff

**Status: ready to record, not yet graded.** The controller completes the official Hard
arena, parks, and stays inside the road on the latest audit. No run has been made with the
supplied evaluator (`Ubuntu_eval` / `Windows_eval.exe`), because both are Linux/Windows
binaries and this machine is macOS arm64. That graded run is the remaining step and it needs
a supported machine.

Current source: `task3/task3.py`, sha256 `c597a2d5f8cd46dbb802556d2493a1ab3a69cadc92697e03f9ad904f7fa7eda4`,
87 passing offline tests (`/Users/aryanachary/.venv/bin/python orchestration/check_task3.py`).

## How the run is actually scored

Task 3A is 80 marks: score out of 100, then scaled by 0.8.

| Earn | Marks | Lose | Marks |
| --- | --- | --- | --- |
| Halt 5 s at the Hospital pickup point | +50 | Off-road (wheel >1 cm past the edge) | -30 each |
| Speed limits kept (3.0 rad/s, 1.2 rad/s in Speed 40) | +20 | Collision | -30 each |
| No collision | +20 | Over 180 s | -0.5 per second |
| Park | +10 | Over the speed limit | -1 per second |

Consequences worth keeping in mind:

- Timing is nearly free. Finishing in 180.85 s instead of 180.0 s costs 0.43 marks out of
  100, about 0.3 after scaling. Do not trade road clearance or parking for seconds.
- One off-road event costs 30 marks, one collision 30 marks. These dominate everything else.
- The score cannot go below 0.

## Measured behaviour on the official arena

All three rehearsals below ran the unmodified official `Task_3_Hard.ttt`
(blob `370d8299033e8b14384eea1d49781b26a2c61434`) in a single CoppeliaSim instance, with
wheel clearance audited from true wheel matrices.

| Run | Source | Wheel clearance | Finish | Terminal lateral | Terminal heading |
| --- | --- | --- | --- | --- | --- |
| `robust-v6-phase-audit` | earlier | -23.2 mm | parked | -3.8 mm | +1.77 deg |
| `tire-baseline-repeat-1` | `3834422` | -8.5 mm | 182.55 s | -8.2 mm | +3.21 deg |
| `tire-trim-corner-1` | current | **-3.7 mm** | **180.85 s** | -2.3 mm | -1.72 deg |

No run has crossed the 1 cm allowance, and none reported a collision. Wheel speeds peaked at
exactly 3.0 rad/s, 1.2 rad/s inside the Speed 40 zone, and the Hospital halt held 5.2 s with a
single halt event in every run.

The remaining -3.7 mm is the rear-right wheel at the bay-mouth corner. A pure lateral offset
cannot fix it: the front-right corner improved 24 mm with the same trim, but the rear-right
is yaw-driven, so only ~5 mm of the 30 mm trim reached it. Pushing the trim harder does help
the corner but starts spending parking alignment, which is a 10-mark and possibly
run-invalidating trade. This is the deliberate stopping point.

## The arena file

Commit `acf6dc2` had committed a modified `task3/Task_3_Hard.ttt` (blob `0a1da73e`,
38,505,675 B) that differed from the official arena (blob `370d8299`, 38,505,611 B). The
evaluation tool refuses to grade a run whose arena has been altered, so that file was restored
to the official blob in commit `ab245bc`. The working tree now matches `origin/main` exactly.

Safest instruction for the graded run anyway: use the official scene from your own clean
checkout, and copy only `task3.py` into it. Do not hand over a modified scene.

## Finish and record on a supported machine

1. Get a clean official checkout and put the current `task3.py` in `task3/`. Do not edit the
   scene. Confirm `git hash-object task3/Task_3_Hard.ttt` prints
   `370d8299033e8b14384eea1d49781b26a2c61434`.
2. Activate the team environment and run from `task3/` on the same machine where CoppeliaSim
   is open. Keep the official Hard scene loaded and stopped; close every other instance, since
   the client talks to the default port 23000. Start one continuous screen recording before
   the evaluator, showing the whole CoppeliaSim window with the simulation time and the
   terminal at start and finish. Let the evaluator drive; do not press Play or interrupt.
3. After it finishes, stop and save the recording unchanged, and confirm `NV_Task3_run.csv`
   exists. The tool hashes `task3.py`: do not change it afterwards, not even a comment, or the
   script hash will not match the run. Any code change needs a fresh run and recording.
4. Upload the unedited video to YouTube as **Unlisted**, with the Team ID in the title, and
   check the link in a private window.
5. From `task3/`, zip exactly the two required files:

```sh
python -c 'from pathlib import Path; from zipfile import ZipFile; files=("task3.py", "NV_Task3_run.csv"); assert all(Path(f).is_file() and Path(f).stat().st_size for f in files); z=ZipFile("NV_Task3.zip", "w"); [z.write(f, f) for f in files]; z.close()'
```

Submit `NV_Task3.zip` and the matching video link through the portal manually. No agent
submits anything.
