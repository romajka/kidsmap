# ORG-10 — язык подписей организации в админке

Status: COMPLETE LOCAL, 2026-10-08.242 browser checks +90 server tests PASS. Отчёт: docs/qa/org-10-fix-2026-10-08.md. Пользователь поручил следующий пункт сообщением «дальше» после завершённого ORG-09. Только ORG-10, без изменения других findings/правил и commit/push/deploy.

1. Свежий RED: шесть name/description labels OrganizationForm после импорта и последовательного RU/AZ/EN; add/change в одном текущем серверном процессе. Сверить остальных потребителей этих двух msgid, локали и контракты.
2. В business.py сохранить lazy translation при percent-format с существующими msgid и маркерами языков данных AZ/RU/EN. Не менять переводы, fields, права, candidate/save/publication/version rules. Добавить регрессию переключения после импорта, используя реальные формы/HTTP, без mocks.
3. GREEN: целевые i18n/admin/permission/publication tests; rendered add/change RU/AZ/EN на360/390/768/1024/1280/1440, клавиатура; fresh synthetic draft/repeat/stale conflict и denial. Снимки PC/mobile, exact commands/snapshot/diff/PASS/FAIL/NOT RUN, сохранность входных файлов и старых QA data. Production/external integrations не выполнять.
