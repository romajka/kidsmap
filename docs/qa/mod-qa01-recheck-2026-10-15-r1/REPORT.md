# PLAN MOD-QA-01 — CONFIRMED OPEN / план готов

2026-10-15. Модуль08 начат с первой задачи по явному «дальше» после module07 LOCAL PASS. Режим только fresh recheck/PLAN. Приложение/CI/schema/existing assertions не менялись. Реализация ожидает одобрения [конкретного плана](IMPLEMENTATION_PLAN.md).

## Snapshot / роли

Фактический root /home/ramin/kidsmap; HEAD e4e05cc213b34e2d771ecb854901bfd016d1db51, task33-progress, dirty WORKTREE, active_run NONE. [Entry](entry.json):29902file hashes,64foreigncontainer identities,3known QA HTTP. Исторические Windows/другие локальные PID/порты не использовались. Один исполнитель, canonical orchestrator/frontend-admin/Django/browser-qa роли последовательно; независимые специалисты не заявляются. Применены systematic-debugging/writing-plans/KidsMap UI/frontend/accessibility/Playwright; querystring API сверен Context7.

## Свежий finding MOD-QA-01 · P2

Роли admin и content reviewer (staff+catalog.change_place), путь moderation hub. Собственные initial fixtures35организаций/candidates:32pending,3draft; author fictional volunteer. Backend отдаёт25строк на первой странице, pending counter32. Ссылок page2 и pager links нет. Ручной URL page=2 даёт7других строк. Отсутствует именно штатный переход из этой очереди; глобальная потеря записей не заявляется.

[Native result](browser-recheck-r2.js.result.json):RU/AZ/EN ×360/390/768/1024/1280/1440 ×2roles =36cells.75control PASS/72source FAIL observations,0NOT RUN в корректном recheck. Это наблюдения, не147независимых tests;72FAIL — одна причина (нет pager/keyboard links). Native login выполнен; page2 адрес введён вручную и не выдаётся за UI pagination. Tab/Enter по отсутствующим controls NOT RUN.

Source: moderation_hub_index в src/catalog/domain_admin/volunteer.py:282–296 уже передаёт Paginator(rows,25).get_page; активный src/catalog/templates/admin/volunteer/hub_index.html завершает таблицу без навигации. Source/template cache/process доказательства в [runtime source](runtime-source-final.json). Graph coverage template partial; прочитан полный короткий template, graph не использован как исчерпывающее доказательство. Существующий baseline текущего source, не regression этого read-only run. Confidence HIGH.

## Regression / UI evidence

[Prototype proposal-RED](proposal-RED.status.json):4QA methods,6ожидаемых locale subtestFAIL (next/previous по3языкам),0ERROR;2метода PASS для existing empty/invalid/out-of-range/denied roles/GET-only/no candidate changes. Ran4 in1.968s,process48.327s,exit1. Прототип только в этом QA каталоге, permanent app test не добавлен. Existing assertions не ослаблялись.

[36PNG manifest](png-manifest.json):admin page1/page2 во всех18language-width cells. Для reviewer rendered DOM/control/state assertions без отдельных PNG; не заявляется полный role×PNG corpus. Ручной просмотр page1 RU1440 и page2 EN1440 — [visual scope](visual-review.json). Остальные PNG имеют native capture/manifest, не объявляются все просмотренными вручную. Native console/pageerror/network captured: unexpected local failures0; blocked external font requests отдельно в result JSON.

Первый QA attempt использовал предполагаемые id_username/login-form, которых нет в текущей Jazzmin login форме. Получены2NOT RUN на login, pagination не проверена. [Оригинальный result](browser-recheck.js.result.json), [наблюдаемый native DOM](login-dom.txt), [коррекция только QA selectors](login-selector-correction.json) сохранены. Новый r2 использует реальные name=username/name=password/button. Source FAIL исходят только из завершённого r2; initial NOT RUN не превращены в PASS.

## Собственная среда / сохранность

DJANGO_TESTING=1; own PG51877/HTTP34211, DB/user mod01_recheck_r1/container+volume mod-qa01-recheck-2026-10-15-r1-pg. Собственные cache/media/private-media/filebased email, очищенный env до setup; .env/production credentials не читались. Python socket guard только свой PG, browser external-origin blocked; host/tool-wide firewall не заявляется. Default deletion policy inactive; для этого recheck её не включали. [Runtime](runtime-info.json):Python3.12.3/Django6.0.2/pypdf6.20.1,175migrations; dependency в своей venv/python-deps, shared installs не менялись.

Текущие RU/AZ/EN PO собраны builder в own locale output, build0/verify0; [manifest](locale-manifest.json), единственный LOCALE_PATHS до django.setup и actual opened3ownMO. Слова для будущего pager уже переведены, PO-изменения не нужны. Новый процесс cached hub template SHA/module origins/current943sources сверяется [gate](verification.json); это current runtime, а не старый PID.

Readonly own [state](state-final.json) fingerprint Organization live/candidate одинаков до/после browser. Initial fixtures и login sessions — setup, а не отсутствие вообще любых DB writes. Никаких approve/reject/publish/save на проверяемых объектах. Gate сверяет29902entry files, sharedMO/HEAD/branch/active_run,64foreigncontainers/3knownHTTP. Только текущая module08guide note/table и own QA artifacts разрешены. Module07reports/evidence сохранены. Непрерывность четырёх гораздо более старых исчезнувших HTTP остаётся NOT VERIFIED, не подтверждается задним числом; чужих restarts не было.

## Решение / NOT RUN

MOD-QA-01 остаётся OPEN, implementation not approved/not applied. [Минимальный diff](proposed-MOD-QA-01.diff):только7строк в hub_index.html +новый4method test-file; git apply --check0. [SHA](plan-source.json). Backend/shared partial/CSS/JS/PO/ACL/count/sort untouched.

[Next prompt](next-prompt.txt). Дальше — отдельное одобрение двух файлов, fresh RED→GREEN и целевые checks. Другие MOD IDs/module08 full, future nav UX/keyboard flow/GREEN, rendered empty/out-of-range/error states, production/commit/push/deploy, real external integration, cross-browser/screen-reader/module09 NOT RUN. Полный модуль08 — один раз после его задач, неизменённый module07 corpus не повторять.
