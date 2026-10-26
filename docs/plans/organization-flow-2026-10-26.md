# Organization Flow Implementation Plan

> **For agentic workers:** выполнять последовательно по задачам после согласования scope. Использовать доступные systematic-debugging, test-driven-development и verification-before-completion; не предполагать наличие дополнительных skills и не запускать специалистов автоматически.

**Goal:** сделать создание организации коротким, а публикацию, очередь и счётчики достоверными во всех точках входа.

**Architecture:** Organization остаётся общим профилем сети, Place — конкретным филиалом. Создание и изменение используют единый контракт новых контактов; публикация проходит через существующие versioned publication services. Presentation получает общие predicates статусов и постепенно раскрывает дополнительные возможности.

**Tech Stack:** существующие Django forms/services/admin, PostgreSQL, серверные templates, vanilla JS/CSS, RU/AZ/EN.

**Spec:** `docs/reports/organization-flow-audit-2026-10-26.md`, особенно ORG-A01–A09 и раздел 8.

## Global Constraints

- Статус плана: APPROVED LOCAL IMPLEMENT — пользователь согласовал исправление всех описанных пунктов. Реализация и приёмка: `docs/reports/organization-flow-implementation-2026-10-26.md`. Deploy и изменение production не разрешены этим scope.
- Сохранить dirty WORKTREE и чужие изменения. Никаких reset/clean/stash, автоматических commit/push.
- Организация создаётся без филиала, адреса, координат и цен. Название AZ — единственное обязательное поле первоначального создания.
- Не удалять программы/команду, не менять модель прав ради упрощения UI.
- Сохранить request/confirm/detach, CSRF, object permissions, ownership/content/revision versions и draft recovery.
- Не объявлять все филиалы публичными при публикации сети; public visibility сети и каждого Place проверяются отдельно.
- Тесты: DJANGO_TESTING=1, очищенное окружение, отдельные PostgreSQL/cache/media/email, внешние интеграции выключены.
- После каждой задачи — целевые проверки и репрезентативные общие сценарии; полный corpus организаций один раз в конце. Production NOT RUN до отдельного разрешённого release scope.

## Файлы и границы ответственности

| Файлы | Ответственность |
|---|---|
| `src/catalog/domain_admin/business.py` | формы админа, counts/filters, обычные и массовые переходы |
| `src/catalog/services/publication.py` | авторитетные переходы publication/review, версии/права |
| `src/catalog/services/organization_ownership.py` | создание и безопасные связи владельцев; без прямого присвоения чужого места |
| `src/catalog/services/phone_numbers.py` | существующая нормализация новых/изменённых контактов |
| `src/catalog/controllers/organization_workspace.py` | bound forms/errors, контекст этапов и разделов |
| `src/catalog/templates/pages/organization_create.html` | короткое создание с компактной подсказкой |
| `src/catalog/templates/pages/organization_workspace.html` | разделы workspace и состояния связи |
| `src/catalog/templates/pages/account_notifications.html` | понятное подтверждение связи |
| `src/catalog/templates/admin/catalog/business/change_form.html` | ошибки и полезные вкладки админа |
| `static/js/organization_workspace.js` | переключение разделов с сохранением существующего recovery/CSRF |
| `locale/{az,ru,en}/LC_MESSAGES/django.po` | полный перевод изменяемых текстов |
| `src/catalog/testcases/test_organization_flow_consistency.py` | новые regression scenarios ниже |

Перед изменением CSS найти существующие organization styles по классам templates и дополнить их; не создавать параллельный дизайн/фреймворк. Общие BusinessEditor изменения проверить также на его других наследниках.

## Task 1: Правильные счётчики и очередь

Consumes: `Organization.status`, `VolunteerPlaceRevision.status`, связь places. Produces: `_dashboard_counts`, `_quick_filters` с одинаковыми predicates; published и pending edits представлены раздельно.

- [ ] Добавить regression на два филиала одной сети. Минимальное ядро теста в новом модуле:

```python
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import TestCase
from catalog.models import Organization
from catalog.services.organization_ownership import request_join
from catalog.testcases.utils import create_quality_place

class OrganizationDashboardRegressionTests(TestCase):
    def test_two_branches_do_not_multiply_total(self):
        owner = get_user_model().objects.create_user('org_dashboard_owner')
        org = Organization.objects.create(owner=owner, name_az='Audit network')
        Organization.objects.create(owner=owner, name_az='Other network')
        for name in ('Audit branch one', 'Audit branch two'):
            place = create_quality_place(owner=owner, created_by=owner, name=name)
            request_join(actor=owner, place_id=place.pk, organization_id=org.pk)
        counts = admin.site._registry[Organization]._dashboard_counts()
        self.assertEqual(counts['total'], 2)
        self.assertEqual(counts['with_places'], 1)
```

