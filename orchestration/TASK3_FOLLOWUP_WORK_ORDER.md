Objective:
Current November 8 priority: eliminate avoidable time penalties. Previous narrow closeout is superseded. Luna model owns execution; target Hard completion within 180 simulation seconds without speed, halt, collision, off-road or parking violations. This is a target, not permission to fabricate observations or claim official grading.
Fix remaining Task 3 perception and completion-time problems identified in the November 6 review. Diagnose actual camera evidence before changing thresholds; improve robustness without bypassing task requirements.

Files:
- task3/task3.py
- orchestration/check_task3.py
- orchestration/TASK3_RESULTS.md
- Temporary harness/data only outside submission files.

Constraints:
Read AGENTS.md, LUNA.md, the pasted official Task3 instructions and previous review. Preserve all existing unrelated dirty files and scene hashes. Single camera-only controller; no ground truth, teleporting, scene edits, simulation ownership, fixed route timing or fabricated sign exit in submitted code. Do not weaken speed limits, Hospital stationary hold or parking acceptance. No commit/push/submission. Keep reporting explicit if official evaluator cannot run on macOS.

Acceptance criteria:
1. Investigate missed second Speed40 using saved and newly captured frames; repair detector/tracker if visually observable. Never release speed cap without evidence of distinct exit sign. If genuinely unobservable, document image evidence and safe remaining limitation.
2. Reject blue building/object false positives while retaining true Hospital/Parking detection, including absent reference_images fallback. Use real positive/negative crops and regression checks.
3. Investigate false obstacle encounters, late Hospital arming, outer parking narrow margin and excess runtime. Correct evidence-backed defects in scope; reduce avoidable delays while retaining safety. Do not promise sub180 if physical speed-zone length prevents it.
4. Repeat final source on Hard twice, Medium and Easy; retain exact source hash, camera events, timing and final pose. Capture failures and debug until safe completion or a concrete external blocker.
5. Run full offline regression, compile, scoped diff check, self-review and report measurements versus previous results. No unofficial score claim.

Verification commands:
First establish simulator access using a bounded localhost ZMQ state query; sandbox process-list denial alone is not proof the simulator is unavailable. Escalation for local API/process inspection is allowed. Do not interfere with an unrelated active controller. Reuse saved evidence and existing harness; avoid broad setup work. Before repeated tuning, measure where time is spent and estimate attainable legal runtime. Send a concise finding if the 180-second target is infeasible under the observed zone/path constraints.
/Users/aryanachary/.venv/bin/python orchestration/check_task3.py
Use existing /private/tmp/task3-review.5AMtFI/rehearse.py or a temporary improved harness. Simulator access may require sandbox escalation. Only this worker owns simulator during execution.

Expected evidence:
Updated report with root causes, source hash, commands, positive/negative detector checks, final repeated run results, limitations and preservation checks. Inform Astra with meaningful milestones; own full execution/debug loop without routine approval.

Focused exit experiment:
Native hard-final-2/camera-00132.85.png board at x520:552,y40:97 contains only20red pixels split into10fragments (largest6),78bluepixels; grouped red hull has45%white/36%dark. Existing120pixel component gate necessarily misses it. These coordinates are diagnostic crop annotations ONLY, forbidden in controller. Investigate image-wide white-board/blue-board candidates and spatially grouped red fragments with perspective-normalized ellipse/arc plus white/dark evidence; require temporal confirmation and reject pizzeria/building/School negatives. A generic lowered threshold without shape support is not acceptable. First replay saved native full frames across the entire lap to establish exit recall and false events; implement only if visually supported. Then address post-confirmation cruise and parking speed schedule using curvature, pose and stopping distance; keep all acceptance tolerances and caps. Retain a pre-experiment source snapshot and roll back any unvalidated/unsafe detector change. No coordinate/time-based exit inference.
