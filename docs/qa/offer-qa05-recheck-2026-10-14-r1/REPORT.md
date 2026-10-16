# OFFER-QA-05 fresh recheck — OPEN / P3

2026-10-14; root sequential, canonical kidsmap-orchestrator. PLAN / AUDIT ONLY.
Checkout `/home/ramin/kidsmap`, branch `task33-progress`, HEAD `e4e05cc213b34e2d771ecb854901bfd016d1db51`; incoming dirty WORKTREE preserved; active_run NONE. See snapshot.json and incoming-manifest.json.

Fresh native reproduction: 24 cells, 11 with a badge exceeding the visible pane. Group all six widths × RU/AZ/EN; Program/Activity390 × all languages. At RU390 group badge ends325.05 inside pane ending322; scrollWidth257 > clientWidth254 with scrollLeft0. At RU360 group badge ends325.05 inside pane292. Program/Activity RU390 validation badge ends390.81 beyond322. Root document overflow false: root-only checks miss clipping. PNG manually viewed: offeringgroup-ru-360.png visibly truncates status. matrix.result.json and png-manifest.json hold24 native screenshots/geometry; these are baseline FAILs, not repair acceptance.

Cause: static/admin/css/kidsmap_admin_components.css:252–263 sets inline-flex + white-space:nowrap. BusinessEditor publication_badge/ownership_badge/verified_badge renders longer text in readonly fields; Jazzmin tab-pane overflow:auto clips initial view. Source and DOM inspected. Graph symbol/coverage discovered; trace had heuristic mis-resolutions, so actual source/template wiring is authoritative.

Own previously created OFFER04 isolated stand revalidated today: PID58504 exact runtime.py command, loopback55765, database offerqa04fix_20261013_r1 at127.0.0.1:35521. Receipt testing=true, entry/startup/disk all match,2804 files; LocMem cache/email, own media/private-media, no .env, egress only own PostgreSQL. Current RU/AZ/EN PO manifest verification executed by runtime before django.setup in seed command; sole isolated locale root from snapshot. No new locale compilation required for source-read recheck, PO untouched; implementation verifies its own profile/build anew. Existing accepted OFFER04 fixtures untouched: only new fictional OFFER05 prerequisites added, non-superuser staff with explicit place.edit/program.manage grants plus platform reviewer permission; fixture ACL checked. No processes stopped/restarted, no active_run assignment. Foreign stand availability NOT RUN.

Commands: see seed.command.json (exit0), commands.jsonl (recheck.js and matrix.js native CLI exit0; matrix baseline has FAIL cells), harness sources and result files. Browser opened using `playwright-cli -s=offerqa05recheck-20261014-r1 open http://127.0.0.1:55765/admin/login/` exit0. Screenshot generation native; language switches and State tabs native. Page errors0, local HTTP error responses0. External Google font requests blocked; external integration acceptance NOT RUN. Initial artifact command `python` unavailable exit127, retried successfully with python3; environment tooling only.

Changed: only this new evidence directory and concrete plan. Incoming file hash comparison confirms 24769 existing files unchanged (verification.json). No application edits/tests/assertion changes, no commit/push/deploy/production.

Business/DB/security: no application semantics changed; own fictional prerequisites only. Long untranslated AZ/EN captions are outside05, reserved for06 recheck. No independent specialist execution claimed.

Next: approve docs/superpowers/plans/2026-10-14-offer-qa05-admin-status-wrap.md; only one application CSS file. Repair, native save/reload/readback,54-cell acceptance, backend/full ACCEPT-05/global/production NOT RUN. OFFER05 remains OPEN until fresh scoped acceptance.
