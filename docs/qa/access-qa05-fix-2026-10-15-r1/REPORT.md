# ACCESS-QA-05 — scoped LOCAL PASS, 2026-10-15

Одобренный scope выполнен: четыре точных записи ошибок удаления аккаунта в AZ/EN PO. [Approval](approval.json), [неизменяемый план](../access-qa05-recheck-2026-10-15-r1/IMPLEMENTATION_PLAN.md), [diff](repair.diff), [inverse proof](inverse-proof.json). Код, exact phrase, sessions/retention policy, RU PO, shared MO и existing assertions не менялись.

## Результат и evidence

**ACCESS-QA-05 CLOSED LOCAL.** Точные тексты «неверный код» и «введите фразу точно» теперь корректны на AZ/EN; fuzzy/устаревший previous-msgid сняты только у этих четырёх записей. Остальные существовавшие изменения двух PO сохранены: обратная замена четырёх блоков восстанавливает entry-хеши.

[RED](../access-qa05-recheck-2026-10-15-r1/locale-regression-red.json): 8 ожидаемых FAIL runtime/MO; перед patch SHA обоих PO совпадали с RED entry. [GREEN](locale-regression-green.json): 8/8 PASS с теми же expected strings; build/verify собственного RU/AZ/EN manifest exit0/0. Никакого массового fuzzy удаления или inline override.

[Настоящий Chromium](observations.json): **522 PASS / 0 FAIL**,18 RU/AZ/EN ×360/390/768/1024/1280/1440 cells, по174 observations на язык. Native exits0/0/0, errornull, по6 completed cells — [queue](queue-status.json). Это observations, не522независимых end-to-end теста. В каждом cell: native request → собственное локальное письмо (recipient + code-hash) → неверный код → неточная фраза → Cancel назад в settings без деактивации → исправление и корректное подтверждение → отдельное письмо отмены → неверный код отмены → корректная отмена → повтор кода400 → старая сессия не восстановлена. Значения полей/aria-invalid/ошибки/Tab/Enter/root overflow проверены. Общий invalid-code msgid отмены проверен на всех18cells. API replay проверяет реальный CSRF-protected endpoint, не скрытую кнопку.

[READ ONLY readback](readback-final.json), exit0:18 завершённых CANCELED запросов, account active/verified, unusable password (нужен новый пароль), коды очищены, attempts0, authenticated sessions0. В initial partial fixture остался один отдельный SCHEDULED/inactive запрос; он не включён в18 accepted cells и не удалялся через ORM. Четыре native перехода выполнялись через UI, fixture только initial user/verified email.

[Семь неизменённых целевых тестов](target-tests.status.json): exit0, Found/Ran7, OK; собственная отдельная test DB, CSRF cookie standard только в unit settings, собственные unit media/private-media. Полные suites здесь не повторялись. Точные selectors [здесь](target-tests.json); [output](target-tests.output.txt).

60native PNG: по wrong-code/wrong-phrase/cancel-wrong-code на18cells плюс canceled390/1440 на3языках; [manifest](png-manifest.json). Выборочно просмотрены оригиналы `en-390-wrong-phrase.png` и `az-1440-cancel-wrong-code.png`, а не все60. На кадрах нет верного кода/письма/URL status token; только заведомо неверные значения и общая exact phrase. Main-page diagnostics:54ожидаемых native HTTP400 и36заблокированных внешних запросов, соответствующие console resource errors; pageerrors/unexplained local failures0. Дополнительно18replay HTTP400 проверены программно; old-session contexts имеют отдельный browser путь и не входят в main-page console capture.

## Snapshot / изоляция

Root `/home/ramin/kidsmap`, HEAD `e4e05cc213b34e2d771ecb854901bfd016d1db51`, branch `task33-progress`, dirty WORKTREE, active_run NONE. [Entry](entry.json):28676 baseline files,61foreign container identities,4known HTTP identities. Собственный новый профиль `.tmp/access-qa05-fix-2026-10-15-r1` mode700, credentials600; без checkout .env/production credentials. DJANGO_TESTING=1 до setup, environment очищен, server egress только own PG; browser external requests блокированы. Own PostgreSQL17-alpine/container+volume `access-qa05-fix-2026-10-15-r1-pg`, DB/user `access_qa05_fix_r1`, loopback36003/59697; отдельные LocMem cache/media/private-media/filebased email. TEST_POLICY только SIMULATED-QA05; default inactive app policy не менялась. Production readiness не заявляется.

Source pinned17paths; runtime PID/argv/cwd, импортированные views/service, cached deletion template SHA, фактически открытые own MO и единственный verified LOCALE_PATHS подтверждены [final verification](verification.json). Shared MO не перезаписывались. Generated credentials, valid codes и signed tokens остаются только в ignored own scratch; CLI raw туда же. Public result sanitizes UUID/token/reset URL/credentials.

## Harness / прерывание и сохранность

Initial ru360:19support PASS +1QA-helper FAIL,0completed cells — [retained result](ru-initial.js.result.json), [notes](harness-notes.md). Public query middleware убрал `?user=` из собственного mail endpoint после logout. Исправлен только QA route на `/qa/mailcode/<fictional-username>/`; прежний matches_own_request assertion сохранён. Один новый fictional user заменил неполный ru360 cell. Initial result/status/source сохранены; первые два same-cell PNG заменены окончательным успешным повтором и не заявляются как отдельные retained evidence. Application middleware не менялся.

После явного прерывания turn очередь уже завершилась (все3per-language receipts сохранены), но прежние HTTP PID отсутствовали. **Непрерывность четырёх foreign HTTP процессов NOT VERIFIED**; их не перезапускали. Это наблюдение после прерывания, причина исчезновения не установлена. Чужие container identity/ports/state сравниваются отдельно и не подменяют HTTP continuity. Только own fix server восстановлен после сверки recorded container ID/loopback bindings,17source hashes и свободного own port: [resume receipt](resume-after-interruption.status.json). Старые PID не считаются актуальными. Итоговый own PID из server.json проверен заново. Исходники/файлы/HEAD/branch/active_run сравниваются с entry; никакой blanket preservation PASS поверх process NOT VERIFIED.

## Команды и границы

[commands.jsonl](commands.jsonl) содержит точные argv/exits/timings: capture0, git apply check/apply0 (exact repair.diff), build0/verify0/docker0/prepare0, locale-green0 (8/8), target-tests0 (7/7), native ru/az/en0 (174/174 each), retry-fixture0, own helper restart0, own resume0, readback0, final gate. Начальные RED/harness результаты не удалены и не переименованы в GREEN. Обратный patch доказан по bytes, а не git diff всего исторически dirty PO.

NOT RUN здесь: actual new-password reset после отмены (unusable-password requirement проверен; предыдущий reset modal отдельно принят в ACCESS01); final deletion processor/30-day wait/backups; полная ACCEPT07/global; cross-browser/real screen reader; SMTP/внешний OAuth/прочие внешние сервисы; production/commit/push/deploy/module08. Далее по исходному поручению — отдельный единый ACCEPT-07 AUDIT ONLY, без новых application fixes.
