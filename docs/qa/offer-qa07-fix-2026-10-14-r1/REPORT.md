# OFFER-QA-07 — CLOSED LOCAL

Дата: 2026-10-14. Закрыт только OFFER-QA-07. Полная ACCEPT-05, общий корпус, внешние интеграции и production: **NOT RUN**.

## Scope и checkout

Одобренный [план](../../superpowers/plans/2026-10-14-offer-qa07-stale-draft-restore.md). Checkout `/home/ramin/kidsmap`; branch `task33-progress`; HEAD `e4e05cc213b34e2d771ecb854901bfd016d1db51`; incoming dirty WORKTREE сохранён. `active_run: NONE` до и после. [Входной snapshot](snapshot.json), [исходные hashes](incoming-source.json), [содержимое пяти исходных файлов](incoming-files.json), [финальная проверка](verification.json). HEAD не описывает текущий dirty source. Commit/push/deploy/production не выполнялись.

Изменены ровно пять разрешённых существующих source-файлов и добавлен один тестовый файл. Diff относительно incoming WORKTREE: `diff-owner_place_continuous.js.patch`, `diff-server_drafts.py.patch`, `diff-photo_views.py.patch`, `diff-views.py.patch`, `diff-permanent_place_wizard.py.patch`. Проверка hashes сохранила остальные входные source/.agents/scripts/locale/common MO. Новые QA evidence и scoped ссылки не заменяют исторические отчёты.

## Причина и исправление

[Свежий RED до patch](../offer-qa07-recheck-2026-10-14-r1/REPORT.md): A сохранил старую private copy; B через настоящий редактор сохранил, отправил и получил одобрение новой версии. Обычный GET молча показывал старый ввод A, хотя fresh GET показывал B. Клиент применял local/server fields до проверки identity/base/candidate; successful explicit save не завершал остальные более ранние копии того же владельца и карточки.

- `static/js/owner_place_continuous.js`: проверки schema/target/source/candidate до apply и установки draft ID/version; текущие данные остаются на экране. Для конфликтной копии — явный выбор текущих данных или восстановления в новый private draft. Поздний GET не подменяет уже набранный ввод. Recovery backup создаётся до выбора/нового набора; при quota failure старый слот не перезаписывается. Wrong-target DTO не позволяет восстановление. Совместимая текущая private/local copy продолжает восстанавливаться.
- `src/catalog/services/server_drafts.py`: explicit save завершает только eligible более ранние копии actor+existing target относительно cutoff начала запроса. Fields/photo history не удаляются; newer/foreign/другие target не затрагиваются. Creation без target не закрывает все новые карточки. Target lock берётся до draft locks, включая save/upload consumers. Запись и upload в завершённую копию отклоняются конфликтом.
- `src/catalog/photo_views.py`, `src/catalog/views.py`: cutoff в начале существующих AJAX/non-AJAX explicit save requests; retirement только после успешного сохранения.
- `src/catalog/services/permanent_place_wizard.py`: три ключа recovery copy в существующем RU/AZ/EN ui_copy. PO/common MO не менялись.
- Новый `src/catalog/testcases/test_offer_qa07_stale_draft_restore.py`: 9 meaningful regression methods. Существующие assertions не ослаблялись; миграций нет.

## Изоляция и runtime provenance

Собственный profile `.tmp/offer-qa07-fix-2026-10-14-r1`, PostgreSQL 17.10 на `127.0.0.1:58559`, DB `offerqa07fix_20261014_r1`, test DB `test_offerqa07fix_20261014_r1`, container `offer-qa07-fix-2026-10-14-r1-pg`, volume `offer-qa07-fix-2026-10-14-r1-pg-data`. HTTP `http://127.0.0.1:42283`, финальный PID 1504824 — параметры этого run, не переносимые параметры будущего.

