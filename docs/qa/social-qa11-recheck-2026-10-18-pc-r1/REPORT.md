# SOCIAL-QA-11 — свежий PLAN, 2026-10-18 pc-r1

## 1. Решение и авторизация
PLAN готов, точный трёхфайловый кандидат вне приложения. SOCIAL-QA-11 P3 и module09 OPEN; IMPLEMENT-APPROVAL PENDING. Пользователь «дальше» разрешил следующий PLAN, не новую реализацию. Scope approval требуется по AGENTS.md:6. Lead kidsmap-orchestrator; профиль UI/accessibility проверен последовательно одним исполнителем, независимых специалистов не запускали.

## 2. Срез
LOCAL HEAD 852938d96764ae315b92859e3651e5ea62054a36; branch codex/module09-transfer-2026-10-16-r1; task33-progress e4e05cc213b34e2d771ecb854901bfd016d1db51; index tree 881e0c48c7d557c46221beb3b2410a157982f861, staged empty, active_run NONE. Origin github.com/romajka/kidsmap. Dirty WORKTREE source1025, включая прежние одобренные SOCIAL01–10, сохранён. HEAD и WORKTREE различаются; production UNKNOWN/NOTRUN.

## 3. Причина и impact
base.html:135 уже содержит main. typed_reviews.html:7 и account_notifications.html:12 создают вложенный main. Baseline свежо подтверждён во всех90cells; accessibility role main также2 в5дополнительных baseline pages. Точное введение UNKNOWN (имеется и в transferHEAD). Реальные screen readers не запускались; заявляется только DOM/landmark семантика.
Простая main→div теряет global rule site.css:1953. Scope расширен с предполагавшихся двух шаблонов до3файлов: добавить общий km-page-content в двух div и alias в существующий main rule с неизменными декларациями. Новый selector в текущем app отсутствует. Account profile более позднее правило сохраняет flex. JS living_map_background.js:139 зависит от main, но context_processors.py:23 allowlist не включает typed_reviews/account_notifications; native90pairs подтвердили отсутствие его script. Routes/base/controllers/services/PO/DB contracts сохраняются.

## 4. Свежая проверка и кандидат
90пар = (place/activity/specialist/event reviews + inbox) × RU/AZ/EN ×360/390/768/1024/1280/1440, fictional author.180навигаций: baseline main2/nested1 → candidate main1/nested0, 900/900checksPASS. Геометрия до100узлов на странице с tolerance≤1CSSpx, computed styles корня, controls/headings, Tab/Shift+Tab, отсутствие горизонтального overflow и livingmap script совпали.30nativePNG на390px; RU inbox baseline/candidate визуально просмотрены. Это сравнительная проверка source1025 и scratch overlay, не GREEN применённого app.
Ещё10 RU390 navigations: visible main roles2→1,0consoleErrors/pageerrors/HTTPerrors/requestfailed/externalblocked. В основной90-cell matrix console/requestfailed НЕ собирались; pageerrors/HTTPerrors/blocked0. Helper login использует только fictional author с email@example.invalid и settings.TESTING, SIMULATED; реальный password login в этом плане не проверялся. Owned QA sessions созданы; application POST/business writes в этом плане не запускались.

## 5. Точный план
См. IMPLEMENTATION_PLAN.md, proposed.diff, candidate-manifest.json, candidate/. Ровно2templates+site.css; app changes0. SHA candidates и diff зафиксированы. Будущий acceptance включает все4kind/guest-author-moderator/3locale/6widths, inbox и целевые настоящие409/403/guestredirect проверки. Backend tests для зеркалирования тегов не добавляются, прежний полный169-method корпус не повторяется без причины.

## 6. Инструменты и изоляция
Fresh3MO nativecompiler и manifestverify до django.setup; soleLOCALE_PATHS собственный. Новый m09s11-plan-r1-app с readonlyroot/repo, собственнымRWscratch/cache/media/private-media, DJANGO_TESTING1, cleared environment, internal ownedPG m09full-r1-pg/m09full_r1 без publishedport, ownedvolume подтверждён свежим inspect. Только loopback33410/33411 proxies; settings без productioncredentials/externalanalytics. Baseline и candidate template/static origins доказаны info.json/candidate-info.json. Новый QA root .tmp/social11-pc-plan-r1; прежние runtimes не использовались для этой проверки.
Codebase Memory C-kidsmap: graph-first symbol discovery, index ready, generation в initial coverage2026-10-16T18:56:53Z; template partial/metadata_changed и CSS/JS incomplete/unavailable coverage. Это research hints; source/rg и native proof использованы для фактических выводов, graph completeness не заявляется.

## 7. Команды, ошибки и evidence
COMMANDS.md содержит exact commands/results. Первая compare попытка exit1: require is not defined в CLI sandbox до навигаций; сохранена compare-first-error-cli.txt. Исправлен только QA harness: JSON возвращается через supported run-code return, разбирается отдельным Python. Повтор сравнения и parser exit0,900checks без изменения assertions/app. Ошибочный read несуществующего старого prepare.py — discovery only, не app/test failure. Никаких assertion changes ради green. Source/Git/preservation fresh verification — verification.json; native/browser scripts и CLI retained в evidence/.

## 8. Сохранность
1025source, sharedMO, .cbmignore,17priorpackages byte-identical; refs/index/staged/activeNONE сохранены. Guide append-only с проверенным oldprefix. Entry контейнеров 54, сейчас 55, идентичности сохранены, added только собственный app. Фактические state deltas: []. Причина любых внешних изменений UNKNOWN; agent stop/restart entrycontainers не выполнял. Нет reset/clean/stash/checkout-switch/commit/push/deploy/production/старыхPNGdownload.

## 9. Ограничения и handoff
Current app остаётся с nested main; SOCIAL11/module09 OPEN. Применение3-file diff ожидает решения пользователя, затем выполнить весь согласованный scope без повторного approval. Новый POST409/403 subset, physical device, real screenreader, cross-browser, full backend/global suite/externalservice/production NOTRUN. Previous ACCEPT09 full169 evidence относится к своему1024snapshot. Модуль10 не начат. Следующий шаг — approval точного IMPLEMENTATION_PLAN, затем отдельный fix package и scoped closure с проверками.
