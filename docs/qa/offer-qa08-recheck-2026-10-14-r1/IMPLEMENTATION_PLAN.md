# OFFER-QA-08 Declined Program Decision Implementation Plan

**Goal:** Владелец видит причину окончательного отказа и отклонённые изменения, понимает, какой текст опубликован и как отправить новое предложение.
**Architecture:** `declined` остаётся окончательным решением. Его payload показывается отдельно и только для чтения; editable form остаётся на approved/live baseline. `rejected` остаётся возвратом на доработку с существующим candidate overlay. Review/propose/ACL/CAS/propagation services не меняются.
**Tech Stack:** existing Django context/template, localized inline copy, scoped organization CSS, targeted Django tests/native browser.
**Spec:** `docs/qa/module05-2026-10-10-r1/findings/OFFER-QA-08.md`; fresh [REPORT](REPORT.md).

## Authorization / exact scope

План предъявлен2026-10-14; пользователь ответил «дальше», разрешив реализацию этого scope. Реализация завершена; см. fresh REPORT. Один ID **OFFER-QA-08**, без09 и других findings. Последовательная работа root; выбранные lead responsibilities — Django/frontend owner, independent delegation не заявляется. Не commit/push/deploy/production. Сохранить incoming WORKTREE, active_run NONE и чужие стенды; только собственный isolated QA.

Ровно четыре source/test файла:

1. `src/catalog/controllers/program_workspace.py`: `_context` готовит безопасный readonly preview только для `declined`, только восьми editable program fields. Не добавлять declined к existing overlay и не менять POST/save/authorization.
2. `src/catalog/templates/pages/program_editor.html`: note для rejected/declined; отдельная declined proposal section, current-content heading/instruction, existing submit action с ясным смыслом нового предложения. RU/AZ/EN в существующем inline-copy стиле. Экранировать пользовательский текст.
3. `static/css/pages/organization_workspace.css`: только новые scoped `.org-program-decision`/`.org-program-decision-note`/`.org-program-proposal` selectors для длинного reason/payload, переносов и читаемого readonly списка. Existing organization/shared layouts не переделывать.
4. Новый `src/catalog/testcases/test_offer_qa08_program_declined.py`: meaningful rendering/lifecycle/security tests; existing assertions не менять.

QA/docs: новый `docs/qa/offer-qa08-fix-2026-10-14-r1/`, progress этого плана, scoped status links в continuation guide/module-acceptance-prompts. Own `.tmp` profile. Исторические отчёты и свежий RED recheck сохранить. PO/common MO, publication/moderation services, schema, dependencies и CI вне scope.

## Task 1 — Expose decision without reviving terminal candidate

- [x] Refresh HEAD/branch/dirty/active_run and exact incoming file hashes; проверить реальные source/runtime/locale receipts. Fresh declined native RED уже сохранён в recheck; перед patch добавить failing behavior test ниже.
- [x] В `_context` сохранить existing initial overlay `draft/pending/rejected`. После его построения добавить `declined_changes=[]` и заполнить только если revision.status == `declined`. Allowlist берётся из реально имеющихся editable `initial` keys **до** добавления hidden expected/revision versions. Не рендерить произвольные revision JSON keys/schema metadata/hidden controls.
- [x] Preview содержит только payload keys из allowlist: name_az/ru/en, description_az/ru/en, category, subcategory. Поля сортируются в существующем редакторном порядке. Значения category/subcategory разрешить через существующие Category/Subcategory querysets и `name_i18n()`; None/missing choice отобразить как «—», не показывать raw foreign IDs. Для текста сохранять пустую строку, переносы и HTML как текст.

Пример формы context, без изменения services:

