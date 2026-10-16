# ACCESS-QA-04 — scoped LOCAL PASS

2026-10-15, Asia/Baku. **Карточки команды места теперь сжимаются до доступной ширины, а длинные email/имена переносятся полностью.** Закрыт только ACCESS-QA-04 в одобренном scope. Full ACCEPT-07 NOT RUN; production не проверялся. Итог подтверждается [verification.json](verification.json) и [native gate exit](verify.status.json).

## Approval, snapshot и изменения

Пользователь явно ответил «одобряю» на [конкретный план](../access-qa04-recheck-2026-10-15-r1/IMPLEMENTATION_PLAN.md). [Approval с SHA](approval.json) привязан к двум точным CSS правилам и одному application файлу. Повторное согласование не запрашивалось, scope не расширялся.

Фактический checkout `/home/ramin/kidsmap`, branch `task33-progress`, HEAD `e4e05cc213b34e2d771ecb854901bfd016d1db51` **+dirty WORKTREE**, `active_run: NONE`. [Entry](entry.json):28470baseline files, в том числе3shared MO,59foreign containers,2known foreign QA HTTP processes. Чужие изменения/артефакты/стенды не присваивались и не очищались. Один исполнитель, канонические orchestrator/frontend-reviewer/browser-qa обязанности последовательно; независимых subagents не было. Применены ранее прочитанные systematic-debugging, UI/accessibility, playwright и verification-before-completion; CSS mirror/unit tests не создавались.

**Единственный application файл:** `static/css/site.css:9753`. [Минимальный diff относительно entry WORKTREE](repair.diff):11добавленных строк, ровно2правила из плана:

```css
.owner-team .owner-team-list,
.owner-team .owner-team-item {
  min-width: 0;
  grid-template-columns: minmax(0, 1fr);
}

.owner-team .owner-team-item h3,
.owner-team .owner-team-item .meta {
  overflow-wrap: anywhere;
}
```

Причина: два grid уровня раньше расширялись по min-content непрерывного email/username. Mobile overflow:hidden маскировал выход, root scrollWidth оставался360/390. Новые track minimum0 и перенос текста устраняют причину без ellipsis, line-clamp, уменьшения шрифта или скрытия данных. Scope `.owner-team` не совпадает с owner reviews. Template/backend/JS/forms/PO/models/migrations/CI и existing assertions не менялись; исходные shared review правила и password-focus CSS побайтно прежние. Gate удаляет только [одобренные правила](approved-rules.txt) из current bytes и требует entry SHA всего CSS.

## Свежая регрессия до и после patch

Реализация начата только после сверки critical CSS/template/controller/views hashes со [свежим recheck](../access-qa04-recheck-2026-10-15-r1/REPORT.md). Затем создан новый own profile, и **до patch** через native owner forms получены те же проблемные состояния. Не использовалась старая DB/session и не подменялись normal transitions ORM.

[Fresh native RED](red-setup.js.result.json), [receipt](red-setup.js.status.json):22observations,17PASS/5layoutFAIL, native exit0/semantic error null. Пять FAIL — card/text у отдельного short-email и card/text/controls у filled long-data наRU360. [RED short PNG](screenshots/red-historical-ru-360.png), [RED long PNG](screenshots/red-filled-ru-360.png). [Prepatch runtime pin](runtime-source-baseline-before-patch.json) и [CSS before](before-site.css) сохранены.

После точного patch перезапущен **только проверенный собственный** HTTP process, source pin обновлён только на новый CSS SHA. Новый собственный GREEN browser session обеспечивает свежую загрузку. [Существующий geometry oracle](oracle-provenance.json) перенесён дословно: panel/card/h3 Range/controls/root bounds не ослаблены. Добавлены проверки полного textContent, metadata/forms, native select/Tab/ShiftTab/outline и реального hit-test сфокусированной кнопки.

**GREEN:575наблюденийPASS/0FAIL**, не575независимых end-to-end тестов. [Все rows/cells](observations.json), individual `*.js.status.json`/`*.js.result.json`; native exit0 отдельно от semantic/FAIL checks.

