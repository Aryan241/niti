# Task 3A results (local, unofficial)

Date: 2026-11-05. Solution: `task3/task3.py` (single file; imports only os/sys/time, cv2, numpy, ZMQ client).
`task3/reference_images/` (copied from 2B) is used at run time but must NOT go in the zip.

## Arena facts used (from the scenes and portal Figure 4)
- Lap is clockwise from spawn; start in the inner lane.
- Hard obstacles: left straight outer lane (ignore), top straight inner lane (change to outer),
  right lobe outer lane (change back to inner). Medium's third obstacle is hidden (layer 0).
- Hospital pickup: inner lane beside the red cross, ~0.565 m before the far Hospital sign.
- Parking: ArUco ID 1, spot centre ~0.20 m from the marker on the bay centre line.

## Behaviour
- Lane following: 2A detector + lane preference (yellow left/right of divider); lane change = flip preference.
- Obstacles: 2B red detector (strict white test), in-lane test against the divider, triggers only while ahead.
- Speed: 2.90 rad/s outside, 1.19 rad/s from the first Speed 40 sign (range <= 0.32 m, or seen within
  0.65 m then lost) to the end of the run (the second sign is not reliably visible clockwise).
- Halt: armed by a Hospital sign first seen > 0.75 m away; frame-rate-aware predicted stop; holds
  5.0 + 0.8 s of simulation time after rest is detected from frame differences.
- Parking: 2C pose estimator + smootherstep lateral path; stops at 0.20 m; script exits after 1 s settle.

## Local monitor results (dev-only scorer in scratchpad, ground truth from the sim)
Final version, Hard arena:
| Run | Off-road | Collisions | Over limit | Halt (s, along error) | Parked error | Min wheel margin | Time |
|---|---|---|---|---|---|---|---|
| normal x4 | 0 | 0 | 0 s | 5.9–6.4, ~1.5 cm | ~2 cm | ~1.9 cm | 224–227 s |
| +20 ms/frame (~0.36 s/frame) | 0 | 0 | 0 s | 6.7, 1.4 cm | 1.4 cm | 2.2 cm | 231 s |
| +30/40 ms (~0.65–0.7 s/frame) | 0–1 | 0 | 0 s | ~2 cm | parking fails | – | 290–300 s |

Easy 217 s and Medium 255 s complete (earlier build of the same logic).
Expected Hard score by the published scheme: ~100 − 23 (time) ≈ 77/100 ≈ 62/80. Not portal-graded.

Time budget (normal run): Speed 40 zone ~118 s at 1.19 rad/s (fixed); parking ~30 s at 1.19
(second sign not visible clockwise, so the zone cap is held); halt 6 s; rest at <= 2.9 rad/s.

## Remaining risks
- Graded run needs Ubuntu_eval or Windows_eval.exe (no macOS tool). Reliable up to ~0.36 s of sim time per
  processed frame (printed in the halt message); beyond ~0.6 s/frame parking degrades.
- Zone start position assumed "just before" the first sign; we slow ~0.25 m before it.
- `NV_VERBOSE=1` enables debug prints; off by default.
