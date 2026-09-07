# Multiple place reviews with cooldown

**Goal:** Preserve separate place reviews from one signed-in user, with a server-enforced 120-second interval and visible countdown. Verify admin publish/reject/hide/delete and rating sync.
**Authorization:** User explicitly requested multiple reviews and a timer; accepted a couple of minutes. Scope is reviews of the same place. Site/specialist review uniqueness and manual moderation remain unchanged.
**Architecture:** Remove place+user uniqueness, keep a separate unique place+user submission gate with next_allowed_at (survives review deletion). Atomically claim the gate before creating a pending review. Countdown consumes server timestamps on both GET and AJAX; HTTP 429/Retry-After enforces early retry.
**Constraints:** No production changes, no review deletion/rewrites, preserve adjacent volunteer/header work. Inspect pending local migrations before applying. No commits/push.

- [x] Write failing tests for cooldown, separate history, other places/users, 120-second boundary, deletion persistence, failed validation, rollback, admin permissions/deletion/rating sync.
- [x] Add PlaceReviewCooldown model/service and migration removing only place-review uniqueness; retain existing reviews. Integrate result metadata with GET and AJAX/POST.
- [x] Add localized shared-style countdown to the review section, preserve submission confirmation, restore composer when timer ends; retain input on blocked requests.
- [x] Adapt old tests from place-review replacement to multiple-review semantics, retaining site/specialist expectations. Run targeted tests and actual browser timer checks.
- [x] Verify admin moderation/delete on isolated fixtures. Check migration path and safely enable local preview. Report exact remaining limitations.

Result: docs/REVIEW_COOLDOWN_2026-09-07.md. 54 Django tests, browser timer/concurrency and actual admin flows passed. Local schema and 120-second runtime verified.
