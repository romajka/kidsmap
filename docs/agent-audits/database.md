# Database audit — database-reviewer

Дата: 2026-09-06. Execution identity: runtime subagent `/root/audit_database`, первый формальный запуск роли по `.agents/agents/database-reviewer/agent.md`. Scope: исходники, история миграций, классификация legacy и отчёт; без application changes и без серверных действий.

LOCAL HEAD: `df6fef3784a6bae6b7ddce90cd41a392d9f9e6bf`; WORKTREE содержит изменённые `models/place.py`, `services/pricing_plans.py` и untracked `0101_unique_user_email.py`. PRODUCTION: `86a0b8cf64a8835f310a608a3428c60f1fc5341a`, catalog до 0100. Production факты ниже получены **оркестратором**, а не личным подключением этого специалиста: [PRODUCTION_READ_ONLY](PRODUCTION_READ_ONLY.md), E1–E6. Проверен пустой diff production commit → LOCAL HEAD для рассматриваемых models/migrations/pricing service/management commands. Это связывает проверенные исходники с commit, но не заменяет полный hash audit активного образа.

## 1. Состояние области

PostgreSQL 17.10, 23 MB, 50 public tables; 119 применённых миграций. E2: 72 FK, 67 CHECK, 24 UNIQUE, 50 PK; нет unvalidated constraints или invalid indexes. Все 72 проверки declared FK дали ноль orphan rows. Семантические связи, не выраженные FK, этим не проверены.

E3: 321 Place; 78 PricingPlan у 25 мест; **266 мест имеют scalar prices без relational plans**. Непустой legacy JSON у 2 мест. Scalar price range заполнен у 230, monthly у 228, per-lesson у 1, per-eight-lessons у 0; группы могут пересекаться. Структурированные расписания у 300 мест, текстовое у 3, пересечение не исключено. Статусы: 237 draft, 83 published, 1 rejected; published не равнозначен public-visible.

`Place.category` — FK на строковый Category.code (`src/catalog/models/place.py:77`), физическая колонка `category`. `pricing_plans_legacy` — Python-имя, физическая колонка всё ещё `pricing_plans` (`:142`). Это предусмотрено `0084_pricingplan_relational.py:9` через SeparateDatabaseAndState с пустыми database_operations; само присутствие JSON не является schema drift.

Google 0101 и allauth migrations отсутствуют в production (E2). Нормализованный email не имеет unique index; 2 непустые duplicate groups включают 6 пользователей (E3). Приватные идентификаторы и email в этот отчёт не включены.

## 2. Сильные стороны

- Реляционные тарифы имеют проверку суммы, price kind, billing mode, quantity/validity pairs, возраста, дат и charge role: `src/catalog/models/pricing_plan.py:114`, миграции начиная с 0084. `save()` вызывает full_clean (`:232`), SQL constraints дополняют прикладную проверку.
- Индексы pricing lookup/order и unique `(place, weekday)` существуют в исходниках и подтверждены E2. FK coverage heuristic не нашёл кандидатов без индекса; это ограниченная эвристика, не полный performance audit.
- Scalar/JSON fallback сохранён явно: `src/catalog/models/place.py:360`, `src/catalog/services/content_quality.py:196`, `:254`, `:269`, `src/catalog/services/pricing_plans.py:549`. Это защищает совместимость существующих карточек.
- 0101 прекращает применение при duplicate email, не объединяя и не удаляя пользователей (`src/catalog/migrations/0101_unique_user_email.py:11`). Индекс обратим и допускает пустые email.
- Migration 0093 сохраняет неоднозначные null-place team rows без расширения прав; обратная data operation намеренно no-op (`0093_backfill_place_scoped_team_access.py`, `backfill_place_scope`, `Migration.operations`).
- Scalar/schedule importers имеют явный `--apply`, default plan, ambiguous/manual_review и повторный пропуск уже заполненных данных. Эти достоинства не отменяют найденных ниже побочных эффектов и гонок.

## 3. Реальные проблемы

