# Этап 11 — независимая проверка

Исполнитель: `/root/stage11_review`, canonical `integration-reviewer` (`.agents/agents/integration-reviewer/agent.md`). Дата: 2026-09-30. Режим: READ-ONLY AUDIT, только этап 11; application code не менял. LOCAL HEAD `c52b871ce5c18656a9eaf9854e66255c2629364e`, dirty WORKTREE этапов 05–11; этот HEAD не содержит проверяемый код. Production UNKNOWN, подключения не было. Dependency 10 DONE, active_run принадлежал lead `/root` для этапа 11.

## Вывод

Подтверждённых P0/P1 после исправления нет. Я нашёл P1 в промежуточном коде: `DJANGO_TESTING=1` не изолировал `DATABASE_URL`. Lead добавил fail-closed проверку в `catalog_conversion._require_isolated_database`, вызываемую перед `build_plan` и `apply_plan`; негативный тест проверяет отказ обеих операций при заданном `DATABASE_URL`. Финальный снимок повторно проверен.

`build_plan` строит план в PostgreSQL READ ONLY транзакции без model saves; dry-run сравнивает счётчики/статистику таблиц до и после. `apply_plan` валидирует digest/identity target, блокирует run/source rows, сверяет fingerprint и пишет mapping с checkpoint в одной `transaction.atomic`. Принудительный сбой на второй записи откатывает обе записи и checkpoint; повторная попытка завершается. Уникальный ключ mapping закреплён DB constraint. Старый план изменённого Place уходит в `changed_source` manual review, новая правка остаётся. Legacy price и неподтверждённые organization/group остаются на совместимом пути без угадывания. Проверены PK/slug/media/favorite/review/reaction на fixture.

Границы: это консервативный pilot mapping, не перенос всех доменов из общей карты. Aggregate reconciliation сравнивает counts, а не доказывает поштучную идентичность всех production объектов. Production данные, полный сайт, browser и внешние интеграции не проверялись.

## Проверки и evidence

- `python3 docs/task33/qa04/run.py --mode all --label catalog.testcases.test_task33_conversion --output /tmp/task33-11-independent-review-guard-final-20260930`: exit 0, 12/12 PASS, 0 failure/error/skip, 1.249 s. QA04: disposable PostgreSQL 17, tmpfs, network none, no mounted checkout, isolated cache/media/email, cleanup PASS. Evidence: `/tmp/task33-11-independent-review-guard-final-20260930/{run.json,suite-results.json}`.
- `git diff --check`: exit 0. Codebase Memory project `home-ramin-kidsmap` ready; checked five stage 11 source/test paths, metadata matched with no recorded coverage issue. Actual source inspected; graph coverage alone was not treated as proof.
- Source SHA256: `models/conversion.py` `c3dfee389bdd53c27379a3060da6804e7e38c9ee7cd33be4f1546095d0f30f99`; migration `0124_task33_conversion.py` `b37a029cd1e859f8e6cae0918b7d91f53e45dc9320715dd8b38f61a0595f2bcb`; `services/catalog_conversion.py` `62c4ba5da583690352c7c06dd57353924d6781c99123d2400e7904ba401157ab`; command `convert_task33_catalog.py` `d461f485a899fdbb20eff7ff4480827317e0f0102841b1bccad708180db00313`; `test_task33_conversion.py` `10051c5cb5a89c638b26c313e6dcc852573b104a43fdba261624b19d4dadcc18`.

Full suite and its baseline classification belong to lead report `11.md`; I did not run them independently. Production DB/migrations, deploy, commit/push, UI/browser and external integrations NOT RUN.

Handoff: `database-reviewer`/lead `/root` should reconcile final source hashes and full-suite result in `11.md`, then close active_run if stage criteria are met. Stage 12 requires a separate user request.
