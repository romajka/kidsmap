# SEO canonical Implementation Plan

**Goal:** убрать лишние URL и согласовать индексацию каталога без изменения адресов карточек.
**Architecture:** единый public_urls очищает default sort/page; middleware делает301. Context processor сохраняет page>=2 и строит canonical фильтров по очищенной query. Detail view объединяет исправление slug и параметров после проверки публичной видимости. Пагинация ссылается прямо на чистую первую страницу.
**Tech Stack:** существующие Django/Python/SSR; новые зависимости не нужны.
**Spec:** docs/qa/seo-indexation-audit-2026-10-09.md, текущая явная команда пользователя на реализацию.

## Constraints

AZ без префикса, RU/EN с префиксом; чистая ветка task33-progress; preserve audit report; без изменения slug, данных, качества и порогов посадочных, auth next, robots доступа. Изолированные тесты DJANGO_TESTING=1; не использовать production credentials. Существующее разрешение на push/deploy и текущая команда на внедрение сохраняются.

## Task 1: Regression and implementation

Files: src/catalog/services/public_urls.py, middleware.py, context_processors.py, views.py, templates/catalog/place_list.html; tests test_seo_indexability.py/test_localized_place_seo.py.
- [x] Добавить тесты: AZ/RU/EN `sort=new&page=2`301→`page=2`→200/index/self-canonical; `category=EDU&page=1`301 сохраняетcategory; auth next не меняется; фильтры noindex с canonical текущей query; старый slug+review_sort301 прямо на публичный detail; скрытый detail404; первая страница пагинации безpage=1.
- [x] RED: `PATH="$PATH:/snap/bin" python3 docs/task33/qa04/run.py --output /tmp/kidsmap-seo-fix-20261009/red --label catalog.testcases.test_seo_indexability --label catalog.testcases.test_localized_place_seo`.
- [x] Реализация: удалять только однозначные `page=1` и `sort=new` в place_list; не менять реальные фильтры, альтернативную сортировку и invalid pagination. Detail query очистить в view вместе соslug после visibility lookup. Canonical фильтров использовать очищенную query и нормальный порядок ключей; robots остаётсяnoindex. Пагинация1 ссылается наrequest.path с реальными фильтрами.
- [x] GREEN: те жеlabels/new output; затем public/auth/url/landing regression. Не менять assertions ради прохождения: изменения старых ожиданий только для явно согласованного нового поведения.

## Task 2: Release

- [ ] Проверить diff, compile/syntax/targeted regression, записать report; commit/push только task33-progress.
- [ ] SSH сверить exact baseline da6d6458/clean и текущий image; pinned candidate собрать из allowlisted Git archive безenv/media/QA. Сохранить предыдущий image; миграций нет. Backup сервернойenv/override перед сменой pin; не трогатьwrite flags/media/mounts.
- [ ] Новый image validate check/migrate --check; заменить только imagepin существующего runtime override; compose recreate web.
- [ ] Внешний HTTP проверяет301defaultsort/page1, page2index/selfcanonical, фильтрnoindex/selfcanonical, one-hop slug query, robots/home/admin и все276sitemapURLs. Browser search/filter/navigation. Логи после cutover:0tracebacks/5xx. При неуспехе pin на предыдущийimage и recreate; schema/data не менялись.
- [ ] Финальный отчёт: deployedSHA, tests, HTTP evidence, GSC live inspection/index request NOT RUN; индексацию Google не обещать.
