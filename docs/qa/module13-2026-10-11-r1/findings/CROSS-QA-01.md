# CROSS-QA-01 — перенесённое будущее событие исчезает из организации

P2, подтверждено на локальном изолированном WORKTREE, 2026-10-11. Роль: владелец сети / публичный посетитель. Production NOT RUN. Приёмка организации теряет действующее мероприятие, хотя оно доступно в общей афише и по прямой ссылке; данных не удаляет.

URL: `/ru/account/places/events/1/manage/`, `/ru/events/`, `/ru/event/1-uydurma-qa13-physical-event/`, `/ru/organizations/9a6a35ed-1f5d-44b3-8bc2-5b8d3b68e4a2/` на localhost:8831.

1. Через UI создать организацию, опубликовать место-филиал и мероприятие на 20.10.2026, организатор — эта организация.
2. Открыть публичную организацию: две ссылки на событие, оно входит в секцию мероприятий.
3. Через кабинет перенести событие на 22.10.2026 16:00–17:00 Asia/Baku с причиной.
4. Reload публичной организации, прямой карточки и общей афиши.

Ожидание: будущее действующее перенесённое событие остаётся в мероприятиях своего организатора с актуальной датой.

Факт: организация — 0 ссылок; общая афиша — 4 ссылки; карточка — HTTP200, «Перенесено», новая будущая дата. Осталось онлайн-событие, то есть секция включена.

Доказательства: [native result](../event-cross.result.txt), [до](../screenshots/organization-event-before-1440.png), [после PC](../screenshots/organization-event-after-1440.png), [после mobile](../screenshots/organization-event-after-390.png), [карточка](../screenshots/rescheduled-event-card-1440.png), [snapshot](../snapshot.json).

Причина подтверждена source: `src/catalog/controllers/public_details.py:135` фильтрует только `occurrence_state='scheduled'`; lifecycle устанавливает `rescheduled`. Это разные правила публичных читателей. Регрессионное происхождение UNKNOWN: точный путь на clean HEAD не повторялся; relevant reader source совпадает с HEAD.

Область исправления: общий контракт upcoming/visible Event и reader организации; проверить специалиста-организатора, cancelled/past/deleted/private события и границы времени. Зависимости: lifecycle Event, public visibility, разделы, локализация; миграция не предполагается без анализа.

Самостоятельный промпт: [CROSS-QA-01-repair.txt](CROSS-QA-01-repair.txt).
