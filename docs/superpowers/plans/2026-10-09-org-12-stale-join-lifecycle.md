# ORG-12 — восстановление устаревшего запроса: план реализации

> Для исполнителя: выполнять последовательно по чекбоксам после согласования этого lifecycle пользователем. Subagents и commit не требуются и не разрешены этим планом.

**Статус:** COMPLETE LOCAL. План согласован пользователем сообщением «дальшн»; реализация и свежие проверки выполнены 2026-10-09.
**Goal:** дать владельцам безопасно отменить старый business join и начать новый с актуальной версией и новыми согласиями.
**Architecture:** canonical cancel_join + существующий request_join/confirm_join; два явных действия вместо автоматической замены. Существующий canceled сохраняет историю; новые состояния/колонки не нужны.
**Tech Stack:** текущий Django/PostgreSQL, существующие HTML forms/JSON API, RU/AZ/EN.
**Spec:** docs/qa/organization-deep-audit-2026-10-08/prompts/org-12.md.

## Свежая проверка и границы

2026-10-09, Codex primary /root, роли orchestrator/Django/security/UI выполнены последовательно; независимых исполнителей не запускали. LOCAL HEAD2da9d33abbc53d1ac71bcb7e15a0170bef6277d5/task33-progress, dirty WORKTREE. Стенд QA8788 после ORG11 имеет source2761 dbaa521711d81ab777802bdb9c70a9f9e9caa7d95f673fe87fe460e9e9e17618; эту версию нельзя переносить на production.

Команда свежего воспроизведения:

```bash
.venv/bin/python .tmp/org12-plan-20261009/run.py --script probe.py
```

DJANGO_TESTING=1, guarded isolated PostgreSQL/cache/media/email, внешние интеграции запрещены. Synthetic organization/place/request и preview созданы внутри транзакции, откатившейся в конце. Изменение content_version — только fixture-имитация сохранения. Результат: confirm_org, confirm_place и request_again → ValidationError `Request is stale.`; запрос pending; связи нет; preview manual_review. Доказательства: docs/qa/org-12-plan-2026-10-09/evidence/probe.json и probe.py. Браузерное воспроизведение и новый UI пока NOT RUN.

Первопричина: request_join заменяет pending при несовпадении владельцев/ownership_version; content_version туда не входит. _confirm правильно запрещает старую версию. _decision превращает такую строку в manual_review, без cancel транспорта. Это fail-closed защита, которую надо сохранить.

## Правила, предлагаемые к согласованию

1. Только business pending. Текущий прямой владелец места или организации может отменить запрос. Сотрудник, прежний владелец и посторонний не получают это право. Informational связи/модераторские согласования не включаются в этот scope.
2. Отмена меняет только request: status=canceled, decided_at/by и note с фиксированной причиной отмены. Место не отсоединяется и не меняется; общие программы, фото, цены, расписания, grants сохраняются. Approved нельзя отменить этим действием — для существующей связи остаётся detach с последствиями.
3. Отмена доступна и для устаревшего pending; актуальность old content не нужна для прекращения запроса. Текущие стороны/права проверяются заново под блокировкой. Архив организации или deleted place не должны мешать безопасному прекращению pending; read visibility при этом не расширяется.
4. Старые timestamps согласий остаются в canceled записи для истории. Никакого переиспользования или стирания истории.
5. «Новый запрос» — отдельная кнопка после отмены. Она ведёт в существующий поиск/preview подключения. Перед созданием заново проверяются доступность карточки, владельцы, ownership/content versions, другая сеть и programs. Новая запись получает новые bases; оба confirmation timestamps исходно NULL.
6. request_join подтверждает сторону инициатора по существующим правилам. Для разных владельцев второе согласие получается отдельно; если один текущий владелец владеет обеими сторонами, сохраняется существующий сценарий подтверждения обеих сторон. Новых прав не возникает.
7. У private карточки может исчезнуть доступность после отмены старого согласия. В таком случае владелец сети не получает название/адрес/новый запрос по ID. Продолжить должен текущий владелец места через свой кабинет; его новое согласие снова открывает только существующий допустимый путь. Автоматически восстанавливать старый доступ запрещено.
8. request_join/confirm_join по старому stale ID продолжают запрещаться. Никакого auto-cancel, auto-retry, переноса сети или неявного сохранения старого согласия.

## Транспорт и CAS

Canonical interface:

