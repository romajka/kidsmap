# ACCESS-QA-02 Implementation Plan

> **For agentic workers:** выполнить шаги последовательно в этом чате после одобрения именно этого документа. Текущий запуск — PLAN, application implementation NOT RUN. Один исполнитель, канонические роли последовательно; независимые subagents не запускались. Пользовательский запрет commit/push/deploy и заданный путь плана имеют приоритет над общими шаблонами skill.

**Goal:** получатель может явно отклонить актуальное приглашение места или организации из уведомлений, не получив и не изменив доступ.

**Architecture:** native CSRF POST с одним notification_id в URL. Controller разрешает только собственную текущую notification, проверяет свежие recipient/email, kind/type/version, expiry и владельца под canonical parent/invitation locks; затем вызывает существующий `business_team.decide_invitation(cancel=False)`. Бизнес-сервис и остальные API не переписываются.

**Tech Stack:** существующие Django6.0.2/PostgreSQL17, SSR templates и native forms; без нового JS/CSS/dependency/schema.

**Spec:** `docs/qa/continuation-and-repair-prompts-2026-10-11.md`, PLAN ACCESS-QA-02; `docs/qa/module07-2026-10-10-r1/repair-ACCESS-QA-02.txt`; свежий [REPORT](REPORT.md), [inbox matrix](inbox-matrix.js.result.json), [existing HTTP transition](existing-reject-api.js.result.json).

## Scope и approval

ID только **ACCESS-QA-02, P2**. Одобрения01/CSS и «дальше» разрешают продолжить recheck/plan, не являются approval этого нового implementation scope. Перед patch нужен отдельный ответ пользователя на этот документ.

Фактический checkout `/home/ramin/kidsmap`, branch `task33-progress`, HEAD `e4e05cc213b34e2d771ecb854901bfd016d1db51` + dirty WORKTREE, `active_run: NONE`. Перед реализацией повторно сверить snapshot/source. Если scoped source изменился, оценить применимость плана; не откатывать чужие изменения.

### Точные application/test файлы

| Действие | Файл | Изменение |
|---|---|---|
| Modify | `src/catalog/controllers/workflow_notifications.py` | recipient-scoped POST `reject_invitation`; небольшое выделение сборки текущего inbox context для GET и ответа409; eligibility нового действия и локализованные success/error сообщения |
| Modify | `src/catalog/templates/pages/account_notifications.html` | native форма отказа рядом с accept только для актуального invitation, csrf_token, локализованный текст; локализованный alert для stale/conflict |
| Modify | `src/catalog/urls.py` | импорт handler и ровно один `account_notification_reject` route |
| Create | `src/catalog/testcases/test_access_qa02_invitation_decline.py` | meaningful endpoint/state/recipient/concurrency regressions для обоих target types |

Документы/QA: новый уникальный `docs/qa/access-qa02-fix-<date>-rN/`, ignored собственный scratch, одна текущая module07 status note в guide. `services/business_team.py`, `services/workflow_notifications.py`, существующие assertions/test files, models/migrations/CI/owner-team/org editor/CSS/JS и PO не меняются. RU/AZ/EN строки следуют существующему inline pattern inbox; новые MO собираются только при изменившихся PO, иначе проверяется manifest своего profile. Обновление shared MO запрещено.

## Подтверждённая причина и граница

Свежие два invite отправлены владельцем через настоящие формы. В inbox нет decline у обоих типов во всех18cells:36FAIL; accept/keyboard/геометрия72PASS. Existing API reject обеих сущностей работает, CSRF/POST/route target/replay проверки11PASS. Значит, требуется связать inbox с уже реализованным отказом.

`decide_invitation` сам проверяет свежего actor, email и PENDING, но не проверяет expiry/current ownership. Прямой вызов из нового view без fresh guard недопустим. `_invitation_current` проверяет email/expiry/owner/base_ownership_version; для неизвестного entity_type возвращает True. Поэтому перед helper нужен строгий mapping и проверка `event_kind='team_invitation'`, `entity_version==1`. Это требования нового adapter, не изменение семантики старых API.

`entity_version==1` — версия invitation event, не произвольный клиентский номер. Ownership version — текущая версия target. Отказ не должен менять grant/его version/actions/scope; отсутствие нового гранта проверяется отдельно. `base_grant_version`/selected-scope контракты принятия остаются в canonical accept, не дублируются в UI.

