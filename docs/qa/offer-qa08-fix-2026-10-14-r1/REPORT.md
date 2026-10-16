# OFFER-QA-08 — CLOSED LOCAL

2026-10-14. Закрыт только OFFER-QA-08 в указанном LOCAL scope. Полная ACCEPT-05/global/external/production **NOT RUN**. OFFER-QA-09 остаётся отдельным OPEN baseline.

## Approved scope / snapshot

[Конкретный план](../offer-qa08-recheck-2026-10-14-r1/IMPLEMENTATION_PLAN.md) предъявлен пользователю; ответ «дальше» после плана принят как разрешение продолжить его реализацию. До изменений назван точный путь и ID. Root sequential, без independent subagent claims. Применены canonical active system, systematic-debugging/TDD/writing-plans/KidsMap UI/frontend-design/verification-before-completion/playwright-cli. Другие findings не реализованы.

Checkout `/home/ramin/kidsmap`; branch `task33-progress`; HEAD `e4e05cc213b34e2d771ecb854901bfd016d1db51` + preserved incoming dirty WORKTREE. `active_run: NONE` до/после. [Snapshot](snapshot.json), [existing source hashes](incoming-source.json), [трёхфайловый incoming source](incoming-files.json), [final WORKTREE](worktree-final.txt), [verification](verification.json). HEAD не описывает dirty source и не является production proof. Чужие изменения/стенды/процессы сохранены; только собственный exact-PID restart. Без commit/push/deploy/production.

## Cause / minimal change

[Fresh prepatch recheck](../offer-qa08-recheck-2026-10-14-r1/REPORT.md):11 prerequisite checks PASS/6 actual FAIL, RU/AZ/EN×390/1440. Canonical final rejection сохранял `declined`, note и payload, но owner template выводил note только для `rejected`; завершённый proposed text не показывался. Live Program/branch оставались approved. Следующая подача уже была доступна в существующем domain service.

Ровно4 source/test файла:

- `src/catalog/controllers/program_workspace.py`: `_context` строит только readonly `declined_changes` из восьми editable content/taxonomy keys. Labels localized; category/subcategory отображаются именами; None/missing choice — «—»; private/hidden/unknown payload keys не рендерятся. Existing editable draft/pending/rejected overlay и live baseline для declined сохранены.
- `src/catalog/templates/pages/program_editor.html`: localized distinction return/final rejection, reason, escaped readonly rejected text вне POST form, current-version heading/instruction и ясная подпись новой подачи. Draft live target не называется опубликованным. Empty proposal имеет нормальный paragraph, не orphan dd. Invalid bound input и CAS fields сохраняются.
- `static/css/pages/organization_workspace.css`: только новые scoped decision/proposal selectors, длинные слова/переносы/readonly dl; общие layout selectors не менялись.
- Новый `src/catalog/testcases/test_offer_qa08_program_declined.py`:12 meaningful behavior/security methods.

[Controller diff](diff-program_workspace.py.patch), [template diff](diff-program_editor.html.patch), [CSS diff](diff-organization_workspace.css.patch) относительно incoming WORKTREE. Publication/moderation/ACL/CAS/propagation services, schema, dependency files, CI, PO/common MO и existing test assertions не менялись. Verification сверяет все зафиксированные existing source/.agents/scripts/locale/common-MO hashes вне этих трёх файлов.

## RED / targeted GREEN / exact counts

Новый основной method до patch: `tests-red` exit1,1 method FAIL из-за отсутствующей причины в owner response. Предыдущий native RED сохранён отдельно.

`tests-green` выбрал **16 methods**:12 новых +4 affected existing guards.15 PASS,1 FAIL — AZ test GET получил301 на canonical default-language redirect, а test client не следовал переходу. `tests-green.txt` и exit1 сохранены, не называются успешным batch. В новом тесте исправлен только request `follow=True` (реальный browser тоже следует301); assertions сохранены. Единственный упавший locale method повторён: `locale-test-green`,1 method PASS/exit0.

После семантического уточнения empty-preview markup повторён только соответствующий method: `empty-preview-green`,1 PASS/exit0. Итого **16 unique accepted methods** через15+1, repeated empty method не увеличивает число. [Exact method manifest](test-methods.json). Широкий module/global/no-label wrapper не запускался. Domain guards: return/pending/draft/approved rendering; gated correction/approval/branch local fields; invalid impact/stale CAS bound input; outsider GET/POST404; note/proposal XSS escaping; null taxonomy/blank fields/private JSON exclusion; localized labels; draft/empty content semantics. Existing assertions не ослаблены.

## Native acceptance / readback

