# NETWORK-GRANT-UI — Implementation Plan

> Execute sequentially with the applicable TDD/debugging/UI/accessibility/verification skills. User/project instructions override commit/delegation defaults. No commit/push/deploy/production.

**Goal:** владелец управляет существующим сетевым доступом через кабинет: актуальный список сотрудников, смена роли, отзыв доступа и отмена pending приглашения, с честным сохранением/conflict/readback.

**Architecture:** один UI patch для общей причины **ORG-QA-02 = ACCESS-QA-03**. Все записи и переходы принадлежат существующим `OrganizationGrant`/`OrganizationTeamInvitation` и `business_team_action`; новую модель/ACL/CAS не создавать.

**Tech stack:** existing Django SSR organization workspace, vanilla JS/CSS, PostgreSQL, native Playwright and isolated RU/AZ/EN locales.

## 1. Snapshot, авторизация и границы

Checkout `/home/ramin/kidsmap`, HEAD`e4e05cc213b34e2d771ecb854901bfd016d1db51`, branch`task33-progress`, dirty WORKTREE, active_run NONE. Entry hashes — `entry.json`; [REPORT.md](REPORT.md) — fresh reproduction. ORG-QA-01 уже LOCAL scoped accepted; его patch не переисправлять.

Этот документ **PLAN READY, IMPLEMENTATION NOT RUN**; для patch требуется одобрение этого конкретного scope. Owner role-change и owner pending-cancel явно включены: они описаны в исходных findings этой же причины и не должны потеряться при закрытии alias. Recipient decline ACCESS-QA-02, leave/re-enable/ownership transfer UI, другие findings и полный редизайн вне scope.

## 2. Точные файлы

| Файл | Разрешённое изменение |
| --- | --- |
| `src/catalog/controllers/organization_workspace.py` | Только team presentation в `_detail_context`: current grant status от canonical `business_team._grant_current`, canonical role choices от существующего model field/permission configuration. Не менять уже исправленный выбор ServerDraft/candidate. |
| `src/catalog/templates/pages/organization_workspace.html` | Owner-only stable grants/management fragments, member row/version/URLs, role control, revoke confirmation, pending-cancel confirmation, management refresh/status. Invitation fragment/select/transport contract сохранить. |
| `static/js/organization_workspace.js` | Делегированная обработка management controls через действующие JSON endpoints; owner-only refresh grants+invitations; локализованные state/error copy; сохранность editor/invite input и focus. |
| `static/css/pages/organization_workspace.css` | Только новая row action/inline confirmation responsive layout, wrapping и focus; существующие project action/danger styles переиспользовать. |
| `src/catalog/testcases/test_network_grant_ui.py` | Новый meaningful regression набор для owner-rendered transport и server permission/version/preservation результата. Existing assertions не менять. |
| `docs/qa/network-grant-ui-fix-2026-10-12-r1/*` | Новый unique profile/report/tests/browser/evidence/PNG manifest/handoff; если имя занято — следующий rN. |
| `docs/qa/continuation-and-repair-prompts-2026-10-11.md` | Только current status двух alias и ссылки на fresh acceptance,88 copy blocks/историю сохранить. |

Не изменять business_team service/API, models/migrations, notifications/inbox, direct Place grants, global modals и их locale, PO/shared MO. New UI text реализовать явными RU/AZ/EN branches/copy objects, как в текущем workspace; current role values/permissions брать из server metadata, не из новой JS таблицы прав. Для verification собрать fresh isolated MO без изменения PO.

## 3. Предлагаемый интерфейс для одобрения

Существующий раздел «Сотрудники» и форма приглашения остаются. Ниже — всегда существующий server-rendered fragment сотрудников и pending приглашений. Управление только владельцу; участникам не показывать чужие записи/controls.