## Task 1: регрессия до patch

- [ ] Создать только новый scoped test file. Fixtures: owner/recipient/other с `@example.invalid`, один own Place и Organization; invites через `business_team.invite`, notification через реальный emit. В browser acceptance invite создаётся только owner UI.
- [ ] Воспроизвести до реализации новый route/render/transition test. Содержательный RED — отсутствующая route или decline форма; сохранить точный native exit и assertion. Не выдавать import/setup/environment exception за application RED.

Минимальное ядро теста (импорты `get_user_model`, `TestCase`, `reverse`, `business_team`, модели и `create_quality_place` в указанном новом файле):

```python
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from catalog.models import (Organization, OrganizationGrant, OwnerTeamMembership,
                            WorkflowNotification)
from catalog.services import business_team
from catalog.testcases.utils import create_quality_place

class InvitationDeclineTests(TestCase):
    def setUp(self):
        U = get_user_model()
        self.owner = U.objects.create_user('qa02_owner', email='owner@example.invalid')
        self.recipient = U.objects.create_user('qa02_recipient', email='recipient@example.invalid')
        self.other = U.objects.create_user('qa02_other', email='other@example.invalid')
        self.place = create_quality_place(owner=self.owner, created_by=self.owner,
                                          with_subcategory=True)
        self.org = Organization.objects.create(owner=self.owner, created_by=self.owner,
                                                name_az='Uydurma təşkilat')

    def invitation(self, kind):
        target = self.place if kind == 'place' else self.org
        invite = business_team.invite(actor=self.owner, target_type=kind,
                                     target_id=target.pk, email=self.recipient.email)
        notice = WorkflowNotification.objects.get(
            event_kind='team_invitation', entity_type=f'{kind}_team_invitation',
            entity_id=invite.pk, recipient_user=self.recipient)
        return invite, notice

    def test_recipient_declines_both_kinds_without_access(self):
        self.client.force_login(self.recipient)
        for kind in ('place', 'organization'):
            with self.subTest(kind=kind):
                invite, notice = self.invitation(kind)
                url = reverse('account_notification_reject', args=[notice.pk])
                self.assertContains(self.client.get(reverse('account_notifications')), url)
                self.assertEqual(self.client.get(url).status_code, 405)
                self.assertEqual(self.client.post(url).status_code, 302)
                invite.refresh_from_db()
                self.assertEqual(invite.status, 'REJECTED')
                self.assertIsNotNone(invite.responded_at)
                self.assertFalse(OwnerTeamMembership.objects.filter(member=self.recipient).exists())
                self.assertFalse(OrganizationGrant.objects.filter(member=self.recipient).exists())
                self.assertNotContains(self.client.get(reverse('account_notifications')), url)
                self.assertEqual(self.client.post(url).status_code, 409)
                self.assertEqual(WorkflowNotification.objects.filter(
                    event_kind='team_invitation_decision',
                    entity_type=f'{kind}_team_invitation', entity_id=invite.pk).count(), 1)
```

Run в проверенном own fix profile: `python <own-runtime.py> test catalog.testcases.test_access_qa02_invitation_decline`. Доpatch ожидается RED, после — GREEN. Нельзя запускать через checkout manage.py/.env.

- [ ] Дополнить новые tests следующими конкретными trigger/assertions для **обоих** target types; каждый отказ сравнивает до/после status/responded_at, grants со всеми version/actions/scope и event/outbox count:

| Trigger | Ответ/инвариант |
|---|---|
| чужой notification_id; собственный user после изменения email |404, нет изменений |
| GET/без CSRF, `Client(enforce_csrf_checks=True)` |405/403; PENDING и counts прежние |
| POST с `entity_type`, `entity_id`, `target_id`, `invitation_id` вместо единственного URL id |400; body не выбирает объект, counts прежние |
| read-notification без event team_invitation; unknown entity type; invitation event version2 |404/403/409 согласно стадии проверки; никакого decision event |
| expiry в прошлом или NULL; status CANCELED/ACCEPTED/REJECTED |409, прежний status не переписан |
| ownership_version изменён; owner сменился при оставшемся PENDING fixture |409, нет grant/decision writes |
| invitation исчезла или parent удалён/архивирован |404/409 без побочных изменений |
| приглашение уже прочитано, но PENDING и актуально |отказ разрешён; read_at не подменяет статус приглашения |
| повтор/две независимые вкладки |ровно один success и одно decision/outbox, второй409 |
| concurrent accept/cancel/owner transfer и новый reject |последовательный canonical lock order; допустим ровно один terminal transition, без воскресшего grant или дублированного event |

