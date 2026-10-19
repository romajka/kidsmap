# SITE-QA-15 — Вторая вкладка молча отменяет первое сохранение

**OPEN / P2 / LOCAL C:\kidsmap / 2026-10-18.** Execution /root sequential; confidence high for observed local behavior, root mechanism qualified below. No production evidence or app fix.

Evidence/repro: concurrency.json two-tab-disjoint-settings: Aphone stored; Bemail saved302 restores old Aphone; original values restored by native form. See [raw evidence](../evidence/) and [PNG manifest](../png-manifest.json); JSON row IDs identify exact scripts/roles/language/width and observed/expected checks. All records/files are synthetic owned fixtures.

Source/symbol: `src/catalog/domain_admin/site.py; src/catalog/models/site.py; src/catalog/templates/admin/catalog/shared_settings_change_form.html:16`.

Root: Full stale ModelForm POST without version/conflict protection. Merge vs409 is a product design decision.

Impact/expected contract: Вторая вкладка молча отменяет первое сохранение; failure checks record intended result and actual values. Priority applies to bounded reproduced behavior, not a production incident.

Owner/dependencies: django-reviewer + frontend-admin. Next: Спланировать version/CAS или safe merge, не теряя Bdraft; добавить two-tab same/disjoint-field regression and native evidence.

[Standalone next-step prompt](SITE-QA-15-repair.txt). Application implementation requires a concrete approved scope.
