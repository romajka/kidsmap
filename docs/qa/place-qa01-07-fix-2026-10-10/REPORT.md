# PLACE-QA-01–07: исправления и свежая проверка

**Итог: семь findings исправлены и проверены в LOCAL WORKTREE.** Это результат локального исправления; production acceptance не выполнялся. Исторический аудит и его OPEN-записи сохранены без изменений.

Разрешение на реализацию: явное сообщение пользователя «Всё, начни работу, всё исправь», после подготовки семи конкретных планов. Подтверждение сохранено в [approval.json](C:/kidsmap/docs/qa/place-qa01-07-fix-2026-10-10/approval.json). PLACE-QA-08–10 ранее упоминались только как номера; подтверждённых файлов findings и согласованных планов для них нет. Они не объявлены исправленными.

## Исправления

| Finding | Реализация | Свежий результат |
|---|---|---|
| PLACE-QA-01 | Continuous-редактор выводит сохранённый review_note в rejected/declined и исправленном draft; стандартное Django-экранирование, локальные RU/AZ/EN подписи, перенос длинных строк | Создание через кабинет → отправка → отказ модератора → reload → настоящий logout/login → исправление/сохранение → повторная отправка. Причина сохраняется до повторной отправки и затем очищается. Литерал script не исполняется |
| PLACE-QA-02 | Clear/locate привязаны до провайдера и один раз; статус и aria-busy, защита от устаревших callbacks, finite/range guards; поздний провайдер подключается без повторных обработчиков; fallback использует textContent | Очистка без SDK, видимые сообщения unsupported/denied/timeout, сохранение и reload; нативный браузерный отказ разрешения и геолокация с вымышленной точкой; поздний load с локальным адаптером создаёт одну карту, clear даёт одно событие |
| PLACE-QA-03 | После немедленного применения pricing_plans rebasing включает реально изменённые пять scalar-проекций. Старые full-form echoes не возвращают старые цены. Отдельный отличающийся scalar intent сохраняется в candidate | 15→18 + имя/адрес, save/reload/submit/реальное approve; 18→21 price-only через AZ; 21→24 mixed через EN; публичная карточка после approve. ID тарифа стабилен. Конкурирующая вкладка и устаревшее одобрение защищены |
| PLACE-QA-04 | Только continuous-форма: при обоих пустых координатах Баку разрешает район; другой город очищает/отключает его. Partial/invalid point не включает ручной режим. Восстановление полей ограничено start/end событиями с отменой старого lookup | Clear → другой город → Баку → район → save/reload; действительное localStorage-восстановление и server-draft-восстановление после очистки localStorage; устаревшие ответы не меняют район |
| PLACE-QA-05 | Mobile popup ограничен контейнером; search может сжиматься; длинные подписи переносятся, счётчик на mobile вынесен на свою строку. Escape работает из поиска/option даже без результатов; выбор возвращает фокус, outside click его сохраняет | RU/AZ/EN × 360/390/768/1024/1280/1440: 18 комбинаций, меню в viewport, полное название, keyboard/focus. Реальные category/subcategory save/reload и проверка сохранённого candidate |
| PLACE-QA-06 | Новый отдельный GNU msgfmt build/verify helper. Новая папка под .tmp, frozen PO, hashes, complete manifest последним; проверка перед Django.setup. Общие MO не меняются | 9 тестов реального компилятора, 4 отказа запуска с испорченными/неполными assets до HTTP bind, 21 runtime gettext check, 15 rendered языковых/ширинных комбинаций, сохранение description с сохранностью остальных полей |
| PLACE-QA-07 | Две singular non-fuzzy записи в AZ/EN; две русские identity-записи удерживают прежний RU-текст при default-language fallback Django. Enum/model/ACL не изменены | Подписи RU/AZ/EN на пяти ширинах; оба machine values сохранены и прочитаны после reload во всех трёх языках. DB подтверждает отсутствие изменения live nature и nature_approved_at |

Примечание к RU: добавление только AZ/EN выявило реальный RED — русский runtime использовал AZ fallback. Две RU-записи необходимы для сохранения прежних русских подписей; остальные переводы и headers не перерабатывались.

## Snapshot и изоляция

LOCAL HEAD: `8d188b316f800fbedf0b1e376905dfd4924cb1b6`, ветка `task33-progress`, `active_run: NONE`. Изменения находятся в WORKTREE, commit/push/deploy не выполнялись. Входящие docs и все семь планов сохранены по SHA256; общие три MO сохранены по SHA256. Проверка существовавших чужих контейнеров выполнена до и после работы. См. [initial-snapshot.json](C:/kidsmap/docs/qa/place-qa01-07-fix-2026-10-10/initial-snapshot.json), [final-snapshot.json](C:/kidsmap/docs/qa/place-qa01-07-fix-2026-10-10/final-snapshot.json).