Для двух thread/connection tests использовать PostgreSQL `TransactionTestCase`, `close_old_connections`, `Event`/barriers и timeouts: удержать `_locked_item`/parent locks на одном connection, отправить второй реальный Client POST на другом, затем освободить locks; проверить blocked-until-commit и свежий status. Не monkeypatch canonical business outcome и не исполнять race на SQLite. При реальной deadlock/необходимости менять canonical locking остановиться и отдельно согласовать расширение.

## Task 2: минимальный adapter и native control

- [ ] Добавить route рядом с accept/read:

```python
path('account/notifications/<int:notification_id>/reject/',
     reject_invitation, name='account_notification_reject'),
```

- [ ] В `workflow_notifications.py` использовать `@login_required`, `@require_POST` и `transaction.atomic()`. Алгоритм фиксирован:
  1. Из `_mine(request.user)` получить notification указанного URL id и event kind team_invitation. Не читать target/entity IDs из browser body; неожиданные поля кроме csrfmiddlewaretoken отклонить400.
  2. Разрешить только mapping `place_team_invitation → place`, `organization_team_invitation → organization`; иначе403. Вызвать существующий `business_team._locked_item(target_type, notification.entity_id, invitation=True)` **внутри atomic**, сохранив canonical Organization→Place→invitation lock order.
  3. Получить свежего actor через существующий canonical `_actor`, заново разрешить notification через `_mine(actor)` и сверить её kind/type/id с уже заблокированным invitation. Notification не блокировать раньше parent; изменившаяся identity — отказ, не redirect к другой сущности.
  4. До mutation проверить event version1 и `_invitation_current(current_notice, normalized_fresh_actor_email, timezone.now())` под удерживаемыми parent/invitation locks. Helper выполняет fresh query; неизвестный entity type уже отвергнут mapping. Expiry/status/owner/base_ownership_version не проверяются только на GET.
  5. Вызвать `business_team.decide_invitation(actor=actor, target_type=target_type, invitation_id=invitation.pk, cancel=False, expected_target_id=parent.pk)`. Не менять статус ORM update/save во view, не вызывать accept/cancel, не создавать/отзывать grants.
  6. После выхода из `with transaction.atomic()` и успешного commit добавить локализованное `messages.success` и redirect302 в inbox. Проверенный base.html уже выводит messages с role=status. Success не берётся из query string и не показывается при exception.
  7. Permission/foreign identity —403/404. Missing target —404. TeamConflict/ValidationError currentness —409 с перечитанным inbox и enum error context; raw exception/string не выводить. Exception handling находится снаружи atomic: перечитывать inbox после rollback/завершения transaction. Общий сборщик inbox context используется для GET и409, существующие accept/read/join actions сохраняются.

- [ ] Eligibility нового `item.can_reject`: team_invitation, известный mapping, event version1 и существующая currentness helper. Existing can_accept поведение не расширять. `read_at` не запрещает отказаться от ещё актуального invite.
- [ ] Добавить **отдельную native form**, не вложенную в accept:

```django
{% if item.can_reject %}
<form method="post" action="{% url 'account_notification_reject' item.pk %}">
  {% csrf_token %}
  <button type="submit" class="account-btn-action">{% if CURRENT_LANGUAGE == 'az' %}Dəvətdən imtina et{% elif CURRENT_LANGUAGE == 'en' %}Decline invitation{% else %}Отклонить приглашение{% endif %}</button>
</form>
{% endif %}
```

Error409: «Приглашение больше недоступно. Обновите список.» / «The invitation is no longer available. Refresh the list.» / «Dəvət artıq əlçatan deyil. Siyahını yeniləyin.» Success: «Приглашение отклонено.» / «Invitation declined.» / «Dəvətdən imtina edildi.» Тексты controller messages выбираются из небольшого явного RU/AZ/EN mapping по текущему language, error enum отображается в template с `role=alert`. Для неизвестной locale fallback RU соответствует текущему inbox pattern. Никакого raw backend exception и подтверждения успеха до commit.

