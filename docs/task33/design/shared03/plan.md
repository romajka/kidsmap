# Admin/public stage 03 Implementation Plan

Goal: standalone reviewable admin/public prototypes, revision admin-public-03-r1.
Architecture: static synthetic HTML/vanilla JS; reuse owner-02-r1 tokens, local fonts and logo. No application writes, storage, API or external transport.
Spec: ../../prompts/03.md; ../../decisions.md D01–D10; ../../architecture.md Screens/Search/Events.

- [x] Preserve baseline and acquire stage lock; inspect actual source/roles/contracts.
- [x] Admin: organization, standalone place, local groups, review current/proposed (volunteer/conflict/new/program), transfer with team consequences.
- [x] Public: concrete-place catalog/map, organization without aggregate rating, place/activity local terms, list/month/day calendar and event state detail.
- [x] Render AZ/RU/EN × 320/360/390/768/1024/1280/1440; default/long/missing data variants, real screenshots; DOM/console/overflow/focus/flows.
- [x] Independent canonical browser-qa review; fix findings and rerun affected evidence.
- [x] Acceptance remains awaiting_user_review; report exact evidence, hashes, preserved baseline, NOT_RUN; release active_run. No later stages/commit/deployment.

Files: admin/*.html, public/*.html, shared03/{prototype.css,prototype.js,verify.cjs,verification.json,plan.md}, respective READMEs/screenshots, design/acceptance.md, design/README.md, ../../reports/03*. Stage journals only.
