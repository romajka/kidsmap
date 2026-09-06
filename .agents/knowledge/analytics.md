# Analytics KidsMap

Срез: 2026-09-06. Значимый существующий слой; analytics-reviewer сохраняется как отдельный специалист.
Local dirty snapshot и production `86a0b8c` различаются: [deployment.md](deployment.md).
Source events и фактическая доставка GA4 — разные уровни доказательств.

## Архитектура

| Слой | Источник |
| --- | --- |
| Имена событий | `src/catalog/services/tracking.py:15` TRACKED_EVENT_NAMES |
| Conversion subset | `tracking.py:33` GA4_CONVERSION_EVENT_NAMES |
| Event service/storage gate | `tracking.py:144`, `:167` |
| Queue across redirects | `tracking.py:123`, `:136` |
| Endpoint controller | `src/catalog/controllers/tracking_controller.py` |
| Repositories | `src/catalog/repositories/tracking_repositories.py` |
| Models | `src/catalog/models/site.py:543` SiteVisit, `:570` FunnelEvent |
| Public GA enablement | `src/catalog/context_processors.py:177` |
| Client bridge/beacon | `src/catalog/templates/base.html:876`, `:893` |
| Server list/detail events | `src/catalog/controllers/place_controller.py:681`, `:874` |
| AI referral detection | `static/js/ai_referral_tracking.js` |
| GA reporting | `src/catalog/services/google_analytics_reporting.py:60` |
| Dashboard mapping | `src/catalog/services/admin_analytics.py:60` |
| Admin surface | `src/catalog/domain_admin/site.py:480`; `templates/admin/catalog/site_analytics.html` |

Сокращённый `tracking.py` относится к `src/catalog/services/tracking.py`.

## Реализованный event contract

- Catalog search/filter, place_open, call/WhatsApp/Instagram CTA, favorite/review, claim start/submit, add-place signup start/complete, ai_referral_visit.
- Полный список и spelling брать из TRACKED_EVENT_NAMES; не создавать параллельный справочник в агенте/JS.
- GA config внедряется в `base.html:39–45`; события вызывают существующий window bridge.
- DEBUG/local/test hosts отключают GA: `context_processors.py:180` и tests/tracking.
- LOCAL_ANALYTICS_STORAGE_ENABLED управляет внутренней записью; отсутствие rows не доказывает отсутствие GA событий.
- Beacon/fetch endpoint и GA emission — отдельные каналы; успешный204 endpoint не доказывает получение GA.
- Conversion здесь — отправленное событие; звонок по CTA не равен подтверждённой продаже/записи.

## Privacy/data boundaries

- Catalog search записывает query_len (`tracking.py:209`), а не raw свободный поисковый текст.
- Обычные локальные funnel events могут иметь user/session (`tracking.py:170–179`): не называть весь слой анонимным.
- AI referral путь нормализуется отдельно (`tracking.py:267`) и создаётся без user/session (`:303–307`).
- AI event содержит source, landing_path, page_type, language; не полный referrer/URL/query.
- Не добавлять email/телефон/имя/свободный текст/секреты в GA params или audit reports.
- Не выводить service-account JSON, credentials path/value или tokens при диагностике подключения.
- `GOOGLE_ANALYTICS_*`, Maps и OAuth Client — независимые конфигурации.

## Подтверждённые проблемы и риски

| Приоритет | Finding | Уверенность |
| --- | --- | --- |
| P2 | Dashboard90 дней использует year KPI | Высокая, committed source |
| P2 | GA reporting делает7 sync report calls, без локального cache/explicit timeout | Высокая по source; задержка не измерена |
| P2 | JS/browser checks отсутствуют в CI | Высокая |

Период: `site_analytics.html:21` предлагает90; `admin_analytics.py:37–42` мапит >30 в year; `google_analytics_reporting.py:65` year=364daysAgo.
При этом period_start в `admin_analytics.py:65` исчисляется от90. Это несоответствие выбранному периоду, а не доказанная неправильность GA данных.
Chart/top pages/events явно имеют фиксированные30 дней (`google_analytics_reporting.py:176/:193/:222`); не смешивать этот подписанный режим с KPI bug.
Sync calls: build_snapshot `:108–112`; period loop `:155`; `run_report(request)` `:151`.
Нужны точный range contract и test90; performance рекомендация требует измерить latency/квоту прежде оптимизации.

## LOCAL изменения и границы AS-IS

- Phone reveal создаёт CTA links после успешного reveal: local `static/js/place_phone_reveal.js:41`.
- Phone/photo/auth/wizard файлы на момент discovery dirty/untracked; не считать production funnel уже изменённым.
- `docs/ai_referral_analytics.md` описывает реализованные payload и ручную GA custom-dimension настройку.
- Наличие docs не доказывает, что dimensions/Realtimes/property настроены в текущем GA account.
- Это аудит реализации; получение GA credentials и изменения property не входят в read-only scope.

## Проверки и безопасный audit

- `node static/js/tests/ai_referral_tracking.test.js` выполнен при discovery: `AI referral tracking tests passed`, exit0.
- Django suites: `src/catalog/testcases/tracking.py`, `test_ai_referral_tracking.py`; dashboard tests в `admin.py:835/:866`.
- Dashboard tests mock GA context; отдельного доказательства корректности90→range mapping в них нет.
- `.github/workflows/deploy.yml` запускает Django checks/tests, не JS test и browser scripts.
- Browser verification: один пользовательский action→одно ожидаемое событие; desktop/mobile/back-forward/retry; проверить GA bridge и local endpoint отдельно.
- Проверять неуспешные действия, duplicate handlers, source/place/language, queued redirects и local-storage disabled.
- На production не создавать специально synthetic CTA/conversions и не менять GA property ради read-only audit.
- Использовать source/существующие агрегаты; browser instrumentation и POST scenarios — на isolated test instance.
- GA Realtime/DebugView/Network в discovery не проверены; не объявлять delivery/funnel PASS по unit tests.
