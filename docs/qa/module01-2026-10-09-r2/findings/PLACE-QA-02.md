# PLACE-QA-02 — Кнопки карты владельца молчат без SDK

OPEN · P2 · PRE-EXISTING BASELINE · local module01-20261009-r2, 2026-10-09. Исправление не выполнено.

**Роль:** owner. **URL/endpoint:** `/ru/account/places/1/edit/` (origin `http://localhost:8813`).

**Шаги:** Открыть карту без внешнего SDK. Ввести вручную 40.4093 / 49.8671. Нажать очистку и определение местоположения.

**Ожидание:** Очистка работает без провайдера; недоступность геолокации/SDK получает понятную обратную связь.

**Факт:** Оба действия оставляют координаты и статус без изменения. Две свежие проверки FAIL.

**Свежие доказательства:** [map-recheck.result.txt](../map-recheck.result.txt); [owner-coordinate-roundtrip.effective.result.txt](../owner-coordinate-roundtrip.effective.result.txt); [deep-matrix.result.txt](../deep-matrix.result.txt).

**Первопричина / уверенность:** static/js/owner_place_map_picker.js:initMapPicker и provider initializers. В unavailable fallback отключается поиск, но обработчики clear/locate остаются внутри provider initialization. Уверенность высокая.

**Почему P2:** Ручной сценарий зависит от внешнего SDK, хотя координаты уже введены; ограниченное нарушение управления формой.

**Область исправления / зависимости:** Owner map picker; общий контракт location resolution. Зависимость: серверная проверка координат.

## Самостоятельный промпт исправления

```text
Работай в фактическом checkout KidsMap. Прочитай AGENTS.md, канонические .agents и docs/qa/module01-2026-10-09-r2/findings/PLACE-QA-02.md. Сначала проверь актуальные HEAD/WORKTREE/active_run; сохрани чужие изменения и стенды. Историческое evidence используй как repro checklist, повтори на свежем DJANGO_TESTING=1 стенде с отдельными DB/cache/media/private-media/email и вымышленными данными. Без production credentials, внешних интеграций, commit/push/deploy.

Сделай очистку ручных координат и понятный ответ на запрос геолокации независимыми от SDK карты. Сохрани серверные ограничения географии и не подставляй 0/0. Проверь отсутствие/позднюю загрузку SDK, отказ и отсутствие geolocation, ручную точку → clear → reload, видимый статус и сохранность других полей.

Подготовь конкретный план и согласуй scope реализации до изменения приложения согласно каноническим инструкциям. После согласования выполни только этот finding, meaningful regression проверки и rendered browser сохранение/reload. Сохрани новый отчёт, точные команды/exit codes, screenshots и ограничения NOT RUN. Не считай этот audit разрешением на реализацию.
```
