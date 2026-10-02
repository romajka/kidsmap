# Этап 02 — независимый bounded review owner-прототипов

Дата: 2026-09-29. Исполнитель: реальный runtime specialist `/root/owner_review`, отдельный от lead `/root`; canonical role `.agents/agents/browser-qa/agent.md`, ACTIVE в `.agents/registry.json`. Режим: PROTOTYPES ONLY / независимый AUDIT. Владение записью: только этот отчёт. Lead выполняет responsive matrix, screenshots и правки макетов; reviewer их не подменяет.

Авторизация: `prompts/02.md` прямо разрешает specialist review и только design-прототипы/документацию. Active run принадлежит lead, `2026-09-29T07:30Z / Codex primary (frontend-reviewer) / stage 02`; это поддержка того же запуска. Зависимость 01 DONE проверена по журналу. LOCAL HEAD: `c52b871ce5c18656a9eaf9854e66255c2629364e`; пакет `docs/task33` untracked/dirty и не входит в HEAD. PRODUCTION UNKNOWN, обращения не выполнялись.

## Scope и evidence

Проверены `design/owner/{place,organization,cabinet,program,groups,team,index}.html`, `prototype.js`, `copy.js`; решения D01–D05/D10. Фактический Chromium DOM и клавиатурные действия на локальных `file:///home/ramin/kidsmap/docs/task33/design/owner/…`; нет server/DB/login/email. Изолированный browser context 1280×900, service workers запрещены, HTTP/HTTPS блокируется. Только синтетические значения, `example.test`. Браузер: Chromium **140.0.7339.16**, cached Playwright **1.55.0**.

Codebase Memory callable: `list_projects` → root `/home/ramin/kidsmap`; `index_status` ready, 11045 nodes / 42824 edges; `get_architecture` выполнен один раз. `check_index_coverage` generation `2026-09-29T07:43:23Z`: decisions metadata_match, owner prototypes **not_tracked**. Для макетов использовано фактическое source/DOM, отсутствие graph узлов не объявлено отсутствием функциональности. Chrome DevTools tools отсутствуют; использован Chromium через Playwright. Прочитаны canonical/shared contracts и skills kidsmap-ui-design, frontend-design, fixing-accessibility, playwright; актуальный Playwright launch/context/routing syntax проверен Context7 `/microsoft/playwright`.

Точная browser-команда:

```bash
node /tmp/kidsmap33-owner-review.cjs
```

Скрипт требует `require('/home/ramin/.npm/_npx/de56a0059759c86a/node_modules/playwright')`; создаёт отдельный context, использует `page.goto(file://…)`, locators, Enter/Tab/Escape и DOM focus inspection. Scratch evidence: `/tmp/kidsmap33-owner-review-result.json`, вне Git artifacts. `command -v npx` exit 0: `/home/ramin/.nvm/versions/node/v20.20.2/bin/npx`. Обычные sandbox exec сначала завершились environment error `error building bubblewrap command: mountinfo path is not absolute`; read/test/report commands выполнены scoped `require_escalated`, auto-review разрешил. Это не application failure.

## Initial findings — переданы lead до финальной приёмки

Результат запуска `2026-09-29T07:48:22Z`: exit 0, **31 checks: 28 PASS / 3 FAIL**. Это результат assertions harness, а не 31 backend tests. Initial `prototype.js` sha256:

`4e145f084bd87087e249fce1e9bcb70ed8a40136fc332e766c5b88cd7d271d03`.