`DJANGO_TESTING=1`; собственные cache/media/private-media/cookies/LocMem email; fictional actors/data. Checkout .env не загружался, production credentials не использовались. Runtime socket egress разрешает только собственный PostgreSQL; browser внешние обращения блокирует. Общие старые стенды/процессы не останавливались; контролируемые restart касались только точного cmdline собственного PID. Доступность чужих стендов NOT RUN; их старые source receipts требуют повторной проверки перед использованием после любых shared source changes.

[Runtime receipt](runtime-final.json): entry=startup=disk, 2805 source files, digest `9040527f96caf6a6651045a9962890eddc55211ced2e6269865ed32b138375e1`. Собственный venv использует существующие пакеты; зависимости не менялись и .env/credentials старого стенда не копировались. Новые fictional fixtures созданы только в собственной DB; fixtures accepted01–06 не изменялись. Предварительный PLAN recheck использовал проверенный ранее собственный06 runtime; реализация и её acceptance выполнены в новом07 profile.

Текущие RU/AZ/EN PO собраны `scripts/build_isolated_locales.py` через GNU msgfmt в `.tmp/offer-qa07-fix-2026-10-14-r1/locales`; [manifest](locale-manifest.json) complete, три compiler exits0, source/MO hashes сохранены. Проверка manifest и единственный `LOCALE_PATHS` применены до django.setup. Общие MO не перезаписывались. Дополнительные localized recovery keys проверены через настоящий UI.

## Targeted tests: 27 unique methods

26 methods GREEN в `final-targeted-tests.txt` (8 новых, 17 существующих draft guards, 1 continuous matching-draft-consumption guard). Затем новый consumed-photo RED и patch: 3 methods GREEN в `closed-photo-green.txt` (1 новый +2 повторных shared photo guards). Итого **27 unique**, не 29. [Method manifest](test-methods.json). Full/no-label wrapper не запускался; discovery общего корпуса не заявляется.

Сохранены исходные failures: `tests-red` exit1 — 6 методов падают на отсутствующем cutoff interface; behavioral browser RED отдельно. `supplementary-guards` и `shared-after-lock-order` exit1 — kept test DB после TransactionTestCase flush не имела EDU taxonomy FK. QA wrappers `test-corpus.py`/`photo-guards.py` восстанавливают fictional prerequisite через существующий helper только в явно проверенной собственной test DB. Assertions и бизнес-правила не менялись. Финальные 26 methods exit0. `closed-photo-red` exit1: old upload не возвращал требуемый consumed-copy conflict, дошёл до photo validation; после guard 3 methods exit0. Эти failures не скрыты и не считаются успешными проверками.

## Native browser и readback

103 принятых assertions: lifecycle12; UI72 (18 RU/AZ/EN×360/390/768/1024/1280/1440 cells, 4 checks/cell); resume/logout/delayed GET5; outsider ACL2; same-source candidate-only5; final edges7. [Индекс результатов](verification.json), [PNG manifest](png-manifest.json): 47 текущих PNG.

A/B/C — реальные autosave/edit/draft-save/submit/admin-approve/normal-fresh reload/recovery transitions. Explicit recovery создаёт новую private copy; approved B остаётся live. Отдельный candidate-only scenario подтверждает, что A не подменяет сохранённый B даже без изменения live source version. Explicit B draft-save имеет предусмотренный Task33 price contract; его не следует описывать как полностью private для всех полей. Проверяемый private autosave/recovery не изменил live B.

Финальный [READ ONLY readback](readback.json), statement timeout10s/lock timeout2s: source2, approved revision, B activity и price35.00; старый ввод retained, новый private typing сохранён, live B unchanged. ORM использовался для fictional prerequisites/readback, не вместо проверяемых пользовательских переходов.

UI: localized warning/current link/restore action, bounds, controls, keyboard link→Tab→button, errors/console/network. Начальная `ui.result.json` содержит FAIL: current link22px; исправлено до44px и принята `ui.result.attempt1791960456.json`. Crop `choice-ru-360.png` просмотрен вручную: оба действия читаемы, кнопка переносится по строкам. Внешние Googlefonts/Leaflet обращения намеренно блокированы; resource console failures не называются успешной проверкой этих сервисов. Page errors/local unexpected HTTP failures в принятых результатах отсутствуют.

