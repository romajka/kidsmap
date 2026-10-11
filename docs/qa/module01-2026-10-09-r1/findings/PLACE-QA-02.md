# PLACE-QA-02 — кнопки карты владельца без SDK ничего не делают

P2: при честном сообщении «Карта недоступна» активные «Очистить» и «Моя геопозиция» не выполняют действие и не дают обратной связи. Baseline failure на HEAD 8d188b3.

Роль owner; `/ru/account/places/2/edit/`, секция адреса. SDK намеренно отсутствует в изолированном стенде.

Шаги: вручную ввести 40.4093/49.8671; нажать очистку мышью/клавиатурой; нажать геопозицию. Ожидание: очистка очищает пару; геопозиция сообщает результат/отказ/недоступность. Факт: значения и статус не меняются. Ручные поля доступны; поиск карты отключён.

Доказательства: [детерминированный повтор](../map-recheck.result.txt), [скриншот](../screenshots/map-no-sdk-recheck-390.png). Source: `static/js/owner_place_map_picker.js`, `initMapPicker`: ветка без provider выставляет placeholder/search disabled и не связывает clear/locate; binding геолокации расположен в ветках SDK. Административный fallback отдельно прошёл simulated denial/unsupported/granted; это другой UI.

Scope: provider-independent очистка и обратная связь геолокации owner; зависимость location resolver. Real external SDK/GPS здесь NOT RUN.

## Готовый промпт

```text
Исправь PLACE-QA-02 из docs/qa/module01-2026-10-09-r1/findings/PLACE-QA-02.md в KidsMap. Прочитай AGENTS.md, сохрани чужие изменения. Разрешён scope owner map fallback, очистки ручной пары, геолокации и связанных проверок. На изолированном DJANGO_TESTING=1 стенде отключи SDK и воспроизведи активные бездействующие кнопки. Свяжи очистку и поддерживаемую геолокацию независимо от provider; показывай локализованный отказ/недоступность, сохраняя ввод. Не выдавай simulated GPS за реальный. Проверь mouse/Enter/Space, reload, RU/AZ/EN, отсутствие SDK и штатную SDK-ветку там, где доступна. Согласуй с location resolver, не ослабляй серверную проверку координат. Дай тесты и свежие mobile/PC screenshots. Без commit/push/deploy/production.
```