| ID / priority | Воспроизведение и evidence | Влияние / уверенность / owner |
|---|---|---|
| O02-R01 / P2 | `place.html?lang=ru&sample=network&state=published-pending` → изменить `#name-az` → дождаться autosave → submit. Начальное «Опубликовано · изменения на проверке» превращается в «Новая карточка ещё не опубликована». `prototype.js:setStatus`, input listener, submit branch используют одну mutable `state`. | Макет нарушает D04: существующая approved карточка остаётся публичной во время правок. High; frontend-reviewer. Исправление lead, повторная browser проверка необходима. |
| O02-R02 / P2 | На park place focus `.side-nav a[href="#section-3"]` → Enter. Hash `#section-3`, но `document.activeElement.id==''` вместо `section-3-title`; native anchor default отменяет выполненный `heading.focus`. `prototype.js:side-nav` click listener. | После keyboard перехода разделу не передаётся ожидаемый фокус. High; frontend-reviewer. Предложено preventDefault + явный scroll/focus. |
| O02-R03 / P2 | `groups.html?lang=ru` → изменить только `#name-az` → submit. Status: «Изменялись только расписание и сумма. Они применяются сразу…». `prototype.js:groups submit` сравнивает только `conditions`. | Существенное поле ошибочно изображено как immediate amount-only save (D04). High; frontend-reviewer. Нужна отдельная проверка изменённых moderation fields, не расширение backend scope. |

Две первые отрицательные строки раннего harness были **ошибкой текстового ожидания**, а не дефектами: ожидаемое слово «Конфликт» вместо фактического «Есть более свежие изменения»; «Пока нет филиалов» вместо фактического «Добавьте первый филиал». Ожидания уточнены по DOM; эти сценарии PASS. Assertions по трём findings не ослаблялись.

## Подтверждённые сильные стороны

- Четыре continuous секции одной формы, без обязательного «Далее»; anchor links. Park submit проходит с пустой organization, без контактов и без required Activity; admission Free.
- Создание organization без address/branch полей ведёт в `cabinet.html?sample=org-empty`, где первый филиал необязателен. Управление creator и проверка бизнеса/публикации различаются в copy.
- Контакт source меняется: organization inherited → local phone → No contacts после detach. Пустой local phone остаётся пустым; общий контакт не копируется в Place. Ограничение: server detach/ACL не проверены.
- Отдельные права Org profile / shared Program / branch creation; manager не получает invite/transfer control. Выбор всех нынешних филиалов сохраняет selected scope; all_network явно включает будущие и скрывает selected picker. Отсутствие local branch и отсутствие permissions блокируют synthetic invite. Email не отправлялся.
- Program impact перечисляет два активных филиала и сохранение местных prices/groups/schedules; detach retains last approved common text with source. Checked AZ/RU/EN.
- Group supports optional upper age; no-upper очищает/disables max; текстовое class schedule отдельно от Place opening hours, teaching language отдельный control. Amount-only explicit save и dependent conditions review различаются.
- Required Place errors отмечают все 3 поля, связывают aria-describedby, alert и фокусируют первое. Failed retry сохраняет ввод; conflict блокирует submit и переводит фокус на compare.
- Native preview и compare dialogs открываются клавиатурой; preview Tab остаётся внутри, Escape закрывает, фокус возвращается к trigger. Это проверено реальным Chromium.
- Locale `html.lang` AZ/RU/EN и помеченный AZ content fallback RU/EN подтверждены; AZ main required, translations optional. Валюта AZN не меняется с locale.
- Console/pageerror/requestfailed/external HTTP attempts: **0 / 0 / 0 / 0**.

## Tests gaps / UNKNOWN / риски

Это интерактивные макеты в памяти вкладки: server autosave, persistence/cross-device resume, concurrency/stale approval, реальные uploads, ACL/negative HTTP access, owner transfer, link consent, detach, email и DB invariants **NOT RUN**, implementation stages не выполнялись. Production и external Google/analytics NOT RUN. Полная responsive matrix 320/360/390/768/1024/1280/1440 и screenshots не повторялись reviewer; ими владеет lead. Browser assert exit 0 сам по себе не означает all checks PASS; initial result содержит три FAIL, перечисленные выше.

Application code/DB/security changes reviewer: **none**. Tech debt/dead code выводы за пределами bounded scope. P0/P1 findings отсутствуют; initial P2 findings перепроверены после исправлений lead; финальный результат ниже. Принятие owner-02-r1 пользователем **не получено** и не выводится из browser результатов.

