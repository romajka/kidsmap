# Module 12 — fresh source contract

Role: `analytics-reviewer`, execution identity `/root/analytics_source`; definition `.agents/agents/analytics-reviewer/agent.md`. Mode: **AUDIT ONLY**. Assigned ownership: this `source-review/` directory only. Parent owns snapshot, isolated runtime, tests, native browser, final findings and journal. LOCAL HEAD reported by parent: `8d188b316f800fbedf0b1e376905dfd4924cb1b6`, branch `task33-progress`, dirty WORKTREE. Production: UNKNOWN, not contacted.

## Source and discovery boundary

Read current AGENTS, actual role definition, engineering/audit contracts, architecture, current-snapshot, source-of-truth analytics rows, analytics knowledge, applicable security/testing references. Dated knowledge is navigation only. Read actual current source below, `docs/product/analytics-event-taxonomy.md`, `docs/product/analytics-operations.md` and `docs/ai_referral_analytics.md`.

Codebase Memory: project `C-kidsmap`, root `C:/kidsmap`, status ready, 186099 nodes / 304462 edges. Scoped coverage returned **metadata_changed**, coverage_unavailable for tracking/visit/admin services and AI JS; base template partial. Graph hints were verified in source. Graph results include ambiguous `resolve` edges into historical backup assets; those are not verified dependencies. No reindex or graph cache export. Relevant analytics source/template paths in the scoped `git diff --name-only` command had no dirty diff. This does not describe other files or deployment.

Actual admin template: `templates/admin/catalog/site_analytics.html`. Historical `src/catalog/templates/admin/catalog/site_analytics.html` does not exist. Existing public Favorites suite is `test_public_favorite_count.py`, not `test_public_favorites.py`.

## Metric definitions and durable keys

| Concept | Current implementation |
|---|---|
| Place view | One `FunnelEvent(event_type=place_view, schema_version=2, subject_type=place, subject_id=Place.pk)` from each canonical detail-context build. Successful detail GET reaches it after visibility and slug/query redirects. It is written before template rendering, so a later render failure can still leave an event. No event-level reload/request ID dedupe. |
| Organization / Activity views | Their public detail GET writes `organization_view` / `activity_view` using stable PK, with a set on **this request only** preventing the same subject twice. No cross-request dedupe. Neither has an aggregate resolver in `build_subject_metrics`; unsupported subjects return unavailable. |
| Unique visitor | For authenticated request HMAC of `user:{pk}`; anonymous HMAC of `anonymous:{session_key}`. Version prefix `v1:`. Distinct qualifying v2 hashes, plus separate legacy session-key distinct count. Across logged-in sessions identity remains user-based. Across anonymous sessions it changes. Count considers all qualifying events, including clicks with no view. |
| Unique session | HMAC of `session:{session_key}`; distinct qualifying v2 hashes plus separate legacy distinct raw session keys. Browser tabs sharing one session count once, while views/actions remain multiple. |
| Aggregate key | v2 `(subject_type=place, subject_id IN selected IDs)`; v1 `place_id IN selected IDs`. URL, localized slug, path, language, query and device dimensions do not partition Place totals. Object rename keeps PK totals. No backfill/legacy-to-v2 identity reconciliation; v1/v2 distinct identities are added separately. |
| Count exclusions | Read-time metrics exclude `device_class=bot`, `user.is_staff=True`, and users with **currently active** `AnalyticsActorExclusion`. Owner is not automatically excluded. Current code does not exclude inactive user events even though taxonomy says it does. Favorites separately require active registered users and exclusions. |
| Contacts / directions | Phone, WhatsApp, website and social canonical clicks plus v1 CTA aliases sum into `contact_actions`; directions counted separately. These are link actions, not evidence of a call, sale, booking or external navigation completion. |
| Favorites | Current eligible `PlaceLike` users, distinct across selected Places, independent of the event period. Additions/removals count eligible events in period. |
| Window | v2 `occurred_at >= start AND < end`; v1 `created_at >= start AND < end`. Previous window is immediately preceding equal duration. Percentage unavailable (`None`) when previous total zero. Owner uses rolling `now-30 days .. now`, not calendar-month buckets. |
| SiteVisit legacy storage | Service definition uses unique `(timezone.localdate(), raw session key)`, increments hits on GET/HEAD, strips lang only for exclusion checking, stores original first path. **No caller is wired in current src/static/scripts search or graph.** Native requests should not create SiteVisit rows. Do not derive current unique visitor totals from this legacy service. |