Контрол повторяет существующую форму accept и native keyboard/focus. Общий restyling account navigation/inbox, добавление новых notification content fields и исправление owner-team clipping относятся к другим причинам; не включать их попутно. Если реальные длинные данные/18cells выявят необходимость CSS для нового control, предъявить точный отдельный scope до CSS patch.

## Task 3: GREEN и целевые native сценарии

- [ ] Повторить новый regression module до GREEN. Один раз запустить affected unchanged consumers: `catalog.testcases.test_task33_notifications` и `catalog.testcases.test_task33_permissions`. Не ослаблять их assertions. Не выдавать no-label/full wrapper за полный corpus; другие модули и полный07 сейчас не повторять.
- [ ] Owner UI→recipient inbox→keyboard/native decline→reload→READ ONLY own DB: REJECTED, responded_at установлен, новых grants0. Оба типа ×RU/AZ/EN×360/390/768/1024/1280/1440. Новые fictional recipient/invite на каждый terminal flow, без ORM подмены проверяемого перехода.
- [ ] Отдельные invites подтвердить native accept для обоих типов; read/unread, decision/outbox/local filebased mail и текущий recipient scope сохранены. Реальный SMTP delivery не заявлять.
- [ ] Две вкладки, owner cancel до decline, real owner change и email change до stale submit; исходная открытая форма не обходит409/404. Для stale-only diagnostic fixture допустим явный QA ORM setup, не для normal decline/accept/owner invitation transitions.
- [ ] Новый control имеет видимый keyboard focus, Enter/Space запускает ровно один корректный POST; кнопка помещается во всех18cells. Native form без JS работает. Long fictional email/display names и stale/error alert не создают horizontal overflow. Подтвердить исходный accepted path и отсутствие ложного success.
- [ ] Network abort только для нового POST помечен SIMULATED. Native browser error не считать application success; back/reload/retry подтверждают фактический статус и отсутствие дублированного event. Новый AJAX/общий JS не вводится ради этой проверки.
- [ ] Console/pageerrors/network/static404, originals PNG mobile/desktop/error и manifest. External requests заблокированы. HTTP200/source/jsdom не заменяют native transitions.
- [ ] Fresh own PG/DB/cache/media/private-media/email, DJANGO_TESTING=1 и sole verified locale path до setup. Старый own recheck stand можно использовать только после проверки PID/argv/cwd/source/isolation; текущие invites уже REJECTED через documented API baseline, их не выдавать за native decline. Предпочтителен новый own fix profile, без старых credentials/ports/session assumptions.
- [ ] Сверить WORKTREE/source/HEAD/branch/active_run и все чужие baseline files/shared MO/container identities. Пропавшие при прерывании прежние processes уже имеют NOT VERIFIED, их не запускать/не восстанавливать автоматически. Зафиксировать фактически доступные чужие стенды на начало fix.
- [ ] Закрыть только ACCESS-QA-02 после полного указанного acceptance. Сохранить причины/changed files/commands/exits/counts/PNG/NOT RUN; обновить одну текущую module07 note. Полный ACCEPT-07 один раз после02/04/05; ACCESS03=ORG02 принят ранее. Module08, commit/push/deploy/production запрещены.

## Риски / stop conditions

1. Canonical helper `_locked_item` private: использовать существующий порядок, не копировать реализацию. Если требуется менять его контракт/сервис/модели, это новый scope и отдельное approval.
2. Existing API reject допускает PENDING без собственного expiry/ownership guard. Этот план защищает **новый notification adapter** и не заявляет исправление всех legacy API. Старые endpoints не меняются.
3. Browser baseline использует fallback fonts при заблокированной внешней загрузке; real CDN/fonts/OAuth/SMTP/production NOT RUN. Это локальное доказательство.
4. В текущем запуске прежние PID/browser потеряны после explicit interruption. Причина потери UNKNOWN; сохранность файлов и Docker проверяется независимо. Нельзя выдавать исчезнувшие processes за preserved PASS.
5. Pending-state race и owner-transfer tests обязательны для закрытия ID, не заменять их source inspection. Если не исполнены, оставить ID OPEN/NOT RUN.

**После одобрения:** реализовать только четыре перечисленных application/test files и QA/docs этого ID. Scope не распространяется на ACCESS04/05 или принятую общую причину ACCESS03.
