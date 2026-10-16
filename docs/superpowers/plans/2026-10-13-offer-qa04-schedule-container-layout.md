# OFFER-QA-04: доступные кнопки расписания — Implementation Plan

> **For agentic workers:** execute inline in this chat after approval of this concrete scope; no extra agents/commits. User instructions override generic skill defaults. Keep checks targeted; full module acceptance comes later.

**Goal:** «Интервал» и «Копировать» остаются полностью внутри формы расписания при любом проверяемом размере окна и наличии боковой панели.

**Architecture:** Owner schedule table becomes a named inline-size query container. Its children use the existing stacked schedule composition when actual table width is insufficient for four fixed columns. Scope is owner-only; popup and mobile overlay are siblings outside the table container, so they keep their original viewport/editor anchoring.

**Tech Stack:** Existing CSS Grid/container queries; current native Chromium, Django isolated local QA solely for acceptance. No new library/dependency.

**Spec:** `docs/qa/module05-2026-10-10-r1/findings/OFFER-QA-04.md`; fresh `docs/qa/offer-qa04-recheck-2026-10-13-r1/REPORT.md`.

## Snapshot / status / scope

- `/home/ramin/kidsmap`, HEAD `e4e05cc213b34e2d771ecb854901bfd016d1db51`, task33-progress, dirty incoming WORKTREE, active_run NONE. Keep prior fixes and stands.
- User selected next PLAN; this document is pending implementation approval. OFFER01–03 approvals do not include04.
- Native baseline27cells = RU/AZ/EN×360/390/768/900/960/1024/1100/1280/1440:17FAIL,10PASS, no harness error. Second exact-table diagnostic1024 confirms FAIL in all3languages. Header/row CSS chooses four columns by viewport width even though sidebar leaves621px table.
- At RU1024 actual table ends942, «Интервал» ends956.25 and «Копировать»1097.94. Table overflow:hidden clips them; document scrollWidth remains1024, so page-level overflow check alone misses defect.
- Browser-only prototype CSS gives3/3geometryPASS at1024, visually inspected RU. It was injected into a disposable browser context then discarded, never applied to source; not application acceptance/PASS.
- Current own03 runtime and current PO manifest verified, no Windows/runtime parameters copied. New fictional regular-schedule cards have2Monday intervals, no candidate revisions. All application files unchanged during PLAN.

## Exact files

Modify only1application file:
- `static/css/components/kidsmap_schedule_editor.css` — append owner-only named-container rules below existing media overrides.

Evidence/documentation:
- this plan and `docs/qa/offer-qa04-recheck-2026-10-13-r1/`;
- new unique `docs/qa/offer-qa04-fix-2026-10-13-r1/` with runtime/source/locale/commands/native results/PNG manifest/REPORT/FINDINGS/next-prompt;
- scoped links/status in `docs/qa/continuation-and-repair-prompts-2026-10-11.md` and `docs/qa/module-acceptance-prompts.md`.

Do not modify JS/templates/backend/schema/business schedule rules/PO/messages/other CSS, or existing assertions. Other OFFER04-adjacent functionality findings do not become approved by this scope. If actual acceptance requires additional application files or a new cause, preserve evidence and request concrete extension before that change.

## Constraints / dependencies

- No commit/push/deploy/production, .env copying, shared MO replacement, foreign process/container/profile control, or active_run assignment.
- Real native user transitions; ORM only fictional fixture setup and explicit READ ONLY readback (timeouts10s/2s).
- DJANGO_TESTING=1, own PostgreSQL loopback DB/container/cache/media/private-media/email, fictional roles, blocked/SIMULATED external requests. Verify actual source/startup/disk before claims.
- Build fresh RU/AZ/EN from current PO through scripts/build_isolated_locales.py into own new profile, verify manifest and install sole LOCALE_PATHS before django.setup. Existing own03 PO build was current and reused only for recheck, not a new04 compilation claim.
- Container must be on table, not entire editor: mobile copy popup uses position:fixed and is appended to editor. Putting containment on that ancestor risks changing fixed positioning.
- Existing tokens/typography/labels/actions/order/focus indicators remain. Do not squeeze font sizes, hide actions, crop content or turn on horizontal scrolling as a substitute.
- Current Chromium reports CSS.supports('container-type','inline-size')=true. Other browser/device coverage remains explicitly NOT RUN unless actually executed.
- Shared template/JS consumers inspected: owner continuous/workspace/legacy owner template and admin Place/volunteer editor. Admin selectors remain outside owner-only rules; verify their native behavior.

## Task1 — preserve failing behavior / prepare own acceptance

- [x] Capture incoming hashes/source snapshot/HEAD/branch/active_run; compare CSS baseline to approved plan and retained recheck. New unique isolated profile/runtime and fictional schedule fixtures; never reuse another computer's ports/credentials.
- [x] Retain existing RED native geometry: all3languages1024, exact row/table bounds and PNG. Own prepatch spot-check same assertion if checkout changed since plan.
- [x] Verify runtime/current PO source and compile manifest. Set fictional regular schedule with Monday09:00–12:00 and14:00–18:00, weekday rows and closed weekends. Canonical fixture setup is allowed; checked add/copy/save transitions use UI only.

## Task2 — minimal owner CSS patch

- [x] Append this candidate; refine only within same CSS file if real acceptance exposes a boundary issue from this same responsive cause.