```text
Сотрудники                                   [Обновить список]

network_ui_member
Редактор · Вся сеть, включая будущие филиалы · Активен
Разрешения: Редактирование филиалов, Просмотр филиалов
Роль [Редактор ▾] [Сохранить роль]           [Отозвать доступ]

После «Отозвать доступ» — inline confirmation в этой строке:
Отозвать сетевой доступ у network_ui_member?
Отдельные права на конкретные места сохранятся.
[Отмена] [Да, отозвать]

Приглашения
outsideraccept01@example.invalid · Редактор · Вся сеть
Ожидает принятия                           [Отменить приглашение]
После действия: [Вернуться] [Да, отменить приглашение]
```

На390/360px кнопки и role selector переносятся под описание; без горизонтального скролла, скрытого фокуса или icon-only опасных действий. Inline confirmation, без нового modal/focus trap. Фокус на «Отмена» после открытия; после отмены вернуть trigger; после server-refresh вернуть соответствующий row/стабильную кнопку refresh. Management status живёт вне заменяемого fragment с `role=status/aria-live=polite`; errors объявляются и видимы. Native buttons/select/form labels; no-JS controls disabled с понятным объяснением. Применить `fixing-accessibility`.

Минимальные новые видимые подписи:

| RU | AZ | EN |
| --- | --- | --- |
| Обновить список | Siyahını yenilə | Refresh list |
| Сохранить роль | Rolu saxla | Save role |
| Отозвать доступ | Girişi ləğv et | Revoke access |
| Отменить приглашение | Dəvəti ləğv et | Cancel invitation |
| Отмена | Geri qayıt | Go back |
| Доступ отозван | Giriş ləğv edildi | Access revoked |
| Роль сохранена | Rol saxlanıldı | Role saved |
| Приглашение отменено | Dəvət ləğv edildi | Invitation canceled |

Error/copy states тоже явно RU/AZ/EN: отправка; success; запись изменилась409; доступ запрещён403; не удалось подтвердить результат; список не обновился. «Смена роли применяет стандартные права выбранной роли» — предупреждение о существующем server контракте, не новая схема прав.

## 4. Точный transport и минимальная реализация

1. Render `data-team-grants` даже при empty state; rows несут server grant_id/version и canonical action URL. Новые controls только для current actionable grant. Outdated owner/base или suspended row не выдавать за действующий; re-enable/confirm не добавлять.
2. Не менять HTML-only API: формы явно methodPOST/action на действительный endpoint; safe JS interception должен установиться до enable. Не отправлять GET/native-urlencoded в JSON adapter при отсутствии JS.
3. `POST organization/<id>/grant/`: revoke `{grant_id, expected_version, active:false}`; role `{grant_id, expected_version, role:<selected server value>}`. Не отправлять actions/scope/place_ids при обычной смене роли/отзыве — сохранить scoped branches и текущий канонический серверный контракт.
4. `POST organization/<id>/cancel/`: `{invitation_id}`. У invitation нет grant version; не придумывать её. API status CAS уже отклоняет pending→accepted race.
5. Операции ожидают server response; busy/duplicate prevention отдельно от editor. Делегировать listener на stable section, чтобы fragment refresh не потерял handlers. Не менять localStorage/sessionStorage draft или form fields после refresh.
6. Refresh получает owner workspace GET и заменяет только server-rendered grants/invitations fragments. Существующий invitation fragment и семантика invite success/failure сохраняются; новый refresh всегда доступен, не только после ошибки.
7.409: показывать conflict, перечитать authoritative list, **не повторять автоматически** mutation со свежей version.403/404: не сообщать success. Потеря ответа после committed POST — uncertain state; refresh/readback, без повторного blind POST. Success POST+failed list refresh — честно показать оба результата.

## 5. RED и targeted regression

До patch новый test file должен получить RED на отсутствующих management controls/metadata и отсутствие stable grants refresh fragment. Проверять HTML-produced action/version через реальные JSON routes, исходные ACL/CAS и состояние DB, не поиск строки в source и не mock assertions.

