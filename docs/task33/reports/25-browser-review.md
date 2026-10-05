# Этап 25 — независимая проверка Specialist макетов

Исполнитель: `/root/stage25_browser`, canonical `browser-qa`, definition `.agents/agents/browser-qa/agent.md`; 2026-10-03. Bounded AUDIT: отдельный исполнитель проверил пакет автора `/root/stage25_design`. Авторизация родительского этапа25 разрешает сейчас самостоятельную design-часть и её проверку. Application integration требует принятия новых экранов пользователем. Статус **CREATED / REVIEW_PENDING**, весь этап25 не завершён.

Snapshot: `C:\kidsmap`, branch `task33-progress`, LOCAL HEAD `015d031d8eb17114bd860159dde805b38df3c13c`; dirty WORKTREE21–25 отличается от HEAD. Production не подключался. Область собственных изменений: `docs/task33/qa25/`, этот отчёт и [25-browser-results.json](25-browser-results.json). Код приложения, БД и production не изменялись.

## Evidence и source

Проверены восемь входов [пакета specialist-25-r1](../design/specialist/README.md): index, profile, person, organization, claim, documents, review, reconciliation. Использован реальный cached Chromium build1247 через Playwright CLI0.1.22, отдельная сессия `qa25`; локальный [allowlisted preview](../qa25/preview.py) на `127.0.0.1:8795`. Только синтетические данные, локальные logo/fonts/CSS; API, Django, DB и внешние assets не требуются. Запросов за пределы local origin не было, transport stubs не применялись.

Codebase Memory у этого исполнителя: `C-kidsmap`, root `C:/kidsmap`, ready, full generation `2026-10-03T14:52:17Z`, generation_matches=true, hash_records_complete=true. Проверка новых design/specialist и qa25 путей вернула `coverage_unavailable` / freshness `not_tracked`. Поэтому graph полноту этих новых файлов не доказывает; выполнены scoped source review и фактический browser render. Доступность инструментов родительского исполнителя может отличаться.

Полный последний матричный прогон выполнен на frozen prototype.js SHA256 `ae981f6024a573e854df303ea0c0ab741f2f1cec28e6a372c2c2cbb210e42151`. После него автор изменил только текст reconciliation/denied/review в shared prototype.js. На конечном SHA256 `63fb1de6a5ce7a72535d831b87d569dbbde24c4073613f08364da95a91db6f4a` независимо повторно проверены все восемь экранов AZ/RU/EN при390/1440, 30 denial-состояний, actual keyboard и ограничения публичных qualifications. Финальный captured source snapshot совпал с текущими **11/11 файлами**, mismatches0. Это два последовательных среза, а не утверждение, что старая матрица исполняла новые bytes.

## Выполненные команды и результаты

Команды из Windows PowerShell, рабочий каталог C:\kidsmap:

```text
wsl -d Ubuntu-24.04 -u root --exec /bin/bash /mnt/c/kidsmap/docs/task33/qa25/run-browser.sh first-20261003
wsl -d Ubuntu-24.04 -u root --exec /bin/bash /mnt/c/kidsmap/docs/task33/qa25/run-browser.sh final-20261003
wsl -d Ubuntu-24.04 -u root --exec /bin/bash /mnt/c/kidsmap/docs/task33/qa25/run-browser.sh pending-red-20261003 /mnt/c/kidsmap/docs/task33/qa25/pending-probe.js
wsl -d Ubuntu-24.04 -u root --exec /bin/bash /mnt/c/kidsmap/docs/task33/qa25/run-browser.sh final2-20261003
wsl -d Ubuntu-24.04 -u root --exec /bin/bash /mnt/c/kidsmap/docs/task33/qa25/run-browser.sh final-copy-20261003 /mnt/c/kidsmap/docs/task33/qa25/final-copy-keyboard.js
wsl -d Ubuntu-24.04 -u root --exec python3 /mnt/c/kidsmap/docs/task33/qa25/build-results.py /mnt/c/kidsmap/docs/task33/reports/25-browser-results.json
```