| ID | Среда / приоритет / confidence | Evidence, trigger и impact | Владелец / следующий шаг |
|---|---|---|---|
| DB-01 | PRODUCTION, P1, high | E2: приложение подключается DB role с superuser, createdb, createrole. При компрометации приложения полномочия не ограничены рабочими таблицами. Это подтверждённая граница привилегий, не доказательство эксплуатации. | Security + release + DB: план разделения runtime/migration roles, проверка grants/default privileges и работа приложения в изолированном PG перед отдельным изменением production. |
| DB-02 | PRODUCTION data + LOCAL pending migration, P1 release blocker, high | E2/E3 и `0101_unique_user_email.py:11`: 2 duplicate groups / 6 users гарантированно блокируют preflight 0101. Повторный migrate или fake-apply не решает identity conflict. Текущий сайт этим не объявляется неработающим. | Security + владелец данных + release: manual_review принадлежности адресов и конкретный согласованный план; затем fresh preflight. Не очищать email автоматически. |
| DB-03 | Source at production commit и LOCAL, P1 при запуске `--apply`, high source confidence | `migrate_pricing_plans.py:56` считает существующие строки, но не пропускает их; `:59` вызывает replacement. `pricing_plans.py:328` удаляет тарифы, не вошедшие в legacy-derived payload. Trigger: у места есть современные тарифы и устаревший JSON/scalar payload, не содержащий часть тарифов. Команда может удалить текущие тарифы. `created=max(0, new-existing)` не сообщает объём замен/удалений. E3 подтверждает совместное существование представлений в домене, но точное число уязвимых мест неизвестно. Команда не запускалась; production loss не наблюдалась. | DB + Django: до будущего применения определить authoritative source per place; conflict/manual_review для расхождений, отчёт additions/updates/deletions, fixture с сохранением современных тарифов. |
| DB-04 | Source at production commit и LOCAL, P2, high source confidence | `migrate_legacy_prices.py:1` обещает не менять legacy fields. Однако `:235` вызывает save → post_save `models/pricing_plan.py:245` → `sync_legacy_price_fields` (`pricing_plans.py:345`). Monthly draft (`migrate_legacy_prices.py:32`) получает default one_time, тогда как обратная проекция monthly требует recurring/month (`pricing_plans.py:362`). Поэтому исходный monthly scalar будет очищен; аналогично membership/8 lessons не совпадает с lesson/8 проекцией. Сумма остаётся в тарифе, но сохранность исходных колонок и эквивалентность представлений не обеспечены. | DB + Django: согласовать billing/product meaning, явно описать projection effects, тест полного before/after snapshot. Не менять существующие assertions только ради зелёного результата. |

Для воспроизведения DB-03/04 достаточно одноразовых fixtures без production rows: (1) современный тариф плюс отличающийся JSON, (2) только monthly/8-lessons scalar. Сравнить все тарифы, scalar columns и публичный summary до/после. В данном role run эти destructive fixture checks **не выполнялись**; вывод основан на проверенной цепочке исходников.

## 4. Tech debt

- **DB-05, P2, high:** E3 + `Place.pricing_plans`/public fallback подтверждают частичный переход, а не завершённую миграцию. 266 scalar-only мест требуют поэтапного semantic inventory. Неизвестно, сколько из них реально публично видимы; нельзя выдавать 266 за число сломанных карточек. Owner: DB + Django. Следующий шаг — согласованный план с aggregate classifications и manual_review неоднозначных диапазонов.
- Две команды переноса цен кодируют monthly/8-lessons по-разному (`migrate_legacy_prices.py:23`, `migrate_pricing_plans.py:32`). Сначала согласовать контракт с backend, затем решать судьбу команд. Это не разрешение выбрать и удалить одну из них.
- История cutover в `docs/postgresql_cutover.md` полезна для transfer/rollback, но старое имя ветки не описывает текущий deployment (E1). Схема уже PostgreSQL; повторный cutover не требуется по одному runbook.
- 0101 управляет индексом stock User только на database level. Поэтому стандартный model-state drift check сам по себе не подтверждает физическое присутствие этого индекса: нужна catalog introspection после согласованного release.

## 5. Risks