**353 native assertions PASS**, [artifact index](verification.json): lifecycle220; finish108; approve19; extra-pending3; extra-approve3. Основные UI состояния rejected/declined/new pending — **54 RU/AZ/EN×360/390/768/1024/1280/1440 cells**. После approve дополнительно6 RU/AZ/EN×390/1440 samples. [PNG manifest](png-manifest.json):66PNG, имена уникальны, предыдущие screenshots не перезаписаны. `declined-ru-390.png` просмотрен вручную: reason/readonly proposed/current baseline разделены и читаемы; длинные strings переносятся, native keyboard focus ring виден на новой подаче.

Путь настоящий: owner submit → admin return → owner reload/resubmit → final reject → owner reload/current-vs-readonly preview → invalid impact400 → независимый B new submit → устаревший A409 → pending reload → admin approve → owner reload. Draft decisions не выполнялись ORM. Preview не содержит inputs/selects/buttons/form; malicious script text отображается текстом, `window.OFFER08` не появляется. Keyboard checkbox→Tab→submit, bounds, localized actions, no old decision on pending/approved, shared organization mobile/desktop smoke проверены.

[Declined READ ONLY checkpoint](readback-declined.json): final reason/payload retained, original Program/branch live unchanged. Один первоначальный pending readback пересёкся с последующим approval и увидел уже approved B; [непринятый снимок](readback-pending-race.json) сохранён, не считается доказательством «до». Повторён только короткий native C submit/approve cycle с **дожданным** [ordered pending checkpoint](readback-pending.json): C pending `FINAL approved OFFER08`, live Program и branch ещё B `CORRECTED new OFFER08`. Затем отдельный native approve и [final checkpoint](readback-approved.json): C approved/live/branch snapshot совпадают, local Activity name сохранено. Все readbacks — READ ONLY, statement10s/lock2s. Первоначальный pending-readback command exit0 означает исполнение, а не достижение ожидаемого checkpoint.

Primary lifecycle/finish/approve instrumented: page errors0, unexpected local HTTP failures0; реальные expected400/409 зафиксированы и отделены. Console имеет ожидаемые blocked external resource failures и expected400/409. Googlefonts blocked; внешние интеграции NOT RUN. Два дополнительных ordered checkpoint scripts покрывают transitions, но отдельный полный console sweep в них NOT RUN. Общая accessibility/все account страницы не объявляются PASS.

Phase provenance: первые36UI cells до исправления только нового test request и empty-DL branch. Populated preview path при этом не менялся. Final RU/AZ/EN declined smoke +pending18cells/errors/conflict/approval проверены на последнем app source; empty branch повторно проверен targeted method. 353 не объявляются одним повторным full suite после последней правки.

## Own isolated runtime / locales / preservation

Новый profile `.tmp/offer-qa08-fix-2026-10-14-r1`, PostgreSQL17.10 `127.0.0.1:57763`, DB `offerqa08fix_20261014_r1`, test DB `test_offerqa08fix_20261014_r1`, container `offer-qa08-fix-2026-10-14-r1-pg`, unique volume `offer-qa08-fix-2026-10-14-r1-pg-data`. HTTP `http://127.0.0.1:57989`, final own PID1563318. Это параметры этого run, не будущие переносимые команды.

DJANGO_TESTING=1; собственные cache/media/private-media/cookies/LocMem email, fictional credentials только ignored0600 scratch files. Checkout .env не загружался, production credentials не использовались. Socket egress только own PostgreSQL; browser outside-base blocked. Own venv использует существующие пакеты, не скачивает новый dependency corpus. ORM только fictional prerequisites и readback. Прежние accepted01–07 и recheck08 fixtures/DBs не менялись. Новые source changes требуют новой source проверки любых прежних runtime перед повторным использованием; чужие процессы не остановлены.

[Fresh locale manifest](locale-manifest.json): current RU/AZ/EN PO compiled через `scripts/build_isolated_locales.py`, native GNU msgfmt, build/verify exits0, sole LOCALE_PATHS `.tmp/offer-qa08-fix-2026-10-14-r1/locales/locale` установлен после manifest verify **до django.setup**. Общие MO не перезаписывались; новая copy inline в существующем RU/AZ/EN стиле, PO без изменений.

[Runtime receipt](runtime-final.json): entry=startup=disk,2806source files, digest `a8998d1c25d4f9cfee882e056d1295cf5f38f9024c7d3e3b0044675c221084d7`; exact own cmdline verified. `entry-before-patch.json`/`entry-before-final.json`/`server-before-final.json` сохраняют provenance phases. Source hashes — provenance, не общий module PASS.

