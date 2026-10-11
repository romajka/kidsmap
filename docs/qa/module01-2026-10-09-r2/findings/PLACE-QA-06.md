# PLACE-QA-06 — Скомпилированные переводы этого WORKTREE устарели

OPEN · P2 · ENVIRONMENT FAILURE — GENERATED ARTIFACT STALENESS · local module01-20261009-r2, 2026-10-09. Исправление не выполнено.

**Роль:** admin editor. **URL/endpoint:** `/admin/catalog/place/3/change/ (django_language AZ/EN)` (origin `http://localhost:8813`).

**Шаги:** Запустить свежую isolated DB с текущими locale/*.mo. Открыть AZ/EN административный редактор; сравнить targeted GNUTranslations lookup с соответствующими .po.

**Ожидание:** Запущенные каталоги соответствуют текущему переводному source: Description/Təsvir для описания, перевод сообщения карты.

**Факт:** html lang правильный, но label описания Cədvəl/Schedule, сообщение карты русское. В .po нужные значения уже правильные; игнорируемые .mo содержат старые значения/не содержат ключ предупреждения.

**Свежие доказательства:** [compiled-translations.json](../compiled-translations.json); [localization.result.txt](../localization.result.txt); [screenshots/localization-admin-az-390.png](../screenshots/localization-admin-az-390.png); [screenshots/localization-admin-en-390.png](../screenshots/localization-admin-en-390.png); [snapshot.json](../snapshot.json).

**Первопричина / уверенность:** locale/az/LC_MESSAGES/django.mo, locale/en/LC_MESSAGES/django.mo; config LOCALE_PATHS. Подтверждены GNUTranslations lookup, source .po и git ignore. Уверенность высокая; это не доказательство дефекта текущих .po или production.

**Почему P2:** Локальная сборка неверно подписывает поле и смешивает языки; граница finding ограничена фактически работающими compiled assets.

**Область исправления / зависимости:** Локальная build/stand preparation для переводов. Зависимость: gettext tooling и manifest compiled assets.

## Самостоятельный промпт исправления

```text
Работай в фактическом checkout KidsMap. Прочитай AGENTS.md, канонические .agents и docs/qa/module01-2026-10-09-r2/findings/PLACE-QA-06.md. Сначала проверь актуальные HEAD/WORKTREE/active_run; сохрани чужие изменения и стенды. Историческое evidence используй как repro checklist, повтори на свежем DJANGO_TESTING=1 стенде с отдельными DB/cache/media/private-media/email и вымышленными данными. Без production credentials, внешних интеграций, commit/push/deploy.

В отдельном согласованном запуске подготовь актуальные compiled каталоги из текущих .po в изолированном стенде, зафиксируй source/asset hashes и повтори PLACE-QA-06 в реальном RU/AZ/EN браузере. Определи воспроизводимый build шаг, предотвращающий stale .mo. Не переписывай правильные .po, не меняй чужие compiled assets и не выполняй production/deploy.

Подготовь конкретный план и согласуй scope реализации до изменения приложения согласно каноническим инструкциям. После согласования выполни только этот finding, meaningful regression проверки и rendered browser сохранение/reload. Сохрани новый отчёт, точные команды/exit codes, screenshots и ограничения NOT RUN. Не считай этот audit разрешением на реализацию.
```
