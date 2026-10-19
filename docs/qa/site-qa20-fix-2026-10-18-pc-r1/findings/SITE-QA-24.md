# SITE-QA-24 — saved message overflows statistics destination at360

**OPEN / P3 / LOCAL, 2026-10-18.** In native9model save acceptance, three analytics `_save` states (AZ/RU/EN,360) correctly POST302→statisticsGET200 with exact data/one log, but document no_overflow fails. Original three failures remain unchanged in [browser-saves](../evidence/browser-saves.json); [RU screenshot](../png/save-siteanalytics-360.png) shows the long brand-linked success message extending right of the viewport.

[Focused native save/dismiss/restore](../evidence/browser-statistics-message.json) records document/alert geometry before and after the real dismiss button, with no style/transport injection, and exact native brand restoration. These positive diagnostic checks are causal measurements, not a replacement for the original three FAIL results. Own extra synthetic logs retained.

Source wiring: src/catalog/domain_admin/site.py:SiteAnalyticsAdmin.changelist_view directly renders templates/admin/catalog/site_analytics.html, which extends admin/base_site.html and has km-statistics-page. The approved changed shared_settings_change_form.html is absent from this destination. Runtime has no settings-editor or settings-hub root there. Dashboard/site.py/base/CSS sources are in1033unchanged current-source hashes. Relevant graph coverage unavailable/metadata_changed; read source is authority. Prepatch native360statistics-toast measurement NOT RUN; pre-existing attribution is inference from unchanged destination/message source and bypass of the modified template, not a claimed historical observation. Existing SITE08 editor and SITE22 hub-only toast scopes remain closed locally.

P3: bounded success notification overflow; valid persistence and allowed navigation work. No production evidence. Owner frontend-admin/analytics-reviewer; next concrete bounded plan for statistics message wrapping/controls, AZ/RU/EN/360–1440/native long-success states and neighbor parity. Do not expand global alert CSS without measuring consumers. No application fix authorized/applied for SITE24.

Module10 now15OPEN(9P2/6P3)=13entry−SITE20+SITE23+SITE24+SITE25. Full module acceptance pending.
