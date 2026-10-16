# OFFER-QA-01 — fresh scoped recheck / PLAN

2026-10-13. Lead kidsmap-orchestrator, root sequential execution, no independent agents. AUDIT/PLAN ONLY; source implementation not authorized yet. Finding remains OPEN, P2, LOCAL.

## Snapshot and authorization

Checkout `/home/ramin/kidsmap`, HEAD `e4e05cc213b34e2d771ecb854901bfd016d1db51`, branch `task33-progress`, pre-existing dirty WORKTREE preserved, active_run NONE. [Entry](entry.json), [verification](verification.json), [application source hashes](entry-final.json). User requested module05 in order; scope is only PLAN OFFER-QA-01, not OFFER-QA-02–08.

## Evidence and cause

One actual Django/PostgreSQL service-level probe with fictional data executed propose→review approval. Two published groups cost20/80; candidate omits80 group. Before approval, live group remains as expected. After approval revision is approved, omitted group remains unarchived and its tariff remains in public pricing queryset, public max80. [State](probe-state.json), [native RED](deletion-publication-red.txt), [exact argv/exit](deletion-publication-red.command.json), [probe](probe.py).

`services/pricing_plans.py:replace_nested_pricing` writes received rows only, has no omitted activity/group reconciliation. `publication.py:_apply` delegates approved complete nested tree to it. `static/js/owner_place_offerings.js` remove_group correctly splices group from submitted tree. Existing canonical `ArchivedEntity.archive()` preserves records/increments content_version and updates price projections; public pricing already excludes archived group/activity. The proposed repair reuses those semantics, not UI hiding or hard deletion.

Graph project home-ramin-kidsmap matches actual root; status ready. Exact coverage for pricing_plans.py, publication.py, owner_place_offerings.js reports metadata_match/no_recorded_issue, best-effort only. Trace lists9 inbound callers (publication and tests); critical conclusions checked directly in current source. No claim of graph completeness.

## Isolation / runtime

Own fresh loopback PostgreSQL container/volume/DB/profile in verification.json. Own cache/media/private-media/email, credentials only ignored `.tmp` files0600. Runtime removes inherited environment, sets DJANGO_TESTING=1 before setup, bypasses manage.py/.env, blocks socket egress except own PG, verifies current RU/AZ/EN manifest before setup and uses sole LOCALE_PATHS. [Locale manifest](locale-manifest.json). Existing packages reused read-only; no production data/credentials copied. Own disposable test DB created/migrated/dropped. No HTTP server/browser started: process under test is command argv runtime.py/probe.py loading current checkout; source hashes preserved.

## Results and limits

Setup/build/manifest verification/Django check native0. Probe native1:1 executed/1 expected behavioral failure,0 errors. This is fresh local confirmation of the backend cause; regression relative to another SHA or production UNKNOWN. Native owner/moderator/public browser transitions/screenshots NOT RUN here; they remain mandatory repair acceptance. Full module05/global corpus NOT RUN, externals blocked, production/commit/push/deploy NOT RUN. No application change or finding closure. No foreign process/container control actions; prior source/docs/shared MO and active_run unchanged by hash comparison.

## Reviewable plan / handoff

[Concrete implementation plan](../../superpowers/plans/2026-10-13-offer-qa01-approved-group-removal.md). Only2 existing application files and1 new focused regression file. Explicit complete_tree flag with safe partial default; approved full nested tree archives omitted groups/activities and refreshes price projection. Partial imports/default calls do not infer removals. Preserve candidate/live, ACL/CAS, historical rows and existing assertions. Native UI and exact targeted tests follow approval. No repeat full unrelated suites; final module acceptance after all selected repairs. Risk: replacement vs partial caller semantics and empty-tree scalar prices; named tests and explicit caller flag cover them.

Needs next: user approval of this concrete plan, then sequential backend implementation and native browser verification. OFFER-QA-02–08 not started.
