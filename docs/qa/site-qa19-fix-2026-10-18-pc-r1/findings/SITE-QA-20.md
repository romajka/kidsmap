# SITE-QA-20 — readonly catalog editor offers active Save buttons

**OPEN / P3 / LOCAL, 2026-10-18.** Newly reachable after SITE19's model representation is fixed. Existing shared-template defect, not a server permission bypass; no production evidence.

Fictional staff fixture has only `catalog.view_catalogcontentsettings`. GET200 renders readonly JSON (no textarea) but both enabled Save buttons remain visible at1440. In RU/AZ/EN, native “Save and continue” click submits the real form and ends at403. JSON/updated_at/admin-log state remains unchanged. [Native evidence](../evidence/browser-viewer-defect.json):3rows/3intended hidden-control failures,6permission/no-write controls PASS; [matrix](../evidence/browser-matrix.json) also records both controls' visibility/enabled state. PNGs `viewer-defect-{az,ru,en}-before.png` and `-403.png` show both stages.

Source: `src/catalog/templates/admin/catalog/shared_settings_change_form.html` unconditional `_continue`/`_save` buttons; context already has `has_change_permission`. Template SHA equals this fix entry cohort. Model/admin permissions are unchanged;105server tests include viewer POST403. SITE01's server permission closure is retained.

Impact: a view-only user is invited to a forbidden action instead of receiving a consistent readonly editor. P3 usability/authority presentation, not unauthorized write/data disclosure. Confidence high for rendered behavior; source condition absent is verified.

Owner: frontend-admin with Django permission regression checks. Next: separate concrete plan for shared consumers' readonly/change/add action visibility and native RU/AZ/EN/direct POST denial. No template fix is approved or applied here. Keep SITE19 closure separate.

Count:14entry OPEN − SITE19/P2 closure + SITE20/P3 + SITE21/P2 =**15OPEN (11P2/4P3)**. SITE21 has its own evidence; SITE08/SITE11 remain open.
