# SOCIAL-QA-02 Implementation Plan

**Статус:** PLAN COMPLETE; scope approval pending. 2026-10-16, Asia/Baku. Candidate diff не применён.

**Goal:** автор видит последнее релевантное решение об отказе, причину и отклонённый текст и может исправить отзыв через существующую форму.

**Architecture:** controller выбирает последнее rejected решение только из author-owned head и только когда оно остаётся последней редакцией без нового candidate. Шаблон показывает отдельный private feedback block. Публичная current и редактор candidate/current сохраняют действующие rating/text/CAS contracts SOCIAL01; отклонённый текст доступен рядом, автоматического замещения текущего редактора не добавляем.

**Tech Stack:** действительные Django6.0.2/Python3.12.3/PostgreSQL17.10, SSR/vanilla browser; без новой зависимости.

**Spec:** [PLAN SOCIAL-QA-02](../continuation-and-repair-prompts-2026-10-11.md#repair-SOCIAL-QA-02), [исторический finding](../module09-2026-10-10-r1/findings/SOCIAL-QA-02.md), [свежий REPORT](REPORT.md).

## Global constraints

- Только SOCIAL-QA-02, P2. Новая причина не входит в ранее одобренный SOCIAL01.
- `/home/ramin/kidsmap`, task33-progress, HEAD e4e05cc213b34e2d771ecb854901bfd016d1db51 +dirty WORKTREE, active_run NONE. Source baseline: [proposal-source-baseline.json](proposal-source-baseline.json).
- DJANGO_TESTING=1, собственные PostgreSQL/DB/cache/media/private-media/email, fictional data, blocked внешние обращения. Проверить sole fresh RU/AZ/EN LOCALE_PATHS до django.setup. .env/production credentials не загружать, shared MO не перезаписывать.
- Без commit/push/deploy/production/reset/clean/stash и назначения active_run. Чужое состояние и все прежние отчёты сохранить.
- Только targeted RED до patch, targeted GREEN +малый affected subset после. Full ACCEPT09 один раз после всех задач, сейчас не запускать.
- Existing assertions не ослаблять. SOCIAL01 tests и его контракт сохраняются.

## Точные application/test файлы

1. **Modify** `src/catalog/controllers/typed_reviews.py` — последние author-owned decision и context key `own_review_decision`.
2. **Modify** `src/catalog/templates/catalog/typed_reviews.html` — отдельный локализованный feedback block с escaped reason/text/rating, используя существующий CSS.
3. **Create** `src/catalog/testcases/test_social_qa02_rejection_feedback.py` —4новых behavior/privacy regressions.

QA helpers/browser PNG/REPORT/verification нового fix-run и текущий статус guide входят в evidence scope. Services/moderation/ACL/CAS/cooldown/schema/PO/JS/CSS и предыдущий regression-файл не меняются.

## Task 1: targeted RED → feedback rendering → GREEN

**Consumes:** `own_review` уже фильтруется по target/request.user/is_current; `head.revisions`, `status`, `rejection_reason`, `text`, `rating`. **Produces:** private feedback только соответствующему автору, если последняя submitted revision rejected и новой candidate нет. Новая pending/approved версия скрывает старое сообщение.

- [ ] Сверить actual checkout/source и авторизацию этого плана. Создать собственный уникальный fix-run, зафиксировать entry/source/index/containers/processes. Profile reuse допустим только с проверенными ownership/source/изоляцией; старые PID/порты не считать актуальными.
- [ ] Скопировать готовый [candidate test](candidate/test_social_qa02_rejection_feedback.py) в точный новый application test path. Запустить на исходном приложении только:

```bash
.venv/bin/python docs/qa/social-qa02-fix-2026-10-16-r1/runtime.py test catalog.testcases.test_social_qa02_rejection_feedback.TypedReviewRejectionFeedbackTests
```

Этот runtime создаётся в новом fix-run по действующему isolated QA примеру. RED ожидается по отсутствию `data-review-rejection`/reason/rejected text; environment/harness failure не считать app RED. Готовые4methods пока NOT RUN.

- [ ] Применить только [proposed.diff](proposed.diff). Полные будущие файлы: [controller](candidate/typed_reviews.py), [template](candidate/typed_reviews.html). Controller перед render:

```python
own_decision = None
if own is not None and own.candidate_revision_id is None:
    latest = own.revisions.order_by('-created_at', '-pk').first()
    if latest is not None and latest.status == 'rejected':
        own_decision = latest
```

Передать `'own_review_decision': own_decision` в существующий render context. Не читать review response/report records и не выбирать history другого пользователя. Не менять `moderate_candidate`: очищение candidate pointer сохраняется.

Шаблонный block расположен внутри authenticated own-review section перед текущим candidate status/form:

```django
{% if own_review_decision %}
<aside class="review-item" aria-labelledby="review-rejection-title" data-review-rejection>
  <h3 id="review-rejection-title">{% if language == 'ru' %}Редакция отклонена{% elif language == 'en' %}Version rejected{% else %}Versiya rədd edilib{% endif %}</h3>
  {% if own_review_decision.rejection_reason %}<p><strong>{% if language == 'ru' %}Причина отказа{% elif language == 'en' %}Rejection reason{% else %}Rədd səbəbi{% endif %}</strong></p><blockquote>{{ own_review_decision.rejection_reason|linebreaks }}</blockquote>{% endif %}
  <p>{% if language == 'ru' %}Отклонённая редакция{% elif language == 'en' %}Rejected version{% else %}Rədd edilmiş versiya{% endif %} · {{ own_review_decision.rating }} / 5</p>
  <blockquote>{{ own_review_decision.text|linebreaks }}</blockquote>
</aside>
{% endif %}
```

Пустая необязательная reason не выдумывается; status/rejected text остаются видимыми. Existing `.typed-reviews` уже имеет overflow-wrap:anywhere и стили aside/blockquote/focus. CSS правка в план не входит.

- [ ] Обновить только новый fix-run startup manifest, включить новый test, сохранить RED source отдельно. GREEN — те же4новых methods +следующий affected subset:

```bash
.venv/bin/python docs/qa/social-qa02-fix-2026-10-16-r1/runtime.py test \
 catalog.testcases.test_social_qa02_rejection_feedback.TypedReviewRejectionFeedbackTests \
 catalog.testcases.test_social_qa01_rating_readback.TypedReviewRatingReadbackTests.test_first_rejection_retains_author_rating \
 catalog.testcases.test_social_qa01_rating_readback.TypedReviewRatingReadbackTests.test_rejected_edit_restores_approved_rating \
 catalog.testcases.test_task33_reviews.ReviewVersionContractTests.test_pending_edit_keeps_approved_projection_and_one_rating \
 catalog.testcases.test_task33_reviews.ReviewVersionContractTests.test_nonstaff_and_stale_decision_cannot_publish
```

Четыре новых methods покрывают4типа: первый отказ; отказ edit с сохранной public projection и outsider/guest privacy; correction/resubmit→pending→approve скрывает старое решение; reason/text с literal script/HTML безопасно escaped. Unit-only cooldown0 явно SIMULATED. Общий11method SOCIAL01 набор без причины не повторять;4selected affected methods здесь обоснованы новыми controller/template consumers.

## Task 2: native acceptance и сохранность

- [ ] Проверить source/PID/template origins/MO manifest работающего собственного процесса. После patch перезапустить только свой runtime на новом manifest; прежние source/report artifacts не переписывать.
- [ ] Через UI create→reject с reason и approved→edit→reject для Place/Specialist/Activity/Event. Автор делает reload: status/reason/rejected text/rating доступны; public current4/count1 и существующий editor4 не меняются из-за отказа edit2. При первом отказе current отсутствует, editor сохранён3.
- [ ] Автор читает отклонённый текст, исправляет существующую форму и resubmit; после настоящего cooldown120s новая pending скрывает старую reason, current остаётся прежней до approval. После approval новый rating/count корректны. Не вводить виртуальные часы в native flow.
- [ ] Rendered RU/AZ/EN×360/390/768/1024/1280/1440 для двух новых rejected states четырёх типов; native key transitions RU/AZ/EN390/1440. Проверить длинную/пустую reason, literal HTML/script, keyboard/focus/scroll, contrast существующего aside, console/network и PNG. Браузер не заменять HTTP200/jsdom/source inspection.
- [ ] Native outsider/guest/другой author не видят private feedback/reason/rejected text; публичный live остаётся видимым. Readonly transaction с5s statement/2s lock timeout сверяет latest/current/candidate/revisions и count/average. Приватные business reports вообще не участвуют в новом selector/context.
- [ ] Зафиксировать commands/exits/counts/PNG manifest/NOT RUN/SIMULATED и preservation entry files/sharedMO/index/HEAD/branch/active_run/containers/processes. Известный общий view-transition event из предыдущего run сохраняется отдельно; его исправление не входит. Новую причину/необходимый дополнительный application файл сначала согласовать.
- [ ] При фактическом acceptance закрыть только SOCIAL02, сохранить новый REPORT/verification и текущий статус guide. Следующий PLAN SOCIAL03; full ACCEPT09 остаётся отложен до завершения задач. Module10 автоматически не начинать.

## Риски и self-review

`head.rejection_reason` недостаточно: после отклонения edit current projection остаётся approved и причина хранится в rejected revision. Выбор любой старой rejected revision тоже неверен — показывать её после исправленной pending/approved нельзя. Поэтому рассматриваем последнюю submitted revision только собственного head и оставляем moderation service/CAS неизменными.

Редактор не подменяется отклонённой версией автоматически: rejection feedback показывает её отдельно. Так сохраняется уже принятый SOCIAL01 contract и автор видит, что именно было отклонено. Если потребуется отдельная кнопка restore, это самостоятельное расширение UI scope.

Свежий recheck:16rendered states,40PASS/24FAIL одной группы причин,16PNG; persisted reasons подтверждены8readonly records. Source968 MATCH. Два existing application файла и один новый test названы точно; candidates unapplied, новые4tests NOT RUN. Historical FAIL не использовался как доказательство current failure.
