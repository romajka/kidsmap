# SITE-QA-16 — Вложенные main на legal/listing pages

**OPEN / P3 / LOCAL C:\kidsmap / 2026-10-18.** Execution /root sequential; confidence high for observed local behavior, root mechanism qualified below. No production evidence or app fix.

Evidence/repro: public-az/ru/en.json:54oneMain FAIL across privacy/terms/listingRules×3langs×6widths. See [raw evidence](../evidence/) and [PNG manifest](../png-manifest.json); JSON row IDs identify exact scripts/roles/language/width and observed/expected checks. All records/files are synthetic owned fixtures.

Source/symbol: `src/catalog/templates/pages/legal.html:114; src/catalog/templates/pages/listing_rules.html:328`.

Root: Inner main inside inherited base main duplicates primary landmark.

Impact/expected contract: Вложенные main на legal/listing pages; failure checks record intended result and actual values. Priority applies to bounded reproduced behavior, not a production incident.

Owner/dependencies: frontend-reviewer. Next: Заменить только внутренние landmark tags без visual/layout/SEO/text changes; проверить DOM all3langs×6widths.

[Standalone next-step prompt](SITE-QA-16-repair.txt). Application implementation requires a concrete approved scope.