- [ ] В отдельном тесте создать draft org, `publication.propose(...submit=True)` и проверить один pending revision в queue; повторить для published org с pending edits, не скрывая её из published.
- [ ] Запустить новый модуль: на исходном поведении ожидать падение counts и queue assertions; зафиксировать результат до исправления.
- [ ] Использовать distinct counts и общий revision predicate; не менять `Organization.status` на pending только ради UI. Сохранить совместимость существующего pending base status.
- [ ] Проверить 0/1/2 филиала, удалённый филиал, archived org, draft/pending/rejected/approved revision. Отфильтрованные строки и счётчик должны совпадать по ID, а не только числу.

## Task 2: Публикация, которой можно доверять

Consumes: existing `publication.propose`, `publication.review`, `publication.unpublish` и их permission/version contracts. Produces: admin bulk action через тот же авторитетный переход, без прямого `status` save.

- [ ] Regression: staff создаёт org draft с revision, применяет bulk publish. Успех допустим только при approved candidate и гостевом public 200; иначе явный отказ с причиной, объект не подписан «успешно опубликован».
- [ ] Negative cases: ограниченный staff без review permission; чужой object scope; устаревшая revision; archived org; mixed batch из допустимых/недопустимых объектов.
- [ ] Запустить эти cases до фикса и увидеть исходный public 404 / неверный переход.
- [ ] В bulk использовать существующий review service, передавая актуальную revision/version. Если объект не имеет подходящей версии, пропустить с понятной причиной вместо создания одобрения напрямую.
- [ ] Для bulk draft переиспользовать `unpublish` с его проверками. Успешные/пропущенные/ошибочные результаты сообщать по фактическому исходу; обеспечить отсутствие частично применённого перехода внутри одного объекта.
- [ ] Проверить обычное одобрение, снятие с публикации, конфликт версии, audit trail, public directory/detail, сохранение опубликованного контента при pending edits.

## Task 3: Обязательность, контакты и сохранение ввода

Consumes: OrganizationForm, OrganizationCreateForm, OrganizationCandidateForm, `_create`, `normalize_contact_patch`. Produces: одинаковые правила новых контактов и локализованные field errors на bound forms.

- [ ] Regression: admin submit `name_az=''`, `name_ru='Сохранить этот текст'` — видимая ошибка AZ, исходное RU остаётся, объект не создан, redirect не стирает форму.
- [ ] Regression: owner/admin create с новым `phone='not-a-phone'` — ошибка именно phone и отсутствие созданного org. Для форм проверить required AZ; RU/EN остаются optional.
- [ ] Regression: исправление контакта валидным международным номером одинаково работает create/edit; пустой optional контакт допустим. Неизменённый legacy-contact не блокирует несвязанную правку.
- [ ] Запустить regression до реализации и зафиксировать FAIL.
- [ ] Подключить существующую нормализацию к `_create` только для Organization, до full_clean/save; поддержать mapping service ValidationError к form fields. Не добавлять второй JS-валидатор с иными правилами.
- [ ] В BusinessEditor сделать AZ required для OrganizationForm; service validation errors вернуть на bound form с сохранёнными полями. Не менять поведение остальных бизнес-редакторов без целевой проверки.
- [ ] В `_organization_save_errors` сохранить специальные version-conflict сообщения, обычные validation errors привязать к полям. Проверить invalid URL, whitespace name, duplicate warning, schema/revision/content conflicts.

## Task 4: Короткое создание и рабочий экран

Consumes: действующие формы и состояния revisions/branches/team. Produces: создание без новых обязательных требований; workspace «Филиалы / Профиль / Дополнительно».

