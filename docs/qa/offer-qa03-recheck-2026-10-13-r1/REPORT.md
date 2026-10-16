# OFFER-QA-03 — fresh LOCAL recheck / PLAN

2026-10-13. Executor /root, sequential, canonical kidsmap-orchestrator; no independent specialists claimed. Application implementation NOT RUN; finding OPEN/P2.

Checkout `/home/ramin/kidsmap`; HEAD `e4e05cc213b34e2d771ecb854901bfd016d1db51`, branch `task33-progress`, dirty incoming WORKTREE captured in entry.json. `active_run: NONE`, unchanged. All incoming nonignored files preserved byte-for-byte (verification.json), no application changes, commit/push/deploy/production.

## Evidence / state

Fresh own reused QA profile offer-qa02-fix-2026-10-13-r1: PID348816, HTTP127.0.0.1:34529, PostgreSQL17.10 own DB offerqa02fix_20261013_r1 loopback60693. /proc cmdline verified exact own runtime path, GET /qa/start-version/ confirms entry=startup=disk source, DJANGO_TESTING=1, .env not loaded, LocMem cache/email and sole isolated locale path. Source receipt in runtime-receipt.json. Existing profile's current RU/AZ/EN manifest verified before django.setup by each script; no new compilation claimed, no common MO changed. Own browser session offerqa03recheck-20261013-r1; outside requests BLOCKED, integrations SIMULATED/NOT RUN.

Created new fictional prerequisites via own runtime: 2activities/4groups/8plans; previous accepted fixtures not modified. Native owner login and edit, second activity/group/plan price0, close all details, actual save, click actual error summary. No ORM substitution for user transitions.

Two native passes ×RU/AZ/EN at390px =6focus assertions,6expected FAIL,0harness exceptions/pageerrors. Endpoint422 and entered0 preserved all cases. Link focuses SELECT program_id in activity0; actual erroneous price belongs to activity1/group1/plan1. Raw response contains only localized flat error strings, no machine target. First pass full-page PNGs, second viewport PNGs;6PNG SHA/bytes in png-manifest.json. Viewport RU focus image visually inspected. Browser native CLI exits0 mean harness ran; they do NOT mean defect PASS.

`browser.result.json`, `focus-viewport.result.json`, `commands.jsonl` retain results/exits. Fixture and READ ONLY readback commands recorded with exact argv, both exit0. Readback uses statement_timeout10s/lock_timeout2s: all8live prices20,2activities/4groups, zero revisions. Rejected saves did not publish or create candidate revisions. Own server drafts/cache may hold fictional edit state as designed.

## Root cause / impact

normalize_pricing_plans collapses PricingPlan.error_dict into a translated tariff message; validate_nested_pricing supplies no activity/group path. OwnerPlaceEditForm retains this exception, photo_views turns it into strings; permanent_place_photos transports strings; fieldTarget attempts to find activities/groups/price in text and falls back to first program selector. Even EN text has only “field price”, not the machine path expected by frontend. goTo successfully opens ancestors of the wrong target.

P2: on long collapsed forms, summary cannot take user to offending field. Canonical price rejection and input retention work. Confidence HIGH for this trigger; production and broader matrix NOT RUN.

## Impact / recommendation

Inspected source chain services/pricing_plans.py → forms.py → photo_views.py → permanent_place_photos.js → owner_place_continuous.js. Codebase Memory graph/coverage checked (best effort, metadata_match) and conclusions verified directly in source. Shared normalize consumers include admin, volunteer forms, publication, direct/relational pricing and legacy migration; retain messages/signatures and add metadata only. No deletions/dead code cleanup, model/schema changes or business rule changes proposed.

Concrete plan: ../../superpowers/plans/2026-10-13-offer-qa03-structured-error-focus.md. Four existing application files plus one new meaningful regression test module. forms.py inspected, unchanged unless separately approved extension proves necessary. Scope approval pending. Targeted backend and native matrix only after approval; full ACCEPT-05 at module end. No extra finding closed.

## NOT RUN / handoff

Application patch, new backend regression suite, full responsive/age/billing matrix, shared admin acceptance, full module05, global suite, production, external maps/integrations, physical devices/screenreader NOT RUN. OFFER-QA-01/02 scoped CLOSED LOCAL remain historical accepted evidence; OFFER-QA-03 stays OPEN until actual implementation/acceptance. OFFER-QA-04–09 untouched. Next: approve exact OFFER-QA-03 plan, then implement only its five application/test files with unique own runtime and fresh locale build.
