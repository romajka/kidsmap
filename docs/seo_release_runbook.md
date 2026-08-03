# KidsMap: release runbook первого технического SEO-пакета

Дата финальной локальной проверки: 3 августа 2026 года.

## Статус релиза

**READY FOR REVIEW.** Локальные release checks зелёные: public `194/194`, smoke
`22/22`, целевой SEO-suite `58/58`, Django system check и migration drift check
пройдены. Production deploy разрешён только после review, commit, push, backup
и отдельного подтверждения пользователя.

Перед публикацией учитывать два операционных ограничения:

1. В рабочем дереве есть посторонние `.swp`-файлы, а
   `scripts/publish-main.sh` выполняет `git add -A`. Этот скрипт нельзя
   использовать для текущего коммита без очистки staging-логики или явного
   исключения пользовательских файлов.
2. Перед reload nginx нужен настоящий `sudo nginx -t` на сервере. Локально nginx
   не установлен; выполнена только структурная проверка конфигурации.

## Необходимые environment variables

Все реальные секреты хранятся только в `/opt/kidsmap/.env`.

```dotenv
DJANGO_DEBUG=0
DJANGO_SECRET_KEY=<existing-production-secret>
DJANGO_ALLOWED_HOSTS=kidsmap.az,www.kidsmap.az,admin.kidsmap.az,127.0.0.1,localhost
DJANGO_CSRF_TRUSTED_ORIGINS=https://kidsmap.az,https://www.kidsmap.az,https://admin.kidsmap.az
DJANGO_ADMIN_HOST=admin.kidsmap.az
PUBLIC_BASE_URL=https://kidsmap.az

GOOGLE_ANALYTICS_MEASUREMENT_ID=<existing-GA4-measurement-id>
GOOGLE_SITE_VERIFICATION=<content-value-from-Google-or-empty>
BING_SITE_VERIFICATION=<content-value-from-Bing-or-empty>

INDEXNOW_KEY=<8-to-128-letters-numbers-or-hyphens>
INDEXNOW_ENDPOINT=https://api.indexnow.org/indexnow
INDEXNOW_TIMEOUT_SECONDS=3
INDEXNOW_MIN_INTERVAL_SECONDS=3600

DATABASE_URL=<existing-production-postgresql-url>
REDIS_URL=redis://redis:6379/0
```

Также должны остаться текущие production-переменные `DB_*`, `EMAIL_*`,
`DEFAULT_FROM_EMAIL`, `GOOGLE_MAPS_API_KEY`, cookie/security и media settings.
Не заменять рабочие значения шаблонными значениями из `.env.example`.

Google/Bing tokens необязательны для запуска приложения: при пустом значении
meta tag не выводится. `INDEXNOW_KEY` обязателен только для работы IndexNow.

## Preflight на рабочем компьютере

Не использовать `./scripts/publish-main.sh` и `git add -A`, пока в дереве есть
посторонние файлы.

```bash
cd /home/ramin/kidsmap
git status --short
git diff --check
./.venv/bin/python manage.py check
./.venv/bin/python manage.py makemigrations --check --dry-run
./.venv/bin/python manage.py compilemessages --ignore .venv --ignore venv
node --check static/js/ai_referral_tracking.js
node static/js/tests/ai_referral_tracking.test.js
./scripts/run_kidsmap_tests.sh smoke --verbosity 1
./scripts/run_kidsmap_tests.sh public --verbosity 1
```

Продолжать можно только при `0 failures, 0 errors`.

Перед коммитом использовать явный staging проверенного списка, а затем ещё раз
проверить его:

```bash
git add .env.example DEPLOYMENT.md deploy/nginx/kidsmap.az.conf docker-compose.yml \
  locale/az/LC_MESSAGES/django.po locale/en/LC_MESSAGES/django.po locale/ru/LC_MESSAGES/django.po \
  src/catalog/apps.py src/catalog/content_data.py src/catalog/context_processors.py \
  src/catalog/controllers/home_controller.py src/catalog/controllers/seo_controller.py \
  src/catalog/controllers/tracking_controller.py src/catalog/indexnow_signals.py \
  src/catalog/management/commands/submit_indexnow.py \
  src/catalog/middleware.py src/catalog/migrations/0081_add_ai_referral_event.py \
  src/catalog/models/category.py src/catalog/models/place.py src/catalog/models/site.py \
  src/catalog/services/indexnow.py src/catalog/services/public_urls.py \
  src/catalog/services/seo.py src/catalog/services/seo_landing_aggregates.py \
  src/catalog/services/seo_landing_visibility.py src/catalog/services/tracking.py \
  src/catalog/sitemaps.py src/catalog/templates/base.html \
  src/catalog/templates/catalog/includes/place_card.html \
  src/catalog/templates/catalog/place_detail.html \
  src/catalog/templates/catalog/seo_landing.html src/catalog/templates/pages/home.html \
  src/catalog/testcases/public.py src/catalog/testcases/tracking.py \
  src/catalog/testcases/test_ai_referral_tracking.py src/catalog/testcases/test_indexnow.py \
  src/catalog/testcases/test_judo_seo_landing.py \
  src/catalog/testcases/test_search_engine_verification.py \
  src/catalog/testcases/test_seo_landing_visibility.py src/config/settings.py \
  src/config/urls.py src/config/views.py static/css/site.css static/js/home_map.js \
  static/js/ai_referral_tracking.js static/js/tests/ai_referral_tracking.test.js \
  docs/ai_referral_analytics.md docs/search_engine_verification.md \
  docs/seo_indexation_audit.md docs/seo_release_runbook.md
git status --short
git diff --cached --check
git diff --cached --stat
git diff --cached --name-only
```

