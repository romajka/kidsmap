# NETWORK-GRANT-UI — fresh recheck and concrete plan

## 1. Решение, scope и авторизация

2026-10-12: **ORG-QA-02 = ACCESS-QA-03, общая причина NETWORK-GRANT-UI, CONFIRMED OPEN / PLAN READY**. Выполнен следующий PLAN из `org-qa01-fix-2026-10-12-r1/next-prompt.txt`, application implementation NOT RUN. [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) включает owner list/refresh, role change, revoke и owner pending-cancel — все перечислены в исходных findings этой причины. Recipient decline ACCESS-QA-02 и остальные findings не входят в scope.

Module02 остаётся IN PROGRESS; ORG-QA-01 сохранён LOCAL scoped accepted, full ACCEPT-02 NOT RUN. Отсутствие UI не приравнивается к излишним серверным правам или production дефекту.

## 2. Checkout и сохранность

Checkout `/home/ramin/kidsmap`, HEAD`e4e05cc213b34e2d771ecb854901bfd016d1db51`, branch`task33-progress`, active_run NONE. Полный dirty/untracked snapshot — [entry.json](entry.json); исходники application/static/config/locale/templates2795 byte-identical. ORG-QA-01 и прежние Place fixes/tests не изменены.

828 файлов предыдущих r6/QA14-close/ORG recheck/ORG fix evidence сохранены. Все10 старых QA PID живы с прежними собственными runtime paths; никто не остановлен/не перезапущен. [preservation.json](preservation.json). Stand и active_run не присваивались. Commit/push/deploy/production NOT RUN.

## 3. Источники и fresh graph

Canonical AGENTS/.agents README/registry/orchestrator/architecture/source-of-truth/audit-contract/engineering-contract — действующий маршрут; application scope требует конкретного одобрения, доступ к production отсутствует. Правила из предыдущих шагов применены, `.agents`/AGENTS diff отсутствует. UI planning использует kidsmap-ui-design +frontend-design, debugging/writing-plans; будущие controls должны соблюдать fixing-accessibility. Независимая делегация не заявляется.

Прочитаны original ORG-QA-02, module07 ACCESS-QA-03 и свежие module13 corroborations обоих alias. Исторический `C:/kidsmap`/localhost/PID не использованы как runtime. Graph current project`home-ramin-kidsmap`, root совпал, ready, generation2026-10-12T13:14:53Z; relevant coverage metadata match. Template partial89–89 компенсирован прямым чтением actual team markup425–503. Trace change_grant:9 callees/6 callers; paginated remainder прочитан. Coverage best-effort, inventory recording truncated; полнота/удаление по graph не заявляется.

## 4. Свой runtime, fixtures и locales

Fresh unique profile `/home/ramin/kidsmap/.tmp/network-grant-ui-recheck-2026-10-12-r1`, URL`http://127.0.0.1:50245`, PID1010756. DB`networkui_20261012_r1`, test DB`test_networkui_20261012_r1`; PostgreSQL17.10 на127.0.0.1:52523 в уже своём `start-local-2026-10-12-r1-pg`. DB клонирована только из своего fictional QA12 профиля, не со старого ПК/production.

DJANGO_TESTING=1; отдельные locmem/cache/media/private-media/email/cookies/browser session. Checkout .env не загружался, production credentials не использованы; secret только ignored own credentials mode600. Browser external origins blocked; Python socket guard разрешает свой PG (не OS firewall).

Fresh RU/AZ/EN native build+verify exit0, sole LOCALE_PATHS до django.setup, shared MO не изменён: [locale-manifest.json](locale-manifest.json), [runtime-version-final.json](runtime-version-final.json). Entry/startup/disk hashes совпадают. Пользователь `network_ui_member` — единственная ORM fixture setup; приглашение/accept/organization/branch выполнены через настоящий UI.

## 5. Native reproduction и уточнение исторического finding

