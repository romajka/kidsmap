# KidsMap Moderation SLA Product Contract

## Purpose

KidsMap tells a submitter when a Place or Review entered moderation and when a decision is expected. Staff receive one deadline-aware queue covering every supported submission path.

The SLA is a maximum time to a moderation decision. It is never a promise that content will be published.

## First release scope

The Place SLA applies to:

- an owner or manager submitting a Place;
- staff moving a Place into moderation;
- a volunteer submitting a `VolunteerPlaceRevision`.

The Review SLA applies to:

- `PlaceReview`;
- `SiteReview`;
- `SpecialistReview`.

Event moderation, Specialist profile moderation and Organization change moderation use the same technical contract only after separate policies for those content types are approved.

## User-visible lifecycle

`Draft → Submitted / On moderation → Approved | Rejected | Needs changes`

- Draft time is outside the SLA.
- A successful transition into moderation starts the clock.
- Repeated submission of an already-open item must not start another clock.
- Approval and rejection close the clock.
- “Needs changes” behavior is controlled by the approved policy: either pause and resume the same attempt, or close the attempt and start a new one after resubmission.
- Review types without an edit-and-resubmit flow expose Approved or Rejected only.

User copy must say that KidsMap will review the material within the configured period. It must not say that publication will occur within that period.

## Required policy decisions

No SLA policy may be activated until an authorized product owner records all of these values:

1. Maximum Place decision time.
2. Maximum Review decision time.
3. Clock start rule.
4. “Needs changes” clock behavior.
5. Warning and critical elapsed-time thresholds.
6. Breach rule.
7. Calendar-time or business-time clock.
8. Public rejection/change-reason catalogue.

The first technical release implements a calendar-time clock. If the approved decision requires business hours, the implementation plan must be extended with a work-calendar model, timezone rules and holiday tests before any SLA policy is activated.

Backlog notification thresholds are optional. If absent, the queue shows counts without claiming that a backlog threshold was crossed.

## SLA state contract

The system derives state from the policy snapshot stored on a moderation case:

- `healthy`: before the warning threshold;
- `warning`: warning threshold reached;
- `critical`: critical threshold reached but deadline not passed;
- `breached`: current effective time is at or after the deadline while the case is unresolved;
- `waiting_user`: the policy paused the clock for requested changes;
- `unconfigured`: no approved policy was available when the case was opened;
- `resolved`: a moderation decision closed the case.

Warning and critical thresholds are percentages of the allowed effective time and must satisfy `0 < warning < critical < 100`. The exact percentages come from policy data, never application constants.

Color reinforces the state but does not carry meaning by itself. Every indicator includes a text label and exact or human-readable remaining/overdue time.

## Source of truth

- Domain models remain the source of content and publication status.
- `ModerationCase` is the source of SLA start, deadline, pause, assignment and outcome timing.
- `ModerationSlaPolicy` is versioned. Each case stores a snapshot so a later policy edit cannot silently move an existing deadline.
- `ModerationCaseTransition` is the immutable operational audit trail.
- `created_at` and general `updated_at` fields are not SLA clocks.

## Admin queue

The unified queue shows:

- content type and source;
- content title and safe preview;
- received time;
- elapsed effective time;
- remaining or overdue time;
- SLA state;
- current workflow status;
- assigned moderator;
- direct link to the existing moderation form.

The default open-queue ordering is deadline first and submitted time second. Received time and elapsed age remain sortable columns.

Filters cover content family, concrete content type, workflow status, submitted date, SLA state and assigned moderator.

Internal dashboard alerts show warning, critical, breached and configured backlog counts. Email and external notifications are outside the first release.

## Reasons and user privacy

Moderators select an approved structured reason for rejection or requested changes and may add a separate internal note. Users see only the localized public reason and links to applicable KidsMap rules. Internal notes, moderator identity and queue diagnostics are not exposed to submitters.

## Accessibility and localization

- User and admin output supports AZ, RU and EN.
- Time is displayed in the configured KidsMap timezone.
- Status is always text plus optional icon/color.
- Tables and controls remain keyboard accessible and usable at 375, 768, 1024 and 1440 CSS pixels.
- Live countdown animation is not required; server-rendered times are authoritative.

## Activation rule

Submissions continue to work when no policy is active, but the case is marked `unconfigured` and user copy omits a duration. Production SLA claims and alerts may be enabled only after the required policy decisions are approved and configured.
