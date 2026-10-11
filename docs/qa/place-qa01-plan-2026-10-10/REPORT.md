# PLACE-QA-01 — scope investigation, 2026-10-10

Mode: AUDIT / PLAN. Executor: `/root`, sequential source investigation under canonical kidsmap-orchestrator and frontend-reviewer definitions. No independent specialist execution claimed. Application implementation has not been authorized or performed.

## Snapshot and preservation

Actual checkout: `C:\kidsmap`, branch `task33-progress`, LOCAL HEAD `8d188b316f800fbedf0b1e376905dfd4924cb1b6`. Shared journal reports `active_run: NONE`; historical `source_head` in that journal is not the current HEAD. PRODUCTION: not accessed; current state UNKNOWN.

Incoming changes: modified `docs/qa/module-acceptance-prompts.md`; untracked `docs/qa/module01-2026-10-09-r1/`, `module01-2026-10-09-r2/`, `module02-2026-10-09-r1/`, `module03-2026-10-10-r1/`. No incoming files were edited. No process or stand was stopped/reconfigured. Observed listening QA ports included 8781, 8811, 8812 and 55431–55434; this observation does not establish health or ownership.

## Source findings

- `src/catalog/templates/pages/includes/owner_place_continuous.html:7` renders lifecycle but no `review_note` block. This is the template reached by `owner_place_edit.html` → `permanent_place_form.html`.
- `src/catalog/views.py:1384` includes the revision in GET and invalid-POST context. The controller obtains the managed place and verifies edit permission before providing the form.
- `src/catalog/models/volunteer.py:15` makes the Place relation one-to-one; no extra latest-revision query is required.
- `src/catalog/services/publication.py:408` saves the moderation reason. Line 360 preserves it on draft save and clears it on submit. Showing only rejected/declined would lose useful feedback after an explicit draft save; the proposed block also handles a draft with a saved reason.
- Localization already uses `permanent_place_wizard.ui_copy` and `permanent_place_rules.copy(ru, az, en)`. One localized heading is sufficient; the moderator's text remains verbatim and escaped.

Conclusion: PLACE-QA-01 remains supported by current source. High confidence in the rendering omission. Historical browser/DB evidence remains dated 2026-10-09; fresh runtime behavior is NOT VERIFIED in this planning phase.

## Discovery limits and commands

Codebase Memory project `C-kidsmap` matches checkout/branch/HEAD. Architecture, symbol search and depth-1 trace were used before targeted source reads. The narrowed search returned all six matching source symbols (`has_more=false`); the earlier broad query was narrowed instead of treated as exhaustive. Trace identified `_place_revision_context` → `owner_place_edit` but does not cover dynamic ORM/template relationships.

Coverage checks reported `metadata_changed`, `coverage_unavailable` for Python/CSS paths and partial parsing of continuous template line 35. Index generation initially 2026-10-09T21:09:07Z, later 2026-10-10T06:16:33Z during auto-refresh. Relevant source was read directly; no graph completeness claim or graph cache export.

Fresh environment checks: `.venv/Scripts/python.exe -I -c "import sys, django; print(sys.version.split()[0]); print(django.get_version())"` printed Python 3.12.15 / Django 6.0.2. `wsl.exe --exec docker version --format '{{.Server.Version}}'` exited 0 and reported Docker server 29.1.3. No container was created.

Several preliminary `rg` calls used shell-unexpanded wildcard path arguments on Windows and reported OS error 123 / exit 1; subsequent directory-scoped or exact-path reads supplied the relevant source. A nonexistent legacy include guess also failed; actual include wiring was then verified in `permanent_place_form.html`. These were discovery-command errors, not application test failures. The final exact snapshot/source verification commands and their native exit codes are recorded in `command-ledger.jsonl`.

## Proposed impact and verification

[Concrete implementation plan](../../superpowers/plans/2026-10-10-place-qa01-rejection-feedback.md): five application/test paths plus a new isolated QA evidence directory. Backend/domain/ACL/models/migrations stay outside the proposed edits. Security checks cover escaping and non-disclosure through existing ACL. Browser checks include actual rejection → reload → logout/login → correction/save → resubmit and AZ/RU/EN × five viewport widths.

Executed: source/graph investigation, current Git/journal/environment checks, plan preparation and final documentation/snapshot verification.

NOT RUN: fresh fixture DB, new regression tests, application changes, rendered browser reproduction/screenshots, full application suite, production, real external integrations, commit/push/deploy. Existing screenshots were not presented as fresh evidence.

Next: user approval of the linked scope, then fresh isolated baseline and RED test before application edits. This audit does not itself grant implementation authorization. The finding remains OPEN / P2.
