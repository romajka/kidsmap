# KidsMap: карта фактической архитектуры

> Актуализация 2026-09-08: [current snapshot](current-snapshot.md) уточняет LOCAL HEAD, volunteer workspace, MCP и native agents. Текст ниже — датированный срез 2026-09-06; production факты и untracked/dirty пометки не описывают сегодняшнее состояние. Перед использованием перепроверить source.

Срез: 2026-09-06. Источник AS-IS — код и read-only наблюдения; документация проверяется по ним. Карта подготовлена **до** консолидации ролей. Навигация: [source-of-truth](source-of-truth.md), [database](database.md), [deployment](deployment.md), [testing](testing.md).

## Три разных состояния

| Срез | Факт | Как использовать |
|---|---|---|
| LOCAL HEAD | `main`, `df6fef3784a6bae6b7ddce90cd41a392d9f9e6bf` | Коммиты после production в основном добавляют agent configuration; не доказывают наличие текущих незакоммиченных функций на сервере |
| LOCAL WORKTREE | Изменённые формы, readiness/wizard, photos, phone reveal, карты, auth, settings, Docker/nginx; untracked Google OAuth и migration0101 | Анализировать diff отдельно; не переносить состояние на production |
| PRODUCTION | `/opt/kidsmap`, clean `86a0b8cf64a8835f310a608a3428c60f1fc5341a`, branch `readiness-legacy-migration` | Django6.0.2/Python3.12.13, PostgreSQL17.10, catalog migrations до0100 |

Google release image был отдельно подготовлен в предыдущей задаче, но **не активирован**. OAuth client не создан, duplicate email preflight блокирует0101. Эта задача не разрешает продолжать deployment.

## Backend и данные

- Основной Django app — `src/catalog`; установлен `catalog.proxy_apps.catalog_moderation`, Django contrib и Jazzmin. Google allauth — дополнение LOCAL WORKTREE. Другие proxy packages на диске не означают installed apps.
- `src/config` — действительная конфигурация; корневой `config` и `catalog/admin.py` — используемые compatibility facades. Не поддерживать вторую реализацию в обёртках.
- `models/place.py`: Place, ScheduleDay/Interval, Event, photos, likes. Place.category — FK на Category.code с физической колонкой `category`; это не integer FK. Place district/metro — строки; Specialist location использует отдельные Region/District/MetroStation связи.
- `models/pricing_plan.py`: relational PricingPlan + constraints/indexes; `Place.pricing_plans` сохраняет fallback на физический JSON `pricing_plans`; scalar prices также используются. Production266/321 Place имеют scalar prices без relational plans: удалять их нельзя.
- `models/owner.py`, `user.py`, `review.py`, `specialist.py`, `site.py`, `seo.py` покрывают ownership/team, stock User profile/OTP, отзывы, специалистов, аналитику и SEO audit history.
- HTTP слой смешанный: `views.py` → controllers → use_cases/repositories/services, но direct ORM и бизнес-правила также есть в admin/models/views. Не объявлять проект полностью реализующим repository pattern.

## Критические потоки

1. **Публикация Place:** owner/admin form → validation → `place_readiness`/quality → сохранение/moderation/audit. Существующая опубликованная legacy-карточка имеет намеренный compatibility path. Public visibility — отдельный SQL contract, не идентичен новым publication requirements.
2. **LOCAL divergence:** owner wizard использует `permanent_place_rules`, а admin — `place_readiness`; требования к120 символам и бесплатным режимам расходятся. Не превращать этот конфликт в новую норму агента.
3. **Pricing:** normalize payload → relational replacement → scalar projections/signals → public summary; legacy JSON/text/scalars живы. Migration ambiguity → manual_review.
4. **Schedule:** пять режимов (включая always_open), structured days/intervals и text fallback; malformed JSON handling требует отдельной проверки.
5. **Доступ:** `place_access` проверяет конкретное место, owner/creator fallback, активную team membership и Django permissions. Global owner-role у UserProfile больше нет (0097).
6. **Auth:** stock User/ModelBackend, inactive password signup + OTP, существующий reset/session/profile. LOCAL Google bridge использует allauth state/PKCE и явную identity policy; local implementation ≠ live capability.
7. **Events:** временный Place и отдельный Event — два существующих пути; не подменять один другим. Production0 Event и0 temporary Place на срезе.
8. **Media:** общая image normalization, owner/admin uploads; private SpecialistDocument route имеет ACL, но общий media serving требует security review. Production0 SpecialistDocument, утечка реальных документов не доказана.

## Frontend, SEO, analytics

- SSR public: `src/catalog/templates/base.html`, `catalog/`, `pages/`; vanilla JS/CSS и карты. AZ без prefix, RU `/ru/`, EN `/en/`. Locale/next/canonical должны согласовываться.
- Admin: корневые `templates/admin` + app overrides `templates/admin/catalog`, `static/admin`, `domain_admin`; Jazzmin. Presentation отдельно от save/moderation semantics.
- SEO: `services/seo.py`, context processors/public_urls/middleware, sitemaps, robots, JSON-LD и отдельный audit/fix subsystem. Команды SEO audit/fix записывают БД даже в некоторых dry-run сценариях.
- Analytics: GA4 browser events и synchronous admin reporting; FunnelEvent/SiteVisit/AI referrals. Отдельная роль оправдана реальным объёмом. Не фабриковать отчёт при отсутствии GA credentials.

## Infrastructure и QA

- nginx → host8000 → Docker Gunicorn; PostgreSQL и Redis — отдельные контейнеры. `/app/media` и `/app/staticfiles` bind mounts; исходники в image, не bind-mounted. Нет обнаруженного отдельного Uvicorn/Celery/RQ runtime.
- IndexNow использует process-local ThreadPoolExecutor/on_commit, а не durable background queue. Management commands/cron — отдельные операционные пути.
- GitHub workflow выполняет Django checks/migrations/tests на PostgreSQL17+Redis, затем deploy-server при push main. Нет подтверждения последнего CI run и browser job.
- `catalog/tests.py` + domain testcases + standalone test modules; custom runner сбрасывает cache/language. Всегда `DJANGO_TESTING=1` и изолированная DB; production тесты запрещены.
- 186 тестов Google/auth/reset/owner ранее прошли на отдельном PostgreSQL17 release image (не полном текущем dirty tree). Исторические baseline failures и свежие проверки — разные доказательства.

## Статус документов

- `AI_HANDOFF.md` содержит устаревшее утверждение о global owner role.
- `PERMANENT_PLACE_FIELD_MATRIX.md` полезен как локальное требование/история, но утверждения об отсутствии price_mode/readiness и четырёх schedule modes противоречат source.
- `DEPLOYMENT.md` содержит старые MariaDB/service/backup примеры. Проверять по compose/scripts и live runtime.
- Design handoffs/plans — TO-BE/PLANNED, пока каждый пункт не подтверждён кодом и проверкой.

## Границы выводов

Codebase Memory не объявлен в repository MCP config и не доступен среди callable tools этой сессии; установка не выполнялась. Наличие MCP JSON — декларация, не доказательство подключённого инструмента. Отчёты не заменяют workload profiling, восстановление backups в текущем аудите, private admin browser QA или external Google/GA проверки.
