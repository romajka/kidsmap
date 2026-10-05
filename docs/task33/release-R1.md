# KidsMap №33 — R1 LOCAL acceptance packet

Status: LOCAL ACCEPTED / stage23 DONE; ready to start24 under a separate instruction. Production activation NOT_REQUESTED / NOT_RUN. This packet identifies a local executable candidate and a tested compatible reading/recovery strategy; it is not a production image or deployment approval.

## Exact local revision

- Checkout `C:\kidsmap`, branch `task33-progress`, LOCAL HEAD `015d031d8eb17114bd860159dde805b38df3c13c`; stages21–23 are dirty WORKTREE. HEAD alone is not R1.
- Exact immutable LOCAL candidate: `r1-local-sha256-df5c662e67f05511b710eae38cd678e170dfa514f483852f15ccf101c5369af3`.
- Archive: `/root/task33-artifacts/r1-local-sha256-df5c662e67f05511b710eae38cd678e170dfa514f483852f15ccf101c5369af3/runtime.tar.gz`; SHA256 `6f5a10004d38403515fa0ad9a7fa5e3b03fc58dff15e206e7c0330b839118682`; manifest SHA256 `2382a223b09b791367695699ad6d88f2a98e5bd5a1d953b7cb1d17bba2b92533`.
- Extracted compatible standby `/root/km23-standby-final5-20261003`:2703 allowlisted runtime/source files including migrations/templates/assets/compiled locales and QA23. No env/media/DB/Git/venv in archive. Python3.12.3 executable SHA256 `e50d468e8b0adfb05733f5b87b3cff34829c4a8c1aea50c865aa8bdfe4bb150f`,39 dependency versions in external full manifest. Existing local venv supplies that verified interpreter/inventory; dependencies are inventoried, not bundled offline wheels.
- Metadata `reports/23-artifact.json`, dirty Windows source hashes `reports/23-source-manifest.json`. V1→V5 changed only QA browser bridge/matrix helpers and organization CSS. Backend/test/migration/template bytes match the final382-test targeted and full-suite executions; the changed CSS passed fresh v5 rendered geometry/keyboard checks. The Linux runtime contains freshly compiled locales; three preserved Windows .mo bytes differ.
- No commit was made merely to identify dirty code: prompt23 permits exact source hashes. A separately built/pinned production image and authorized source commit remain future release gates.

## Schema, conversion and write cohort

- Isolated PostgreSQL17.11, Docker `postgres:17-alpine`, image ID `sha256:b0f9560a2de083e2cc7382e75f808c7381a32852a7ec49117deedb300e552b24`, network none/no ports/tmpfs/private Unix socket.164 migrations applied/0 pending, catalog leaf `0130_task33_review_versions`; check and migration consistency PASS. Production schema UNKNOWN.
- Conversion v1 preserves Place/PricingPlan IDs and legacy values, creates an idempotent checkpoint ledger, leaves ambiguous organization/group/price decisions in `manual_review`. It is QA-only and deliberately refuses non-isolated DB targets. Native rehearsal covers dry-run, forced mid-batch rollback, partial checkpoint1, resume/rerun21 pieces, source digest preservation and post-switch drift detection.
- `TASK33_R1_WRITE_MODE=all` retains current behaviour. `selected` accepts only explicit positive integer `TASK33_R1_WRITE_USER_IDS` from server settings; malformed mode/cohort fails closed. Membership adds no business permission. `off` blocks unsafe catalog HTTP and both admin namespaces with503, `Retry-After:60`, no-store; public/approved readers and account authentication remain available. Staff and client headers cannot bypass. RU/EN localized admin negative red→green plus CSRF tests passed.
- This is an HTTP write gate. Before a future pause, separately quiesce offline writers, commands, queues and scheduled jobs; they do not become blocked by middleware. No production flags/credentials/integrations changed. Synthetic actors are not a production pilot; KidsMap chooses real participants separately.

## Tested local compatible recovery

Keep schema0130 and the same compatible frozen binary; pause HTTP writes and offline writers. A pre-switch dump or old incompatible binary is not the strategy. The QA23 rehearsal dumps after new writes, restores into a separate owned disposable DB, copies synthetic media, compares source/restored table counts and row digests and verifies media byte hashes. It never replaces the source DB or discards post-switch rows.

V1 preliminary/frozen native recovery passed94 public tables and25 media files with531637-byte custom-format dump. Final V5 recovery PASS on the exact identity above: `/root/task33-evidence/qa23-final5-20261003-1530`,531672-byte native post-write dump,94 table count/row digests,25 media byte hashes,2703 frozen reader files; child0/cleanupPASS. Full evidence is recorded in `reports/23-recovery-closure.md`. The separate standby reader verifies archive/manifest/all2703 files and interpreter/dependencies, imports that frozen application, guards its named Unix-socket restore DB, uses `BEGIN READ ONLY`, and confirms post-switch place/program approved snapshot/direct+group prices/review/reaction/media/AZ-RU URLs with HTTP GET200/POST503.

## Monitoring and stop criteria for a later activation

The future operator records approved cohort, immutable image/source/schema, endpoint error rates/p95 latency/query counts, conversion counts/checkpoints/manual-review queue, publication/review pending state, owner/manager denials, redirects, tariff display, notification/outbox health and user reports. Local cold-cache query measurements and scaling tests are in reports23; they are synthetic baseline measurements, not production thresholds. Fix numeric latency/error thresholds and on-call ownership against an actual separately authorized production baseline before release.

Stop cohort expansion on any missing ID/media/revision, cross-owner access, false identity match, wrong review target, contradictory price, lost old URL, unexpected500, migration inconsistency or reconciliation mismatch. Disable the tested HTTP gate, quiesce offline writers and preserve evidence/new data. Resume only after reconciliation and named review. Never restore a pre-switch dump over new writes or reverse irreversible schema to obtain a green startup.

## Acceptance evidence and handoff

Final targeted382/382 PASS; full1619/98F8E/0skips (95 unique classified IDs,unknown0); browser QA23 294/294+175/175,QA21 105/105,QA22 462/462 and48/48 lifecycle. Lifecycle retains9 native ViewTransition cancellation pageerrors without functional failure and is not console-clean. `reports/23.md` and `reports/23-results.json` record exact evidence and independent reviews. Classified historical/superseded-contract full-suite failures remain visible and unskipped; targeted PASS does not mean whole application suite green. Independent DB/security/publication/cohort review and independent release artifact/recovery review have separate authors and reports. No production command, deploy/backup script, external integration, commit/push/merge or stage24 implementation was run.

Next available stage after LOCAL acceptance: `prompts/24.md`, only under a separate user instruction.
