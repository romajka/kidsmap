# OFFER-QA-08 — свежий recheck / PLAN ONLY

2026-10-14. **CONFIRMED OPEN · P2 · source baseline текущего LOCAL WORKTREE.** Application fixes не выполнялись. Новый [конкретный план](IMPLEMENTATION_PLAN.md) ожидает одобрения; только OFFER-QA-08. Full ACCEPT-05/global/external/production **NOT RUN**.

## Snapshot / authorization

Последовательный root; Django/frontend/browser responsibilities выполнены одним исполнителем, независимые специалисты не заявляются. Канонические AGENTS/README/registry/active kidsmap-orchestrator/architecture/source-of-truth/audit-contract и engineering contract сверены; применены systematic-debugging, writing-plans, KidsMap UI/frontend-design и playwright-cli.

Фактический checkout `/home/ramin/kidsmap`, branch `task33-progress`, HEAD `e4e05cc213b34e2d771ecb854901bfd016d1db51`, incoming dirty WORKTREE сохранён. `active_run: NONE` до/после. [Входной snapshot](snapshot.json), [incoming hashes](incoming-source.json), [финальный WORKTREE](worktree-final.txt), [verification](verification.json). Ни один existing source/.agents/scripts/locale/common MO hash не изменился. Записаны только собственные QA/plan documents и scoped status reference. Commit/push/deploy/production не выполнялись; чужие процессы/стенды не остановлены.

## Fresh reproduction / evidence

[Исторический finding](../module05-2026-10-10-r1/findings/OFFER-QA-08.md) использован как checklist, а не доказательство текущего checkout. Созданы fictional owner/admin/org/program/linked branch/activity в новой собственной DB. Approved baseline setup через ORM и authorized organization structural hook — только prerequisites. Candidate submit/return/resubmit/final reject/correction/approve — настоящие браузерные переходы, без ORM подмены.

Принятый [recheck](recheck.result.attempt1791962791.json): 12 checks, 6 prerequisites PASS и **6 fresh FAIL** — RU/AZ/EN×390/1440. В каждом после native final reject и owner reload видно declined chip, но **нет причины и предложенного текста**; editable form показывает approved baseline. [Correction cycle](correction.result.json): ещё 5 PASS — новый submit после declined, owner reload и native approve работают. Всего17 scoped assertions:11 prerequisites PASS /6 reproduced FAIL. [PNG manifest](png-manifest.json):10PNG. Desktop [RU evidence](screenshots/final-decline-ru-1440.png) просмотрено вручную: published/declined chips, approved description, причина и preview отсутствуют.

[READ ONLY checkpoint до нового submit](readback-declined.json), statement timeout10s / lock timeout2s: revision declined, review_note и payload сохранены; live Program и linked Activity snapshot остаются approved original. [Checkpoint после approval](readback-approved.json): corrected description опубликовано и распространено в branch snapshot, local Activity name сохранено. DB не потеряла причину — ошибка в owner rendering. Эти fictional тексты не являются реальными user records.

## Root cause / contract / impact

`src/catalog/services/publication.py:review` сохраняет final_reject как `declined` с review_note; `src/catalog/services/volunteer_proposals.py:review` отличает actions return/reject. `src/catalog/templates/pages/program_editor.html:9` показывает review_note только при rejected. `src/catalog/controllers/program_workspace.py:_context` накладывает payload только для draft/pending/rejected. Поэтому terminal proposed text доступен DB/moderator, но не владельцу.

`publication.propose` уже принимает новую подачу после declined, проверяет текущие source/revision versions и строит новую candidate base. Fresh correction/resubmit/approve подтвердил этот путь. Простой добавленный declined overlay смешал бы завершённое решение и active candidate: план сохраняет editable current baseline, показывает declined payload отдельно, readonly, с явной инструкцией о новом предложении. Возврат rejected остаётся editable correction. Никакого переименования статусов или изменения review/propose/ACL/CAS/candidate-live semantics.

Impact P2: владелец не может понять окончательный отказ или свериться со своим отклонённым текстом. Live данные при отказе остаются безопасны. Regression относительно другой версии или production UNKNOWN/NOT RUN.

## Isolated stand / runtime / locales

Own `.tmp/offer-qa08-recheck-2026-10-14-r1`, container `offer-qa08-recheck-2026-10-14-r1-pg`, unique volume `offer-qa08-recheck-2026-10-14-r1-pg-data`; PostgreSQL17.10 `127.0.0.1:35809`, DB `offerqa08recheck_20261014_r1`; HTTP `http://127.0.0.1:37167`, own PID1532450. Эти значения относятся только к текущему run. [Runtime receipt](runtime-final.json): DJANGO_TESTING=true, entry=startup=disk,2805files,digest `9040527f96caf6a6651045a9962890eddc55211ced2e6269865ed32b138375e1`. Cmdline собственного процесса проверен.

Fresh RU/AZ/EN compiled из текущих PO через `scripts/build_isolated_locales.py`, GNU msgfmt; [manifest](locale-manifest.json) complete, единственный LOCALE_PATHS `.tmp/offer-qa08-recheck-2026-10-14-r1/locales/locale` проверен до django.setup. Locale build/verify exits0. Own DB/cache/media/private-media/cookie names/LocMem email. `.env` не загружался; secrets только own ignored0600 files; никаких production credentials/старых данных. Runtime socket egress ограничен own PostgreSQL; browser outside-base blocked. Googlefonts BLOCKED, внешние интеграции не проверены. Принятые results без page errors/unexpected local HTTP failures. Полный console/static/all-consumer audit NOT RUN на PLAN этапе.

