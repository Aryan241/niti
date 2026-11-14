Objective:
Recover a genuine oblique red Speed40 encounter using supported shape evidence, without restoring the confirmed Parking false positive. Luna implements/tests; Sol handles review and submission-requirement audit separately.

Read:
AGENTS.md, orchestration/LUNA.md, latest checkpoint; /private/tmp/task3-followup.ZNTHv6/oblique-exit-audit/REPORT.md and original-pixel-comparison.png. Current source ea3a4954d97dcced427beac4cf379b6a6bce64b6c20e0a732a4602135f6a7da8,77 tests. Weak white/blue exit fallback disabled; keep it disabled. Prior181/182s Hard timing used that invalid fallback and does not validate current source timing. Actual red Speed40 projected at Medium135.15 x384.6–393.6/y52.5–112.9 and Hard128.85 x414.7–427/y51.7–114.9; these are diagnostic labels ONLY, never controller coordinates. Accepted blue board70+pixels away is Parking.

Files:
Only task3/task3.py sign-candidate helpers/classification and necessary sign diagnostic hooks; orchestration/check_task3.py/results/checkpoint. Temporary offline helpers/fixtures in /private/tmp/task3-followup.ZNTHv6. Preserve unrelated dirty scenes/files.

One bounded candidate:
The normal detector already classifies Speed40 from a red circular outline plus a dark interior, rather than OCR. Literal readable40 is therefore not the only possible discriminative evidence. Inspect the actual RED board across saved sequences, including frames earlier/later than120–145. Test whether affine/perspective normalization of its red rim plus enclosed white/dark interior can distinguish a circle/ellipse from School's triangle and red obstacle/building trim under severe foreshortening. A normalized ellipse/rim residual or two-sided curved-rim evidence may support classification; a vertical red/white strip alone does not. Start with measured component sizes/fragmentation and current area120/150/aspect.45/circularity gates. Do not merely lower all thresholds. No scene-wide reverse engineering, learned model/downloads, timed/world/arena shortcuts, new external reference dependencies or guessed confidence.

Offline gate:
Use diagnostic projection labels to curate actual red-board ROIs and confusable School/Stop(if applicable)/Parking/Hospital/obstacle/building/background negatives from saved full frames. Never use the scene labels/coordinates at runtime. One generic candidate must reject embedded Parkingfalsepositives, preserve normal readable signs and remain conservative on ambiguous/clipped cases. If available original red pixels cannot distinguish its class, return concrete measurements and stop after this candidate; do not invent a release. No further broad sweep. Keep this phase concise and credit-conscious.

If supported:
Implement the bounded correction in the normal red perception path or separate red-only temporal classifier, retaining first-sight zone entry, rearm/distinct encounter, no release from absence or School or Parking, unchanged<=1.2 cap until true confirmation. All motion/parking/observer/gains/speed/stop constraints unchanged. Require positive and negative recorded-image regressions, mirror/scale/fragmentation checks, same-sign reappearance and distinct encounter/dropout tests. Confirm no-reference-images behavior and one-file compatibility. Run focused suite, syntax and scoped diff checks.

Live only after supported offline evidence/tests:
ONE clean Medium diagnostic using current controller-ready-before-engine rehearse_groundheading.py, /Users/aryanachary/.venv/bin/python, elevated localhost. Exact hash, absolute times, at most2startup attempts,300sbound. Capture red candidate features and tracker rearm/count in temporary instrumentation. No top-level--controller. Clean isolated HEAD scene; preserve workspace scenes. Restart identified stalledsimwithout saving authorized. If Medium safely proves actual distinctsecondSpeed40 and completes, ONE clean Hard regression on samehash. No further tuning/runs. Diagnostic truth never controls vehicle.

Return:
Changedscope/hash/testresults, original-pixel/shape measurements and semantic uncertainty, offline falsepositive/positive results, live timings/zone evidence ifauthorizedgatepassed, physicalparkpose/interpolationgaps, restduration separatedfromHospitalpatchlocation, speedmaxima, markermargins/misses, preservedfailures, stopped/zerostatus. No no-penalty/readinessclaim: Hospitalpatchcontainment, evaluator9cmsquarecollision/wheel>1cmoffroad, reliableHard<=180,Mediumtwice/Easyonce and officialsupportedplatformartifacts remain open. Return a focused recommendation, not an autonomous new tuning cycle.
