# SITE-QA-10 — Пустой 410 превращается в ошибку браузера

**OPEN / P2 / LOCAL C:\kidsmap / 2026-10-18.** Execution /root sequential; confidence high for observed local behavior, root mechanism qualified below. No production evidence or app fix.

Evidence/repro: flags.json events OFF:18 matrix cells request410 plus native Chromium net::ERR_HTTP_RESPONSE_CODE_FAILURE/chrome-error; source returns empty Gone. See [raw evidence](../evidence/) and [PNG manifest](../png-manifest.json); JSON row IDs identify exact scripts/roles/language/width and observed/expected checks. All records/files are synthetic owned fixtures.

Source/symbol: `src/catalog/views.py:362,1300`.

Root: HttpResponseGone() has no HTML recovery body. Status410 is intentional contract.

Impact/expected contract: Пустой 410 превращается в ошибку браузера; failure checks record intended result and actual values. Priority applies to bounded reproduced behavior, not a production incident.

Owner/dependencies: django-reviewer + frontend-reviewer. Next: Сохранить410 и добавить локализованную recovery страницу; проверить прямой native GET и keyboard link RU/AZ/EN.

[Standalone next-step prompt](SITE-QA-10-repair.txt). Application implementation requires a concrete approved scope.
