# PLACE-QA-13 unsaved modal localization Implementation Plan

> APPROVED 2026-10-12: user explicitly approved QA12 and QA13 together. Only this ID/cause; no commit/push/deploy/production. Existing fixes/worktree/active_run/stands preserved.

**Goal:** render the admin unsaved-navigation modal and its save-and-exit status in active RU/AZ/EN, without changing navigation/save behavior.

**Architecture:** extend the existing request-language `ui_copy()` dictionary and consume its JSON keys from the existing admin controller. No new translator, frozen import-time labels, global modal rewrite or business enum duplication.

**Tech stack:** existing Python copy selector, JSON script, vanilla JS and native Chrome.

**Spec:** `docs/qa/module01-full-2026-10-12-r2/PLACE-QA-13.md`.

## Files and exact copy

- Modify `src/catalog/services/permanent_place_wizard.py`: add five `ui_copy()` keys through existing `t(ru,az,en)` only.
- Modify `static/admin/js/kidsmap_place_form.js`: use those keys in this unsaved-navigation modal, and existing `labels.labelSaving` in its toast/status.
- Own `docs/qa/place-qa13-fix-2026-10-12-r1/` scripts/report; module01 current status links only after evidence. No template, global modal, backend save logic, PO/MO shared files or schema changes.

| Key | RU | AZ | EN |
|---|---|---|---|
| unsaved_title | Есть несохранённые изменения | Yadda saxlanılmamış dəyişikliklər var | You have unsaved changes |
| unsaved_body | Вы изменили карточку, но ещё не сохранили изменения. | Kartı dəyişmisiniz, lakin dəyişiklikləri hələ yadda saxlamamısınız. | You changed the place but have not saved your changes yet. |
| unsaved_stay | Остаться | Qalmaq | Stay |
| unsaved_save_exit | Сохранить и выйти | Yadda saxla və çıx | Save and leave |
| unsaved_discard | Выйти без сохранения | Yadda saxlamadan çıx | Leave without saving |

## Task 1 — RED and minimal copy wiring

- [ ] Fresh native EN and AZ changed form → breadcrumb; preserve raw Russian RED/PNG. RU is reference, not a replacement for translated acceptance.
- [ ] Add exact approved strings to the existing dictionary, e.g.:

```python
unsaved_title=t('Есть несохранённые изменения',
                'Yadda saxlanılmamış dəyişikliklər var',
                'You have unsaved changes'),
```

- [ ] Replace only corresponding options:

```js
title: entryCopy.unsaved_title,
message: entryCopy.unsaved_body,
stayText: entryCopy.unsaved_stay,
saveText: entryCopy.unsaved_save_exit,
discardText: entryCopy.unsaved_discard,
```

Use existing localized saving label for the save-and-exit toast. Keep callbacks, CSRF, endpoint, ACL, redirects and dirty-state logic identical. No global blanket Russian-string replacement.

## Task 2 — native acceptance

- [ ] Fresh own profile/DB/cache/media/email and RU/AZ/EN native build verified before setup; shared MO and existing profiles remain untouched. No .env/production credentials or real external calls.
- [ ] All18cells: modal copy, line wraps/viewport/focus, Tab/ShiftTab/Enter/Space/Escape. Stay preserves dirty input; discard leaves without persisting; save-and-leave performs actual native save and later reload/readback. Network failure/conflict keeps the input and honest state. ORM only synthetic setup.
- [ ] Run existing copy/continuous/admin and affected JS checks unchanged; native screenshots/manifest required. Record exact commands/exits/counts/runtime/locale hashes and NOT RUN. Close only QA13 on fresh proof, then repeat module01 acceptance. Any separate save/redirect defect must receive its own finding/plan.

## Execution and testing cadence

Evidence: docs/qa/place-qa13-fix-2026-10-12-r1/REPORT.md. Targeted checks per repair; one module acceptance after all its findings; global corpus after all13 modules per user. Shared modal keyboard QA14 is separate and remains OPEN, not silently added to this copy scope.
