# Этап 04 — независимый bounded review

Исполнитель `/root/stage04_review`, canonical `.agents/agents/database-reviewer/agent.md`; 2026-09-29. Режим LOCAL QA FOUNDATION, авторизация выбранного этапа 04; ownership только этот отчёт/evidence. LOCAL HEAD `c52b871ce5c18656a9eaf9854e66255c2629364e`; tracked source clean, docs/task33 untracked. Production UNKNOWN, не подключался. Применён verification-before-completion.

**PASS в ограниченном scope:** собственный новый disposable PostgreSQL runner действительно запущен для isolation/discovery и повторно для migration-state/synthetic-query probe. Это не PASS application suites или продуктовая приёмка и не готовность production.

## Evidence и выполненные проверки

- `python3 docs/task33/qa04/run.py --mode discovery --output /tmp/task33-04-independent-discovery` — exit 0. PostgreSQL 17.10, Django 6.0.2, Python 3.12.3, psycopg 3.2.10. Новый ownership-checked контейнер: network none, нет published ports, PGDATA tmpfs; единственный bind — собственный Unix socket scratch под ignored `.tmp`. Application/media checkout не смонтирован. Удаление контейнера и обоих scratch roots PASS.
- DB один alias с Unix socket, DJANGO_TESTING=1; LocMem cache/mail, временные media; внешние credentials исключены clean-env launcher. Guard установлен до django.setup, включая отдельный synchronous libpq guard.
- `.venv/bin/python docs/task33/qa04/test_safety.py` — exit 0, 7/7 PASS на финальном reviewed source.
- Дополнительные собственные synthetic checks — 4/4 PASS: extra Redis cache alias отклонён; symlink QA root отклонён; hostile inherited environment исключён; PGHOST/PGSERVICE/SMTP/socket variables отсутствуют в clean child env.
- Собственные libpq negatives — 4/4 PASS до реального подключения: TCP host, чужой Unix socket, hostaddr и service. Реальные попытки подключения в negative checks — 0.
- Runtime discovery: `catalog` 1091 уникальных IDs; explicit canonical modules 1231 уникальных IDs. Duplicates 0, extra default 0, missing full 140. Source AST и runtime согласованы. Wrapper owner153/admin228/public238/catalog118.

`scripts/run_kidsmap_tests.sh` full → `manage.py test catalog`; `src/catalog/tests.py` импортирует только 12 non-prefixed suites. Поэтому full пропускает 11 non-prefixed modules: adult_classes14, image_uploads14, legacy_migrations21, permanent_place_wizard16, phone_reveal8, photo_workflow9, place_filepond_admin2, place_readiness33, place_taxonomy_admin2, postgresql_cutover5, specialists16. QA04 explicit labels устраняют этот baseline coverage gap, исходный wrapper не исправлялся.

Codebase Memory callable: project root/freshness проверены, architecture scoped src/config, coverage original settings/runner/wrapper/tests metadata_match. testcases имеет ignored __pycache__ gap; статический AST/direct source использован для полноты. Graph best-effort не доказывает exhaustive completeness.

## Findings и ограничения

При первом собственном synthetic воспроизведении новый guard принимал extra cache alias и symlink root. Lead исправил оба; свежая проверка отклоняет их. App assertions/source не менялись. Ранний sandbox command отказал из-за bubblewrap mountinfo; разрешённые escalated read-only/local QA команды выполнены, это tooling boundary, не app failure.

Existing settings требуют overrides: TESTING не исключает DATABASE_URL/LEGACY_DATABASE_URL, media defaults repo/media, inherited EMAIL_BACKEND побеждает default. Reviewed launcher явно заменяет все эти пути. Transport guards предназначены для текущих Python connect/synchronous psycopg путей, не являются OS sandbox для arbitrary subprocess/UDP/async driver. Owned new container и проверенный mount/clean env — основная граница PostgreSQL isolation.

Synthetic fixtures source прочитан и measure лично запущен в новом disposable probe: network/shared-address/group через текущие Place/PricingPlan поля помечены логическими сценариями. Organization/OfferingGroup ещё не существуют. Parent application-suite evidence нельзя приписывать этому reviewer.

## Дополнительный собственный PostgreSQL probe

`python3 docs/task33/qa04/run.py --mode probe --output /tmp/task33-04-independent-probe` — exit0 PASS; новый контейнер и scratch cleanup PASS. `check` и `makemigrations --check --dry-run` PASS; forward migrate применил150 миграций, unapplied0, catalog leaf0116_moderation_sla_lifecycle. Backward/concurrency migration tests здесь NOT RUN; их покрытие принадлежит baseline suites lead.

