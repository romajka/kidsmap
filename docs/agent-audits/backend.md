# Django backend audit — 2026-09-06

Роль: `django-reviewer`. Исполнитель: отдельный runtime subagent `/root/audit_backend`, первый формальный запуск по `.agents/agents/django-reviewer/agent.md`. Режим AUDIT ONLY; собственных подключений к серверу, application edits и запусков management commands не было. Записан только этот отчёт. Применены `systematic-debugging` и `verification-before-completion`.

## 1. Состояние области

- LOCAL HEAD: `df6fef3784a6bae6b7ddce90cd41a392d9f9e6bf`; прочитан dirty WORKTREE, включая untracked `permanent_place_rules.py`. Он не равен HEAD и не является deployed release.
- PRODUCTION: `86a0b8cf64a8835f310a608a3428c60f1fc5341a`, catalog0100, PostgreSQL17.10. Эти факты и агрегаты ниже получены **оркестратором**, источник [PRODUCTION_READ_ONLY.md](PRODUCTION_READ_ONLY.md), E1–E6. Я не проводил live-проверку.
- Проверены models/forms, readiness/public visibility, owner create/edit/submit, admin publication, permissions, ownership moderation, schedule validation/sync, pricing replacement и migration entry points. Auth identity, media endpoints, инфраструктура передаются владельцам соответствующих ролей; это не полный security audit.
- Система использует отдельные контракты: готовность к новой публикации, совместимость уже опубликованных карточек, public SQL visibility, verified badge. Их различие само по себе не дефект.
- Байтовое сравнение с нормализацией CRLF: WORKTREE `place_schedule.py`, `models/owner.py`, `migrate_pricing_plans.py`, `place_readiness.py` совпадают с файлами **git revision** production. Это не самостоятельная аттестация работающего image. `pricing_plans.py` изменён локально; `git diff` показывает изменение WhatsApp presentation, без изменения рассматриваемого replacement.
- Отдельное AST-сравнение `replace_place_pricing_plans` с `git show 86a0b8c:src/catalog/services/pricing_plans.py` подтвердило идентичность функции. Пять scoped Python файлов успешно разобраны AST; проверено наличие всех девяти разделов отчёта.

## 2. Сильные стороны

- `services/place_readiness.py:35` (`PlaceReadinessData`) отделяет правила от сохранения; `:568/:680` строят единый результат для модели и формы. Admin использует его в `domain_admin/place.py:268`; owner create дополнительно проверяет несохранённые данные в `controllers/owner_places_controller.py:461`.
- `domain_admin/place.py:273` ограничивает compatibility уже опубликованной активной карточкой. Public `services/content_quality.py:236` намеренно сохраняет текстовые часы и scalar prices. Production E3: 266 карточек со scalar prices без relational plans — реальная причина сохранять совместимость.
- `services/place_access.py:54/:70/:78` не оставляет creator постоянных полномочий после передачи owner и не включает публикацию в direct manager role. Pure-function проверка подтвердила оба свойства. `owner_place_use_cases.py:61` явно исключает legacy null-place membership из выдачи доступа.
- Owner create/edit/submit обёрнуты в транзакции; локальное редактирование при неудачной отправке вызывает rollback (`owner_places_controller.py:762`). Старые фото удаляются после commit (`:680/:685`), а не до успешной транзакции. Это source evidence, не проверка всех отказов файлового хранилища.
- `PlaceOwnershipRequest.apply_moderation` блокирует конкретную заявку и отклоняет повторное применение (`models/owner.py:95–105`). DB constraints и отсутствие declared-FK orphan подтверждены E2, а не выведены из одного model source.
- `validate_schedule_payload` проверяет порядок времени, пересечения и переход через полночь (`place_schedule.py:300`); слабая часть находится перед этими семантическими проверками — см. BE-02/03.

## 3. Реальные проблемы

### BE-01 — локальный owner gate расходится с canonical readiness

