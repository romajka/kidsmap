# PLACE-QA-07 — Тип места остаётся русским в AZ/EN

OPEN · P3 · PRE-EXISTING BASELINE — SOURCE TRANSLATION GAP · local module01-20261009-r2, 2026-10-09. Исправление не выполнено.

**Роль:** owner. **URL/endpoint:** `/az/account/places/1/edit/; /en/account/places/1/edit/` (origin `http://localhost:8813`).

**Шаги:** Открыть выбор типа места в AZ/EN кабинете владельца, прочитать варианты business/public space; сверить gettext ключи в source каталогах.

**Ожидание:** UI choices переведены на выбранный язык; enum значения неизменны.

**Факт:** В обоих языках варианты «Бизнес» и «Общественное место». В RU корректно. Для этих msgid нет записей в AZ/EN .po и .mo.

**Свежие доказательства:** [edge-cases.result.txt](../edge-cases.result.txt); [compiled-translations.json](../compiled-translations.json).

**Первопричина / уверенность:** src/catalog/forms.py:1042–1044 gettext choices, locale AZ/EN .po. В отличие от 06, простой rebuild не добавит отсутствующий source перевод. Уверенность высокая.

**Почему P3:** Небольшая локализационная несогласованность, не блокирует сохранение.

**Область исправления / зависимости:** AZ/EN gettext entries для nature choices; зависит от согласованного rebuild каталога.

## Самостоятельный промпт исправления

```text
Работай в фактическом checkout KidsMap. Прочитай AGENTS.md, канонические .agents и docs/qa/module01-2026-10-09-r2/findings/PLACE-QA-07.md. Сначала проверь актуальные HEAD/WORKTREE/active_run; сохрани чужие изменения и стенды. Историческое evidence используй как repro checklist, повтори на свежем DJANGO_TESTING=1 стенде с отдельными DB/cache/media/private-media/email и вымышленными данными. Без production credentials, внешних интеграций, commit/push/deploy.

Добавь корректные AZ/EN переводы двух nature choices «Бизнес» и «Общественное место», сохрани enum и бизнес-логику. В изолированном стенде собери каталоги и проверь реальные select варианты RU/AZ/EN, сохранение и reload; не заменяй значения enum переводными строками.

Подготовь конкретный план и согласуй scope реализации до изменения приложения согласно каноническим инструкциям. После согласования выполни только этот finding, meaningful regression проверки и rendered browser сохранение/reload. Сохрани новый отчёт, точные команды/exit codes, screenshots и ограничения NOT RUN. Не считай этот audit разрешением на реализацию.
```
