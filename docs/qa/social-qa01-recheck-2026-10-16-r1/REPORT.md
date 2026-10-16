# SOCIAL-QA-01 — CONFIRMED OPEN / PLAN COMPLETE

2026-10-16, Asia/Baku. Исполнитель `/root`: kidsmap-orchestrator; проверки frontend-reviewer, django-reviewer и browser-qa выполнены последовательно одним исполнителем по действующим definitions, независимая делегация не заявляется. **PLAN ONLY**, application changes0; candidate diff не применён. Реализация ожидает одобрения [конкретного плана на два файла](IMPLEMENTATION_PLAN.md).

## 1. Состояние области

Фактический checkout `/home/ramin/kidsmap`, branch `task33-progress`, HEAD `e4e05cc213b34e2d771ecb854901bfd016d1db51`, dirty WORKTREE, `active_run: NONE`. [Входной snapshot](entry.json), [итоговый gate](verification.json). Checkout не переключался. Записанный deployed code `cfef63e3…` и Git release branch из [module08 release](../module08-release-2026-10-16-r1/REPORT.md) — отдельные снимки; production в этом запуске не проверялся. LOCAL module01–08 принятие сохранено в записанных границах, не повторялось.

Новый собственный PostgreSQL17.10 `social-qa01-recheck-2026-10-16-r1-pg`, ID `c838b7136b27…`, loopback50819, database/role `social01_r1`. HTTP `127.0.0.1:46131`, PID при старте350020, после interruption356757. Python3.12.3/Django6.0.2, Chromium153.0.8010.36. Проверены175applied migration rows. Fictional author/moderator/outsider и четыре target созданы первоначальным seed; отзывы и решения создавались native UI, ORM не подменял проверяемые переходы.

`DJANGO_TESTING=1`; inherited credentials очищены до импорта settings; checkout .env/manage.py не загружались. Собственные LocMem cache, media/private-media/staticfiles, file-based local email; внешние ключи пусты. Socket guard разрешает только собственный PostgreSQL; новый browser context блокирует внешние запросы. Два blocked Google Fonts запроса и соответствующие console errors — ожидаемая offline граница, не app failure. Первичный CLI bootstrap открыл login до установки context route blocker; внешний integration PASS не заявляется. Воспроизведение целиком проведено в новых contexts с blocker.

Текущие RU/AZ/EN PO собраны штатным `scripts/build_isolated_locales.py` в собственный `.tmp/social-qa01-recheck-2026-10-16-r1/locales`. Проверка manifest выполнена до django.setup; единственный LOCALE_PATHS указывает на собственный locale_root. Shared MO сохранены. [Locale manifest](locale-manifest.json), [runtime/isolation](runtime-info.json), [финальные source/PID/template/MO данные](runtime-source-final.json). Startup hashes967source/static/template/PO и текущий disk совпадают; template origin — действительный `src/catalog/templates/catalog/typed_reviews.html`, loaded hash отдельно сравнивается с disk.

## 2. Что работает

Native author login→rating4→text→submit→reload и staff approve→author reload выполнены для Place/Specialist/Activity/Event, RU390. Во всех четырёх случаях candidate сохранила4, после approval published head/current сохранил4, public count1/average4. Text сохранился; literal script/HTML показан текстом, JS не исполнился. Пустая форма остаётся required с пустым rating. **20controlPASS**, [результат и readonly state checkpoints](reproduce-corrected.js.result.json).

## 3. Подтверждённая проблема

**SOCIAL-QA-01, P2 OPEN**, причина **REVIEW-RATING-READBACK**, confidence HIGH, LOCAL current WORKTREE. Восемь failed observations одной причины: четыре типа × pending/approved.

Шаги: автор выбирает4, вводит вымышленный текст и отправляет; после redirect/reload редактор показывает «—». Затем модератор одобряет через встроенные формы, автор перезагружает — снова «—». В обоих состояниях БД сохраняет4. Ожидание — выбранное4 без повторного ручного ввода. POST из такого редактора требует заново выбрать оценку.

Причина подтверждена current source и native evidence: `src/catalog/templates/catalog/typed_reviews.html:24` содержит пять option без selected; `src/catalog/controllers/typed_reviews.py:87` уже передаёт author-owned head с candidate/current. Существующий текст использует candidate→head, CAS token candidate→current. `src/catalog/services/review_versions.py:moderate_candidate` проецирует current rating в head и очищает candidate; первый rejected сохраняет rating head. Поэтому достаточно отображения в общем шаблоне. Представление и данные не требуют новой бизнес-логики.

[8nativePNG сSHA/dimensions](png-manifest.json), например [pending Place](screenshots/pending-place-ru-390.png) и [approved Place](screenshots/approved-place-ru-390.png). Реальная картинка approved Place просмотрена исполнителем. Другие семь PNG проверены на валидность, размеры и hash; их DOM/value/readback доказательства записаны автоматизацией.

## 4. Технические границы

