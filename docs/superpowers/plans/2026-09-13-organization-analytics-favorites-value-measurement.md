# Organization Analytics, Favorites Count and KidsMap Value Measurement Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use test-driven-development and verification-before-completion to implement this plan task by task.

**Goal:** Start collecting trustworthy, privacy-conscious interaction history now and expose authorized Place-level insights, while keeping a single raw event per user action and preserving a clean path to Organization → Place → Activity rollups.

**Architecture:** Evolve the existing `FunnelEvent` pipeline into a versioned canonical event stream. `PlaceLike` remains the source of truth for current Favorites; add/remove events describe history and never drive the current count. A dedicated aggregation service calculates event totals, unique visitors, unique sessions, current Favorites and equal-period comparisons. It resolves parent scopes from domain relations at query time so one Activity event can later roll up to Place and Organization without cloning the event. The current repository has `Place`, `Event` and `Specialist`, but no `Organization` or `Activity` model; collection starts with Place and the Organization/Activity resolvers are enabled only when architecture №33 provides real domain IDs and ownership relations.

**Tech Stack:** Django models/migrations, PostgreSQL-compatible ORM aggregation, server-rendered Django templates, existing JavaScript event transport, Django `TestCase`, management commands, existing Place permission scopes.

**Spec:** User attachment of 2026-09-13: Organization/Place/Activity analytics, canonical event taxonomy, distinct event/user/session/Favorite metrics, public Favorites candidate, abuse resistance, owner insights, hierarchy-safe aggregation and future monetization boundaries.

---

## Scope and decisions

### Confirmed implementation scope

- Record one canonical event for each accepted action. Do not create separate Organization, Place and Activity copies of one action.
- Canonical v2 event names:
  `organization_view`, `place_view`, `activity_view`, `favorite_added`, `favorite_removed`, `phone_click`, `whatsapp_click`, `website_click`, `social_click`, `directions_click`.
- Preserve existing funnel events and normalize these aliases at read time:
  `place_open → place_view`, `cta_call → phone_click`, `cta_whatsapp → whatsapp_click`, `cta_instagram → social_click`, and `favorite_toggle` plus `event_meta.action` to `favorite_added` or `favorite_removed`.
- Do not rewrite old event rows. New writes use event schema version 2; reports read both versions so history remains continuous.
- Implement Place collection and Place owner insights first. `Organization` and `Activity` event acceptance/rollups stay disabled until their domain models and relationships from architecture №33 exist in this repository.
- Treat `PlaceLike` rows belonging to active, registered, non-excluded users as the authoritative current Favorite set. `Place.likes_count` remains a reconciled cache for ordering and legacy UI only.
- Add local raw-event retention and aggregate privacy rules before enabling owner analytics in production.
- Keep advanced/paid analytics, prices, export and AI insights out of this implementation.

### Product gates that must remain configurable and off by default

| Decision | Safe default | Activation requirement |
|---|---|---|
| Public Favorites Count | Disabled | Product owner approves the wording, locations and the exact small-count rule. |
| Small Favorites threshold | Unset | Product owner explicitly chooses `0`, `1`, `2`, `3` or another threshold; code must not invent one. |
| Free versus paid metrics | No paywall | Separate product and billing decision. |
| Owner reporting periods | 30 days only | Product/privacy owners approve longer periods together with compatible raw-data retention. |
| Organization/Activity scope | Disabled | Architecture №33 is checked into the repository with stable IDs, parent relations and analytics ownership. |
| Local analytics production storage | Existing default remains off | Privacy owner approves purpose, legal basis, retention, user disclosure and operations schedule. |

## Current source audit

