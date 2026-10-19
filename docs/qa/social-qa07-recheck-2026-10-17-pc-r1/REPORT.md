# SOCIAL-QA-07 — CONFIRMED OPEN/P3, PLAN COMPLETE

2026-10-17, Asia/Baku. Свежая проверка подтверждает техническое Activity object в заголовке отзывов вместо действительного публичного имени. **Application changes0; implementation approval PENDING** для двух файлов: контроллер и новый9method test. [План](IMPLEMENTATION_PLAN.md), [two-file diff](proposed.diff), [candidate controller](candidate-typed_reviews.py), [candidate tests](candidate_tests.py), [hashes](candidate-manifest.json).

Это тот же SOCIAL07, который ранее наблюдался как ADJ-ACTIVITY-TITLE в05–06; новые независимые finding IDs не создавались. SOCIAL01–06 сохраняют scoped LOCAL closures, module09 OPEN. Production applicability UNKNOWN.

## Source и причина

C:\kidsmap, branch codex/module09-transfer-2026-10-16-r1, LOCAL HEAD852938d96764ae315b92859e3651e5ea62054a36, dirty approved SOCIAL03–06.1021source/PO совпадают с final06. task33-progress=e4e05cc213b34e2d771ecb854901bfd016d1db51, index tree881e0c48c7d557c46221beb3b2410a157982f861/staged empty, active_run:NONE. [Entry](source-entry.json), [final](source-final.json), [preservation](preservation.json).

Один lead последовательно выполнял canonical django/frontend/browser checks; независимых subagents нет. Применены writing-plans/verification и проектные source/UI/testing rules.

Graph C-kidsmap generation2026-10-16T18:56:53Z. Broad BM25 query был ограничен, затем narrow exact public_presentation symbols возвращены полностью; coverage unavailable/metadata_changed, public detail template partial. Source прочитан, dynamic Django/template relationships проверены literal search. Exhaustive/graph completeness/reindex выводов нет, cache не сохранялся. Первоначальные rg path wildcards в PowerShell дали OS123; повтор через existing dirs/-g/rg --files корректен, app files не создавались.

typed_reviews.target_reviews() около98 использует name_i18n or str(target). У Activity отсутствует нужный display accessor, результат — Activity object(pk). Публичная карточка уже использует public_presentation.present()['name']. Его activity_texts/translated обеспечивают request locale→AZ fallback и разрешённый approved snapshot/live Program path, не читая candidate revision.

Предлагается только Activity target_name получать через тот же present(target,request language)['name']; Place/Specialist/Event оставляют прежний путь. Никакой новой локализации, model accessor/__str__, template/PO/schema/service refactor.

## Новый isolated runtime

Собственные m09s07-plan-r1-app/pg, internal network m09s07-plan-r1-net, volume m09s07-plan-r1-pgdata; DB m09s07_plan_r1/testDB test_m09s07_plan_r1. Repo bind RO, own scratch RW. DJANGO_TESTING1/cleared env до setup, no .env/prodcredentials; отдельные cache/media/private-media/locmem email. Fictional author,3Activity name scenarios и3other target kinds.

Fresh RU/AZ/EN MO из текущих PO через native builder/verify, sole LOCALE_PATHS=.tmp/social07-pc-plan-r1/locales/locale; sharedMO прежние. Separate Chromium155.0.8059.12/session social07-pc-plan-r1, loopback33347/hidden own proxy; Python3.12.15/Django6.0.2/PG17.11. Localhost-only browser/external blocked. [Runtime](runtime-info.json), [live-final](live-final.json), [locale manifest](locale-manifest.json).

## Native evidence

