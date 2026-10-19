# SOCIAL-QA-09 Implementation Plan

> Исполнение: один lead django-reviewer; SEO/frontend/browser проверки последовательно тем же /root. Canonical roles из .agents, без независимых subagent claims. Расположение и запреты guide имеют приоритет над общими skill defaults.

**Goal:** Пагинация и сортировка ленты отзывов о местах сохраняют законные page/sort вместо301на первую страницу.

**Architecture:** Добавить только route-owned allowlist place_reviews:{sort,page} в существующий PUBLIC_QUERY_PARAMS. CleanPublicQueryMiddleware, controller/Paginator/normalization, context processor и header language links уже используют этот единый contract. Unknown keys продолжают удаляться; canonical/robots policy не меняется.

**Tech Stack:** Python3.12.15/Django6.0.2/PostgreSQL17.11, native Chromium155.0.8059.12; isolated RU/AZ/EN MO.

**Spec:** ../module09-2026-10-10-r1/findings/SOCIAL-QA-09.md, ../module09-2026-10-10-r1/repair-prompts/SOCIAL-QA-09.txt и PLAN SOCIAL-QA-09 в ../continuation-and-repair-prompts-2026-10-11.md. Текущие REPORT/results/source-entry/candidate-manifest этого run задают фактический snapshot.

## Global Constraints

- PLAN only, application changes0. Implementation09 требует одобрения именно этого двухфайлового scope. Уже данное одобрение scope не спрашивать повторно.
- C:/kidsmap, branch codex/module09-transfer-2026-10-16-r1, HEAD852938d96764ae315b92859e3651e5ea62054a36; source1023/dirty03–08 сохранить. После добавления теста ожидается1024.
- Без reset/clean/stash/dirty checkout switch/commit/push/deploy/production/автоматического active_run. Старые scripts — evidence, не команды автопродолжения.
- DJANGO_TESTING1, свой fictional PostgreSQL/DB/cache/media/private-media/locmem email, очищенный env без production credentials. Internal network/localhost browser allowlist; свежие own RU/AZ/EN MO, manifest verify/sole LOCALE_PATHS до setup.
- Не менять existing assertions ради green. Новые тесты исполняются как candidate из scratch до patch; кандидат не подменяет live source. Full ACCEPT09/global отдельно, старые PNG не догружать.
- ADJ-ANONYMOUS-LOGIN-08 OPEN/P2 сохраняется отдельно; этот план не включает auth/login/settings/404 fix.

## Task1 — gates и meaningful RED

- [ ] Получить human approval конкретного плана/diff. Сверить1023current source hashes, HEAD/branch/task33-progress/index/dirty/active_run:NONE/sharedMO/.cbmignore и предыдущие12packages.
- [ ] Fresh runtime/ownership/internalnet/RO repository mount/current source/template/soleMO проверить до reuse own09 PG. Новый implementation app/serve должен загрузить новое allowlist, не cached module PLAN09.
- [ ] Если source1023 прежний — использовать текущий RED:9unique methods (8failed/1passed,33assertion/subtest failures/0errors) и native matrix/probes. После drift воспроизвести affected кейсы заново; исторические module09 screenshots не замена свежему proof.
- [ ] Initial candidate robot expectation был уточнён до существующей полной DEFAULT_ROBOTS_CONTENT строки; первоначальный shortened expectation не достигался за RED301. Также pagination href проверяется после html.unescape, чтобы literal ampersand существующего template и HTML entity имели одинаковый URL смысл. Обе строки до этого не достигались за RED301. Два старых candidate/log сохранены (1.910s/2.171s), финальный exact candidate дал те же33fail за1.987s, без app patch или weakening query expectations.

## Task2 — exact two-file patch

**Modify:** src/catalog/services/public_urls.py, рядом с site_reviews allowlist около29.

**Create:** src/catalog/testcases/test_social_qa09_feed_query.py,9methods из candidate_tests.py.

Точный proposed.diff и полный candidate-public_urls.py/candidate_tests.py; SHA в candidate-manifest.json. Единственное изменение runtime:

~~~python
"site_reviews": {"sort", "page"},
"place_reviews": {"sort", "page"},
~~~

- [ ] git apply --check --ignore-space-change docs/qa/social-qa09-recheck-2026-10-17-pc-r1/proposed.diff
- [ ] Только после source/approval gates: git apply --ignore-space-change docs/qa/social-qa09-recheck-2026-10-17-pc-r1/proposed.diff
- [ ] Source1024, exactcandidate hashes, остальные1022 прежних source побайтно unchanged. Controller/template/middleware/context/JS/CSS/PO/models/schema не менять.
- [ ] Allowlist только sort/page, без расширения route family или wildcard. next/utm/foreign удаляются, repeated/default/invalid owned values оставляются существующему controller/Paginator контракту. Нормализация invalid sort→popular и invalid page fallback прежняя.
- [ ] Не добавлять canonical-query/robots изменения: у place_reviews canonical/hreflang остаются base URL без query, robots прежний DEFAULT_ROBOTS_CONTENT; видимый language switch query сохраняется через existing helper. Site reviews noindex/query policy и catalog default cleanup прежние.

