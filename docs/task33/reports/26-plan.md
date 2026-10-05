# Event Domain Implementation Plan

**Goal:** implement only Task33 stage26 Event organizer, immutable venue, occurrence history and shared period query contracts.

**Architecture:** extend the existing Event rather than create a second event catalog. Publication status and occurrence state are independent; all new owner mutations use fresh organizer rights, version checks and PostgreSQL transactions. Preserve unresolved legacy identity explicitly; never infer organizer/address from names or today's Place.

**Tech Stack:** existing Django6/PostgreSQL17, aware Asia/Baku dates, server-rendered templates and gettext. No new framework.

**Spec:** ../prompts/26.md; decisionsD07/D09 and architecture Events/Rights/Reviews. User directly authorized only26; no commit/push/production/27+.

## Constraints and ownership

Entry265 dirty/untracked files and binary patch preserved in26-entry-manifest.json; dependency25 source136SHA MATCH, active_run was NONE. Root django-reviewer owns lead and services/event_domain.py, OwnerEventForm/owner_events_controller, owner-event view symbols/admin integration, QA26 launcher and final docs. stage26_domain database-reviewer owns Event fields/validation/event_domain model/migration0133/schema tests and26-domain.md. stage26_public django-reviewer owns shared query/controller list delegate/event_detail/SEO/public tests and26-public.md. Later separate independent security and browser reviewers own only their tests/harness/reports; implementation executor evidence is not independent.

## Task1 — schema and preservation

- [x] Write test_task33_event_schema.py then execute isolated RED before implementation. Examples: both organizer FK values fail; resolved+neither fails; online+Place/coords raw update fails; naive interval rejected; ended Event date rewrite rejected; publication snapshot survives Place move.
- [x] Add organizer_organization/organizer_specialist, organizer_resolution resolved|legacy_unresolved, event_format physical|online, occurrence_state scheduled|cancelled|rescheduled, venue_label and venue_snapshot JSON. Conditional XOR: resolved exactlyone, explicit legacy_unresolved bothnull. New owner/service paths always resolved; marker is not writable in forms. Legacy default retained only for old low-level compatibility, never an inferred organizer.
- [x] Add EventOccurrenceChange(kind,before,after,actor,reason,version,happened_at); append-only records. On initial approved save capture snapshot; later snapshot immutable except explicit future-reschedule service transaction. Past dates cannot be replaced with future under sameID.
- [x] Migration0132→0133 preserves IDs/links/content/reviews: snapshot only Event's own address/district/metro/coords; old Place label unknown. Old expired/cancelled becomes published only if published_at proves approval; otherwise draft. Rerun reconciliation and PostgreSQL constraints checked on synthetic fixture.

## Task2 — organizer mutations and forms

- [x] Write root test_task33_event_domain.py; execute RED. Example: venueowner cannot mutate foreign event even if Event.owner stale; Org transfer revokes priorowner; unverified Specialist cannot organize; a current person account can organize online without Place.
- [x] Implement services/event_domain.py interfaces: capture_venue_snapshot(event)->dict; can_manage_event(actor,event)->bool; create_event(actor,values)->Event; save_event(actor,event_id,values,expected_updated_at)->Event; submit_event(actor,event_id,expected_updated_at)->Event; publish_event(actor,event_id,expected_updated_at)->Event; cancel_event(actor,event_id,expected_updated_at,reason)->Event; reschedule_event(actor,event_id,start_datetime,end_datetime,expected_updated_at,reason)->Event. Mutation locks fresh actor→organizer→Event→venue; version and organizer must remain unchanged. History stores actual before/after periods, snapshot and occurrence, not a computed approximation.
- [x] Connect existing owner controllers/forms to these services, add organizer/format controls using existing accepted styles, explicit Baku date combine. Published/ended editing remains protected. Admin publish uses same readiness/snapshot; unpublish returns to draft, not cancellation. Platform review never grants venue owner Event rights.

## Task3 — query/detail/reviews/schema

- [x] Write query/public tests then isolated RED: hand-derived Baku midnight, multi-day [start,end) overlap, month unpaginated, list pagination separate; past/cancelled approved200, private draft/rejected/deleted404, archive district from snapshot.
- [x] Implement EventPeriod(start,end), parse_event_period(params,now=None,calendar=False), query_public_events(params,period=None,now=None,calendar=False). Strict date parser/local boundaries; month/day and inclusive input date_to map to nextday exclusive end, default upcoming. Existing q/category/age/format/district filters shared; calendar is backend contract only, UI remains27.
- [x] Connect typed EventReview current approved heads to visible detail/rating and matching Event JSON-LD. Pending candidate/foreign target does not contaminate rating; script unsafe markup escaped. Online schema uses virtual location, snapshot physical address/coords and actual organizer/state match page.

## Task4 — acceptance and handoff

- [x] Targeted GREEN and full Task33 regression in DJANGO_TESTING=1/disposable PostgreSQL/cache/media/email with external credentials absent and network guards; no production test credentials. Exact commands/exits/snapshot/migrations/cleanup recorded.
- [x] Independent security/DB negative review after frozen implementation. Real local Chromium AZ/RU/EN×320/360/390/768/1024/1280/1440 for affected owner/detail surfaces, focus/errors/console/network and page/schema parity. Browser artifacts synthetic and outside Git.
- [x] Review every prompt criterion, preserve incoming files, source SHA+dirty inventory without report self-hash, update26.md/results/status. Release own active_run only after executors complete; DONE only after fresh checks. Full application historical NOT_GREEN remains explicit, unrun integrations/prod/27+ remain NOT_RUN.