Sources: `analytics_identity.py:14/22/32`; `analytics_metrics.py:31/43/72`; `favorite_metrics.py:12/19`; `tracking.py:225/340/503`; `place_controller.py:735`; `views.py:393`; `models/site.py:580/607`; `visit_tracking.py:33`; `tracking_repositories.py:41`; `public_details.py:159/187`.

## Client → endpoint → storage → reporting

- Public bridge in `src/catalog/templates/base.html:706` exports `kidsMapTrackEvent`, emits GA separately, then sends POST through beacon or fetch to `/{lang}/events/track/`. Click delegation selects `[data-track-event]` plus `[data-track-place-id]` and `[data-track-source]`, sends current pathname. Canonical server view is not POSTed again; `analytics_events` only emits GA. Beacon returning false is not checked; HTTP response/errors are silent.
- Endpoint `views.py:640`: POST only, deliberately CSRF exempt, host/origin validation and rate limiting by session + remote address, then JSON controller. Accepted/rejected/rate-limited aggregate ingress counts on local day when storage enabled. Error codes: invalid payload400, unsupported event400, origin403, rate429. No arbitrary client ID/hash/timestamp/meta acceptance. Invalid request can still consume rate budget.
- `TrackingController:30` accepts click events and AI referral. Client `place_view` POST is unsupported; view truth is server render. Legacy `cta_call/whatsapp/instagram` write canonical names. Repository eligibility currently checks active and not soft-deleted only; it does **not** enforce published/public visibility.
- Canonical writer stores user FK, blank raw session key, HMAC identities, bounded source/page/language/device/referrer-domain/campaign and metadata allowlist. Device is UA-based; default Playwright headless UA classifies bot and is excluded from aggregate. Native count fixtures need normal Chrome UA.
- Local storage disabled returns successful no-op for valid events; it does not prove GA received anything. AI event is anonymous v1 with safe source/path/type/language, no user/session, client sessionStorage dedupe per source+landing path in one tab; backend repeated requests are not deduped.
- Browser GA disabled for DEBUG, local/test hosts or absent measurement ID (`context_processors.py:233`). **Admin GA reporting has a separate enable rule**: measurement OR property ID. Config contains nonempty default property ID; test stand must override BOTH empty and clear Google credential env. Real Google requests must remain disabled. Stubbed GA reporting is SIMULATED.
- Reporting service makes 4 period + daily chart + top pages + top events synchronous reports, without explicit timeout/cache. Source latency risk only; no measured latency assertion. Snapshot distinguishes enabled/connected/error. A partially failed report can leave already-populated period stats and empty later results.

## UI, permissions, periods and lifecycle

| Surface | Contract / useful selector |
|---|---|
| Owner | `/{lang}/account/places/{pk}/analytics/`; guest login redirect; feature flag off404; unrelated or deleted Place404; own draft still allowed with `place.stats.view` permission. Actual permissions delegated to `business_team.has_action`; managers/moderators get stats, editors do not unless explicit grant. Five metric cards `.owner-analytics__grid article strong`, no chart/date filter or metrics JSON API. Fixed labelled last30days; collection timestamp and generated last-updated timestamp. |
| Admin | `/admin/catalog/siteanalytics/?period=7|30|90|365`; `.km-period-selector [data-period]`; invalid period30 fallback. Three GA KPI `[data-kpi-value]`, fixed30day canvas `#km-visits-chart` and JSON `#km-visits-chart-data`, fixed30day GA top tables. Local Place summary is computed in context but absent from rendered template. |
| Error/empty | Owner unavailable notice exists but configuration check forbids enabled owner UI with local collection disabled; test only via isolated adapter labelled SIMULATED. GA empty sections show generic no-data text, KPI0 and 'updated today'; template never displays `ga4.error` or disconnected status. Real external validity NOT RUN. |
| Period90 | `_ga_period_key(90) == year`, report range364daysAgo..today, while header period90 and local window90. Source mismatch; runtime test/stub must confirm separately from intentionally fixed30 charts. |
| Hide/archive | `PlaceAdmin.mark_inactive:4956` / `mark_draft:5008` change active/status, not FunnelEvent. `FunnelEvent.place` is SET_NULL on actual delete; v2 `subject_id` survives. Owner stats controller permits draft/inactive but excludes deleted; admin local aggregate filters nondeleted Places, so soft-delete removes it from this total while historical events remain. Do not confuse history retained with available UI access. Org/Activity archive visibility gate rejects new views; no archive code evidence of raw event deletion. |

