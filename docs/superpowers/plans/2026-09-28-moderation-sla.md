# Moderation SLA Implementation Plan

**Goal:** Show users a truthful moderation deadline and give staff one queue ranked by SLA risk for places and reviews.

**Approved policy:** Place 72 calendar hours; review 24 calendar hours; warning at 50%, critical at 80%, breach at 100%; pause while changes are requested; restart on resubmission.

**Scope:** `Place`, `PlaceReview`, `SiteReview` and `SpecialistReview`; no external notifications in this release.

1. Add failing unit tests for SLA state calculation, paused work and due-ordering, then implement the shared service using Django settings.
2. Add moderation timestamps and assignee fields through a reversible migration; set them on submission and resolution paths.
3. Add a staff-only unified queue with filters, age/deadline columns, risk badges and oldest-first order.
4. Add owner/reviewer status copy in AZ/RU/EN and a `Needs changes` return flow for places.
5. Run focused unit, admin and browser checks on isolated fixtures; do not deploy without separate release approval.
