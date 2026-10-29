# Place identity and duplicate registry implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Let staff and research agents compare stored and candidate place identities, see the scope of duplicate checks, and prevent a second confirmed place creation.

**Architecture:** A read-only identity service extracts a strict allowlist from stored Place, authorized active revisions and actor-private drafts. Admin comparison, paginated matching, full JSON inventory and create-time validation use this service. A PostgreSQL advisory transaction lock serializes guarded creation; no schema/data migration or automatic merging.

**Tech Stack:** Existing Django/PostgreSQL, Django admin templates, existing vanilla JS and CSS, unittest and Chromium.

**Spec:** This document's Approved behavior section implements the proposal accepted by the user on 2026-10-29.

## Approved behavior and constraints

- Keep normal editing export backward compatible. Add dedicated comparison and duplicate registry JSON.
- Preserve stored and working identities separately: names AZ/RU/EN, address, coordinates, public contacts, source, status and versions. Never include owner details, notes, tokens, pricing/media payloads or unrelated metadata.
- Actor-private drafts are visible only to their actor and only while target access remains valid. Recheck active actor and object permissions; no hidden record counts.
- Compare signals within each version; do not stitch different versions into a stronger match. Same venue requires more than a shared network phone/site. Separate branches retain their own identities.
- Return exact accessible-record coverage, timestamp, pagination and match evidence. No result means not found within this access, never globally absent.
- Recheck identity before storage/model writes at shared admin/owner create and volunteer create. Exclude the active private draft being materialized. Confirmed and unresolved strong likely duplicates produce actionable validation errors; weak shared network signals do not prohibit a distinct branch.
- Preserve existing volunteer same-creator name/branch contract while routing identity extraction/matching through the shared service.
- Creation races must serialize. Do not silently publish, merge, rewrite or remove records.
- Preserve the 16 pre-existing dirty/untracked public UI paths. Use a cleared-environment `DJANGO_TESTING=1` profile with separate database/cache/media/email and disabled external keys.
- User approved implementation and prior Git/server release authorization continues. Run inline; no additional agents or repeated approval gate.

## Task 1: Identity service and duplicate policy

**Files:** create `src/catalog/services/place_identity.py`; preserve normalizers used by public guides in `place_duplicates.py`; create `src/catalog/testcases/test_place_identity.py`.

**Interfaces:** `identity_registry(actor, can_view=None, can_edit=None, exclude_draft_id=None)` returns `{schema_version, generated_at, coverage, records}`. Each record contains versions with separate identity fields. `check_duplicates(actor, values, exclude_place_id=None, exclude_draft_id=None, registry=None)` adds evidence and classifications; `guard_new_place(...)` raises ValidationError under the create transaction lock.

- [x] Write regressions for stored/candidate identities, explicit clears, multilingual/transliterated names, all contacts, same-venue strong matches, branch ambiguity, no cross-version signal stitching, private draft scope, revoked actor/object access, metadata non-disclosure and coverage.
- [x] Run `.../run.py test catalog.testcases.test_place_identity --keepdb --noinput`; verify failures from missing service/behavior.
- [x] Implement allowlist extraction and access policy; records are one Place with multiple separately labelled versions, plus accessible actor-private drafts.
- [x] Implement signal matching and explicit result confidence, with date/access scope. Test matches remain correctly attributed to their version.
- [x] Implement serialized guard before any files or base Place are written; same-actor legacy matching must use the same source versions.
- [x] Run identity tests green, then existing duplicate and volunteer tests affected by this contract.

## Task 2: Read-only admin comparison, export and matching

**Files:** create `src/catalog/domain_admin/place_identity.py`, `src/catalog/templates/admin/catalog/place/identity_registry.html`, `src/catalog/templates/admin/catalog/place/identity_compare.html`, `static/admin/css/pages/place_identity.css`; edit route/context wiring only in `src/catalog/domain_admin/place.py`, list/form templates; add `test_place_identity_admin.py`.

**Interfaces:** staff admin routes `duplicate-registry/` (HTML or JSON), `<id>/compare-versions/` (HTML or JSON). Matching endpoint retains `results` compatibility and adds `total`, pagination, coverage and per-version evidence. All endpoints are GET/read-only and `never_cache`.

- [x] Write tests for export containing both versions without mutation, no personal metadata, role boundaries, matching beyond eight results, stable full export, invalid pagination, malformed payload isolation and form/list links.
- [x] Verify tests fail before implementation.
- [x] Add authenticated routes with object-level permission callbacks and safe `Content-Disposition`. Registry JSON includes completeness/access limits; comparison labels approved/base and saved candidate honestly.
- [x] Render mobile-safe version tables and next/edit links using existing admin styles; values escaped. Add dedicated registry/export links and per-card compare links.
- [x] Run tests, retain ordinary export/import contract, and verify JSON cannot accidentally be imported as an editing snapshot.

## Task 3: Editor hints, create validation and workflow copy

**Files:** edit `static/admin/js/kidsmap_place_duplicates.js`, relevant admin form clean/save conflict recovery, `publication_forms.py`, `volunteer_places.py`, `server_drafts.py` only for draft exclusion, JSON research prompt copy. Add focused JS/create regression tests.

- [x] Write failing tests for input names/secondary phones, coverage shown when no matches or failed network, stale response protection, matching-source display and pagination link.
- [x] Update hints from the server; failed/partial checks must say so and never display absence as certainty. Use locale-provided strings and textContent.
- [x] Wire server guard into shared create paths, preserve form submissions on duplicate validation, and return actionable existing record references only within permissions.
- [x] Add race regression: two attempts for the same full identity cannot create two Places, while a distinct confirmed branch can be saved. Verify actor-private materialization excludes itself and remains idempotent.
- [x] Update research prompt to use timestamped registry with both versions and preserve per-candidate blockers while continuing independent research. Do not claim execution of the external agent's 24-candidate task.

## Task 4: Verification and narrow release

- [x] Run all changed-module Django tests once, relevant existing regressions, and focused JS tests. Record commands, counts and isolated environment.
- [x] Browser: registry and compare AZ/RU/EN at 390/768/1024/1280/1440; check photos/status list unaffected, table scrolling, keyboard links, JSON downloads and create duplicate validation with synthetic data. Console/network must be clean.
- [ ] Verify the foreign-file hashes, stage only this scope, commit and push without bundling dirty public UI.
- [ ] Read current server revision/image/overrides, preserve rollback, build from exact Git archive, run Django/schema checks and production READ ONLY comparison/registry checks before activation. No dump/records copied locally or into Git.
- [ ] Activate with recoverable previous image, collect static without clearing old hashed files, verify active source hashes/HTTP assets/health/GET endpoints, then fast-forward a clean server checkout.
- [ ] Save concise implementation/release evidence and disclose limits; do not claim a production browser login or independent candidate investigation that was not performed.
