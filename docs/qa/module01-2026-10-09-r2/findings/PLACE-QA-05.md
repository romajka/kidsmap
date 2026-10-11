# PLACE-QA-05 — Открытый select категории выходит за экран 360 px

OPEN · P2 · PRE-EXISTING BASELINE · local module01-20261009-r2, 2026-10-09. Исправление не выполнено.

**Роль:** moderator/admin editor. **URL/endpoint:** `/admin/catalog/place/3/change/ (django_language RU/AZ/EN)` (origin `http://localhost:8813`).

**Шаги:** В Chromium viewport 360 px открыть выпадающий выбор категории административного редактора, повторить RU/AZ/EN.

**Ожидание:** Открытый список целиком укладывается в viewport, доступен с клавиатуры.

**Факт:** Ширина document scroll становится 373 px при viewport 360; воспроизведено во всех трёх языках. Другие проверенные ширины этого дефекта не показали.

**Свежие доказательства:** [deep-matrix.result.txt](../deep-matrix.result.txt); [contact-sheets/deep-moderator-open-control.jpg](../contact-sheets/deep-moderator-open-control.jpg); [screenshots/deep-moderator-open-control-ru-360.png](../screenshots/deep-moderator-open-control-ru-360.png).

**Первопричина / уверенность:** static/admin/css/pages/kidsmap_place_form.css:1104–1109: min-width 320 плюс позиционирование. Уверенность высокая по rendered geometry; размеры native popup вне DOM не оценивались.

**Почему P2:** Обязательная мобильная ширина получает горизонтальную прокрутку при выборе категории.

**Область исправления / зависимости:** Admin category popup responsive CSS; зависит от trigger position и длинных labels.

## Самостоятельный промпт исправления

```text
Работай в фактическом checkout KidsMap. Прочитай AGENTS.md, канонические .agents и docs/qa/module01-2026-10-09-r2/findings/PLACE-QA-05.md. Сначала проверь актуальные HEAD/WORKTREE/active_run; сохрани чужие изменения и стенды. Историческое evidence используй как repro checklist, повтори на свежем DJANGO_TESTING=1 стенде с отдельными DB/cache/media/private-media/email и вымышленными данными. Без production credentials, внешних интеграций, commit/push/deploy.

Ограничь ширину и позицию открытого category popup административного редактора доступным viewport без обрезки вариантов. Проверь RU/AZ/EN × 360/390/768/1024/1280/1440, длинные значения, Tab/Shift+Tab/Enter/Escape и фокус после закрытия. Подтверди свежими screenshots и scrollWidth; не делай общий редизайн.

Подготовь конкретный план и согласуй scope реализации до изменения приложения согласно каноническим инструкциям. После согласования выполни только этот finding, meaningful regression проверки и rendered browser сохранение/reload. Сохрани новый отчёт, точные команды/exit codes, screenshots и ограничения NOT RUN. Не считай этот audit разрешением на реализацию.
```