В staged-списке не должно быть `.swp`, `.env`, credentials JSON, дампов БД,
media или логов.

После отдельного разрешения пользователя:

```bash
git commit -m "seo: ship first technical package"
git push origin main
```

## Backup перед production deploy

```bash
ssh root@157.173.119.227
cd /opt/kidsmap
git status --short
git rev-parse HEAD
mkdir -p /opt/backups
date -u +%Y%m%d-%H%M%S
BACKUP_DIR=/opt/backups ./scripts/backup-db.sh
tar --create --gzip --file /opt/backups/kidsmap-media-before-seo.tar.gz -C /opt/kidsmap media
sudo cp --archive /etc/nginx/sites-available/kidsmap /opt/backups/kidsmap.conf.before-seo
gzip --test /opt/backups/kidsmap-db-*.sql.gz
ls -lh /opt/backups
```

Записать SHA из `git rev-parse HEAD`: это `PREVIOUS_COMMIT` для rollback.
Если server worktree не чистый, остановиться и разобрать изменения вручную.
Не полагаться вслепую на автоматический stash deploy-скрипта.

## Подготовка env

Новые переменные уже проброшены в сервис `web` через `docker-compose.yml`.
После заполнения `/opt/kidsmap/.env` проверить итоговую конфигурацию:

```bash
cd /opt/kidsmap
sudoedit /opt/kidsmap/.env
docker compose config > /tmp/kidsmap-compose-rendered.yml
grep -E 'PUBLIC_BASE_URL|GOOGLE_SITE_VERIFICATION|BING_SITE_VERIFICATION|INDEXNOW_' /tmp/kidsmap-compose-rendered.yml
```

Не публиковать вывод `docker compose config`: он может содержать секреты.
Проверять только наличие имён и непустых значений локально на сервере.

## Порядок deploy и миграции

После зелёных тестов, backup, push в `main` и отдельного подтверждения deploy:

```bash
ssh root@157.173.119.227
cd /opt/kidsmap
./scripts/deploy-server.sh main
docker compose exec -T web python manage.py showmigrations catalog
docker compose exec -T web python manage.py migrate --plan
docker compose exec -T web python manage.py migrate --noinput
docker compose exec -T web python manage.py collectstatic --clear --noinput
docker compose exec -T web python manage.py compilemessages
docker compose exec -T web python manage.py makemigrations --check --dry-run
docker compose exec -T web python manage.py check
docker compose ps
```

`deploy-server.sh` уже запускает release tasks, migrate, compilemessages,
collectstatic и check. Повторные команды выше — явная post-deploy верификация;
операции идемпотентны.

## Установка nginx-конфига

Не reload до успешного `nginx -t`.

```bash
cd /opt/kidsmap
sudo cp deploy/nginx/kidsmap.az.conf /etc/nginx/sites-available/kidsmap
sudo ln -sfn /etc/nginx/sites-available/kidsmap /etc/nginx/sites-enabled/kidsmap
sudo nginx -t
sudo systemctl reload nginx
sudo systemctl is-active nginx
```

Также проверить, что TLS-сертификат покрывает `www.kidsmap.az`; иначе браузер
увидит ошибку сертификата до получения 301.

## Smoke-check URL

```bash
curl -fsSI https://kidsmap.az/healthz
curl -fsSI https://kidsmap.az/
curl -fsSI https://kidsmap.az/ru/
curl -fsSI https://kidsmap.az/en/
curl -fsSI https://kidsmap.az/catalog/
curl -fsSI https://kidsmap.az/ru/catalog/
curl -fsSI https://kidsmap.az/en/catalog/
curl -fsSI https://kidsmap.az/ru/catalog/dzudo-dlya-detey-v-baku/
curl -fsSI https://kidsmap.az/sitemap.xml
curl -fsS https://kidsmap.az/robots.txt
curl -fsSI https://admin.kidsmap.az/ru/admin/login/
```

