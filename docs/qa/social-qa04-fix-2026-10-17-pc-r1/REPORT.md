# SOCIAL-QA-04 — исправление и локальная приёмка

**SOCIAL-QA-04 CLOSED LOCAL в одобренном scope. Module09 OPEN.** 2026-10-17, Asia/Baku. Исполнитель /root; канонический frontend-reviewer lead, browser-qa и Django/security checks последовательно. Независимых субагентов не было.

Уведомления теперь используют оформление кабинета: активную навигацию, адаптивные строки, контрастные действия высотой не меньше44px, видимый клавиатурный focus и текстовое состояние «Не прочитано». Empty/read/unread, действующие и недоступные приглашения, ответы400/409 отображаются в том же оформлении. Существующие серверные действия и права сохранены.

## Разрешение и snapshot

Пользователь ответил «одобряю» на конкретный [двухфайловый план](../social-qa04-recheck-2026-10-16-pc-r1/IMPLEMENTATION_PLAN.md). [approval.json](approval.json) фиксирует сообщение/дату/planSHA/scope. Прежний PLAN с approval PENDING остаётся историей до этого одобрения; повторное согласование того же scope не запрашивалось.

Checkout C:\kidsmap, branch codex/module09-transfer-2026-10-16-r1, HEAD852938d96764ae315b92859e3651e5ea62054a36 + retained dirty SOCIAL03 + approved SOCIAL04. [Entry1020](source-entry.json), [GREEN1021](green-source.json), [verification](verification.json), [preservation](preservation.json). Index/HEAD/branch/task33 ref и active_run:NONE прежние. Новая запись guide добавлена к истории. Source вне разрешённого template совпадает с entry; новый CSS добавлен отдельно. Уже одобренные SOCIAL01–03 и .cbmignore сохранены.

## Что изменилось

| Файл | Изменение |
|---|---|
| src/catalog/templates/pages/account_notifications.html | Подключены существующий account_profile.css и новый page CSS; scoped hooks, read/unread badge AZ/RU/EN, оформление actions/empty/error |
| static/css/pages/account_notifications.css | Только inbox list/rows/buttons, переносы mobile/длинных переводов,44px actions, focus-visible и brand-token contrast |

Оба файла совпадают с одобренными кандидатами после нормализации LF/CRLF; дополнительных iterations не потребовалось. [Patch scope/hashes](patch-scope.json), [applied diff](applied.diff). Controllers/services/models/routes/schema/PO/global CSS/JS/shared navigation/account/org CSS и existing assertions не менялись. Существующие4form methods/actions, CSRF и URL tags сохранены.

Первопричина устранена в template→asset wiring: до patch inbox не загружал локальные account styles. Вместо всего organization workspace CSS bundle добавлен небольшой page stylesheet с собственными selectors. Соседние страницы его не подключают.

## RED → GREEN

Перед patch повторно проверен текущий source1020 и metadata предыдущего [fresh RED](../social-qa04-recheck-2026-10-16-pc-r1/REPORT.md): все источники совпали. Поэтому неизменённая108cell RED переиспользована:684применимых style FAIL,1188control PASS;18raw every([]) slots без действий остаются явно N/A. Полный старый browser/backend corpus не повторялся.

После patch **4 unique affected backend methods,0F/0E, exit0,1.400s** — один запуск. Проверены recipient scoping/revoked/POST-only, CSRF, current-owner join confirmation и decline forms обоих типов приглашения во всех языках. [GREEN log](green.log), [commands/exits](commands.md). Неизменённые assertions не ослаблялись; новый app Python import-assertion test не добавлялся.

## Native browser и фактическое сохранение

Actual Chromium155.0.8059.12/Playwright CLI, SSR/views/services и fictional PostgreSQL fixtures. QA-only login готовит роль; пароль/OAuth не проверены. Reviewable source/locale/template/static hashes привязаны к новому собственному running profile. Browser clicks, redirects и reload/readback выполнены на настоящих routes, без jsdom.

| Проверка | Охват | Итог |
|---|---|---|
| [Матрица](matrix.json) |6states × RU/AZ/EN ×360/390/768/1024/1280/1440 |108cells,1188control +1368style/outcome PASS,0FAIL |
| [Действия](flows.json) |10 независимых language/action fixtures ×3языка |30cases,279PASS |
| [ACL/CSRF/POST guards](guards.json) |RU/AZ/EN, actual HTTP probes +browser login/navigation |3cases,24PASS |
| [Роли и соседние страницы](smoke.json) |owner/staff inbox12cells; Favorites/profile/organization18cells |30cases,144PASS |
| [Focus contrast](focus.json) |RU/AZ/EN ×390/1440 |6cases,18PASS |

Это observations, не количество независимых backend tests. Ordinary recipient role покрыта основной матрицей; owner/staff дополнительно12cells. В shared smoke18cells страницы возвращают200, имеют заголовок, не подключают inbox CSS, не меняют protected notification state; горизонтального overflow не наблюдалось. Это bounded smoke, не полная приёмка этих модулей.

Матрица проверила загруженные CSS/computed flex и breakpoint direction, list/row, буквальный unread state, локализацию, current action eligibility, CSRF/forms, no business write до действий, отсутствие page overflow, keyboard Tab/Shift+Tab, видимый focus/hit target и44px actions. Для empty/read без кнопок action checks отсутствуют; vacuous PASS не суммируется. Контраст измеренных inbox title/intro/row/time/badge/buttons/empty не ниже **6.0945:1**; focus outline против окружающей поверхности в6key samples также не ниже6.0945:1. Полный WCAG audit не заявлен.