DJANGO_TESTING=1; PostgreSQL 17 alpine, отдельный контейнер `kidsmap-placeqa01-07-fix-20261010-r2`, loopback 55445, DB `placekmfix_plan`, отдельная тестовая DB; HTTP 8840. Отдельные LocMem cache/email, media/private-media, allowlisted environment, пустые внешние ключи. Python socket transport разрешён только к собственной БД; browser transport разрешён только к 127.0.0.1:8840. Все записи вымышленные. Пароли, cookies и сырые HTML-дампы находятся только в ignored scratch.

Локали собраны WSL GNU msgfmt 0.21 с check-format/statistics/little-endian и без fuzzy в `.tmp/place-qa01-07-fix-20261010/locale-build-02`. Полный manifest проверяется до Django.setup; sole LOCALE_PATHS указывает на эту сборку. Повторная hash-проверка прошла после всех изменений. [Документация helper](C:/kidsmap/docs/qa/isolated-locale-build.md), [isolation.json](C:/kidsmap/docs/qa/place-qa01-07-fix-2026-10-10/isolation.json).

Один последовательный исполнитель. Независимые специалисты не запускались. Codebase Memory MCP при свежей попытке возвращал Transport closed; использован ограниченный поиск и проверка нужных исходников. Граф не служил основанием для удаления кода или DB-структур.

## Проверки и точные exits

| Набор | Количество | Native exit | Evidence |
|---|---:|---:|---|
| Новые regression + publication/continuous/taxonomy/admin editors | 92 | 0 | [django-green-second.txt](C:/kidsmap/docs/qa/place-qa01-07-fix-2026-10-10/django-green-second.txt) |
| Geography, drafts, pricing, relational pricing | 76 | 0 | [django-geography-pricing-regression.txt](C:/kidsmap/docs/qa/place-qa01-07-fix-2026-10-10/django-geography-pricing-regression.txt) |
| Две отдельные PostgreSQL connections, JSON/pricing modes, volunteer admin | 75 | 0 | [django-concurrency-final.txt](C:/kidsmap/docs/qa/place-qa01-07-fix-2026-10-10/django-concurrency-final.txt) |
| Map picker/location resolver, включая invalid restored point | 34 | 0 | [js-final-expanded.txt](C:/kidsmap/docs/qa/place-qa01-07-fix-2026-10-10/js-final-expanded.txt) |
| GNU gettext builder: context/plural/fuzzy, deterministic hash, stale/tamper/missing/format/path/junction | 9 | 0 | [locale-tool-final.txt](C:/kidsmap/docs/qa/place-qa01-07-fix-2026-10-10/locale-tool-final.txt) |
| Startup gate: 4 повреждённых случая + валидный preflight | 5 | wrapper 0; invalid children 1, valid 0 | [locale-startup.json](C:/kidsmap/docs/qa/place-qa01-07-fix-2026-10-10/locale-startup.json) |
| Runtime gettext | 21 | 0 | [locale-runtime.json](C:/kidsmap/docs/qa/place-qa01-07-fix-2026-10-10/locale-runtime.json) |
| Финальные hash verify / git diff --check | — | 0 / 0 | [locale-verify-final.txt](C:/kidsmap/docs/qa/place-qa01-07-fix-2026-10-10/locale-verify-final.txt), [diff-check-final.txt](C:/kidsmap/docs/qa/place-qa01-07-fix-2026-10-10/diff-check-final.txt) |

Итого выполнено 243 Django-проверки, 34 JS-проверки и 9 тестов builder. Системная проверка Django в каждом server test run не выявила проблем. В existing tests встречаются ожидаемые логи специально внедрённых storage failures — suites завершились OK. PostgreSQL concurrency проверяет ровно одного успешного writer и один конфликт при одинаковых исходных версиях; победившие цена/candidate сохранены, чужая запись не теряется.

Исходный RED сохранён: rejection/labels/projection failures, отсутствие helper, junction acceptance, invalid/partial restored point. После исправлений соответствующие наборы GREEN. [Точные команды и exits](C:/kidsmap/docs/qa/place-qa01-07-fix-2026-10-10/COMMANDS.md), [native ledger](C:/kidsmap/docs/qa/place-qa01-07-fix-2026-10-10/command-ledger.jsonl), [browser ledger](C:/kidsmap/docs/qa/place-qa01-07-fix-2026-10-10/browser-command-ledger.jsonl).

## Браузер и DB readback

Chromium headless shell 153.0.8010.12, настоящие rendered страницы, формы и HTTP сохранение. Автоматические проверки дополняются просмотром mobile screenshot. Финальное меню 360 px имеет popup left=53/right=307 и полностью читаемую длинную подпись. Screenshot animation отключена только при capture, чтобы не сохранять промежуточный fade frame.

Структурированные результаты: [rejection matrix](C:/kidsmap/docs/qa/place-qa01-07-fix-2026-10-10/browser-owner-rejection-matrix.result.json), [resubmission](C:/kidsmap/docs/qa/place-qa01-07-fix-2026-10-10/browser-owner-resubmit.result.json), [manual map](C:/kidsmap/docs/qa/place-qa01-07-fix-2026-10-10/browser-map-manual.result.json), [local/server restore](C:/kidsmap/docs/qa/place-qa01-07-fix-2026-10-10/browser-district-restore.result.json), [native permission/late adapter](C:/kidsmap/docs/qa/place-qa01-07-fix-2026-10-10/browser-map-permissions-late.result.json), [menu matrix](C:/kidsmap/docs/qa/place-qa01-07-fix-2026-10-10/browser-admin-matrix.result.json), [admin save](C:/kidsmap/docs/qa/place-qa01-07-fix-2026-10-10/browser-admin-save-locales.result.json), [nature saves](C:/kidsmap/docs/qa/place-qa01-07-fix-2026-10-10/browser-nature-save.result.json).

