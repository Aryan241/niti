# Task 3 submission handoff

**Status: graded twice, current build banked at 59.50/80.** The first submission scored
**44.28/80** (55.35/100), losing every mark to the Speed 40 zone. The latch fix (see *The
Speed 40 finding* below) lifted it to **59.50/80** (74.38/100, run id `0170a5d8122a`), and
that run maxed four of the five blocks:

| Item | Result |
| --- | --- |
| HALT | 50.00 / 50 (held 6.0 s) |
| SPEED | 20.00 / 20 (at most 1.2 rad/s through the whole zone) |
| NO COLLISION | 20.00 / 20 |
| PARKING | 10.00 / 10 |
| TIME | 0 / 25, **-25.62** (3 min 51 s, 51 s over) |

The best score is kept, so anything below this can be ignored. The only remaining loss is
time, and the analysis below says most of it is structural - except for a probe build, in
*Probe build: a later zone entry*, which rehearses clean at 200.45 s but leans on the zone
starting at the top-bend sign, so it is a deliberate bet rather than a free win.

**Two things to confirm with the team before the hard deadline (16 Nov, 23:59):**

1. The portal labels this 3A run **"Late, not eligible"**. The Task 3A soft deadline was 9 Nov
   and the hard deadline is 16 Nov; if a late-but-before-hard submission carries no penalty
   then this is only a display label, but that has to be confirmed on the portal rather than
   assumed, because it decides whether 59.50 counts at all.
2. The uploaded pair must stay matched: the graded run was produced from sha256
   `fcbb86ae9dca2a6716fbd35ed58ab1dd302b870adce0cbc2717e7ff33bf41b17`. Do not edit
   `task3/task3.py` without a fresh recorded run.

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

## The two Speed 40 boards, and where the zone sits

The scene does contain two boards. `/Speed_40_Sign` sits at `(0.370, -0.820)`, beside the bay
and `ID_2`. The second one is misnamed: the object `/Cylinder`, at `(0.194, 1.205)` on the top
bend, is a copied sign plate - identical bounding box (`0.070 x 0.1625 m`, 7 mm thick), only
rotated - that kept its default alias. Both boards are roadside, about 0.10-0.13 m off the
traffic lane. That is worth a line in the viva; a search for objects named `Speed_40*` finds
only one of them.

The latched cap covers 3.73 m of path at 1.2 rad/s: 2.10 m from the first sighting at
`(-0.829, 0.856)` to the bay-board sighting at `(0.494, 0.191)`, then 1.63 m to the hand-over.
The old build's report bounds the zone's far end: it released at the bay-board sighting and was
counted over-limit for 24.6 s of the 28.2 s it spent covering those 1.63 m, so the zone ends
87% of the way - roughly 0.2 m before the hand-over, essentially at the bay board. The cap is
therefore within ~0.2 m of the zone at the exit and, at worst, 1.08 m early at the entry.

That entry margin is the only open question left. Our car sees the top-bend board from
`(-0.829, 0.856)`, 1.08 m before it passes abeam (closest approach 0.149 m at 90.5 s), so the
cap engages there. The graded run proves the zone does not start earlier than that point: at
`(-0.941, 0.530)` the car was commanded 2.99 rad/s and the report still awarded `SPEED 20/20`
with no `SPEED LIMITS` line at all. So the zone starts somewhere between the cap point and the
top-bend board, and the rubric's "the first one starts the Speed 40 zone" says it starts at the
board - which would make up to ~19 s of that crawl avoidable.

## Where the 25.62 lost marks come from

TIME is the only block left and it is structural. The lap is 6.83 m and the zone covers at
least 3.73 m of it, where 1.2 rad/s at the 0.0213 m wheel radius is 0.0256 m/s. A compliant
run therefore spends at least 146 s in the crawl alone:

