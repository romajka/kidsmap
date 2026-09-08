# SEO audit — 2026-09-08

Role: `seo-reviewer`; definition `.agents/agents/seo-reviewer/agent.md`. Execution identity `/root/audit_backend`, sequential role after backend/database by the same runtime worker; not a new independent reviewer. Bounded AUDIT ONLY: metadata/canonical/hreflang/sitemap/visibility/Event/SEO audit and fix side effects. No SEO command, browser, DB write, application edit or subagent. SEC-02 owns JSON-LD escaping; excluded from reproduction and duplicate findings here.

LOCAL HEAD `d75b34f4db5d4ba484cf8392ff3ae0c9939031e2`; source diff for reviewed SEO services, context processor, sitemaps and route registration empty. Dirty agent-system work preserved. Current PRODUCTION revision/feature flags/indexation/traffic UNKNOWN.

## 1. Состояние области

Read actual SEO role and `.agents/knowledge/seo.md`; reused verified current snapshot/shared contracts/source map and pricing/schedule contracts from previous sequential roles. Codebase Memory project/root/architecture already established; fresh SEO graph search and coverage preceded source reads. Broad search returned 20 of 29 hits (not exhaustive); direct symbol/source checks narrowed relevant implementations. Coverage generation `2026-09-08T06:04:25Z`, full, metadata_match/no_recorded_issue on SEO/sitemap/public_urls/context/audit/fix sources. `base.html` has explicit parse-partial ranges, so actual head/template source was read; no rendered-browser claim.

AZ uses default unprefixed paths, RU/EN prefixed paths. Canonical/alternates come from the shared context processor and stable configured public origin. Place sitemap uses public quality visibility. SEO landings use indexable thresholds, specialists use their feature flag. Event detail has content/meta and expiration gates but no Event-specific schema or sitemap registration. SEO audit/fix is a stateful application subsystem, not a read-only external crawler.

## 2. Сильные стороны

- `context_processors.py:116–159` builds canonical and language alternates consistently from path/public origin, emits x-default and explicit noindex policy. `templates/base.html:16–31` renders these values. `services/public_urls.py` and `middleware.py:49` restrict route-owned query parameters; `config/views.py:126` redirects old default-language prefixes.
- `sitemaps.py:14` enables localization/alternates/x-default and public-origin override. `PlaceSitemap:56` shares `public_place_queryset` with public content; unpublished/inactive/deleted status is not enough for inclusion. Landing thresholds and specialist flags are applied separately.
- `services/seo.py:359` derives Place metadata, coordinates and schedule from actual fields/relations. Nonregular modes do not invent weekly intervals; on-request offers do not become a fictional zero price. Exactly free price mode provides a zero offer fallback, while free-entry/events do not.
- Current dry-run correction: `services/seo_fix_engine.py:98–108` returns an **unsaved** SEOChange and exits before DB issue updates. `testcases/test_seo_audit_system.py:test_dry_run_safe_fixes_makes_zero_database_changes` covers that contract. Historical knowledge claiming current dry-run creates change rows is stale. Constructor/cache reads still do not make arbitrary SEO commands production-safe, and nothing was run here.

## 3. Реальные проблемы

All findings are current LOCAL source findings, high confidence in the code paths; exact runtime reproductions NOT RUN by this role. Production occurrence and scope UNKNOWN. Recommendations do not authorize executing these commands.

### SEO-01 — P2: scoped audit deletes unrelated unresolved issues

**Trigger:** existing open AZ/EN or other-place issues are present; execute a language-limited, place-count-limited or only-errors full audit without target_url/target_place_id. A sitemap-only engine invocation also reaches this path.

**Evidence:** `src/catalog/services/seo_audit_engine.py:49` creates a run; branch `:67–69` unconditionally deletes every open SEOIssue and orphan issue before the new audit. It does not scope deletion by language, place limit, audit type or run. `:72–77` then audits only selected categories/language/limit; `:79–80` can remove noncritical results under only_errors. `src/catalog/management/commands/audit_seo.py:23–43` exposes language/limit/only-errors and passes them directly. A later exception marks the run failed (`seo_audit_engine.py:102–108`) without restoring previous deleted issues.

**Impact:** unexamined unresolved issues disappear, older run details no longer match stored summary counts, and a failed replacement audit can lose its baseline. This is distinct from intentional recording of a new audit run; cleanup should not imply that untested defects were resolved. Owner: seo-reviewer/integration-reviewer. Next isolated test: seed open issues in two languages/places, run a bounded stubbed audit, assert out-of-scope issues and failed-run baseline remain.

### SEO-02 — P2: auto-fix marks semantic defects fixed without verifying repair

**Trigger:** an open Level A missing_canonical, missing_hreflangs or schema issue persists due to current template/data; execute the real apply path.

**Evidence:** `src/catalog/services/seo_fix_engine.py:79–90` assigns a success description for canonical/hreflang/schema cases but changes no template/context configuration. `_recheck_issue_url:131–139` checks only HTTP status, not the defective tag/schema. `_fix_single_issue:125–127` sets status FIXED unconditionally even if recheck text records a non-200/failure. `apply_safe_fixes:38` clears cache only after processing fixes; cache invalidation alone does not prove semantic repair. Unknown Level A issue codes also receive a generic processed summary (`:92–93`).