- Owner получает role/revoke/cancel controls и правильный scoped URL/expected_version; member с organization.view, stranger, guessed nested IDs не получают управление. Owner-only UI не заменяет403 server.
- Native transport remains CSRF protected; wrong content type/GET/no token не создаёт mutation; no-JS disabled state есть наRU/AZ/EN.
- Role change обновляет canonical actions/version, сохраняет selected_places/scope/ownership/live/candidate. Revoke меняет только эту network grant; direct grant/Place owner права сохраняются.
- Stale expected_version role/revoke409 без изменения winner; pending cancel after accept409 сохраняет accepted grant; owner cancel PENDING не создаёт grant и препятствует replay accept.
- Fragment SSR после операций соответствует DB; список пустых grants/invitations остаётся доступным; suspended/ownership-stale row не предлагается как current.

Пример RED/GREEN:

```text
.venv/bin/python docs/qa/<новый-fix-run>/runtime.py test catalog.testcases.test_network_grant_ui
```

Один финальный targeted прогон: новый файл; `catalog.testcases.test_organization_invitation_transport`; `catalog.testcases.test_organization_invitation_result`; `catalog.testcases.test_org_qa01_autosave_base`; конкретные `catalog.testcases.test_task33_permissions.GrantTests.test_revocation_and_leave_immediately_remove_cached_account_access`, `...test_endpoint_denies_foreign_nested_ids_and_manager_team_post`, `...test_invitation_grant_version_and_replay_are_checked`, `...test_endpoint_transport_csrf_config_and_conflict`. Existing CSRF tests вручную используют `csrftoken`: test process настроить на это имя, browser оставляет unique cookie. Не менять assertions ради green.

## 6. Fresh native acceptance и изоляция

Новый LOCAL profile: DJANGO_TESTING=1, собственные loopback PG/DB/cache/media/private-media/email/browser session, fictional roles; .env/production credentials не использовать, чужие stand/active_run сохранить. Fresh RU/AZ/EN MO через helper, sole LOCALE_PATHS до django.setup; imported source/HEAD/WORKTREE match.

- Native owner invite → recipient inbox accept → owner refresh → row visible → change role/save → independent readback → revoke confirmation/cancel confirmation then true revoke → reload → бывший member denied по applicable branch/editor endpoints.
- Native owner pending invite → cancel → reload → recipient accept replay denied. Recipient decline не добавлять.
- Direct-place grant независимого scope и реальные selected_places/all_network fixtures: revoke network не снимает прямое право и не расширяет branch доступ. ORM только fictional fixture setup, не проверяемые invite/accept/role/revoke/cancel transitions.
- Real two-tab stale grant attempts; pending cancel/recipient accept race;403/404; interrupted response/fetch/list refresh явно SIMULATED transport conditions. Не объявлять externally real integrations.
- UI RU/AZ/EN×360/390/768/1024/1280/1440: actual rendered states/long-name wrapping/keyboard/focus/confirmation/error/console/network. Полный native lifecycle минимум mobile390/desktop1440 каждого языка; остальные widths — целевые native management controls и состояния. Это scope UI matrix, не full module02 ACCEPT.
- Readback READ ONLY transaction, statement/lock timeouts, fictional fields/aggregate only. PNG manifest + screenshots success/conflict/role/revoked/canceled, exact commands/exits/counts.

## 7. Закрытие и следующий шаг

Reviewable diff и свежий REPORT с snapshot/provenance/RED/GREEN/native evidence, environment/baseline/harness failures и NOT RUN. Проверить byte-preservation old evidence/исходных чужих edits/stand PIDs/active_run; guide88blocks и diff check.

Закрыть **оба historical ID одной ссылкой на принятую общую причину** только при выполненных role/revoke/cancel acceptance. Если отдельная часть не проверена или не работает — ID/эта часть остаётся OPEN, без общего PASS module02. ACCEPT-02 после оставшихся ORG scopes. Следующий PLAN автоматически не запускать.
