# Module01 local completion Implementation Plan

> Execution: последовательно в этой переписке, после одобрения этого документа. Пользовательский PLAN → approval → implementation → ACCEPT имеет приоритет над шаблонными советами skill о commits и дополнительных execution skills. Commit/push/deploy/production запрещены.

**Goal:** исправить PLACE-QA-09 и PLACE-QA-10 и выполнить недостающую локальную приёмку постоянных мест; выдать закрытие только при фактическом acceptance.

**Architecture:** два раздельно проверяемых изменения существующего continuous editor: видимость фокуса и корректное восстановление после candidate CAS conflict. Серверный CAS, ACL, candidate/live и приватные ServerDraft остаются источниками бизнес-правил. Затем отдельный AUDIT ONLY ACCEPT-01 без автоматических новых fixes.

**Tech stack:** существующие Django/PostgreSQL, vanilla JS/CSS, native Chrome, isolated gettext RU/AZ/EN.

**Spec:** `docs/qa/module01-full-2026-10-12-r1/findings/PLACE-QA-09.md`, `PLACE-QA-10.md`, `docs/qa/continuation-and-repair-prompts-2026-10-11.md#accept01`.

## Snapshot, authorization and constraints

План составлен 2026-10-12 в `/home/ramin/kidsmap`, branch `task33-progress`, HEAD `e4e05cc213b34e2d771ecb854901bfd016d1db51`. `active_run: NONE` в `docs/task33/implementation-status.md`. Dirty: ранее изменённый `docs/qa/module-acceptance-prompts.md`, untracked `docs/qa/start-local-2026-10-12-r1/` и `docs/qa/module01-full-2026-10-12-r1/`. Это существующие evidence, не disposable файлы.

Статус **APPROVED IMPLEMENT**: пользователь ответил «Одобряю этот план» 2026-10-12. Просьба «закроем первый модуль полностью» выбирает цель; ранее показанные PLAN prompts и audit report не являются конкретным implementation plan. Этот документ впервые фиксирует оба новых ID и файлы для одобрения.

- Scope application repairs: только PLACE-QA-09 и PLACE-QA-10. PLACE-QA-01–08 не переисправлять по старому r2; QA08=CROSS-QA03.
- Другие modules/findings, CROSS-QA-02 discovery repair, legacy QA04 guards и specialist assertions вне implementation scope. Их результаты и ограничения честно фиксировать.
- До выполнения снова проверить HEAD/dirty/active_run, хеши затрагиваемых файлов и исходники процессов. Чужой active_run не присваивать/снимать.
- Существующие START/ACCEPT processes и их базы сохранить. Для changed-source verification создать новый собственный profile/DB/cache/media/private-media/email, свежую сборку locales и собственный процесс. Порты/инструменты определить заново, исторические PID/URL не запускать как команды.
- DJANGO_TESTING=1; без checkout .env/production credentials. Синтетические fixtures, внешние обращения blocked/SIMULATED. Readback READ ONLY с statement/lock timeouts. Секреты только ignored scratch.
- Общие MO, миграции, бизнес-правила, ACL/CAS, существующие assertions и история evidence не изменяются. Новые findings OPEN, без автоматического расширения patch.

## Exact file boundaries

Application changes allowed:

1. `static/css/pages/owner_place_continuous.css` — focus-safe layout/scroll margins for QA09.
2. `static/js/owner_place_continuous.js` — minimal focus visibility; typed candidate conflict, halted saves, separate canonical comparison view for QA10.
3. `src/catalog/photo_views.py` — add non-breaking machine-readable candidate conflict metadata to existing 422 response.
4. `static/js/permanent_place_photos.js` — preserve that metadata through XHR/error/save result, suppress misleading retry only for typed candidate conflict; shared consumers regression check.
5. `src/catalog/templates/pages/includes/owner_place_continuous.html` — compare-view/action metadata only if needed for the explicit canonical mode. Existing single action/translated caption are reused.

New regression test: `src/catalog/testcases/test_place_candidate_conflict_recovery.py`; own browser/regression scripts and reports under new `docs/qa/module01-completion-2026-10-12-r1/`; acceptance under `docs/qa/module01-full-2026-10-12-r2/`. Existing backend probes may be reused without overwriting r1.

Localization: existing `server_conflict` and `open_current_draft` copy in `src/catalog/services/permanent_place_wizard.py` already provides RU/AZ/EN text. No new copy or PO patch planned; compile current PO through the existing helper into own profile and prove runtime labels in all three languages. If wording changes become necessary, present their exact copy/files separately before expansion.

Status changes allowed: row01 only in `docs/qa/module-acceptance-prompts.md`, and current module01 summary in guide, linking new reports and preserving historical evidence. Do not rewrite old findings as if they originally passed.

## Task 1 — PLACE-QA-09: native focused control remains visible

Source confirms `.pc-actions` is sticky bottom; focus margins are static 110px/135px/230px. Original normal textarea native Tab case has top914.765625/bottom984.765625 at height950 and is obscured. Static margins alone are insufficient evidence of correction.