**Impact:** dashboard reports a defect fixed while the page can still lack the canonical/schema or even fail the recheck. No actual indexing loss is asserted. Owner: seo-reviewer + QA. Next isolated test: serve HTTP 200 with the original missing tag, then non-200; verify the issue remains open until its original detector passes. Scope supported fix actions explicitly instead of declaring generic success.

### SEO-03 — P2: rating rollback records success without restoring old values

**Trigger:** apply a rating recalculation through SEOFixEngine and then rollback its reversible change.

**Evidence:** `src/catalog/services/seo_fix_engine.py:64–77` stores the prior rating_count/rating_avg in old_value and saves recalculated values. `rollback_change:152–157` detects the rating marker, but merely calls `place.save()`; it neither parses nor reassigns the old values. `:161–167` then marks the change rolled back and reopens its issue. Thus rollback metadata claims completion without reversing the persisted rating mutation.

**Impact:** audit trail misrepresents recovery and prior values are not restored. Price/content fields are not affected by this specific branch; no general rollback capability claim. Owner: seo-reviewer/backend owner. Next isolated test: record distinct old/new ratings, apply+rollback, refresh Place, assert exact old values and truthful change status. Atomic failure handling belongs in the reviewed implementation plan.

## 4. Tech debt

Event discoverability gap freshly rechecked: `src/catalog/views.py:1192–1220` renders Event detail with title/description, published/not-deleted/future-end gates and canonical-slug redirect. `templates/catalog/event_detail.html:1–9` has no Event extra_head block. `services/seo.py` has no Event payload builder, and `config/urls.py:21–26` registers only static/places/seo/specialists sitemaps. The generic base Organization/WebSite scripts remain present; this is absence of **Event-specific** schema, not absence of all JSON-LD. Static sitemap includes events landing when enabled. Product decision required before assigning implementation priority: feature flag/current public Event count and search strategy UNKNOWN. Bounded P3 follow-up, not a proven production indexability outage.

The audit engine accepts target_page_type and skip_performance (`seo_audit_engine.py:45–47`) but these names have no later uses in the source inspected. CLI options therefore overstate selection/verification coverage; do not infer a page-type-limited or external-performance audit from command flags alone. No command was run to certify this behavior.

## 5. Risks

SEC-02 JSON-LD script-context handling is an existing security-owned dependency, not repeated here. BE-01/BE-03 price/schedule loss can change visibility/schema indirectly; DB migration findings also affect Offer/schedule consistency. Any future backend changes need SEO regression. Google/Bing indexation, rich-result eligibility, canonical chosen by search engines, deployed robots headers and live sitemap responses UNKNOWN; no external SEO performance promises.

`SEOAuditEngine.__init__:32` uses Django test Client; `_get_page:113` renders app responses, not nginx/TLS/CDN/browser evidence. `run_audit` creates/deletes/saves DB records. Real fix/rollback writes DB and clears cache. Current true dry-run returns unsaved changes, but historical docs and generic command names are insufficient authorization for production execution.

## 6. Dead/legacy candidates

No deletion candidates confirmed. Old default-language redirect and query cleanup are active compatibility paths. Event model is a separate implemented public surface; missing Event sitemap does not make it dead code. Audit/fix engines are active and require truthful state transitions rather than deletion. SEO knowledge dry-run claim should be corrected in a separately owned documentation change; this role changes only its assigned report.

## 7. Tests gaps

Executed here: projected graph coverage/search, targeted source reads and app-scope git diff (empty), report whitespace/section validation. NOT RUN: SEO management commands, custom fixtures, browser/head inspection, external crawler/search tools, production requests or DB changes.

Attributed [qa.md](qa.md): selected eight-label run executed 375 tests, exit 1 with 12 failure records all in public.py; non-public selected pricing/round-trip/landing visibility modules had no failure records. Exact commands/isolation are in QA section 1; this does not establish whole SEO subsystem correctness. `catalog.testcases.test_seo_audit_system` was inspected here, not newly executed. Needed cases: scoped audit preserves unrelated/history records; failed audit retains baseline; semantic fix detector gates FIXED; rating rollback actually restores values; Event-specific sitemap/schema if enabled and product-approved. AZ/RU/EN canonical/hreflang/robots and HTTP redirect matrix require root browser/runtime evidence separately.

## 8. Recommendations

1. Preserve audit history/out-of-scope issues and make failed replacement audits non-destructive.
2. Require the original semantic detector to pass before FIXED; HTTP 200 alone is insufficient.
3. Implement and verify actual rollback restoration before marking changes reversible/rolled-back.
4. Resolve Event indexing scope with product owner, then add only supported Event metadata/sitemap behavior.

All implementation remains recommendations pending concrete approved scope. No live SEO audit/fix/rollback is authorized by this report.

## 9. P0/P1/P2/P3

| Priority | Findings | Evidence boundary |
|---|---|---|
| P0/P1 | No new findings in bounded role | SEC-02 stays security-owned |
| P2 | SEO-01, SEO-02, SEO-03 | Current source; custom runtime/prod unverified |
| P3 | Event discovery gap/options/documentation debt | Product/feature applicability still UNKNOWN |

Handoff: lead consolidates with SEC/BE/DB without duplicate IDs; integration reviewer owns isolated tests; frontend owns rendered head; release owns deployed headers/origin/feature-state checks. Sequential role changed only seo.md.