Предложены ровно два application/test файла: общий typed_reviews.html и новый `src/catalog/testcases/test_social_qa01_rating_readback.py`. [Готовый template diff](proposed.diff), [готовый новый regression исходник](candidate/test_social_qa01_rating_readback.py); оба application изменения НЕ применены. Controller/services/ACL/CAS/cooldown/schema/JS/CSS/PO остаются прежними. New tests содержат7methods, пока **NOT RUN**; RED→GREEN запланирован после scope approval.

Codebase Memory `home-ramin-kidsmap` root совпал; index ready/full, generation2026-10-16T11:00:29Z. Target controller/template coverage metadata_match/no_recorded_issue с best-effort caveat; guessed services/reviews.py missing, вместо него проверен фактический импорт review_versions.py напрямую. Graph не использован как доказательство полноты или отсутствия кода. Graph caches в artifacts не копировались.

## 5. Риски и сохранность

Изолированное воспроизведение классифицируется как **current source failure / pre-existing baseline at entry**; дата появления и regression относительно clean HEAD/production UNKNOWN. Факт постоянной потери текста/оценки не установлен.

Входные34916files hashed:34915 без изменений; единственное разрешённое изменение — добавление текущего статуса в guide. Точные changed/missing/unexpected и74foreigncontainer identity/ports/state — [preservation gate](verification.json). Shared MO входят в сравнение. HEAD/branch/active_run проверяются повторно. Исторические QA reports сохранены. Index byte baseline отдельно не снимался; index-mutating commands не выполнялись.

Явное прерывание пользователем завершило пять входных QA HTTP и собственный HTTP. **Foreign HTTP continuity NOT VERIFIED**, [зафиксированное interruption](interruption.json). Чужие процессы не перезапускались; восстановлен только свой HTTP после проверки исходных967hashes. PostgreSQL собственного стенда сохранился. Непрерывность чужих процессов не объявляется PASS; сохранность файлов/контейнеров — отдельный проверяемый результат.

## 6. Legacy/dead code

Удаление/рефакторинг не предлагаются. Head fallback нужен и для отсутствующей current после первого отказа. Candidate precedence нужна, чтобы pending edit не выбирал прежнюю публичную оценку. Соседние SOCIAL02–09 этим планом не исправляются.

## 7. Проверки, команды и ограничения

Фактически выполнено: **28browser observations =20PASS/8FAIL,8PNG**, четыре типа, pending/approved, RU390. Это targeted reproduction одного бага, не приёмка модуля. Unexpected local HTTP/pageerror/console ошибок в corrected native flow0; expected blocked external diagnostics4. Readback выполняется в READ ONLY transactions с5s statement/2s lock timeout. [Итоговый readonly state](state-final.json).

Команды и exits — [commands.jsonl](commands.jsonl); создание собственного контейнера — [create-container.json](create-container.json). Основные invocations:

```bash
python3 docs/qa/social-qa01-recheck-2026-10-16-r1/capture.py
python3 docs/qa/social-qa01-recheck-2026-10-16-r1/start.py
# start.py: build isolated locales0, verify0, runtime.py prepare0, runtime-info0; own serve long-running
python3 docs/qa/social-qa01-recheck-2026-10-16-r1/drive.py reproduce-corrected.js
# CLI exit0; semantic result complete=true,20PASS/8FAIL

git apply --check docs/qa/social-qa01-recheck-2026-10-16-r1/proposed.diff
# exit0, только feasibility check, diff не применён
.venv/bin/python scripts/build_isolated_locales.py verify --manifest .tmp/social-qa01-recheck-2026-10-16-r1/locales/manifest.json
# exit0
.venv/bin/python docs/qa/social-qa01-recheck-2026-10-16-r1/verify.py
# preservation/evidence gate; result в verification.json
```

Первый reproduce.js завершился QA selector strict-mode error до проверяемых переходов: CLI exit0/complete=false/observations0. Он сохранён отдельно, не считается app failure или PASS; [исправление harness](harness-notes.md). Повторялись только невыполненные действия. Application assertions не менялись.

**NOT RUN:** application patch/GREEN; новые7Django methods и shared subset; rejected/pending-edit/repeated-submit lifecycle; RU/AZ/EN×6width acceptance; весь ACCEPT-09; другие SOCIAL findings; global corpus; production, physical devices, screenreader, cross-browser и внешние integrations. Offline fonts/transport блокировка — явно SIMULATED/offline, реальная доставка email/SDK не заявляется.

## 8. Следующий шаг

Одобрить [implementation plan](IMPLEMENTATION_PLAN.md) для **SOCIAL-QA-01 и ровно двух application/test файлов**. После одобрения выполнить весь scope, RED→patch→targeted GREEN→native matrix→новый fix-report. Дополнительное application расширение согласовать отдельно. Затем отдельный PLAN SOCIAL02; полный ACCEPT09 один раз после всех его задач. Module10 автоматически не начинать.

## 9. Приоритеты

SOCIAL-QA-01 P2 подтверждён и остаётся OPEN; P0/P1 в узком scope не установлены. SOCIAL02–09 — историческая очередь для свежих PLAN, нынешний статус не проверялся. Модуль09 целиком не закрыт.