- `FunnelEvent` already stores event type, day, path, nullable Place/User, a raw session key, metadata and timestamp. Its taxonomy uses legacy names and has no subject type, Organization ID, Activity ID, language/device/referrer dimensions or retention command.
- Local persistence is controlled by `LOCAL_ANALYTICS_STORAGE_ENABLED` and defaults to false. GA4 emission and local persistence are separate paths.
- Place views, phone, WhatsApp and Instagram are partly instrumented. `cta_map` is present in the Place HTML but is rejected by `CLICK_EVENT_TYPES`; website links are not instrumented.
- `favorite_toggle` records the result in metadata, while the requested contract needs distinct add/remove events.
- `PlaceLike` has database uniqueness for `(place, user)`. The public toggle already requires login, but legacy anonymous rows are allowed by the model and cached `Place.likes_count` counts every row without filtering inactive users.
- The owner dashboard exposes a `place.stats.view` permission but currently shows cached likes/reviews and no event-derived analytics.
- `Organization` and `Activity` domain models are absent. `Event` and `Specialist` exist. No source file for the referenced architecture №33 was found.
- Baseline on LOCAL HEAD `a66842f`: 25 focused tracking/Favorite/owner tests pass with `DJANGO_TESTING=1`.

## Canonical measurement contract

### One event, one subject

Every v2 event has exactly one direct subject:

```text
event_id
schema_version = 2
event_type
subject_type = organization | place | activity | event | specialist
subject_id
occurred_at
user_id (nullable internal FK)
visitor_key_hash
session_key_hash
source
page_type
language
device_class
referrer_domain
campaign
event_meta (allowlisted action-specific values only)
```

`visitor_key_hash` unifies authenticated activity across sessions and represents one browser session for anonymous activity. `session_key_hash` always supports session-level uniqueness. Both are keyed, versioned hashes; raw session keys, IP addresses, full user-agent strings, full referrer URLs and arbitrary client metadata are not stored in new rows.

### Metric definitions

| Metric | Definition |
|---|---|
| Views | Count of canonical `*_view` events in the selected scope and period. |
| Unique visitors | Count of distinct non-empty `visitor_key_hash` values after bot, staff and active exclusion filters. |
| Unique sessions | Count of distinct non-empty `session_key_hash` values after the same filters. |
| Favorites | Current distinct `PlaceLike.user_id` count for active registered users who are not excluded; independent of the reporting period. |
| Favorite additions/removals | Counts of canonical `favorite_added` / `favorite_removed` events in the period. |
| Contact actions | Sum of `phone_click`, `whatsapp_click`, `website_click` and `social_click`. |
| Directions | Count of `directions_click`. |
| Activity interactions | Activity-scoped events rolled up through the current Activity → Place relation after architecture №33 is available. |
| Change | Current period compared with the immediately preceding period of the same length; show no percentage when the prior value is zero. |

Organization totals query the raw events through subject/parent relationships and count distinct event IDs or visitor hashes. They must never sum branch-level unique visitor totals.

## Task 1: Check in the taxonomy and activation contract

**Files:**

- Create: `docs/product/analytics-event-taxonomy.md`
- Create: `docs/product/analytics-operations.md`
- Modify: `docs/ai_referral_analytics.md`
- Test: `src/catalog/testcases/test_analytics_contract.py`

**Steps:**

1. Write a contract test that loads the taxonomy document and verifies that every canonical event has a stable name, subject rule, allowed metadata, source of truth and metric mapping.
2. Document the v1 aliases, v2 schema, uniqueness definitions, bot/staff/exclusion policy, property ownership, privacy fields, retention dependency and GA4/local-store separation.
3. Document the deployment order: schema → code in dual-read mode → retention schedule → local collection activation → owner UI activation.
4. Record that no historical backfill exists for events that were never collected.
5. Record the six unresolved product decisions from the table above. The public counter configuration must reject activation while its threshold is unset.

## Task 2: Add the v2 event envelope without breaking history

**Files:**