| Проверенный сценарий | Фактическое покрытие |
|---|---|
| Filled member+pending/accepted/canceled invitation cards, длинные email/username | RU/AZ/EN×360/390/768/1024/1280/1440:18cells |
| Empty team lists | Та же18cell матрица, отдельный empty owner остаётся пустым |
| Native self-invite error | Та же18cell матрица, реальный POST200+flash-error, команда/версии/notifications до и после прежние |
| Единственная historical `cancelled07@example.invalid` card | RU/AZ/EN×360/390:6cells, отдельный solo owner/place |
| Shared current owner reviews | RU/AZ/EN×360/1440:6render/control/focus/empty smoke states,0matching owner-team scope |
| Native affected lifecycle | RU390:invite→recipient accept, owner role MANAGER→EDITOR, pending cancel и removal отдельного участника; reload+READONLY readback |
| Дополнительная видимость фокуса | RU/AZ/EN×360/1440:6целевых keyboard/hit states, кнопка действительно видна и не перекрыта |

Три языковых скрипта дали175PASS каждый =525; [native lifecycle](functional.js.result.json)25PASS; [focus/occlusion](visual-focus.js.result.json)25PASS. Всего66matrix states +1lifecycle +6focus states. Клавиатура: native select Space/Arrow/Enter/Escape, Tab/ShiftTab, видимый outline; изменение выбора без submit не меняет membership/version. Native кнопки/селекты сохраняют POST/CSRF и после действий корректно отображают состояние после reload.

Historical card стала **x21..339 на360**, **x21..369 на390** во всех трёх языках, вместо прежних x21..399.375. Весь email остаётся в DOM и во всех rendered line fragments. Длинное имя переносится и на desktop; metadata/role forms/buttons больше не растягиваются за panel. Root/body и вложенные bounds проверены независимо.

## PNG, console/network и ограничения UI

[PNG manifest](png-manifest.json):**71native PNG =2RED+69postpatch**, пути/SHA/размеры/classification. [Выборочный просмотр](visual-review.json): [shortRU360](screenshots/historical-solo-ru-360.png), [desktop long](screenshots/filled-en-1440.png), [после CtrlHome](screenshots/review-top-en-1440.png). Не все71кадра просмотрены вручную. Raw full-page focus captures сохраняют fixed header в позиции текущего scroll offset; дополнительно получены2GET-only top captures, а6actual elementFromPoint checks доказывают отсутствие перекрытия сфокусированной кнопки. Tool может уменьшать показ изображения, native файлы не редактировались.

В выбранных RED/GREEN receipts **0необъяснённых pageerrors/local request failures/badResponses/static404**. Внешние Google/fonts/CDN requests явно blocked; их ошибки отдельно классифицированы. Native animation source не менялся. Existing RU fallback отдельных EN/AZ labels/errors сохранён, полная локализация не выдаётся за исправленную — это не04 scope. Reviews проверены кратко в текущем empty presentation; review moderation/replies/ACL не принимались заново.

## Runtime, locales, DB и локальная почта

Own container/volume `access-qa04-fix-2026-10-15-r1-pg`, PostgreSQL17 наloopback52069; DB/user `access_qa04_fix_r1`, HTTP43249. [Actual server PID/argv](server.json), [prepatch](server-before-patch.json), [patched source](runtime-source-patched.json), [final source](runtime-source-final.json). Перед новым использованием перепроверять PID/port/source. Сервер запущен из этого WORKTREE; gate проверяет14source hashes, imported owner controller/service paths, cached owner_team template origin/SHA, cwd/argv/PID и **SHA реально отданного CSS HTTP response**.

`DJANGO_TESTING=1` до settings/setup, inherited env cleared, `sys.dont_write_bytecode=True`, checkout.env/manage.py не загружались. Свои LocMem/cache/cookies/media/private-media/filebased email, отключённые analytics/OAuth/Google settings. Python egress разрешает только ownPG, browser route блокирует external; отдельный external probe отвергнут до connect. Productioncredentials не использовались. ORM допустим только для5fictional users/3places; приглашения/принятия/role/cancel/remove выполнены native UI. Shared DB/schema/config не менялись;175migrations применены только к новой ownDB при подготовке.

