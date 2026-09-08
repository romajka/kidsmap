# Backend domain audit — 2026-09-08

Role: `django-reviewer`; execution identity: `/root/audit_backend`, independent specialist, definition `.agents/agents/django-reviewer/agent.md`. Mode: AUDIT ONLY. Final bounded scope: price/schedule validation, owner/admin draft versus submission/publication, JSON round-trip and PricingPlan projections. Authentication/access-control and event moderation are excluded from this final report after the lead narrowed scope; migration mechanics belong to database-reviewer. No application edits, production access, scripts importing settings, commits or subagents.

Snapshot: LOCAL HEAD `d75b34f4db5d4ba484cf8392ff3ae0c9939031e2`. `git diff --name-only -- src/catalog static/admin/js/kidsmap_place_json_import.js` returned no changes. Dirty agent-system WORKTREE preserved. Current PRODUCTION code/data and affected row count: UNKNOWN. September 6 observations and validation A/C are navigation only.

## 1. Состояние области

Relational PricingPlan is the main tariff source, with deliberate scalar/JSON legacy compatibility. `Place.save` dispatches pending tariff payloads to atomic replacement; row signals update five scalar projections. Schedule is shared through `PlaceScheduleEditorFormMixin` and `place_schedule`, while publication requirements split between canonical readiness and owner `publication_errors`. Admin existing-live compatibility is intentional, but does not ensure preservation of legacy price values.

Discovery: Codebase Memory `list_projects` selected `home-ramin-kidsmap`, root `/home/ramin/kidsmap`; `index_status` ready, full architecture discovery 8,338 nodes/31,383 edges. First coverage generation `2026-09-08T05:40:34Z`; later shared generation `2026-09-08T05:54:13Z`, full/complete, metadata_match/no_recorded_issue for cited forms/admin/model/rules/readiness/importer/test files, plus pricing/schedule/volunteer services. This is best-effort coverage, not proof of completeness. Templates have parse gaps; none are used as rendered-browser proof. Graph search located publication_errors and sync_place_schedule; inbound trace confirmed forms → owner/admin/volunteer save callers, but was truncated (6 of 7), so no exhaustive caller/dead-code claim. Critical edges were read in actual source. An initial glob-style search returned zero and was corrected to regex; an initial trace argument mismatch was corrected, not treated as absent code.

## 2. Сильные стороны

- `services/pricing_plans.py:182` normalizes canonical/legacy payloads and validates candidates; `:294` atomic replacement retains matching IDs and derives scalar projections. `models/pricing_plan.py:233` validates direct saves; `:247` signals cover direct deletion.
- Owner `forms.py:1392` explicitly avoids assigning an empty pending tariff payload to an existing scalar-only place. `testcases/permanent_place_wizard.py:161` contains a focused preservation regression test.
- Canonical readiness understands three price modes without tariffs and four schedule modes without weekly days (`place_readiness.py:239`). Short real descriptions are advice rather than a publication blocker (`:164`).
- New publication readiness, already-live compatibility, draft persistence and public SQL visibility are intentionally distinct contracts. Their mere difference is not a finding.

## 3. Реальные проблемы

All findings below apply to unchanged LOCAL source. Source confidence is high; exact UI/database reproductions were NOT RUN by this specialist. Production applicability and occurrence remain UNKNOWN. Test execution is owned by `/root/audit_qa`, and its final evidence must be attributed separately.

### BE-01 — P1: ordinary admin save clears scalar-only legacy prices

**Trigger:** an existing published/active place has no relational/JSON tariffs, but one or more scalar prices. Submit a valid ordinary admin edit with the existing empty tariff editor (`pricing_plans=[]`), without changing price information.

**Evidence chain:** `src/catalog/domain_admin/place.py:233–234` always sets `instance.pricing_plans` to normalized `[]`; unlike owner `forms.py:1392`, there is no scalar-only preservation guard. Admin `:269–284` permits ordinary edits to existing live cards under compatibility. `PlaceAdmin.save_model` at `:4854` delegates persistence without restoring scalars. `src/catalog/models/place.py:592–615` detects the pending payload and calls replacement. `services/pricing_plans.py:295–333` calls `sync_legacy_price_fields` even with zero tariffs; `:345–368` writes all five scalar fields as None when the relational set is empty. The admin form excludes these scalar fields (`domain_admin/place.py:172`), so the routine edit provides no replacement values.

**Impact:** persisted price information disappears during an unrelated edit. For tariff-mode cards without another price source, public price visibility can also be lost (`services/content_quality.py:192`, `_has_price_q`). This is a data-preservation failure, not a request to abolish legacy compatibility or disable deliberate deletion of real tariffs. P1 is justified by silent loss of the sole stored price source; no production incident is asserted.