Создано6 Place,2 логических филиала,2 независимых бизнеса с общим адресом,1 место без фото/координат,2 возрастных тарифа,4 старых отзыва (один known account с2 текстами +2 null-user),1 Event и1 Specialist. Volunteer identity использует импортированный backend constant; обе его HTTP проверки200.

Повторено по2 раза на одинаковых fixtures: ORM catalog6 результатов/2 SQL; map5/2 SQL; age tariffs1/1 SQL. HTTP200 во всех7 поверхностях: catalog19 SQL/6 результатов, detail64, owner43, admin47, volunteer13, events16/1 результат, specialist11. Результаты/SQL counts стабильны; exact ORM IDs сравнивались только в памяти. HTTP test client не rendered browser evidence. SQL text и row payloads не сохранены. Полные агрегаты в review evidence JSON.

## NOT RUN и handoff

Application suites — lead integration-reviewer выполняет отдельно; этот bounded review их не дублирует. Rendered browser, внешние integrations, production и рабочие services/media NOT RUN.

Named handoff: **integration-reviewer `/root`** — сопоставить собственные fresh baseline/migration/query результаты с 1231 explicit IDs, отметить baseline failures отдельно от environment failures; принимать этап 04 только после всех criteria. Следующие этапы/production не запускать. Review applies к SHA source в [04-review-evidence.json](04-review-evidence.json); если launcher/guard/settings/commands изменены, перепроверить изменённую границу.

## Review дополнений после первого полного baseline

Lead изменил только новый harness: убрал display sender override, добавил canonical bounded labels, complete subtest capture без params и запрет stale/symlink output. Повторная собственная safety7/7 PASS. Дополнительные собственные4 pre-Docker negatives PASS: некорректный prefix label, label в discovery mode, stale output (оставлен byte-identical), symlink output. Synthetic result capture без БД:2 failed subtests +1 error,3 complete records, параметры не сохранены. Runtime unknown canonical label после discovery отдельно не запускался; source whitelist predicate проверен, DB guard unchanged.

`src/catalog/testcases/test_password_reset.py:test_password_reset_standard_post_redirects` ожидает canonical KidsMap display sender; прежнее qa@ override было harness-induced false failure. Удаление только этого override сохраняет LocMem mail/clean env и исходный бизнес sender. Application assertion не менялась.

**Parent execution, отдельная attribution:** первый full1231 дал29 failures+4 errors/0 skipped. Старый capture пропустил2 subtest records; счётчики unittest и raw headers lead сохранены, полнота старого JSON не заявлена. Reviewer прочитал aggregate `/tmp/task33-04-failures-rerun/suite-results.json`:32 selected tests,27 failures+4 errors/0 skipped,31 complete failure/error instances в30 unique IDs, cleanup PASS. Mail и volunteer concurrent-create больше не среди problems. Mail — исправленный harness mismatch; concurrent-create — flaky/order-dependent, исправление приложения не заявлено.

Другие31 instances воспроизведены lead на unchanged application HEAD после sender correction; классификация existing baseline в текущей QA конфигурации, не regression от изменений app этапа04.4 errors — application district ValidationError; assertions затрагивают geographic filters/validation, localized copy, admin markup. Source geocoding tests используют explicit synthetic API-key override и mocks; это не доказательство live integration failure. В первом full нет network/libpq guard exceptions. Diagnosis каждого assertion и production effect остаются UNKNOWN; приложение/assertions не исправлены ради green. Финальный consistent full lead завершён; aggregate review ниже.

## Финальная сверка aggregate evidence

Lead `/root` выполнил финальный `--mode all`, artifacts `/tmp/task33-04-baseline-handoff`. Reviewer лично прочитал/проверил JSON aggregates, а не выполнял full application suite: **1231 тест,28 failures,4 errors,0 skipped,511.098s,exit32**. Все1231 executed IDs уникальны. Полные32 problem records,31 unique failed/error test IDs (два subtests относятся к одному parent). Checks/migrations и повторные query metrics PASS; unapplied0; cleanup контейнера и обоих roots PASS. Reviewed `.py` SHA совпадают evidence.

Первый full33 instances → финальный32 после удаления одного mail harness false failure; canonical sender testcase теперьPASS. Volunteer concurrent-create опятьFAIL в full: два fullFAIL и selectedPASS. Причина не исследована, appfix NOT_DONE; записано как flaky/order-dependent baseline, не скрыто и не объявлено исправленным. Остальные воспроизводимые failures остаются исходным application baseline. Assertions не ослаблены.

**Итог bounded independent review: PASS для выполненного scope этапа04 — isolation, reproducibility/discovery, synthetic probe и корректная фиксация baseline. Application suite остаётся BASELINE_FAILURE,32 failure/error instances.** Lead может завершить QA foundation при сохранении этих ошибок/границ в журнале; это не разрешение на stage05 или production и не принятие макетов владельцем.
