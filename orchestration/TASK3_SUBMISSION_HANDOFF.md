# Task 3 submission handoff

**Status: graded once, fix landed, needs graded run #2.** The team's Task 3A submission
scored **44.28/80** (55.35/100). Every mark lost came from one defect: the Speed 40 zone.
That is fixed in the current `task3.py` (see *The Speed 40 finding* below), so a resubmission
is expected to land near **60/80**.

The evaluator (`Ubuntu_eval` / `Windows_eval.exe`) only runs on Linux/Windows, so the graded
run has to happen on a supported machine; this macOS arm64 box rehearses on the same official
scene instead.

Current source: `task3/task3.py`, 90 passing offline tests
(`/Users/aryanachary/.venv/bin/python orchestration/check_task3.py`).

Submit exactly the committed file - commit `af462ef`, sha256
`fcbb86ae9dca2a6716fbd35ed58ab1dd302b870adce0cbc2717e7ff33bf41b17`. Any edit, even a
comment, changes the hash the evaluator records and needs a fresh run.

## How the run is actually scored

Task 3A is 80 marks: score out of 100, then scaled by 0.8.

| Earn | Marks | Lose | Marks |
| --- | --- | --- | --- |
| Halt 5 s at the Hospital pickup point | +50 | Off-road (wheel >1 cm past the edge) | -30 each |
| Speed limits kept (3.0 rad/s, 1.2 rad/s in Speed 40) | +20 | Collision | -30 each |
| No collision | +20 | Over 180 s | -0.5 per second |
| Park | +10 | Over the speed limit | -1 per second |

Consequences worth keeping in mind:

- Time was nearly free and no longer is. The compliant Speed 40 crawl alone puts the finish
  at about 228 s, so 48 s over the 180 s line is -24 marks out of 100. Every second saved
  inside that crawl is worth 0.4 marks after scaling, but see the next point.
- One off-road event costs 30 marks, one collision 30 marks. These dominate everything else.
  Do not trade road clearance or parking for seconds - the crawl above is already the
  compliant minimum, and cutting it is what produced the 44.28.
- The score cannot go below 0.

## Measured behaviour on the official arena

All rehearsals below ran the unmodified official `Task_3_Hard.ttt`
(blob `370d8299033e8b14384eea1d49781b26a2c61434`) in a single CoppeliaSim instance, with
wheel clearance audited from true wheel matrices and pose logged from the simulator.

| Run | Build | Wheel clearance | Finish | Terminal lateral | Terminal heading |
| --- | --- | --- | --- | --- | --- |
| `robust-v6-phase-audit` | earlier | -23.2 mm | parked | -3.8 mm | +1.77 deg |
| `tire-baseline-repeat-1` | `3834422` | -8.5 mm | 182.55 s | -8.2 mm | +3.21 deg |
| `tire-trim-corner-1` | pre-latch | **-3.7 mm** | **180.85 s** | -2.3 mm | -1.72 deg |
| `zone-hold-1` | current | -8.5 mm | 228.35 s | -0.2 mm | +0.36 deg |
| `hold-a` | current | -9.8 mm | 228.80 s | +0.4 mm | -0.31 deg |

No run has crossed the 1 cm allowance, and none reported a collision. In the two current
runs, **0 frames** were commanded above 1.2 rad/s while the zone flag was set, and the
Hospital halt held 5.2 s with a single halt event. The 48 s of extra finish time against the
pre-latch build is the price of compliance: it is time the graded run spent illegally fast.

A third current-build rehearsal with `MERGE_CLEARANCE = 0.040` (`trim40-hold-1`) was
**rejected**: it over-rotated the bay-mouth merge, lost the target marker at 218.30 s with
heading -0.71 rad and never parked.

The rear-right wheel at the bay-mouth corner remains the tightest point. A pure lateral offset
cannot fix it: the front-right corner improved 24 mm with the same trim, but the rear-right
is yaw-driven, so only ~5 mm of the 30 mm trim reached it. Pushing the trim harder does help
the corner but starts spending parking alignment, which is a 10-mark and possibly
run-invalidating trade. This is the deliberate stopping point.

**Watch this number.** The current build is 0.2 mm inside the 1 cm allowance (-9.8 mm) at
`(0.393, -0.822)`, the corner beside the Speed 40 sign, where the 180 degree bay swing carries
the rear-right wheel. The pre-latch build had 6 mm of margin there. If the next graded report
shows an off-road deduction, this is the cause, and the fix is to make the bay turn start
earlier rather than to push the trim further.

## The Speed 40 finding

The graded report for run `850eb52a1297` reads:

| Item | Result |
| --- | --- |
| HALT | 50.00 / 50 (held 6.0 s) |
| SPEED | **0.00 / 20** (24.6 s over the limit, top speed 3.00 rad/s) |
| SPEED LIMITS | **-24.65** |
| NO COLLISION | 20.00 / 20 |
| PARKING | 10.00 / 10 |
| TIME | 0 (finished in 3 min 0 s) |

The rubric says speed is the wheel speed **the code commands**, and that the zone "starts just
before the first Speed 40 sign and ends at the second one". The old controller released the
1.2 rad/s cap the moment it saw the second sign. The evaluator kept counting for another
24.6 s, which is almost exactly the whole 28.2 s the old code spent between that sighting and
the parking hand-over. So the camera cannot tell "still approaching the sign" from "just
passed it", and the release was roughly 1.2 m early.

The fix latches the cap at zone entry and releases it only at the parking hand-over. The
crawl is unavoidable either way - the zone covers all but the last ~0.25 m of that stretch -
so the whole cost is a few seconds, against 44.65 marks of exposure.

One scene fact is worth knowing for the viva: `Task_3_Hard.ttt` contains a single
`/Speed_40_Sign` object, at `(0.370, -0.820)`, right beside the bay and `ID_2`. Logged
trajectory from `hold-a` shows the car first sighting a Speed 40 board at `(-0.829, 0.856)`
on the far side of the loop, 2.06 m from that object, and the cap then covering 2.1 m of path
around the top and down the right side to the bay - so the "two signs" of the rubric are the
two passes of the Speed 40 signage around the loop, not two separate boards.

Expected score for the current build: 100 - 0.5 x (228.8 - 180) = 75.6, times 0.8, about
**60/80** (range 59-61 depending on where the finish lands). That is +16 marks on the current
44.28.

## What the next graded report decides

Two things only the evaluator can answer, and both are read straight off the next report:

1. **Does it start counting before our first sighting?** If `SPEED` is 20/20 and no
   `SPEED LIMITS` deduction appears, our entry is early enough and the zone timing is
   finished. Any residual over-limit seconds mean the zone starts further back than the
   first detection, and the fix is to cap earlier, not later.
2. **Is -9.8 mm inside the off-road line?** A clean `NO COLLISION 20.00/20` with no
   off-road deduction means our wheel envelope is conservative enough and the bay turn can be
   left alone.

Both answers are available from one submission, and the best score is kept, so a probe run
cannot damage the 44.28 standing.


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
