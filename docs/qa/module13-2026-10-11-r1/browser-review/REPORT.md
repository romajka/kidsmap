# Module13 — browser-qa

2026-10-11; execution `/root/cross_browser`, actual definition `.agents/agents/browser-qa/agent.md`; **AUDIT ONLY**. Ownership: this `browser-review/` directory and its own ignored scratch/session. No application, migrations, rules, assertions, production, commit/push/deploy changes.

LOCAL checkout `C:/kidsmap`; HEAD `8d188b316f800fbedf0b1e376905dfd4924cb1b6`; branch `task33-progress`; foreign dirty WORKTREE preserved. `active_run=NONE` comes from the parent snapshot. Runtime `/qa/version` independently attests `DJANGO_TESTING=1`, Python3.12.15/Django6.0.2, isolated PostgreSQL:55444, runtime PID23204 and source digest `e13c36f2af3aca03513ff860a1dee7c02a8cb2ab8214c89bcffd7dd5fe5914b1`: startup, parent entry and current disk match. PRODUCTION: NOT RUN.

## 1. Состояние области

**FAIL within the executed locale checks; no overall product PASS.** [Matrix JSON](matrix.json), [CSV](matrix.csv), [counts](counts.json): **2205 PASS / 20 FAIL / 72 NOT RUN**. Counts are scenario assertions, not unique Django tests. FAIL includes18 unchanged-page locale assertions and2 explicitly SIMULATED visible empty-selection rechecks. Native rendered observations: **270** = public180 + owner54 + admin36. Each role independently covers RU/AZ/EN ×360/390/768/1024/1280/1440, with actual HTML language recorded. Admin RU/EN use explicit `/ru/admin/` and `/en/admin/` URLs.

Public: created Place, initial ready Place, Organization, Activity, Specialist, physical and online Events, Organization index, filled and empty catalog search. Owner: Place editor, Organization editor, Program editor. Admin: Place and Event change forms. Paths and state-before/state-after snapshots are in the raw `matrix-<role>-<lang>.result.json` files; root lifecycle changes occurred after the public/owner matrix was released. The same fixtures do not imply identical business state across all capture times.

Native completed-run PNGs: **629**; **688** retained including initial probe and the unfinished first attempt. **12** derived contact sheets are navigation aids, not extra native evidence. [Manifest with dimensions/SHA](screenshot-manifest.json), [contact provenance](contacts.json), [manual visual review and limits](visual-review.md), [fresh artifact verification](verification.json).

## 2. Сильные стороны

Rendered pages have expected main headings, images without detected loaded-image failures, document/body width within viewport, effective page language and keyboard-reachable visible first targets. Computed first-target outline/shadow was inspected after Tab; Shift+Tab and Escape were exercised. Mobile drawers, Organization custom selectors, catalog sort selectors, anonymous favorite auth notices, owner details and admin Event Select2 dropdowns were opened through native keyboard/click events. These checks do not prove every control's complete Tab cycle.

Public Place EN correctly shows the visible fallback explanation while its title uses the available AZ content; this is displayed fallback, not evidence of a stored EN translation. Actual long descriptions were viewed. Additional 195-character title wrapping was tested by explicit **SIMULATED DOM textContent stress**, without changing persisted data. Real empty catalog results and delayed/503 read-only search suggestion responses were captured at390/1440 for all three languages.

## 3. Реальные проблемы

* **PLACE-QA-06**, fresh corroboration: 12 AZ/EN admin cells show the map unavailable warning in RU. Current active AZ/EN PO translations exist, but corresponding compiled MO keys are missing. [Locale assertions](locale-check.result.json), [compiled evidence](translation-proof.json), [AZ screenshot](screenshots/native-r2-locale-az-390-admin-map-notice.png), [EN screenshot](screenshots/native-r2-locale-en-1440-admin-map-notice.png). Classification: environment/generated assets; shared compiled-catalog dependency with SITE-QA-07. No duplicate CROSS ID.
* **[CROSS-QA-03](CROSS-QA-03.md), P3**: RU owner district placeholder is AZ at all six widths; current RU PO entry is obsolete and RU compiled catalog lacks the key. [Standalone repair prompt](CROSS-QA-03-repair.txt). Classification: source translation gap; no clean-HEAD regression attribution.

No fresh layout, loaded-image or unsimulated local console/network defect was confirmed in this delegated surface set. Other module13 functional findings belong to the root report.

## 4. Tech debt

Source PO and running compiled MO can disagree while HTML language is correct. Native locale acceptance must check message content, not only `html.lang`. The admin automatic URL-preview POST is blocked by this role's conservative write guard; its resulting ERR_FAILED is explicitly SIMULATED and never classified as an application defect.

