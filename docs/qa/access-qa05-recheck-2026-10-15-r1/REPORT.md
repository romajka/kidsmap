# ACCESS-QA-05 — свежий recheck и план, 2026-10-15

Результат: **ACCESS-QA-05 подтверждён, OPEN. PLAN готов, исправление NOT RUN — ожидается отдельное одобрение.**
[Конкретный план](IMPLEMENTATION_PLAN.md), [точный предполагаемый diff](proposed.diff), [финальная сверка](verification.json).

## Snapshot и границы

Фактический checkout `/home/ramin/kidsmap`; HEAD `e4e05cc213b34e2d771ecb854901bfd016d1db51`, branch `task33-progress`, dirty WORKTREE; `active_run: NONE`. [Entry](entry.json) фиксирует28616 baseline-файлов,60чужих контейнеров и3known QA HTTP identities. Исторические module07 FAIL использованы как указатель, не как текущий результат. ACCESS01/02/04 уже scoped LOCAL PASS; ACCESS03=ORG02 принят в свежем module02-full-2026-10-13-r2. Они здесь не исправлялись и их полные наборы не повторялись.

Роли kidsmap-orchestrator/frontend-reviewer/browser-qa проверены последовательно одним исполнителем; независимое исполнение ролей не заявляется. Применены существующие debugging/planning/accessibility/UI/browser/verification навыки. Graph-first project `home-ramin-kidsmap` указывает фактический root, generation2026-10-15T08:03:54Z; source .py metadata_match, PO partial. Критические четыре записи и динамические Django связи проверены непосредственно в исходниках. Graph cache в артефакты не копировался.

## Свежая причина и доказательства

`src/catalog/views.py:1982–1983` переводит два точных русских msgid. В AZ/EN оба fuzzy и имеют чужой смысл: «код отправлен» / «ввести код». Свежий GNU msgfmt исключает их, поэтому runtime gettext отдаёт русский оригинал. [Четыре исходных блока](exact-entries.json), [runtime source/gettext/фактически открытые MO](runtime-source-with-loaded-MO.json), [exact oracle RED](locale-regression-red.json).

Настоящий Chromium149.0.7827.55:18 RU/AZ/EN×360/390/768/1024/1280/1440 cells, по2состояния ошибки в каждом. **252observations:228PASS/24ожидаемых языковыхFAIL**. RU84/84PASS; AZ72PASS/12FAIL; EN72PASS/12FAIL. [Объединённые observations](observations.json); отдельные `<lang>.js.result.json` и `.status.json` сохраняют native exit0, errornull, по6завершённых cells. Exit0 не истолкован как отсутствие дефекта.

Пользовательский путь каждого вымышленного аккаунта: native login → request → confirmation → неверный шестизначный код при точной фразе → неточная фраза → Tab на кнопку. Native POST обеих ошибок HTTP400; корректное поле aria-invalid/aria-describedby, введённые значения сохранены. Account remains active, запрос CONFIRMATION_SENT,4из5попыток осталось: wrong phrase проверяется раньше code и вторую попытку не тратит. Все18страниц без горизонтального overflow. Успешное подтверждение/отмена до одобрения будущего ремонта не запускались.

Console/network:36ожидаемых HTTP400 на confirm,18заблокированных внешних запросов и соответствующие console resource errors. Pageerrors/необъяснённые local network failures/другие HTTPerrors отсутствуют. Это не проверка работоспособности внешних сервисов.

12native PNG = RU/AZ/EN×390/1440×2ошибки: [manifest](png-manifest.json). Выборочно открыты оригиналы AZ390wrong-phrase и RU1440wrong-code; [границы визуального просмотра](visual-review.json). Все12кадров вручную не пересматривались. На PNG только заведомо неверный код и общая exact phrase, без рабочего mail code, signed token или адресной строки browser. CLI raw transcript хранится только в собственном ignored scratch, а не в отчётах.

## Изолированная среда и QA-harness уточнение

Новый уникальный `.tmp/access-qa05-recheck-2026-10-15-r1`, mode700; generatedcredentials600. DJANGO_TESTING=1 до django.setup; environment очищен, checkout .env и production credentials не загружались. Собственные PostgreSQL17-alpine/container/volume `access-qa05-recheck-2026-10-15-r1-pg`, DB/user `access_qa05_recheck_r1`, loopbackPG36977/HTTP38969; own LocMem cache/media/private-media/filebased email. Серверные внешние соединения запрещены, кроме собственного PG; browser внешние обращения блокированы. Никакие business transitions не seedились: fixture только18вымышленных пользователей с verified email.

