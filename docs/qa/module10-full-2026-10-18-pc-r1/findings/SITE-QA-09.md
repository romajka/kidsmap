# SITE-QA-09 — Events OFF оставляет direct legacy temporary Place

**OPEN / P2 / LOCAL C:\kidsmap / 2026-10-18.** Execution /root sequential; confidence high for observed local behavior, root mechanism qualified below. No production evidence or app fix.

Evidence/repro: supplement-final.json legacy-temporary-event-flag: own temporary future Place exists at direct200 with OFF; ON200 and count4 retained. See [raw evidence](../evidence/) and [PNG manifest](../png-manifest.json); JSON row IDs identify exact scripts/roles/language/width and observed/expected checks. All records/files are synthetic owned fixtures.

Source/symbol: `src/catalog/controllers/place_controller.py; src/catalog/views.py:place_detail; src/catalog/services/features.py`.

Root: Legacy Place direct visibility does not enforce events feature policy used in event/catalog surfaces.

Impact/expected contract: Events OFF оставляет direct legacy temporary Place; failure checks record intended result and actual values. Priority applies to bounded reproduced behavior, not a production incident.

Owner/dependencies: django-reviewer. Next: Согласовать off policy для legacy temporary Place/direct/map/search; не удалять записи и не унифицировать статусы без контракта.

[Standalone next-step prompt](SITE-QA-09-repair.txt). Application implementation requires a concrete approved scope.
