# SOCIAL-QA-04 — свежая проверка и конкретный план

**CONFIRMED OPEN/P2; PLAN COMPLETE; implementation approval PENDING. Application changes в этом run:0.** Run начат2026-10-16; финальная metadata сверка2026-10-17, Asia/Baku. Исполнитель /root: канонический frontend-reviewer lead и browser-qa/Django/security checks последовательно; независимых субагентов не было.

Страница уведомлений по-прежнему не подключает локальное оформление кабинета. Свежий native browser подтвердил это во всех108сочетаниях состояний/языков/ширин: навигация со стандартными синими подчёркнутыми ссылками, account-main-layout и sidebar display:block, список с маркерами, обычные21px browser buttons. Серверные адресаты/состояния/POST/CSRF работают в проверенном subset. Предлагаются ровно два application файла; кандидаты не применены.

## Snapshot и разрешённая работа

Пользователь сказал «дальше» после scoped closure SOCIAL03; согласно очереди это свежий PLAN04. Отдельный concrete implementation scope04 ещё не одобрен. [План](IMPLEMENTATION_PLAN.md), [точный unapplied diff](proposed.diff), [candidate hashes](candidate-manifest.json), [следующий prompt](next-prompt.txt).

Checkout C:\kidsmap, branch codex/module09-transfer-2026-10-16-r1, HEAD852938d96764ae315b92859e3651e5ea62054a36 + retained approved dirty SOCIAL03. [Source-entry1020](source-entry.json), [final source gate](verification.json). Прежние две правки typed_reviews и новый regression03 сохранены. task33-progress=e4e05cc213b34e2d771ecb854901bfd016d1db51, index tree881e0c48c7d557c46221beb3b2410a157982f861, active_run:NONE, shared MO и .cbmignore сохранены. Новая запись guide добавлена к истории; старые QA packages не переписаны.

Production deployment/schema/runtime UNKNOWN, production не открывался и не изменялся. Никаких commit/push/deploy/reset/clean/stash/checkout switch и автоматического active_run. Недостающие старые PNG не скачивались.

## Причина и impact

- src/catalog/templates/pages/account_notifications.html:1–5 extends base, использует account/org classes, но не имеет extra_head/account CSS. Route src/catalog/urls.py:106 → controllers/workflow_notifications.py:inbox/_render_inbox → именно этот template; origin/SHA подтверждён работающим процессом.
- static/css/pages/account_profile.css:811/818/832/1009/1605 уже определяет layout/sidebar/nav/button/mobile. organization_workspace.css:823/829 содержит org-list/org-row styling; inbox не подключает и его. Shared account nav include уже даёт localized links/active/aria-current.
- Native inbox stylesheet list не содержит account_profile/organization_workspace; полученные локальные CSS не дают нужных правил. В6контрольных Favorites cells тот же sidebar получает account_profile.css и computed flex, active link без underline. Отсутствующий локальный asset import объясняет дефект; external fonts его не объясняют.
- Missing styling присутствует в текущем HEAD template, не внесён dirty SOCIAL03. Classification **PRE-EXISTING BASELINE / CURRENT SOURCE**, confidence HIGH, reproducibility108/108. P2: ограниченный сбой визуальной согласованности/размера действий/понятности состояний, без установленной утраты данных/компрометации. Production applicability UNKNOWN.

Codebase Memory C-kidsmap проверен первым: ready, root C:/kidsmap, generation2026-10-16T18:56:53Z; targeted coverage metadata_changed/unavailable, navigation partial parse. Поиск нашёл inbox/WorkflowNotification; trace нашёл _render_inbox/_inbox_items, но ошибочно связал Django render с одноимённым docs example. Этот edge отвергнут по фактическому import/source. Routes/ORM/template/static связи проверены напрямую; graph не доказательство полноты. Cache graph не копировался, reindex не запускался.

## Свежая изоляция

