# SEO source audit — 2026-09-16

Роль: seo-reviewer (`.agents/agents/seo-reviewer/agent.md`), execution identity `/root/seo_source`. Режим AUDIT ONLY. Отдельное поручение orchestrator: sitemap, robots, canonical, hreflang, indexability локального кода. Разрешены чтение и этот отчёт; приложение и сервер не изменялись.

**Snapshot:** LOCAL HEAD `01d330ba97397951d7f493670573391708436393`. При запуске `git status --short` пуст; перед отчётом `git diff --stat` пуст. Текущая PRODUCTION версия этим исполнителем не проверялась. Все выводы ниже — LOCAL, пока orchestrator не сопоставит с сервером/HTTP.

## Подтверждённая реализация

- `src/catalog/sitemaps.py:14`: локализованные sitemap entries, alternates и x-default; origin берётся из PUBLIC_BASE_URL. Place sitemap использует public quality queryset (:56–63). SEO landing sitemap включает только пригодные страницы (:66–86).
- `src/catalog/services/seo_landing_visibility.py:15`: минимум **5** публичных мест; :124–142 требует общего slug и достаточного количества во всех языках. `controllers/seo_controller.py:47` ставит noindex слабым страницам. Это намеренное ограничение, а не автоматически ошибка.
- `src/catalog/context_processors.py:121`: canonical/hreflang; для Place используются реальные языковые slug (:143–150). `templates/base.html:16–22` выводит robots, googlebot, canonical, hreflang и x-default.
- `services/place_urls.py:16–31`: переключатель LOCALIZED_PLACE_URLS_ENABLED управляет локализованными slug; :24 строит языковой URL. `models/place.py:581` использует этот helper. `views.py:394–400` делает permanent redirect неверного slug и задаёт Place для canonical.
- `src/config/views.py:76–121`: публичный crawl разрешён, закрываются admin/auth/account/служебные действия; объявлен sitemap. `middleware.py:15` канонизирует www, :51 очищает чужие query params; `config/views.py:128` переводит /az/ в AZ URL без префикса.
- Историческую проблему JSON-LD из сентябрьских knowledge-файлов **нельзя повторять как актуальную**: `services/seo.py:16–22` теперь экранирует `<`, `>` и `&` через serializer. Это source-наблюдение, не полный security audit и не runtime test.

## Findings и решения

### SEO-SRC-01 — P2: sitemap исключает больше карточек, чем публичный detail

**Evidence:** `src/catalog/controllers/place_controller.py:793–805` получает detail через `published_place_queryset`; `services/content_quality.py:355–362` требует только published, active, not-deleted. Sitemap в `sitemaps.py:60` использует `public_place_queryset`, где добавлены качество, расписание, цена, описание, возраст, feature flag событий и срок temporary event (`content_quality.py:236–280`). Чистый place_detail не noindex в `context_processors.py:154–158`; detail template/controller не переопределяют robots.

**Следствие:** карточка может отсутствовать в sitemap/каталоге, но оставаться доступной и индексируемой по старой ссылке. Это объясняет возможные «лишние URL сайта»; оно НЕ объясняет само по себе чужие snippets Turbo/Instagram. Совместимость опубликованных карточек может быть намеренной; автоматический 404 не рекомендован.

**Уверенность:** высокая по коду; наличие таких карточек в текущей production БД UNKNOWN. **Проверка:** агрегат published-minus-public, отдельно expired temporary/feature-disabled; затем несколько публичных HTTP heads. **Решение:** согласовать продуктовую политику — сохранять полезные detail URL либо noindex/архив для действительно непригодных. **Owner:** django-reviewer + seo-reviewer; acceptance: согласованные catalog/detail/sitemap/robots состояния.

### SEO-SRC-02 — P2, policy review: пагинация каталога объединена с поисковыми фильтрами

`services/public_urls.py:13–24` разрешает page; `context_processors.py:137` строит canonical только из path, :157–158 ставит noindex при любом query на place_list/place_new/site_reviews. Следовательно, `/catalog/?page=2` получает canonical `/catalog/` и noindex на уровне исходного кода. Аналогично RU/EN.

Не доказано, что Google потерял карточки: они отдельно присутствуют в sitemap. Но страницы пагинации имеют другой набор карточек; политику page следует отделить от произвольного q/filters и проверить внутреннее обнаружение глубоких карточек. **Уверенность:** высокая для source, влияние на реальные позиции UNKNOWN. **Owner:** seo-reviewer; acceptance: отдельная политика pagination и filters, проверенная по живому HTML.

### SEO-SRC-03 — P3: публичный FAQ отсутствует в статическом sitemap

