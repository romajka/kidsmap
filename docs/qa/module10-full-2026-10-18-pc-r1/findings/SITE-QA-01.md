# SITE-QA-01 — Staff без model permissions меняет глобальный логотип

**OPEN / P1 / LOCAL C:\kidsmap / 2026-10-18.** Execution /root sequential; confidence high for observed local behavior, root mechanism qualified below. No production evidence or app fix.

Evidence/repro: media.json: staff-media-authorization/public-effect/delete: hub200, upload200, delete200; actual public logo changed, missingCSRF403. Fictional staff: is_staff=True, superuser=False, direct permissions0/groups0. See [raw evidence](../evidence/) and [PNG manifest](../png-manifest.json); JSON row IDs identify exact scripts/roles/language/width and observed/expected checks. All records/files are synthetic owned fixtures.

Source/symbol: `src/catalog/domain_admin/site.py:570,975,986,1065`.

Root: Custom changelist and AJAX bypass model permission checks; admin_view only enforces active staff.

Impact/expected contract: Staff без model permissions меняет глобальный логотип; failure checks record intended result and actual values. Priority applies to bounded reproduced behavior, not a production incident.

Owner/dependencies: security-reviewer + django-reviewer. Next: Определить и применить явную модельную политику чтения/изменения для медиахаба и всех upload/delete routes; добавить deny/no-mutation и legitimate-admin tests; сохранить CSRF.

[Standalone next-step prompt](SITE-QA-01-repair.txt). Application implementation requires a concrete approved scope.
