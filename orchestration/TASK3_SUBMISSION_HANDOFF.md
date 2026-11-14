# Task 3 submission handoff

**Status: not ready.** The full-score timing target is at most 180 simulation seconds; exceeding it is a scoring penalty, not automatic submission rejection. Reliable completion and scored rule compliance remain unverified on the current source.

Latest reviewed checkpoint (November 12): source `ea3a4954d97dcced427beac4cf379b6a6bce64b6c20e0a732a4602135f6a7da8`, 77 passing tests. An unsafe exit-sign fallback was disabled after it accepted a Parking-associated board. Historical Hard finishes at 181.05 and 182.10 seconds used the older fallback; they do not validate the current source's timing or correct Speed40 exit recognition. The corrected source's new Hard diagnostic logged parking at **238.25 seconds**, with no speed-zone exit; its dense capture wrote 840 pre-parking frames without drops. Physical and sign-visibility audit of that run is still pending. Artifacts: `/private/tmp/task3-dense-camera/dense-hard-ea3a4954/`. Read the latest checkpoint before copying code, because implementation work is ongoing.

The terminal-pose audit of that run measured center-forward distance 0.20616 m, front-lateral error -0.00378 m and heading error +1.769 degrees, using a 0.50 s matrix bracket. These satisfy the stated parking tolerances for that measured finish; they do not certify the whole route. Sign-object correspondence remains unresolved: projected Medium geometry cannot identify objects in Hard-run pixels. Two subsequent startup attempts processed zero frames and provide no additional driving evidence. The latest failed attempt started the engine despite an API reply timeout; it was subsequently stopped with both motor targets zero. Harness recovery is being corrected before further testing.

Before final recording, prove Hospital containment in the designated pickup patch as well as five seconds at rest; correct first/second Speed40 handling and command caps; obstacle avoidance using the evaluator's 9 cm square criterion; and wheel clearance within the road, including its yellow edges and the 1 cm allowance. Successful parking and absence of visible physics contact alone do not prove those scoring conditions. The local harness has not captured all of them. Final supported-platform evaluator evidence, encrypted CSV and matching video are not available yet.

## Current machine check

The reported attempts on the current machine ended as follows: `eyantra-autoeval evaluate --year 2026 --theme NV --task 3` failed with `ModuleNotFoundError` for `task3`; attempting `task3/Ubuntu_eval` failed with `Exec format error` because it is a Linux x86-64 ELF and the machine is macOS arm64. These are current-machine compatibility/launch outcomes, not a completed graded run. The supplied evaluator files are `Ubuntu_eval` (Linux x86-64) and `Windows_eval.exe` (Windows x86-64). Run the matching evaluator on a supported Ubuntu or Windows machine with CoppeliaSim open there; do not use this Mac attempt as a recording.

## Finish and record on supported machine

1. Finish and verify the controller target `<=180` in `task3.py`. Practice Easy, Medium, and Hard; the graded scene is the unmodified official `Task_3_Hard.ttt`. This workspace's Hard scene is preexisting dirty and is not certified as official: do not use it, present it as verified, or restore/change it. Use the official scene from your own clean checkout. Confirm Hospital halt inside its pickup patch for 5 simulation seconds, speed no more than 3.0 rad/s everywhere and 1.2 rad/s in the Speed 40 zone, obstacle avoidance, parking, and clean script exit. Do not edit the scene or use simulator object positions/orientations in controller code. Confirm the final one-file solution works without optional reference files omitted from the zip.
2. Activate the already configured team environment (no team ID is specified in this handoff) and run from `task3/` on the same supported machine where CoppeliaSim is open. Keep the official Hard scene loaded and stopped; close other simulator instances. Start one continuous screen recording before the evaluator, showing the whole CoppeliaSim window with simulation time and the terminal at both start and finish. Let the evaluator control the run; do not press Play or interrupt it.

Ubuntu:

```sh
conda activate <configured-team-environment>
cd ~/eYRC_26-27_Niti-Vahan/task3
./Ubuntu_eval
```

Windows Anaconda Prompt:

```bat
conda activate <configured-team-environment>
cd %USERPROFILE%\eYRC_26-27_Niti-Vahan\task3
Windows_eval.exe
```

3. After the evaluator finishes, stop and save the recording unchanged. Confirm it wrote `NV_Task3_run.csv`. The tool fingerprints `task3.py`: do not change its contents after the run, including comments or formatting, or the submitted script hash will not match. If code changes, make a new graded run and recording. The evaluator may not print local marks; the portal reports the marks after submission.
4. Upload the continuous, unedited video to YouTube as **Unlisted**, with the Team ID in its title; verify the link works in a private/incognito window.
5. From `task3/`, create the zip containing exactly these two files and nothing else:

```sh
python -c 'from pathlib import Path; from zipfile import ZipFile; files=("task3.py", "NV_Task3_run.csv"); assert all(Path(f).is_file() and Path(f).stat().st_size for f in files); z=ZipFile("NV_Task3.zip", "w"); [z.write(f, f) for f in files]; z.close()'
```

Check the archive names and contents are exactly `task3.py` and `NV_Task3_run.csv`; submit `NV_Task3.zip` and the matching video link through the portal manually. Do not upload through an agent.
