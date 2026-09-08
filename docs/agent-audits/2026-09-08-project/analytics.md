# Analytics audit — 2026-09-08

Role analytics-reviewer, applied sequentially by coordinator /root after reading actual definition; not an independently spawned analytics worker. LOCAL HEAD d75b34f, application unchanged; prior agent-system WORKTREE retained. Production/real GA state UNKNOWN. Scope reporting periods, client referral tests and event storage contract; no external analytics events or private records.

## 1. Состояние области

GA reporting lives in google_analytics_reporting; admin_analytics builds dashboard. tracking supports queued GA events and optional local FunnelEvent persistence; SiteVisit/referral are separate consumers. Graph search found _ga_period_key; exact coverage for six relevant service/client/test paths metadata matched, best-effort only; source read directly.

## 2. Сильные стороны

Event types use allowlists; local raw event storage is explicitly gated by LOCAL_ANALYTICS_STORAGE_ENABLED. Referral classifier has standalone Node assertions including internal navigation exclusion. External reporting returns a connection/error state; no real GA connection claimed by this audit.

## 3. Реальные проблемы

### AN-01 — P2: “90 days” dashboard KPI requests yearly data

Trigger: select period=90 in `templates/admin/catalog/site_analytics.html:21`; `domain_admin/site.py:472-480` passes90 to build_statistics_context. `services/admin_analytics.py:37-42,65-69` maps90 to year, while displayed period_start is90 days. `google_analytics_reporting.py:61-66` defines year as364daysAgo through today. KPI therefore represents365 days under a90-day selected period when GA data is available.

Executed isolated stdlib proof: AST-extracted actual _ga_period_key, no Django import/network; results7→week,30→month,90→year,365→year. Full GA response not fetched. This is a deterministic mapping error, not a fabricated discrepancy in real audience counts.

## 4. Tech debt

Period keys and arbitrary day-count selection have different domains. Daily/top-page/top-event charts use fixed30-day queries; where labeled30 days this is a separate intentional window, not automatically AN-01. A single explicit reporting-range contract would make the distinction testable.

## 5. Risks

build_snapshot sequentially requests four period reports, daily chart, top pages and top events; _run_report calls client.run_report without local timeout/cache arguments. Potential request latency/quota exposure, not measured slowdown. SDK defaults must be checked before claiming “no timeout at all”. Missing/failed GA data must remain distinguishable from actual zero activity; no external config/credential inspection performed.

## 6. Dead/legacy candidates

Optional raw analytics persistence is not dead merely because disabled in isolated audit settings. No event models/tables/history nominated for deletion without deployment/data evidence.

## 7. Tests gaps

Executed `node static/js/tests/ai_referral_tracking.test.js`: exit0, “AI referral tracking tests passed”. Exact helper period probe exit0 with mapping above. These validate local classification/mapping only, not GA transport, consent, production event deduplication or real dashboard values. Django coverage and browser CTA evidence belong to qa.md/browser.md; no duplicated claim.

## 8. Recommendations

Fix90-day KPI mapping under separate approved scope with explicit range assertions. Measure GA latency before cache/retry optimization. Preserve local/GA delivery distinction and avoid manufacturing zeros when disconnected. Handoff: Django reporting owner → integration-reviewer period tests; browser/frontend for CTA changes only.

## 9. P0/P1/P2/P3

AN-01 P2 source-confirmed and pure helper reproduced. No P0/P1 analytics finding; latency is unmeasured risk. Current GA delivery/configuration/data UNKNOWN. No application edits, provider requests, event injections or production writes.