- first: exit0, 168/168 rendered cells,178/178 checks; предварительный render-only срез.
- final: exit1,168/168 cells,344/346 checks. Два RU→EN checks читали исходный html.lang=ru до deferred JS; исправлен harness ожиданием navigation `networkidle`. Application fix для этих двух не делался, assertions сохранены.
- pending-red: exit1,0/3 cells и0/3 checks. Реальный дефект макета: AZ/RU/EN public profile `state=pending` показывал certificate action. Исправлен автором; отрицательный критерий повторён в final2/final-copy.
- **final2: exit0,168/168 cells +586/586 checks PASS**. Cells: восемь экранов ×AZ/RU/EN ×320/360/390/768/1024/1280/1440. Checks:192 responsive state variants,216 actual flow assertions,168 keyboard first-focus,10 static preview boundary probes.
- **final-copy: exit0,78/78 cells +111/111 checks PASS**.48 default cells всех восьми экранов при390/1440;30 denied cells. Checks:96 настоящих Tab→Enter skip-link переходов,6 Enter-triggered demo reconciliation,9 public pending/rejected/revoked negatives.
- Во всех последних двух прогонах console/page errors0, static failures0, failed requests0, external requests0. Python `py_compile` preview/collect/summary и `bash -n` runner: exit0.

Raw evidence и screenshots остаются вне Git: `/root/task33-evidence/stage25-design-final2-20261003` (24PNG), `/root/task33-evidence/stage25-design-final-copy-20261003` (16PNG); старые RED/harness snapshots в аналогичных отдельных каталогах сохранены. Полные raw records не копируются в repository aggregate. Примеры: `profile-ru-390.png`, `person-ru-1440.png`, `organization-active-ru-390.png`, `documents-approved-ru-1440.png`, `review-denied-ru-390.png`; последний copy-run имеет свежие default PNG для всех восьми экранов. Лично просмотрены mobile public/organization и desktop person/documents/index screenshots; source inspection не выдаётся за эти rendered evidence.

## Проверенное поведение и пределы

На макетах invitation создаёт0/2 согласий; отдельное действие организации либо человека даёт1/2 pending; явное действие второго участника даёт2/2 active. Переключение языка сохраняет actor/consent; cancellation сохраняет роль, период, дату03.10.2026 и ровно существующие consent events (none/one/both). History отделена от текущей работы. Organization не содержит controls biography/person contact/documents. Online скрывает текущие office fields, сохраняя прежнюю practice history.

Claim требует подтверждения «это мой профиль», ждёт KidsMap и может быть отозван без удаления synthetic ID/старого URL. Identity upload choice отсутствует; pending qualification остаётся private даже при выборе публикации; approved opt-in/withdraw обновляет видимый Public/Private badge. Reviewer approval не выбирает публикацию за человека. Dedicated-review denial не содержит private controls. Required/error fields связаны с aria-invalid/error text и получают фактический focus; неподдерживаемый file extension отклоняется, valid synthetic file не отправляется никуда. Реальные ACL, bytes storage, claim ownership или server validation этим не сертифицируются.

Preview GET positives: index/logo/twofonts200. Negatives: .env/.git/config/private media/directory listing/encoded traversal404. Каждый runner закрыл только собственную `qa25` session и HTTP server8795; последний close exit0 и endpoint8795 недоступен. Отдельный root user-preview8796 не затронут.

## Остаток и named handoff

P3 copy caveat: [prototype.js](../design/specialist/prototype.js), `descriptions.review`, RU gallery содержит «публичный выбор не reviewer scope». Это видимая смешанная терминология макета; root решил сохранить текущий frozen срез для review. Функциональные checks её не маскируют; будущая polish правка требует свежей affected-screen проверки.

**NOT RUN:** application integration, PostgreSQL/migrations/Django checks для design-only25, реальные nested-ID/role/URL backend tests, реальный transfer reconciliation, реальная загрузка/скачивание документов, production, user acceptance, полный screen-reader audit. Native file/date picker язык и формат определяет браузер/OS; headless Chromium default English не доказывает локализацию native dialogs. Показанный reconciliation — синтетическая демонстрация, а не перенос данных.

Handoff → root `frontend-reviewer`: представить specialist-25-r1 и recorded REVIEW_PENDING пользователю. После явного принятия продолжить только stage25 application integration; для backend границ подключить `django-reviewer`, выполнить isolated PostgreSQL negative/integration checks и новый реальный browser matrix приложения. Этап26 и production не запускать. Не объявлять stage25 DONE по этим макетам.