Проверки выполнялись по фазам: UI72 до последних JS preservation/identity guards; final edges7 привязаны к последнему UI source. Последний backend consumed-photo guard проверен 3 целевыми тестами; runtime/readback повторно привязаны к финальному source. Все 103 assertions не объявляются выполненными после последней маленькой правки. Quota error и wrong-target DTO — **SIMULATED** fault injection: 3 из103 assertions; остальные сценарии native с реальными own-server responses. Delayed response удерживает реальный GET, не подменяет его contents.

PNG provenance: candidate-only script повторно использовал имена первых A-autosave/B-draft screenshots; эти два текущих файла относятся к вторичной Place2, а не к первоначальной Place1. Остальные lifecycle screenshots/JSON описывают соответствующие фазы; historical prepatch9PNG не изменены. Manifest описывает последние bytes, не доказывает единолично более ранний переход.

Сохранены harness failures раннего recheck (URL constructor в callback, ожидание200 вместо201, формат35.00 вместо35); это исправления QA harness, не app regressions. Предварительные unsuccessful результаты сохранены.

## Пределы и handoff

OFFER-QA-07 **CLOSED LOCAL** по scoped evidence. Backend ACL/CAS/candidate/live consumers охвачены указанными целевыми guards, но полный модуль05 и общие модули не объявляются PASS. Concurrent newer-copy cutoff behavior проверен тестом; stress/deadlock load NOT RUN. Внешние сервисы/production/global corpus/full ACCEPT-05 NOT RUN. Чужой WORKTREE, active_run и исторические evidence сохранены.

Следующий отдельный scope: **PLAN OFFER-QA-08**, причина окончательного отказа программы не видна владельцу. [Copyable prompt](next-prompt.txt). Это подготовка следующего recheck/плана, не разрешение реализовать08. OFFER-QA-09 OPEN baseline остаётся отдельным. Полная ACCEPT-05 после выбранных ремонтов, по предпочтению пользователя.

## Exact captured commands / exits

Полные stdout/stderr в одноимённых `.txt`; argv/exits/durations в `.command.json`, последовательность в `commands.jsonl`. Ниже shell-rendering точных argv, без секретов.

