# SOCIAL-QA-02 — CLOSED LOCAL

2026-10-16, Asia/Baku. Выполнен одобренный пользователем [конкретный план](../social-qa02-recheck-2026-10-16-r1/IMPLEMENTATION_PLAN.md); [approval](approval.json). Исполнитель /root, kidsmap-orchestrator; роли django-reviewer, frontend-reviewer, browser-qa и security-reviewer выполнены последовательно одним исполнителем, независимая делегация не заявляется.

**Автор видит последнее отклонённое решение, причину, текст и оценку.** После исправления и новой отправки устаревшая причина скрывается. Закрыт только SOCIAL-QA-02, полный module09 ACCEPT ещё NOT RUN.

## Snapshot и изоляция

`/home/ramin/kidsmap`, `task33-progress`, HEAD `e4e05cc213b34e2d771ecb854901bfd016d1db51` + dirty WORKTREE, active_run NONE. Checkout не переключался. Deployed cfef63e3 и release-ветка — другие снимки; production не проверялся.

Собственный PostgreSQL17.10: контейнер `social-qa02-fix-2026-10-16-r1-pg`, loopback34223, database/role social02_fix_r1. HTTP127.0.0.1:42609, текущий PID516441; Python3.12.3, Django6.0.2, Chromium153.0.8010.36. DJANGO_TESTING=1, отдельные cache/media/private-media/staticfiles/email/cookies. Environment очищен до settings, checkout .env/manage.py и production credentials не загружались. Socket guard разрешает только собственный PG; браузер блокирует внешние запросы. Данные вымышленные:20аккаунтов/24targets, review переходы через UI.

Текущие RU/AZ/EN PO собраны штатным scripts/build_isolated_locales.py в собственный каталог; manifest проверен до django.setup, sole LOCALE_PATHS `.tmp/social-qa02-fix-2026-10-16-r1/locales/locale`. Общие MO сохранены. GREEN tests, HTTP startup и disk совпали по969source files, загруженный template также совпал.

[Entry](entry.json), [runtime/isolation](runtime-info.json), [locale manifest](locale-manifest.json), [running source](runtime-source-final.json), [verification](verification.json).

## Причина и исправление

После reject candidate pointer очищается. При отказе edit head продолжает представлять approved current; причина и отклонённый текст остаются в revision history. Шаблон их не читал. [Свежий recheck](../social-qa02-recheck-2026-10-16-r1/REPORT.md) подтвердил16rendered states:40controlPASS/24FAIL, а8readonly records подтвердили сохранённую причину.

Controller теперь выбирает только последнюю submitted revision собственного author-owned head, если candidate отсутствует и эта revision rejected. Template показывает отдельный локализованный private aside: статус, optional reason, rating и текст с escaping. Candidate/current в редакторе сохраняет контракт SOCIAL01: после отказа edit редактор содержит approved current, отклонённая версия доступна рядом. Новая pending/approved версия скрывает старый отказ.

Ровно3application/test файла: `src/catalog/controllers/typed_reviews.py`, `src/catalog/templates/catalog/typed_reviews.html`, новый `src/catalog/testcases/test_social_qa02_rejection_feedback.py`. [Diff](application.diff), [побайтное соответствие approved candidates](approved-source-match.json). Services, moderation/ACL/CAS/cooldown/schema/PO/JS/CSS и существующие assertions не менялись.

## RED → GREEN

До patch выполнены только4новых regression methods:4failing methods/26assertion failures/0errors, exit1. Все падения по отсутствию author rejection feedback. После patch те же4methods и4затронутых shared methods: **8/8PASS**, exit0. Full прежний SOCIAL01 набор и полный module09 не повторялись.

Проверено: первый reject; rejected edit сохраняет public current/count; own/outsider/guest privacy; новая pending/approved скрывает старое решение; reason/text script HTML остаётся literal. Shared subset: первый отказ/отказ edit SOCIAL01, pending-edit public projection и one rating, nonstaff/stale moderation. Unit-only cooldown0 — SIMULATED; native flow использует настоящий120s.

[RED](regression-red.txt), [GREEN](regression-green.txt), [counts](test-results.json), [точные commands/exits](commands.jsonl). Полный HTML response из диагностических assertion logs исключён из repository artifact; исходная диагностика оставлена только в собственном ignored scratch0600. Assertions не ослаблены.

## Настоящий браузер

