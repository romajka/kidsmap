# Google OAuth KidsMap — состояние 7 сентября 2026

## Результат

Google Login **не активирован и не объявляется готовым**. Client ID подготовлен в production env. Проверки приложения прошли: 77 локальных тестов и 80 тестов подготовленного OAuth-image на изолированном PostgreSQL 17. Реальный обмен с Google не выполнялся.

Два блокера: Client Secret ещё пуст; production содержит **2 группы совпадающих нормализованных email / 6 аккаунтов**, включая 5 staff и 1 superuser. Уникальный индекс отсутствует. До решения владельца по этим аккаунтам миграцию и включение OAuth выполнять нельзя. Ни email, ни владельцы, ни пароли production-пользователей не изменялись.

## OAuth-конфигурация

| Параметр | Значение |
|---|---|
| Client ID | `88663636869-ol0qmuh01j1v4v6h3s0202kbdgfnd02i.apps.googleusercontent.com` |
| Environment names | `GOOGLE_OAUTH_CLIENT_ID`, `GOOGLE_OAUTH_CLIENT_SECRET` |
| Production environment | `/opt/kidsmap/.env`, mode `0600` |
| Production origin | `https://kidsmap.az` |
| Callback | `https://kidsmap.az/auth/google/callback/` |
| Django route | `path("auth/google/callback/", google_callback, name="google_callback")` в `src/config/urls.py` |
| Callback handler | `catalog.google_auth.google_callback` → `allauth.socialaccount.providers.google.views.oauth2_callback` |
| Provider | `django-allauth[socialaccount]==65.19.2`, `allauth.socialaccount.providers.google` |
| Adapter | `catalog.google_auth.KidsMapSocialAccountAdapter` |
| Scopes | Только `openid`, `email`, `profile` |
| Provider options | PKCE S256; `access_type=online`; `prompt=select_account`; сохранение токенов отключено |
| Google Auth Platform | Testing — по сообщению пользователя; настройки Google Cloud не изменялись |

Провайдер настроен через `SOCIALACCOUNT_PROVIDERS["google"]["APP"]`. Дополнительный SocialApp в Django admin не нужен: он создаёт неоднозначную конфигурацию. `django.contrib.sites` не установлен; отдельный Site/SITE_ID для данного callback не требуется. allauth получает путь через `reverse("google_callback")`, а домен/схему — из request. Callback единый, вне i18n_patterns.

## Свежая проверка production

- SSH-аутентификация установлена после предоставления пользователем доступа. Учётные данные доступа не сохранены в файлы/отчёт.
- Checkout: `/opt/kidsmap`, HEAD `86a0b8cf64a8835f310a608a3428c60f1fc5341a`. До изменений рабочее дерево чистое; после — только разрешённое изменение `.dockerignore` среди tracked-файлов. `.env` не добавлялся в Git.
- Активный `kidsmap-web` остаётся на прежнем image, совпадающем с `kidsmap-web:before-google-20260906` (digest prefix `47e941626be80`). Контейнер запущен `2026-09-04T12:55:16.35726024Z` и не перезапускался.
- В активном image Django 6.0.2, **allauth отсутствует**. OAuth ещё не является live-возможностью сайта.
- В production применена `catalog.0100_place_price_mode`; `catalog.0101_unique_user_email`, account/socialaccount migrations отсутствуют.
- SQL-проверка выполнена в `SET TRANSACTION READ ONLY`, `statement_timeout=15s`, `lock_timeout=2s`. Выведены только агрегаты; пользовательские записи и email не извлекались в отчёт.
- `kidsmap.az` присутствует в allowed hosts; `https://kidsmap.az` — в trusted origins. SSL redirect и secure session/CSRF cookies включены. `SECURE_PROXY_SSL_HEADER=(HTTP_X_FORWARDED_PROTO, https)`, forwarded host включён.
- `nginx -T` прошёл; подтверждены передача Host и X-Forwarded-Proto. TLS-соединение с проверкой hostname/certificate успешно, TLS 1.3; сертификат действителен до 8 октября 2026.
- Активный `/opt/kidsmap/docker-compose.yml` пока **не передаёт OAuth env**. Подготовленный release `/opt/kidsmap-releases/google-20260906/docker-compose.yml` передаёт обе переменные. Одно заполнение `.env` не устанавливает OAuth-код и не активирует его.

## Сделанные изменения

1. Перед изменениями создан root-only backup `/opt/backups/kidsmap-google-config-20260906T212158Z/`: каталог `0700`, копии `.env`, `docker-compose.yml`, `.dockerignore` — `0600`. UTC-имя каталога соответствует 7 сентября по Asia/Baku. Секретосодержащие копии остались только на сервере.
2. В `/opt/kidsmap/.env` записан предоставленный Client ID; `GOOGLE_OAUTH_CLIENT_SECRET` оставлен пустым. Файл записан атомарно, права `0600`. После записи проверены совпадение Client ID и отсутствие secret, без вывода secret.
3. В локальный и серверный `.dockerignore` добавлены `.env`, `.env.*`, `.tmp`; `.env.example` сохранён в контексте через исключение. Это предотвращает попадание production env в будущие сборки. Новая production-сборка не выполнялась.
4. Application-код, production DB, PostgreSQL, Redis и nginx не изменялись/не перезапускались. Ни commit, ни push не выполнялись. Другие dirty-функции локального дерева не выкладывались.

## Автоматическая проверка

