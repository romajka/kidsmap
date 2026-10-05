# Stage 23 — LOCAL release closure review

Role: sequential named `release-reviewer`, AUDIT, 2026-10-03. Canonical role and engineering/audit contracts applied. Output ownership is this report only; application, tests and production were not changed during this review. LOCAL checkout `C:\kidsmap`, `task33-progress`, HEAD `015d031d8eb17114bd860159dde805b38df3c13c` plus dirty WORKTREE. Production revision, runtime, data and schema remain UNKNOWN. Codebase Memory became unavailable after the prior transport failure; graph freshness/coverage for final paths is UNKNOWN. Conclusions below use actual source and evidence.

## Reviewed result

No remaining confirmed P0/P1 in the bounded **LOCAL** artifact/cohort/recovery scope. This closes historical REL23-01–03 for local acceptance, not production deployment. Root integration acceptance still depends on its final full-suite classification and fresh browser matrix. The reviewer previously authored publication/location fixes under a separate approved assignment; those are **not independently reviewed here**. Their independent boundary review belongs to database-reviewer and is recorded in `23-recovery-closure.md`.

| Historical finding | Closure evidence and boundary |
|---|---|
| REL23-01 — no immutable exact runtime | Exact content-addressed runtime archive, manifest, executable hash and 39 installed dependency versions identify the dirty local candidate. Independently verified all 2703 archive and standby files. HEAD alone is not R1. This is an executable LOCAL artifact, not a production Docker image or bundled offline dependencies. |
| REL23-02 — no demonstrated write/cohort pause | Actual `r1_cohort.py`, `r1_middleware.py`, settings and seven regression methods implement server-selected explicit positive actor IDs, malformed configuration fail-closed, no staff/header bypass, both admin namespaces and CSRF retained. Native final rehearsal observed public GET 200/unsafe POST 503 with rows unchanged. This gate covers HTTP content writers; offline commands/queues must separately be quiesced for a future activation. |
| REL23-03 — no compatible recovery reader | Native post-write dump/restore compares all 94 public tables and 25 media files; frozen standby reader verifies exact artifact/interpreter/dependencies, imports that application, guards its named Unix-socket restore DB and reads in an explicit read-only transaction. New Place, approved Program snapshot, direct/group prices, review/reaction, media and AZ/RU URLs survive. This keeps compatible schema 0130 and post-switch data; it does not endorse old binary rollback or an old dump over new writes. |

REL23-04 remains a **future production activation gate**: current conversion intentionally accepts only isolated QA. Real cohort selection, production data decisions, pinned production image, production baseline thresholds and offline writer ownership need separately authorized work. They are explicitly stated in `release-R1.md`; no production evidence was inferred from local synthetic data.

## Exact candidate and independent checks executed

Identity: `r1-local-sha256-df5c662e67f05511b710eae38cd678e170dfa514f483852f15ccf101c5369af3`.

Archive SHA256: `6f5a10004d38403515fa0ad9a7fa5e3b03fc58dff15e206e7c0330b839118682`.
Manifest SHA256: `2382a223b09b791367695699ad6d88f2a98e5bd5a1d953b7cb1d17bba2b92533`.
Standby: `/root/km23-standby-final5-20261003`. Metadata: `23-artifact.json`; full file/dependency manifest is outside Git beside the archive.

Read-only independent verification command:

```powershell
wsl -d Ubuntu-24.04 -u root -- /root/kidsmap-task33/.venv/bin/python /mnt/c/Users/Ramin/AppData/Local/Temp/km23_release_verify.py
```

Exit 0/PASS. The private script recomputed canonical manifest identity, manifest/archive SHA256, verified every 2703 standby file and every regular allowlisted tar entry, compared Python 3.12.3 executable SHA256 and all 39 installed distributions to manifest. It set `sys.dont_write_bytecode=True`; no Django settings, database or external integration was loaded. Runtime archive excludes env, database, media, Git and venv; interpreted application and dependencies are supplied by the verified existing LOCAL interpreter/venv.

Frozen source artifact safety tests:

```powershell
wsl -d Ubuntu-24.04 -u root -- bash -lc 'cd /root/km23-standby-final5-20261003/docs/task33/qa23 && PYTHONDONTWRITEBYTECODE=1 /root/kidsmap-task33/.venv/bin/python -m unittest test_artifact -v'
```

Exit 0, **2/2 PASS**: deterministic identity, tampered standby rejection, existing standby rejection and forbidden env/private/traversal paths. Tests use their own temporary fixtures; no shared mirror or QA container was mutated.

