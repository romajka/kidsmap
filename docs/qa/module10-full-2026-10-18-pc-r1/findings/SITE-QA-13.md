# SITE-QA-13 — Исторический выход фокуса media modal

**NOT REPRODUCED CURRENT PROFILE / P2 / LOCAL C:\kidsmap / 2026-10-18.** Execution /root sequential; confidence high for observed local behavior, root mechanism qualified below. No production evidence or app fix.

Evidence/repro: media-localized.json18dialogs: initialFocus/8Tabs/ShiftTab/EscapeNoDelete PASS at all3langs×6widths. See [raw evidence](../evidence/) and [PNG manifest](../png-manifest.json); JSON row IDs identify exact scripts/roles/language/width and observed/expected checks. All records/files are synthetic owned fixtures.

Source/symbol: `static/admin/js/kidsmap_site_media.js:314; shared kmModal`.

Root: Current shared modal behavior did not reproduce historical defect under settled render timing.

Impact/expected contract: Исторический выход фокуса media modal; failure checks record intended result and actual values. Priority applies to bounded reproduced behavior, not a production incident.

Owner/dependencies: frontend-admin. Next: Не исправлять неподтверждённый сценарий. Сохранить focused regression and separate fast-Escape timing observation as unresolved.

[Standalone next-step prompt](SITE-QA-13-repair.txt). Application implementation requires a concrete approved scope.