- Modify: `src/catalog/models/site.py`
- Modify: `src/catalog/interfaces/tracking.py`
- Modify: `src/catalog/repositories/tracking_repositories.py`
- Create: `src/catalog/services/analytics_identity.py`
- Modify: `src/catalog/services/tracking.py`
- Modify: `src/config/settings.py`
- Create: `src/catalog/migrations/0105_analytics_event_v2.py` (use the next free number at implementation time if another approved plan lands first)
- Modify: `src/catalog/domain_admin/site.py`
- Test: `src/catalog/testcases/test_analytics_events_v2.py`

**Steps:**

1. First add failing tests for canonical choices, schema version, one direct subject, hashed visitor/session identifiers and metadata allowlisting.
2. Add indexed structured fields to `FunnelEvent`: `schema_version`, `subject_type`, `subject_id`, `occurred_at`, `visitor_key_hash`, `session_key_hash`, `source`, `page_type`, `language`, `device_class`, `referrer_domain` and `campaign`. Keep existing `place`, `user`, `session_key`, `path`, `event_meta`, `day` and `created_at` readable during transition.
3. Add a check constraint requiring both `subject_type` and `subject_id` for v2 entity events. Do not invent Organization or Activity rows.
4. Generate keyed, versioned hashes server-side. Add a dedicated analytics hash key setting and a Django system check that prevents local production collection when the key or approved retention setting is absent.
5. Stop populating raw `session_key` on v2 rows. Limit source/page/device/language/referrer/campaign to server allowlists and bounded lengths; normalize referrer to a host and UTM data to accepted scalar values.
6. Reject client-supplied user IDs, visitor hashes, session hashes, timestamps, Organization IDs and parent IDs. Resolve identity, time and subjects on the server.
7. Add indexes for `(subject_type, subject_id, occurred_at, event_type)`, `(event_type, occurred_at)` and the two hashed identity fields needed by distinct counts.
8. Show schema version, subject and safe dimensions in the staff analytics admin. Never show raw session keys in new-event views.
9. Run migrations only against the isolated test database and run the new model/repository tests.

## Task 3: Write canonical events from real user actions

**Files:**

- Modify: `src/catalog/services/tracking.py`
- Modify: `src/catalog/controllers/tracking_controller.py`
- Modify: `src/catalog/views.py`
- Modify: `src/catalog/controllers/place_controller.py`
- Modify: `src/catalog/templates/base.html`
- Modify: `src/catalog/templates/catalog/place_detail.html`
- Modify: `src/catalog/templates/catalog/place_list.html`
- Modify: `src/catalog/templates/catalog/includes/place_card.html`
- Modify: `static/js/place_phone_reveal.js`
- Test: `src/catalog/testcases/tracking.py`
- Test: `src/catalog/testcases/public.py`

**Steps:**

1. Add failing tests proving that Place render produces one `place_view`, each accepted CTA resolves an active Place server-side, and unsupported/forged subjects are rejected.
2. Add separate canonical event constants and retain legacy constants as read-only aliases.
3. Accept `phone_click`, `whatsapp_click`, `website_click`, `social_click` and `directions_click`; replace the ineffective `cta_map` markup with `directions_click` and instrument every public Place website/social/contact location.
4. Emit `favorite_added` or `favorite_removed` only from the successful server-side toggle result. Do not trust a client-provided favorite action and do not increment a counter from the event stream.
5. Make the favorite state mutation and its event write consistent. Use `transaction.on_commit()` or a transactionally written local event so a failed mutation cannot emit a false saved/removed result.
6. Deduplicate accidental duplicate page-view writes for the same request. Preserve repeated legitimate visits as events; uniqueness is calculated in reporting, not by discarding repeated views.
7. Keep the existing same-origin checks and rate limit. Add per-event validation and automated-client classification; rate-limited or invalid attempts do not become owner-visible events.
8. Emit canonical names to GA4 as well as the local store, without sending internal user IDs or analytics hashes to GA4.
9. Verify AZ/RU/EN page context, website, social, phone, WhatsApp and route CTAs with focused request tests.

