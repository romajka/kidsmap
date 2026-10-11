# PLACE-QA-01 — причина отказа отсутствует в редакторе владельца

P2: владелец видит необходимость исправлений, но не замечание модератора. Baseline failure на HEAD 8d188b3; исправления приложения в этом запуске отсутствуют.

Роли: moderator → owner. URL: `/admin/volunteer/review/1/` → `/ru/account/places/1/edit/`.

Шаги: отправить кандидат; модератором указать `QA reason repeat module01` и отклонить; открыть редактор владельцем; reload; войти в новой сессии. Ожидание: причина показана рядом со статусом. Факт: только «Нужны исправления»; текст отсутствует во всех трёх проверках. Read-only наблюдение подтверждает сохранённый review_note.

Доказательства: [повтор](../rejection-recheck.result.txt), [скриншот](../screenshots/rejection-recheck-1440.png), [состояние](../observations.txt). Source: `src/catalog/services/publication.py:408` сохраняет note; `src/catalog/templates/pages/includes/owner_place_continuous.html:7` выводит статус без note. Это подтверждённая связь источника и воспроизведения, а не доказательство дефекта всех остальных экранов.

Scope: сообщение кандидата в редакторе владельца и локализация. Зависимость: действующий lifecycle revision; не подменять его legacy Place.rejection_reason.

## Готовый промпт

```text
В KidsMap исправь PLACE-QA-01 из docs/qa/module01-2026-10-09-r1/findings/PLACE-QA-01.md. Сначала прочитай AGENTS.md и текущие canonical инструкции; сохрани чужие изменения. Scope разрешён только для показа замечания отклонённого кандидата владельцу, применимых шаблонов/локализации и необходимых проверок. Повтори отказ через UI на свежем изолированном DJANGO_TESTING=1 стенде с вымышленными данными. Выведи escaped review_note для соответствующего rejected/declined кандидата, после reload и нового входа. Проверь RU/AZ/EN, mobile/PC, отсутствие раскрытия замечания гостю и чужому владельцу. Сохрани live/candidate и права доступа. Не меняй assertions ради зелёного результата. Дай diff, точные тесты и свежие скриншоты. Без commit/push/deploy/production.
```