| Leg | Length | Cap | Best possible | Measured |
| --- | --- | --- | --- | --- |
| Start to zone (includes the 6 s halt) | 2.32 m | 3.0 rad/s | ~42 s | 45.8 s |
| Zone crawl | 3.73 m | 1.2 rad/s | 146 s | 153.5 s |
| Parking manoeuvre | 0.77 m | - | ~21 s | 30.9 s |

The drive legs run at 91%, 96% and 94% of their caps; the rest is wheel slip, not a controller
defect. So the compliant floor is about 209 s with a perfect park and about 219 s at the
current park timing - 65/80 and 61/80. The one genuinely recoverable item is the parking
manoeuvre, which grew from 21.4 s to 30.9 s when the bay hand-over lateral rose to 0.29 m, and
that is the same corner where the rear-right wheel has only ~0.2 mm of audited margin. Spending
10 marks and a 30-mark off-road exposure to win ~4 marks of time is a bad trade, which is why
the current build stops here.

## What the second graded report decided

Both questions from the previous probe are answered, and both came out clean:

1. **Entry:** `SPEED 20/20` with no over-limit seconds anywhere. The cap engages at or before
   the evaluator's zone start, so no further crawl can be reclaimed upstream without risking
   the block. Sections above record the one remaining 1.08 m of uncertainty.
2. **Clearance:** `NO COLLISION 20.00/20` with no off-road deduction. The audited -9.8 mm at
   `(0.393, -0.822)` is inside the evaluator's line, so the bay turn and the trim are correct
   as they stand.

Best score is kept, so this stands whatever else is submitted.

## Probe build: a later zone entry

`~/Downloads/task3_probe_late_entry.diff` (patch, applies to `af462ef`) gates the cap on the
sign filling 6000 px^2 of the frame instead of on first sight, and holds the cap to the parking
hand-over as before. With the probe applied `task3/task3.py` is
`f0c1d3772124e67716d1dcdffba27c3628c30a24c9627750e45512abdcc229fa`.

| Rehearsal | Build | Cap engages | Parked | Bay sign clearance | Top board clearance |
| --- | --- | --- | --- | --- | --- |
| `base-bay-1` | `fcbb86ae` (graded) | 0.71 m from the board | 228.80 s | 29.2 mm | 96.6 mm |
| `entry-probe-1` | `f0c1d377` (probe) | 0.327 m from the board | **200.45 s** | 20.0 mm | 93.0 mm |

Clearances above are true minimum mesh distances from `sim.checkDistance` at each run's
closest pose, not centre distances. The probe is 10 mm tighter at the bay sign and still has
20 mm of air, which is more than the -9.8 mm the graded run was forgiven at that same corner.
Obstacle passes are unchanged (0.206-0.210 m), the halt still holds 5.2 s in one event, the two
lane changes are the same, and the capped window has **0 frames** above 1.22 rad/s.

`check_task3.py`: 89 of 90 pass. The one failure is
`test_first_sight_caps_even_distant_sign`, which asserts the old rule (cap on a distant sight);
it encodes the behaviour the probe deliberately removes, so it is expected, not a regression.

The entry is area-triggered, not timeout: the controller printed no `zone entry fallback`
line, so the cap fired because the board filled the frame 0.327 m out. That is geometry, so it
reproduces on a real run rather than depending on a timer.

**What is being bet.** The graded log shows the old build capping at a marker range of 0.71 m
(area 884 px^2). `SPEED 20/20` there proves the zone does not begin before that point, so the
true zone start lies in the 0.38 m between 0.71 m and the probe's 0.327 m - about 4.2 s at
3.0 rad/s. If the evaluator starts the zone at the board's plane (the rubric's "just before the
first sign"), the probe is clean and saves 10.2 s of crawl plus ~7 s of parking. If it starts
further out, those ~4.2 s are over the limit and SPEED costs up to 20 marks against a ~5-14
mark gain.

Per the marks table, time is -0.5 per second, so the 28.35 s saved is worth about +14 marks
(59.50 -> ~73/80) provided the entry is free.

To revert: `git checkout -- task3/task3.py` restores `fcbb86ae`, the banked build.


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