| Срез | Среда | Результат |
|---|---|---|
| Текущее local worktree поверх HEAD `df6fef3784a6bae6b7ddce90cd41a392d9f9e6bf` | Python 3.14.0, Django 6.0.2, allauth 65.19.2, новая временная SQLite DB/media | **77 tests, OK, 59.458 s, exit 0** |
| Подготовленный `kidsmap-web:google-20260906`, digest prefix `3f44ada8b182` | Python 3.12.13, Django 6.0.2, allauth 65.19.2, отдельный PostgreSQL 17 | **80 tests, OK, 89.778 s, exit 0** |

Оба запуска: `DJANGO_TESTING=1`, очищенное application environment, LocMem cache/email, временный media root. Google HTTP заменён тестовыми ответами; неожиданные requests HTTP-вызовы блокировались. PostgreSQL работал в отдельном контейнере, без опубликованных портов, с отдельной internal Docker network и tmpfs-данными, без production credentials/volumes. После запуска тестовые контейнеры и сеть удалены; удаление проверено.

Команда локального запуска:

```powershell
.venv/Scripts/python.exe .tmp/verify_google_oauth_20260907.py
```

В обоих runners выполнены:

```text
manage.py check
manage.py makemigrations --check --dry-run
manage.py test catalog.testcases.test_google_auth catalog.testcases.auth_flow catalog.testcases.auth_access catalog.testcases.test_password_reset --noinput --verbosity 2
```

System checks прошли, migration drift отсутствует. Миграции, включая индекс уникального email и allauth, применились только на пустых изолированных тестовых DB.

PostgreSQL runner: `.tmp/google_oauth_pg_verification_20260907.py`. На сервере его копия `verify_pg.py`, orchestration `run_pg.py`, `tests-pg.log` и `tests-pg.exit` находятся в указанном backup-каталоге. `run_pg.py` запускает свежие изолированные контейнеры и передаёт runner в `docker run ... --entrypoint python kidsmap-web:google-20260906 -`; его нельзя заменять запуском тестов внутри production web.

К 77 существующим тестам runner добавляет три контрактные проверки без изменения production-кода:

- `test_verified_existing_user_full_password_reset`: исходный email уже подтверждён в KidsMap; Google возвращает тот же User/PK, всего один User; исходный email и password hash сохранены; старый password login работает; reset email → token → установка нового пароля → password login ведут в тот же User; SocialAccount по-прежнему относится к нему.
- `test_locale_success_and_cancel`: успешный login и локализованная отмена для AZ/RU/EN; повторные входы не создают дублей.
- `test_callback_https_and_local_origins`: фактический allauth callback через HTTPS proxy для AZ/RU/EN и localhost/127.0.0.1:8000, без языкового префикса.

Существующие тесты покрывают new/repeat Google user, unusable password и верификацию без повторного OTP, linking/password preservation, missing/unverified email, invalid/expired/replayed state, OAuth cancel/error/network failure, issuer/audience/expiry validation, identity conflicts, safe/malicious next, POST/CSRF, scopes/PKCE, уникальность email при insert/update, откат позднего identity collision и коллизии обычной регистрации/profile update.

Проверены совпадающие SHA256 (после нормализации CRLF) шести локальных файлов и image: requirements, Google bridge, config urls, migration 0101, auth_redirects, Google tests. Это не утверждение о совпадении всего dirty worktree с release. В OAuth-image `/app/.env` отсутствует.

Ограничения: настоящая параллельная гонка двух процессов не запускалась; проверены DB constraints и искусственно вызванные поздние конфликты. Полный owner/public suite заново не запускался. Реальный Google consent/token exchange, Audience test user и live linking не проверены.

## Account linking и migration gate

Реализованное правило — один **непустой** `lower(trim(email))` → один User. Активный пользователь с verified Google email переиспользуется; выбранный локальный email не перезаписывается. Существующий пароль/права сохраняются. Новый Google User получает unusable password. Inactive User автоматически не активируется; конфликтующие identities отвергаются без объединения.

`catalog.0101_unique_user_email` сначала проверяет дубли, затем создаёт уникальный expression index. Production preflight показывает, что её prerequisite сейчас не выполнен. Выполнять release/migrate, пропускать эту миграцию, автоматически очищать email или выбирать главный аккаунт нельзя. Владелец должен определить корректные уникальные email/учётные записи в двух группах; дальнейшее изменение данных требует отдельного согласованного способа, без ручного SQL в рамках этой задачи.

## Следующий шаг пользователя

На сервере `157.173.119.227` открыть:

```bash
sudo nano /opt/kidsmap/.env
```

В существующую строку `GOOGLE_OAUTH_CLIENT_SECRET=` самостоятельно вставить Client Secret, сохранить файл. Client ID уже установлен. Не использовать `cat`, `echo` с secret или передачу secret в аргументах команды. Backup уже сделан; nano проверен: `/usr/bin/nano`.

После этого всё равно остаётся migration gate по дублям. Только после его разрешения, установки проверенного OAuth-релиза/Compose и применения стандартных миграций обновляется **только `web` / контейнер `kidsmap-web`**:

```bash
cd /opt/kidsmap
docker compose --env-file /opt/kidsmap/.env up -d --no-deps --force-recreate web
```

Эта команда приведена для последующего этапа, **сейчас её выполнять не следует**: текущие source/image/Compose ещё не являются активированным OAuth-релизом. Обычный `docker restart` не перечитывает Compose environment.

Реальный smoke test затем выполняется только для Audience → Test users. Обязательный критерий готовности: существующий verified email → Google Login → тот же production User/PK, без дубля, с сохранением password login/reset. До этого готовность Google Login остаётся неподтверждённой.
