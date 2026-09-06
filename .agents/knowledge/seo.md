# SEO KidsMap

Срез: 2026-09-06, источник AS-IS — source files. Local dirty и production `86a0b8c` не одна версия.
Связанные карты: [source-of-truth.md](source-of-truth.md), [public-ui.md](public-ui.md), [security.md](security.md).

## Источники истины

| Контракт | Source |
| --- | --- |
| Canonical/locale alternates/robots | `src/catalog/context_processors.py:116–164` |
| Head rendering | `src/catalog/templates/base.html:16–22`, `:31` |
| Canonical origin/query cleanup | `src/catalog/services/public_urls.py`; `src/catalog/middleware.py:22`, `:52` |
| Organization/WebSite | `src/catalog/services/seo.py:193` |
| Home/catalog metadata/schema | `seo.py:226`, `:252` |
| Place LocalBusiness | `seo.py:359`, `:396` |
| Offers/schedule/geo | `seo.py:415`, `:465`, `:506` |
| SEO landing | `services/seo_landing_visibility.py`, `seo_landing_aggregates.py`, `controllers/seo_controller.py` |
| Sitemap | `src/catalog/sitemaps.py`; registration `src/config/urls.py:21` |
| Public inclusion | `src/catalog/services/content_quality.py:public_place_queryset` |
| Audit models/engine | `src/catalog/models/seo.py`; `src/catalog/services/seo_audit_engine.py` |
| Fix/rollback engine | `src/catalog/services/seo_fix_engine.py` |

Сокращённые services/controllers и seo.py пути относятся к `src/catalog/`.

## Реализованные правила

- AZ default без префикса, RU/EN с префиксом; canonical строится через public absolute URI.
- Alternates создаются в context processor; x-default указывает default language.
- NOINDEX_URL_NAMES и query noindex policy находятся в context processor; не сочинять вторую политику в шаблоне.
- LocalizedSitemap включает i18n/alternates/x-default: `sitemaps.py:14`.
- Place sitemap берёт `public_place_queryset`, не все status=published записи: `:56`.
- SEO landing sitemap использует threshold/indexable_slugs: `:66`.
- Specialists sitemap учитывает feature flag: `:89`.
- Place JSON-LD LocalBusiness использует реальные relational pricing plans, только active primary: `seo.py:466`.
- On-request offer не превращается в выдуманную нулевую цену; free fallback учитывает price_mode.
- OpeningHoursSpecification зависит от schedule_mode и relational days/intervals.
- Events: есть public detail/title/description, но Event schema и EventSitemap не обнаружены.

## Критический режим аудита

Название management command не гарантирует read-only.

- `SEOAuditEngine.run_audit`: `seo_audit_engine.py:49` создаёт SEOAuditRun, `:83` записывает issues, `:100` сохраняет run.
- Использует Django test Client `:32`, `:113`: это app-level rendering, не внешний nginx/TLS/browser audit.
- `SEOFixEngine`: даже dry-run может создавать SEOChange (`seo_fix_engine.py:110`) и обновлять issue (`:127`).
- Поэтому `audit_seo`, `apply_seo_fixes`, `ci_seo_check.sh`, SEO admin actions не запускать на production в этой read-only фазе.
- Безопасный audit: source inspection, ограниченные SELECT, HTTP GET/HEAD, чтение уже существующих отчётов без копирования private data.
- Tests/audit commands выполнять только на изолированной тестовой DB при соответствующем разрешении workflow.
- Не применять автоматически предлагаемые SEO fixes/rollback: они меняют состояние.

## Подтверждённые риски

| Приоритет | Наблюдение | Уверенность/границы |
| --- | --- | --- |
| P1 | Обычный json.dumps + safe внутри JSON-LD позволяет `</script>` закрыть тег | Высокая; isolated Django render, без prod exploit |
| P2 | Event detail без Event JSON-LD и отдельного sitemap | Высокая по source; impact зависит от enabled section |
| P2 | Команды audit/dry-run пишут DB | Высокая; operational constraint |

JSON-LD источники: `seo.py:537`, `:221–222`, `:595`; sinks: `place_detail.html:12–13`, `base.html:89/:92`, `seo_landing.html:145–146`.
Place name включён `seo.py:397`; owner names проходят strip (`forms.py:1430`), что не защищает script raw-text context.
Изолированный render подтвердил дополнительный executable script tag; публикационный/access путь должен отдельно подтвердить security review.
Нужен единый безопасный JSON-LD serializer и regression; HTML escaping всего JSON не заменяет корректную JSON/script serialization.

## LOCAL и документация

- В discovery diff `src/catalog/services/seo.py` содержит только удаление telephone из schema для local phone reveal.
- Это не исправляет описанный JSON-LD sink и не означает, что telephone удалён с production.
- `docs/seo_indexation_audit.md`, `seo_release_runbook.md`, `search_engine_verification.md` — исторические проверки/runbooks.
- Сверять их URL/threshold/features с кодом и текущим production; старые результаты не являются новым PASS.
- `docs/PERMANENT_PLACE_FIELD_MATRIX.md:119` различает фактические price modes и ожидаемые режимы; SEO не должен добавлять несуществующие семантики.

## Verification/handoff

- Проверить title/meta/canonical/hreflang/robots для AZ/RU/EN, filters/query/pagination, slug redirect и404.
- Сопоставить sitemap/public visibility/detail доступ; draft/deleted/disabled не должны попадать по обходному пути.
- JSON-LD должен соответствовать видимому контенту, реальным ценам, времени, контактам, отзывам.
- После изменения public models/pricing/schedule обязательны backend→SEO→QA handoff.
- Suites: `test_seo_audit_system.py`, `test_seo_landing_visibility.py`, `test_judo_seo_landing.py`, соответствующие pricing/content tests в `src/catalog/testcases/`.
- В первый source audit внешняя rich-results validation и полный crawl не выполнялись; не обещать индексацию/позиции.
