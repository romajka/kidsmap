# Module 12 — integration-reviewer handoff

AUDIT ONLY; 2026-10-11; delegated execution `/root/analytics_tests`.
Definition: `.agents/agents/integration-reviewer/agent.md`.
Ownership: this `test-review/` directory only. Application, original assertions,
rules, migrations, credentials, foreign stands and reports were not modified.

Snapshot: `C:/kidsmap`, branch `task33-progress`, HEAD
`8d188b316f800fbedf0b1e376905dfd4924cb1b6`, dirty WORKTREE, `active_run: NONE`.
Parent snapshot and runtime identity remain the source of the full stand evidence.
[31 relevant source/test files](source-snapshot.json) are unchanged against HEAD.
This confirms the examined implementation already exists in HEAD; a completely
clean checkout process was not executed, so no new-regression claim is made.

Isolation: parent-owned fresh PostgreSQL `module12` at `127.0.0.1:55443`,
disposable `test_module12`, `DJANGO_TESTING=1`, separate LocMem cache and unit media,
private media and email. The launcher clears inherited service credentials and
blocks all external sockets. Unit defaults disable collection/owner analytics;
existing decorators and own assertions enable the required branches explicitly.
GA contexts and injected persistence faults are **SIMULATED**. Real GA is **NOT RUN**.

## Executed checks and commands

| Check | Result | Exit | Evidence |
| --- | --- | --- | --- |
| Existing scoped Django suites and four admin analytics methods | 60/60 PASS | 0 | [argv/count/duration](primary.json), [log](primary.log) |
| Own final acceptance assertions | 4 PASS / 5 FAIL / 0 ERROR, 9 tests | 1 | [argv/count/duration](supplement.json), [log](supplement.log) |
| AI referral JavaScript | One assertion script PASS; no numbered runner count | 0 | [command](ai-js.json), [log](ai-js.log) |
| Phone reveal DOM | 4/4 PASS | 0 | [command/count](phone-dom.json), [TAP](phone-dom.log) |

Exact reproducible PowerShell commands from the repository root:

```powershell
.venv/Scripts/python.exe docs/qa/module12-2026-10-11-r1/test-review/run-tests.py primary
.venv/Scripts/python.exe docs/qa/module12-2026-10-11-r1/test-review/run-tests.py supplement
.venv/Scripts/python.exe docs/qa/module12-2026-10-11-r1/test-review/run-tests.py ai-js
.venv/Scripts/python.exe docs/qa/module12-2026-10-11-r1/test-review/run-tests.py phone-dom
.venv/Scripts/python.exe docs/qa/module12-2026-10-11-r1/test-review/build-evidence.py
```

`primary.json` contains all 13 exact Django labels. The requested historical name
`catalog.testcases.test_public_favorites` is absent; actual existing module
`catalog.testcases.test_public_favorite_count` was executed instead.

Latest canonical Django results cover 69 distinct methods: 64 PASS / 5 FAIL.
Additional earlier execution attempts are preserved; they must not be folded
into unique-method totals or treated as extra product findings.
[Own artifact verification](verification.json): syntax, result counts, report
links and absence of the local QA credential literal all pass, exit0.

## Confirmed failed assertions for root reconciliation

1. **Global analytics ACL:** active staff without `view_siteanalytics` or
   `change_siteanalytics` obtains HTTP200 and the aggregate dashboard, expected
   403/404. [Observation](staff-permission-observation.json).
   `src/catalog/domain_admin/site.py:470` overrides `changelist_view` without a
   model permission check. Business/security impact: global aggregate access
   beyond assigned model permission. Root native corroboration is separate.

2. **90-day GA KPI period:** selected90 yields simulated yearly367 page views,
   expected quarterly92. [Observation](ga90-observation.json).
   `admin_analytics._ga_period_key(90)` selects `year`;
   `google_analytics_reporting.GoogleAnalyticsAdminReportingService.PERIODS`
   uses `364daysAgo`. This is a local mapping failure verified with a **SIMULATED**
   adapter; external GA values, credentials, timezone and ingestion are NOT RUN.