- `acl-seed.command.json`: exit **0** — `.tmp/offer-qa07-fix-2026-10-14-r1/venv/bin/python docs/qa/offer-qa07-fix-2026-10-14-r1/runtime.py script acl-seed.py`
- `candidate-seed.command.json`: exit **0** — `.tmp/offer-qa07-fix-2026-10-14-r1/venv/bin/python docs/qa/offer-qa07-fix-2026-10-14-r1/runtime.py script candidate-seed.py`
- `closed-photo-green.command.json`: exit **0** — `.tmp/offer-qa07-fix-2026-10-14-r1/venv/bin/python docs/qa/offer-qa07-fix-2026-10-14-r1/runtime.py script photo-guards.py`
- `closed-photo-red.command.json`: exit **1** — `.tmp/offer-qa07-fix-2026-10-14-r1/venv/bin/python docs/qa/offer-qa07-fix-2026-10-14-r1/runtime.py test catalog.testcases.test_offer_qa07_stale_draft_restore.StaleDraftRetirementTests.test_consumed_copy_photo_write_conflicts_without_touching_history --keepdb`
- `final-readback-r2.command.json`: exit **0** — `.tmp/offer-qa07-fix-2026-10-14-r1/venv/bin/python docs/qa/offer-qa07-fix-2026-10-14-r1/runtime.py script readback.py`
- `final-readback.command.json`: exit **0** — `.tmp/offer-qa07-fix-2026-10-14-r1/venv/bin/python docs/qa/offer-qa07-fix-2026-10-14-r1/runtime.py script readback.py`
- `final-server.command.json`: exit **0** — `.tmp/offer-qa07-fix-2026-10-14-r1/venv/bin/python docs/qa/offer-qa07-fix-2026-10-14-r1/start-server.py`
- `final-source-server.command.json`: exit **0** — `.tmp/offer-qa07-fix-2026-10-14-r1/venv/bin/python docs/qa/offer-qa07-fix-2026-10-14-r1/start-server.py`
- `final-targeted-tests.command.json`: exit **0** — `.tmp/offer-qa07-fix-2026-10-14-r1/venv/bin/python docs/qa/offer-qa07-fix-2026-10-14-r1/runtime.py script test-corpus.py`
- `preservation-server.command.json`: exit **0** — `.tmp/offer-qa07-fix-2026-10-14-r1/venv/bin/python docs/qa/offer-qa07-fix-2026-10-14-r1/start-server.py`
- `readback.command.json`: exit **0** — `.tmp/offer-qa07-fix-2026-10-14-r1/venv/bin/python docs/qa/offer-qa07-fix-2026-10-14-r1/runtime.py script readback.py`
- `server.command.json`: exit **0** — `.tmp/offer-qa07-fix-2026-10-14-r1/venv/bin/python docs/qa/offer-qa07-fix-2026-10-14-r1/start-server.py`
- `shared-after-lock-order.command.json`: exit **1** — `.tmp/offer-qa07-fix-2026-10-14-r1/venv/bin/python docs/qa/offer-qa07-fix-2026-10-14-r1/runtime.py test catalog.testcases.test_task33_drafts --keepdb`
- `sized-server.command.json`: exit **0** — `.tmp/offer-qa07-fix-2026-10-14-r1/venv/bin/python docs/qa/offer-qa07-fix-2026-10-14-r1/start-server.py`
- `supplementary-guards.command.json`: exit **1** — `.tmp/offer-qa07-fix-2026-10-14-r1/venv/bin/python docs/qa/offer-qa07-fix-2026-10-14-r1/runtime.py test catalog.testcases.test_offer_qa07_stale_draft_restore.StaleDraftRetirementTests.test_unauthorized_actor_cannot_retire_owners_copy catalog.testcases.test_offer_qa07_stale_draft_restore.StaleDraftRetirementTests.test_invalid_explicit_ajax_save_leaves_draft_resumable --keepdb`
- `tests-green.command.json`: exit **0** — `.tmp/offer-qa07-fix-2026-10-14-r1/venv/bin/python docs/qa/offer-qa07-fix-2026-10-14-r1/runtime.py test catalog.testcases.test_offer_qa07_stale_draft_restore catalog.testcases.test_task33_drafts catalog.testcases.test_task33_place_continuous.ContinuousPlaceFormTests.test_explicit_place_save_consumes_matching_server_draft --keepdb`
- `tests-red.command.json`: exit **1** — `.tmp/offer-qa07-fix-2026-10-14-r1/venv/bin/python docs/qa/offer-qa07-fix-2026-10-14-r1/runtime.py test catalog.testcases.test_offer_qa07_stale_draft_restore --keepdb`
- `verification-final.command.json`: exit **0** — `.tmp/offer-qa07-fix-2026-10-14-r1/venv/bin/python docs/qa/offer-qa07-fix-2026-10-14-r1/verify.py`
- `verification.command.json`: exit **0** — `.tmp/offer-qa07-fix-2026-10-14-r1/venv/bin/python docs/qa/offer-qa07-fix-2026-10-14-r1/verify.py`
- `verification-handoff.command.json`: exit **0** — `.tmp/offer-qa07-fix-2026-10-14-r1/venv/bin/python docs/qa/offer-qa07-fix-2026-10-14-r1/verify.py`; final source/runtime/HEAD/branch/active_run preservation, node syntax and diff checks confirmed.