- **Среда/приоритет:** LOCAL WORKTREE, P2; высокая уверенность. Не утверждается наличие нового wizard в production.
- **Источник:** `services/permanent_place_rules.py:15/:28/:35/:42`, вызов `forms.py:1469`; canonical `_check_description` / `_check_price` / `_check_schedule` в `place_readiness.py:164/:252/:276`; вторичная проверка create `owner_places_controller.py:461`, отдельный submit `:877`.
- **Trigger/эффект:** короткое содержательное описание либо existing карточка с free/free-entry/events price mode без тарифов отвергаются owner gate, хотя readiness их допускает. Owner form не предоставляет `price_mode`; существующий режим остаётся свойством instance, а новый helper его не учитывает. Обратное расхождение: helper принимает текстовое regular schedule и legacy scalar price, но последующий canonical gate может их отвергнуть. Это не обход публикации: downstream readiness остаётся, зато правила и ошибки между действиями непоследовательны.
- **Проверено:** прямой запуск реальных функций на синтетическом полностью заполненном `PlaceReadinessData`: `readiness_ready=true`; owner errors для short/free — `description_az, pricing_plans`; при длинном описании — только `pricing_plans`. БД, HTTP и browser не использовались. Приём текстового schedule/legacy helper и downstream отказ прослежены по source, но не прогнаны end-to-end.
- **Владелец/handoff:** Django + frontend-reviewer + integration-reviewer. Следующий шаг — согласовать единый контракт и parity matrix для create/edit/submit/admin, отдельно сохранить deliberate legacy compatibility; исправления сейчас не разрешены.

### BE-02 — повреждённый schedule JSON признаётся корректным пустым расписанием

- **Среда/приоритет:** LOCAL + production git revision, P2; высокая уверенность в parser/sync поведении, запись реальных данных не выполнялась.
- **Источник:** `services/place_schedule.py:202–222` (`parse_schedule_payload`), `:300`, `:415–420` (`sync_place_schedule`); `forms.py:150/:175` (`_clean_schedule_editor`, `save_schedule`); owner edit `owner_places_controller.py:681`.
- **Trigger/эффект:** непустой malformed payload, например `{broken`, преобразуется в семь закрытых дней с `errors={}`. `sync_place_schedule` сначала удаляет существующие строки, затем возвращается для нем meaningful schedule. На разрешённом сохранении draft/ordinary edit это может очистить прежние часы вместо ошибки. Publish gate может остановить некоторые варианты, но не заменяет проверку синтаксиса при сохранении черновика.
- **Проверено:** настоящие parser/validator вернули `valid=true, days=7, closed=7`; вызов настоящего sync с mock relation вызвал `delete` один раз и не создавал дни. Это доказательство ветки кода, **не** выполненное удаление в БД и **не** сообщение о потере production данных. HTTP-form save целиком не запускался.
- **Владелец/handoff:** Django + integration-reviewer, database-reviewer для сохранности rows. Следующий шаг — различить omitted/explicit clear/malformed и проверить сохранение прежнего расписания при отказе.

### BE-03 — JSON shape может вызвать исключение до form errors

- **Среда/приоритет:** LOCAL + production git revision, P2; высокая уверенность в service exception, полное HTTP воспроизведение не выполнено.
- **Источник:** `place_schedule.py:205/:216/:303/:328`; `forms.py:125–144` строит editor days непосредственно из parsed payload до semantic validation.
- **Trigger/эффект:** `{"days":1}` вызывает `TypeError`; список с открытым днём и `intervals:1` также вызывает `TypeError` в validator. `_init_schedule_editor` дополнительно индексирует ожидаемые ключи без нормализации: произвольная структура hidden-field JSON может дать 500 вместо понятной ошибки. Маршруты форм требуют своего доступа; эта проверка не устанавливает anonymous exploit.
- **Проверено:** оба указанных вызова настоящего `validate_schedule_payload` дали `TypeError`. Ошибка формы init прослежена по исходнику; response status не измерялся.
- **Владелец/handoff:** Django + security-reviewer + integration-reviewer. Следующий шаг — schema validation до rendering/iteration и отрицательные cases для dict/list/item/interval types.

### BE-04 — migration command может заменить уже существующие тарифы legacy-проекцией