- **DB-06, P2, medium-high source confidence:** concurrent migration/editor path не полностью сериализован. `migrate_legacy_prices.py:225` использует atomic + exists без блокировки Place; при двух writers оба могут увидеть отсутствие тарифов. `replace_place_pricing_plans` блокирует существующие PricingPlan (`pricing_plans.py:298`), но пустой набор не блокирует родительскую Place. Нужен PostgreSQL test с двумя соединениями; частота/реальный инцидент не установлены. Owner: DB + Django.
- Schedule importer планирует на prefetched `schedule_days__intervals` (`migrate_legacy_schedules.py:56`), затем `_apply` повторно сериализует тот же объект без refresh/parent lock; serializer читает related `.all()` (`place_schedule.py:397`), а sync удаляет текущие дни (`:418`). Это source risk пропустить изменение редактора и перезаписать расписание. Не воспроизведено на PG; включить в DB-06 concurrency rehearsal.
- Ownership moderation блокирует заявку (`models/owner.py:100`), но разные заявки на одно место не блокируют одну и ту же request row. Нужно отдельно проверить согласованный порядок передачи владельца, stale Place object и аудит (`:116`). Передано Django/security как test gap; нарушение прав в production не заявляется.
- Миграционный SQL и API-разрешения защищают разные уровни. Ноль FK orphans не доказывает правильность product type, времени, ownership, email ownership или координат. E3: ноль Place/Subcategory mismatch — полезная отдельная проверка, не универсальная гарантия качества данных.
- E2: non-executing EXPLAIN выбрал seq scan + sort на таблице из **321 rows**. Это не достаточное основание добавлять индекс. Нужны реальный query shape, распределение фильтров, размер, workload и изолированное измерение; EXPLAIN ANALYZE в production не выполнялся.
- Recovery: E5 подтверждает gzip/header/completion у 4 регулярных backups, но не restore текущего backup schedule. Исторические 186 tests относятся к предыдущей задаче и отдельному restored dump. Owner: release; текущий аудит не создаёт backups/restore DB.

## 6. Dead / legacy candidates без удаления

| Объект | Статус | Код + migration + DB + поведение | Решение |
|---|---|---|---|
| JSON `pricing_plans` | LEGACY-IN-USE; схема MIGRATED-BUT-RETAINED | `place.py:142/:360`; 0084 state-only rename; E3 nonempty 2; property возвращает JSON при отсутствии relational rows, публичный price path его читает | Удаление запрещено до per-place equivalent migration и public/admin regression. Непустой JSON не доказывает, что он авторитетнее relational rows. |
| Scalar `price_*` | LEGACY-IN-USE + ACTIVE projection | `place.py:156`; 0084 сохраняет Decimal fields; E3 scalar-only 266; SQL visibility/filter и summary читают, pricing signals пишут | Не cleanup candidate сейчас; сначала разделить legacy input и projection. |
| `Place.schedule` | LEGACY-IN-USE | `place.py:128`, `content_quality.py:254`, importer сохраняет текст; E3 3 непустых текста / 300 structured places | Проверить overlap и эквивалентность parsed hours, не удалять fallback. |
| `Place.category` / строковые location поля | ACTIVE | category FK на code; миграции и E2 schema; E3 mismatch 0; public filters принимают текущую семантику | Не преобразовывать в integer/другой location model по названию поля. District/metro semantic validation остаётся UNKNOWN. |
| Null-place team compatibility | MIGRATED-BUT-RETAINED | 0092/0093; null не даёт scope; E3 memberships/invitations 0/0; ACL paths сохранены | Ноль строк не доказывает dead API. Рассмотреть только после анализа writers/URL/backward compatibility. |
| Event / temporary Place / Specialist | ACTIVE paths, retirement UNKNOWN | модели, отдельные domain paths; E3 Event 0, temporary Place 0, Specialist 0; схемы и формы существуют | Не удалять таблицы/код по пустоте данных. |
| UserProfile legacy role fields | Удалены; migration history ACTIVE | 0097 уже применена по E2, текущая модель не содержит global role | Не восстанавливать по старым docs; не удалять исторические migrations. |
| Дублирующиеся price importers | CANDIDATE-FOR-REMOVAL только после consolidation | DB-03/04, разные product mappings, поддерживающие tests, production usage команд UNKNOWN | План unified migration contract и equivalence tests; сейчас сохранить обе. |
| `cleanup_migration_junk` и cutover scripts | ACTIVE operational tools, usage UNKNOWN | `cleanup_migration_junk.py:21/:47` guard + deletes; `migrate_legacy_database.py:155` prune и `:168` report write | Не запускать по названию audit/dry-run. Наличие инструмента не означает наличие данных, допустимых к удалению. |

## 7. Tests gaps и выполненные проверки

