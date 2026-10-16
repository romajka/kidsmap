# SOCIAL-QA-01 Implementation Plan

**Дата:** 2026-10-16, Asia/Baku. **Статус:** PLAN COMPLETE; application patch НЕ применён; scope approval pending.

**Goal:** сохранённая оценка вновь выбрана в редакторе четырёх типов отзывов после reload.

**Architecture:** общий SSR-шаблон читает ту же author-owned модель, что уже используется для текста и CAS token. При наличии candidate берём её rating; иначе берём rating head, который service проецирует из одобренной current revision либо сохраняет после первого отказа. Новому отзыву остаётся пустой required select.

**Tech Stack:** Django6.0.2 templates, PostgreSQL17.10, Python3.12.3, native Chromium153.0.8010.36.

**Spec:** [PLAN SOCIAL-QA-01](../continuation-and-repair-prompts-2026-10-11.md#repair-SOCIAL-QA-01), [свежий REPORT](REPORT.md), [исходный finding](../module09-2026-10-10-r1/findings/SOCIAL-QA-01.md), [module13 corroboration](../module13-2026-10-11-r1/findings/SOCIAL-QA-01.md).

## Global constraints

- Только ID **SOCIAL-QA-01**, P2, причина **REVIEW-RATING-READBACK**. SOCIAL02–09 не входят.
- /home/ramin/kidsmap; task33-progress; HEAD e4e05cc213b34e2d771ecb854901bfd016d1db51 +чужой dirty WORKTREE; active_run NONE. Перед patch сверить hashes из runtime-source-final.json.
- DJANGO_TESTING=1; собственный PostgreSQL/DB/cache/media/private-media/email; .env не загружать; внешние обращения блокировать. Shared MO не переписывать. Единственный проверенный LOCALE_PATHS до django.setup.
- Без reset/clean/stash, назначения active_run, commit/push/deploy/production. Чужие процессы не перезапускать.
- До patch только целевой RED. После patch целевые и затронутые проверки. Полный ACCEPT-09 один раз после всех задач модуля, сейчас НЕ запускать.
- Все существующие assertions сохранить. Новую причину/существенное расширение сначала согласовать.

## Точные application/test файлы

1. **Modify** `src/catalog/templates/catalog/typed_reviews.html:24` — только восстановление selected в существующем select.
2. **Create** `src/catalog/testcases/test_social_qa01_rating_readback.py` — семь новых meaningful regression methods; готовый исходник в [candidate/test_social_qa01_rating_readback.py](candidate/test_social_qa01_rating_readback.py).

QA helpers/REPORT/verification/browser scripts/PNG нового уникального fix-run и текущая строка статуса модуля — evidence этого же scope. Controller, services, schema, CSS, JS, PO и существующие tests править не требуется.

## Task 1: RED → минимальное восстановление → GREEN

**Consumes:** `own_review.candidate_revision`, `own_review.rating`, existing typed editor routes/actions. **Produces:** selected option из сохранённой редакции; неизменные text/expected_revision_id/POST/moderation/ACL/cooldown contracts.

- [ ] Сверить checkout, baseline source и локальный runtime; создать уникальный fix-run. Исходный recheck сохранить.
- [ ] Скопировать новый test из candidate в точный application test path выше. До template patch запустить только:

```bash
.venv/bin/python docs/qa/social-qa01-recheck-2026-10-16-r1/runtime.py test catalog.testcases.test_social_qa01_rating_readback.TypedReviewRatingReadbackTests
```

При подготовке нового fix-run launcher путь меняется на него; settings сохраняют отдельную test DB `test_social01_r1` либо новый уникальный эквивалент. Не запускать prepare/seed второй раз на заполненной БД. RED должен доказывать пустое значение вместо сохранённого rating; технический сбой runner не считать RED приложения.

- [ ] Применить только [proposed.diff](proposed.diff); полный итоговый шаблон — [candidate/typed_reviews.html](candidate/typed_reviews.html). Суть:

```django
{% with editor_review=own_review.candidate_revision|default:own_review %}
  <select id="review-rating" name="rating" required>
    <option value="">—</option>
    <option value="1"{% if editor_review.rating == 1 %} selected{% endif %}>1</option>
    <option value="2"{% if editor_review.rating == 2 %} selected{% endif %}>2</option>
    <option value="3"{% if editor_review.rating == 3 %} selected{% endif %}>3</option>
    <option value="4"{% if editor_review.rating == 4 %} selected{% endif %}>4</option>
    <option value="5"{% if editor_review.rating == 5 %} selected{% endif %}>5</option>
  </select>
{% endwith %}
```

Существующие локализованный label, id/name/required и разметка вокруг остаются как в candidate. Никакой новой серверной нормы выбора rating.

- [ ] В новом fix-run сохранить RED manifest отдельно; после patch пересоздать его startup manifest на текущих исходниках, включив новый test. Исторический recheck baseline не переписывать. Повторить семь новых methods GREEN; отдельно один небольшой shared subset:

```bash
.venv/bin/python docs/qa/social-qa01-recheck-2026-10-16-r1/runtime.py test \
 catalog.testcases.test_task33_reviews.ReviewVersionContractTests.test_typed_review_page_uses_requested_language \
 catalog.testcases.test_task33_reviews.ReviewVersionContractTests.test_pending_edit_keeps_approved_projection_and_one_rating \
 catalog.testcases.test_task33_reviews.ReviewVersionContractTests.test_nonstaff_and_stale_decision_cannot_publish \
 catalog.testcases.test_task33_reviews.ReviewVersionContractTests.test_reaction_ids_and_original_revision_are_preserved
```

Семь новых methods проверяют четыре типа: пустой/чужой редактор, pending4, approved5, candidate2 поверх live5, первый отказ3, отказ edit1 поверх live4, GET→повторный POST выбранного rating с HTML escaping. Saved text и CAS token проверяются вместе с rating; average/count/live неизменны до approval. Override cooldown=0 действует только внутри новых unit tests и маркируется SIMULATED; browser основной lifecycle сохраняет действительный cooldown120s.

## Task 2: native acceptance данного ID

**Files:** новый уникальный `docs/qa/social-qa01-fix-…/` с browser scripts, PNG manifest, REPORT и verification; при необходимости только собственные `.tmp` настройки.

- [ ] Перезапустить только свой HTTP после новой startup source аттестации; проверить template origin/loaded hash/PID/current disk hashes, fresh locale manifest и единственный LOCALE_PATHS.
- [ ] Native login→select4→text→submit→reload→staff approve→author reload для Place/Specialist/Activity/Event. Реальное значение `4`, текст и token должны совпасть с readonly DB. Повторная отправка без изменения rating сохраняет4. Для cooldown дождаться срока, не менять product policy/время.
- [ ] Native edit2 при live4, reject и reload; отдельный первый rejected отзыв без current. ORM разрешён только для начальных fictional targets/accounts, проверяемые review transitions через UI.
- [ ] Проверить сохранённые empty/pending/approved/pending-edit/rejected состояния четырёх типов на **RU/AZ/EN ×360/390/768/1024/1280/1440**. Достаточно создавать состояние нативно один раз и читать его на18cells; не дублировать одинаковые mutation suites без причины. Key flows native по RU/AZ/EN390/1440.
- [ ] Tab/Shift+Tab в select/textarea/button, ArrowUp/Down/Enter/Space/Escape где применимо, focus-visible, required empty validation, длинный escaped text, безопасное public отображение, console/network и PNG. Transport loading/error и stale conflict — контроль сохранности существующего поведения в representative cells; SIMULATED transport явно пометить, известный SOCIAL03 не чинить.
- [ ] Readonly transactions с statement_timeout5s/lock_timeout2s: одна current head, candidate/live rating/text hashes, revision IDs, summary count/average; outsider/guest не видят чужую candidate. Пока candidate pending/rejected, опубликованные rating/count не меняются.
- [ ] Сохранить commands/exits/unique method counts, actual browser assertions и gaps. Сравнить entry files/shared MO/index/HEAD/branch/active_run/container identity/state; process continuity сообщать честно после interruption. Закрыть только SOCIAL01 при фактическом acceptance, затем отдельный PLAN SOCIAL02; full ACCEPT09 пока отложен.

## Риски и решение

Нельзя выбирать rating по `own_review.rating` без candidate precedence: у live head это старое публичное значение. Нельзя использовать только current revision: после первого отказа current отсутствует. Предложенный fallback сохраняет оба случая и не требует изменения domain service. Approval of this plan разрешает только указанные два application/test файла и их проверки/evidence. Любой дополнительный application файл требует отдельного согласования.

## Self-review

Текущий trigger подтверждён 8FAIL/20controlPASS и8PNG на исходном приложении. Два файла названы точно, candidate diff не применён. Новый regression исходник пока **NOT RUN**, RED/GREEN будет после approval. Rejected/pending-edit и18cells пока **NOT RUN** и включены в acceptance. Полный module09/global corpus не запущен. Commit steps исключены прямым запретом пользователя.