Day fields use Django current timezone/localdate. Root must confirm actual stand TIME_ZONE/active timezone is Asia/Baku. Rolling windows do not promise calendar month buckets; GA property timezone is externally configured and **UNKNOWN** without real provider access. Native Back/Forward may use browser bfcache without a network render: actual network + DB delta determines expected view increment, not button press alone.

## Hypotheses for fresh runtime checks — NOT confirmed findings here

1. 90day admin KPI uses year; explicit SIMULATED report ranges can demonstrate deterministically without Google.
2. GA disabled/failure shown as0 audience with no provider status; verify native DOM/screenshot.
3. `SiteAnalyticsAdmin.changelist_view:470` has no `has_view_or_change_permission` guard. Django admin wrapper baseline is staff access; test staff with no analytics model permission direct URL.
4. Active draft/private Place ID can accept forged click because repository checks only active/deleted. Test published foreign Place click is public event, not automatically unauthorized; active private ID is the useful boundary.
5. Inactive-account event exclusion promised in taxonomy missing from `_base_events`; seed inactive identity history, compare current owner summary. Need controlled runtime aggregate proof.
6. Owner AZ percentage deltas append Russian `к прошлому периоду` (`owner_analytics.html:32/44`); create prior+current period fixtures and inspect rendered AZ.
7. Beacon false return silently drops local event because code returns unconditionally; SIMULATED native override with empty network capture and aggregate delta can demonstrate, if needed. Actual browser rare beacon refusal UNKNOWN until simulated.

These are not severity-assigned findings. Root must reject duplicates/false positives, assign `ANALYTICS-QA-xx` only after concrete evidence, keep source-only or unavailable outcomes NOT RUN/UNKNOWN.

## Executed / not run

Executed here: canonical document reads; Memory list/status/architecture/search/trace/coverage; direct bounded source reads and rg wiring searches; scoped `git diff --name-only` (no output). Initial trace API wrong key was corrected (`function_name`), one outdated admin-template read and one test path read failed then actual paths found. No runtime/backend/native checks executed by this specialist. No app/database/rules/assertion edits; no external integrations.

Structural verification command: `.venv/Scripts/python.exe docs/qa/module12-2026-10-11-r1/source-review/source_checks.py` — exit0, 18 source files hashed, scoped dirty files0, Python AST PASS. Evidence: `source-checks.json` (source hashes and exact definition lines; no secrets). This is a read-only source check, **zero executed application tests / runtime checks**.

Recommended suites to parent/integration-reviewer: `catalog.testcases.test_analytics_contract` (1), `test_analytics_events_v2` (7), `test_analytics_metrics` (5), `test_favorite_metrics` (3), `test_owner_analytics` (4), `test_public_favorite_count`, `test_analytics_commands` (3), `tracking`, `test_ai_referral_tracking`, relevant admin statistics tests. Node `static/js/tests/ai_referral_tracking.test.js`. Existing tracking suite baseline expects collection False; run tests profile separately from enabled native stand and preserve existing assertions. Commands must be guarded by parent isolated runner. Source/Node alone never substitutes native verification.

Named handoff: `/root` (`kidsmap-orchestrator` execution as native browser lead), `integration-reviewer` for isolated assertions/range/error adapters. Acceptance: each controlled action read-only before/after aggregate; normal-UA actors; active-private fixture; stats model ACL; disabled/error/90days GA SIMULATED profiles; owner AZ positive percentage fixture; native 18-cell matrix. No independent browser execution claimed.

Follow-up: parent native browser found same-origin explicit-port403. Fresh app+installed-Django helper verification is in `origin-port-handoff.md` / `origin-checks.json`; seven source-function checks exit0, app matches HEAD. This confirms the root cause behind parent browser evidence, without claiming independent native execution. Downstream transport adapter must be labelled SIMULATED; no app fix.

Localization follow-up: `locale-handoff.md` / `locale-checks.json` verifies15 AZ analytics locale keys,11 fuzzy PO / absent MO keys, all selected PO contents matching HEAD. Source-only command exit0, no compilation. Parent native AZ Russian labels have a confirmed fuzzy-content cause distinct from historical SITE-QA-07 valid-PO/MO mismatch; owner AZ hardcoded delta is separate.
