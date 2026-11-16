# Task 3 v3 — guard against demonstrated oblique-exit speed regression

Objective:
User asks fix after v2 portal SPEED0/20 with24.6s overspeed, HALT50/50, collision20/20, parking10/10, ~182s portal versus185.10log. Root supported defect: v2 releases full cap on oblique-only pattern at137.50,bbox606,39,33,52, range.548, then evaluator reports still insidezone. Do NOT assume whether object is false or early; implement stronger readable-only release and safe fallback. Do not promise under180/fullspeed from offline tests.

Read AGENTS/LUNA, task3/task3.py, checker, task3_debug-4.log, v2 report. Files Luna may write ONLY:
- task3/task3.py
- orchestration/check_task3.py
- NEW orchestration/TASK3_V3_RESULTS.md
- NEW submission_packages/NV_Task3_TEST_v3.zip
- NEW submission_packages/NV_Task3_TEST_v3_README.md
Parent owns this workorder, review. No commits/push/main changes during implementation. Preserve root logs and v1/v2 archives exactly. No CSV reuse/submission zip creation.

Implementation decision:
Retain existing first-sight entry, near/travel/absence/distinct rearm, 2frame raw route confirmation and weak-pattern regressions. Decouple ROUTE progress from permission to accelerate. Oblique-only distinct encounter may setzone_done/routeexit but must keep zone_speed_holdtrue. That is original safe cappedparking fallback, not successfulzoneproof.
Maintain independent readable-exit SignTracker using ONLY normal detect_signs Speed40 candidates meeting stricter clear-face criteria: near-frontal aspect roughly.75..1.33, width+height>=24px each, area>=400 (tune only if recorded readable positives evidence justifies). Need first readable near encounter+absence/travel rearm, then distinct farther readable object with THREE spatially consistent observations to accelerate. Tentative/strong oblique candidates NEVER feed that readable verifier. First normal sign still caps immediately even if too small for verifier. Competing/multiple normal candidates must not be filtered down to unique without resetting/readableconfirmation; avoid suppressing truefirstentry. No acceleration from routeprogress/School/elapsedtime/commanddistance alone. This policy does not prove officialboundary or glyphidentity and may fallback entirely to lateparking; document honestly.

If separate verifier improves clean code more than above, use helper/class existing patterns, no newdependencies/globalstates. Final cap stays <=1.2 if routeexit confirmedweakbutreadableverifiercount<2. Preserve parkedhandover fallback releaseshold (whileactivezone stillcaps). As before hold gone only readableexitconfirmed or originalparking. Continue normal sign perception while routecompleteholdtrue, but no extra oblique/fullframework afterweakroutecount2; parkedshortcut must preserve cap until fallback.

Logging:
Startup 'Task 3 TEST v3' existing sourcepath+SHA. At oblique routeconfirmation print exactcandidate bbox,range/source and 'cap retained: readable exit unverified'. At readable verifier activation/secondconfirm compact logs normal evidence bbox,range,streak/count, 'readable second Speed40 confirmed: cap released'. If normal exitcandidate rejected, log concise reason/changes only when NV_VERBOSE, avoid dumping eachframe. On parkingfallback saycapreleasedforparking (existing). Do not claim physicalpassproof.

Tests:
Exact regression for log4 obliquebbox606,39,33,52 may complete route but must NOT command>1.2 even later dropout/travel. Known strong/tentative/reacquired/multiple/weaknever readable release. Normal readable secondneeds3 and boundedcommands. Only firstsmallmustcap. Readable nearfirst absence rearm&samefirstsign rejection. 2 normalsplus1weak duplicate safe. Invalidframes+pause/timing reset readableobservationidentity. No duplicated firstcountupdated sameframe. Existing hospital/parking/posecontrol tests unchanged; don't retune Parker/PoseEstimator. Replace v2 intentionalobliquerelease assertions with correct caps, preserve sourceidentity/runtime/perception/baselineequivalence checks. Normalfilter tests mirrored,toosmall/thin,multiplemixed eligible/ineligible. Missing secondnormal leavesknownfallback. Fullsuite, ASTcompile,no .pyc, scopedwhitespace.

Packaging:
New v3 ZIP exactlytop-leveltask3.py matchingproductionhash, verifyCRC/content. README testonly, useextractedscript, checkprintedhash, getnewCSV+log+feedback especially SPEED. State strictreadableexit maynotappear so fallbackcanrestoreoldslowtiming; no fixed24.6sdelay/no scenes/worldposes. Historical evaluatorpenalty vswording unresolved. Existing v2 ZIP mustnotbe overwritten or pairedwithnewCSV.

Expected final evidence:
Exacthash/testcount/commands and candidatearchive; snapshotguard against exactfailedbbox/source branch; compare AST PoseEstimator/Parker to v2 unchanged. Explain regressions targeted and no live validation. Do not pretend fulltimegoal complete: nextuser test mustfirstverifySPEED, and video/capturedframes arestillneeded if readableexitneverappears. No blindnewtiming/parkingparameters.