## Task 4: Make Favorites an authoritative, abuse-filtered state metric

**Files:**

- Modify: `src/catalog/models/place.py`
- Modify: `src/catalog/services/reactions.py`
- Create: `src/catalog/services/favorite_metrics.py`
- Create: `src/catalog/models/analytics.py`
- Modify: `src/catalog/models/__init__.py`
- Create: `src/catalog/migrations/0106_analytics_exclusions_and_like_constraints.py` (renumber with Task 2 if needed)
- Create: `src/catalog/management/commands/reconcile_place_favorite_counts.py`
- Test: `src/catalog/testcases/test_favorite_metrics.py`
- Test: `src/catalog/testcases/test_analytics_commands.py`

**Steps:**

1. Add failing tests for one registered user per Place, inactive/deleted/excluded users, add/remove idempotency, cached-count drift and concurrent toggles.
2. Audit legacy `PlaceLike` rows before tightening constraints. Add a constraint that a Favorite has an authenticated user and a non-empty-user uniqueness rule; provide a deterministic data migration for invalid/duplicate legacy rows based on the audit result.
3. Add an `AnalyticsActorExclusion` record for staff-reviewed metric exclusions with reason code, actor reference/hash, start/end, creator and timestamps. Do not expose it to owners.
4. Implement `eligible_favorites_queryset(*, place_ids: Collection[int])` as the only source for owner/public Favorite metrics: distinct registered users, `user.is_active=True`, no active analytics exclusion.
5. Keep `Place.likes_count` as a cache, update it from the authoritative queryset after toggles, and supply an idempotent `--dry-run` reconciliation command for operational repair.
6. Ensure deactivation, account-deletion anonymization and exclusion changes schedule reconciliation for affected Places. This must integrate with the approved account-deletion plan rather than create a second deletion policy.
7. Verify that repeated clicks and concurrent requests cannot inflate the current Favorite set or add-event count.

## Task 5: Build one aggregation service for staff and owners

**Files:**

- Create: `src/catalog/services/analytics_metrics.py`
- Modify: `src/catalog/services/admin_analytics.py`
- Test: `src/catalog/testcases/test_analytics_metrics.py`
- Test: `src/catalog/testcases/admin.py`

**Steps:**

1. Add failing tests for event totals, distinct visitors, distinct sessions, current Favorites, contact actions, directions and current/previous equal-length windows.
2. Normalize v1 aliases at query time and combine them with v2 events without double counting a row.
3. Introduce a typed result contract:

   ```python
   build_subject_metrics(*, subject_type, subject_ids, start, end) -> AnalyticsSummary
   ```

4. Scope every query by explicit subject IDs. Return `None` for unavailable metrics and comparisons instead of presenting zero as collected truth when local storage was disabled.
5. Implement Place rollups first. Add resolver interfaces for Organization and Activity, with tests that keep those types unavailable until real architecture №33 adapters are registered.
6. For future Organization aggregation, query the raw event set across all related Places/Activities and apply `COUNT(DISTINCT visitor_key_hash)` once. Add a contract test that demonstrates why summing two Place unique counts would be wrong.
7. Reuse the same service in the staff Site Analytics page where definitions overlap; do not maintain a second formula for the same metric.

## Task 6: Add an authorized Place Analytics owner page

**Files:**

- Modify: `src/catalog/urls.py`
- Modify: `src/catalog/views.py`
- Create: `src/catalog/controllers/owner_analytics_controller.py`
- Create: `src/catalog/templates/pages/owner_analytics.html`
- Modify: `src/catalog/templates/pages/owner_places.html`
- Modify: `static/css/pages/account_profile.css`
- Test: `src/catalog/testcases/test_owner_analytics.py`

**Steps:**

