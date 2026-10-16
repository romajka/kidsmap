# Module07: PLAN ACCESS-QA-01 — CONFIRMED OPEN / AWAITING APPROVAL

2026-10-14, Asia/Baku. Только свежий recheck и конкретный план; application patch не выполнен. Один `/root`, последовательно обязанности канонических kidsmap-orchestrator/frontend-reviewer/browser-qa; независимых специалистов не запускал. Registry и реальные definitions прочитаны. Применены systematic-debugging, writing-plans, fixing-accessibility, kidsmap-ui-design/frontend-design, playwright и verification-before-completion.

## Snapshot и границы

Реальный checkout `/home/ramin/kidsmap`; branch `task33-progress`; LOCAL HEAD `e4e05cc213b34e2d771ecb854901bfd016d1db51`, **dirty WORKTREE**, `active_run: NONE`. [Entry](entry.json):27396 прежних файлов,54 существующих контейнера и5 прежних QA processes (own snapshot shell отдельно ошибочно включена collector). Никаких reset/clean/stash/active_run ownership/commit/push/deploy/production. Dirty diff — прежняя работа, не результат этого плана.

Module06 [LOCAL PASS](../module06-full-2026-10-14-r1/REPORT.md)/[verification](../module06-full-2026-10-14-r1/verification.json)/[next prompt](../module06-full-2026-10-14-r1/next-prompt.txt) сверены; не доказательство production. Module07 acceptance не запускалась.

## Подтверждённый дефект

**ACCESS-QA-01, P2, SOURCE, HIGH confidence, OPEN.** Anonymous login/reset modal. На current WORKTREE после второго Tab: `INPUT#resetModalEmailInput → BUTTON#resetModalSubmitBtn → BODY#top → background brand/burger/Google button`. Shift+Tab тоже уходит на фон. Escape/крестик закрывают диалог, focus opener не восстанавливается. Space на opener-ссылке прокручивает страницу. Loading отключает focused submit и теряет focus; success не переводит focus на доступную кнопку.

Причина: [`login.html`](../../../src/catalog/templates/auth/login.html) opener161; modal192; openModal312/initial timeout330; closeModal338; keydown380; setLoading365; success transition430. Есть initial focus/Escape/ARIA dialog, но нет focus trap/inert/opener lifecycle. Ошибка ограничена управлением клавиатурой, обход доступа не установлен. [Исторический finding](../module07-2026-10-10-r1/FINDINGS.md) использован как checklist; current FAIL установлен заново.

**Конкретный scope:** только login.html, собственные целевые QA scripts/evidence и текущая строка guide. [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) перечисляет точные пути, algorithm/code, dependencies и regression acceptance. CSS/PO/backend/schema/API/existing assertions правок не требуют в этом scope.

## Свежие проверки

- [Focus matrix](focus-matrix.js.result.json): RU/AZ/EN ×360/390/768/1024/1280/1440,18cells, **162observations:54PASS/108FAIL**. Шесть FAIL на каждой cell: forward/reverse containment, inert background, Escape restoration, Space opening, close restoration. PASS: Enter/initial email focus, Escape closing, dialog geometry. CLI native exit0 означает выполнение, а не semantic GREEN.
- [Reset first run](reset-flow.js.result.json) RU390:13observations10PASS/3FAIL, затем QA selector strict-mode error `.auth-errors` совпал с login alert и hidden modal alert. Raw сохранён. Исправлен только own selector на `form.register-form .auth-errors`; [resume](reset-flow-resume.js.result.json) выполняет2RU login gaps +30AZ/EN rows, **32observations26PASS/6FAIL**. RU уже проверенные13 не повторялись. Initial verification exit1 ошибочно ожидала51PNG, хотя scripts снимают36focus+12reset=48; исправлен только own manifest accounting на точный обязательный список имён, raw [attempt](verification-output.txt) сохранён. Existing/domain assertions не менялись. Итого **45observations36PASS/9FAIL**, три focus FAIL на язык390: loading containment/success focus/success close return.
- Native RU/AZ/EN390: empty/network localization, identifier retention/reopen, disabled/spinner, AJAX400, actual reset POST200; собственное filebased письмо → настоящий link → новый пароль → old-password отказ/new-password login → consumed link refusal. UI переходы выполнялись в Chromium, ORM только initial synthetic fixtures. Local mail не равно real SMTP delivery.
- [Existing reset tests](reset-tests.txt): **9methods PASS, exit0,6.680s**, только `catalog.testcases.test_password_reset`. Assertions unchanged; module/global corpus NOT RUN. Own staticfiles directory warning не test failure; реальные CSS/JS доступны через runserver static finder.
- [Commands/exits](commands.jsonl): Docker/locale verify/prepare/reset tests и browser driver receipts. [Locale build](locales-build.txt) exit0. Browser startup first attempt exit1: CLI искал отсутствующий chromium1247. Second attempt использовал проверенный existing chromium1228 executable: **Chromium153.0.8010.36**, новая session `accessqa01r1`, чужие sessions не закрывались. [Setup receipts](setup-attempts.json).
- [PNG manifest](png-manifest.json):48nativePNG (36focus+12reset states), originals unchanged. Просмотрены RU390/EN1440 form, RU360 escaped-focus и локальные error/success/replay frames. Визуально dialog помещается; actual activeElement trail доказывает focus defect сильнее screenshot.
- Focus diagnostics: pageerrors0, localBadResponses0, local failed requests0. Reset diagnostics: pageerrors0; deliberate network failure и SIMULATED400 отдельно сохранены. Непроверенные engine/screen-reader возможности не объявлялись PASS.

