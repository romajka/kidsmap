# KidsMap

> Supported Python version: **3.12** (see `.python-version` and the CI image).

## Local setup

The dependency files are split by purpose:

- `requirements/base.txt` — framework and application runtime;
- `requirements/production.txt` — base plus Gunicorn, Brotli, and MariaDB/MySQL support;
- `requirements/development.txt` — base plus test tooling (`tblib` is required for parallel tracebacks).

### Windows (PowerShell)

Install Python 3.12 first; newer unsupported interpreters are not a substitute for the project version.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements\development.txt
python manage.py migrate
python manage.py check
python manage.py runserver
```

The default local database is SQLite, so Windows development does not require `mysqlclient` or
`Brotli`. Install `requirements\production.txt` only when reproducing the production stack.

### Linux

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements/development.txt
python manage.py migrate
python manage.py check
python manage.py runserver
```

For a production/container installation use `pip install -r requirements/production.txt`.
Before running `compilemessages`, install GNU gettext (`gettext` package on Debian/Ubuntu).

### Tests

```bash
python manage.py test --parallel auto
```

`catalog/tests.py` is the canonical suite manifest. It includes every current testcase module
without re-exporting TestCase classes, preventing duplicate execution.

### Uploaded images

JPEG, PNG, and WebP uploads are validated by decoding their contents. KidsMap generates
responsive WebP variants for cards, detail pages, galleries, hero banners, and avatars;
public templates use these variants through `srcset` while retaining the original as a fallback.

To backfill variants after importing media or after enabling this pipeline, run:

```bash
python manage.py optimize_images
```

KidsMap — каталог детских кружков, секций и курсов по Азербайджану.

Проект помогает родителям быстро находить подходящие занятия по региону, району, метро, возрасту, цене и отзывам, а владельцам кружков — управлять своими карточками через отдельный owner-flow с модерацией.

Если проект открывается в новом AI-чате, попросите ассистента **сначала прочитать [AI_HANDOFF.md](./AI_HANDOFF.md)**. Этот файл подготовлен как подробный контекст для продолжения работы без потери понимания продукта и текущих технических правил.

## Что уже есть

- каталог кружков и секций по регионам Азербайджана
- мультиязычность `RU / AZ / EN`
- регистрация и логин
- подтверждение email через OTP
- восстановление пароля по email
- личный кабинет пользователя
- owner-кабинет
- заявки на управление карточками
- модерация карточек и ownership-заявок
- отзывы о кружках
- отдельные отзывы о сайте
- лайки / дизлайки для отзывов
- карта кружков
- Google Maps / геокодирование
- админка на отдельном поддомене

## Продуктовая идея

KidsMap — не просто список карточек. Это сервис, где:

- родитель может быстро сузить выбор по понятным параметрам
- владелец кружка может подать заявку на карточку и управлять ею после модерации
- модератор сохраняет контроль качества контента и прав на управление карточками
- карточка должна быть полезной как в списке, так и на детальной странице: фото, возраст, цена, расписание, адрес, контакты, карта, отзывы

## Текущий стек

- Backend: `Django`
- База данных: `MariaDB` в Docker, `SQLite` возможен локально для части dev-flow
- Frontend: Django templates + custom CSS + vanilla JS
- Инфраструктура: `Docker Compose`
- Прод: VPS Contabo
- Домен сайта: `https://kidsmap.az`
- Админка: `https://admin.kidsmap.az/ru/admin/`

## Структура проекта

```text
/home/ramin/kidsmap
├── config/                  # служебный конфиг и entry points
├── locale/                  # переводы RU/AZ/EN
├── media/                   # загруженные файлы
├── scripts/                 # deploy/run helper scripts
├── src/
│   ├── catalog/
│   │   ├── controllers/     # orchestration/use-case entry points
│   │   ├── interfaces/      # контракты
│   │   ├── repositories/    # работа с ORM / persistence
│   │   ├── services/        # бизнес-логика
│   │   ├── templates/       # app templates
│   │   └── migrations/
│   └── config/              # settings / urls / wsgi
├── static/                  # исходные статические файлы
├── staticfiles/             # collectstatic output
├── templates/               # общие шаблоны
├── docker-compose.yml
├── DEPLOYMENT.md
└── AI_HANDOFF.md
```

## Архитектурный принцип

Проект уже ведётся в стиле:

- `interfaces`
- `repositories`
- `controllers`
- `services`

Это важно сохранять. При доработках не стоит уводить бизнес-логику в шаблоны, `views.py` или произвольные хелперы без необходимости.

## Основные пользовательские потоки

### 1. Обычный пользователь

- регистрируется
- подтверждает email
- входит в аккаунт
- редактирует профиль
- ставит лайки и пишет отзывы
- может отправить заявку на управление карточкой

### 2. Владелец кружка

- после одобрения ownership-заявки получает доступ к управлению карточкой
- создаёт / редактирует карточки через owner-интерфейс
- карточки проходят модерацию
- видит статусы карточек и заявок

### 3. Модератор / админ

- работает в админке
- модерирует ownership-заявки
- управляет карточками
- видит аудит и структурированные разделы админки

## Важные бизнес-правила

