# SITE-QA-17 — RU privacy title обрезан на360px

**OPEN / P2 / LOCAL C:\kidsmap / 2026-10-18.** Execution /root sequential; confidence high for observed local behavior, root mechanism qualified below. No production evidence or app fix.

Evidence/repro: supplement-final.json privacy-title-clipping; native png/privacy-ru-360-viewport-final.png; original360 viewport screenshot visually reviewed, width286 scroll364. See [raw evidence](../evidence/) and [PNG manifest](../png-manifest.json); JSON row IDs identify exact scripts/roles/language/width and observed/expected checks. All records/files are synthetic owned fixtures.

Source/symbol: `static/css/pages/legal.css:175; src/catalog/templates/pages/legal.html:38`.

Root: Unbreakable long Russian word exceeds hero content width and is clipped by ancestor overflow.

Impact/expected contract: RU privacy title обрезан на360px; failure checks record intended result and actual values. Priority applies to bounded reproduced behavior, not a production incident.

Owner/dependencies: frontend-reviewer. Next: Спланировать responsive wrapping/type scale preserving long titles and reading; verify360/390/200%-equivalent RU/AZ/EN.

[Standalone next-step prompt](SITE-QA-17-repair.txt). Application implementation requires a concrete approved scope.
