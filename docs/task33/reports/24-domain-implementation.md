# Stage 24 — specialist domain implementation

Executor: `django-reviewer`, `/root/stage23_owner_admin` (the same executor that previously handled stage 23 owner/admin and browser checks; this is implementation evidence, not an independent review). Mode: APPROVED IMPLEMENT, stage 24 only. Date: 2026-10-03. Named handoff: `kidsmap-orchestrator` → independent `database-reviewer` / `security-reviewer` and final integration checks.

Snapshot: branch `task33-progress`, LOCAL HEAD `015d031d8eb17114bd860159dde805b38df3c13c`, dirty WORKTREE with preserved earlier-stage changes. Production was not accessed. Codebase Memory returned `Transport closed`; index freshness and coverage are UNKNOWN. Relevant source and dynamic Django relationships were checked with bounded source reads and `rg`.

## Implemented contract

- Person proposals record `created_by` and never establish person ownership. The owner form revalidates after binding the freshly locked profile; existing edits require the current verified person account. A new form instance cannot inject verified identity. New proposals containing documents fail before saving; claimed edits use the separate private-document upload service.
- Dedicated claim decisions require an active, non-volunteer staff account with `catalog.review_specialist_claim`. Approval binds the verified person account, keeps the legacy owner as decision history, and updates the compatibility owner projection. Claims have explicit withdrawal, version checks and immutable historical rows. A legacy manager alone is not proof of person identity.
- Employment proposals record organization/person participants, role and start/end dates. Neither proposal, organization invitation nor a practice-location link confirms either side. Person and organization each make an explicit versioned confirmation; even one account holding both roles needs two calls. Cancelled rows, confirmation history, practice locations and existing review identities remain present.
- Exact pending/active employment duplicates are refused, including open-ended periods and concurrent proposals. Distinct roles/periods remain allowed; cancellation permits a new proposal. Confirmation compares both participant IDs and the organization ownership epoch, preventing stale consent after ownership transfers away and back.
- Online mode deactivates practice locations without deleting historical primary rows. Returning to an unchanged location reactivates it. A changed location retires the previous row and creates a replacement instead of overwriting historical address/contact/price data.

Owned application files: `src/catalog/models/specialist_domain.py`, `src/catalog/services/specialist_domain.py`, `src/catalog/services/owner_specialist_use_cases.py`; dedicated tests: `src/catalog/testcases/test_task33_specialist_domain.py`. Root owns existing Specialist fields, model imports, migrations 0131/0132, account-deletion integration and private-document service. The root-added ownership epoch and duplicate constraint are included in runtime checks; no migration file was edited by this executor.

## Concurrency and authority boundary

Claim decisions lock relevant applicant/reviewer/legacy-manager User rows in sorted order before Specialist and claim rows. Employment operations lock the current participant/actor Users in sorted order before Organization → Specialist → employment. Current parents are re-read after locking; changed participants outside the locked set cause a retry conflict. No new User lock is acquired after parent locks. This aligns with account deletion and protects foreign-key writes from the opposite lock order.

PostgreSQL tests exercise two claimants for one person, one applicant for two persons, simultaneous side confirmations with fresh-version retry, duplicate open-ended employment proposals, and actual account finalization racing consent. Unexpected database exceptions propagate; tests do not treat deadlocks as acceptable conflicts.

## Executed evidence

Commands use the ignored local wrapper, an owned `/root/km24-domain` source-only mirror, the unchanged QA04 launcher, shared dependency virtualenv only, isolated PostgreSQL/cache/media, `DJANGO_TESTING=1`, clean environment and blocked external integrations. No environment files, application media, database files or credentials were copied. QA raw output is created under `/tmp` and immediately retained outside Git under `/root/task33-evidence` within the same WSL shell.

```text
wsl -d Ubuntu-24.04 -u root -- bash /mnt/c/kidsmap/scratch/task33-stage24/run-domain-qa.sh all <stamp> --label catalog.testcases.test_task33_specialist_domain
```

| Evidence stamp under `/root/task33-evidence` | Result | Purpose |
|---|---|---|
| `stage24-domain-red-20261003` | 20 tests, 4 failures, 15 errors, 0 skips | Existing auto-owner/authority/location-loss defects plus absent domain API. |
| `stage24-domain-green1-20261003` | 20/20 PASS, 0 skips; 165 applied migrations / 0 pending; checks and cleanup PASS | Initial person/claim/employment contracts and three concurrency scenarios. |
| `stage24-domain-red2-20261003` | 24 tests, 3 failures, 0 errors, 0 skips; checks and cleanup PASS | Forged new-instance identity, prevalidated form dropping edits, exact duplicate proposals. Distinct overlapping employment was already PASS. |
| `stage24-domain-aba-red-20261003` | 1 test, 1 failure, 0 errors; 166 applied / 0 pending; checks and cleanup PASS | Actual ownership transfers away and back incorrectly preserved pending consent. |
| `stage24-domain-green3-20261003` | **28/28 PASS**, 0 failures/errors/skips; 166 applied / 0 pending; checks and cleanup PASS | Final assigned domain source, all five PostgreSQL concurrency scenarios, epoch guard and strengthened form/duplicate cases. |