## Task3 — targeted GREEN одним запуском

После approval новые9 + affected3existing =12unique methods:

~~~text
catalog.testcases.test_social_qa09_feed_query.SocialQA09FeedQueryTests
catalog.testcases.public.TestPublicPagesSmoke.test_legacy_redirect_keeps_catalog_filter_but_drops_foreign_query
catalog.testcases.public.TestReviewEnhancements.test_site_reviews_page_can_sort_reviews_by_likes
catalog.testcases.test_organization_directory.OrganizationDirectoryTests.test_directory_seo_and_language_links_preserve_only_public_filters
~~~

- [ ] New9 проверяют guest/author RU/AZ/EN page2; distinct complete pages1/2/3 (12/12/5 из29); все4sort choices с независимыми literal order expectations; combined sort/page+pagination href; foreign cleanup с сохранением legal params; repeated/default values+legacyAZ helper; language query/canonical/robots; invalid sort/page fallback; site/catalog/auth helper controls.
- [ ] Existing3 покрывают shared canonical/language query, site likes sorting и directory public filters/SEO. Existing assertions не менять. Full module09/project suite не запускать вместо targeted run.
- [ ] Ошибки среды/fixtures/контракта отдельно от SOURCE/BASELINE; не изменять проверяемое поведение/ожидания ради green. Новый root cause требует отдельного плана.

## Task4 — actual native acceptance

- [ ] Повторить ту же36cell matrix: guest/author×RU/AZ/EN×360/390/768/1024/1280/1440.29public fictional PlaceReview +29SiteReview controls, data seeded до запуска, без concurrent fixture mutation. Independent expected sort arrays из literal seeded counts/dates, не из самого сортирующего controller.
- [ ] Реальные anchors страницы2/3 и focus/Enter, real select likes+submit. После patch page2/page3 имеют URL/query/active2/3 и другие12/5review texts; likes сохраняется и меняет порядок на независимый expected. Page1/default popular/site page2 control прежние. Без response/DOM stubs или candidate module substitution.
- [ ] Все original15controls/cell сохраняются;6source failures/cell должны стать PASS. Добавить final GET reload page2/page3/likes и combined likes/page2; non-repeating native clicks, focus/scroll/layout, console/pageerrors/network/static/fonts, PNG после finite wait.
- [ ] SEO/query6rows:3langs mixed query cleanup→legal sort/page retained, canonical/hreflang base/robots policy unchanged; actual language menu switch retains2params; legacyAZ prefix+unknown cleanup single301→defaultAZ URL preserving2params. Site reviews/catalog cleanup controls прежние.
- [ ] Foreign query removed без внешнего next redirect; invalid/repeated/default values по existing fallback и только owned keys. Neither2nd redirect loop nor silent stripping of legal params. Exact status/Location chain/readback записать.
- [ ] Business review/vote aggregates unchanged для всех native GET interactions. Реакции/формы отправки/модерация не входят в patch. Other browsers/physical/realSR/fullWCAG/external services NOTRUN без отдельного выполнения.

## Task5 — report / preservation / stop

- [ ] Новый unique docs/qa/social-qa09-fix-…: approval/diff/source/candidate hashes, current RED→GREEN, exact commands/exits/counts, screenshots manifests, failed attempts, NOTRUN и verifier.
- [ ] Проверить all1024/other1022unchanged, все предыдущиеpackages bytes/manifests, entrycontainer ID/name/state, refs/index/activeNONE/sharedMO/.cbmignore. Из Docker snapshot не выводить whole-machine continuity.
- [ ] Добавить отдельную guide note с reverse-hash proof сохранения старых bytes. Закрыть только scoped SOCIAL09 после фактического GREEN; module09 не объявлять закрытым автоматически.
- [ ] Следующий этап — отдельный ACCEPT-09 по guide (full fresh corpus один раз), с учётом OPEN ADJ-ANONYMOUS-LOGIN-08 и новых findings; global corpus отдельно. Этот scope не разрешает автоматически fixes adjacent login, full module acceptance или module10.

## Review boundary

Одна строка общего allowlist + новый regression file, no DB migration or new strings/assets. Shared query consumers/source edges проверены; graph metadata gaps не скрыты. Proposed diff применимость проверена; candidate live rendering/implementation GREEN NOTRUN. Для implementation нужен конкретный scope approval по AGENTS/guide PLAN→IMPLEMENT, approval предыдущих03–08 на09 не переносится.
