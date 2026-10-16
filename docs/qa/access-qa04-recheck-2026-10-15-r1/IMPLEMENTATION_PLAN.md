# ACCESS-QA-04 Implementation Plan

> **For agentic workers:** выполнять последовательно в этом чате только после одобрения именно этого плана. Текущий этап PLAN ONLY. Пользовательские запреты commit/push/deploy, отдельное approval каждого нового scope и выбранный путь документа имеют приоритет над общими skill-шаблонами. Независимые subagents не требуются.

**Goal:** карточки команды места помещаются в доступную ширину; полный email и длинное имя читаются с переносом, кнопки/селекты доступны с клавиатуры.

**Architecture:** исправить intrinsic sizing существующих двух grid уровней и разрешить перенос непрерывного текста только внутри `.owner-team`. Уже существующая корневая секция позволяет ограничиться CSS; template, backend и JS не меняются. Общие `.owner-review-*` правила остаются прежними.

**Tech Stack:** текущие Django SSR/native forms, CSS Grid/Flex, RU/AZ/EN и реальный Chromium; без новой зависимости.

**Spec:** PLAN ACCESS-QA-04 в `docs/qa/continuation-and-repair-prompts-2026-10-11.md`; `docs/qa/module07-2026-10-10-r1/repair-ACCESS-QA-04.txt`; свежие [REPORT](REPORT.md), [geometry/observations](observations.json) и [verification](verification.json).

## Границы и approval

Только **ACCESS-QA-04, P2**, одна причина: min-content растягивает list/item grid, а email/username не переносятся. Исторический short-email trigger проверен отдельно от длинных данных. Валидное длинное имя ломает также большие ширины; фикс не ограничивается media(max-width:360px).

Фактический checkout `/home/ramin/kidsmap`, `task33-progress`, HEAD `e4e05cc213b34e2d771ecb854901bfd016d1db51` +dirty WORKTREE, `active_run: NONE`. Перед implementation сверить заново, сохранить чужие файлы/процессы/контейнеры и прошлые отчёты. Нынешний ответ «продолжи» разрешает recheck/plan, не реализацию ещё не предъявленного scope04. Одобрения01/02 не переносятся.

| Действие | Точный файл | Разрешённая дельта |
|---|---|---|
| Modify | `static/css/site.css` | Два узких правила ниже рядом с существующим owner-team/owner-review блоком |
| Create | `docs/qa/access-qa04-fix-2026-10-15-r1/` | Собственные scripts/receipts/REPORT/verification/PNG; если путь уже занят, новый rN |
| Modify | `docs/qa/continuation-and-repair-prompts-2026-10-11.md` | Только текущая note04 после фактического результата; сохранить прежний текст |

**Единственный application файл — `static/css/site.css`.** `owner_team.html` уже имеет нужные scope/classes, правка разметки не требуется и не входит в план. Не менять JS, routes/controllers/services/forms/models/migrations/PO/shared MO/CI, существующие assertions или общие `.owner-review-*` определения. Не исправлять global overflow:hidden, review lifecycle, переводы05 или no-JS transition anomaly из02. Нельзя прятать текст, уменьшать шрифт, добавлять ellipsis/line-clamp/fixed height или имитировать исправление через overflow:hidden.

## Task 1: pin baseline и минимальный CSS

**Files:** Modify `static/css/site.css`; собственный QA каталог.

- [ ] Сверить текущие хеши CSS и team template с [entry](entry.json), HEAD/branch/active_run. Если source изменился, оценить diff без отката чужих изменений; новую причину отдельно предъявить пользователю.
- [ ] Сохранить исходный CSS/минимальный diff относительно текущего dirty WORKTREE. Вставить ровно следующие правила после `.owner-team-item h3 a, .owner-review-item h3 a` и перед `.owner-team-role-form`:

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

Grid track с минимумом0 позволяет list и внутренней сетке item сжиматься до доступной ширины. `overflow-wrap:anywhere` уменьшает min-content непрерывных email/имён и сохраняет полный текст. Иерархия, типографика, padding/gap и native forms остаются прежними. Scope `.owner-team` не совпадает с owner reviews.

- [ ] Убедиться по diff, что старые shared team/review declarations, принятый password focus CSS и остальные правила не изменены. Не добавлять зеркальный CSS/unit test: для этой обратимой визуальной правки регрессия — сохранённая native RED geometry, затем такой же реальный GREEN.

## Task 2: новый изолированный runtime и целевой native GREEN

**Files:** только собственный QA каталог и ignored `.tmp/<own-run>/`; application дельта остаётся одним CSS файлом.