[Версии инструментов](versions.json): Python3.12.3, Node20.20.2, Docker29.8.0, GNU gettext0.21, playwright-cli0.1.17, Chromium153.0.8010.36. Использованы существующие пакеты/read-only package paths, dependencies не менялись. Accepted01–07 fixtures/DBs не затрагивались. Новый isolated stand оставлен для own QA; active_run не присвоен.

## Preserved harness/environment failures

Первый setup дошёл до migrations/locale success, затем fictional Place fixture попытался прямую organization binding. Structural service закономерно отклонил shortcut. `prepare.txt` exit1 и `seed-initial.py` сохранены. `seed.py` продолжил существующий own setup и использовал `organization_ownership.request_join`; `prepare-resume` exit0. Это QA fixture setup failure, не finding приложения; чужие data/processes не менялись. Текущий seed — продолжение этого run, не portable команда для новой DB.

Первый `recheck.result.json` сохранил timeout native checkbox `.check()` из-за unstable geometry. До submit состояние не менялось. `recheck-initial.js` сохранён; принятый harness использует настоящий keyboard Space для impact checkbox с проверкой checked, без forced click/JS присваивания/ORM. Повторён только этот незавершённый scoped lifecycle; не full module.

Targeted backend tests на PLAN этапе **NOT RUN**: новый regression file ещё не создан и app patch запрещён до конкретного approval. Для будущего RED/GREEN выбран bounded corpus в плане; assertions не ослаблялись.

## Source map / graph caveats / proposed change

Codebase Memory текущего `/home/ramin/kidsmap` project ready; bounded coverage пяти relevant paths metadata_match/no_recorded_issue, generation2026-10-14T07:19:42Z. Best-effort, не completeness proof. `_context` callers program_detail/program_save подтверждены source и native endpoints. Graph static/dynamic hints сверены реальным кодом; graph cache не сохранён в Git. Broad inventory intentionally не трактуется как исчерпывающий.

Предлагаются ровно4файла: program_workspace.py (readonly declined context), program_editor.html (reason/preview/current/new action copy), organization_workspace.css (новые scoped wrapping selectors), новый test_offer_qa08_program_declined.py. Service/schema/PO/shared MO/dependencies/CI не меняются. [План](IMPLEMENTATION_PLAN.md) содержит точные границы, snippets, tests и RU/AZ/EN×6width acceptance. Остальные findings не входят в scope.

## Handoff / NOT RUN

OFFER-QA-08 **остаётся OPEN** до implementation acceptance. Следующий шаг — approval конкретного [плана](IMPLEMENTATION_PLAN.md), затем targeted RED/GREEN и native declined/rejected/new submit UI в own fresh fix profile. [Копируемый approval prompt](next-prompt.txt). OFFER-QA-09 остаётся отдельным OPEN baseline. Full ACCEPT05 выполняется в конце выбранных module repairs, согласно предпочтению пользователя. Global corpus, stress/concurrency load, full security audit, все другие modules, external integrations и production NOT RUN.

## Commands / exits

Exact argv/exits последовательности setup/browser в [commands.jsonl](commands.jsonl); отдельные wrappers в `.command.json`, sanitized stdout/stderr в одноимённых `.txt`. Browser CLI exit0 означает успешное выполнение harness, не PASS app: шесть expected finding assertions FAIL сохранены.

- `approved-readback.command.json`: exit0 — `.tmp/offer-qa08-recheck-2026-10-14-r1/venv/bin/python docs/qa/offer-qa08-recheck-2026-10-14-r1/runtime.py script readback.py approved`.
- `declined-readback.command.json`: exit0 — `.tmp/offer-qa08-recheck-2026-10-14-r1/venv/bin/python docs/qa/offer-qa08-recheck-2026-10-14-r1/runtime.py script readback.py declined`.
- `prepare-resume.command.json`: exit0 — `.tmp/offer-qa08-recheck-2026-10-14-r1/venv/bin/python docs/qa/offer-qa08-recheck-2026-10-14-r1/runtime.py script seed.py`.
- `server.command.json`: exit0 — `.tmp/offer-qa08-recheck-2026-10-14-r1/venv/bin/python docs/qa/offer-qa08-recheck-2026-10-14-r1/start-server.py`.
- `verification.command.json`: exit0 — `.tmp/offer-qa08-recheck-2026-10-14-r1/venv/bin/python docs/qa/offer-qa08-recheck-2026-10-14-r1/verify.py`.

- `check.command.json`: exit0 — `.tmp/offer-qa08-recheck-2026-10-14-r1/venv/bin/python docs/qa/offer-qa08-recheck-2026-10-14-r1/runtime.py check`.

- `verification-handoff.command.json`: exit0 — `.tmp/offer-qa08-recheck-2026-10-14-r1/venv/bin/python docs/qa/offer-qa08-recheck-2026-10-14-r1/verify.py`.