## Финальная независимая проверка — PASS

Повторный запуск **2026-09-29T07:53:46Z**, та же exact command `node /tmp/kidsmap33-owner-review.cjs`, exit **0**: **43/43 browser assertions PASS**, новых подтверждённых findings нет. Проверено именно конечное source ниже; файлы не хешированы до исправлений и не выданы за новый HEAD.

- **O02-R01 FIXED**: после изменения опубликованного места и autosave сохранён «Опубликовано» с пояснением approved версии; submit снова «Опубликовано · изменения на проверке». Дополнительно live + rejected (`state=rejected&published=1`) сохраняет публикацию после повторной отправки.
- **O02-R02 FIXED**: Enter на section-3 anchor → hash `#section-3`, actual `document.activeElement.id=='section-3-title'`.
- **O02-R03 FIXED**: изменения только group name, age-from, teacher, teaching language и payment unit → «Изменения группы на проверке». Условия с dependent price также pending; **отдельный свежий amount-only fixture** всё ещё immediate. No-upper проверен отдельно и не смешан с amount-only case.
- Оба dialogs при **390×844**, каждый из **9 Tab и 9 Shift+Tab**: фокус внутри dialog на каждом шаге, Escape закрывает и возвращает trigger. На 1280 preview проверен каждый из 9 Tab. Ранее проверка только конечного фокуса после 8 Tab была недостаточной: она не исключала transient BODY focus, найденный lead; финальный harness проверяет каждый шаг.
- Console/pageerror/requestfailed/external HTTP: **0/0/0/0**. Browser remains Chromium 140.0.7339.16, synthetic file:// context; не было production traffic.

После нового общего title для moderation group первоначальная проверка dependent conditions ожидала старый конкретный текст «условий на проверке». Harness обновлён до фактической семантики «на проверке»; выполнение по старому тексту не объявлено application defect. Остальные существенные assertions не изменены ради green.

Финальные sha256 (команда `sha256sum docs/task33/design/owner/*.html docs/task33/design/owner/prototype.js docs/task33/design/owner/copy.js docs/task33/design/owner/prototype.css`, exit 0):

| Artifact в design/owner | sha256 |
|---|---|
| cabinet.html | `7d534d9e9faa08a9eedc05a9961613526a7515200f99c6efa407606fcaa628ec` |
| groups.html | `b956bb8ac41fd8ede724cca24d50e038b09367c90c9cc4eb3b6636048c393699` |
| index.html | `d0c6ae0f7782a4e12ee28b0d852d02edc6d5555732716b02cabd8030c42fcaef` |
| organization.html | `404bb62b563d22ffed1a3c76ade47f66cc4e991f0124cbde102119326b15351b` |
| place.html | `eb1f90f5b39234cdc7d7224b477cfded387ab655f84280d581e0c8d3bc05b595` |
| program.html | `7f066f5bb890599e0a0b7accae2b59051aed8b34728b1530c474d4353624f493` |
| team.html | `c3130a8651f5586d17352e9e05616a8a1d625dda84b44e19db96111c8a9fc9e8` |
| prototype.js | `73e9e870b0e8a0c919e9f4170b7ba9b830a184e260e98c8f7749900f3079da56` |
| copy.js | `810f34cf0dfe535e43ffdca00fcaf658ea8bb1e685ded89c3f58cc215992644c` |
| prototype.css | `0b262d6dbbb5ecee23f755d976b826b6df3f7c373f0507dd6d3ae579077fc020` |

## Named handoff

**frontend-reviewer / kidsmap-orchestrator `/root`**: bounded independent review **PASS** на указанных hashes; сверить с собственными final screenshots/matrix, поместить ссылку на этот отчёт в `reports/02.md`, оставить acceptance **awaiting_user_review**, завершить и снять active_run только stage 02. Любые новые изменения interactive source требуют bounded retest затронутого поведения. Принятие пользователем и будущая application/production готовность из этого результата не следуют. Stage 03 и production не запускать.