- [ ] На макете/локальном prototype проверить 390 и 1280 px: заголовок, одно предложение про Organization/Place, поле AZ и основная кнопка видны без длинного обучающего блока. Пояснение «Чем отличается от филиала?» раскрывается по запросу.
- [ ] Сохранить optional translations/contacts/description. Подтверждение дубликата показывать только при реальном duplicate conflict.
- [ ] После создания: «Профиль создан», основная кнопка «Добавить филиал» → «Создать новое место» / «Подключить существующее», доступна «Позже». Создание нового места ведёт к его editor, подключение — к существующему preview/consent.
- [ ] Три раздела переключают содержимое; URL/hash сохраняет открытый раздел и возвращает пользователя к форме с ошибкой. Без JS остаются доступные ссылки/содержимое. Не терять unsaved draft при переключении.
- [ ] Профиль: сведения/контакты, status pending/rejected/published, понятная кнопка отправки; «Дополнительно»: программы, команда и specialist cooperation, только при соответствующих правах. Team не участвует в readiness запуска.
- [ ] Не вводить процент заполнения без backend specification. Показать конкретные этапы и причину недоступного действия; не требовать branch publication для сохранения Organization.
- [ ] Browser acceptance: пустая/одна/много организаций; 0/1/много филиалов; нет прав; ошибки; draft restore; RU/AZ/EN; клавиатура, фокус и отсутствие скрытого focusable содержимого.

## Task 5: Список, подтверждение связи и локализация

Consumes: counts/statuses Task 1–2, existing notification/request services. Produces: один понятный список и осмысленное согласие второго владельца.

- [ ] В админском списке оставить один ряд status filters/counts; default columns: название, публикация/изменения, владелец, филиалы, обновление. Existing column chooser сохраняется для телефона/программ.
- [ ] Убрать пустую техническую вкладку, версии оставить hidden; required AZ и errors доступны в активном разделе и summary.
- [ ] Для standalone place показать «Самостоятельное место», для pending — ожидание стороны, для stale — причину и recovery action. Не показывать устаревшую связь месту, которое никогда не было подключено.
- [ ] В уведомлении показать название места и сети; вместо мгновенного неинформированного подтверждения открыть актуальный preview последствий. Финальное действие остаётся POST+CSRF с проверкой текущего владельца и версий через существующий service.
- [ ] На public WA не выводить обещание WhatsApp только по телефону: согласовать явный opt-in «WhatsApp на этом номере» для нового/изменяемого контакта; миграция старых данных исключена из scope.
- [ ] Выбор владельца при создании staff выделить отдельным продуктовым решением до реализации. До него явно показывать текущего назначаемого владельца; не добавлять произвольное FK-присвоение.
- [ ] Перевести затронутые подписи/ошибки на RU/AZ/EN, проверить реальный DOM EN/AZ на оставшийся русский UI-текст. Названия/описания пользовательского контента могут иметь AZ fallback с пояснением.

## Task 6: Итоговая приёмка

- [ ] Один финальный запуск существующих 13 test modules из audit report + нового regression module на изолированном runtime. Не менять assertions ради зелёного результата.
- [ ] Репрезентативно проверить другие BusinessEditor consumers и Place contacts, если менялись общий error handler/normalization/publication service.
- [ ] Browser E2E: owner create → own branch create → editor draft → optional submission; отдельно connect self + foreign → preview → consent → second-owner preview/confirm → staff review → guest directory/detail.
- [ ] Дополнительно выполнить программу/команду локально с LocMem email: приглашение, принятие другим пользователем, реальный scoped access, отказ stranger, stale grant; не называть это live email delivery.
- [ ] Browser negative: invalid contact с сохранением ввода, duplicate create, missing AZ, rejected/pending changes, stale second tab, forbidden user, CSRF failure, double submit, mixed bulk.
- [ ] 5 поверхностей × RU/AZ/EN × 390/768/1024/1280/1440 px; измерить horizontal overflow, active form visibility, focus order и размеры интерактивных целей. Сохранить screenshots и JSON с результатами.
- [ ] Финальный report: каждый ORG-A01–A09 CLOSED/OPEN с evidence, exact command/exit code, LOCAL HEAD/WORKTREE, NOT RUN и отдельно отсутствие production verification.

## Критерий окончания

1. Counts совпадают с уникальными организациями; queue содержит каждую pending revision ровно один раз.
2. «Опубликовано успешно» означает выполненный authoritatively approved переход и ожидаемую гостевую видимость; bulk и обычный путь согласованы.
3. Ошибки полей конкретны, локализованы, введённые данные сохранены; контакты проверяются одинаково.
4. Создание по-прежнему требует одно поле; дополнительные инструменты не навязаны; подтверждение связи содержит обе стороны и последствия.
5. Regression + репрезентативные shared scenarios + browser matrix подтверждены. Оценка 8.5/10 остаётся целевой до выполнения этих условий.

План не предусматривает автоматических commit/push/deploy. Следующий разрешаемый scope — локальная реализация Task 1–6 с повторной приёмкой; server release согласуется отдельно.
