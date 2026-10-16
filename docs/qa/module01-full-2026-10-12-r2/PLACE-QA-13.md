# PLACE-QA-13 — unsaved-navigation modal ignores active admin language

P3 OPEN, LOCAL Chrome153, final approved diff. Recent-regression attribution UNKNOWN; raw-Russian modal options predate this repair.

Native admin `/en/admin/catalog/place/2/change/` on owned repair stand, edit AZ name, click Place-list breadcrumb. Actual modal: «Есть несохранённые изменения», «Вы изменили карточку, но ещё не сохранили изменения.», «Остаться», «Сохранить и выйти», «Выйти без сохранения». English page must show English UI. The defect is rendered, not inferred solely from static strings.

Evidence: `../module01-completion-2026-10-12-r1/unsaved-modal.result.json`, native `screenshots/unsaved-modal-en.png`. Source: `static/admin/js/kidsmap_place_form.js` navigation interception passes hardcoded Russian strings to `kmModal.unsavedChanges`; save-and-exit toast also uses raw Russian. Existing `#km-place-entry-copy` request-language dictionary is already available through `ui_copy()`, so no parallel translation system is needed.

AZ applicability is source-backed but full native matrix NOT RUN for this new finding. Not an alias/reopening of historical compiled-locale QA06/QA08. Fresh MO cannot translate raw literal JS options automatically. No fix performed. Bounded future plan: `docs/superpowers/plans/2026-10-12-place-qa13-unsaved-modal-localization.md`.
