# Заявка остаётся открытой после публикации

Follow-up: реализация локально одобрена пользователем и выполнена; итог `docs/reports/publication-and-readiness-2026-10-26.md`. Ниже сохранён исходный audit до реализации.

Дата: 2026-10-26. Исполнитель: /root; bounded BUG audit, без делегирования. Маршрутизация: kidsmap-orchestrator → backend domain. Definition: `.agents/agents/kidsmap-orchestrator/agent.md`.

## Срез и границы

LOCAL HEAD: `1b0acf8c6d03e71d8516cfb92c19018db1426ebf`, branch `codex/admin-draft-recovery-2026-10-26`. WORKTREE содержит чужие изменения, сохранены. Из связанных файлов dirty `domain_admin/place.py` и `services/admin_place_preview.py`; проверенный diff последнего меняет saved-draft preview, не `request_is_stale`.

PRODUCTION: текущий SHA/DB UNKNOWN. Пользовательский скриншот показывает место №351 в ожидающих заявках, статус «На модерации», решение «Ожидает решения» и признак устаревшей заявки. Текущая публичность сообщена пользователем; нового live-подключения не было. Историческая проверка 2026-10-16 подтверждала публикацию №351, но не заменяет текущую проверку.

## PUB-REQUEST-01 — P2, LOCAL source confirmed

`src/catalog/services/publication.py:383` (`review`) одобряет revision, публикует Place и отправляет уведомление. `:451` (`publish`) делегирует review либо публикует Place напрямую. Эти пути не завершают связанную PlaceOwnershipRequest.

Обратный путь `src/catalog/services/organization_ownership.py:185` (`moderate_place_request`) вызывает publish и затем в строках 200–201 завершает заявку и пишет audit. Поэтому публикация через карточку и одобрение через заявку дают разные результаты для статуса заявки.

`src/catalog/services/admin_place_preview.py:182` сравнивает версии заявки с текущими версиями карточки/revision. После публикации прежняя заявка может стать stale, сохранив PENDING. `src/catalog/domain_admin/owner.py:899` отображает статус заявки, а `:1107` и `:1126` считают все PENDING, включая stale. Соответствие конкретной production строки этой причине требует read-only проверки kind/версий/истории решений; по одному скриншоту оно не доказано.

Влияние: лишняя задача модерации и неверный счётчик ожидания. Само наличие опубликованного Place не доказывает одобрение заявки CLAIM на передачу владения.

## Предлагаемый scope для согласования

1. В единой транзакции одобрения карточки завершать только соответствующую PENDING заявку PUBLICATION: тот же владелец, ownership/content/candidate версии, реально одобренный контент. Сохранить модератора, время и audit. Согласовать вызов из moderate_place_request, чтобы избежать повторного решения/audit.
2. Не закрывать CLAIM, заявки другого владельца, новые версии или неоднозначные stale заявки по одному признаку published. Не скрывать проблему фильтром списка.
3. Проверить изолированно: approve через карточку и через заявку; прямую публикацию без pending revision; повторный вызов; другие CLAIM/новые изменения; conflict и rollback; корректность счётчиков и отсутствие дублей audit/уведомлений.
4. Зависшая production заявка №351 — отдельный read-only разбор соответствия старому решению. Коррекция только после подтверждения истории и отдельной авторизации production записи. Deploy не входит в локальную правку.

DB impact: существующие статусы/audit, миграция пока не обоснована. Security: сохраняются проверки reviewer и freshness, владение автоматически не выдаётся.

## Проверки и handoff

EXECUTED: git snapshot/status/diff; graph search/trace; direct source; coverage metadata совпадает для четырёх изученных файлов. Индекс generation `2026-10-26T08:32:39Z`; граф содержит эвристические связи, критические выводы проверены по source.

NOT RUN: Django tests, локальное воспроизведение с DB, rendered browser QA, текущий production DB/public check, commit/push/deploy. Application source не менялся.

Следующий владелец: Django backend, после согласования перечисленного scope — regression reproduction → локальная правка → targeted verification. Основание остановки: пользовательский AGENTS.md требует конкретный план и approval перед реализацией findings.