1. Add failing permission tests for direct owners, scoped team members with `place.stats.view`, users without that permission, volunteers, unrelated owners, deleted Places and unpublished Places.
2. Add a route scoped to a Place ID and a controller that derives allowed Place IDs from the existing `place.stats.view` permission. Return the same non-disclosing response for missing and unauthorized subjects.
3. Render a 30-day dashboard with Views, Unique visitors, Favorites, Contact actions and Directions, plus equal-period comparison where available.
4. Clearly label Favorites as “users who saved this Place”; do not describe it as visits, recommendations or quality.
5. Show “data collection unavailable/not enabled for this period” separately from a measured zero.
6. Add event-collection start date and last-updated time. Do not expose raw users, sessions, referrers or events to owners.
7. Hide small source/campaign/device segments below a documented privacy cohort threshold and omit those breakdowns from the first owner release.
8. Add an Analytics link only for Places where the current user has `place.stats.view`.
9. Verify keyboard navigation, focus, responsive layout and AZ/RU/EN labels at 360, 768, 1366 and 1440 CSS pixels after implementation.

## Task 7: Prepare, but do not silently activate, public Favorites Count

**Files:**

- Modify: `src/catalog/models/site.py`
- Create: `src/catalog/migrations/0107_public_favorite_count_settings.py` (renumber with Tasks 2 and 4 if needed)
- Modify: `src/catalog/controllers/place_controller.py`
- Create: `src/catalog/templates/catalog/includes/favorite_social_proof.html`
- Modify after product approval: `src/catalog/templates/catalog/place_detail.html`
- Modify after product approval: `src/catalog/templates/catalog/includes/place_card.html`
- Test: `src/catalog/testcases/test_public_favorite_count.py`

**Steps:**

1. Add configuration fields for `public_favorites_count_enabled` and a nullable `public_favorites_minimum`. Validate that enabling is impossible while the minimum is unset.
2. Add failing tests proving that the count is hidden by default, uses `eligible_favorites_queryset`, excludes anonymous/inactive/excluded users and respects the exact configured threshold.
3. Implement a localized, accessible partial whose meaning is only “saved by N users”. Do not use review, visit, recommendation or quality language.
4. Add the partial to approved surfaces only after the product owner approves wording, design and threshold. Until then, ship the configuration and tests with rendering disabled.
5. Do not use `Place.likes_count` directly in the public partial.

## Task 8: Add retention, data-quality operations and safe observability

**Files:**

- Create: `src/catalog/management/commands/purge_analytics_events.py`
- Create: `src/catalog/management/commands/audit_analytics_quality.py`
- Modify: `src/config/settings.py`
- Modify: `docs/product/analytics-operations.md`
- Test: `src/catalog/testcases/test_analytics_commands.py`

**Steps:**

1. Add failing tests for dry-run, cutoff boundaries, idempotency, batch processing, legal/privacy hold behavior if approved, and refusal to run with an invalid retention configuration.
2. Require an explicit `ANALYTICS_RAW_EVENT_RETENTION_DAYS`; do not invent a default production duration. Document that a 30-day current-versus-previous report needs at least 60 days of usable history.
3. Purge raw v1 session keys as part of the approved migration/retention rollout. Preserve only approved non-identifying aggregates if such aggregates are part of the retention decision.
4. Add daily quality output containing aggregates only: accepted/rejected event counts, unknown subjects, empty identity hashes, rate-limit totals, cache drift, excluded-actor impact and collection gaps. Never print user-level rows, session hashes or referrer details.
5. Document scheduler ownership, alerting, retry, rollback and the effect of backup retention. Do not run the commands against production as part of implementation.

## Task 9: End-to-end verification and rollout evidence

**Files:**

- Modify: `docs/product/analytics-operations.md`
- Test: `src/catalog/testcases/test_analytics_events_v2.py`
- Test: `src/catalog/testcases/test_analytics_metrics.py`
- Test: `src/catalog/testcases/test_favorite_metrics.py`
- Test: `src/catalog/testcases/test_owner_analytics.py`
- Test: `src/catalog/testcases/test_public_favorite_count.py`
- Test: `src/catalog/testcases/test_analytics_commands.py`
- Test: `src/catalog/testcases/tracking.py`
- Test: `src/catalog/testcases/public.py`
- Test: `src/catalog/testcases/owner.py`
- Test: `src/catalog/testcases/admin.py`

