# Two prompts in the existing place dialog — Implementation Plan

> **For agentic workers:** Execute inline in this chat. No delegation, commits, push or deployment. The user's clarification authorizes the two-prompt UI in the existing modal; do not broaden this scope.

**Goal:** Put search and JSON preparation in the existing KidsMap admin dialog, with optional category/subcategory for search and no other filters.

**Architecture:** Reuse the existing native dialog and current server-supplied taxonomy. Keep independent editable prompt drafts for search/JSON. Preserve the import pipeline; JSON prompt includes its current field contract and actual dictionaries automatically.

**Tech Stack:** Django template/i18n, existing vanilla JS and scoped CSS; node:test/jsdom and browser verification.

**Spec:** User clarification on 2026-10-20 with screenshot: everything belongs in this dialog; one prompt finds several places, another prepares JSON files; only optional category refinement for search.

## Global constraints

- LOCAL HEAD e4e05cc213b34e2d771ecb854901bfd016d1db51; task33-progress; pre-existing dirty state preserved, including six existing lines in the scoped CSS.
- Existing read-only findings PR-01/PR-02/PR-05 inform prompt wording only. PR-03/PR-04/PR-06/PR-07 backend/import changes are out of scope.
- No external prompt-library UI, city/age/count/priority filters, schema paste field or six-step workflow.
- Search options never change the place form category/subcategory. They use the server taxonomy already embedded in the form.
- Keep JSON keys/import callbacks/permissions/readiness/save/publication behavior unchanged. No backend edits or migration.
- Prompt content is editorial Russian; UI labels/hints/statuses have RU/AZ/EN translations. Do not overwrite shared compiled MO files.
- Tests use synthetic data and isolated settings; no .env, production credentials, shared databases or production calls.

## Files

- Modify `src/catalog/templates/admin/catalog/place/form/json_prompt_dialog.html`: two native radio choices; optional category/subcategory; existing editable textarea and copy/reset/close actions.
- Modify `static/admin/js/kidsmap_place_json_import.js`: search builder; mode/draft/choice handling; strengthen JSON instructions for selected places and separate files; preserve importer.
- Modify `static/admin/css/pages/kidsmap_place_form.css`: dialog-specific layout, responsive controls and focus styles.
- Modify `locale/ru/LC_MESSAGES/django.po`, `locale/az/LC_MESSAGES/django.po`, `locale/en/LC_MESSAGES/django.po`: only added UI messages.
- Create `scripts/tests/place_json_prompts.test.cjs`: execute actual JS against current dialog fixture, test independent drafts, dependent taxonomy and copy/reset behavior without mutating place fields.
- Modify `src/catalog/testcases/admin.py`: align existing render test with the intentionally changed dialog heading and both prompt controls.
- Reports/synthetic rendered fixture: `docs/qa/place-two-prompts-2026-10-20-r1/`; own runtime: `.tmp/place-two-prompts-2026-10-20-r1/`.

## Task 1 — Existing dialog and prompt behavior

- [x] Capture exact pre-edit files/hashes in own scratch directory.
- [x] Add behavior tests against existing JS: two modes, optional server taxonomy, no mutation of place fields, independent drafts, copied edited text and reset only current draft.
- [x] Run tests and confirm failures from missing two-mode behavior.
- [x] Add native radio controls, two optional selects and translated hints to the current dialog.
- [x] Implement search prompt and independent drafts using the existing taxonomy. JSON generation continues to append the current contract automatically.
- [x] Adjust JSON prompt to research only selected places, request unresolved facts in the ChatGPT conversation, and produce one file/object per place. Do not invent unknown enum/boolean facts from the example.
- [x] Run focused and affected dialog checks. Inspect source diff to prove import section is preserved.

## Task 2 — Translations, rendered UI and handoff

- [x] Add new RU/AZ/EN messages without changing existing translations.
- [x] Compile only own isolated locale output; render the real modal template with current CSS and JS for browser checks using synthetic taxonomy.
- [x] Verify both modes, category/subcategory dependency, copy, draft retention/reset, keyboard and native Escape/close focus in a real browser.
- [x] Verify RU/AZ/EN at 390/768/1024/1280/1440; record overflow and screenshots. This template fixture is not an authenticated full admin or backend-save test.
- [x] Record exact commands/results and NOT RUN boundaries. No commit, push or production access.

**Acceptance:** This same modal contains exactly two prompt modes. Search works without selecting a category; a selected subcategory narrows only its prompt. JSON has its full current taxonomy/field contract without manual copying. Switching modes retains edits. Separate JSON objects/files are requested for multiple selected places. No application field or import behavior is changed by opening or using prompt controls.
