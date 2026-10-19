# SITE-QA-19 / P2 — hidden CatalogContentSettings editor returns500

**OPEN, LOCAL only. New finding; pre-existing code defect, not caused by SITE15.**

Superuser GET `/admin/catalog/catalogcontentsettings/1/change/` returns500 before shared-template rendering. Native probe: [browser-catalog-probe.json](../evidence/browser-catalog-probe.json). First editor suite retained the failed control (2failed checks) and actual500: [browser-editors.json](../evidence/browser-editors.json). It is not a404, permission denial or passing UI.

Cause: `src/catalog/models/site.py:784` returns lazy gettext from `CatalogContentSettings.__str__`. Python requires a real string; installed Django ModelAdmin calls str(obj) before render_change_form, producing `TypeError: __str__ returned non-string (type __proxy__)`. The same error occurs when calling str(obj) independently of templates. [Bounded proof](../evidence/catalog-baseline.json), [probe source](../catalog_baseline_probe.py).

Model source SHA equals entry1028 cohort; CatalogContentSettingsAdmin class AST equals its original entry-source class. SITE15 changes neither model nor this admin class. This proves the error precedes the current backend/template change, but is not production verification.

Impact: hidden direct admin editor cannot expose its JSON controls. Native checks of those controls beyond the exception are **NOT RUN**. Gallery's shared-template consumer is separately tested and passes. Do not register the hidden editor as working based only on template compilation.

Recommended next work: separate concrete plan and RED test for real-string model representation, localized RU/AZ/EN admin GET/form behavior and JSON preservation; then user scope approval. No model/application fix was applied for this finding.

Count reconciliation: original16OPEN − closed SITE01 − closed SITE15 =14; add new SITE19/P2 =**15currently OPEN (12P2/3P3)**. Historical SITE07/13 NOT REPRODUCED remain outside OPEN count. Module10 full acceptance remains pending; module09 composite LOCAL closure retained.