Маршрут `/faq/` есть в `src/catalog/urls.py:91`, но `StaticViewSitemap.items` (`sitemaps.py:33–50`) его не содержит. Это не запрещает индексацию через внутренние ссылки. После проверки ценности страницы добавить все языковые FAQ в sitemap — небольшой будущий change. **Уверенность:** высокая; **owner:** seo-reviewer.

### SEO-SRC-04 — P2 условно: Event detail без Event sitemap/schema

`src/config/urls.py:21–26` регистрирует static/places/seo/specialists, но не Events. `views.py:1226–1250` показывает опубликованный актуальный Event и передаёт title/description, но не Event JSON-LD; `templates/catalog/event_detail.html:1–9` не добавляет schema block. Feature-disabled возвращает 410. **Impact:** упущенная явная подача Event URL и структурированных данных, если существуют публичные Event. Наличие/число таких Event в production UNKNOWN; при выключенном разделе низкий приоритет. **Owner:** django-reviewer + seo-reviewer.

### SEO-SRC-05 — P3: неодинаковая query-indexability разных каталогов

`public_urls.py:19–23` разрешает фильтры events_landing и specialist_list, но их нет в `QUERY_NOINDEX_URL_NAMES` (`context_processors.py:81–86`). Их шаблоны не переопределяют robots. По source фильтры этих списков получают index и canonical чистого списка, тогда как Place-фильтры noindex. Это не само по себе авария; требуется единая сознательная политика при включении разделов. **Уверенность:** высокая по inspected source; feature-state UNKNOWN. **Owner:** seo-reviewer.

## Что проверить в production (handoff)

1. Совпадение deployed HEAD и указанных файлов, PUBLIC_BASE_URL/locale/feature flags — только booleans/без секретов в отчёте.
2. Все `<loc>` из live sitemap: status, redirect target, canonical, meta robots/googlebot, X-Robots-Tag, title, language; отдельно взаимность alternate URL. Проверка HTTP-доступности не равна проверке Google index.
3. `/`, `/ru/`, `/en/`, `/az/`, www/http redirects, `/catalog/?page=2`, поисковые фильтры, `/faq/`, 404, старый slug и актуальный языковой slug.
4. Агрегат published-minus-public для SEO-SRC-01, без выгрузки приватных записей.
5. GSC Page indexing + Sitemaps + URL Inspection для выбранных исключений; только доступ к GSC позволяет подтвердить Google-selected canonical/last crawl/index state по URL. Без него статус «все ссылки проиндексированы» недоказуем.

## Проверки и ограничения

Executed: `git rev-parse HEAD`, `git status --short`, `git diff --stat`; source reads `cat`, `nl -ba`, `sed -n`, bounded `rg` по перечисленным файлам; Codebase Memory `list_projects`, `index_status`, `get_architecture`, `search_graph`, `check_index_coverage`.

Memory project `/home/ramin/kidsmap`, generation `2026-09-15T06:33:48Z`, full, metadata matches для checked paths. `base.html`, events_landing.html и specialist_list.html имеют parser partials; критические выводы проверены direct source, не отсутствием в графе. Один probe несуществующего `src/catalog/repositories/place_repository.py` вернул file-not-found; правильный detail caller подтверждён в controller. Никакого отрицательного вывода из этого probe не делалось.

NOT RUN: Django/application tests, DB queries, production connection, browser render, внешняя индексация/GSC, management SEO audit/fix commands. Тестовая БД не создана. Это bounded source audit, не полный security/performance review.

Operational caution: `services/seo_audit_engine.py:49,69,83,100` создаёт/удаляет/сохраняет audit records; `seo_fix_engine.py:110–127` пишет changes/issues. Команды audit/dry-run не запускать на production в этой фазе.

Changed: только этот отчёт. DB impact: none. Security impact: no writes/secrets copied. P0/P1 по этому ограниченному исследованию не установлены.

**Named handoff: kidsmap-orchestrator** — объединить local findings с собственными HTTP/server/GSC evidence, явно отделить подтверждённые live проблемы от условных улучшений. После решения пользователя seo-reviewer + django-reviewer могут реализовать конкретный согласованный scope; сейчас исправления не выполнялись.

## Дополнение orchestrator (получено после source review)

Root сообщил: live server clean HEAD совпадает `01d330b`; active-container hashes sitemaps.py/context_processors.py/content_quality.py совпадают с local. Read-only DB агрегаты: Place total 339, active published not-deleted 75, temporary 0; live sitemap 270 URL, из них 225 Place (=75×3), 30 static, 15 landings. Это **полученное от root evidence**, не самостоятельное подключение этого агента. При подтверждении уникальности 75 Place IDs SEO-SRC-01 имеет **latent**, а не текущий массовый impact; не выдавать его за причину нынешней поисковой проблемы. Точное равенство множеств должен завершить orchestrator.