Actual native business actions: Mark read3cases → read_at/read state после reload; Accept Place/Organization6cases → ACCEPTED и ровно один текущий grant; Decline Place/Organization6cases → REJECTED без grant; join confirmation3cases → approved request и linked organization/readback. Для native actions использованы отдельные fixtures на каждый язык/действие. RU/AZ flows на390, EN на1440; все языки/обе key widths для keyboard/focus покрыты основной матрицей и focus supplement.

Дополнительно6real error responses:3native malformed decline400 после явно внесённого QA hidden extra field и3stale decline409 после конкурирующей отмены владельцем. Отмена — **SIMULATED concurrent event** через собственный QA endpoint, вызывающий настоящий business_team service; это не запуск owner UI. Во всех случаях error alert styled, protected state без записи самим ошибочным POST; следующий GET очищает alert и сохраняет актуальный state. Малформированный DOM/конкурентное событие не выдаются за обычный продуктовый ввод.

Транспорт:3 **SIMULATED finite500ms** delays с сохранённым CSRF payload/no early business write и одним последующим native POST;3 **SIMULATED pre-delivery aborts**, одна явная попытка/no write/GET recovery, автоматического retry нет. Ожидаемый net::ERR_FAILED отделён от нормальных HTTP failures. Не выполнялись внешние сетевые сбои/доставка.

Guards на трёх языках: guest GET302login, guest POST403; outsider inbox без строк и valid-CSRF foreign read404; recipient missingCSRF403, GET action405. Protected snapshot до/после одинаковый. Снимки — explicit READ ONLY transaction со statement_timeout5s/lock_timeout2s; login/session записи на собственном стенде не называются отсутствием всех DB writes.

В протоколах matrix/flows/smoke **0unhandled pageerrors**. Ожидаемые400/409/403/404/405 и SIMULATED transport failures не называются чистой консолью/сетью. В shared pages внешние fonts.googleapis.com requests намеренно блокировались allowlist; local bundled icons использовались, external font success не заявлен.

[174native PNG](png-manifest.json):108matrix,30flow reload/readback,6error states,12role inbox и18shared smoke; без DERIVED изображений. Визуально просмотрены mobile unreadRU390 и desktop invitationEN1440; отдельный ручной просмотр всех174не заявлен. SHA/размеры проверены final verifier.

## Изоляция, сохранность и QA notes

Новые m09s04-fix-r1-app/m09s04-fix-r1-pg, internal network, собственный persistent volume, DB m09s04_fix_r1/test_m09s04_fix_r1, отдельные LocMem cache/email/media/private-media. Python3.12.15/Django6.0.2/PostgreSQL17.11. Repo bind read-only, writable только собственный scratch; очищенный env/DJANGO_TESTING=1 до setup, .env/production credentials не загружались.

Свежие3MO RU/AZ/EN собраны штатным builder и проверены до каждого django.setup; единственный LOCALE_PATHS — собственный compiled каталог. [Locale manifest](locale-manifest.json), [runtime info](runtime-info.json), [final live info](live-final.json). Общие MO не менялись. Browser allowlist только127.0.0.1:33314, app internal Docker network; runtime settings/profile/credentials не копировались в evidence package.

[30pre-existing containers](containers-entry.txt) сохранили ID/state в [final snapshot](containers-final.txt), включая работающие предыдущие QA app/PG; чужих restart commands0. Созданы только два новых контейнера. Whole-machine process continuity NOT VERIFIED. Старые running profiles не считаются автоматически соответствующими новому source1021; свежий результат относится только к этому fix profile.

Первый prepare вернул1: собственный PG ещё не готов сразу после старта, migrate/seed/tests до этого не выполнялись. После фактической готовности prepare0. Git apply выдал CRLF whitespace warnings нового36line CSS; текстовых trailing blanks нет, normalized candidate MATCH и git diff --check0. Early seed.log/read-path discovery observations отдельно в commands; browser suites не прерывались и не перезапускались для получения PASS. Никакой product assertion failure не перекрашен в green.

Исторические QA packages/manifests сохранены; guide дополнен новой записью, original bytes до note сохранены. Ни commit/push/deploy/production/reset/clean/stash, ни dirty checkout switch, ни automatic active_run не выполнялись. Partial old PNG archive не догружался. Историческое shared CTA contrast наблюдение SOCIAL03 остаётся отдельным; его CSS не входит в SOCIAL04.

## Граница решения

SOCIAL04 закрыт только LOCAL в проверенном2file scope. SOCIAL01–03 сохраняют scoped historical LOCAL closures. Module09 остаётся OPEN: SOCIAL05–09 требуют отдельных свежих PLAN; full ACCEPT09 один раз после всех задач, global project corpus отдельно в конце. Автоматического перехода к SOCIAL05 нет.

**NOT RUN:** full ACCEPT09/global corpus, SOCIAL05–09/module10, production/GitHub/commit/push/deploy, real external integrations/delivery, physical devices/other browsers/real screenreader/full WCAG. Ни scoped PASS, ни сохранность Docker IDs не являются global product/production PASS.
