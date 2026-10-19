# Module09: безопасная синхронизация и свежий PLAN SOCIAL-QA-03

2026-10-16, Asia/Baku. **Синхронизация завершена; SOCIAL-QA-03 CONFIRMED OPEN / P2, обновлённый план готов к одобрению. Реализация не выполнялась.** [План](IMPLEMENTATION_PLAN.md), [verification](verification.json), [неприменённый diff](proposed.diff).

Исполнитель `/root`, один lead `django-reviewer` под контрактом `kidsmap-orchestrator`; frontend-reviewer, browser-qa и security-reviewer выполнены последовательно тем же исполнителем по прочитанным каноническим definitions. Независимых запусков специалистов не было. Режим — bounded recheck / PLAN; разрешены Git-синхронизация, изолированная проверка и документы.

## Git и сохранность

Найден checkout `C:\kidsmap`, origin `https://github.com/romajka/kidsmap.git`. На входе `task33-progress`, HEAD `e4e05cc213b34e2d771ecb854901bfd016d1db51`, WORKTREE/index clean. `ls-remote` и полученный remote ref совпали с контрольным SHA. До переключения проверены worktrees и повторно проверена чистота; создана tracking-ветка через `checkout --no-overwrite-ignore`. Игнорируемые файлы не перезаписывались принудительно.

Итоговая ветка `codex/module09-transfer-2026-10-16-r1`, HEAD **852938d96764ae315b92859e3651e5ea62054a36**, divergence с origin **0/0**. Исходный ref `task33-progress` остался на прежнем SHA. Прочитаны Git log, RESUME_PROMPT, transfer REPORT/verification и относящиеся к SOCIAL03 материалы. Полный архив отсутствующих старых PNG не догружался; обычный checkout получил только опубликованные Git-файлы. Старые manifests не объявлены полным архивом.

После синхронизации зафиксирован [entry snapshot](source-entry.json): 1019 tracked source/config файлов выбранных расширений, shared MO, index tree, HEAD, branch и `active_run: NONE`. Это явно определённая выборка, не повторение исторического manifest1017/969. [Final snapshot](source-final.json) подтверждает совпадение этой выборки. Новых application файлов нет; изменены только этот QA-пакет и одна новая статусная запись guide. История прежних отчётов сохранена.

Reset/clean/stash, commit/push/deploy, production, назначение active_run и запуск исторических remote/prepare/activate scripts не выполнялись. Внешние чужие процессы не останавливались; остановлен один собственный HTTP для исправления QA URLconf. Все 24 входных Docker-контейнера были остановлены до работы; их IDs/names/состояния сохранены. Непрерывность всех процессов ПК не проверялась.

## Текущий source и изоляция

Codebase Memory `C-kidsmap` доступен; generation `2026-10-11T20:44:10Z`, full, metadata truncated. Coverage трёх нужных путей сообщает `metadata_changed / coverage_unavailable`. Graph search/trace использованы как навигация; trace ограничен 15/52 callees и содержит неоднозначные связи. Причина, маршруты и динамические ORM consumers сверены по фактическому source, отрицательных выводов из графа нет; graph caches в Git не добавлялись.

Собственный run `.tmp/module09-pc-resume-2026-10-16-r1`: Docker internal network `m09pc-r1-net`, PostgreSQL `m09pc-r1-pg`, приложение `m09pc-r1-app`; DB/role `m09pc_r1`, отдельная test DB. PostgreSQL наружу не опубликован. Вход в HTTP — собственный loopback proxy `127.0.0.1:33261`, потому что internal bridge не публикует порт приложения. Python **3.12.15**, Django **6.0.2**, PostgreSQL **17.11**, Chromium **155.0.8059.12**, Node24 для CLI; это версии нового стенда.

Окружение очищено до импорта settings, `DJANGO_TESTING=1`; checkout .env/manage.py и production credentials не загружались. Source смонтирован read-only, scratch — отдельно writable; source1019 проверяется перед каждым django.setup. Изолированы LocMem cache, media/private-media/staticfiles, locmem email, сессии и вымышленные accounts/targets. External app egress блокирует internal network; browser allowlist разрешает только собственный HTTP origin. External font/integration success не заявляется. [Runtime](runtime-info.json).

Текущие RU/AZ/EN PO собраны штатным `scripts/build_isolated_locales.py`, GNU msgfmt native в WSL. Три каталога прошли build и verify, manifest проверяется до django.setup, единственный LOCALE_PATHS — собственный `locales/locale`. Shared MO не менялись. [Manifest](locale-manifest.json).

## Подтверждённая причина и влияние

