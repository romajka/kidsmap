from pathlib import Path
Q=Path(__file__).resolve().parent
p=Q/'matrix-template.js';t=p.read_text().replace("p.locator('main').count()","p.locator('main,[role=main]').count()");p.write_text(t)
O=Q.parents[1]/'docs/qa/module09-full-2026-10-17-pc-r1'
(O/'findings').mkdir(exist_ok=True);(O/'repair-prompts').mkdir(exist_ok=True)
(O/'findings/SOCIAL-QA-11.md').write_text('''# SOCIAL-QA-11 — вложенные основные ориентиры страницы

OPEN, P3, LOCAL current WORKTREE. Execution identity /root; actual screenreader NOT RUN.

Guest/author/owner/etc: typed review pages `/ru/reviews/{place|specialist|activity|event}/target/<fixture>/`; authenticated `/ru/account/notifications/`, equivalents AZ/EN.

Steps: open any supported target or the inbox; inspect rendered accessibility structure and `document.querySelectorAll('main,[role=main]')`. Expected one top-level main content landmark. Actual two nested `<main>` elements. Guest matrix reproduces72 observations (4 target types×18 cells); author matrix adds notifications18. Remaining role batches recorded in matrix.

Source: `src/catalog/templates/base.html:135` wraps content in `<main>`; `src/catalog/templates/catalog/typed_reviews.html:7` and `src/catalog/templates/pages/account_notifications.html:12` introduce another main inside this block. Browser DOM plus source confirmed; this is separate from scoped CSS04, conflict03 and title07 fixes. Navigation by main landmark becomes ambiguous; no demonstrated data loss or access bypass.

Classification: current-source baseline issue; compare unchanged outer base and entry HEAD before assigning introduction. Production UNKNOWN. SeverityP3: bounded structural accessibility issue, not a proven screenreader failure.

Proposed scope for a future PLAN: replace the two inner landmark elements with semantically appropriate non-main containers, preserving classes/IDs/layout/feedback/ACL. Verify all review types and inbox roles at RU/AZ/EN×six widths; keyboard and error-state regression checks. Shared base alteration is not required by current evidence. No implementation in this audit.
''',encoding='utf-8')
(O/'repair-prompts/SOCIAL-QA-11.txt').write_text('''KidsMap: PLAN SOCIAL-QA-11 only. Read module09-full-2026-10-17-pc-r1 REPORT, matrix, finding SOCIAL-QA-11 and current guide. Freshly verify current source/runtime/MO; keep existing dirty changes, refs, active_run NONE and prior evidence. Reproduce the two nested main landmarks on typed reviews and account notifications in a disposable local profile. Inspect both templates and their base wrapper, propose a bounded two-template markup change preserving classes, layout, IDs, conflict/rejection/invitation feedback, public projections and ACL. Produce concrete files/diff/acceptance checks before requesting scope approval; do not apply fixes in PLAN. Historical screenreader/device/production evidence is unavailable. No commit/push/deploy/production/reset/clean/stash, no old PNG download.
''',encoding='utf-8')
print('Provisional confirmed landmark finding recorded; exact aggregate coverage pending matrix completion')
