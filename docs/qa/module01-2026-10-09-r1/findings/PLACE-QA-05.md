# PLACE-QA-05 — список категорий админки выходит за экран 360 px

P2: правые подписи/счётчики popup обрезаны, появляется горизонтальное переполнение. Baseline failure на HEAD 8d188b3.

Роль moderator/admin; `/admin/catalog/place/3/change/`. Шаги: viewport 360×950; открыть category picker. Ожидание: popup укладывается в viewport. Факт: scrollWidth=373 при viewport=360; воспроизведено RU/AZ/EN. Остальные проверенные ширины 390/768/1024/1280/1440 проходят этот geometry check.

Доказательства: [72 admin cells](../deep-admin-final.result.txt), [RU screenshot](../screenshots/deep-moderator-open-control-ru-360.png), [все языки](../contact-sheets/deep-moderator-open-control.jpg), [matrix](../matrix.csv). Source: `static/admin/css/pages/kidsmap_place_form.css:1104–1109`, min-width:320px у popup плюс левый отступ родителя даёт right=373. Исходник согласуется с rendered измерением.

Scope: responsive placement/width category popup. Зависимости picker keyboard/focus; бизнес-правила категорий без изменений.

## Готовый промпт

```text
Исправь PLACE-QA-05 из docs/qa/module01-2026-10-09-r1/findings/PLACE-QA-05.md в KidsMap. Прочитай AGENTS.md и применимые UI skills; сохрани чужие изменения. Разрешён scope CSS/placement административного category popup и необходимые UI проверки. Повтори RU/AZ/EN на360 px и устрани выход списка за viewport без обрезания содержимого. Ограничь ширину/позицию с учётом родителя и viewport. Сохрани keyboard navigation, Enter/Space/Escape, видимый focus и выбор категории. Проверь 360/390/768/1024/1280/1440, длинные labels, пустую/заполненную форму и открытый popup в реальном браузере. Дай screenshots и geometry evidence, не меняй business rules. Без commit/push/deploy/production.
```