## Handoff / limits

OFFER-QA-08 **CLOSED LOCAL** по фактическому scoped acceptance. No broad regression claim; full ACCEPT05/global/load/stress/production/external NOT RUN. Следующий отдельный scope — fresh PLAN OFFER-QA-09, частичная правка карточки с групповыми тарифами ошибочно блокирует модерацию. [Next prompt](next-prompt.txt); этот finding не исправлялся здесь и не относится к историческим73tasks/76IDs. После его выбранного repair — модульная ACCEPT-05. Общий финальный прогон по завершении модулей не заменён целевыми проверками.

## Commands / exits

Полные exact argv/exits/durations: [commands.jsonl](commands.jsonl), `.command.json`; sanitized stdout/stderr `.txt`. Browser CLI exit0 не трактуется автоматически как application PASS — verifier читает every result/assertion и raw failure history. Ниже captured commands.

- `approved-readback.command.json`: exit0 — `.tmp/offer-qa08-fix-2026-10-14-r1/venv/bin/python docs/qa/offer-qa08-fix-2026-10-14-r1/runtime.py script readback.py approved`.
- `declined-readback.command.json`: exit0 — `.tmp/offer-qa08-fix-2026-10-14-r1/venv/bin/python docs/qa/offer-qa08-fix-2026-10-14-r1/runtime.py script readback.py declined`.
- `empty-preview-green.command.json`: exit0 — `.tmp/offer-qa08-fix-2026-10-14-r1/venv/bin/python docs/qa/offer-qa08-fix-2026-10-14-r1/runtime.py test catalog.testcases.test_offer_qa08_program_declined.ProgramDeclinedTests.test_empty_declined_draft_does_not_claim_published_content --keepdb`.
- `final-server.command.json`: exit0 — `.tmp/offer-qa08-fix-2026-10-14-r1/venv/bin/python docs/qa/offer-qa08-fix-2026-10-14-r1/restart-owned.py`.
- `locale-test-green.command.json`: exit0 — `.tmp/offer-qa08-fix-2026-10-14-r1/venv/bin/python docs/qa/offer-qa08-fix-2026-10-14-r1/runtime.py test catalog.testcases.test_offer_qa08_program_declined.ProgramDeclinedTests.test_declined_labels_are_localized_and_state_specific --keepdb`.
- `pending-readback-ordered.command.json`: exit0 — `.tmp/offer-qa08-fix-2026-10-14-r1/venv/bin/python docs/qa/offer-qa08-fix-2026-10-14-r1/runtime.py script readback.py pending`.
- `pending-readback.command.json`: exit0 — `.tmp/offer-qa08-fix-2026-10-14-r1/venv/bin/python docs/qa/offer-qa08-fix-2026-10-14-r1/runtime.py script readback.py pending`.
- `server.command.json`: exit0 — `.tmp/offer-qa08-fix-2026-10-14-r1/venv/bin/python docs/qa/offer-qa08-fix-2026-10-14-r1/start-server.py`.
- `tests-green.command.json`: exit1 — `.tmp/offer-qa08-fix-2026-10-14-r1/venv/bin/python docs/qa/offer-qa08-fix-2026-10-14-r1/runtime.py test catalog.testcases.test_offer_qa08_program_declined catalog.testcases.test_task33_program_workspace.ProgramWorkspaceTests.test_create_and_edit_program_has_separate_right_and_pending_impact catalog.testcases.test_task33_program_workspace.ProgramWorkspaceTests.test_linked_activity_uses_approved_program_and_keeps_local_group catalog.testcases.test_task33_publication.PublicationTests.test_pending_and_rejected_keep_approved_live catalog.testcases.test_task33_publication.PublicationTests.test_program_propagates_only_common_active_links --keepdb`.
- `tests-red.command.json`: exit1 — `.tmp/offer-qa08-fix-2026-10-14-r1/venv/bin/python docs/qa/offer-qa08-fix-2026-10-14-r1/runtime.py test catalog.testcases.test_offer_qa08_program_declined.ProgramDeclinedTests.test_declined_owner_sees_reason_and_readonly_proposal_without_live_overlay --keepdb`.
- `verification.command.json`: exit0 — `.tmp/offer-qa08-fix-2026-10-14-r1/venv/bin/python docs/qa/offer-qa08-fix-2026-10-14-r1/verify.py`.

- `verification-handoff.command.json`: exit0 — `.tmp/offer-qa08-fix-2026-10-14-r1/venv/bin/python docs/qa/offer-qa08-fix-2026-10-14-r1/verify.py`. Final runtime/source/HEAD/branch/active_run/diff preservation confirmed.
