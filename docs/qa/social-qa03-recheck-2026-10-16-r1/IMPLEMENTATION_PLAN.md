# SOCIAL-QA-03 Implementation Plan

**Статус:** REVIEWABLE PLAN READY; scope approval pending. Current-source recheck REQUIRED перед patch из-за параллельных application/PO changes. Candidate diff не применён. 2026-10-16, Asia/Baku.

**Goal:** при настоящем409 автор видит конфликт внутри KidsMap, свой неотправленный вариантB и актуальную редакциюA; может сравнить и явно отправитьB с обновлённой версией либо загрузитьA с понятным предупреждением о сбросе ввода.

**Architecture:** сохранить существующий submit service/CAS. При ReviewConflict controller продолжает построение author-owned page context и рендерит тот же template со status409 и validated submitted payload. Template показывает A отдельно, B в существующей форме, актуальный expected_revision_id и явные действия. Автоматического POST, silent overwrite или browser storage не добавлять.

**Tech Stack:** текущие Django6.0.2/Python3.12.3/PostgreSQL17.10, server-rendered template; без новой зависимости.

Источники: [guide PLAN SOCIAL03](../continuation-and-repair-prompts-2026-10-11.md#repair-SOCIAL-QA-03), [исторический finding](../module09-2026-10-10-r1/findings/SOCIAL-QA-03.md), [repair prompt](../module09-2026-10-10-r1/repair-prompts/SOCIAL-QA-03.txt), [свежий REPORT](REPORT.md). Исторический FAIL сам по себе не использовался как current evidence.

## Границы

Только SOCIAL-QA-03, P2. SOCIAL01–02 уже закрыты LOCAL в записанных границах. `/home/ramin/kidsmap`, task33-progress, HEAD e4e05cc213b34e2d771ecb854901bfd016d1db51 +dirty WORKTREE, active_run NONE. [Proposal source baseline](proposal-source-baseline.json).

Без commit/push/deploy/production/reset/clean/stash, переключения checkout и назначения active_run. Сохранить чужие изменения/процессы/контейнеры/артефакты. Новый fix-run только с DJANGO_TESTING=1, собственными PostgreSQL/DB/cache/media/private-media/email, fictional data и blocked внешними обращениями. Не загружать checkout .env. Свежие RU/AZ/EN PO собрать штатным builder в собственный каталог, manifest проверить до django.setup, sole LOCALE_PATHS, sharedMO не менять. Старые PID/порты/profile не считать актуальными без проверки.

До patch — только targeted RED. После — тот же набор и4затронутых shared tests. Полный ACCEPT09 один раз после всех задач; сейчас NOT RUN. Existing assertions не ослаблять. Новая причина или дополнительный application файл требует отдельного одобрения.

## Точные файлы

1. **Modify** `src/catalog/controllers/typed_reviews.py` — сохранить validated rating/textB в локальном response context при ReviewConflict, продолжить существующий author-owned query/render, status409. Успешный message/redirect только после успешного submit. Удалить ставший неиспользуемым import t.
2. **Modify** `src/catalog/templates/catalog/typed_reviews.html` — локализованный conflict aside; latestA rating/text для сравнения; editorB при конфликте, прежний candidate/current default на обычном GET; явный submit и ссылка загрузкиA. Сохранить CSRF и актуальный expected_revision_id.
3. **Create** `src/catalog/testcases/test_social_qa03_conflict_recovery.py` —6meaningful behavior/security regression methods.

Полные unapplied candidates: [controller](candidate/typed_reviews.py), [template](candidate/typed_reviews.html), [tests](candidate/test_social_qa03_conflict_recovery.py). [Конкретный diff](proposed.diff). QA helpers/PNG/REPORT/verification нового fix-run и текущий статус guide входят в evidence scope. Services, moderation, ACL, CAS, cooldown, schema, PO, JS, CSS и предыдущие regression files не меняются.

## Обязательный refresh из-за нового source drift

Captured native18cells относятся к recorded969snapshot. После них чужая работа изменила общий review_versions service, admin files и RU/AZ/EN PO и добавила новые файлы; [точный snapshot drift](source-drift-current.json). Controller/template этого плана пока совпадают с baseline, но current-source PASS не заявляется. Не заменять startup manifest новым hash без повторной проверки.

После одобрения scope и **до application patch** создать новый isolated fix-run по фактическому source; пересобрать RU/AZ/EN, verify manifest и sole LOCALE_PATHS до setup; выполнить свежий targeted native двухвкладочный409 recheck на текущем коде и6method RED. Сохранить новый baseline и природу чужих изменений, не перезаписывать их. При прежней подтверждённой причине продолжить ровно этот3file scope. Если причина изменилась/исчезла либо нужны дополнительные файлы — остановить зависимый patch и согласовать новый план. Предыдущие результаты сохраняются как bounded evidence, а не current acceptance.

## Task 1 — targeted RED

- [ ] Перепроверить checkout/source и одобрение именно этого плана; сохранить entry/index/source/process/container snapshot в новом уникальном fix-run.
- [ ] Скопировать candidate regression в точный новый test path и выполнить на ещё не изменённом controller/template:

```bash
.venv/bin/python docs/qa/social-qa03-fix-2026-10-16-r1/runtime.py test \
 catalog.testcases.test_social_qa03_conflict_recovery.TypedReviewConflictRecoveryTests
```

Runtime создать по проверенному изолированному QA примеру, не запускать manage.py/.env. Шесть методов сейчас **NOT RUN**. Ожидаемый RED — отсутствующие editorB/latestA/conflict UI. Остальные methods являются guard controls; environment/harness failure не считать bug reproduction.

Методы: staleB рендерится409 без записи для4типов/RU-AZ-EN; повторная гонка снова409 и явный retry с актуальным token; scriptB безопасно escaped; B не сохраняется и не раскрывается другому пользователю/гостю; malformed payload/token остаётся400; ранний повтор с current token остаётся429 с Retry-After для Place/Activity/Event. Unit cooldown0 для CAS tests явно SIMULATED; отдельный guard429 использует120s.

## Task 2 — минимальный patch

- [ ] Применить только proposed.diff после сверки baseline. До POST branch определить review_conflict=False/submitted_review=None. В except ReviewConflict установить flag и `{'rating': payload.rating, 'text': payload.text}`. Это валидированный исходный текст до moderation; существующее trimming границ сохраняется. Success message/redirect выполнять только когда конфликта нет. Общий render получает status409 при flag, иначе200.
- [ ] На409 сохранить обычную навигацию и public current. Собственный latestA из уже ограниченного request.user head показан отдельно. Никаких запросов чужих private candidates/причин/жалоб.
- [ ] Form содержитB и fresh expected_revision_id из актуального own head. Кнопка «Отправить мой вариант» — новый явный POST; новый race снова проходит тот же CAS и409. Ссылка «Загрузить актуальную редакцию — мой ввод будет сброшен» — обычный GET, явный отказ отB. Прямой reload/Back не является единственным способом восстановления; долговременное сохранение draft после ухода со страницы не обещается.
- [ ] Добавить role=alert/heading и aria-describedby для полей, autofocus textarea только на409; сохранить native label/select/textarea/button и существующий видимый focus. Safe escaping reason/text не отключать. Локализовать RU/AZ/EN в принятом текущем стиле template. Нового CSS/JS нет.

## Task 3 — GREEN и native browser

- [ ] Выполнить6новых methods и4selected affected methods, всего10unique methods:

```bash
.venv/bin/python docs/qa/social-qa03-fix-2026-10-16-r1/runtime.py test \
 catalog.testcases.test_social_qa03_conflict_recovery.TypedReviewConflictRecoveryTests \
 catalog.testcases.test_social_qa01_rating_readback.TypedReviewRatingReadbackTests.test_new_editor_and_foreign_candidate_have_empty_rating \
 catalog.testcases.test_social_qa02_rejection_feedback.TypedReviewRejectionFeedbackTests.test_rejected_edit_feedback_is_author_only_and_keeps_current_projection \
 catalog.testcases.test_task33_reviews.ReviewVersionPostgresConcurrencyTests.test_two_edits_compare_and_swap_then_two_approvals \
 catalog.testcases.test_place_review_cooldown.PlaceReviewCooldownTests.test_early_repeat_is_429_and_never_overwrites_review
```

Subset обоснован затронутыми POST/render consumers: SOCIAL01 empty/foreign editor, SOCIAL02 feedback/privacy, PostgreSQL concurrent CAS, общий persisted cooldown. Остальные ранее успешные наборы не повторять без новой причины.

- [ ] Подтвердить running source/PID/template/MO; перезапускать только свой новый runtime при необходимости.
- [ ] Native две вкладки для4типов: current4→pendingA5; staleB2 получает настоящий409, B2 остаётся в форме, A5 отдельно для сравнения, current4/count1 не меняется и новая revision не создаётся. В Place дождаться реального cooldown перед stalePOST, иначе429 имеет приоритет; services/order не менять. Activity/Event CAS проверяется раньше cooldown; Specialist намеренно без этого cooldown.
- [ ] Rendered conflict state4типов×RU/AZ/EN×360/390/768/1024/1280/1440. Native ключевые transitions RU/AZ/EN390/1440: чтение конфликта, keyboard/focus, явный retry после реального cooldown, pendingB и approvalB; альтернативная reload-link явно загружаетA. Проверить повторную гонку, long/scriptB, guest/outsider privacy, public count/average, loading/transport failure как SIMULATED только при намеренном injection, console/network и PNG.
- [ ] Проверить heading/message/textarea/кнопки на достижимость прокруткой и клавиатурой; не считать DOM/source/jsdom/HTTP200 заменой rendered UI. Контраст и overflow проверять на реальной странице. Если нужен дополнительный app файл, сначала отдельное согласование.
- [ ] Readonly DB readbacks5s statement/2s lock timeout подтверждают candidate/current/history, no write на409 и one public contribution. Новый response409 не превращать в302/200 для удобства теста.

## Task 4 — evidence и остановка на новом scope

- [ ] Сохранить новый REPORT/verification: approved plan, snapshot/source, exact commands/exits/counts, RED→GREEN, matrix/native PNG manifest, diagnostics, NOT RUN/SIMULATED, сохранность entry/sharedMO/index/HEAD/active_run/containers/processes. Существующие process discontinuity ограничения не превращать вPASS.
- [ ] Закрыть только SOCIAL03 при фактическом acceptance; обновить текущий guide со ссылкой, сохранить историю. Затем отдельный PLAN SOCIAL04. Полный ACCEPT09 после всех задач; module10 автоматически не начинать.

## Риски и self-review

Raw409 сейчас защищает данные, но убирает UI. Исправляется только представление конфликта и author response context. Fresh token выдаётся после failed POST, но применится только по явному действию автора; очередная конкурентная запись снова проверяется CAS. Сервис и transaction boundary остаются прежними. Формат malformed400/forbidden403/cooldown429 не меняется.

Кандидаты — точный reviewable scope, не применённый patch и не GREEN. Текущий recheck ограничен Specialist; остальные типы проверены как shared source path, их rendered409 до реализации NOT RUN. После одобрения regression RED и native acceptance покрывают все4типа.

Свежий recheck:18native Specialist cells,72observations (36controlPASS/36sourceFAIL),18PNG; каждый stalePOST409 оставил latestA/public projection неизменными, editor/B/navigation отсутствуют. Running source969 MATCH, новый sole RU/AZ/EN locale manifest проверен до setup. Остальные3типа pre-patch rendered NOT RUN.

Runtime limitation:18known-signature ViewTransition opt-in disabled pageerrors сопровождали raw409; data controls прошли. В SOCIAL01 уже наблюдалась та же сигнатура, introduction UNKNOWN. После SSR409 patch проверить этот переход целево. Общий JS/CSS в scope не добавлен; если сохранится и потребует отдельной причины/файла — отдельный план и одобрение, не молчаливый PASS.
