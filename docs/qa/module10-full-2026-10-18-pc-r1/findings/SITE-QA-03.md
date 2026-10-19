# SITE-QA-03 — Редактируемый текст контактов не выводится

**OPEN / P2 / LOCAL C:\kidsmap / 2026-10-18.** Execution /root sequential; confidence high for observed local behavior, root mechanism qualified below. No production evidence or app fix.

Evidence/repro: admin-recovery.json: contacts visibleSavedCopy FAIL RU/AZ/EN, saved fields read back. See [raw evidence](../evidence/) and [PNG manifest](../png-manifest.json); JSON row IDs identify exact scripts/roles/language/width and observed/expected checks. All records/files are synthetic owned fixtures.

Source/symbol: `src/catalog/templates/pages/contacts.html:40; src/catalog/views.py:contacts`.

Root: Public template does not render configured site_contacts_text.

Impact/expected contract: Редактируемый текст контактов не выводится; failure checks record intended result and actual values. Priority applies to bounded reproduced behavior, not a production incident.

Owner/dependencies: frontend-reviewer. Next: Согласовать место текста в UI и вывод трёх языков, проверить empty/fallback и реальные save→public.

[Standalone next-step prompt](SITE-QA-03-repair.txt). Application implementation requires a concrete approved scope.
