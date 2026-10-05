# Specialist screens — Stage25 Design Checkpoint Plan

**Goal:** create a concrete, reviewable specialist-25-r1 prototype within stage25; application integration starts only after user acceptance.

**Architecture:** standalone HTML/CSS/vanilla-JS screens under design/specialist reuse the accepted owner/public brand tokens and local logo/fonts. All people, documents and organizations are synthetic; interactions demonstrate stage24 state transitions without API, DB, real uploads or messages. Existing application source remains preserved.

**Tech Stack:** semantic HTML, responsive CSS, local assets, vanilla JavaScript, loopback static HTTP server and real Playwright Chromium.

**Spec:** docs/task33/prompts/25.md; decisions.md D08; architecture.md Specialists/Screens; reports/24.md. Lead frontend-reviewer. Full stage25 is REVIEW_PENDING until both accepted designs and subsequent implementation/checks exist.

## Constraints

- Only stage25 design checkpoint is currently executable. No26+, production, commit/push/merge/deployment.
- Dependency24 DONE; owner-02-r1 and admin-public-03-r1 accepted; additional Specialist screens not yet accepted.
- Person ownership is separate from business grants; explicit two-party confirmations and history remain visible. Private identity never becomes a public certificate.
- Public qualifications require specialist choice and KidsMap approval. Dedicated reviewer access is separate from ordinary staff/organization grants.
- Preserve private independent offices, online practice and old profile URLs by explicit identifiers; do not infer identity/consent from names or Place FK.
- AZ/RU/EN;320/360/390/768/1024/1280/1440; focus, error states, no horizontal overflow and console/static failures verified in actual browser.
- No external assets or integrations. Design simulation is not backend/ACL/transfer evidence.

## Deliverables and responsibilities

- [x] Preserve192 incoming dirty/untracked files and tracked binary diff,25-entry-manifest.json; branch task33-progress,HEAD015d031d.
- [x] Read prompt/checkpoints/canonical roles; active_run stage25 design-only. Root Codebase Memory transport closed; scoped source fallback. Browser executor obtained ready generation2026-10-03T14:52:17Z, but new design/qa25 coverage unavailable/not_tracked; no full graph-coverage claim.
- [x] Frontend prototype executor owns only docs/task33/design/specialist/: index, public profile, person editor, organization invitations, person claim, private certificates, dedicated review, fixture reconciliation; reusable local CSS/copy/JS and screen README.
- [x] Root reviews states against stage24 symbols and records design-only coverage; application/backend/migration files are not edited.
- [x] Separate browser-qa executor owns qa25 harness and reports/25-browser-review.md; renders all screen/language/width combinations, checks keyboard/forms/negative design visibility and captures fresh PNG evidence.
- [x] Root views selected screenshots, fixes prototype findings through assigned executor, validates hashes/entry preservation/no app delta and checks local links.
- [x] Update25.md,25-design-manifest.json, design/acceptance.md and implementation-status.md to CREATED/REVIEW_PENDING; active_run NONE at handoff. Present concrete reviewable mockups and explain the exact prompt checkpoint requiring acceptance.

## Design scenarios

1. Public profile: specialties/age/language/online/current practice, approved opted-in qualification; past cooperation separated, no private IDs/evidence.
2. Person editor: biography/contacts/publication, independent office and online format with retained past locations; saved/error/conflict and ordinary-business denial states.
3. Organization: propose/invite specialist, explicit role/start/end, one-sided consent vs two-sided confirmation, cancel/withdraw retains history; no person/doc editors.
4. Claim: existing stable profile, author is not owner, submit/pending/rejected/withdrawn/KidsMap-approved/conflict states; no automatic identity inference.
5. Documents: private upload, identity always private, qualification opt-in and moderation independently visible; pending/rejected/approved/revoked, private access provenance.
6. Dedicated review: person claim and document decisions, publication choice cannot be set by reviewer; identity not public, ordinary-staff denial.
7. Reconciliation: synthetic IDs/old URL retained, legacy owner/location association ambiguous manual review, no name guesses or double confirmation; counts/checkpoint, no actual DB transfer.

## Acceptance gate

Prototype creation does not finish25. Prompt25 explicitly requires showing new designs to the user, recording REVIEW_PENDING and beginning Specialist screen integration after acceptance. No repeated approval of owner/admin-public designs is needed. Remaining application nested-ID/role/URL/isolated transfer checks are NOT RUN during design-only work.