**Steps:**

1. Run the focused suite with isolated settings:

   ```powershell
   $env:DJANGO_TESTING='1'
   .\.venv\Scripts\python.exe manage.py test `
     catalog.testcases.test_analytics_contract `
     catalog.testcases.test_analytics_events_v2 `
     catalog.testcases.test_analytics_metrics `
     catalog.testcases.test_favorite_metrics `
     catalog.testcases.test_owner_analytics `
     catalog.testcases.test_public_favorite_count `
     catalog.testcases.test_analytics_commands `
     catalog.testcases.tracking --noinput
   ```

2. Run affected regression modules:

   ```powershell
   $env:DJANGO_TESTING='1'
   .\.venv\Scripts\python.exe manage.py test `
     catalog.testcases.public `
     catalog.testcases.owner `
     catalog.testcases.admin `
     catalog.testcases.auth_flow --noinput
   ```

3. Run `makemigrations --check --dry-run` under `DJANGO_TESTING=1` and confirm no uncommitted migration drift.
4. Use isolated fixtures to verify this sequence: search/referrer → Place view → Activity unavailable until architecture adapter → phone/WhatsApp/site/social/directions → add Favorite → remove Favorite → owner dashboard. Confirm one raw event per action and correct event/user/session/current-Favorite numbers.
5. Verify two Places sharing one visitor: Place reports each show one unique visitor; a synthetic Organization resolver reports one unique visitor, not two.
6. Verify collection-disabled periods, zero metrics, inactive/excluded accounts, data purging and cached-Favorite reconciliation.
7. Record exact commands, commit/working-tree snapshot, pass/fail totals and the intentionally disabled Organization/Activity/public-counter scope in the implementation report.

## Rollout order

1. Approve architecture №33 identifiers/relations, public Favorite decisions and analytics privacy/retention policy.
2. Deploy schema and dual-read code with owner/public features disabled.
3. Run quality and Favorite reconciliation commands in dry-run mode; review aggregate results.
4. Configure the approved hash key and retention schedule, then enable local v2 collection.
5. Observe collection quality for an agreed burn-in period and record the first reliable collection timestamp.
6. Enable Place owner analytics for authorized accounts.
7. Enable Organization/Activity resolvers only after their domain relations exist and hierarchy tests pass.
8. Enable public Favorites Count only after the explicit wording/design/threshold decision.

## Acceptance criteria

- Every accepted v2 action creates one canonical local event with a real subject and server-derived identity/dimensions.
- A repeated visitor increases Views but not Unique visitors; multiple sessions affect Unique sessions without duplicating an authenticated unique visitor.
- One active registered user has at most one current Favorite per Place, and add/remove events match committed state changes.
- Current Favorites exclude inactive, deleted and actively excluded users and do not depend on click count.
- Phone, WhatsApp, website, social and directions CTAs are all accepted and measurable.
- Owners can see only aggregate analytics for Places covered by `place.stats.view`; disabled collection is distinguishable from zero.
- Parent rollups count raw event IDs/visitor hashes once and never sum branch-level unique counts.
- Public Favorites Count is off by default and cannot be enabled without an explicit small-count threshold.
- Raw analytics has an approved retention period, an idempotent purge command and aggregate-only operational diagnostics.
- No paid analytics, pricing, export or AI insights are implied or enabled.

Plan complete and saved to `docs/superpowers/plans/2026-09-13-organization-analytics-favorites-value-measurement.md`. Implementation requires approval under the repository rule in `AGENTS.md`: “Future implementation requires a concrete plan and user approval for its scope.”