```python
cancel_join(*, actor, request_id, expected_state) -> OrganizationPlaceRequest
```

expected_state — подписанный сервером, ограниченный временем30минут снимок для actor+request_id; включает request status/bases/confirmation timestamps и текущие parent owner IDs/ownership/content versions, archive/delete flags. GET/read только выдаёт токен; POST проверяет его под блокировкой. Клиент не определяет авторитетную версию сам. Использовать существующий signing pattern проекта; токены не сохранять в evidence.

Lock order: Organization → Place → OrganizationPlaceRequest, как canonical join; cancellation-helper допускает archived/deleted родители, но не выполняет link mutation. Проверка current side owner обязательна даже на replay. CAS mismatch →409, ничего не отменять, предложить перечитать запрос. UI содержит новый токен после reload. Confirmation и cancellation сериализуются теми же locks: победивший approved не отменяется, победивший canceled не подтверждается.

Idempotency: повтор того же cancel с валидным actor-bound токеном на уже canceled request возвращает200/canceled без новых side effects; текущие права проверяются вновь. Если другая вкладка создала новый pending, повтор старого cancel касается только старого ID. Нельзя автоматически отменять найденный «последний pending».

HTML: POST `/account/organizations/<org_id>/requests/<request_id>/cancel/`, CSRF + expected_state; отсутствие/неверный токен →400, конфликт→409. Результат PRG, no-JS работает. При недоступной организации возврат на собственный кабинет с нейтральным сообщением; не раскрывать private metadata в ошибке/redirect.

JSON: новая additive action `cancel-join` в существующем organization_ownership_action, target_type=place; target_id, как confirm-join, означает request ID; body строго `{expected_state}`. Ответ только `{request_id,status}`, без place/org metadata.403 forbidden,404 missing,400 malformed,409 request_conflict/already_approved. GET ничего не отменяет. Текст RU/AZ/EN в UI; API errors — стабильные codes. Старые actions/payloads и их status codes сохраняются.

Recovery read: общий helper строит stale/cancel capability + token только текущим владельцам. Для невидимой карточки выдаёт нейтральную строку «Запрос к недоступной карточке» и cancel control, без названия, адреса, public URL, фото. В owner place кабинете показывать запрос к его месту, не требуя доступа к private организации; её metadata также проверять отдельно.

Connections search/preview: для stale строки сохранять неисполняемость, добавить recovery_required/can_cancel только разрешённой стороне. Cancellation не выполняется массовой кнопкой подключения; ссылка открывает просмотр конкретного запроса. Старые preview snapshots изменяются после cancel/new request и получают прежний conflict; нужен новый preview/key.

## Совместимость и миграции

- Схемная/data migration не планируется: canceled,decided_at/by,note и conditional pending unique уже существуют.
- Старые pending не исправляются пакетно и не удаляются; stale определяется при чтении. Владельцы явно отменяют выбранную запись.
- Старые клиенты продолжают получать отказ на stale и не начинают автоматически новый запрос. Новый сервер добавляет только cancel action; новый UI не обещает поддержку на старом сервере.
- Уже approved/rejected/canceled records и informational flow неизменны. Текущая автоматическая замена после ownership changes не расширяется на content changes.
- Новое уведомление/email в scope не входит. Прежние join_confirmation/join_approved сохраняются; canceled запрос не может быть подтверждён по старому уведомлению.

## PC/mobile — предлагаемый интерфейс

PC: одна строка/карточка в «Запросы на подключение»: название при наличии ACL, статус «Карточка изменена», пояснение «Старое согласие больше не действует. Отмените запрос и создайте новый», кнопка «Отменить запрос». Отдельное inline подтверждение «Отмена не отсоединяет место и не удаляет данные» → «Подтвердить отмену»/«Назад». После успеха status «Запрос отменён» + отдельная «Создать новый запрос» при допустимом доступе.

Mobile360/390: та же карточка в одну колонку; действия на отдельных строках, минимум44px; длинное название переносится. Ошибка409 остаётся рядом с действием: «Запрос изменился. Обновите сведения», отдельная кнопка reload. Никаких горизонтальных таблиц. Статус сохранения/ошибка в role=status/alert, pending button disabled во время POST, фокус после ответа переносится на итог/ошибку; все действия native buttons/links, без обязательного JS. Скрытая metadata не появляется в aria/text/data attrs.

## Файлы и шаги реализации после согласования