## 5. Risks

Only bundled real Chromium headless shell on Windows was executed. Native phones/tablets, Safari/Firefox, production CSS deployment, real Maps/Google fonts/network and screen-reader behavior remain NOT RUN. External routes were deliberately aborted; fonts may use local/system fallback. A screenshot and HTTP200 alone do not establish saved state, moderation or authorization.

## 6. Dead/legacy candidates

None established. No deletion, orphan or database-deadness conclusion follows from this browser slice. Historical reports were used only to deduplicate the fresh compiled-locale failure.

## 7. Tests gaps и точные команды

72 NOT RUN rows: 18 real-map transport/SDK checks and 54 owner save/error/conflict checks assigned to the parent native workflow. This role never submitted those forms; the root's fresh evidence must be used separately. Every field focus cycle, every owner empty/error variant in all18cells, actual persisted195-character names and every native browser/device remain unproven here. No standalone Django suite was executed by browser-qa; integration-reviewer owns those results.

Commands from repository root:

```powershell
.venv/Scripts/python.exe docs/qa/module13-2026-10-11-r1/browser-review/setup.py
& 'C:/Program Files/nodejs/node.exe' 'C:/Users/Ramin/AppData/Local/npm-cache/_npx/31e32ef8478fbf80/node_modules/@playwright/cli/playwright-cli.js' -s=module13-visual open http://localhost:8831/qa/version/ --config .tmp/module13-20261011-r1/browser-review/playwright.json
.venv/Scripts/python.exe docs/qa/module13-2026-10-11-r1/browser-review/drive.py probe.js
.venv/Scripts/python.exe docs/qa/module13-2026-10-11-r1/browser-review/drive.py matrix.js guest ru
.venv/Scripts/python.exe docs/qa/module13-2026-10-11-r1/browser-review/batch.py
.venv/Scripts/python.exe docs/qa/module13-2026-10-11-r1/browser-review/drive.py auth-recheck.js
.venv/Scripts/python.exe docs/qa/module13-2026-10-11-r1/browser-review/drive.py supplement.js
.venv/Scripts/python.exe docs/qa/module13-2026-10-11-r1/browser-review/drive.py locale-check.js
.venv/Scripts/python.exe docs/qa/module13-2026-10-11-r1/browser-review/drive.py locale-visible.js
.venv/Scripts/python.exe docs/qa/module13-2026-10-11-r1/browser-review/translation-proof.py
.venv/Scripts/python.exe docs/qa/module13-2026-10-11-r1/browser-review/build-report.py
.venv/Scripts/python.exe docs/qa/module13-2026-10-11-r1/browser-review/verify.py
```

[Per-command timestamps/durations/exits](command-ledger.jsonl): successful final nine matrix batches, auth recheck, supplement and locale-check CLI exit0. Scenario FAIL counts are independent of CLI exit. The initial matrix was interrupted solely to correct stale transformed drawer-close automation (CLI exit1, no exported completed assertions). A mistaken attempt to pass Python `batch.py` to the JS driver also returned CLI exit1. These are retained QA harness failures in [inventory](harness-error-inventory.json). Initial artifact verification returned1 because that mistakenly dispatched Python source had a `.js` filename; its unchanged content is preserved as `.txt`, and [verification.attempt1.json](verification.attempt1.json) retains the failed result. Final verifier returns0: syntax, matrix counts/cells/languages,688 PNG dimensions/hash/integrity, local links, exact isolated credential scan and unchanged runtime-source attestation. Six initial RU auth FAIL assertions incorrectly expected a dialog; native UI uses `role=status` toast. Raw assertions are preserved and explicitly excluded; fresh correct six-width recheck passes. Existing application assertions were not changed.

## 8. Recommendations

Resolve the compiled-catalog dependency under a separately approved implementation scope, then the missing active RU district translation. Re-run exact native locale cells and save/reload checks after those changes. Preserve stable geographic codes, runtime source attestation and separate actual transport from simulations. Detailed inspection of all controls and device/browser coverage requires additional scoped verification; do not replace it with graph/source or DOM-only tests.

## 9. P0/P1/P2/P3 и named handoff

No P0/P1 evidence in this slice. Preserve the existing PLACE-QA-06 priority and identity in the root reconciliation; CROSS-QA-03 is P3 because it is wrong-language empty-field copy with no demonstrated data/ACL failure. **Next: kidsmap-orchestrator** merges this report and the root native transitions; **frontend-reviewer/integration-reviewer** own the concrete locale repair scope and fresh verification. Findings are recommendations; no fix authorization was inferred.