```python
labels = {
    'name_az': t('Название (AZ)', 'Ad (AZ)', 'Name (AZ)'),
    'name_ru': t('Название (RU)', 'Ad (RU)', 'Name (RU)'),
    'name_en': t('Название (EN)', 'Ad (EN)', 'Name (EN)'),
    'description_az': t('Описание (AZ)', 'Təsvir (AZ)', 'Description (AZ)'),
    'description_ru': t('Описание (RU)', 'Təsvir (RU)', 'Description (RU)'),
    'description_en': t('Описание (EN)', 'Təsvir (EN)', 'Description (EN)'),
    'category': t('Категория', 'Kateqoriya', 'Category'),
    'subcategory': t('Подкатегория', 'Alt kateqoriya', 'Subcategory'),
}
declined_changes = []
if revision and revision.status == 'declined':
    for name, label in labels.items():
        if name not in revision.payload:
            continue
        value = revision.payload[name]
        if name in ('category', 'subcategory'):
            model = Category if name == 'category' else Subcategory
            choice = model.objects.filter(pk=value).first() if value is not None else None
            value = choice.name_i18n() if choice else '—'
        declined_changes.append({'field': name, 'label': label, 'value': value})
```

- [x] Template note block явно различает `rejected` («Вернули на доработку») и `declined` («Предложение отклонено») без переименования canonical enum. Note autoescaped, `role=status`, multiline wrap. Readonly preview вне POST form:

```django
<section class="org-program-proposal" aria-labelledby="declined-proposal-title">
  <h3 id="declined-proposal-title">{% if CURRENT_LANGUAGE == 'az' %}İmtina edilmiş dəyişikliklər{% elif CURRENT_LANGUAGE == 'en' %}Rejected changes{% else %}Отклонённые изменения{% endif %}</h3>
  <dl>{% for change in declined_changes %}
    <dt>{{ change.label }}</dt>
    <dd data-declined-field="{{ change.field }}">{{ change.value|default_if_none:'—' }}</dd>
  {% endfor %}</dl>
</section>
```

- [x] Declined instruction RU «Ниже — текущая опубликованная версия. Исправьте нужные поля и отправьте новое предложение на проверку.»; AZ «Aşağıda hazırda dərc olunmuş versiya göstərilir. Lazımi sahələri düzəldib yeni təklifi yoxlamaya göndərin.»; EN «The current published version is shown below. Edit the required fields and submit a new proposal for review.» Preview heading AZ «İmtina edilmiş dəyişikliklər», EN «Rejected changes». Empty payload имеет localized empty text, не пустой декоративный блок. Если live target ещё draft, wording говорит «текущая версия», а не falsely «опубликованная»; использовать `program.status == 'published'` для этого различия.
- [x] Reason heading RU «Причина решения», AZ «Qərarın səbəbi», EN «Decision reason». При declined existing button label RU «Отправить новое предложение», AZ «Yeni təklif göndər», EN «Submit a new proposal»; other states сохраняют existing labels/action. Form hidden CAS/version, branch impact confirmation и bound invalid POST form сохраняются.
- [x] Scoped CSS: `min-width:0; max-width:100%; overflow-wrap:anywhere` на decision/proposal; note/preview dd `white-space:pre-wrap; overflow-wrap:anywhere`; компактный readable dl. Не менять global form widths/checkbox behavior/layout.

## Task 2 — RED/GREEN targeted regression

- [x] Создать test class с fictional owner/outsider/staff, organization/program approved baseline и linked Activity fixture через существующие authorized structural hooks. Candidate создаётся `publication.propose`; decision — `publication.review`, не ручная запись enum.
- [x] Первый RED method `test_declined_owner_sees_reason_and_readonly_proposal_without_live_overlay`: propose description «Proposed», final_reject note «Reason», owner GET; assertContains Reason/Proposed, form.initial.description_az == approved baseline, declined context содержит только proposed field; program и linked Activity live unchanged. До patch причина/preview отсутствуют — этот failure сохранить.

```python
revision = publication.propose(
    actor=self.owner, target_type='program', target_id=self.program.pk,
    patch={'description_az': 'Proposed'}, schema_version=publication.SCHEMA_VERSION,
    expected_version=self.program.content_version, revision_version=0, submit=True,
)
publication.review(actor=self.staff, revision_id=revision.pk,
    version=revision.version, approve=False, final_reject=True, note='Reason')
self.client.force_login(self.owner)
response = self.client.get(self.detail_url)
self.assertContains(response, 'Reason')
self.assertContains(response, 'Proposed')
self.assertEqual(response.context['form'].initial['description_az'], 'Approved')
```