Pricing: [mixed save](C:/kidsmap/docs/qa/place-qa01-07-fix-2026-10-10/browser-pricing-mixed.result.json), [review matrix/approve](C:/kidsmap/docs/qa/place-qa01-07-fix-2026-10-10/browser-pricing-review.result.json), [pending DB](C:/kidsmap/docs/qa/place-qa01-07-fix-2026-10-10/pricing-db-pending.json), [approved DB](C:/kidsmap/docs/qa/place-qa01-07-fix-2026-10-10/pricing-db-approved.json), [public readback](C:/kidsmap/docs/qa/place-qa01-07-fix-2026-10-10/browser-public-readback.result.json), [stale tab](C:/kidsmap/docs/qa/place-qa01-07-fix-2026-10-10/browser-stale-confirm.result.json), [stale review](C:/kidsmap/docs/qa/place-qa01-07-fix-2026-10-10/browser-stale-review-confirm.result.json), [final DB assertions](C:/kidsmap/docs/qa/place-qa01-07-fix-2026-10-10/browser-final-db.json).

Админское сохранение согласно существующему lifecycle создаёт candidate: description/category/subcategory проверены в revision.payload, а не объявлены немедленно опубликованными. Аналогично редактирование другим admin меняет текущий candidate; свежий review может быть approvable. Проверка старого review выполнялась после реального сохранения и одобрения конкурирующего candidate: старое одобрение отклонено, чужой live текст сохранился. После конкурентных проб тестовая цена равна 27.00; ранний public readback фиксирует успешно одобренные 24.00. Stable plan ID=1 подтверждён на обоих этапах.

Основные изображения: [причина 390 px](C:/kidsmap/docs/qa/place-qa01-07-fix-2026-10-10/rejection-ru-390.png), [после login](C:/kidsmap/docs/qa/place-qa01-07-fix-2026-10-10/rejection-after-login-1440.png), [меню 360 px](C:/kidsmap/docs/qa/place-qa01-07-fix-2026-10-10/admin-ru-360.png), [ручной район после reload](C:/kidsmap/docs/qa/place-qa01-07-fix-2026-10-10/map-manual-reload-390.png), [локали](C:/kidsmap/docs/qa/place-qa01-07-fix-2026-10-10/locales-az-390.png), [реальный stale conflict](C:/kidsmap/docs/qa/place-qa01-07-fix-2026-10-10/genuine-review-conflict-1440.png). Все screenshots и SHA256 перечислены в [manifest](C:/kidsmap/docs/qa/place-qa01-07-fix-2026-10-10/screenshots-manifest.json).

## Отклонения harness и ограничения NOT RUN

Логи не скрывают промежуточные неудачные команды. Первый порт 55460 входил в Windows excluded range; только свой неработающий контейнер остановлен, новый создан на 55445. Исправлены неверный импорт test enum, обращение test к отсутствующему Place.region, передача multiline/ampersand через npx.cmd, предположение о redirect после save и повторное использование session, аннулированной реальным logout. Нулевая exact price и пустой product_type были корректно отклонены в первичном заполнении fixture; затем выбран полноценный тариф. У stale tests уточнён наблюдаемый локализованный error, backend защита подтверждена DOM и DB. Проверка `git -c core.autocrlf=false diff --check` дала CRLF false positives; обычный check с фактическими настройками checkout прошёл. Первый finalizer искал active_run не в том файле; финальный snapshot читает канонический implementation-status.

**NOT RUN:** production, внешние интеграции и настоящие Google/OSM SDK/provider requests; физическая геолокация устройства; Firefox/WebKit и браузер под корпоративной политикой Chrome; весь несвязанный project suite; ретроспективное исправление старых persisted candidates; acceptance остальных модулей. Late provider проверен локальными synthetic adapters в JS и rendered browser, browser geolocation использует разрешения Chromium и вымышленную emulated point. Внешние Leaflet requests дают ожидаемые blocked-by-client console errors. Shared MO не обновлялись: для будущих QA-стендов требуется новый isolated build/verify по документации helper.

## Завершение стенда

Собственный browser session и HTTP server закрыты; оба собственных PostgreSQL контейнера остановлены и сохранены для воспроизводимости. Чужие стенды не останавливались. Точный результат закрытия записан в cleanup.json. Исходники, новые tests, отчёт и evidence оставлены в WORKTREE для проверки пользователя.

Native runserver завершился exit 1 после намеренного Stop-Process проверенного PID в Windows; cleanup wrapper — exit 0, HTTP port 8840 проверен свободным. Это остановка собственного стенда, не ошибка проверки приложения. См. shutdown-native.json.