- [ ] RED regression: создать src/catalog/testcases/test_organization_join_recovery.py. Проверить stale cancellation/new request/new confirmations, approved refusal, foreign/employee/former owner, private metadata, cancel replay, concurrent confirm/cancel, CAS ownership/content change, archive/delete cancellation, informational refusal. До правки отсутствующий безопасный recovery должен давать FAIL; нельзя менять assertions ради green.
- [ ] Canonical service src/catalog/services/organization_ownership.py: отдельный cancel_join/recovery snapshot helper. Сохранить request_join/confirm_join/_apply_link/access gates. Никакого прямого присвоения organization_id.
- [ ] Transport src/catalog/controllers/organization_ownership_api.py, organization_workspace.py, src/catalog/urls.py: строго POST/CSRF/state, safe response, no-JS PRG. Тесты real HTTP JSON/HTML и неверных методов/CSRF/extra fields.
- [ ] src/catalog/services/organization_connections.py: additive recovery hints, nonexecutable stale; существующие snapshot/idempotency guards сохраняются. Проверить old preview after cancel/re-request→conflict, partial batch outcome/repeat.
- [ ] src/catalog/templates/pages/organization_workspace.html + новый shared organization_join_recovery.html; интеграция в существующий owner place editor после проверки его действительного include-point (поиск owner_place_edit/controller — не делать второй cabinet flow). src/catalog/templates/pages/organization_connections.html/static/js/organization_connections.js: ссылка recovery и список conflicts. CSS только локальные responsive/focus/loading rules. Новые строки RU/AZ/EN; существующие locale duplicate defects не исправлять попутно.
- [ ] Rendered RED/GREEN и acceptance: RU/AZ/EN×360/390/768/1440, owner каждой стороны/employee/outsider, PC/mobile screenshots, keyboard/no-JS, две вкладки, network lost-response/replay, недоступная private карточка. Не выдавать browser accessibility role/name за реальный screen reader.
- [ ] Fresh targeted server: organization ownership/workspace/connections/permissions + новый recovery module; exact module list определить через rg --files src/catalog/testcases перед запуском. Guarded runners клонировать из org11; DJANGO_TESTING=1, отдельная тестоваяDB, locmem, no external. Сохранить входной WORKTREE snapshot и old/new domain hashes, source/runtime manifest; full suite только при обоснованной необходимости.
- [ ] Финальный отчёт: local diff только относительно входного WORKTREE, команды/exit/results/PASS/FAIL/NOT RUN, screenshots, проверка старых gallery/activity/groups/prices/schedule/access неизменны, active_run NONE. Без commit/push/deploy/production.

## Приёмка lifecycle

| Сценарий | Ожидаемый пользовательский результат |
|---|---|
| Content изменился после первого согласия | Старое подтверждение запрещено; видна причина и отмена |
| Cancel→новый request, разные owners | Старый canceled сохранён; новая версия, подтверждена только сторона инициатора |
| Вторая сторона подтверждает новый request | Canonical link создан, старые файлы/зависимости сохранены |
| Confirm старого request | Отказ, новая связь/новый pending не меняются |
| Cancel повтор/две вкладки | Один canceled результат, новый request не отменяется |
| Content/owner изменён между read и cancel |409, никаких записей; перечитать права/состояние |
| Confirm победил cancel | Approved сохраняется; отмена запрещена, detach отдельно |
| Cancel победил confirm | Link не появляется; нужна новая запись и согласия |
| Чужой/employee/former owner |403/404,0writes,0metadata leak |
| Private place стал недоступен сети | Отмена без metadata; новый запрос инициирует place owner |
| Другая сеть/несовместимый program | Новый join запрещён прежними guards |
| Informational request | Новый business recovery его не отменяет/не одобряет |

Текущий результат: source/server дефект подтверждён; план готов к согласованию. Реализация, новые regression tests, browser и screenshots нового UI — NOT RUN.

Фактическая интеграция place-side выполнена в существующий owner_places_dashboard (src/catalog/views.py/pages/owner_places.html), без второго процесса редактора. Signed state содержит keyed HMAC, не читаемые private owner/version values. Server149PASS; browser domain lifecycle11PASS; cabinet141PASS/3existing overflowFAIL, console ViewTransitionFAIL; migration checkFAIL outside scope. Отчёт docs/qa/org-12-fix-2026-10-09.md. Full suite/production/commit/push/deploy NOT_RUN.