3. **Analytics persistence fault breaks public Place:** a confirmed injected
   `DatabaseError` in the actual repository class makes a public Place return500,
   expected200 with analytics unavailable.
   [Observation](analytics-fault-observation.json), [isolated rerun](fault-confirmed.log).
   `PlaceController.build_detail_context` calls tracking synchronously before
   constructing content; the failure propagates. **SIMULATED local persistence
   fault**, healthy primary DB. Native error rendering is root-owned.

4. **Private active draft ID accepts events:** anonymous `phone_click` to a
   fictional active draft returns200 and event delta+1, expected refusal/delta0.
   [Observation](private-id-observation.json), [targeted run](private-origin.log).
   `DjangoEventPlaceRepository.find_active_for_event` checks active/not deleted,
   but not moderation/public visibility. This endpoint returns only event status;
   this evidence does not establish private contact disclosure.

5. **Legitimate same-origin port rejected:** matching
   `HTTP_HOST=testserver:8829` and `Origin=http://testserver:8829` returns403,
   expected200. [Observation](port-origin-observation.json).
   `views._allowed_tracking_hosts` drops the port while origin validation compares
   complete netloc. This explains local native contact event rejection.

All five failures are bounded current LOCAL evidence. Relevant examined source
is unchanged against HEAD; they are pre-existing implementation issues rather
than demonstrated regressions in the foreign dirty edits.

## Passed acceptance boundaries and limitations

The four own PASS cases verify half-open interval inclusion at the Asia/Baku
day/month boundary; ingress date rollover at UTC20:00; owner events included
while bot/staff excluded; and contact-only identity counted in the unique visitor
metric even with zero views. Date fixtures are fictional and deterministic.

Existing60 checks cover canonical/hash/scoping metadata, event types, basic bad
payload/origin/rate limits, favorites and reconciling cached counts, staff and
actor exclusion, comparison periods, owner/team/deleted ACL, disabled feature
gates, retention purge idempotence in the disposable test DB, safe aggregate
output, AI referrals, JS markup, test cache/language reset and admin GA layouts.

Phone DOM is **SIMULATED**, including mocked fetch and jsdom's unimplemented
document navigation warning; it does not establish rendered browser behavior.
Native matrix, save/reload, rename redirects, browser back/forward/two tabs,
period selects, archive/history, keyboard, screenshots and console/network are
root-owned and are **NOT RUN by this specialist**. Full Django suite, concurrent
database stress, production, real external GA/device attribution, scheduled
retention in deployment and cross-browser engines are NOT RUN here.

Codebase Memory was callable: project `C-kidsmap`, ready generation
`2026-10-11T10:18:23Z`; searched graph before bounded source reads. Exact cited
coverage reports were `coverage_unavailable/metadata_changed`; graph hints were
verified against source. Static test coverage was unavailable. No graph cache
was exported and no absence/exhaustive claim was based on the graph.

## Harness attempts excluded from product findings

The first phone evidence wrapper hit a Windows stdout Unicode encoding error
after Node itself exited0. Own wrapper was corrected to UTF8 and explicit TAP;
both [original metadata](phone-dom-attempt1.json) and [log](phone-dom-attempt1.log)
are preserved. Final phone wrapper/test exits0.

Initial own persistence-fault test patched a singleton not used by the public
controller. Its unverified PASS is excluded:
[original observation](analytics-fault-unverified-attempt1.json),
[initial seven-test log](supplement-attempt1.log). The corrected test patches the
repository class and asserts the injection actually ran; final result is500/FAIL.

A later isolated rerun initially failed before tests because root QA helper
`inspect.py` shadowed stdlib `inspect`. [Attempt metadata](fault-confirmed-environment-attempt1.json)
and [log](fault-confirmed-environment-attempt1.log) are preserved. Root renamed its
own helper; the specialist wrapper preloads stdlib `inspect`. This is an
environment/harness failure, not an application defect. Corrected runs execute.

## Named handoff

**Next: kidsmap-orchestrator / browser-qa.** Reconcile these five bounded failures
with root native evidence; assign final `ANALYTICS-QA-xx` IDs and individual
repair prompts. A repair requires separate scoped authorization; this run
performs no application fixes. Source/funnel and permission decisions go to
`analytics-reviewer`, `django-reviewer` and `security-reviewer` as appropriate.
