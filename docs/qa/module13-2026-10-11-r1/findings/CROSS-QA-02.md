# CROSS-QA-02 — команда CI не обнаруживает значительную часть тестов

P2, свежий локальный discovery на WORKTREE, 2026-10-11. Роль: QA / release. Endpoint: команды тестирования. Actual GitHub execution NOT RUN.

Команда `.github/workflows/deploy.yml:78` — `python manage.py test --parallel 1` без labels. Свежий discovery-only relay настоящего `manage.main` обнаружил 618 методов, без `catalog.testcases.test_*`. Отдельный `catalog` обнаруживает 1950; `catalog` плюс 11 пропущенных non-test-prefixed модулей — 2090 уникальных методов. Разница: 1472 метода относительно CI-команды и 140 относительно wrapper `full`.

Это числа текущего локального корпуса, включающего чужие untracked tests; они не доказывают наличие всех этих файлов в GitHub. 1472 пропущенных WORKTREE методов = 1452 из tracked sources + 20 из чужих untracked tests. Свежий отдельный HEAD donor: no-label618, catalog1930, полный2070; CI-команда пропускает1452, wrapper140. Разбивка с точными IDs: [corpus qualification](../test-review/discovery-corpus-qualification.json), [HEAD discovery](../test-review/head-discovery.json). Discovery не исполняет тесты и не создаёт DB; результаты полного запуска указаны отдельно.

Ожидание: обязательный quality gate обнаруживает согласованный полный набор тестов, новые `test_*` модули не выпадают молча.

Факт: root discovery идёт через `test_catalog.py:7`, импортирующий только `catalog.tests`. Каталог src без `__init__.py` не обходится root unittest discovery. Wrapper `scripts/run_kidsmap_tests.sh:58` передаёт `catalog`, но не включает 11 non-test-prefixed доменов. Пять relevant tracked sources сопоставлены с HEAD; assertions не изменялись.

Шаги: на изолированном DJANGO_TESTING=1 окружении получить suite IDs для labels=[]; затем для catalog; затем catalog плюс перечисленные в full-inventory.json 11 доменов; сравнить уникальные IDs. Повторить фактический manage.main через discovery-only relay.

Доказательства: [discovery-audit](../test-review/discovery-audit.json), [manage relay](../test-review/manage-discovery.json), [source verification](../test-review/discovery-source-verification.json), [полный корпус](../test-review/full-inventory.json), [отчёт исполнителя](../test-review/REPORT.md).

Риск: зелёный запуск quality gate может не покрывать owner/admin/security/domain regressions; конкретный production incident не установлен. Область исправления: discovery/явные suite labels, wrapper и CI; зависимости — custom runner cache/translation resets, PostgreSQL, transport fixtures и locale profile. Не делать пропущенные tests необязательными ради green.

Самостоятельный промпт: [CROSS-QA-02-repair.txt](CROSS-QA-02-repair.txt).
