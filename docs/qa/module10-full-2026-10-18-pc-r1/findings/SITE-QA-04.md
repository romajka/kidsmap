# SITE-QA-04 — Главная игнорирует настройки placeholder и CTA

**OPEN / P2 / LOCAL C:\kidsmap / 2026-10-18.** Execution /root sequential; confidence high for observed local behavior, root mechanism qualified below. No production evidence or app fix.

Evidence/repro: supplement-final.json: home-configured-placeholder-cta RU/AZ/EN; persisted QA strings absent. See [raw evidence](../evidence/) and [PNG manifest](../png-manifest.json); JSON row IDs identify exact scripts/roles/language/width and observed/expected checks. All records/files are synthetic owned fixtures.

Source/symbol: `src/catalog/templates/pages/home.html:261; src/catalog/controllers/home_controller.py:120`.

Root: Controller supplies variables; template uses literal localized strings.

Impact/expected contract: Главная игнорирует настройки placeholder и CTA; failure checks record intended result and actual values. Priority applies to bounded reproduced behavior, not a production incident.

Owner/dependencies: frontend-reviewer. Next: Связать видимые controls с настройками и fallback; сохранить query, labels и search behavior.

[Standalone next-step prompt](SITE-QA-04-repair.txt). Application implementation requires a concrete approved scope.
