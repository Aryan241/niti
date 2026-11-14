# Focused implementation handoff

Implement and validate image-only recognition of the second oblique Speed40 sign.
Read AGENTS.md, LUNA.md, TASK3_ASTRA_FINISH_WORK_ORDER.md; this narrows the next
implementation step, not the overall submission objective. Do not run another
dense simulation or repeat geometry provenance audits. Preserve dirty scenes.

Current source ea3a4954d97dcced427beac4cf379b6a6bce64b6c20e0a732a4602135f6a7da8;
77 tests. Corrected-source last Hard parked237.65, no zone exit. Saved same-run
954 frames, geometry, normal detections, state and commands:
`/private/tmp/task3-dense-camera/runtime-identity-dense-final/`.
First sign is generic /Cylinder handle56; second named handle47. Geometry is
diagnostic labeling only, never controller input. At132s actual second rim has
17 red pixels, largest component9; normal component threshold120 rejects it.
First sign rearm precedes this encounter. Actual right-edge sign is visible
beside overlapping Parking. Parent visually confirmed readable40 in deskewed
`/private/tmp/task3-dense-camera/patch-check/positive-target-v2.png`.

Use that image and `patch_extractor_check_v2.py` to understand successful target
localization. Prior prototypes are failed experiments, not designs to preserve.
They repeatedly: scored storefront proposals as targets; used dilation padding
as face boundaries; discarded thin fits; compared whole merged Parking+sign
patches to face-only references; or failed to replay the encounter tracker.
Final-oblique-eval scanned954frames/2378proposals but OMITTED real target and
tracker; do not cite it as recognition evidence. Do not repeat these mistakes.

Allowed code: task3/task3.py, orchestration/check_task3.py; temporary diagnostics
under/private/tmp; update results/checkpoint. Choose a small robust recognizer
from actual image evidence. Group fragmented rim with adjacent face/glyph,
separate or mask blue neighbor, preserve meaningful geometry. Match visible
structure or learned first-sign appearance consistently; ORB on resized tiny
patches is not mandatory. No per-scene coordinates/times, lookup of trial images,
global poses, fake speed releases, or restoration of generic blue-board fallback.
Keep normal first-sign detection and conservative caps. A recognizer should
accept first-sign reacquisition; distinct encounter is existing tracker logic.

Required output: reproducible candidate that includes actual132s sign and
rejects non-Speed40 imagery; inspect patch images yourself. Calibrate known
readable positives first, then recorded oblique positives and existing Parking,
School, obstacle, storefront negatives. Replay complete954frame stream WITH
normal detector and actual tracker using recorded timestamps/travel. Assert
one entry and one visually justified distinct exit, no release from same first
sign. Test saved older Hard/Medium as held-out data where available. Threshold
chosen only from calibration, not arbitrary tuning until one run passes.
If candidate passes, integrate self-contained code + focused regressions, run
77 baseline suite plus new tests, syntax/diff review, then one light cleanHard
run with known resilient harness. Exact hash, actual exit image/event, elapsed
time, terminalpose and caps required; follow remaining full work order if pass.

Own the debug loop. Do not end after an avoidable prototype bug or claim
external blocker merely because first algorithm fails. If genuinely no supported
candidate, return actual matched positive/negative patches and measured overlap
with correct localization and calibrated easy-positive behavior. No more broad
audits or repeated empty reports. No children. No commit/push/portal.