| Группа | Результат |
|---|---|
| Localized Activity guest/author ×RU/AZ/EN ×6widths |36cells|
| AZ-only fallback и permitted snapshot, обе роли×3langs×390 |12cells|
| Shared Place/Specialist/Event, обе роли×3langs×390 |18cells|
| Всего |66cells/540controlPASS|
| Activity h1/document title/no technicalID |48cells/144sourceFAIL|
| Shared other kind title checks |18cells PASS внутри controls|
| Unhandled pageerrors / local HTTP failures / request failures |0 /0 /0|
| Native viewport PNG |114|

[Matrix](matrix.json), [runner](matrix.py), [native cell](cell-body.js), [targets](targets.json), [PNG manifest](png-manifest.json), [CLI commands](browser-commands.jsonl). Exit0 означает завершённую сборку RED, не product PASS. Исторические18FAIL finding не смешиваются с нынешними144explicit checks.

В48Activity cells открыт настоящий public detail, проверен его literal human h1, выполнен native click по реальной ссылке отзывов, затем reload. Карточка корректна, review h1 и browser title содержат Activity object; причина одинаковая при local fields/AZ fallback/approved snapshot. Role editor/locale prefix/layout/reload/data controls PASS. Business aggregates до/после:3activities,0reviews всех четырёх типов. QA auth session setup fictional; не password/OAuth proof.

Вручную просмотрена пара public detail/reviews guest RU390: человеческое имя карточки и техническое имя после перехода. Native screenshots не доказывают real screenreader/fullWCAG acceptance.

## Candidate regression RED

Полный новый тестовый файл исполнен как candidate_tests.SocialQA07TitleTests из ignored scratch, **не application path**.9unique methods, **7failed methods/2PASS,18assertion-subtest failures,0errors**,2.769s,exit1. [Log](tests.log), [exit](tests.exit), [code](candidate_tests.py).

Падают Activity requested names, AZ fallback, permitted snapshot, live approved Program inheritance, escaping-title value, canonical empty и staff-only hidden canonical name. Visibility guest/author404 и other target kind paths PASS. Это meaningful functional RED против текущего controller; существующие assertions не менялись. Предыдущие successful unchanged full suites не повторялись.

## План и ограничения

Изменить только src/catalog/controllers/typed_reviews.py и создать src/catalog/testcases/test_social_qa07_activity_review_title.py. Diff apply-check0; оба candidate Python files AST parse PASS. Candidate не импортирован в application handler и не применён, post-patch GREEN NOT RUN.

Canonical empty осознанно остаётся empty, включая permitted staff-only unpublished target: не раскрывать private raw name и не выдумывать локализованную подпись. Заголовок тогда может содержать только локализованный префикс, как в public presentation нет имени. Это крайняя граница плана, не утверждение о готовности content-quality/admin UX.

Добавляется второй read-only present() для Activity после visibility check; часть SQL чтений дублируется. Query optimization/cache/refactor вне scope. Existing visibility/CAS/POST/moderation/schema не меняются. После approval:9new tests GREEN +2small affected03render/CAS methods, actual native66cells and representative privacy/escaping/live Program checks. Existing assertions не ослаблять.

## Preservation / stop

Все1021source/dirty03–06/sharedMO/.cbmignore/refs/index/active_run сохранены; все8prior QA packages/manifest/verification сохранены. IDs/states38entry containers прежние, добавлены только own2контейнера07, foreign restarts0. Whole-machine process continuity NOT VERIFIED. Guide дополняется новой note с reverse-removal SHA, история не переписывается.

NOT RUN: app patch/postpatchGREEN/acceptance, SOCIAL08–09/full ACCEPT09/global/module10, unchanged full backend corpus, physical/crossbrowser/realSR/fullWCAG, real external integrations/production/commit/push/deploy. Без reset/clean/stash/dirty checkout switch; старые PNG не догружались.

Следующее действие — одобрение [конкретного двухфайлового плана](IMPLEMENTATION_PLAN.md). Реализация07 не начинается автоматически. [Commands](commands.md), [verification](verification.json), [artifact manifest](artifact-manifest.json), [next prompt](next-prompt.txt).
