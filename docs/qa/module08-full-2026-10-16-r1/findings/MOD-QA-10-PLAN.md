# PLAN MOD-QA-10 — язык уведомлений публикации

Новая причина внутри модуля08. P3: AZ/EN получают русский loading toast; AZ дополнительно подтверждён реальный success toast снятия с публикации. Native transport91observations:12localeFAIL при явно SIMULATED ожидании, настоящий UI JS; native-publication.partial содержит actual AZ successFAIL и RU controls. Отдельный renderer stall после AZ publish пока не приписан этой строке/причине.

Источник: static/admin/js/kidsmap_place_changelist.js, executeTogglePublication —2loading и2success literals. Ранее MOD06 был принят в ограниченном scope confirmation, его отчёт явно не принимал actual action/toasts. Данные/ACL/confirm/egress менять не требуется.

Точный scope6files:
1. static/admin/js/kidsmap_place_changelist.js: в executeTogglePublication использовать4server-provided labels вместо literals; безопасная подстановка name функцией replace, прежний RU fallback. Не менять fetch/URL/CSRF/row state/loading/error/retry/quick action semantics.
2. src/catalog/templates/admin/catalog/place/change_list.html:4новых data-атрибута существующего km-changelist-i18n с translate/blocktranslate и %(name)s.
3–5. locale/ru/LC_MESSAGES/django.po, locale/az/LC_MESSAGES/django.po, locale/en/LC_MESSAGES/django.po:4соответствующие записи. RU сохраняет текущие формулировки, AZ/EN переведены; placeholders совпадают.
6. NEW src/catalog/testcases/test_mod_publication_toast_localization.py: actual authenticated changelist отдаёт локализованные labels RU/AZ/EN и безопасный name placeholder. Сначала meaningful RED. Existing assertions не менять.

[Фактический proposed diff пяти существующих файлов](MOD-QA-10-proposed.diff), [SHA/unapplied manifest](MOD-QA-10-manifest.json). Candidate вне приложения; JS/templates/PO не изменены. Если одобрены одновременно09/10, менять разные PO entries patch-ами; не копировать целый candidate поверх другого одобренного изменения.

После approval: только новая regression группа+existing targeted publication/confirmation guards. Fresh own3MO build/manifest доsetup; real browser RU/AZ/EN×6widths с loading(явно delayed transport), unpublish/publish success на собственных фикстурах, имя с кавычками/HTML-like вводом; guards/retry/error/reload, PNG/diagnostics/domain conservation кроме ожидаемых собственных переходов. Незавершённый AZ renderer case сначала отделить и разобраться; он не получает молчаливого исправления этим планом. Полный неизменённый ACCEPT-08 повторно не запускать. Новый scope требует одобрения.
