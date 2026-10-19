# SITE-QA-07 — Исторические RU labels переключателей в EN/AZ

**NOT REPRODUCED CURRENT PROFILE / P2 / LOCAL C:\kidsmap / 2026-10-18.** Execution /root sequential; confidence high for observed local behavior, root mechanism qualified below. No production evidence or app fix.

Evidence/repro: last-controls.json visibility-current-mo-labels + current3MO; admin localized html languages match. Shared historical MO untouched. See [raw evidence](../evidence/) and [PNG manifest](../png-manifest.json); JSON row IDs identify exact scripts/roles/language/width and observed/expected checks. All records/files are synthetic owned fixtures.

Source/symbol: `src/catalog/domain_admin/site.py; locale/{az,en}/LC_MESSAGES/django.po`.

Root: Historical compiled-MO observation not reproduced with freshly built isolated catalogs. Production/shared-MO deployment not audited.

Impact/expected contract: Исторические RU labels переключателей в EN/AZ; failure checks record intended result and actual values. Priority applies to bounded reproduced behavior, not a production incident.

Owner/dependencies: release-reviewer. Next: Не заявлять production closure. При необходимости отдельно проверить build/deploy locale pipeline; application patch здесь не нужен.

[Standalone next-step prompt](SITE-QA-07-repair.txt). Application implementation requires a concrete approved scope.