`src/catalog/controllers/typed_reviews.py:67` (`target_reviews`, except ReviewConflict) возвращает отдельный `HttpResponse(..., status=409)` до общего render. `services/review_versions.py:169` сохраняет CAS; запись revision находится после проверки. `typed_reviews.html:31` содержит обычную форму, но эта ветвь до неё не доходит.

В свежем браузере: вкладка B открывает current4, вводит оценку2/`Unsaved draft B`; вкладка A настоящим POST отправляет candidate5/`Latest private candidate A`; B отправляет свой stale token клавишей Enter и получает настоящий409. Read-only readbacks используют отдельную transaction READ ONLY, statement_timeout5s/lock_timeout2s.

[Матрица](matrix.json): Specialist × RU/AZ/EN × 360/390/768/1024/1280/1440 = **18 cells**, 18 actual409, **72 control PASS / 36 recovery FAIL** (6 именованных checks на cell). Все no-write comparisons совпали: candidateA5/current4/history/public average4/count1 сохранены, B в БД отсутствует. В каждом409 отсутствуют editor/B/navigation. [18 новых native PNG](png-manifest.json); RU390 и EN1440 дополнительно просмотрены визуально. Постоянная потеря данных не заявляется; fresh Back recovery NOT RUN.

В каждом конфликте зарегистрирован `InvalidStateError: Transition was aborted because of invalid state. ViewTransition opt-in disabled`: **18 pageerrors**, плюс ожидаемые browser console409. Сигнатура совпадает с историческим SOCIAL01/03; её introduction UNKNOWN. Она не скрыта и не исправлена, чистая консоль не заявляется. После SSR409 требуется отдельная целевая проверка; новый JS/CSS scope автоматически не разрешён.

## Targeted RED и affected subset

Шесть уже предложенных методов запущены **из historical candidate directory как внешний test module**; в `src/catalog/testcases` ничего не копировалось. Один валидный запуск текущего source: **10 unique methods, 3 failing methods / 14 assertion failures, 7 passing methods, 0 errors**; exit1 — ожидаемый RED, не продуктовый PASS. Внутри SOCIAL03: 3 failing recovery methods и 3 passing guard methods. Первый recovery method проверил все4типа × RU/AZ/EN и дал12 ожидаемых FAIL; два других остановились на первом failing Place, их оставшиеся branch checks до GREEN не выполнены.

Четыре affected methods прошли: SOCIAL01 empty/foreign rating; SOCIAL02 author-only rejected feedback/current projection; PostgreSQL concurrent CAS/two approvals; persisted Place cooldown. Это обоснованный subset общего POST/render/service пути; полный прежний корпус01–02 не повторялся. [Точный запуск](commands.md), [лог](targeted-red-shared-v2.log).

Сохранены первоначальные ошибки QA: seed неверно распаковал возвращаемый tuple; WSL остановился между короткими командами и завершил только собственные новые контейнеры, tmpfs DB пришлось заново создать миграциями; included i18n URLconf вызвал harness error. После исправления только scratch harness, удержания WSL собственным proxy и нового seed проверки выполнены на текущем source. Отдельно сохранены старый failed test run и логи попыток. Они не переклассифицированы в PASS. Node18 отказал до browser launch; отдельный Node24 устранил environment gate.

## Решение и следующий шаг

Старый diff проходит свежий `git apply --check --ignore-space-change` (exit0), **не применён**. Обновлённый [план](IMPLEMENTATION_PLAN.md) подтверждает прежнюю причину и ровно3 application файла. При409 сохранить validatedB в форме, показать author-owned latestA, выдать fresh CAS token для явного повторного POST и GET-ссылку загрузкиA с предупреждением о сбросеB. Сохранить409/CSRF/ACL/CAS/current-candidate/cooldown; без автоматических повторов.

Реализация/acceptance03, остальные3типа native409, full ACCEPT09/global corpus, SOCIAL04–09, physical devices, cross-browser, screenreader и external integrations **NOT RUN**. SOCIAL01–02 сохраняют историческую scoped LOCAL closure, текущий subset не является их полной повторной приёмкой. Deployed public SOCIAL01–02 и текущее production состояние UNKNOWN; production не посещался. Module09 OPEN; module10 не начинался.

Следующий шаг — одобрение **этого** трёхфайлового плана. До patch сверить текущий source/locale manifest с этим snapshot; при прежнем source повторять всю18cell RED-матрицу не требуется. Изменившаяся причина или дополнительный app файл требуют нового конкретного scope. После approval — approved patch, targeted GREEN/affected subset и native4types×18cells по плану. Полный ACCEPT09 — один раз после закрытия всех SOCIAL01–09.
