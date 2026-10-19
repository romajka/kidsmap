# SITE-QA-06 — Повреждённый PNG принят и ломает публичный logo

**OPEN / P2 / LOCAL C:\kidsmap / 2026-10-18.** Execution /root sequential; confidence high for observed local behavior, root mechanism qualified below. No production evidence or app fix.

Evidence/repro: media.json invalid-png-rejected: status200/successTrue; filename invalid.png, native public naturalWidth0. Valid logo restored. See [raw evidence](../evidence/) and [PNG manifest](../png-manifest.json); JSON row IDs identify exact scripts/roles/language/width and observed/expected checks. All records/files are synthetic owned fixtures.

Source/symbol: `src/catalog/domain_admin/site.py:986-1012`.

Root: Direct file assignment/save bypasses image content validation.

Impact/expected contract: Повреждённый PNG принят и ломает публичный logo; failure checks record intended result and actual values. Priority applies to bounded reproduced behavior, not a production incident.

Owner/dependencies: django-reviewer + security-reviewer. Next: Проверять фактическое содержимое/форматы/размеры до сохранения; rollback unchanged media on rejection; сохранить согласованную SVG policy.

[Standalone next-step prompt](SITE-QA-06-repair.txt). Application implementation requires a concrete approved scope.