- [ ] Reproduce nameAZ → descriptionAZ with native click/Tab and reverse ShiftTab on unpatched source. Record focus target, bounding rectangle, sticky footer/nav rectangles, occlusion and PNG at all six widths × RU/AZ/EN. Preserve RED separately.
- [ ] Measure occupied visible nav/footer space on focus (next animation frame after native browser scrolling). Only scroll if the focused visible representation lies outside the usable viewport; use immediate minimal delta, not smooth scrolling. Do not reorder focus, cancel native keys or scroll on ordinary typing. CSS scroll margins use measured occupancy with existing fallback; update measurement for resize/dynamic footer wrapping.

Proposed visibility calculation (helper in the existing IIFE, invoked on `focusin` and resize):

```js
function focusScrollDelta(rect, safeTop, safeBottom) {
  if (rect.top < safeTop) return rect.top - safeTop;
  if (rect.bottom > safeBottom) return rect.bottom - safeBottom;
  return 0;
}
```

`safeTop`/`safeBottom` come from actual viewport-intersecting top navigation and bottom actions, plus 8px clearance. Only include overlapping sticky surfaces. For controls inside these surfaces do not treat their own container as an occluder. Resolve custom visually hidden input to its visible label/focus representation; do not scroll towards a 1px hidden checkbox. If the control is taller than available viewport, show its leading focus/caret area without oscillating. Register neither input-driven nor scroll-driven loops.

- [ ] Native verify Tab/ShiftTab through visible inputs, tariff/gallery actions, summary/details, navigation and error jumps; open sections/dropdowns, long RU copy, footer wrapping, short-height viewport, reduced motion. Check typing stays stationary while already visible. Owner create/edit both covered.
- [ ] Gate: former 12 failing cells GREEN; all 18 applicable cells have visible normal focus and no overlay/overflow regression. Browser proof is required; no CSS-mirroring unit test.

## Task 2 — PLACE-QA-10: typed conflict and honest comparison

Actual chain: `publication.py` raises code `candidate_version_conflict`; `OwnerPlacesController.save_edit_form` preserves it in non-field ValidationError; `photo_views.py` serializes only strings; `permanent_place_photos.js:send/save` propagates only errors; continuous submit sets generic error and keeps recovery hidden. Existing `draft_current=1` addresses private ServerDraft/localStorage, not canonical candidate.

- [ ] RED exact native two-context case and a new endpoint regression. Owner A saves newer candidate; owner B submits original token with retained text; expect current baseline422 but missing typed conflict metadata. Record immutable candidate/live readback, both versions and input preservation without recording credentials/tokens in artifacts.
- [ ] In existing 422 payload add `conflict: 'candidate_version_conflict'` only when a form error's **code**, obtained from `form.errors.as_data()`, matches that exact code. Ordinary age/photo/other validation422 and forbidden403 must not be tagged.

Proposed extraction:

```python
conflict = any(
    error.code == 'candidate_version_conflict'
    for errors in result.form.errors.as_data().values()
    for error in errors
) if result.form is not None else False
payload = {'ok': False, 'errors': errors}
if conflict:
    payload['conflict'] = 'candidate_version_conflict'
```

Keep existing HTTP status and errors. Do not derive conflict from localized text, attach current tokens or include private model data.

- [ ] Carry `conflict` through XHR reject, result-not-ok throw and save catch return. Existing non-conflict retry behavior remains. For this typed conflict no gallery retry button should claim a retry will resolve stale candidate; restore controls/input/file state normally.
- [ ] Continuous editor receives exact conflict, sets halted/dirty preservation and existing translated conflict status. No autosave/explicit submit allowed with stale tokens. Persist local input using existing localStore, retain photos in original tab, show comparison action.
- [ ] Add explicit **canonical comparison mode** `candidate_current=1` on the existing same-origin owner edit URL. Link opens new tab with `rel=noopener`. Remove `draft_id`, `draft_current`, `draft_session` query parameters; no inherited private draft ID. In this mode initial restore ignores both browser-local and ServerDraft overlays, displaying the existing GET-built canonical candidate. Use an isolated localStorage key suffix for this comparison view, not the original key. ACL and backend form builder unchanged.

URL construction:

```js
const url = new URL(location.href);
for (const key of ['draft_id', 'draft_current', 'draft_session']) url.searchParams.delete(key);
url.searchParams.set('candidate_current', '1');
url.hash = '';
```

Maintain a conflict-kind variable so private ServerDraft409/structure conflicts continue to use their existing private-draft path. Candidate mode must not become a blanket `fresh=1` bypass dependent on local key absence. Never refresh original publication token or auto-merge versions. The user can compare and manually enter intended changes in the new current view; original input stays available.

- [ ] Meaningful endpoint regression cases: real valid stale candidate →422 typed code + denied write; current valid token →success; ordinary invalid age →422 without conflict; foreign owner →denied without metadata leak; UUID retry still idempotent. Use existing quality fixtures/form fields and real service advancement for test setup; no mocking conflict result to test only serialization. Existing publication tests unchanged.
- [ ] Native browser regression all18cells: A/B stale candidate, actionable status, link keyboard activation/new view, newer candidate visible despite older local/private draft, original text/photos intact, stale repeated save blocked, deliberate manual comparison/save from current view. Separately ServerDraft409, normal422, upload failure and offline handling retain distinct behavior.
- [ ] Gate: actual endpoint → shared photo transport → continuous consumer chain GREEN, newer candidate/live protected and input preserved. jsdom alone does not close this ID.

