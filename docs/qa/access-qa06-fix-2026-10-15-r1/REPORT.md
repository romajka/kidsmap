# ACCESS-QA-06 — scoped LOCAL PASS

Одобрение пользователя «одобряю» относится к [точному плану](../module07-full-2026-10-15-r1/PLAN-ACCESS-QA-06.md); [SHA/scope](approval.json). Новый run2026-10-15. Реализация только в двух согласованных application-файлах.

## Что исправлено

`src/catalog/forms.py:907`: добавлен strip=False только полю AccountDeletionConfirmForm.typed_confirmation. До patch форма отрезала крайние пробелы, после — передаёт буквальную строку строгому сервису. Неточная фраза теперь даёт400 и сохраняет активный аккаунт/код. Новый `src/catalog/testcases/test_access_qa06_deletion_phrase.py` — ровно предложенные4метода,91строка. Другие поля, сервис/фразы/PO/JS/CSS/views/sessions/retention не менялись. [Точный inverse](inverse-proof.json) возвращает entry-байты dirty forms.py, сохраняя чужие изменения.

## Snapshot и среда

Root /home/ramin/kidsmap; HEAD e4e05cc213b34e2d771ecb854901bfd016d1db51; branch task33-progress; dirty WORKTREE; active_run NONE. [Entry](entry.json):29682project files,63foreigncontainers,2knownHTTP. Entry mode label was inherited from the audit capture helper; [explicit metadata correction](entry-mode-correction.json) links the actual APPROVED IMPLEMENT authority. Original entry unchanged. Один исполнитель последовательно выполнял канонические orchestrator/django-reviewer/browser-qa/integration проверки; независимые специалисты не заявляются. Skills debugging/TDD/verification/Playwright, прежний concrete plan и docs сохранены.

DJANGO_TESTING=1; собственные PG41859/HTTP39199, DB/user access06_fix_r1/container+volume access-qa06-fix-2026-10-15-r1-pg; отдельные cache/media/private-media/filebased email+private mail journal. ENV очищен до setup, checkout .env не загружался; Python socket guard допускает только свой PG; browser blocks external origin. Host-wide firewall не заявляется. Только SIMULATED TEST_POLICY, production default остаётся inactive. [Runtime](runtime-info.json):Python3.12.3/Django6.0.2/pypdf6.20.1,175migrations. Exact pypdf скопирован в собственный python-deps/venv; shared environment не менялась. [Dependency hashes](dependency-manifest.json).

Fresh current RU/AZ/EN PO собраны builder→собственные MO, build0/verify0. [Manifest](locale-manifest.json); sole LOCALE_PATHS до django.setup, actual opened own3MO в [source](runtime-source-final.json). Shared MO не перезаписаны. Свой prepatch HTTP остановлен только после argv/cwd/PID check; после patch новый own interpreter загрузил strip=False. Source943paths/cached template/module origins/runtime dependency сверяются final gate. Чужие HTTP не перезапускались.

## RED → GREEN и точные проверки

[Fresh RED](regression-RED.status.json):4новых метода в app test-file,24ожидаемых subtestFAIL,0ERROR;66.607s process/29.266s tests. [Native RED](native-RED.js.result.json):RU390,5controlPASS/1sourceFAIL; raw padded string реально отправлена с кодом собственного письма, HTTP302/account inactive/SCHEDULED. Prepatch app field strip=True. Это fresh reproduction, не перенос старого FAIL.

[Target GREEN](target-GREEN.status.json):те же4метода без изменения assertions плюс прежние7целевых deletion tests,11/11PASS,exit0;89.292s process/45.341s tests. Проверены exact/raw HTTP/form, code hash/attempts, correct/wrong code, sessions, cancellation/reset requirement, signed status/foreign-user boundaries. [Selectors](GREEN-selectors.json). [Form guards](form-guards.json):12/12PASS required/max_length/exact/padded в RU/AZ/EN, без DB writes. Existing assertions не ослаблялись.

[Accepted native](accepted-observations.json):684PASS,0FAIL/0NOT RUN,18cells RU/AZ/EN×360/390/768/1024/1280/1440. Все18начинаются с собственных initial verified fixtures; registration не объявляется заново проверенной. Затем реальные UI login→deletion request→local mail. Leading/trailing/both/NBSP дают400/локализованную typed error, сохраняют исходную строку и код/активность/5attempts. Tab/Shift+Tab/visible focus и Enter; ошибки и геометрия. Exact phrase+wrong code400/4attempts; exact+valid302/SCHEDULED/inactive/code consumed, signed status, old-session denial. Последний unauthenticated replay POST не меняет состояние; это не отдельный сервисный replay при авторизованной сессии. State19SCHEDULED включает1сохранённый prepatch RED fixture и18GREEN; final processor в fix-run NOT RUN.

[QA oracle provenance](oracle-provenance.json): original native-GREEN JSON retains666PASS/18FAIL caused only by the wrong status-URL expectation. Separate status-recheck renders all18already UI-scheduled accounts at canonical signed URLs, tests missing/bad token404 and no mutation. Its18PASS replace only these QA observations in accepted684; no new native redirect proof is claimed.6new status PNGs retained.

[134PNG manifest](png-manifest.json):2RED+126GREEN+6read-only-status; нативная mask только поля кода, без DOM/CSS edits. Code сохранён приватно до mask, реальные mail bodies/passwords/tokens не включаются. Manual visual scope в [visual-review](visual-review.json); не заявляется просмотр каждого134PNG. Console/pageerror/network по каждой18cell: фактические expected HTTP400 errors и заблокированные external fonts отдельно от локальных сбоев, [diagnostics](native-GREEN.js.result.json). [Commands/exits](commands.jsonl), driver consumes actual JS text, а ledger `<path>` — ссылка на template, не literal CLI argument; собственная сессия access06fixr1green, private credential lookup только в памяти.

## Сохранность и решение

[Gate](verification.json) проверяет exact inverse формы/guide, новый test byte-match approved proposal, HEAD/branch/active_run,29682baseline files, sharedMO,63container ID/name/ports/state и2knownHTTP identity, own runtime source, semantic GREEN,PNG hashes и secret scan. Предыдущие full-r1/repair отчёты не переписаны. Четыре более старых HTTP отсутствовали ещё до full-r1: continuity остаётся NOT VERIFIED, не восстановлена задним числом.

ACCESS-QA-06 CLOSED LOCAL только по проверенному scope. [Текущая сводная приёмка модуля](../module07-accept-2026-10-15-r2/REPORT.md) сохраняет полную предыдущую приёмку по hashes;338неизменённых методов не гонялись повторно. Natural retention/backup expiry, real OAuth/SMTP, production/commit/push/deploy, cross-browser/real screen reader, module08/global corpus NOT RUN.
