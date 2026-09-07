# Volunteer admin form implementation plan

**Goal:** Replace the volunteer owner-style wizard with the existing admin visual structure and a useful instruction, preserving the proposal service and object permissions.
**Architecture:** Reuse admin CSS, section/nav/field and language components; existing tariff/schedule/map widgets. A small presentation adapter groups restricted VolunteerPlaceForm fields into five admin sections. No ordinary ModelAdmin save endpoint, publication controls, global duplicate lookup or owner API.
**Scope:** User screenshot/request, local only; no account/role changes, deployment or commit.

- [x] Update the UI contract test for five admin sections, accessible instruction, exactly one copy of each allowed field and no privileged actions; run red.
- [x] Add presentation context, admin shell/instruction, scoped interaction adapter and CSS. Preserve multipart draft/submit, revision tokens, conflict/review feedback and canonical backend readiness.
- [x] Run volunteer/security/owner regression tests; real browser create/draft/submit, language tabs, instruction keyboard close, readiness links and responsive views. Restart existing local preview with its saved DB.
