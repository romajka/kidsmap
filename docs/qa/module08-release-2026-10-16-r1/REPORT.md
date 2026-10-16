# Модуль08: Git и выкладка выполнены

2026-10-16. Пользователь разрешил отправить все изменения в Git и применить их на сервере после готовности модуля. Условие выполнено: [ACCEPT-08 LOCAL PASS](../module08-accept-2026-10-16-r2/REPORT.md), MOD-QA-01–13 закрыты в записанном scope. Модуль09 не начат.

## Три разных снимка

| Среда | Фактическое состояние |
|---|---|
| Исходный локальный checkout | /home/ramin/kidsmap, task33-progress, HEAD e4e05cc213b34e2d771ecb854901bfd016d1db51 +dirty WORKTREE, active_run NONE. Исходный HEAD и индекс сохранены |
| Git | Ветка codex/module08-release-2026-10-16. Кодовый commit cfef63e3dbc93e971ac0e2ae963a17a3821ae27c, полный пакет QA-снимков 5c98e965278f556e38b72f1b7f699c7f9a3b3929; последующий receipt содержит только QA/документы |
| Production | /opt/kidsmap на новой release-ветке, код cfef63e3dbc93e971ac0e2ae963a17a3821ae27c. Образ kidsmap:module08-cfef63e3, ID sha256:1f2d56ca252808d941c7f0514c268cdcc8d68d0ecacbe3ad5a151132302ede73. Новый web ff834ae278e4a86fc5100f53dde11f1646ee64c7be790e686f935d862d826905 |

Git-история содержит отдельные крупные коммиты с QA PNG. После кодового commit изменения касаются только docs/qa; runtime приложения совпадает с опубликованным пакетом. Git parity сама по себе не использовалась как доказательство работающего приложения.

## Git-пакет и сохранность

[План и исключения](git-package-plan.json), [коммиты](git-commits.json), [пять проверенных push](push-verification.json), [source parity](git-code-source-parity.json).

Все актуальные безопасные изменения приложения, тестов, планов и QA-материалов отправлены в новую ветку. Для почти2ГБ материалов использованы пять последовательных push, без force. Создан отдельный Git-индекс: исходные локальные HEAD, индекс и WORKTREE не переключались и не очищались. Reset/clean/stash не применялись.

Пять исторических QA-логов с сырыми CSRF-токенами исключены из публикации; оригиналы сохранены локально. Секреты, .env, production records, dumps и текущие SSH credentials в Git не копировались. Исходники приложения не исключались.

## Что сделано на сервере

До изменения проверены чистый task33-progress@8d188b316f800fbedf0b1e376905dfd4924cb1b6, соответствие образа старому source, здоровые PostgreSQL/Redis, mounts и окружение: [before](server-before.json), [preflight](server-preflight.json).

1. Созданы закрытые резервные копии БД, статики, media/private-media; проверены pg_restore --list и gzip integrity. [Backup metadata](server-backup.json). Данные остаются только на сервере. Полный restore drill с production records **не выполнялся**.
2. Старая server-ветка и старый образ сохранены для отката. Новый код получен из Git в отдельную release-ветку.
3. Образ собран из проверенного Git-кода. В build context отсутствуют .env и массив QA-артефактов. [Build](build-result.json).
4. Перед переключением проверены **968 файлов исходников/PO и3MO**, версии Django6.0.2/pypdf6.20.1 совпали с локальным стендом. System check PASS;175 применённых миграций, ожидающих0. [Image preflight](image-preflight.json).
5. Модели и миграции относительно старого production не менялись. Миграции/изменения данных/sync_site_defaults не запускались. Выполнен collectstatic и переключён только web. [Activation](activation.json).
6. Окружение, .env, media/private/static mounts сохранены. ID контейнеров PostgreSQL и Redis не изменились. Старый образ доступен; старый override и статика сохранены. Автоматический возврат подготовлен, **не понадобился и не выдаётся за выполненный rollback drill**.

Общие MO локального checkout не перезаписывались. Production MO собраны внутри нового образа из текущих PO и совпали с отдельной проверенной локальной сборкой.

## После переключения

[Running verification](running-verification.json), [финальный сервер](final-server.json), [браузер](production-browser.json), [12PNG с SHA/dimensions](PNG-manifest.json).

- Реально работающий контейнер использует нужный image ID. Проверены все968 исходников/PO и3MO; DEBUG=False, TESTING=False.
- /healthz, публичные RU/AZ/EN, каталог и origin admin login:10HTTP-проверок200.
- Публичные JS/CSS совпадают с текущими исходниками. HTML использует fingerprinted static URLs, а не старые имена из браузерного cache.
- Настоящий Chromium: **30PASS,0FAIL**, RU/AZ/EN×390/1440. Анонимные страницы входа public/admin, окно восстановления пароля, Tab/ShiftTab, Escape и возврат фокуса. Формы не отправлялись; production users/пароли/данные не менялись.
- Page errors0.24 внешних запроса к GTM/Cloudflare Insights/fonts намеренно blocked, соответствующие console ERR_FAILED ожидаемы; first-party failed requests0. Production tracking ради проверки не запускался.
- Обычный Python HTTP-клиент получил Cloudflare403 на admin host, но настоящий браузер открыл все6admin login cases и корректные стили. Этот ответ клиента не выдан за поломку приложения; правила Cloudflare не изменялись.

Полный модульный корпус261 был выполнен локально один раз. После исправлений использованы только13целевых/sharedDjango,4Node и433+341 native наблюдений по новым причинам. При выкладке полный модульный и глобальный наборы повторно не запускались.

## Ограничения и исходная проблема вне модуля08

Authenticated admin mutations, реальная отправка production email/reset, OAuth/Maps/GA API, cross-browser/physical devices/screenreader и общая приёмка всех модулей **NOT RUN**. Локальный полный сценарий восстановления пароля проверялся ранее на собственном письме и вымышленных данных; production-формы здесь не отправлялись.

При preflight найдено существовавшее до выкладки состояние: GOOGLE_APPLICATION_CREDENTIALS настроен, но файл по этому пути не читается. [Metadata без значений](google-credential-preflight.json). Новая выкладка сохраняет окружение; ключ не создавался, интеграция GA API не объявлена рабочей. Это отдельный вопрос внешней аналитики, а не новый MOD finding и не автоматический запуск модуля12.

Вывод: модуль08 закрыт LOCAL и его изменения развёрнуты с подтверждённым source/runtime и указанным production smoke. Это не утверждение об отсутствии дефектов во всех оставшихся модулях.
