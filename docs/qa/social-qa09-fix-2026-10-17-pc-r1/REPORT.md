# SOCIAL-QA-09 — CLOSED LOCAL, scoped PASS

Пагинация и сортировка публичной ленты отзывов о местах теперь сохраняют page/sort. Страницы1/2/3 показывают разные12/12/5 из29отзывов; likes сохраняет выбранную сортировку и правильный порядок, включая reload и combined sort/page. Foreign/next/utm удаляются, легальные параметры и language switch остаются. Canonical/hreflang base URLs и full robots policy прежние. Это scoped LOCAL closure; module09 остаётся OPEN до отдельной полной ACCEPT09, production UNKNOWN.

Execution /root,2026-10-17; один django-reviewer lead, SEO/frontend/browser проверки последовательно тем же агентом, без independent-subagent claims. Сообщение пользователя jlj,hz. распознано как «одобряю» в английской раскладке в ответ на конкретный двухфайловый PLAN09. Ветка codex/module09-transfer-2026-10-16-r1/HEAD852938d96764ae315b92859e3651e5ea62054a36. Применён exact approved diff: одна строка place_reviews:{sort,page} в src/catalog/services/public_urls.py и новый test_social_qa09_feed_query.py. Source1024; остальные1022 прежних source побайтно неизменны, dirty03–08 сохранён. Нет controller/middleware/template/context/JS/CSS/PO/model/schema changes.

## RED → GREEN

Неизменившийся RED ../social-qa09-recheck-2026-10-17-pc-r1/: current9methods8failed1passed/33assertion-subtest failures/0errors; native36cells540controlPASS/216sourceFAIL и SEO6rows23controlPASS/10sourceFAIL. Wrong query cleanup301 происходил до controller. Current candidates/hash совпадают с одобренными; existing assertions не менялись.

Один targeted GREEN запуск:12unique methods (9новых+3affected existing canonical/site/directory),3.853s,0failures/0errors,exit0. Проверены guest/author/RU-AZ-EN, pages1/2/3 и all4sort choices с literal order expectations, combinedquery/pagination href, repeated/default/invalid values, foreign key removal, legacyAZ helper, language/canonical/robots и shared site/catalog/directory rules. Full module/project corpus не запускался.

Native36guest/author×RU/AZ/EN×360/390/768/1024/1280/1440:648controlPASS/216sourcePASS. Original15controls/6source assertions/cell unchanged, добавлены3reload checks. Реальные page2focus/Enter, page3anchor, likes select/Apply; после navigation и reload правильные URL/active page/review texts/selected sort. Site page2 shared control проходит, placeholders/response stubs не использовались. Review/vote aggregate snapshots неизменны;0pageerrors/requestfailed/HTTPfailures/consoleerrors.108PNG.

SEO/query6rows:23controlPASS/10sourcePASS,3PNG. Mixed query301 очищает foreign keys и сохраняет legal sort/page; real language dropdown click сохраняет оба параметра, canonical/hreflang остаются base, robots — full current DEFAULT. LegacyAZ+unknown query даёт один301 на defaultAZ URL с2параметрами; site/catalog cleanup controls прежние.

Combined6guest/author×3langs native flows:96checksPASS,12PNG. Direct likes/page2=200,correct12texts→reload→native page3 сlikes/last5→reload→keyboard page1/first12. Canonicalbase/layout/business snapshot checks также PASS. Все123PNG свежие local native; representative manual subset отмечен отдельно, не утверждается manual review всех файлов/full WCAG/realSR.

## Runtime / preservation

Новый own m09s09-fix-r1-app/session social09-pc-fix-r1/loopback33370, verified own PLAN09 PG/internal network reused. Python3.12.15/Django6.0.2/PostgreSQL17.11/Chromium155.0.8059.12. Repository RO, только own scratch RW; cleared env/DJANGO_TESTING1, separate testDB test_m09s09_fix_r1/cache/media/private-media/locmem email. Normal fictional DB29+29reviews retained without reseed or concurrent writes; browser GETs не изменили review/vote aggregates. Fresh native RU/AZ/EN MO manifest verified before each setup, sole LOCALE_PATHS; sharedMO unchanged. External browser requests blocked by localhost allowlist, no production credentials/integrations used.

13prior packages preserved byte-for-byte, включая весь PLAN09. Entry container ID/names сохранены, добавлен только ownapp; actual state deltas в container-state-changes.json/results.json, не подменяются claims о полной process continuity. Старый04fix app уже exited до входного snapshot этого run. No task stop/restart/delete чужих контейнеров; current own app/PG running/live source hashes verified. HEAD/branch/index/task33-progress/active_run:NONE/sharedMO/.cbmignore сохранены. Guide получает separate closure note с reverse-hash proof old bytes. Без reset/clean/stash/dirty checkout switch/commit/push/deploy/production.

## Limits / next step

Git apply exit0 дал nonfatal new-blank-line-at-EOF warning для exact approved regression candidate; hash сохранён. Preparation/native/application failures в этом fix-run отсутствуют. Exact source/assertion/PNG/artifact integrity проверяется свежим verifier перед delivery.

SOCIAL01–09 закрыты только в своих фактически проверенных LOCAL scopes. Module09 ещё OPEN; ADJ-ANONYMOUS-LOGIN-08 (anonymous inbox302→/accounts/login/404) остаётся отдельным OPEN/P2 и не исправлялся этим patch. Следующий этап — отдельная full ACCEPT-09 по guide, с учётом этого finding; после новых acceptance findings нужны отдельные планы/решения. FullACCEPT09/global/adjacent login fix/production/physical/realSR/fullWCAG/otherbrowsers/external services NOTRUN. Module10 автоматически не начат, повторное approval уже выполненного09 не требуется.