**Verification:** fresh source trace, no runtime reproduction. Existing owner-only regression does not cover admin. Reproduce next in isolated DB with scalar 80/120, normal valid admin edit, DB refresh, assert values and public visibility remain. Owner: django-reviewer; dependencies database-reviewer for legacy scope and QA for fixture proof. Escalated to lead during audit.

### BE-02 — P2: owner submission uses incompatible price/schedule/description requirements

**Trigger:** submit an otherwise complete new owner place using free/free_entry_paid_services/events with no tariff; or a genuine description shorter than 120 characters. Conversely, submit an owner place with regular text-only schedule.

**Evidence:** `src/catalog/forms.py:1469` invokes `services/permanent_place_rules.py:15`. That helper unconditionally requires a public primary tariff at `:36–42`, blocks description shorter than 120 at `:28`, and accepts legacy schedule text at `:34`. Canonical readiness exempts the three non-tariff price modes (`services/place_readiness.py:252`), accepts short genuine AZ description (`:164`), and rejects regular text-only schedules (`:275–292`). Admin uses `evaluate_form_readiness` (`domain_admin/place.py:268`); separate saved-card submission calls `place_quality_check` (`controllers/owner_places_controller.py:1067`).

**Impact:** an owner cannot submit a valid free place through the form, while saved-card/admin evaluation treats that price mode as complete; the text-only schedule goes the opposite direction and reaches moderation without satisfying canonical schedule readiness. Owner form errors, completeness and moderation expectations disagree. This finding concerns current entry-point parity, not ordinary live legacy edits.

**Verification:** source-only. Needed matrix: all four price modes, five schedule modes, genuine AZ description below/above 120, create submit versus saved submit versus admin readiness. Owner: django-reviewer with frontend reviewer for client messages; product decision on one canonical new-submission contract before implementation.

### BE-03 — P2: malformed schedule JSON can silently erase a saved regular schedule

**Trigger:** draft-save an owner/admin regular place with existing weekly hours and a nonempty malformed `structured_schedule` value, e.g. a truncated JSON payload. This finding does not depend on publication being allowed.

**Evidence:** `services/place_schedule.py:202–220` converts JSON parse failure into seven closed days; `:300` validates that fallback without a parse error. Shared form initializer (`forms.py:125–130`) and cleaner (`:149–171`) use this result. Draft does not require meaningful publication schedule. `forms.py:174–178` calls `sync_place_schedule` for regular mode; `place_schedule.py:418–420` deletes existing days and returns when the payload has no meaningful hours. Owner persistence calls `save_schedule` (`controllers/owner_places_controller.py:867`); admin `save_model` does the same (`domain_admin/place.py:4880`). Transactions cannot prevent a successful but semantically incorrect replacement.

**Impact:** a truncated schedule payload is accepted as an intentional empty schedule, losing saved opening hours. Clean new-publication readiness limits some entry points, but does not protect draft saves. Empty deliberate schedules remain legitimate draft content and should be distinguished from parse failure.

**Verification:** source-only; needed isolated existing-hours → malformed draft POST → form error and unchanged days regression. `VolunteerPlaceForm.__init__` (`volunteer_forms.py:46`) already validates JSON shape before the shared initializer, so this report does not claim the same path affects volunteer forms. Owner: django-reviewer; QA to reproduce ordinary data corruption handling, frontend to preserve/report serialization errors.

### BE-04 — P2: exported JSON cannot reconstruct a regular schedule

**Trigger:** export a weekly scheduled place and import its JSON into a fresh form/card.

**Evidence:** `PlaceAdmin.export_place_json_view`, `src/catalog/domain_admin/place.py:3967–4004`, exports schedule_mode and localized notes but neither structured days nor legacy schedule text. Importer accepts `schedule_days`/`structured_schedule` at `static/admin/js/kidsmap_place_json_import.js:490`; `setStructuredSchedule` at `:80–94` skips absent values. Thus the export carries the mode but none of the actual opening hours. Existing target imports leave target hours untouched; this is not evidence that export/import always erases an existing schedule.

**Impact:** a fresh imported regular place cannot recover the source opening hours or satisfy canonical schedule readiness without re-entry. Legacy scalar-only/JSON price information is also absent because export serializes only relational rows at `:4000`; scalar omission is explicitly expected by `testcases/pricing_plans_relational.py:188`, so changing that policy requires an explicit compatibility decision, rather than treating every omitted field as a bug.

