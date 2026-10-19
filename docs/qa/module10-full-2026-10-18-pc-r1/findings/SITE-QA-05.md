# SITE-QA-05 — Загруженные hero PC/mobile не используются

**OPEN / P2 / LOCAL C:\kidsmap / 2026-10-18.** Execution /root sequential; confidence high for observed local behavior, root mechanism qualified below. No production evidence or app fix.

Evidence/repro: media.json:18 hero-configured-asset rows, saved=True, usedByVisibleDOM=False; native uploads successful. See [raw evidence](../evidence/) and [PNG manifest](../png-manifest.json); JSON row IDs identify exact scripts/roles/language/width and observed/expected checks. All records/files are synthetic owned fixtures.

Source/symbol: `src/catalog/templates/pages/home.html; src/catalog/controllers/home_controller.py; src/catalog/domain_admin/site.py:653`.

Root: Editable media field contract and new hero/gallery rendering diverged; exact desired placement requires plan.

Impact/expected contract: Загруженные hero PC/mobile не используются; failure checks record intended result and actual values. Priority applies to bounded reproduced behavior, not a production incident.

Owner/dependencies: frontend-reviewer + frontend-admin. Next: Согласовать PC/mobile placement и fallback, затем подключить файлы; не менять галерею молча.

[Standalone next-step prompt](SITE-QA-05-repair.txt). Application implementation requires a concrete approved scope.
