# CROSS-QA-03 — RU district placeholder falls back to Azerbaijani

**Priority:** P3. **Role:** owner. **Classification:** pre-existing source translation gap; not a demonstrated regression. **Confidence:** high. **Environment:** isolated native Chromium, `DJANGO_TESTING=1`, `http://localhost:8831`, PostgreSQL module13:55444, LOCAL dirty WORKTREE HEAD `8d188b316f800fbedf0b1e376905dfd4924cb1b6`, source digest `e13c36f2af3aca03513ff860a1dee7c02a8cb2ab8214c89bcffd7dd5fe5914b1`.

URL: `/ru/account/places/2/edit/?fresh=1`. Field: `select#id_district`, first option.

1. Sign in as the isolated fictional owner.
2. Open the RU owner Place editor; verify `html[lang=ru]` and surrounding RU form text.
3. Scroll to region/district. Read the first district option without changing the selected district or submitting the form.
4. Repeat at 360, 390, 768, 1024, 1280 and 1440px.

Expected: the empty option is Russian, for example “Выберите район”. Actual: “Rayon seçin” at all six widths. This is interface copy; neither an AZ district value nor a saved user translation is inferred from it. The saved selected district and Place translations were not modified by this check.

Evidence: [six fresh unmodified DOM assertions and screenshot paths](locale-check.result.json), [visible RU mobile placeholder](screenshots/native-r2-locale-visible-ru-390-empty-district-simulated.png), [visible RU desktop placeholder](screenshots/native-r2-locale-visible-ru-1440-empty-district-simulated.png), [visible-state details](locale-visible.result.json), [compiled-catalog inspection](translation-proof.json). The two visible-placeholder captures use native `selectOption('')` in isolated contexts with all non-login writes blocked: **SIMULATED local unsaved state**, original selected code `baku_yasamal` recorded first. No save/submit was clicked; no guarded write occurred; contexts were closed. The original screenshots show the saved district selection rather than the empty option, so they support page context and DOM scope, not visible placeholder text.

Source: `src/catalog/services/locations.py:561` sets the placeholder through `gettext("Выберите район")`. The current RU PO has only an obsolete `#~ msgid` entry at `locale/ru/LC_MESSAGES/django.po:18354`; the compiled RU MO lacks the key. The AZ compiled catalog contains it as “Rayon seçin”. Native RU output matches this default-language fallback. **Confirmed root cause:** missing active RU translation key; rebuilding the unchanged RU PO alone cannot restore an obsolete entry. No clean-HEAD run was performed, so regression attribution remains UNKNOWN.

Impact/severity: an understandable but wrong-language empty field label, with no demonstrated loss of data, publication or access failure. This supports P3. No P0/P1 claim.

Fix scope: active RU gettext entry and reproducible isolated catalog build/locale acceptance. Keep stable district codes, request-language resolution, validation and saved values unchanged. Depend on the existing compiled-catalog work for PLACE-QA-06 / SITE-QA-07, while keeping this missing source entry distinct from stale MO assets.

Named handoff: **frontend-reviewer** for RU interface copy; **integration-reviewer** for catalog build and rendered RU reload verification. [Standalone repair prompt](CROSS-QA-03-repair.txt). No application fix was made.
