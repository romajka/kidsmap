# ORG-QA-04 — AZ/EN patch, RU fallback regression OPEN

2026-10-13 Asia/Baku. Root / kidsmap-orchestrator, `.agents/agents/kidsmap-orchestrator/agent.md`, последовательное исполнение. LOCAL checkout `/home/ramin/kidsmap`, task33-progress, HEAD e4e05cc213b34e2d771ecb854901bfd016d1db51 +dirty WORKTREE, active_run NONE. Production NOT RUN.

## 1. Состояние области

**OPEN**, полного acceptance нет. По конкретному [плану](../module02-remaining-recheck-2026-10-13-r1/PLAN-ORG-QA-04.md), одобренному «одобряю», изменены только AZ/EN PO: 14 absent exact entries добавлены, один fuzzy «Одобрить заявку» переведён и fuzzy снят. [authorization.json](authorization.json), [entry.json](entry.json), [source](entry-final.json). Existing assertions/backend/settings/application workflow/shared MO/RU PO не менялись.

Собственный fresh profile `http://127.0.0.1:45793`, PID50447, DB orgqa04_20261013_r1, собственный PG loopback127.0.0.1:35715, unique cache/media/private-media/email/cookies/browser. DJANGO_TESTING=1, no .env/production, only own-PG egress. Fresh isolated [manifest](locale-manifest.json), helper build/verify exit0, sole LOCALE_PATHS. [Runtime source match](runtime-version-final.json).

## 2. Сильные стороны / executed

[Copy proof](copy-proof.json):15 согласованных entries корректно возвращаются на AZ/EN в одном процессе с повторной сменой языка; lazy model/section/badge использует активный язык. [Browser](browser.result.json):55 rows,52PASS/3FAIL, pageerrors0/local network errors0. Native admin language dropdown, native create/save/reload/submit/approve/candidate save на RU/AZ/EN; 36 add/edit renders на6widths и4 same-session switches. [READ ONLY state](diagnostic.json): все3 собственные native организации published, live names отдельно от draft candidate.

## 3. Реальные проблемы

Новый regression этого же ID:14 missing RU msgid теперь fallback к default AZ, потому что LANGUAGE_CODE=az. RU labels «Adlar», «Təşkilatlar», «Sahiblik»; два native RU return checks FAIL. Before patch русский fallback был source msgid, после добавления default AZ catalogue изменился. Причина доказана actual gettext/lazy output и `dom-diagnostic.result.json` htmlLang=ru. Это реальная regression, не environment failure.

Минимальное нужное расширение — [PLAN-RU-FALLBACK.md](PLAN-RU-FALLBACK.md): единственный дополнительный `locale/ru/LC_MESSAGES/django.po`,14 identity translations (msgstr=русская подпись), «Одобрить заявку» в RU уже переведён. RU был явно исключён из предыдущего плана; expansion approval запрошен отдельно и пока не получен. Settings/LANGUAGE_CODE менять не надо.

`published-en` probe FAIL при мгновенном count button; READ ONLY доказывает published, поздний GET видит один unpublish button. Причина count timing/DOM discrepancy не окончательно установлена; исходный FAIL сохранён, не объявлен PASS по предположению. После разрешённой locale correction нужен fresh visible-state/readback gate.

## 4. Tech debt

Default catalogue fallback влияет даже на source-language RU; отсутствующие identity entries требуют внимания при новых default-language translations.

## 5. Risks

Рабочий diff содержит незакрытую RU regression; production не затронут. Никаких чужих процессов/WORKTREE/assertions изменений, кроме отдельно approved CSS другого scope. Historical recheck runtime не перезапускался.

## 6. Dead/legacy

Не исследовано, удаления не выполнялись.

## 7. Tests gaps / NOT RUN

4 targeted existing tests включены в подготовленный248 explicit module suite; запуск один раз отложен до завершения locale corrections, без повторных full runs. Native error/conflict и полный final matrix не приняты. Real external integrations/production/commit/push/deploy NOT RUN.

## 8. Handoff

Ждём конкретного approval RU дополнения. После него новый fresh build, only own runtime restart/unique profile, RU→AZ→EN→RU и rendered acceptance, затем один полный module test run. Полная ACCEPT-02 продолжается в `../module02-full-2026-10-13-r1/` и не считается PASS.

## 9. Priorities

ORG-QA-04 P3 OPEN, regression RU после разрешённого AZ/EN patch требует исправления перед closing. Не закрывать ID или module по количеству PASS rows.
