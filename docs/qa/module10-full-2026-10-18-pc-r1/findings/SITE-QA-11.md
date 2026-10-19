# SITE-QA-11 — Loading/delete медиа остаются русскими в EN/AZ

**OPEN / P3 / LOCAL C:\kidsmap / 2026-10-18.** Execution /root sequential; confidence high for observed local behavior, root mechanism qualified below. No production evidence or app fix.

Evidence/repro: media-localized.json:12 language-specific loading and12 dialog title FAIL; normal labels surrounding them translated. See [raw evidence](../evidence/) and [PNG manifest](../png-manifest.json); JSON row IDs identify exact scripts/roles/language/width and observed/expected checks. All records/files are synthetic owned fixtures.

Source/symbol: `static/admin/js/kidsmap_site_media.js:119,197,314`.

Root: JavaScript literals bypass translation catalogs.

Impact/expected contract: Loading/delete медиа остаются русскими в EN/AZ; failure checks record intended result and actual values. Priority applies to bounded reproduced behavior, not a production incident.

Owner/dependencies: frontend-admin. Next: Подключить проектный механизм локализации async states/dialog; проверить loading/error/re-enable/delete/cancel на3языках.

[Standalone next-step prompt](SITE-QA-11-repair.txt). Application implementation requires a concrete approved scope.