Текущие RU/AZ/EN PO собраны один раз в новый свой `.tmp/access-qa04-fix-2026-10-15-r1/locales` через `scripts/build_isolated_locales.py`: [build](locales-build.txt), [verify](locales-verify.txt), [manifest](locale-manifest.json), exits0. Startup и final gate проверяют manifest/source/MO, ровно RU/AZ/EN и **единственный LOCALE_PATHS до django.setup**. Shared3MO побайтно сохранены; PO не менялись.

[READ ONLY final audit](readback-final.json), statement10s/lock2s:

- 5invitations:2ACCEPTED/3CANCELED; каждый accepted имеет ровно1decision, canceled0.
- Active EDITOR membership version3 после двух смен роли; removed inactive EDITOR version2; active grant только1. Ownership versions всех3places остаются1.
- 8notifications:5invitation/2decision/1access_disabled. Outbox sent4/suppressed4, failed/retry/pending0; suppression только stale_access для уже consumed/canceled undelivered invites.
- 4реальных own filebased letters в3files, все адресаты fictitious@example.invalid. Scheduler tick **SIMULATED**, письма настоящие локальные, SMTP NOT RUN. Одно приглашение было отправлено ещё PENDING, затем отменено; это не делает ранее sent letter ошибкой.

## Команды, exits и сохранность

[Полный журнал argv/exits/durations](commands.jsonl), current [collect receipt](collect.status.json), [gate receipt](verify.status.json). Нативных/harness semantic failures в этом fix run не было; сохранённые RED5FAIL — намеренное воспроизведение до patch, не environment error.

| Команда | Результат |
|---|---|
| `.venv/bin/python .../capture.py` | Entry/source/dirty/stands snapshot, свои credentials только вignored700/600 |
| `.venv/bin/python .../launch.py` | Own locale build0/verify0, docker run --pull=never0, own migrate/prepare0, prepatch source match |
| `playwright_cli.sh -s=accessqa04fixr1red open about:blank --config=<own browser.json>` |0, свежая RED session |
| `.venv/bin/python .../browser_run.py red-setup.js` |0,22rows/5expectedFAIL, no semantic error |
| Verified own restart +new `accessqa04fixr1green` session |0, новая CSS pin и served source |
| `.venv/bin/python .../green_queue.py green-ru.js green-az.js green-en.js` | Все native0/semantic null/FAIL0;525PASS |
| `.../green_queue.py functional.js`, затем `visual-focus.js` | Native0/semantic null/FAIL0,25+25PASS |
| `.venv/bin/python .../collect.py` |0,575PASS/71PNG/READONLY/mail/source aggregate,4.684s |
| `.venv/bin/python .../verify.py` | Фактический финальный exit/check counts в verification.json/verify.status.json; JS syntax и git diff --check включены |

Сохранность проверена относительно **entry этого fix**:28470files,3sharedMO, HEAD/branch/active_run,59foreign containers (ID/name/ports/state),2known foreign QA HTTP processes. Единственные разрешённые baseline дельты — exact CSS insertion и одна current guide04 note с [before](guide-note-before.txt)/[after](guide-note-after.txt); inverse bytes обязаны дать entry hashes. Свой QA каталог — единственный новый deliverable scope. Прошлые accepted/recheck/report/plan файлы immutable, reset/clean/stash/commit/push/deploy не выполнялись, active_run не присваивался.

Чужие процессы/контейнеры/browser sessions не останавливали и не перезапускали. Статические файлы общего checkout получили только одобренную CSS дельту; сохранность process identity не называется неизменностью всего shared runtime CSS. Этот inventory не доказывает availability всех произвольных host processes/production и не переобъявляет давно остановленные чужие стенды работающими.

## Остаток / NOT RUN

Только ACCESS-QA-04 CLOSED LOCAL в описанном scope. ACCESS01/02 сохраняют scoped acceptance;03=ORG02 уже принят [module02](../module02-full-2026-10-13-r2/REPORT.md), повторной правки не было. ACCESS05 — следующий отдельный fresh PLAN/approval: [handoff](next-prompt.txt).

Full ACCEPT07/global suites/production/deployment/commit/push/module08 **NOT RUN**. Backend suites не повторялись для чистого CSS изменения, CSS mirror/unit test не создавался. Real screen reader/cross-browser, SMTP/real OAuth/external integrations, полный review lifecycle — NOT RUN. Full ACCEPT07 выполняется один раз после всех задач модуля; модуль07 в целом ещё не принят.