Новые m09s04-plan-r1-app/m09s04-plan-r1-pg, internal Docker network и собственный persistent volume, DB m09s04_plan_r1, test DB test_m09s04_plan_r1. Python3.12.15, Django6.0.2, PostgreSQL17.11. App repo bind read-only, собственный ignored scratch writable. Очищенный env, DJANGO_TESTING=1 до setup, отдельные DB/cache/media/private-media/LocMem email; .env/production credentials не загружались.

Fresh RU/AZ/EN из текущих PO штатным isolated builder; manifest verified до каждого django.setup, LOCALE_PATHS ровно собственный compiled каталог. Shared MO не менялись. [Locale manifest](locale-manifest.json), [runtime info](runtime-info.json). Browser Chromium155.0.8059.12, отдельная Playwright CLI session, localhost33304 allowlist до первой navigation. App egress ограничен internal network. Реальная email delivery/external integrations NOT RUN.

Шесть fictional recipients: empty, unread, read, invitation, revoked, expired. Place и organization invitations созданы настоящим business_team.invite; revoked — cancel через service. Expired — явно заданные первоначальные fixture dates; во время browser checks сроки/guards не обходились. Read — первоначальный read_at fixture. Вход подготовлен QA-only login; реальные пароль/OAuth и все account роли не проверялись. Six states относятся к обычным recipients; owner/staff profile smoke запланирован после approval.

State endpoint использует explicit READ ONLY transaction, statement_timeout5s/lock_timeout2s. Перед/после сравниваются notification row/read/unread/action counts, invitation statuses/versions, membership/grant/outbox counts. Login/session записи на собственном стенде не называются отсутствием вообще любых DB writes.

## Проверки и counts

| Проверка | Выполнено | Результат |
|---|---|---|
| [Native inbox matrix](matrix.json) |6states × RU/AZ/EN ×360/390/768/1024/1280/1440 |108cells,1188control PASS,684applicable style FAIL |
| [Favorites control](neighbors.json) |RU/AZ/EN ×390/1440 |6cells,42checks PASS; existing account stylesheet действительно оформляет sidebar |
| [Affected backend baseline](baseline.log) |4unique existing methods, один запуск |exit0,0F/0E,1.502s |
| proposed.diff apply-check |точный2file diff |exit0, не применён |

11control observations/cell: actual200/canonical URL, rows/read-state/current invite actions, active navigation/accessible names, POST+CSRF form wiring, keyboard Tab в навигации, localized heading, protected business snapshot без изменений. Это1188наблюдений, не1188независимых тестовых методов. Сохранены pending accept/reject по двум типам invitations; revoked/expired не показывают stale accept/reject, read state не показывает mark-read. Native clicks на сами business actions до approval не выполнялись.

Четыре style failures/cell — отсутствие account CSS, layout/sidebar block, active underline. Для заполненных состояний ещё list/card assertions; для72cells с действиями —44px assertion против фактических21px buttons. **18raw TRUE actions_min44 у read-state получены от every([]) без кнопок и считаются N/A**, а не PASS оформления; исходный raw matrix сохранён без перекрашивания. Всего702raw style slots =684FAIL +18N/A; подтверждённого UI style PASS нет. После approval runner должен явно пропускать этот N/A с сохранением RED history.

Все108inbox cells без page horizontal overflow и local HTTP failures;0unhandled pageerrors. Наличие/outline keyboard focus записано, полный a11y/contrast/screenreader PASS не заявлен. В Favorites0pageerrors, external Google Fonts request намеренно blocked в6cells, консольные ошибки блокировки не объявляются product failure или чистой консолью. Локально bundled Material Symbols видны на native PNG; внешнее font success не заявлено.

Четыре backend methods проверили recipient scoping/revoked invitation/POST-only, CSRF403, current-owner join confirmation, decline URL и server-rendered labels обоих типов приглашения в трёх языках. Они не проверяют CSS и не закрывают SOCIAL04. [Точные команды/exits](commands.md), [browser commands](browser-commands.jsonl). Existing assertions не менялись, успешные полные module/project suites не запускались повторно.