- **Среда/приоритет:** LOCAL HEAD/WORKTREE + production git revision, **P1 при запуске `migrate_pricing_plans --apply`**. Это опасный административный путь, не текущая авария. Высокая уверенность по source, runtime migration не запускалась.
- **Источник:** `management/commands/migrate_pricing_plans.py:22–59` обходит все Place, собирает payload из legacy JSON и трёх scalar products, считает `existing`, но не пропускает уже мигрированные карточки. Вызванный `services/pricing_plans.py:295/:328–331` удаляет планы, отсутствующие в `keep`.
- **Trigger/эффект:** у карточки уже есть современные relational тарифы, а scalar fields содержат их ограниченную проекцию. Повторный `--apply` восстанавливает только представимые legacy продукты и может удалить остальные тарифы/атрибуты. Например membership projection не представляет все дополнительные/неосновные/camp plans. `existing` используется для счётчика, не для защиты. `--dry-run` сообщает created count, но не отдельный план удалений/изменений, поэтому малый created count не доказывает безвредность.
- **Production relevance:** E3 сообщает 78 планов у 25 Place, но состав конкретных карточек не исследован и запуск команды в production не доказан. Ни один тариф не изменялся в этом аудите.
- **Владелец/handoff:** database-reviewer + Django + release-reviewer; orchestrator уведомлён сразу. Следующий шаг — изолированный repeated-run/round-trip сценарий и конкретный план merge/skip/conflict policy, с явным отчётом updates/deletes до разрешения apply.

## 4. Tech debt

- **BE-05, LOCAL, P3:** `forms.py:72/:76` и `:353/:362` повторно определяют `MultipleFileInput/MultipleFileField`; позднее определение затеняет раннее. Кандидат на консолидацию после проверки использования/наследников, не доказательство безопасного удаления. Owner: Django; воспроизводимость — source/поиск имён, runtime inheritance не проверен; confidence high для затенения, removal safety unknown.
- Forms/controllers/admin одновременно содержат ORM и business rules. Это фактическая смешанная архитектура, а не достаточное основание для массовой замены на repositories. Первым полезен BE-01, а не полная перепись слоёв.
- Комментарий `permanent_place_rules.py:1` о shared admin/public requirements неверен по call graph: admin продолжает использовать `place_readiness`. Комментарий не является контрактом.

## 5. Risks

- **BE-R1, LOCAL + production git revision, P2 investigation:** `models/owner.py:100` блокирует заявку, но не сам Place до проверки/смены owner (`:115–124`). Две разные pending заявки на одно место могут обе стать approved; окончательный owner зависит от порядка обновлений. Это source interleaving, не воспроизведённая PostgreSQL гонка и не автоматически доказанный дефект политики: последовательная передача владения тоже может быть намеренной. Нужны определение expected-owner policy и isolated two-connection test. Owners: Django/database/security; confidence medium; production conflict count неизвестен.
- `replace_place_pricing_plans` блокирует существующие child rows, но пустой набор не блокирует родителя (`pricing_plans.py:298`). Между несколькими edit paths нужна отдельная проверка concurrent replacement и родительских блокировок; не утверждается потеря тарифов только по этому паттерну.
- Google OAuth, catalog0101 и новый photo/phone wizard находятся в dirty/untracked срезе. E1/E2 подтверждают отсутствие активации Google/allauth на проде; E3 — две группы duplicate normalized email. Это release prerequisite/security handoff, а не разрешение автоматического исправления пользовательских email.
- Контракт `published_place_queryset` мягче `public_place_queryset`; подмена одного другим без карты потребителей может сломать совместимость и SEO. Не считать наличие legacy карточек доказанной уязвимостью.

## 6. Dead/legacy candidates

| Объект | Статус | Доказательство и действие |
|---|---|---|
| Scalar `price_*` | LEGACY-IN-USE / current projection | `pricing_plans.py:345`, public filter; E3:266 scalar-only Place. Не удалять. |
| Legacy JSON pricing | LEGACY-IN-USE | `Place.pricing_plans` property `models/place.py:360`; E3:2 nonempty JSON. Не считать уже мигрированным целиком. |
| Text schedule | LEGACY-IN-USE | `content_quality.py:250`, `place_schedule.py:514`; E3:3 text schedules. Переход только с проверкой часов. |
| Root config/admin facades, owner aliases | ACTIVE compatibility | Корневой config переэкспортирует src; admin autodiscovery; `owner_place_use_cases.py:22/:85`. Не удалять по имени. |
| Null-place team membership | MIGRATED-BUT-RETAINED | `owner_place_use_cases.py:61` не выдаёт прав; production0 memberships не доказывает бесполезность compatibility кода. |
| Первые MultipleFile classes | CANDIDATE-FOR-REMOVAL | BE-05; отдельно проверить references и tests, сейчас оставить. |
| Отдельные Event и temporary Place | ACTIVE, retirement UNKNOWN | Существуют два контракта; production0/0 не является доказательством dead code. |

## 7. Tests gaps и выполненные проверки

