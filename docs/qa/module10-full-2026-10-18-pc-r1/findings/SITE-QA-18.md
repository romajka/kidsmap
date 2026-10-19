# SITE-QA-18 — Длинное сохранённое имя бренда ломает desktop width

**OPEN / P2 / LOCAL C:\kidsmap / 2026-10-18.** Execution /root sequential; confidence high for observed local behavior, root mechanism qualified below. No production evidence or app fix.

Evidence/repro: supplement-final.json long-brand-empty-hero-fallback and final-diagnostics-recovery.json long-brand-desktop-overflow:3language desktop1440cells; native save accepted within120character limit. Brand restored. See [raw evidence](../evidence/) and [PNG manifest](../png-manifest.json); JSON row IDs identify exact scripts/roles/language/width and observed/expected checks. All records/files are synthetic owned fixtures.

Source/symbol: `src/catalog/templates/includes/header.html; static/css/components/header.css; src/catalog/models/site.py:77`.

Root: Long configured brand expands header/navigation beyond desktop viewport; exact cascade to confirm in repair plan, offending elements captured.

Impact/expected contract: Длинное сохранённое имя бренда ломает desktop width; failure checks record intended result and actual values. Priority applies to bounded reproduced behavior, not a production incident.

Owner/dependencies: frontend-reviewer. Next: Ограничить/перенести brand/navigation без потери accessible name; проверить maximum length,360–1440 and keyboard menus.

[Standalone next-step prompt](SITE-QA-18-repair.txt). Application implementation requires a concrete approved scope.
