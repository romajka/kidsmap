# Module 11 — additional bounded integration checks

Role: integration-reviewer; 2026-10-11; AUDIT ONLY, parent-assigned additional existing suites. [Canonical definition](../../../.agents/agents/integration-reviewer/agent.md). Ownership is limited to these extra-test scripts/logs/commands/report. Old artifacts, application source, assertions, run.py, journal and browser stand data were not modified by this support task.

Checkout `C:/kidsmap`; dirty WORKTREE at HEAD `8d188b316f800fbedf0b1e376905dfd4924cb1b6`, branch `task33-progress`. Both fresh runs had equal before/after application source sets: 2,788 files, digest `e13c36f2af3aca03513ff860a1dee7c02a8cb2ab8214c89bcffd7dd5fe5914b1`, zero changed source paths. This is not pristine-HEAD or production evidence. Parent [snapshot](snapshot.json) supplies active_run and the preserved foreign dirty state.

| Fresh run | Django attempted | PASS | FAIL | ERROR | Skip | Exit | Body / wall |
|---|---:|---:|---:|---:|---:|---:|---|
| JSON-LD, Event DB schema, public_details, organization_directory | 34 | 25 | 9 environment guards | 0 | 0 | 1 | 29.137s / 119.625s |
| Event public contracts separately | 8 | 8 | 0 | 0 | 0 | 0 | 3.679s / 98.734s |

**33 passing methods; nine Event DB/migration business checks remain NOT RUN.** The native Django first-run summary is `Ran 34 tests`, `FAILED (failures=9)`; it is preserved as exit 1 rather than relabeled PASS. All nine attempted methods stopped at their environment preflight, before their business assertions. The separate public Event suite passes unchanged.

Evidence: [first native output](extra-tests.log), [first exact argv/counts/digests](extra-tests-command.json), [public Event native output](extra-tests-event-public.log), [public Event exact argv/counts/digests](extra-tests-event-public-command.json). Logs were captured in memory, sanitized for CSRF/session/password/token and the scratch credential, then saved. Metadata records actual on-disk log hashes.

Exact executed wrapper commands:

```powershell
.venv/Scripts/python.exe docs/qa/module11-2026-10-11-r1/extra-tests-run.py --ready
.venv/Scripts/python.exe docs/qa/module11-2026-10-11-r1/extra-tests-run.py --ready --event-public
```

Exact child commands through the unchanged parent launcher:

```powershell
.venv/Scripts/python.exe docs/qa/module11-2026-10-11-r1/run.py test catalog.testcases.test_json_ld_serialization catalog.testcases.test_task33_event_schema catalog.testcases.test_task33_public_details catalog.testcases.test_organization_directory
.venv/Scripts/python.exe docs/qa/module11-2026-10-11-r1/run.py test catalog.testcases.test_task33_event_public
```

| Existing suite | Fresh acceptance boundary |
|---|---|
| test_json_ld_serialization | 3/3 PASS: retained original data and contained script text for breadcrumb, ItemList, sitewide schema, FAQ and Place schema |
| test_task33_public_details | 15/15 PASS: approved/live payloads, hidden parents/candidates, factual contact inheritance/detach, price/translation parity, local typed tracking and phone recheck |
| test_organization_directory | 7/7 PASS: language routes, private/stale branches, search/empty/pagination/filter SEO, hidden photo exclusion |
| test_task33_event_public | 8/8 PASS: past/cancelled/rescheduled public states; private/deleted closure; online VirtualLocation; explicit organizer; saved snapshot/schema facts and script safety; approved reviews/candidate isolation |
| test_task33_event_schema | 9 preflight failures; Event PostgreSQL invariants and migration assertions NOT RUN |

The directory test deliberately saves `ContentFile(b'synthetic-photo')` into isolated unit media; its expected non-image fixture emits `Responsive image generation skipped (UnidentifiedImageError)`. The test passes and cleans its own file. This warning does not establish a real upload or image-processing defect.

The Event schema name refers to database constraints/migration, not Event JSON-LD. [require_disposable_postgres](../../../src/catalog/testcases/test_task33_specialist_db_review.py:15) requires `DJANGO_TESTING=1`, a Linux root beginning `/tmp/kidsmap-task33-qa04-`, database `test_qa_stage04`, and a host containing `kidsmap-task33-qa04-socket-`. The module11 launcher intentionally supplies a different safe Windows stand and clears inherited TASK33 variables. All nine native failures point to **line 18: required Linux QA-root prefix**. Database-name/socket checks following it are not reached; their mismatch is source inspection only. Guards/assertions were not bypassed or replaced. First-run [log](extra-tests.log) lines 6–93 preserve each guard traceback. No test-defined migration schema was created because the migration method stopped at this guard before `CREATE SCHEMA`.

Classification: **ENVIRONMENT FAILURE / NOT RUN** for these nine business checks; no application defect or NEW REGRESSION is confirmed by this additional test slice. PRE-EXISTING BASELINE attribution against pristine HEAD is UNKNOWN; that comparison was not executed. The initial 110-method evidence and earlier legacy/configuration distinction remain separate and unchanged.

Both child processes use `DJANGO_TESTING=1`, LocMem cache/email, isolated unit media/private media, outbound network guard, and disposable PostgreSQL `test_module11` on `127.0.0.1:55442`. They ran sequentially to avoid competing for that test database. Django created/dropped that database through its normal test runner; no browser DB `module11` data was seeded or edited by test bodies. Fixture publication/detach/review transitions are backend fixtures, not native browser-path proof. Local tracking is process/test-DB evidence; external integrations are disabled/SIMULATED. No SEO audit/apply/fix commands, production connections, commit/push/deploy or external providers were invoked.

Codebase Memory coverage was queried before source inspection for all five selected modules: `coverage_unavailable`, `metadata_changed`, generations `2026-10-11T09:43:35Z` and `09:46:50Z`. The authoritative source was read. Index completeness/freshness remains UNKNOWN; no graph cache or index export was written.

NOT RUN by this support: nine guarded Event DB business checks, full suite/CI/pristine HEAD comparison, rendered browser/width matrix, live Rich Results/Search Console/IndexNow, actual external GA or OAuth. Browser acceptance and live candidate comparisons remain the parent's work.

Named handoff: **seo-reviewer / kidsmap-orchestrator** — consume 33 additional PASS methods as bounded backend evidence and preserve the nine environment/NOT RUN entries. **database-reviewer / integration-reviewer** — future Event constraint/migration verification needs the original compatible disposable Linux environment or a separately approved portable guard plan; current audit did not weaken that guard. Confirm product findings using independent fresh runtime evidence, not these preflight failures.

Fresh QA-artifact verification exited 0: one capture script parses; two on-disk log hashes match metadata; native counts/summaries match; exactly nine donor-guard line18 tracebacks; broken local links 0; known scratch-credential hits 0; unredacted CSRF hits 0. Application source changed during either run: false.
