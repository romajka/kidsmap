# SITE-QA-14 — После обрыва POST нет восстановления черновика

**OPEN / P2 / LOCAL C:\kidsmap / 2026-10-18.** Execution /root sequential; confidence high for observed local behavior, root mechanism qualified below. No production evidence or app fix.

Evidence/repro: concurrency.json transport-failure; last-controls.json draft-recovery-recheck: noServerWrite/dbUnchanged, native error/Back/reopen loses entered fictional text. See [raw evidence](../evidence/) and [PNG manifest](../png-manifest.json); JSON row IDs identify exact scripts/roles/language/width and observed/expected checks. All records/files are synthetic owned fixtures.

Source/symbol: `src/catalog/templates/admin/catalog/shared_settings_change_form.html:16`.

Root: SSR form navigation with no persisted draft recovery. Simulated route abort; actual network outage not tested.

Impact/expected contract: После обрыва POST нет восстановления черновика; failure checks record intended result and actual values. Priority applies to bounded reproduced behavior, not a production incident.

Owner/dependencies: frontend-admin. Next: Согласовать bounded draft recovery/retry UX и confidential-field policy; не скрывать transport failure и не писать черновик в production без дизайна.

[Standalone next-step prompt](SITE-QA-14-repair.txt). Application implementation requires a concrete approved scope.