[114native PNG](png-manifest.json):108inbox +6Favorites controls, без DERIVED изображений. Вручную просмотрены mobile emptyRU390 и invitationRU390; остальные имеют computed DOM/geometry и screenshots, отдельный ручной просмотр всех114не заявлен. SHA/размеры проверяет final verifier.

## Конкретное предложение

1. **Modify** src/catalog/templates/pages/account_notifications.html: подключить существующий account_profile.css и новый inbox CSS; добавить page scope и row/actions/empty/error hooks, текстовый unread badge AZ/RU/EN. Существующие4form actions/methods/CSRF, URL tags, backend eligibility/read guards сохранены в candidate; это проверено статически.
2. **Create** static/css/pages/account_notifications.css: scoped list/row/buttons, перенос mobile/длинных переводов, min44px, visible focus, brand-token contrast, empty/error и unread presentation. Остальные страницы не подключают этот stylesheet.

Полный [implementation plan](IMPLEMENTATION_PLAN.md) содержит code candidates, checks, зависимости/риски и остановку после scoped closure. Новый CSS предпочтительнее подключения всего organization workspace bundle: общие account/nav rules переиспользуются, org/editor rules в inbox не добавляются. Shared CSS/JS/navigation/controller/services/models/routes/PO/schema вне patch. Отдельный app Python import-assertion test не предлагается; meaningful outcome regression — actual browser layout/action/readback плюс4affected backend tests после patch.

Кандидат **не рендерился как приложение**, его визуальный результат и post-patch GREEN **NOT RUN**. Apply-check и сохранность URL/CSRF не являются acceptance. Возможные итерации в этих2файлах входят в будущее scope; третий application файл/новая общая причина требуют отдельного конкретного согласования.

## Сохранность и ограничения

[Entry containers](containers-entry.txt), [final](containers-final.txt), [preservation](preservation.json):28pre-existing container ID/state сохранены, включая работающий SOCIAL03 app/PG; чужих restart commands0. Созданы лишь два новых owned containers. Это bounded Docker observation, не гарантия непрерывности всех процессов компьютера. Старый WSL discontinuity предыдущего run не переписан как успех этого run.

Source1020 текущего WORKTREE совпадает с entry; previous approved source edits и .cbmignore сохранены, sharedMO/index/refs/active_run прежние. Исторические manifests предыдущих двух QA packages проверены; недостающий старый PNG archive не используется. Старые логические task33/module13 ledgers не объявлены новым global PASS.

Discovery-only опечатки/ранние not-ready probes описаны в commands.md; не отнесены к product test failures. Один JS wrapper вызова записи отчёта имел SyntaxError до выполнения tool, затем исправлен; файлы приложения не затронуты. Browser matrix,4targeted methods и6neighbor controls завершились без harness abort; style assertions остались FAIL. Final verifier хранит отдельные metadata results и не ослабляет product oracle.

**NOT RUN:** применение2file patch, rendering кандидата, post-patch GREEN/acceptance, native mark-read/accept/reject/join/error/loading/transport flows, полная role matrix, physical devices/другие браузеры/реальный screenreader/full WCAG, full ACCEPT09/global corpus, SOCIAL05–09/module10, production/GitHub/deploy/external delivery. SOCIAL01–03 сохраняют прежние scoped LOCAL closures, module09 OPEN. Дальше — одобрение этого конкретного плана, затем его выполнение; последующие findings автоматически не реализуются.

Основание отдельного approval: [AGENTS.md](../../../AGENTS.md), «Future implementation requires a concrete plan and user approval for its scope». Здесь завершены разрешённые recheck/документы и дан точный2file diff; прежнее одобрение SOCIAL03 не расширяет scope на SOCIAL04.