Ожидается `200` для публичных страниц и админ-логина. Лендинг дзюдо может быть
`noindex,follow`, пока по реальному фильтру меньше пяти качественных карточек.

## Проверка www 301

Команды запускать без `-L`, чтобы увидеть первый ответ:

```bash
curl -sSI http://www.kidsmap.az/
curl -sSI https://www.kidsmap.az/
curl -sSI 'https://www.kidsmap.az/ru/catalog/?category=SPRT&page=2'
```

Ожидается один `301` и соответственно:

```text
Location: https://kidsmap.az/
Location: https://kidsmap.az/
Location: https://kidsmap.az/ru/catalog/?category=SPRT&page=2
```

## Проверка canonical, hreflang, sitemap и structured data

```bash
curl -fsS https://kidsmap.az/ru/catalog/ | grep -E 'canonical|hreflang=|og:url'
curl -fsS https://kidsmap.az/ru/catalog/dzudo-dlya-detey-v-baku/ | grep -E 'robots|canonical|hreflang=|application/ld\+json'
curl -fsS https://kidsmap.az/sitemap.xml | grep -F 'https://www.kidsmap.az' && exit 1 || true
curl -fsS https://kidsmap.az/sitemap.xml | grep -F '<loc>https://kidsmap.az/' | head
```

Ожидается только `https://kidsmap.az`, полный набор `az`, `ru`, `en`,
`x-default`, корректный self-canonical и валидные JSON-LD блоки. Для
индексируемого лендинга ожидается `FAQPage` и `BreadcrumbList`; для каталога —
`ItemList`, для карточки — `LocalBusiness` и `BreadcrumbList`.

## Проверка IndexNow

Подставить реальный ключ только в shell на сервере, не в git и не в историю
команд общего доступа.

```bash
cd /opt/kidsmap
docker compose exec -T web python manage.py submit_indexnow --dry-run
curl -fsS "https://kidsmap.az/${INDEXNOW_KEY}.txt"
```

После отдельного разрешения на внешнюю отправку:

```bash
docker compose exec -T web python manage.py submit_indexnow --limit 1 --force
docker compose logs --since=10m web | grep -i indexnow
```

Ожидается HTTP `200` или `202` от API. Ошибка IndexNow не должна откатывать
сохранение карточки.

## Проверка Google и Bing

```bash
curl -fsS https://kidsmap.az/ | grep 'google-site-verification'
curl -fsS https://kidsmap.az/ | grep 'msvalidate.01'
```

Если соответствующая переменная пуста, отсутствие тега нормально. После
появления тегов нажать Verify в URL-prefix properties. Для Google Domain
property всё равно нужен выданный Google DNS TXT и отдельное разрешение на DNS.

Отправить один sitemap в оба кабинета:

```text
https://kidsmap.az/sitemap.xml
```

## Проверка AI referral tracking

1. Открыть страницу с `?utm_source=chatgpt` при пустом referrer.
2. В GA4 DebugView/Realtime найти `ai_referral_visit`.
3. Проверить параметры: только `ai_source`, `landing_path`, `page_type`,
   `language`.
4. Перейти внутри сайта и убедиться, что повторного landing event нет.

## Rollback

### Быстрый rollback приложения

Оставить применённую миграцию `0081`: она лишь синхронизирует choices поля и
совместима с предыдущим кодом. Срочно возвращать БД назад не требуется.

```bash
ssh root@157.173.119.227
cd /opt/kidsmap
git fetch origin
git switch --detach PREVIOUS_COMMIT
docker compose build web
docker compose run --rm web ./scripts/release-server.sh
docker compose up -d --no-deps web
docker compose exec -T web python manage.py check
docker compose ps
```

После стабилизации создать revert-коммит в `main`, push и вернуться на
нормальный branch-based deploy. Не оставлять production надолго в detached
HEAD.

### Rollback nginx

```bash
sudo cp /opt/backups/kidsmap.conf.before-seo /etc/nginx/sites-available/kidsmap
sudo nginx -t
sudo systemctl reload nginx
```

### Restore данных

Restore БД нужен только при подтверждённом повреждении данных, а не при обычной
ошибке шаблона или nginx. Он перезаписывает production-данные и требует
отдельного решения. Сначала остановить запись, выбрать точный backup и проверить
его `gzip --test`. Media восстанавливать из
`/opt/backups/kidsmap-media-before-seo.tar.gz` только при фактической потере
файлов.