Существующий TEST_POLICY извлечён из тестового источника без импорта моделей до setup; только own settings используют versionSIMULATED-QA05/approved_bySIMULATED LOCAL QA ONLY. Default inactive policy приложения не менялась. Это SIMULATED policy, не согласование реального хранения/production readiness.

RU/AZ/EN PO собраны в собственные MO через `scripts/build_isolated_locales.py`; build0/verify0. Единственный LOCALE_PATHS из manifest подключён до django.setup. Own process startup pins17app/source paths, views/service imports/templateSHA; проверены фактические PID/argv/cwd, fresh manifest и actual opened own MO после инструментирования QA runtime. Общие MO не перезаписывались.

Уточнение harness сохранено: [mail-helper-initial.txt](mail-helper-initial.txt). Первоначальный reader искал шестизначное число в MIME-фрагменте, а не только decoded body; такая проверка не доказывала recipient/code привязку. В собственном QA helper заменён только parser: отдельное письмо, точный To, decoded payload. Дополнительный **READ ONLY mailproof** подтвердил18из18писем по получателю и password-hash кода соответствующего запроса; [readback](readback-final.json), exit0. Предыдущие native отказ/полевые ошибки/attempts4 не зависят от правильного mail-кода; он в этих POST не использовался. Успех request→верный mail code→confirm здесь не заявляется.

Перезапускался только собственный PID188576 ради instrumentation и parser. Первичная10sготовность нового процесса оказалась короткой: restart_owned.py exit1 «Own source not ready». Повторная read-only HTTP source-проверка подтвердила успешный запуск собственного PID195388 с теми же17исходниками, sole locales и22openedMO, включая3owncatalogs. Это QA readiness timeout, не app FAIL и не причина менять assertions/production. Чужие процессы не перезапускались. Текущий PID проверен повторно финальным gate; старыеPID не считаются актуальными.

## Команды и классификация

[commands.jsonl](commands.jsonl): exact build/verify/docker/prepare/native commands/exits/timings. Все запускались из фактического root.

- `.venv/bin/python .../capture.py`:0; entry baseline/собственная конфигурация.
- `.venv/bin/python .../launch.py`:0; build0/verify0/docker0/migrate+fixture0. Источники до patch; application patch отсутствует.
- `playwright_cli.sh -s=accessqa05recheckr1green open about:blank --config=<own ignored browser.json>`:0; новая сессия, не старый browser.
- `.venv/bin/python .../browser_run.py ru.js`, `az.js`, `en.js`:0/0/0; semantic errornull, по84observations/6cells.
- `.venv/bin/python .../locale_regression.py`:1,8/8expectedRED по точным ожидаемым AZ/EN строкам (runtime+MO). Oracle не ослаблялся.
- `.venv/bin/python .../restart_owned.py`:1 — описанный readiness timeout; отдельная HTTP source recovery0.
- `.venv/bin/python .../runtime.py mailproof`:0,18recipient/codehash PASS, transaction READ ONLY +10s timeout.
- `.venv/bin/python .../verify.py`: результат/exits в [verification.json](verification.json); baseline inverse guide hash, исходники/локали/stand/process/PNG/leaks/syntax/diff проверяются отдельно от expected language FAIL.

Классификация: source defect ACCESS05; locale build корректен; isolated environment SIMULATED; mail parser/readiness — QA-harness замечания с дополнительной проверкой, не новые application ID. Четыре точные PO-записи — единственный предлагаемый app diff.

## Сохранность и NOT RUN

Финальный gate сравнивает все entry файлы; допускает лишь новую строку current05PLAN в guide с обратным хешем. Собственные артефакты находятся только в этом новом run/ignoredscratch. Entry HEAD/branch/active_run, sharedMO, все чужие файлы/контейнеры/knownHTTP сравниваются с текущим состоянием. Это ограниченная локальная сверка, не доказательство доступности произвольных host процессов или production.

NOT RUN: application patch/GREEN; успешные confirm/cancel/reset после отмены; backend suites; full ACCEPT07/global; cross-browser/real screen reader; SMTP/OAuth/прочие внешние сервисы; production/commit/push/deploy/module08. ACCESS05 не закрыт. [План](IMPLEMENTATION_PLAN.md) и [handoff](next-prompt.txt) ждут отдельного scope approval.
