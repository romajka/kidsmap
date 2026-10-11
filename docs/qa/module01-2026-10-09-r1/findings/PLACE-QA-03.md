# PLACE-QA-03 — проекция цены создаёт конфликт собственного кандидата

P1: модератор не может одобрить корректное изменение опубликованного места; available action остаётся отказ. Baseline failure на HEAD 8d188b3.

Роли owner/moderator; `/ru/account/places/1/edit/` → `/admin/volunteer/review/1/`.

Шаги: создать и одобрить самостоятельное место с билетом 15; владельцем изменить RU-название/адрес, schedule_mode и билет на 18; явно сохранить; reload; отправить из свежей сессии. Ожидание: немедленные изменения доступны live, остальные можно одобрить; реальный конкурентный конфликт защищён. Факт: live цена 18 и расписание обновились, название/адрес остались прежними; reviewer показывает «Карточка изменилась после отправки» без approve. Другой пользователь live не редактировал. Read-only состояние: candidate_base_mismatch_keys = price_from, price_to.

Доказательства: [candidate/live](../published.result.txt), [свежая отправка](../resubmit-diagnose.result.txt), [review](../review-inspect.result.txt), [скриншот](../screenshots/review-published-error-1440.png), [наблюдение](../observations.txt).

Source-supported причина: `publication.py:354–357` обновляет base только для immediate keys. `replace_place_pricing_plans` / `sync_legacy_price_fields` (`pricing_plans.py:354,603`) также меняют зависимые scalar price_from/to. Эти проекции остаются с прежним base в кандидате. `_apply` уже вызывает refresh_from_db (`publication.py:300`); отсутствие refresh не является причиной. `volunteer_places.py` проверяет base строгим сравнением и честно блокирует конфликт. Точный способ исправления требует проектирования согласованного rebasing, не отключения guards.

Scope: publication base/pending и производные цены; зависимости pricing plans/signals, candidate/live и CAS. Организации/занятия целиком не входят в scope.

## Готовый промпт

```text
Исправь PLACE-QA-03 из docs/qa/module01-2026-10-09-r1/findings/PLACE-QA-03.md. Прочитай AGENTS.md и текущий контракт publication/pricing, сохрани чужие изменения. Scope: согласованность base snapshot/pending после немедленного обновления pricing plans и производных price_from/to, плюс необходимые тесты. Сначала воспроизведи через UI опубликованное место: билет15 → билет18 вместе с изменением identity/address и расписания; save/reload/submit/review. Спроектируй атомарное согласование производных полей с base, сохраняя модерацию identity и реальные конкурентные конфликты. Не убирай conflict guards и не добавляй обход approve. Добавь meaningful regression test и отрицательный двухпользовательский конфликт. На свежем DJANGO_TESTING=1 стенде проверь live/candidate, approve и public после reload. Дай diff, exact commands/results и свежие screenshots. Без commit/push/deploy/production.
```
