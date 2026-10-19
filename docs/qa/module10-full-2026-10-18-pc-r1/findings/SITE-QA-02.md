# SITE-QA-02 — AZ about/empty игнорируют сохранённые тексты

**OPEN / P2 / LOCAL C:\kidsmap / 2026-10-18.** Execution /root sequential; confidence high for observed local behavior, root mechanism qualified below. No production evidence or app fix.

Evidence/repro: admin-recovery.json: visibleSavedCopy FAIL AZ about and AZ empty; form readbacks PASS. See [raw evidence](../evidence/) and [PNG manifest](../png-manifest.json); JSON row IDs identify exact scripts/roles/language/width and observed/expected checks. All records/files are synthetic owned fixtures.

Source/symbol: `src/catalog/templates/pages/about.html:76; src/catalog/templates/catalog/place_list.html:970`.

Root: AZ hardcoded branch precedes configured content.

Impact/expected contract: AZ about/empty игнорируют сохранённые тексты; failure checks record intended result and actual values. Priority applies to bounded reproduced behavior, not a production incident.

Owner/dependencies: frontend-reviewer + django-reviewer. Next: Применить настройки AZ с согласованным fallback; проверить save/reload/public RU/AZ/EN и пустое значение.

[Standalone next-step prompt](SITE-QA-02-repair.txt). Application implementation requires a concrete approved scope.