The ABA RED command selected `catalog.testcases.test_task33_specialist_domain.SpecialistDomainTests.test_organization_handover_away_and_back_invalidates_pending_consent`. Assertions were not weakened to obtain green. Additional open-ended duplicate and actual deletion-race tests strengthen the initial cases.

`stage24-domain-green2-20261003` was a preparation failure: QA04 correctly refused output outside `/tmp` before database/test execution. Its output guard was preserved; the local wrapper was corrected. Final GREEN3 used the exact module command above. PostgreSQL 17.11, Django 6.0.2, Python 3.12.3 and psycopg 3.2.10; discovery 1678 unique IDs / 0 duplicates, network/libpq guards true, external credentials present false. Launcher child exit 0; test/cache/media/socket roots removed. Both `check` and `makemigrations --check --dry-run` passed.

After completion all four assigned application/test files matched the executed isolated mirror byte-for-byte (4/4 SHA256 checks). Final hashes:

| File | SHA256 |
|---|---|
| `src/catalog/models/specialist_domain.py` | `8f24acd3054d9bf464a7f2d1fe299ffe036e14d955b1c0e4f1f2b58928a4123c` |
| `src/catalog/services/specialist_domain.py` | `093179ca93eb35112c2feca3fd252ffce41e38414a2e74be820c592f88cdfa66` |
| `src/catalog/services/owner_specialist_use_cases.py` | `921eb817ee71976ecfb4db35d7bbdca708842b3263b40b61dfaf6532a603a35b` |
| `src/catalog/testcases/test_task33_specialist_domain.py` | `77e209f8201db25745b0e3abf1a108b55594a038ead0f720d9e663672d707165` |

## Limits and handoff

This report covers the assigned domain implementation and targeted isolated checks. Independent security/database review, root-owned document/privacy/retention suites, browser checks and wider regressions are separate evidence; this executor does not claim them here. Production, external integrations, deployment, commit/push and stage 25 UI were NOT RUN. Full stage-24 readiness is the orchestrator's decision after all assigned boundaries pass.

## Bounded follow-up: private-document admin layout

Root subsequently assigned the affected existing private-document inline's responsive defect to this executor. `kidsmap-ui-design`, `frontend-design` and `fixing-accessibility` were applied. Browser executor `/root/stage23_public_contracts` supplied actual RED evidence: at 390px the Bootstrap row had client width 326px but scroll width 1602px; the intrinsic grid and 1470px document table escaped the viewport. Focusing the download link scrolled the whole document by 460px. Evidence: `/root/task33-evidence/browser24-final5-20261003/inline-diagnostic.txt`; failures were retained, not excluded.

Minimal source fix is limited to `static/admin/css/pages/specialist_form.css` and `src/catalog/templates/admin/catalog/specialist/change_form.html`: shrinkable grid tracks/children, bounded page layout, private-document wrapper horizontal scrolling, and a scoped override of the global inline's hidden overflow. Root explicitly authorized the existing wrapper's `tabindex="0"`, named region linked to its section heading, and visible keyboard focus. Stylesheet version changes from 5 to 6. All private controls, labels, permissions and fields remain intact; there is no stage-25 redesign. Fresh rendered verification is owned by the separate browser executor and must pass before this follow-up is called complete.

Source SHA256 at handoff: CSS `178bba446b06012ab879bf552705e2ffd08724290c631e92cd3268661a7aa9b0`; template `1c776c158ad8cfd8ba13d90756b525ab8a155980234e01cf17e5e56923d3f4df`. Domain GREEN3 predates this CSS/template-only follow-up; the four domain files listed above were not changed by it.

The separate browser follow-up initially passed all 147 role/language/width rows but retained 7 failures in actual keyboard reachability checks. `/root/task33-evidence/browser24-reviewer-stable-20261003` repeated the failures after 1000ms: controls fit the region and all textareas passed, but native focus scrolling left narrow selects/download links partly outside the scroll region. A RU/1440 download link also clipped against the region despite fitting the viewport. This disproved the proposed oversized-field and short-settling hypotheses; no speculative width CSS was added.

Root authorized a minimal `static/admin/js/specialist_admin.js` private-wrapper `focusin` handler. After native focus, a rendering-frame callback compares the current focused child with the wrapper client region intersected with the viewport and adjusts only the wrapper's horizontal scroll by the bounded necessary delta. It never reassigns focus or calls whole-page scrolling. Fresh browser assertions were strengthened to require full control visibility inside the actual region, preserving actual Tab navigation and preventing viewport-only false positives. JavaScript SHA256: `17a99d4e823f97d13d8bd320bfc4eeef7484b9400b2d77a8bc980610b190949c`; `node --check` and `git diff --check` passed.

Separate browser executor's final fresh corrective evidence `/root/task33-evidence/browser24-reviewer-final-20261003`: **21/21 rows and 73/73 checks PASS**, zero console/page/request events, launcher cleanup PASS. All AZ/RU/EN × seven widths require each actually Tab-focused link/select/textarea fully inside the actual wrapper/viewport intersection with document horizontal scroll remaining zero. Named region ArrowRight and rightmost-column reachability passed. The exact final JavaScript hash above was validated. The previous 147-row matrix covers the other affected roles; this bounded corrective run specifically rechecks the reviewer region after the final JavaScript fix. No remaining confirmed private-region UI blocker was reported. Source ownership is released to root for final integration; stage-24-wide readiness still depends on the separate orchestrator checks.
