# Admin table repair implementation plan

**Goal:** Correct the oversized sorting SVG shown by the user and verify the working admin lists/forms.
**Architecture:** The generic result template uses a shared sorting component. Its styles must be loaded by the shared admin stylesheet, with explicit SVG dimensions as a safe HTML default. Preserve existing domain actions, data and historical evidence.
**Tech stack:** Django/Jazzmin templates, CSS, actual Chromium via playwright-cli; isolated existing PostgreSQL preview.
**Spec:** User screenshot of /admin/catalog/organization/ and explicit instruction to fix the broken interface.

## Constraints

APPROVED IMPLEMENT, lead frontend-admin executed by /root sequentially. Existing WORKTREE preserved. No production/commit/push/deploy; no migrations or business-contract changes for this presentation fix. Tests DJANGO_TESTING=1 with isolated DB/cache/media/mail. Keep final-audit/completion and prior runtime mirrors unchanged. Evidence belongs to manual-check/admin-fix.

## Tasks

- [x] Reproduce the screenshot using the real authenticated local preview: generic sorting SVG 266px, header 287px. Check graph coverage and verify source/template/stylesheet ownership.
- [x] Create browser regression before application edits: six lists at 1440/390; expected icon ≤24px, header ≤100px, no page overflow or unexpected browser errors. Actual RED: eight oversized-icon failures.
- [x] Preserve changed file originals, manifest, launcher and source hashes before edits.
- [x] In static/admin/css/kidsmap_admin_tables.css define the shared sorting badge and 14px SVG sizing/orientation. Add width/height/focusable/aria-sort in src/templates/admin/change_list_results.html. Update imported table CSS and root CSS cache versions in static/admin/css/kidsmap_admin.css and templates/admin/base{,_site}.html.
- [x] Prepare /root/km-manual-adminfix from the previous verified runtime; copy only authorized deltas, verify every source hash and update local launcher/manifest. Restart only the owned local HTTP process, retaining DB/media/sessions.
- [x] Re-run the same regression. Broaden actual-browser checks to sidebar lists, main forms, AZ/RU/EN ×390/768/1024/1280/1440; check sort/search/filter, keyboard and page overflow. Correct any additional confirmed defects and retain their failing evidence.
- [x] Save screenshots and report exact executed results/not-tested scope, source/evidence preservation, running URL and journal. Close active_run after checks complete.

Additional confirmed defects from the 366-case pass: Place table overflow (overflow:visible wrapper), Staff header actions (non-wrapping flex row), SEO Select2 filter (fixed inline width), malformed Place TH class attribute. Preserve the five additional source originals, repair the owning CSS/template with cache versions, repeat the exact failed pages before repeating the broader matrix. No data/schema/action changes.

Additional rendered localization finding: RU Home was untranslated; missing RU entries for Save and Copyright fell back to the default AZ catalog. Preserve locale/ru/LC_MESSAGES/django.po, provide explicit Russian strings, compile the local runtime catalog and verify the same RU/EN/AZ form. Keep the established AZ term Ana səhifə; the first probe's alternative synonym was a QA expectation error, not an application defect.

Commands use the established owned QA launcher and playwright-cli sessions adminfix/admininteractions. Evidence: browser-red.json, browser-green.json, browser-regression-final.json, browser-matrix-final.log, browser-mobile-final.log and new screenshots under output/playwright/manual-check/.