```css
.km-schedule-editor--owner .km-schedule-editor__table {
  container-type: inline-size;
  container-name: km-owner-schedule;
}
@container km-owner-schedule (max-width: 940px) {
  .km-schedule-editor--owner .km-schedule-editor__header { display: none; }
  .km-schedule-editor--owner .km-schedule-editor__row {
    grid-template-columns: minmax(0, 1fr);
    gap: 10px;
    padding: 14px 12px;
    min-height: 0;
  }
  .km-schedule-editor--owner .km-schedule-editor__row > div { padding: 0; min-width: 0; }
  .km-schedule-editor--owner .km-schedule-editor__status { flex-direction: row; align-items: center; gap: 12px; }
  .km-schedule-editor--owner .km-schedule-editor__work,
  .km-schedule-editor--owner .km-schedule-editor__intervals { width: 100%; }
  .km-schedule-editor--owner .km-schedule-editor__copy {
    justify-content: flex-start;
    margin-left: 0;
    flex-wrap: wrap;
    max-width: 100%;
  }
}

```

940px is a conservative real table-width threshold: desktop four-column layout plus padding/gaps/long RU actions needs more width than the owner's621–805px tables. Spacious owner tables can retain existing four-column layout; cramped ones use existing reading order with actions below working hours. flex-wrap handles long labels without reducing type size.

- [x] Preserve generic/admin media rules. No owner wrapper/sidebar breakpoint change, no style applied to unrelated pricing/forms. Container table affects its own header/rows only; copy popup stays sibling outside containment.

## Task3 — targeted rendered regression / functionality

No redundant unit tests asserting CSS text. No unchanged backend/full-module/global test runs: this is a reversible visual CSS change with native browser acceptance.

Exact execution pattern (unique session/profile paths recorded in report):

```text
playwright-cli -s=<owned-offer04-session> open about:blank
python3 docs/qa/offer-qa04-fix-2026-10-13-r1/drive.py browser.js
<own-python> <own-runtime.py> script <absolute-readback.py>
<own-python> scripts/build_isolated_locales.py verify --manifest <own-manifest.json>
```

- [x] RU/AZ/EN×360/390/768/1024/1280/1440, plus900/960/1100 breakpoint neighbors. Every case explicitly regular and2Monday intervals; compare actual button rectangles to row/table/viewport and clipping ancestors, not only document overflow. Real screenshots of complete controls and layout.
- [x] Sticky sidebar and save bar remain usable; keyboard focus on add/copy controls has visible outline and uncovered hit test, Tab/ShiftTab follow actual DOM order. Do not force clicks through clipping/overlays.
- [x] Native «Интервал»: add a third valid interval, edit times, save draft, reload; candidate has changed schedule, live schedule unchanged before approval. No JS hidden-input mutation or ORM substitute for checked transition.
- [x] Native «Копировать»: open popup, select target days/confirm, save/reload and readback. Popup/overlay/confirm/cancel fit visible viewport at mobile and desktop. Open/close must not change hours; apply copies exactly selected days according to existing contract. Check clipboard is unrelated—use schedule copy UI.
- [x] Native switch closed/open/24h and back, intervals remain accessible. Retain validation errors/entered schedule on rejected save and verify CSS does not hide error rows.
- [x] Actual admin Place and volunteer schedule consumers: smoke at390/1024/1440, regular/multiple intervals/actions/popup/keyboard; admin layout unchanged by owner-only container, no claim of unrelated module acceptance.
- [x] Check real console/pageerrors/network; classify expected validation422 and blocked external requests separately. PNG manifest includes SHA/bytes; source inspection/HTTP200 alone is not rendered acceptance.

## Task4 — evidence / scoped closure

- [x] READ ONLY own fictional data with timeouts: approved candidate schedule/readiness semantics unchanged; checked successful saves/reload and invalid saves don't alter live prematurely. For one corrected fictional schedule per language at390px perform actual submit/approval/public schedule reload, then READ ONLY confirm candidate/live schedule and stable IDs; do not call source-only lifecycle PASS.
- [x] Verify current source process, locale manifest and preserved incoming bytes; exact1application CSS diff, active_run unchanged, no new out-of-scope source files. Reports separate baseline, environment and harness failures.
- [x] Close only OFFER-QA-04 if native acceptance passes. Update current status with report/verification links; preserve historical audit. Full ACCEPT-05/global/production remain NOT RUN.
- [x] Handoff next PLAN OFFER-QA-05; OFFER-QA-09 baseline and other historical findings stay outside scope. No automatic next implementation.

## Execution clarification: existing schedule contract

The plan incorrectly expected schedule changes to remain candidate-only until approval. Current canonical business contract in docs/task33/prompts/08.md:51 and publication.py:_immediate explicitly applies schedule immediately after explicit save of a published card; autosave remains private (prompts/09.md:50). Native save/readback confirmed it. Preserve this behavior; backend/JS/file scope is unchanged. Correct only the new acceptance expectation, retain its initial false-positive failure in raw evidence, and still verify invalid-save rejection, actual draft/reload and moderation/public metadata path. No new application finding or expanded scope inferred.

## Execution receipt

Approved by user; completed2026-10-13, only1CSS application file39appended lines. Same-file approved popup viewport acceptance required owner-only fixed desktop centering/max-height/internal scroll; no new JS/backend/PO scope.335unique native assertions PASS,81accepted PNGs, readback/current-source/preservation verification in docs/qa/offer-qa04-fix-2026-10-13-r1/REPORT.md. Canonical immediate schedule policy clarification above supersedes the mistaken candidate-only expectation. Existing test assertions unchanged; backend/full module/global/production NOT RUN.