- [ ] Создать свежий own fix profile: `DJANGO_TESTING=1` до settings/setup, env cleared, свои PostgreSQL/DB/cache/media/private-media/filebased email, fictional@example.invalid, egress только ownPG, external browser requests blocked. Checkout .env/production credentials не читать. Старые PID/порты/session не считать действующими; чужие стенды не трогать.
- [ ] Собрать текущие RU/AZ/EN PO через `.venv/bin/python scripts/build_isolated_locales.py build --output .tmp/<own-run>/locales --locales ru az en --compiler native`; выполнить `verify --manifest .../manifest.json` и require ровно RU/AZ/EN **до django.setup**, единственный LOCALE_PATHS из manifest. Shared MO не перезаписывать. Сверить PID/argv/cwd, imported source/cached template origin+SHA и текущий CSS hash работающего own процесса.
- [ ] Fictional fixtures: отдельные владельцы для filled, empty и isolated historical list; валидные длинные email/username, отдельный участник для последующего удаления. Place/user setup допустим ORM; invite/accept/cancel/role/remove выполняются через настоящие UI forms, с HTTP response/reload/readback. Не подменять нормальные transitions ORM update.
- [ ] Filled: pending/accepted/canceled invitation cards и активный участник с длинным username/email. Проверить **RU/AZ/EN ×360/390/768/1024/1280/1440**. После конечных entry animations замерять root/body, list/item, h3 Range.getClientRects, metadata, role form/select/buttons. Все карточки/строки/контролы в panel/viewport с допуском0.5px; полный исходный текст сохранён, вложенного горизонтального clipping нет. Одного root.scrollWidth недостаточно.
- [ ] Empty и реальный server error (native valid self-invite →200+flash-error и неизменная команда): те же18cells для каждого состояния; не имитировать ошибку вставкой DOM. На узком и широком экране сохранить оригинальные PNG, включая focus/error, и manifest SHA/размеров.
- [ ] Отдельно повторить `cancelled07@example.invalid` как единственную карточку на360/390 во всех3языках: не допустить, чтобы длинная соседняя карточка маскировала причину исторического trigger.
- [ ] Keyboard: Tab/Shift+Tab в role select→button, видимый focus и полностью видимый control, native select Arrow/Enter/Escape. Не менять роль простым фокусом. После geometry на отдельных own fixtures: invite→recipient accept→owner role change→reload/readback, отмена pending и удаление отдельного участника→reload/readback. Проверить ожидаемые status/role/version/active membership, отсутствие дублей.
- [ ] Shared owner reviews: настоящий `/account/places/reviews/`, RU/AZ/EN ×360/1440, root/controls/focus/empty render и PNG; подтвердить отсутствие `.owner-team` scope и сохранность исходных review CSS/template. Это краткий affected-consumer smoke, не новая приёмка review moderation/replies/ACL.
- [ ] Проверить console/pageerrors/network/static404, отделить blocked external transport и ожидаемые ответы. Не считать CLI exit0 достаточным: нужны законченные cells, правильные assertions и состояние DB. Не ослаблять сохранённый geometry oracle ради GREEN.

Если эти два правила не устраняют подтверждённую причину или обнаружена необходимость иной разметки/JS/другой общей причины — сохранить результаты и отдельно предъявить расширение до правок вне плана. Новые security/data findings автоматически не исправлять.

## Task 3: source/preservation gate и scoped handoff

**Files:** own fix REPORT/verification/commands/PNG manifest; одна note04 в guide.

- [ ] Read-only собственная DB, statement10s/lock2s: проверить последовательно созданные состояния/role/version/counts, local email/outbox и отсутствие unintended mutations после error. Ничего не читать/не изменять в production.
- [ ] `git diff --check`, ограниченный diff относительно entry WORKTREE, locale verify, источник actual PID; сравнить все чужие baseline файлы/shared MO, HEAD/branch/active_run, foreign process/container identities и состояние. UNKNOWN/NOT VERIFIED оставить явно; не восстанавливать чужие процессы автоматически.
- [ ] Сохранить новый REPORT: причина, один changed application файл, точные команды/exits/counts, native transitions/geometry/PNG/диагностика и NOT RUN. Закрыть только04 при полном указанном GREEN. Если проверка не завершена,04 OPEN/NOT RUN.
- [ ] Обновить только note04 ссылкой, сохранив историю. Не повторять неизменившиеся02 backend suites/полный модуль; CSS04 не затрагивает их source. ACCESS01/02 сохраняют scoped acceptance,03=ORG02 принят ранее. Далее отдельный fresh PLAN05; **ACCEPT-07 один раз после завершения всех задач**, global corpus отдельно в конце. Commit/push/deploy/production/module08 запрещены.
