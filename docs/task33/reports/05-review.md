# Этап05 — независимая проверка схемы

**PASS bounded schema review. Подтверждённых оставшихся blockers в этом scope не найдено.**

2026-09-29, отдельный runtime `/root/stage05_review`, canonical `.agents/agents/django-reviewer/agent.md`. Режим независимого AUDIT: source/diff и собственные isolated PostgreSQL проверки; изменены только назначенные `05-review.md` и `05-review-evidence.json`. Application fixes выполнял lead. Авторизация: прямое поручение этап05, отдельное принятие owner-02-r1/admin-public-03-r1 «Принимаю оба набора». Прочитаны actual AGENTS/registry/engineering/audit contracts, prerequisites01/04 и актуальные entity/data контракты.

LOCAL HEAD `c52b871ce5c18656a9eaf9854e66255c2629364e`, dirty WORKTREE additive schema. HEAD не является версией новых моделей. Проверены actual модели, services, Place diff, registration и migration0117. SHA шести изменённых source artifacts зафиксированы в [evidence](05-review-evidence.json); до/после окончательного собственного запуска они совпали. Все116 прежних numbered catalog migrations и PricingPlan byte-identical к HEAD. Codebase Memory callable, project/root проверены, architecture вызван, старые PricingPlan symbols найдены; inventory исключений truncated, свежесть/coverage новых файлов UNKNOWN. Критические выводы проверены непосредственно в source, graph отсутствие не использовалось как доказательство.

## Что проверено

- `models/catalog_structure.py`: Organization/Program/Activity/OfferingGroup и отдельный confirmed Location; отдельные заявки Org/venue, nullable legacy связи. Новые иерархические FK PROTECT, instance/queryset hard-delete запрещены, archive идемпотентен, не изменяет Place/reviews. Пользовательские evidence links SET_NULL сохраняют строки при удалении аккаунта.
- `Place.Meta`: positive versions, явные NULL/known-enum approval pairs, venue confirmation pair; прежняя publication/is_active независимы, backfill inactive→closed отсутствует.
- `services/catalog_structure.py`: atomic locks Organization→Place→Program→Activity в PK order; initial anchors перечитываются после locks; mismatch/reparent/archive/stale version отвергаются. Внутренние helpers требуют авторизующего caller; публичных endpoints здесь нет. Bulk/raw SQL не является разрешённым structural API.
- `preserve_place_structure`: на существующем Place lock сохраняет актуальные новые readonly поля при старом full save; запрещает explicit partial writes/new nondefault structural creation. Прежние поля, scalar/JSON pricing, media и URL не заменяются.
- Migration0117 зависит от actual leaf0116, содержит только CreateModel/AddField/AddConstraint; прежние миграции/IDs/данные не переписываются. Старые nullable связи допускают standalone Place. Group tariffs и их XOR/signals остаются этапу10.

## Собственные выполненные проверки

Из `/home/ramin/kidsmap`:

```bash
python3 docs/task33/qa04/run.py --mode all --label catalog.testcases.test_task33_catalog_schema --output /tmp/task33-05-independent-first
python3 docs/task33/qa04/run.py --mode all --label catalog.testcases.test_task33_catalog_schema --output /tmp/task33-05-independent-final2
python3 /tmp/task33-05-review-extra-launch.py --mode probe --output /tmp/task33-05-independent-extra-first
python3 docs/task33/qa04/run.py --mode all --label catalog.testcases.test_task33_catalog_schema --output /tmp/task33-05-independent-final3
```

Первый запуск27 tests/0F2E/exit2: две новые synthetic Event fixtures не задали обязательную category; это fixture error, не старый baseline и не schema migration PASS. Lead исправил fixtures. Следующий28/0F0E/exit0 PASS. Отдельный reviewer scratch wrapper использовал неизменённый clean QA04 launcher и собственный disposable container: partial-save negative отвергнут, сохранённая Place/Program пара остаётся согласованной, exit0.

**Окончательный собственный запуск:31 tests,0 failures,0 errors,0 skipped,11.109s,exit0.** Включает DB FK/negative ages/version/approval/request checks, archive/retention, legacy readonly-save, independent venue/Event address, pending links without rights, stale structural rollback, три PostgreSQL concurrency cases и forward migration на заполненной legacy DB с сохранением каждого прежнего concrete field восьми synthetic rows семи record types и HTTP200 прежних AZ/RU/EN URL. Forward тест откатывает expansion только до создания новых business records внутри своей disposable DB; это не production recovery после новых writes.

Перед suite fresh пустая PostgreSQL также получила все миграции: check и makemigrations --check --dry-run exit0, applied151/unapplied0, catalog leaf0117. PostgreSQL17.10/Django6.0.2/Python3.12.3/psycopg3.2.10, DJANGO_TESTING=1, clean env, один owned Unix socket DB alias, network none/tmpfs/no ports, LocMem cache/email, private media, внешние credentials отсутствуют. Все собственные контейнеры/scratch удалены, cleanup PASS. Raw logs/env/SQL/row payloads в отчёты не копировались.

## Finding и границы

05-REVIEW-01: source review обнаружил обход cross-table invariant через Activity.save(update_fields=['program']) после изменения и Place, и Program: валидация проверяла proposed pair, partial save мог сохранять другую. Lead добавил RED regression, `_check_partial_relationships` теперь отвергает изменённый structural parent, исключённый из update_fields, под locks. Собственный synthetic negative и окончательная suite PASS. Finding закрыт.

Lead отдельно выявил stale legacy Place overwrite и исправил readonly preservation; reviewer проверил финальный source и лично исполнил regression test. Self-check lead не выдаётся за reviewer discovery.

Full application baseline reviewer **NOT_RUN**: на момент handoff lead сообщил, что1262 tests (1231old+31new) выполняются в `/tmp/task33-05-full-final`; итог/классификация и сравнение с04 принадлежат lead и reports/05.md. Rendered browser, реальные external integrations, production,06–28 и postwrite rollback NOT_RUN. UI/ACL/public readers этим этапом не переключаются. Версионность approved candidates, полный join/detach/permissions, target-scoped grouped pricing — следующий согласованный scope, не реализованная здесь возможность. ORM bulk/raw structural writes обходят сервис и запрещены caller contract; DB проверяет локальные инварианты, не межтабличное organization matching.

Handoff: primary database-reviewer сверяет своё окончательное baseline и журнал. Следующий django-reviewer в этапе06 должен использовать текущий locked integrity service и добавить authorized relationship/ownership transitions без обхода hooks. Этот review не разрешает запуск06 или production.