**1420PASS/0FAIL accepted observations**, 144rendered state cells, 198native PNG. Это количество проверок, не количество независимых bugs.

Матрица:4типа ×2состояния (first rejected и rejected edit) ×RU/AZ/EN ×360/390/768/1024/1280/1440. На каждой cell проверены reason/text/rating, сохранность редактора SOCIAL01, literal script/HTML, readonly candidate/current/public4 count1, Tab/ShiftTab и видимый focus, отсутствие горизонтального overflow, contrast heading≥4.5. Пустая причина — Specialist, длинная неразрывная — Event, literal script — Activity.

Native key transitions отдельно RU/AZ/EN390/1440: create4→approve; first3→reject; approved4→edit2→reject; автор читает отклонённый текст, исправляет и отправляет после реального cooldown120s; новый pending скрывает old reason, approval меняет public contribution на2/count1; первый rejected3 повторно отправляется без повторного выбора оценки. Состояния не подменялись через ORM/виртуальные часы.

Guest/outsider/другой автор проверены в RU/AZ/EN390/1440: приватные reason/text автораA не видны, public current остаётся видимой, другой автор видит только собственный feedback. Финальный readonly readback: по каждому case/type author approved current2/no candidate; второй автор pending3/no current; rejected history сохранена; average2/count1. READ ONLY transactions с5s statement/2s lock timeouts.

[Matrix JSON](matrix.json), [CSV](matrix.csv), [PNG manifest](png-manifest.json), [representative visual review](manual-png-review.json), [final DB state](state-final.json). Часть автоматических кадров фиксирует заголовок под sticky header; четыре дополнительных native scroll проверки подтвердили доступность заголовка, сохранены отдельные visual PNG. Исходные кадры не заменялись. Все PNG — native captures; вручную просмотрена representative selection, остальные проверены DOM/geometry/assertions и PNG integrity.

| Фаза | Accepted assertions |
|---|---:|
| correct | 96 |
| edit | 120 |
| initial | 100 |
| initial-resume | 20 |
| matrix-edit | 432 |
| matrix-first | 432 |
| privacy | 216 |
| visual | 4 |

В завершённых browser phases неожиданных local HTTP/pageerror/console ошибок0. Внешние fonts блокировались намеренно; их failure/console diagnostics сохранены и не считаются реальной проверкой внешней интеграции. Старый shared view-transition event из SOCIAL01 остаётся отдельной исторической границей, здесь не исправлялся. SOCIAL03 raw409 UX не входит в эту приёмку.

## Сохранность и инцидент окружения

Проверены35644входных files; изменились только controller/template и статус guide, новый regression разрешён отдельно. Missing/unexpected changes0, index/sharedMO/HEAD/branch/active_run MATCH. Все76входных контейнеров сохранили identity/name/port/state. Чужие процессы не останавливались и не перезапускались командами этого run.

После смены модели/tool session обнаружено исчезновение собственного HTTP и обоих входных QA HTTP. Причинная связь не установлена; их непрерывность **NOT VERIFIED**, это не PASS сохранности процессов. Более ранние5HTTP также остаются исторически NOT VERIFIED. Восстановлен только собственный HTTP после сверки source969; БД не пересоздавалась. [Инцидент](process-interruption.json), [source resumed](runtime-source-resumed.json), [case4 readback](interrupted-case4-state.json).

Четыре завершённые initial phases не повторялись. Незавершённый initial4-en не имел final semantic result; два partial PNG сохранены. Resume сначала прочитал фактическое состояние: не повторял уже сделанные POST/решения, выполнил недостающие переходы и заново проверил этот незавершённый case. Неполученные assertions исходной попытки не выдуманы. Позже batch runner завершился exit143 после сохранённого complete/PASS correct-case2, перед стартом case3. HTTP/DB продолжали работать; выполнены только ещё не начатые cases3–5. [Batch evidence](batch-exit143.json).

## NOT RUN / следующий шаг

Полный ACCEPT-09 запланирован один раз после SOCIAL01–09; общий project corpus отдельно. Другие SOCIAL findings, physical devices/real screenreader/cross-browser, реальные SMTP/Google/SDK и production/commit/push/deploy — NOT RUN. Unit cooldown и offline external fonts явно SIMULATED. Следующий отдельный scope — PLAN SOCIAL-QA-03; новое исправление требует одобрения конкретного плана.