## Task 3 — fresh runtime and affected regression evidence

- [ ] Own unique launcher verifies fresh locale manifest and single LOCALE_PATHS before django.setup; snapshot application/source hashes at startup and read back process source match. Existing stands stay running unchanged. Run exact helper build/verify commands using actual own output path and native msgfmt.
- [ ] Run new test module plus existing PLACE continuous/publication/ServerDraft/photo/image/owner ACL families selected from actual discovery. Run shared photo editor consumers (legacy wizard and continuous), Node configured corpus and complete configured Django corpus with explicit unique-ID discovery, not no-label/wrapper blanket claims.
- [ ] Record commands/exits/counts/duration, discovery omissions, changed-source results and clean HEAD baseline. Existing QA04 environment guards and stale specialist assertion remain failures with attribution; do not weaken assertions, mimic WSL or change global discovery as part of this patch. A relevant behavior blocked behind a guard remains NOT RUN until independently verified in the isolated applicable profile.
- [ ] New repair report contains RED/GREEN, cause, exact files/diff, locale/runtime evidence, browser PNG SHA manifest, preservation hashes and limits. Mark only proven scoped ID closures; no module PASS from repair alone.

## Task 4 — ACCEPT-01 local completion, AUDIT ONLY

New run must replay delivered fixes and lifecycle on repaired source and finish the real local gaps from r1. Preserve old raw attempts and matrices; build new explicit applicability rows rather than turning all NOT RUN into PASS.

- [ ] Enumerate current categories/subcategories and branch creation variants from canonical source, cover actual different validation paths through native UI with save/reload/moderation/public readback. Record exact exercised categories and genuinely inapplicable role cells.
- [ ] Repeat standalone/network branch lifecycle: create → partial draft → reload/logout/login → continue → invalid input → corrected submit → rejection/reason → resubmit → approval/public → edit published. AZ/RU/EN fallback display must not populate empty persisted translations.
- [ ] Pricing: owner visible tariff kinds, admin all4policies and repeated switching, general ticket/event pricing; nested group tariff validation and roundtrip. Mark absent owner price-policy control N/A rather than untested supported action. Hours modes separately from lesson timetable.
- [ ] Coordinates: absent,0/0,partial/out-of-range, manual save/reload, geographic publication contract; denied/unavailable geolocation and SDK are explicitly SIMULATED. Contacts/address/region/district and error links across18cells.
- [ ] Gallery: applicable formats supported by actual normalizer, corrupt/oversized/dimension/pixel/batch limits, distinct files/dedup, cap, order/replacement/promotion/deletion, save/reload and public media. Test backend-rejected cases through native upload where possible; distinguish browser filtering from server validation.
- [ ] Concurrency: actual simultaneously released valid saves, double-submit, candidate stale state, private ServerDraft CAS, UUID retries. Simulate transport loss **after a confirmed server commit**, then native retry/reload/readback proves no duplicate/lost update. Do not count abort-before-send as this case.
- [ ] Owner/admin/guest/foreign-owner endpoint ACL and private media/draft access. Use read-only readback for accepted writes; ORM only fictional setup, never audited user transitions.
- [ ] Complete applicable empty/filled/loading/error/conflict/modal states × role × RU/AZ/EN ×360/390/768/1024/1280/1440. Keyboard Tab/ShiftTab/Enter/Space/Escape, styled-control visible focus, long text, occlusion/overflow, console/network. Manually inspect representative real PNGs and every failing screenshot.
- [ ] Repeat configured discovery/full Django/Node suites and baseline attribution on final source. Actual CI, other engines/physical devices, screenreader, production and real external providers remain NOT RUN unless separately authorized and actually executed; never claim their acceptance.
- [ ] Decision: local module acceptance only when applicable required local scenarios pass and both IDs have fresh closure evidence. Relevant required local NOT RUN or confirmed new failure prevents full closure. Out-of-module legacy/environment corpus failures stay explicit, not silently green. New findings receive new IDs and separate plans; implementation stops for that expansion.
- [ ] Update only module01 current journal/guide status with report links and counts. Give handoff and next module02 PLAN prompt **only after** actual module01 acceptance; otherwise name the exact blocker.

## Review and handoff

Plan covers both confirmed IDs and r1 mandatory local gaps; app files listed above, no unrelated patches. Source verified directly after graph lookup (graph templates partial, historical snapshot hits excluded). Approval of this document authorizes two bounded repairs plus local QA/evidence; it does not authorize making any new defect green by expanding patch scope. No guarantee of PASS before execution.

Approval phrase: «Одобряю план docs/superpowers/plans/2026-10-12-module01-completion.md: PLACE-QA-09, PLACE-QA-10 и локальную ACCEPT-01 по его границам. Без commit/push/deploy/production».
