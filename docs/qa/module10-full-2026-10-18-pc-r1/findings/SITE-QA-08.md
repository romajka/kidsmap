# SITE-QA-08 — Общие настройки переполняют мобильный viewport

**OPEN / P2 / LOCAL C:\kidsmap / 2026-10-18.** Execution /root sequential; confidence high for observed local behavior, root mechanism qualified below. No production evidence or app fix.

Evidence/repro: admin-localized-az/en/ru-final.json: actual scrollWidth > viewport; branding/about/footer/empty examples at360/390; some wider cells too. See [raw evidence](../evidence/) and [PNG manifest](../png-manifest.json); JSON row IDs identify exact scripts/roles/language/width and observed/expected checks. All records/files are synthetic owned fixtures.

Source/symbol: `src/catalog/templates/admin/catalog/shared_settings_change_form.html:16; static/admin/css/pages/kidsmap_admin_form_shell.css`.

Root: Rendered form controls/layout exceed available width; a single universal CSS root is not yet proven.

Impact/expected contract: Общие настройки переполняют мобильный viewport; failure checks record intended result and actual values. Priority applies to bounded reproduced behavior, not a production incident.

Owner/dependencies: frontend-admin. Next: Исследовать offending elements/cascade; ограничить ширины и сохранить desktop/sidebar controls, native save on mobile.

[Standalone next-step prompt](SITE-QA-08-repair.txt). Application implementation requires a concrete approved scope.