- регистрация больше **не спрашивает тип пользователя**
- новая регистрация создаёт обычного пользователя
- ownership-заявку на карточку может отправить **любой авторизованный пользователь**
- после одобрения ownership-заявки пользователь автоматически получает owner-роль
- карточки не должны ломать существующие URL
- локализация должна быть полной, включая dynamic labels
- карта каталога и карточек зависит от наличия `lat/lng`

## Запуск локально

### Вариант 1. Через venv

```bash
cd /home/ramin/kidsmap
source .venv/bin/activate
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

### Вариант 2. Через Docker

```bash
cd /home/ramin/kidsmap
docker compose run --rm web ./scripts/release-server.sh
docker compose up -d --build
```

Обычный `docker compose` автоматически подключает `docker-compose.override.yml`: это dev-режим
с bind mount исходников, Django runserver и MariaDB на `127.0.0.1:3307`. Значения dev-секретов
задаются только override-файлом и не используются production-конфигурацией.

Production запускается только с базовым compose-файлом и заполненным `.env`:

```bash
docker compose -f docker-compose.yml build web
docker compose -f docker-compose.yml up -d db
docker compose -f docker-compose.yml run --rm web ./scripts/release-server.sh
docker compose -f docker-compose.yml up -d web
```

В production исходники не монтируются, БД не публикуется наружу, а постоянный каталог media
монтируется отдельно через `MEDIA_ROOT_HOST` (по умолчанию `./media`). Media должен отдавать
reverse proxy напрямую; `SERVE_MEDIA_FILES` оставьте равным `0`.
`DJANGO_SECRET_KEY`, `DB_PASSWORD` и `DB_ROOT_PASSWORD` обязательны и не должны быть placeholder-значениями.
HSTS preload намеренно выключен до отдельной проверки всех поддоменов.

## Основные env-переменные

Смотри [.env.example](./.env.example), но наиболее важные:

- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG`
- `DJANGO_ALLOWED_HOSTS`
- `DJANGO_CSRF_TRUSTED_ORIGINS`
- `DJANGO_ADMIN_HOST`
- `GOOGLE_MAPS_API_KEY`
- `GOOGLE_ANALYTICS_MEASUREMENT_ID`
- `GOOGLE_ANALYTICS_PROPERTY_ID`
- `GOOGLE_APPLICATION_CREDENTIALS`
- `EMAIL_*`
- `DB_*`

## Проверки перед любым push/deploy

```bash
cd /home/ramin/kidsmap
./.venv/bin/python manage.py check
./.venv/bin/python manage.py makemigrations --check --dry-run
./.venv/bin/python manage.py test
```

Для локальной и AI-проверки не обязательно гонять весь набор. Быстрые сьюты:

```bash
./scripts/run_kidsmap_tests.sh smoke
./scripts/run_kidsmap_tests.sh auth
./scripts/run_kidsmap_tests.sh public
./scripts/run_kidsmap_tests.sh admin
./scripts/run_kidsmap_tests.sh owner
./scripts/run_kidsmap_tests.sh catalog
./scripts/run_kidsmap_tests.sh full
```

Можно передавать дополнительные флаги дальше в `manage.py test`, например:

```bash
./scripts/run_kidsmap_tests.sh smoke --keepdb
```

Если менялись переводы:

```bash
./.venv/bin/python manage.py compilemessages
```

## Git flow

```bash
cd /home/ramin/kidsmap
git status
git add -A
git commit -m "Your message"
git push origin main
```

## Деплой на сервер

Подробный runbook лежит в [DEPLOYMENT.md](./DEPLOYMENT.md).

Короткий ручной сценарий:

```bash
ssh root@157.173.119.227
cd /opt/kidsmap
git stash push -m "before-deploy"
git fetch origin
git checkout main
git pull --ff-only origin main
docker compose build web
docker compose up -d db
docker compose run --rm web ./scripts/release-server.sh
docker compose up -d web
```

Smoke-check:

```bash
docker compose ps
curl -sS -L -o /dev/null -w '%{http_code} %{url_effective}\n' http://127.0.0.1:8000/
curl -sS -L -o /dev/null -w '%{http_code} %{url_effective}\n' http://127.0.0.1:8000/catalog/
curl -sS -L -o /dev/null -w '%{http_code} %{url_effective}\n' https://admin.kidsmap.az/ru/admin/login/
```

## Что важно не ломать

- публичные URL
- owner-flow
- мультиязычность
- media/display изображений
- карточки с уже существующими фото и данными
- админку и moderation flow

## Частые проблемные зоны

- локализация динамических значений
- mobile responsiveness
- карта и координаты
- корректность фильтрации каталога
- owner-кабинет и статусы карточек
- media/static cache после деплоя
- расхождения локалки и прод-сервера

## Для нового чата / нового ассистента

Если работа продолжается в новом чате, правильный prompt такой:

> Прочитай сначала `AI_HANDOFF.md`, потом кратко перескажи архитектуру и только после этого предлагай изменения.

Это позволяет новому ассистенту быстро понять:

- как устроен проект
- какие ограничения уже есть
- какие правила работы обязательны
- что обязательно проверять после правок
