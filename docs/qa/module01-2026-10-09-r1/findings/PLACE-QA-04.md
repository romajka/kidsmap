# PLACE-QA-04 — район остаётся отключён после очистки координат

P2: требуется район Баку, но пользователь не может выбрать его обычным интерфейсом. Baseline failure на HEAD 8d188b3.

Роль owner, `/ru/account/places/create/?fresh=1`.

Шаги: в пустом редакторе ввести точку 40.4093/49.8671; очистить обе ручные координаты; выбрать Баку в region. Ожидание: список районов Баку включён. Факт: region=baku, district='', disabled=true, lat/lng пустые. Повтор на новой форме исключает старый кандидат. Более сложный путь филиала также упирался в географическую валидацию, но его timing-сбои отдельно не считаются дефектами.

Доказательства: [повтор](../district-enable.result.txt), [скриншот](../screenshots/district-disabled-390.png). Source: `static/js/location_resolution.js:38–45`, values('', '') отключает district. В continuous форме не найден соответствующий city-change re-enable; аналогичный legacy wizard handler не загружается этой формой. Корень подтверждён для указанного пути, не для всех форм географии.

Scope: согласование manual region/district с resolver и очисткой; зависимость PLACE-QA-02. Backend geographic validation сохраняется.

## Готовый промпт

```text
В KidsMap исправь PLACE-QA-04 из docs/qa/module01-2026-10-09-r1/findings/PLACE-QA-04.md. Прочитай AGENTS.md и актуальную continuous place форму; сохрани чужие изменения. Scope: синхронизация region/district после ручного изменения, очистки координат и результата location resolver. На fresh DJANGO_TESTING=1 форме повтори enter point → clear pair → choose Baku: район должен стать доступным. Обработай смену региона, empty/error/out-of-country ответы и запоздавший resolver без потери ввода. Не обходи disabled через тестовую DOM-мутацию и не ослабляй серверное согласование города/района. Проверь выбрать район/save/reload, другие регионы, RU/AZ/EN и mobile/PC. Дай meaningful tests и свежие доказательства. Без commit/push/deploy/production.
```
