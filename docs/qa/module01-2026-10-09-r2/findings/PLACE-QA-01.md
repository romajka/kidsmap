# PLACE-QA-01 — Причина отказа не показана владельцу

OPEN · P2 · PRE-EXISTING BASELINE · local module01-20261009-r2, 2026-10-09. Исправление не выполнено.

**Роль:** owner. **URL/endpoint:** `/ru/account/places/1/edit/; /ru/account/places/2/edit/` (origin `http://localhost:8813`).

**Шаги:** Создать и отправить место через кабинет. Модератор отклоняет с вымышленной причиной. Открыть редактор владельца, reload, выполнить новый вход.

**Ожидание:** Владелец видит сохранённую причину и может исправить заявку.

**Факт:** Статус отказа виден, текст причины отсутствует во всех трёх повторных проверках; revision.review_note заполнен.

**Свежие доказательства:** [rejection-recheck.result.txt](../rejection-recheck.result.txt); [branch-lifecycle-stable.result.txt](../branch-lifecycle-stable.result.txt); [screenshots/owner-rejection-390.png](../screenshots/owner-rejection-390.png); [diagnostic.json](../diagnostic.json).

**Первопричина / уверенность:** src/catalog/templates/pages/includes/owner_place_continuous.html:7; views.py:_place_revision_context; publication.py:review. Контекст revision передаётся, review_note сохраняется, continuous template не выводит причину. Уверенность высокая.

**Почему P2:** Ограниченный сбой обратной связи мешает исправить заявку; потеря самой причины в DB не обнаружена.

**Область исправления / зависимости:** Owner continuous template, локализация и regression проверки отказа. Зависимость: действующая ACL и revision context.

## Самостоятельный промпт исправления

```text
Работай в фактическом checkout KidsMap. Прочитай AGENTS.md, канонические .agents и docs/qa/module01-2026-10-09-r2/findings/PLACE-QA-01.md. Сначала проверь актуальные HEAD/WORKTREE/active_run; сохрани чужие изменения и стенды. Историческое evidence используй как repro checklist, повтори на свежем DJANGO_TESTING=1 стенде с отдельными DB/cache/media/private-media/email и вымышленными данными. Без production credentials, внешних интеграций, commit/push/deploy.

Покажи владельцу последнюю причину отказа в continuous редакторе места, с безопасным экранированием и корректными RU/AZ/EN подписями. Сохрани ACL и жизненный цикл revision. Проверь отказ → reload → logout/login → исправление → повторная отправка в реальном браузере; добавь проверку сохранённой причины. Не меняй остальные экраны.

Подготовь конкретный план и согласуй scope реализации до изменения приложения согласно каноническим инструкциям. После согласования выполни только этот finding, meaningful regression проверки и rendered browser сохранение/reload. Сохрани новый отчёт, точные команды/exit codes, screenshots и ограничения NOT RUN. Не считай этот audit разрешением на реализацию.
```
