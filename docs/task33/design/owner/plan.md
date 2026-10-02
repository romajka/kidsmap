# Owner prototypes — stage 02 implementation plan

**Goal:** Reviewable local HTML mockups for Place creation and Organization workspace, within prompts/02.md.
**Architecture:** Standalone HTML shells, shared vanilla JS, local CSS snapshot of KidsMap tokens and existing brand/font assets. No application imports, API calls, storage, DB or backend changes. Fixtures are synthetic; all save/upload/invitation results are demonstrations.
**Spec:** docs/task33/prompts/02.md; decisions D01–D05/D10; architecture sections Screens, Revisions/drafts, Permissions.

## Boundaries

Only docs/task33/design/owner and stage documentation. No commit/push/deploy. Owner review does not imply user acceptance. AZ required content; RU/EN translations optional. Four continuous Place sections; standalone Park without invented activity. Organization may have zero branches and no address.

## Work and evidence

- [x] Create index.html explanation/review directory plus place.html, organization.html, cabinet.html, program.html, groups.html, team.html. Shared prototype.css, copy.js, prototype.js. Reuse existing logo, local Chiron and Material Symbols, site.css token values.
- [x] Demonstrate empty/draft/saving/save-failed/browser-only/pending/rejected/conflict/published+pending; retain typed values on failure/conflict; show inherited/local contact source and optional translations.
- [x] Demonstrate branch list, approved Program impact with retained local prices/groups, group ages/text schedule/language/teacher, employee presets/actions and selected_places vs all_network including future branches.
- [x] Open real Chromium locally; verify AZ/RU/EN × 320/360/390/768/1024/1280/1440, long strings, overflow, labels, focus, section navigation, validation/retry/conflict, CTA and console/network. Store reproducible verify.cjs and aggregate verification.json; screenshots at 390/1280.
- [x] Obtain bounded independent review under canonical browser-qa; reviewer owns only reports/02-review.md. Lead owns prototypes, acceptance, report and status. Fix findings within prototype scope and rerun affected checks.
- [x] Record source HEAD, original dirty package, before/after preservation checks and source-artifact sha256 in reports/02-manifest.json; update reports/02.md and status; clear active_run. Mark acceptance awaiting_user_review; user approval remains pending.

Execution is already authorized by the current stage instruction; no additional execution-choice prompt. Low-impact prototype interactions use rendered acceptance checks, not application unit tests. No automatic commit.