## Изоляция и runtime source

Собственный PostgreSQL17.10 container/volume `access-qa01-recheck-2026-10-14-r1-pg`, bind **127.0.0.1:34811**, DB `access_qa01_r1`, test DB `test_access_qa01_r1`; новый volume,3fictional users. HTTP **127.0.0.1:57059**, PID625007; [argv/source](server.json)/[runtime](runtime-source.json). Python3.12.3/Django6.0.2/Node20.20.2. Existing DB/stand credentials не переиспользовались.

`runtime.py` очищает унаследованное окружение, устанавливает DJANGO_TESTING=1 до settings/django.setup, не импортирует manage.py/.env. Собственные LocMem cache, cookies, media/private-media и filebased email в ignored `.tmp/access-qa01-recheck-2026-10-14-r1`; test email LocMem. Credentials/email links/passwords в Git evidence не сохранялись. QA endpoints loopback+TESTING only, не deployment files.

Current RU/AZ/EN PO собраны `scripts/build_isolated_locales.py build --compiler native` в новый own каталог. [Manifest](locale-manifest.json) verified до django.setup; единственный LOCALE_PATHS — `.tmp/access-qa01-recheck-2026-10-14-r1/locales/locale`. Общие MO не перезаписывались. Final gate повторно проверяет content manifest без новой сборки. Own git-files snapshot исключил ignored shared MO: их текущие SHA отдельно сверены с module06 entry; это provenance относительно прежнего snapshot, не собственный before/after manifest MO. Builder писал только в новый .tmp каталог.

Backend connect/connect_ex разрешены только к собственному PG port; browser все внешние запросы abort. OAuth/Maps/analytics/IndexNow отключены. AJAX400 message,1s delay и deliberate network failure — **SIMULATED transport**, actual successful POST/mail/password/replay/login — приложение. Тексты и DOM не подменялись.

Runtime identity: PID/listener + process cwd/argv + startup hashes десяти relevant source + loaded template origin/source SHA + disk comparison и реальный UI. [Runtime proof](runtime-source.json); echo endpoint сам по себе не использован как единственное доказательство. Login SHA `efc1949f5ed1e136bf0b22e0f56a900b852ad2afdde39c48570d44ac4b10423b`.

Codebase Memory: current project `home-ramin-kidsmap`, root actual checkout,ready; generation2026-10-14T12:39:05Z, metadata_match relevant files. Password-reset search paginated18matches. Login template partial parse148 → direct source checked; views/forms/CSS/reset tests no recorded gap, completeness не обещана. Graph caches в artifacts не копировались.

## Другие ID и сохранность

`ACCESS-QA-03 = ORG-QA-02`: свежий [module02 r2](../module02-full-2026-10-13-r2/REPORT.md) принял native list/role/revoke/pending cancel, CAS и access denial. [Provenance](module02-alias-provenance.json): template/JS/API/service byte-identical принятому source; organization_workspace CSS после той приёмки отличается. Это не свежий FAIL network lifecycle; здесь он NOT RUN и заново не исправлялся. Повторная общая проверка будет в ACCEPT-07. ACCESS02/04/05 не recheck/fix этим запуском.

Вторая собственная verification дала exit1: collector включил собственную временную snapshot shell из-за substring runtime.py в тексте shell. Entry/raw output сохранены; при final gate исключена только точно опознанная собственная snapshot command,5 actual old QA processes проверены по прежним argv/cwd.

[Final verification](verification.json) сравнивает27396entry hashes, HEAD/branch/active_run, old process identities/containers и own runtime/locales. Единственная разрешённая правка прежнего файла — одна новая status note guide; обратное удаление точной note восстанавливает entry SHA. Новые файлы только этот QA каталог; приложение не менялось. Возможный concurrent foreign drift всегда фиксируется отдельно, не откатывается и не присваивается.

Final integrity gate [verification-final-r3-output.txt](verification-final-r3-output.txt), native exit0:27395 прежних файлов byte-identical + exact guide status note, missing/unexpected drift0, HEAD/branch/active_run unchanged,5 actual old QA processes и54 containers preserved, runtime/current source и sole fresh locales MATCH. [Shared MO provenance](shared-mo-provenance.json):3/3 current SHA совпадают module06 entry. После gate добавлено только это пояснение в own REPORT; application/foreign files не менялись. Четыре QA JS syntax checks, git diff-check и27 report/plan links PASS; receipts в commands.jsonl.

## NOT RUN / следующий шаг

Application implementation/GREEN, полный ACCEPT-07, ACCESS02/04/05, свежий network lifecycle/access denial ACCESS03, полный project/global corpus, production, real SMTP/OAuth/Maps/analytics, Firefox/Safari/screen readers/physical devices; reset end-to-end1440 и полный state matrix на остальных widths — NOT RUN здесь, включены в будущую целевую приёмку. Natural token TTL не проверялся. Пользовательское одобрение этого плана ещё не получено.

Итог: свежий **ACCESS-QA-01 CONFIRMED OPEN**, recheck/plan готовы, module07 LOCAL PASS не заявляется. [Next prompt](next-prompt.txt). После одобрения выполнить только этот scope, затем отдельные планы02/04/05; полный ACCEPT-07 после завершения задач; module08 не начинать.