**Выполнено этим специалистом:** чтение AGENTS/registry/реальной роли/knowledge/audit contract; `git rev-parse HEAD`; scoped `git status --short`; `git diff 86a0b8cf64a8835f310a608a3428c60f1fc5341a HEAD -- src/catalog/models src/catalog/migrations src/catalog/services/pricing_plans.py src/catalog/management/commands` (пустой); `git diff --unified=2 -- src/catalog/models/place.py src/catalog/services/pricing_plans.py`; `rg -n` и чтение перечисленных исходников/тестов. Первые догадки о названиях 0084/test_migrate_legacy* дали file-not-found; правильные `0084_pricingplan_relational.py` и `testcases/legacy_migrations.py` найдены через `rg --files` и прочитаны. Это ошибки поиска, не test failures.

**Получено от оркестратора:** E2 read-only PG catalog/FK/index/migration evidence; E3 exact aggregates; E5 ограниченная backup evidence. Сам специалист DB connection не открывал и SQL не выполнял.

**Не выполнялось:** Django tests, migrations, management commands, concurrent PostgreSQL fixtures, forward/backward schema rehearsal, restore, browser QA, EXPLAIN ANALYZE. Причина — этот role run ограничен source/evidence audit; PG/backup writes на production запрещены. Никаких новых утверждений «tests pass».

Существующие тесты прочитаны: `testcases/legacy_migrations.py:21/:31/:105` проверяют default dry-run, mapping и последовательный повтор; `pricing_plans_relational.py:129` проверяет последовательную idempotency; `:31` — projections. Они не доказывают parallel safety и не проверяют сохранение всех monthly/8-lessons scalars после scalar migration. Google tests моделируют conflict paths; они не заменяют два настоящих PG connections.

Следующие проверки — только по отдельному согласованному plan, `DJANGO_TESTING=1`, disposable DB/cache/media, без production credentials:

1. DB-03: mixed legacy/modern тарифы, разные IDs/verified fields, полный diff additions/updates/deletions и повторный run.
2. DB-04: monthly/8-lessons/free/range/all-currency round trip; сохранность исходного payload и эквивалентность public/admin summary.
3. DB-06: две транзакции первого тарифа, replace против editor, schedule migration против editor; итоговое число/содержимое rows, rollback и сигналы.
4. 0101: duplicate preflight без changes, case/whitespace normalization на PG, параллельный signup/profile/Google, index forward/reverse и compatibility старого приложения.
5. Interrupted transfer/import: checkpoint/rerun после частичного table/place commit, sequence correctness, nullable relationships, deterministic report, recovery без обнуления legacy.
6. Регулярный backup restore отдельно от gzip verification, затем constraints/counts и business flows. Ни upstream historical result, ни SQLite не заменяют этот PG rehearsal.

## 8. Recommendations

Сначала сохранить аудитный режим и объединить DB-01/02 с security/release findings. Не запускать price migration для «завершения перехода» по числу 266: требуется classification и согласованный meaning, затем конкретный reviewable plan. Для DB-03/04/06 подготовить изолированные repro fixtures, сравнить все четыре измерения: code, schema/data, migration history, public/admin behavior.

Будущий destructive процесс: AUDIT → PLAN → DRY RUN → BACKUP → USER APPROVAL → APPLY → VERIFY. План должен определить authoritative representation, manual_review, точные границы Place batches, совместную блокировку writers, before/after aggregates, rollback/checkpoint и критерий остановки. Dry-run проверяется на side effects; отчёты с user-level rows и приватными значениями не попадают в repository.

Индексы добавлять только после измерения нужного query; historical migrations и живые JSON/scalar fallbacks сохранять. Решение о реализации остаётся у пользователя после MASTER_AUDIT.

## 9. P0 / P1 / P2 / P3

| Приоритет | Findings / решение |
|---|---|
| P0 | Не подтверждён: нет доказанной текущей DB аварии, потери данных или эксплуатации. |
| P1 | DB-01 superuser runtime role; DB-02 identity preflight blocker для будущего Google release; DB-03 риск удаления современных тарифов при конкретном migration apply. Согласовать планы, не выполнять fixes в аудитном запуске. |
| P2 | DB-04 scalar preservation/product mismatch; DB-05 частичная миграция; DB-06 concurrent writer risks, требующие PG reproduction. Recovery rehearsal — handoff release. |
| P3 | Уточнение cutover/runbook статуса, единая документация двух importers, пояснение database-only index verification. |

Артефакт содержит рекомендации, а не разрешение на изменения приложения/production. Приватные строки, env values, dumps и production logs не копировались.