Actual source reviewed: QA23 `artifact.py`, `test_artifact.py`, `container_guard.py`, `rehearsal.py`, bridge commands, compatible reader; catalog cohort resolver/middleware/tests; settings middleware placement and parsing; final candidate packet and DB recovery report. The middleware follows CSRF and authentication. The reader enforces named disposable restore DB, isolated media, AF_UNIX/libpq guards, empty external endpoints, writes-off, frozen catalog import path, `BEGIN READ ONLY` and statement timeout.

## Recovery evidence reviewed, execution attributed

Historical v2 independent archive/file/interpreter/dependency verification and its frozen 2/2 artifact tests passed before this final review. V3 repeated those checks and changed only the QA browser matrix. V4 repeated the independent checks above and its frozen 2/2 artifact tests, then received a fresh native restore drill. An independent full-manifest comparison from v2 to final v5 found exactly two changed files: `docs/task33/qa23/browser-matrix.js` and `static/css/pages/organization_workspace.css`. Backend, application tests, migrations and templates are byte-identical. Earlier backend suite evidence therefore applies to the final backend bytes; fresh browser evidence is still required for the new CSS/matrix.

Bounded CSS source review: the newly added `width:100%` on `.org-workspace .account-main-content` constrains mobile cross-axis width when the parent switches to column flex layout with `align-items:flex-start`. Existing `min-width:0` preceded the correction and by itself did not prove closure. Desktop `flex:1 1 0` and tab horizontal scrolling remain. This is source review, not a rendered-browser PASS claim; the lead retains final browser acceptance ownership.

Final v5 repeated all independent archive, file, interpreter and dependency assertions above and frozen artifact tests **2/2 PASS**. Independent v4→v5 full-manifest comparison found only `static/css/pages/organization_workspace.css` changed; the strict browser matrix and all backend/test/template/migration bytes are identical. The final responsive `.org-tabs { flex-wrap:wrap; }` at widths ≤768 keeps tab labels in normal wrapped flow, preserves visible focus and leaves desktop behaviour unchanged. Earlier width correction alone had not demonstrated stable focused last-tab text at RU320; the final rendered focused-tab/geometry acceptance remains attributed to the browser reviewer. Native final5 results below supersede earlier v2/v3/v4 drills for final identity alignment.

Database-reviewer/lead executed the native final5 launcher; this reviewer independently read its aggregate evidence and traced its source, and did **not** claim an additional database rehearsal execution.

Evidence: `/root/task33-evidence/qa23-final5-20261003-1530/{r1-rehearsal,run,isolation}.json`; synthetic-only raw dump/media/logs stay outside Git.

Observed PASS: 531672-byte post-write custom-format dump; 94 table counts/row digests equal source/restore; 25 media byte hashes equal; 21 mapping pieces with forced mid-batch rollback/checkpoint 1/resume/rerun; source digests retained; frozen compatible reader 2703 files and exact identity verified. Launcher Exit 0/child 0/cleanup PASS; owned container and run/socket roots removed. Docker network none/no ports/tmpfs PGDATA/private socket; testing on, single disposable DB, local cache/email/media, no external credentials. PostgreSQL 17.11, Django 6.0.2, Python 3.12.3, psycopg 3.2.10.

The native drill is a valid LOCAL restore rehearsal, not evidence of production backup retention, off-host storage or disaster recovery on another host. Dependency inventory does not provide offline wheels/shared-library portability. Those limits appear in the packet.

## Not run and handoff

Not run by this reviewer: shared QA launcher, full Django suite, browser matrix, production reads or writes, external integrations, deployment/release/backup scripts, container/image deployment, commit/push/merge, stage 24. Full/targeted and browser conclusions belong to the lead's final evidence. No dead/legacy deletion proposed.

Lead handoff reports final full-suite execution of 1619 tests with 98 failures, 8 errors, 0 skips and cleanup PASS; this is **not a green full suite**. The lead reports all initial 129 problem IDs classified (95 remaining unique IDs, 34 resolved, zero unknown), with targeted 382/382 PASS. Those classification/acceptance conclusions are attributed to the lead, not independently re-executed by this release reviewer. Fresh final browser 294 scenarios plus 175 geometry checks remained pending at this report handoff.

Named handoff: lead `integration-reviewer` / KidsMap orchestrator incorporates LOCAL REL23-01–03 closure plus the explicit future gates into `23.md`, `release-R1.md` and stage 24 readiness. Keep final acceptance pending until the lead validates full-suite classifications and browser results on the identified application bytes. This report grants no production activation authorization.