1. Owner native создал fictional organization3 и бизнес-филиал7, пригласил fictional member5 EDITOR/all_network.
2. Member принял через notification inbox native POST; OrganizationGrant1 active/version1, actions`place.edit/place.view`, member.edit true. Реальная страница `/ru/account/places/7/edit/` открылась200. READ ONLY [final-readback.json](final-readback.json) связывает грант/филиал/ownership.
3. Owner same-tab хранит старый invitation-only fragment после стороннего accept; открытого управления/refresh сотрудников нет. После reload **строка сотрудника есть** — [grant-row390](screenshots/grant-row-390-1791811262570.png). Поэтому историческое «список отсутствует» здесь уточнено: SSR row присутствует, management controls отсутствуют.
4. Ни mobile390, ни desktop1440 не дают native revoke. Grant row не содержит select/button/form смены роли. Native owner создал отдельное pending invitation для fictional outsider; строка существует, native cancel отсутствует.
5. Member имеет branch editor доступ, но organization management page404 и canonical `organization.team.manage=False` — правильная граница прав.

[recheck.result.json](recheck.result.json), [rendered-inspection.result.json](rendered-inspection.result.json), [pending-check.result.json](pending-check.result.json).14 assertions:9PASS/5FAIL; четыре FAIL на отсутствующих role/revoke mobile+desktop/cancel controls, один — наблюдение stale same-tab list после external accept. Это одна причина, не новый самостоятельный ID. CLI exits0 доказывают исполнение, не общий PASS.

## 6. Причина и server contract

`organization_workspace.html` выводит grants и invitations как read-only строки. `organization_workspace.js` после invite умеет refresh только `[data-team-invitations]`, management action handlers отсутствуют. Controller получает grants только владельцу, но не даёт presentation для безопасных actions/current status.

Действующие server routes уже обеспечивают нужные переходы:

- `business_team_action(...,'grant')` → `change_grant`, owner/nested-parent/expected_version проверки; role defaults canonical; `active:false` отзывает только network grant и повышаетversion.
- `...,'cancel'` → owner `decide_invitation`, только PENDING; после accept conflict409. Invitation не имеет grant version, её нельзя изобретать на клиенте.
- `has_action` отделяет network от direct place access, проверяет current ownership и selected_places/all_network.

Новая система permissions, schema или ослабление CAS не нужны. Предлагаемое изменение — presentation и safe JSON transport существующих owner actions. PLAN не меняет backend validation.

## 7. Точечная baseline проверка

[targeted-baseline-tests.txt](targeted-baseline-tests.txt):3 Django tests PASS, exit0. Явные labels: GrantTests.test_revocation_and_leave_immediately_remove_cached_account_access; test_endpoint_denies_foreign_nested_ids_and_manager_team_post; test_invitation_grant_version_and_replay_are_checked. Доказывают существующие service/endpoint contracts; **не native UI acceptance**.

[commands.jsonl](commands.jsonl): locale build/verify/check0; own seed-member0; stand start/source gate0; drivers0 с semantic FAIL; targeted tests0. Новый regression для предлагаемого UI и его RED/GREEN ещё NOT RUN. Все existing assertions сохранены.

## 8. Browser/DB evidence, environment и NOT RUN

Все доказанные переходы native. Proof helper только fictional org prefix/owner2, READ ONLY transaction +10s statement/2s lock timeout; не выполняет grant/invitation transitions. [png-manifest.json](png-manifest.json):10 native PNG/SHA256. Grant row mobile визуально просмотрен: действующий редактор есть, owner actions нет.

Pageerror0. Единственный localHTTP≥400 — ожидаемый member organization404. Google font requests блокируются (`net::ERR_FAILED`) и отражены в console events; это environment limitation, не zero-console claim. Исторический Windows runtime/external integrations/production не использовались.

NOT RUN: application patch, native role/revoke/cancel (controls отсутствуют), true browser race future UI, AZ/EN и полная width matrix, fresh regression RED/GREEN, other findings, full module02/global tests, production/commit/push/deploy. Эти пункты не заменены API/ORM/HTTP200 доказательством.

## 9. Reviewable plan и handoff

[IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) перечисляет точные пять application/test файлов, unique evidence/status files, UI sketch/copy RU/AZ/EN, owner role/revoke/pending-cancel transport/CAS, targeted checks и future rendered acceptance. Shared API/service/models/inbox/direct grants/ORG-QA-01 source logic не менять. [next-prompt.txt](next-prompt.txt) — одобрение только данного плана.

Следующий шаг — пользовательское одобрение этого конкретного документа. После него один repair закрывает обе historical aliases только при полном перечисленном acceptance. Непроверенная часть остаётся OPEN. Другие PLAN автоматически не запускать; full ACCEPT-02 после остальных задач модуля.
