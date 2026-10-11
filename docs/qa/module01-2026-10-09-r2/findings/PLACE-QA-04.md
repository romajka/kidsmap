# PLACE-QA-04 — Район остаётся disabled после очистки точки

OPEN · P2 · PRE-EXISTING BASELINE · local module01-20261009-r2, 2026-10-09. Исправление не выполнено.

**Роль:** owner. **URL/endpoint:** `/ru/account/places/1/edit/` (origin `http://localhost:8813`).

**Шаги:** На свежей форме ввести ручную точку, очистить lat/lng, выбрать регион Baku. Осмотреть district.

**Ожидание:** При ручном выборе региона доступен предусмотренный формой выбор района.

**Факт:** Регион baku выбран, lat/lng пусты, district.disabled=true. Выбрать район нельзя.

**Свежие доказательства:** [district-enable.effective.result.txt](../district-enable.effective.result.txt); [manual-roundtrip.effective.result.txt](../manual-roundtrip.effective.result.txt).

**Первопричина / уверенность:** static/js/location_resolution.js:38–45 и привязки continuous owner form. Пустые координаты отключают district; согласованного пересчёта при ручной смене региона в этом пути не обнаружено. Уверенность высокая по поведению, причинная связь подтверждена source.

**Почему P2:** Ограниченная недоступность обязательной географии после изменения режима ввода.

**Область исправления / зависимости:** Location state machine и owner form bindings; зависит от server geographic policy.

## Самостоятельный промпт исправления

```text
Работай в фактическом checkout KidsMap. Прочитай AGENTS.md, канонические .agents и docs/qa/module01-2026-10-09-r2/findings/PLACE-QA-04.md. Сначала проверь актуальные HEAD/WORKTREE/active_run; сохрани чужие изменения и стенды. Историческое evidence используй как repro checklist, повтори на свежем DJANGO_TESTING=1 стенде с отдельными DB/cache/media/private-media/email и вымышленными данными. Без production credentials, внешних интеграций, commit/push/deploy.

Исправь переход ручная точка → очистка → ручной регион/район в continuous редакторе. Определи единый пересчёт доступности district по актуальным координатам и региону; не обходи серверную проверку простым снятием disabled. Проверь Baku/другой регион, пустую/неполную/неверную точку и reload с сохранённым районом.

Подготовь конкретный план и согласуй scope реализации до изменения приложения согласно каноническим инструкциям. После согласования выполни только этот finding, meaningful regression проверки и rendered browser сохранение/reload. Сохрани новый отчёт, точные команды/exit codes, screenshots и ограничения NOT RUN. Не считай этот audit разрешением на реализацию.
```