- [x] Остальные focused methods: rejected сохраняет note+editable proposal; pending/draft editable overlay не меняется; approved не показывает obsolete rejection section; terminal correction/resubmit остаётся gated и approve распространяет только approved data, сохраняя local Activity fields; stale CAS/invalid impact POST оставляют reason/preview и submitted bound form; outsider GET/POST404 и отсутствие private note; note/proposal HTML autoescaping + RU/AZ/EN labels + nullable taxonomy/blank proposed values/unknown payload key exclusion. Без новых бизнес-правил/ослабления existing assertions.
- [x] GREEN новый test class + affected existing `catalog.testcases.test_task33_program_workspace.ProgramWorkspaceTests.test_create_and_edit_program_has_separate_right_and_pending_impact`, `catalog.testcases.test_task33_program_workspace.ProgramWorkspaceTests.test_linked_activity_uses_approved_program_and_keeps_local_group`, `catalog.testcases.test_task33_publication.PublicationTests.test_pending_and_rejected_keep_approved_live`, `catalog.testcases.test_task33_publication.PublicationTests.test_program_propagates_only_common_active_links`. Перед запуском проверить exact discovered names/classes; использовать только эти names и own isolated settings. Record exact selected IDs/counts/exits. Full module/global wrapper не запускать на этом repair.

## Task 3 — Native acceptance / evidence

- [x] Новый own fix profile, fresh RU/AZ/EN compiled locales/manifest/sole LOCALE_PATHS до django.setup; DJANGO_TESTING=1, loopback own PostgreSQL/DB/cache/media/private-media/email, fictional accounts, external egress blocked. Не копировать checkout .env. Runtime entry=startup=disk доказать заново.
- [x] Native owner submit → moderator return → owner correction/reload/resubmit → final reject → owner reload. Подтвердить reason и readonly proposal; main editable form live baseline. Через native edit/submit создать новое предложение, затем approve/reload. До approve Program/branch live не меняется; после — canonical propagation, local fields сохраняются. ORM только fixtures + READ ONLY transaction с timeout10s/lock2s для checkpoints.
- [x] Declined/rejected/new-proposal states RU/AZ/EN ×360/390/768/1024/1280/1440; длинный/multiline reason/text, current/proposed distinction, keyboard/focus, note visibility, submit/impact/error/conflict, overflow, console/network и PNG manifest. Readonly preview не имеет successful form controls и не меняет submission. Existing impacted organization editor layout smoke в own fixture, не полный другой модуль.
- [x] Reviewable four-file diff, commands/exits/method counts, snapshot/source/runtime/locales, native result/PNG manifest, retained RED/harness/environment failures, NOT RUN limits. Только OFFER-QA-08 CLOSED LOCAL при фактическом acceptance; OFFER-QA-09 OPEN и full ACCEPT05 остаются до отдельного выбора/модульной проверки.

## Stop / risk boundaries

Окончательный отказ не превращать в «вернули». Принудительное применение declined payload к editable form или изменение publication.revision base/reset semantics — существенное расширение, отдельно согласовать. Новый submit уже существует: никаких дополнительных service/API/schema изменений для его разрешения не требуется. История одного candidate row до следующего submit остаётся текущим canonical contract; долговременный moderation archive не вводить этим repair. При нужде изменить дополнительные source files сначала представить extension, независимый authorized QA продолжать.

## Completion2026-10-14

OFFER-QA-08 CLOSED LOCAL: [REPORT](../offer-qa08-fix-2026-10-14-r1/REPORT.md),16unique targeted methods accepted15+1,353native assertions,66PNG. Original failed16-method batch retained; no full rerun after test-only canonical redirect correction/empty-preview markup refinement. Actual four-file scope preserved. Full ACCEPT05/global/external/production NOT RUN. Next PLAN09 not started.
