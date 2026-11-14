# Agent collaboration protocol

This repository uses two optional roles:

- **Astra** is the thinking and review agent. Astra studies the task instructions, creates one precise work order, and reviews Luna's final result. Astra does not edit files or run implementation commands.
- **Luna** is the execution agent. Luna edits the requested files, runs checks, debugs failures, and reports the exact changes and results.

The role prompts live in `orchestration/ASTRA.md` and `orchestration/LUNA.md`. Use `orchestration/WORK_ORDER.md` for each handoff.

## Handoff rules

1. Astra writes one complete work order before Luna edits code.
2. Luna stays within the named files and constraints unless a blocker is reported.
3. Luna owns the full implementation and verification loop and records the evidence.
4. Astra performs one final review of the diff and test results, then either requests a focused correction or declares the work complete.
5. Neither role submits code to the e-Yantra portal. Submission remains a deliberate manual action by the team.

Keep generated reports and temporary outputs out of the submission files unless the task instructions explicitly require them.