**Executed:** чтение роли/knowledge/contract, `git status --short`, `git rev-parse HEAD`, `git diff --stat -- src/catalog`, scoped `git diff`, `rg` references; сравнение source с `git show 86a0b8c:<path>`. Два inline Python запуска завершились exit0 и дали результаты BE-01/02/03 и permission checks. Это focused probes, не полный Django test suite. Никаких assertions существующих tests не менялось.

Оба запуска выполнялись командой PowerShell `@'<Python source>'@ | .venv/Scripts/python.exe -` с настоящими переводами строк. Общий exact isolation bootstrap:

```python
import os, sys, json
from pathlib import Path
os.environ['DJANGO_TESTING'] = '1'
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path('src').resolve()))
from django.conf import settings
settings.configure(
    USE_I18N=False, LANGUAGE_CODE='en', INSTALLED_APPS=[],
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
    CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}},
    MEDIA_ROOT=str(Path('.tmp/audit-backend-unused-media').resolve()),
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
)
```

После bootstrap первый probe вызывал `validate_schedule_payload` для `{broken`, `{"days": 1}`, `[{"weekday":"mon","is_closed":false,"intervals":1}]`; результат malformed передан настоящему `sync_place_schedule` с `Mock` place и `catalog.models` stub для `PlaceScheduleDay/PlaceScheduleInterval`. Второй вызывал настоящие `publication_errors/evaluate_readiness` на синтетическом заполненном free/always_open объекте (короткое и длинное описание), затем `is_direct_place_manager/direct_place_permissions` для бывшего creator и текущего owner. Настройки проекта/.env не загружались; DB connection, files/media writes, mail/network не вызывались. Translation была отключена; ORM sync был явно mocked, не тестом SQL.

**Not run:** полный backend/auth/owner/admin/pricing suite; HTTP malformed-save; real PostgreSQL concurrency; browser; real OAuth; миграции/management commands; production reads/writes самим исполнителем. Исторические 186 release tests из E5 не объявляются проверкой текущего dirty tree.

**Пробелы для следующего согласованного запуска:** parity owner/admin/standalone submit для short description/free modes/legacy; malformed schedule сохраняет прежние rows; shape errors не дают 500; migration repeated-run сохраняет все современные тарифы и сообщает удаления; две разные ownership заявки и одновременные empty-plan writes. Уже есть tests в `testcases/place_readiness.py`, `legacy_migrations.py`, `pricing_plans_relational.py`, `owner.py`; это не означает, что эти конкретные отрицательные сценарии покрыты или сейчас проходят.

## 8. Recommendations

1. Перед любым использованием legacy migration команд подготовить изолированный regression/round-trip plan BE-04; не запускать apply на основании только created count.
2. Согласовать backend контракт BE-01 и сохранить public/live legacy compatibility отдельной явной политикой. Дальнейшие UI/JS правила должны опираться на тот же verdict.
3. Запланировать parser schema validation и отсутствие записи при ошибке BE-02/03; проверить как owner, так и admin/draft сохранения.
4. Зафиксировать бизнес-решение по competing ownership approvals, затем PostgreSQL concurrency tests. Не выдавать автоматически новым пользователям глобальную роль.
5. После master cross-review и одобрения конкретного scope выполнить исправления отдельно. Этот отчёт останавливается на рекомендациях; deployment Google остаётся приостановленным.

## 9. P0 / P1 / P2 / P3

| Приоритет | ID | Решение |
|---|---|---|
| P0 | — | Подтверждённой аварии/компрометации данным backend аудитом не найдено; это не гарантия отсутствия. |
| P1 | BE-04 | Потенциальная потеря relational pricing при конкретном административном `--apply`; source-confirmed, не запускался. |
| P2 | BE-01 | LOCAL owner/readiness integration mismatch. |
| P2 | BE-02, BE-03 | Schedule malformed handling: очистка/исключение на проверенных service ветках; HTTP/DB end-to-end pending. |
| P2 investigation | BE-R1 | Определить ownership concurrency policy и воспроизвести на isolated PostgreSQL. |
| P3 | BE-05 | Консолидация затенённых definitions только после отдельного плана. |

Handoffs: database-reviewer — BE-04/BE-R1/legacy transition; security-reviewer — BE-03/object access race; frontend-reviewer — BE-01; integration-reviewer — negative/parity/round-trip tests; release-reviewer — отсутствие разрешения apply и независимость production snapshot. Финальное решение принадлежит orchestrator/пользователю, не этому отчёту.
