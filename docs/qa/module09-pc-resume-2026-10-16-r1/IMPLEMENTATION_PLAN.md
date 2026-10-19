# SOCIAL-QA-03 Implementation Plan

> Для исполнителя: выполнять checkbox tasks последовательно только после явного одобрения этого scope; использовать канонические роли KidsMap. Этот документ и приложенный diff не являются разрешением на patch.

**Статус:** UPDATED REVIEWABLE PLAN; SOCIAL-QA-03 CONFIRMED OPEN/P2; approval PENDING. 2026-10-16, Asia/Baku. Application changes0.

**Goal:** настоящий409 сохраняет вариант автораB внутри KidsMap и позволяет сравнить его с актуальнымA, явно повторить отправку с fresh CAS либо загрузитьA с предупреждением о сбросеB.

**Architecture:** существующий service/transaction/CAS остаётся единственным валидатором. Controller обрабатывает ReviewConflict через общий author-owned render со status409 и validated submitted payload. Shared template показывает A отдельно от editorB; сохранение возможно только новым явным POST.

**Tech Stack:** проверенный на новом ПК Python3.12.15, Django6.0.2, PostgreSQL17.11, SSR Django, Chromium155 для native QA. Новых app dependencies нет.

**Spec:** [RESUME_PROMPT](../module09-transfer-2026-10-16-r1/RESUME_PROMPT.txt), [guide PLAN SOCIAL03](../continuation-and-repair-prompts-2026-10-11.md#repair-SOCIAL-QA-03), [finding](../module09-2026-10-10-r1/findings/SOCIAL-QA-03.md), [свежий REPORT](REPORT.md). Исторический [план](../social-qa03-recheck-2026-10-16-r1/IMPLEMENTATION_PLAN.md) сохранён; этот документ обновляет текущий snapshot и evidence.

## Global constraints

- Только SOCIAL-QA-03; исходники `C:\kidsmap`, branch `codex/module09-transfer-2026-10-16-r1`, HEAD `852938d96764ae315b92859e3651e5ea62054a36`; entry clean, index tree `881e0c48c7d557c46221beb3b2410a157982f861`, active_run NONE.
- Без commit/push/deploy/production/reset/clean/stash и автоматического active_run; сохранить чужие файлы/процессы/контейнеры.
- Сохранить status409, CSRF/ACL/CAS, current/candidate, cooldown и moderation semantics. Без автоматического POST/retry, localStorage и долговременного draft storage.
- Application scope строго3файла ниже. Services/schema/PO/JS/CSS/CI и existing assertions не менять.
- Только собственный DJANGO_TESTING=1 PostgreSQL/DB/cache/media/private-media/email, fictional data и blocked egress; .env и production credentials не загружать. RU/AZ/EN MO штатным builder в новый собственный каталог, verify/sole LOCALE_PATHS до setup, shared MO не менять.
- До patch — только targeted RED; затем targeted GREEN и обоснованный affected subset. Не повторять неизменившиеся успешные полные наборы. Full ACCEPT09 один раз после SOCIAL01–09; global corpus отдельно в конце.

## Причина и актуальность proposal

Свежие18native Specialist cells подтвердили raw409 без editor/B/navigation; кандидатA/current/public не меняются. Шесть candidate methods исполнены вне application package:3FAIL/3PASS,14 assertion failures. Четыре shared methods PASS. Версии, source1019, свежие3MO и ограничения — в REPORT/verification; source после проверки совпал с entry.

`target_reviews:except ReviewConflict` возвращает HttpResponse до render. Service CAS проверяется до revision create. Shared template содержит editor, который не достигается в этой ветви. Cause прежняя; existing controller/template и новый отсутствующий test path подходят под [точный proposed.diff](proposed.diff). Свежий apply-check exit0; diff не применён.

## Точные application файлы и интерфейсы

1. **Modify** `src/catalog/controllers/typed_reviews.py`: `target_reviews(request, kind, pk)` сохраняет `review_conflict: bool` и `submitted_review: {'rating': int, 'text': str} | None`. В except используется проверенный payload, render получает status409. Success message/redirect только после успешного submit. Удаляется неиспользуемый import `t`.
2. **Modify** `src/catalog/templates/catalog/typed_reviews.html`: читает эти2context fields и существующий ограниченный автором own_review; рендерит alert/latestA, editorB, свежий expected_revision_id, явный submit и GET reload link. Обычный GET сохраняет SOCIAL01/02 default/feedback.
3. **Create** `src/catalog/testcases/test_social_qa03_conflict_recovery.py`: ровно6методов из [candidate tests](../social-qa03-recheck-2026-10-16-r1/candidate/test_social_qa03_conflict_recovery.py). Existing tests не менять.

Полный код всех3файловых изменений находится в [proposed.diff](proposed.diff); это reviewable future patch. QA документы/PNG/helpers нового fix-run и одна статусная запись guide — отдельно evidence scope.

## Task1 — authorization/source gate и RED

- [ ] Получить одобрение этого конкретного плана. Сверить HEAD/branch/index/dirty/active_run и [source-entry.json](source-entry.json); не перезаписывать новые чужие изменения. При unchanged source использовать свежую RED здесь; при drift обновить только затронутое воспроизведение до patch.
- [ ] Проверить ownership/isolation/live state собственного runtime либо создать новый уникальный профиль. Старые порты/PIDs/containers не считать действующими автоматически; WSL shutdown уже был, continuity не обещана. Проверить свежие PO/MO и loaded source до setup.
- [ ] Разместить одобренный candidate regression в указанном новом app test path. Если это отдельный будущий runtime, выполнить только его6методов до controller/template patch:

```powershell
wsl -d Ubuntu-24.04 -- docker exec m09pc-r1-app python /mnt/c/kidsmap/.tmp/module09-pc-resume-2026-10-16-r1/runtime.py test catalog.testcases.test_social_qa03_conflict_recovery.TypedReviewConflictRecoveryTests
```

Команда применима только после проверки этого собственного профиля; другой run использует свои container/path. Runtime source manifest обновлять явно после разрешённого добавления test file, сохранив RED baseline, а не подменять его молча. Текущий валидный RED использовал внешний `test_social_qa03_conflict_recovery.TypedReviewConflictRecoveryTests` из candidate directory: app file не создавался.

Шесть методов: staleB409/no-write для4типов×3языков; repeat race409/explicit retry; escaped scriptB; no persistence/no foreign disclosure/guest403; malformed input/token400; current-token early-repeat429/Retry-After для Place/Activity/Event. CAS unit cases cooldown0 явно SIMULATED; отдельный429 guard120s. Ожидаемый RED — recovery UI отсутствует; environment/harness error не является RED багa.

## Task2 — минимальный approved patch

- [ ] Применить ровно controller/template sections приложенного diff. До POST определить flag/payload; при ReviewConflict сохранить `{'rating': payload.rating, 'text': payload.text}`, пройти существующую author-owned context сборку, вызвать render(...,status=409). Успешный submit продолжает прежний message/redirect.
- [ ] При409 latestA показывается из own candidate/current, B2 остаётся в select/textarea; новый hidden token соответствует свежему own head. Другие авторы не получают B или privateA. Autoescaping не выключать.
- [ ] Локализованный alert/heading/description, aria-describedby, native labels/select/textarea/button; autofocus только при409. Явная кнопка «Отправить мой вариант» делает новый POST. Повторный race снова даёт409. GET-ссылка «Загрузить актуальную редакцию — мой ввод будет сброшен» явно отказывается отB. Никакого автоматического сохранения/повтора.

## Task3 — targeted GREEN и native acceptance

- [ ] Обновить отдельный approved-source manifest и проверить running source/template/sole fresh MO. Выполнить6new+4affected, всего10unique methods:

```text
catalog.testcases.test_social_qa03_conflict_recovery.TypedReviewConflictRecoveryTests
catalog.testcases.test_social_qa01_rating_readback.TypedReviewRatingReadbackTests.test_new_editor_and_foreign_candidate_have_empty_rating
catalog.testcases.test_social_qa02_rejection_feedback.TypedReviewRejectionFeedbackTests.test_rejected_edit_feedback_is_author_only_and_keeps_current_projection
catalog.testcases.test_task33_reviews.ReviewVersionPostgresConcurrencyTests.test_two_edits_compare_and_swap_then_two_approvals
catalog.testcases.test_place_review_cooldown.PlaceReviewCooldownTests.test_early_repeat_is_429_and_never_overwrites_review
```

Точный pattern запуска — runtime.py test +эти labels (как в [commands.md](commands.md)). Этот subset проверяет затронутый render/POST, privacy/readback, реальную PostgreSQL concurrency и persisted cooldown. Existing assertions не ослаблять.

- [ ] Native4типа × RU/AZ/EN × 360/390/768/1024/1280/1440 =72conflict cells. Две вкладки: current4→candidateA5; staleB2 получает настоящий409 с B2 в форме, A5 рядом, fresh token; revision/history/current/public4/count1 неизменны. Для Place дождаться реального cooldown перед stalePOST:429 имеет приоритет; не менять service order. Activity/Event CAS раньше cooldown, Specialist без этого cooldown.
- [ ] Ключевые native transitions на390/1440 RU/AZ/EN: keyboard/focus/scroll, explicit retry с соблюдением cooldown→pendingB→approvalB; alternative GET loadA/discardB; повторная гонка, long/scriptB, гостевой/чужой доступ и valid/invalid CSRF, loading/transport только с явным SIMULATED attribution. Все no-write readbacks — READ ONLY transactions/таймауты.
- [ ] Проверить rendered overflow/контраст/достижимость message и полей, console/network/static404 и новые native PNG. На текущем RED18InvalidStateError; после SSR409 перепроверить эту сигнатуру. Если для неё нужен общий JS/CSS или иной app файл — отдельный scope/approval; чистую консоль либо полныйPASS молча не объявлять.

## Task4 — evidence и остановка

- [ ] Сохранить новый уникальный fix-run REPORT/verification/source/commands-exits-counts/RED→GREEN/matrix/PNG hashes/diagnostics/NOT RUN-SIMULATED; проверить foreign state, index/HEAD/active_run/sharedMO. Failed attempts сохранить с исходной классификацией.
- [ ] Закрыть только фактически принятую SOCIAL03; guide обновить новой статусной записью, историю оставить. Затем отдельный PLAN04 по поручению пользователя;05–09 и module10 автоматически не начинать. ACCEPT09 один раз после всех SOCIAL tasks.

## Риски и self-review

Plan покрывает raw409 cause без смены service/transaction boundary. Fresh token используется только по новому явному действию автора, следующая конкурентная запись снова проходит CAS. B существует в response, а не в общем storage. Privacy/escaping/400/403/429 проверяются отдельно. Долговременное хранение B после ухода/Back не обещается. Cause/pre-patch источник подтверждены сейчас; bug fix/GREEN72cell acceptance ещё не выполнены. Scope остаётся3файловым, approval PENDING.