**Verification:** source-only. `testcases/test_json_roundtrip_audit.py:188` calls fixture creation → tariff replacement → readiness/SEO, not the actual export/import/save cycle. Needed genuine exported payload → importer → fresh saved Place assertion for each weekday/interval and all schedule modes. Owner: django-reviewer with frontend importer owner; database-reviewer for legacy price transport semantics.

## 4. Tech debt

Duplicate owner/canonical publication validation creates observable disagreement (BE-02); misleading module docstring claims rules are shared with admin. Shared schedule parsing mixes display fallback and persistence validation (BE-03). Public properties, readiness and projection updates operate on both instance and DB state; explicit refresh in tests matters after signals update scalars via queryset.

## 5. Risks

Current affected production row counts, deployment revision and applied migrations are UNKNOWN. Historical scalar-only row counts were not reused. No concurrency or storage-failure experiments were run. Pricing replacement is atomic internally, but this does not establish atomicity of every external caller or migration. No exhaustive audit of public filtering, events, reviews, ownership, volunteer lifecycle, security or migration mechanics is claimed under final bounded scope.

## 6. Dead/legacy candidates

No confirmed deletion candidates. Scalar prices, legacy JSON and textual schedule have actual fallback consumers and migration obligations. Compatibility wrappers and the separate Event model are not dead-code findings. `permanent_place_rules` is active despite its misleading shared-contract docstring; consolidate only after a reviewed parity plan.

## 7. Tests gaps

**Executed by this specialist:** read-only `git rev-parse HEAD`; `git diff --name-only -- src/catalog static/admin/js/kidsmap_place_json_import.js` (empty); targeted `rg`/`sed` source reads; projected graph coverage/search/trace. These establish source/snapshot, not runtime correctness.

**NOT RUN here:** Django tests, custom reproductions, browser, production/DB checks, external calls. No settings import or fixture writes. QA was asked to run existing labels `catalog.testcases.pricing_plans_relational`, `catalog.testcases.test_json_roundtrip_audit`, `catalog.testcases.test_place_json_and_pricing_modes`, `catalog.testcases.place_readiness`; see its report for actual command, isolation, results and limitations. Availability of `/tmp/kidsmap-audit-20260908-qa/run.py` alone is not a passing result.

**Attributed fresh QA result:** `/root/audit_qa` reported, and this specialist read [qa.md](qa.md), section 1: eight selected labels ran 375 tests in 66.364s, exit 1, 12 failure records across 11 methods, all in `catalog.testcases.public`. No failure records in selected pricing/readiness/legacy/round-trip modules. Exact command and environment are retained there: disposable SQLite memory DB, DJANGO_TESTING=1, cleared inherited environment, LocMem cache/email, scratch media and blocked external sockets. This does not reproduce BE-01–04 or prove PostgreSQL parity. QA is preparing a lead-authorized benign scalar-preservation probe; its result is pending at this specialist's handoff and must be linked by the lead when available.

Missing focused coverage: admin scalar-only ordinary edit preservation; owner/admin new-submission parity; malformed schedule draft preservation; actual schedule export/import/save. Existing owner scalar-preservation test and volunteer malformed-schedule test are useful but cover different paths. Existing successful suite results, if QA obtains them, cannot disprove these untested paths.

## 8. Recommendations

1. QA reproduces BE-01 in a disposable fixture; database-reviewer estimates applicable legacy shapes using authorized read-only evidence. Then propose scoped admin-preservation work that retains deliberate tariff deletion semantics.
2. Agree and test one new-submission contract for owner/admin; keep draft persistence and ordinary existing-live compatibility explicit.
3. Separate invalid schedule input from intentional empty content; require preserved DB hours on rejected draft input.
4. Define a round-trip schema for schedule and legacy price transport, then exercise the real export/import/save path.

All are recommendations only. Application implementation requires a concrete approved scope; this report grants none.

## 9. P0/P1/P2/P3

| Priority | Findings | Evidence boundary |
|---|---|---|
| P0 | None confirmed | No current production incident evidence |
| P1 | BE-01 | High-confidence LOCAL source chain; exact runtime reproduction outstanding |
| P2 | BE-02, BE-03, BE-04 | Current LOCAL validation/round-trip defects; runtime/production not asserted |
| P3 | Duplicate-rule documentation and test naming debt | Included in sections 4/7, not inflated into extra incident IDs |

Handoff: QA → targeted fixture evidence; database-reviewer → scalar legacy/projection impact; frontend reviewer → importer/owner completeness messaging; lead → deduplicate and set final priority in MASTER_AUDIT. Changed only this assigned report.
