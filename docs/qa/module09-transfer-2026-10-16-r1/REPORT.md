# Module09 — перенос на другой ПК

2026-10-16. Разрешён пользователем Git-transfer всей накопленной работы; продолжение реализации SOCIAL03 не одобрено.

Целевая ветка: `codex/module09-transfer-2026-10-16-r1`. Основной checkout `task33-progress` и общий index сохраняются. Используется отдельный index и frozen Git tree; main/deploy не затрагиваются. Snapshot содержит также накопленные изменения модулей01–08 и параллельной админской задачи, без переноса на них нового acceptance.

Точка продолжения: [один полный промт](RESUME_PROMPT.txt). SOCIAL01–02 — scoped LOCAL в своих зафиксированных снимках. SOCIAL03 — OPEN, план требует current source/MO recheck и отдельного одобрения до patch. Full ACCEPT09 NOT RUN. Исторические runtime/PID/порты не переносим как рабочие.

[Entry/authorization](entry.json), [проверки упаковки](verification.json). Исходники и QA evidence публикуются WIP-снимком; push не означает release/deployment. Последний записанный параллельный релиз админки описан в ../admin-moderation-release-2026-10-16-r2/REPORT.md, production здесь не проверяется.

Новые ignored .tmp/credentials/env/local DB/cache/private-media/venv и pyc не включаются. Безопасные локальные QA logs после проверки будут включены явно, чтобы ссылки в отчётах работали. Старые уже tracked `.tmp/*.html` являются наследием исходного HEAD; новых runtime данных в .tmp не добавляется.

Full tests не запускались ради переноса. Выполняются file/source inventory, syntax для переносимого application code, контроль секретов/forbidden paths, SHA/PNG integrity и проверка удалённых refs. Снимки старых acceptance остаются привязаны к собственным source manifests.
