# SITE-QA-12 — DEBUGFalse 404 не локализован и без recovery

**OPEN / P3 / LOCAL C:\kidsmap / 2026-10-18.** Execution /root sequential; confidence high for observed local behavior, root mechanism qualified below. No production evidence or app fix.

Evidence/repro: last-controls.json generic404-copy; interactions.json18status404/noDebug checks. Own DEBUGFalse runtime; staticfinder QA override. See [raw evidence](../evidence/) and [PNG manifest](../png-manifest.json); JSON row IDs identify exact scripts/roles/language/width and observed/expected checks. All records/files are synthetic owned fixtures.

Source/symbol: `src/config/urls.py; absence of custom404 template/handler`.

Root: Django generic error page supplies English body and no app recovery links.

Impact/expected contract: DEBUGFalse 404 не локализован и без recovery; failure checks record intended result and actual values. Priority applies to bounded reproduced behavior, not a production incident.

Owner/dependencies: frontend-reviewer + django-reviewer. Next: Добавить локализованную404 с безопасным возвратом в каталог; проверить DEBUGFalse RU/AZ/EN и bad paths.

[Standalone next-step prompt](SITE-QA-12-repair.txt). Application implementation requires a concrete approved scope.
