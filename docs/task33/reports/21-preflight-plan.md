# Stage21 — план возобновления после локального preflight

**Исторический план. Обновление2026-10-03:** WSL restart, Ubuntu24.04, local Docker и cached postgres image установлены; QA04 discovery/probe PASS, миграции161/0. Реализация21 выполнена локально и проходит финальную приёмку; актуальный verdict/evidence — [21.md](21.md). Описанные ниже environment blockers относятся к прежнему preflight.

2026-10-02, C:\kidsmap, task33-progress / 015d031d8eb17114bd860159dde805b38df3c13c. Авторизация только21 сохраняется. Это план разблокировки и проверки scope, не утверждение выполненной реализации.

## 1. Поднять обязательный изолированный harness

На preflight2026-10-02 WSL и Docker отсутствовали; Linux QA04 не работает на Windows путях. Обновление2026-10-03: WSL3.0.1 установлен, требуется Windows reboot, Ubuntu ещё не установлена. После reboot установить локальную Linux среду и Docker, загрузить postgres:17-alpine, создать Linux .venv по requirements.txt. Конкретные installation/checkout commands уже сохранены в `C:\kidsmap\scratch\task33-prepare-20261002\README.md`; Windows .venv и production .env не копировать в Linux. Использовать локальный Docker endpoint, Unix socket, network none, PGDATA tmpfs и текущие ownership guards. Не использовать project compose, рабочую/production DB или remote Docker.

В Linux checkout выполнить:

```bash
.venv/bin/python -m pip check
.venv/bin/python docs/task33/qa04/run.py --mode discovery --output "$(mktemp -d /tmp/task33-stage21-discovery-XXXXXX)"
.venv/bin/python docs/task33/qa04/run.py --mode probe --output "$(mktemp -d /tmp/task33-stage21-probe-XXXXXX)"
```

Перед реализацией: exit0 обоих launchers, checks.json PASS, migrations.json unapplied0, isolation.json expected booleans, run.json cleanup PASS. Failure fixture/application vs bootstrap классифицировать отдельно; не ослаблять safety guard/assertions. Версии будут отличаться от старого baseline04: записать фактические versions/image и fresh evidence. Сам probe не делает приложение GREEN.

## 2. Проверить существующие регрессии до изменения source

На текущем SHA выполнить bounded suite:

```bash
.venv/bin/python docs/task33/qa04/run.py --mode all \
  --label catalog.testcases.test_task33_public_details \
  --label catalog.testcases.test_localized_place_urls \
  --label catalog.testcases.test_localized_place_seo \
  --label catalog.testcases.test_seo_indexability \
  --label catalog.testcases.test_seo_landing_visibility \
  --output "$(mktemp -d /tmp/task33-stage21-before-XXXXXX)"
```

Сохранить IDs/counts/exception classes и существующие failures до реализации; ни один historic report не считать новым запуском. Discovery1546 в native preflight — количество найденных tests, не executed tests.

## 3. Source boundaries и RED/GREEN для21

После доступности harness написать meaningful PostgreSQL integration tests для следующих точных требований; сначала увидеть RED на старом source, затем минимально изменить production paths.

| Требование | Проверяемая boundary / возможные файлы | Приёмка |
|---|---|---|
| Approved AZ обязателен только новой публикации | services/publication.py, place_readiness.py и действующий approved presentation; сначала проверить существующий контракт | New AZ missing rejected; legacy published retained; RU/EN missing не блокирует |
| Translation display и indexability | public_presentation.py, context_processors.py:seo_urls, place_urls.py | AZ-only и partly RU → AZ canonical; не объявлять неполный перевод hreflang/sitemap; complete RU/EN имеют взаимные альтернативы и self canonical |
| Legacy paths/ID/reviews/media | services/slugs.py, place_urls.py, views.py:place_detail(_legacy), public middleware | Existing ID/slug сохранены; old URL301 прямо на same-language current URL, без цепочки; reviews/media доступны |
| Organization/Activity approved facts | controllers/public_details.py и services/seo.py | Title/description/JSON-LD only approved visible presentation; no Org aggregate rating, invented dates/location; draft/pending не утекли |
| Sitemap | sitemaps.py:LocalizedSitemap/PlaceSitemap, config/urls.py registry | Entry только для содержательных переводов и реально public entities; no hidden/draft; не менять языки статических страниц по правилам карточек |
| Historical closed Place | views.py/detail resolver и каталог/карта readers | Detail200 с честной отметкой; отсутствие в ordinary list/map; no массовый noindex |
| Safe script serialization | seo.py:_serialize_json_ld и actual templates | malicious </script>, <, >, & roundtrip сохранён без script termination; actual browser head проверен |
| Locale не меняет facts | approved presentation/pricing/groups | Currency/geography/class language одинаковы на AZ/RU/EN; только текст оболочки локализуется |

Действующий `seo_urls` не учитывает completeness: native synthetic AZ-only Place на RU даёт canonical RU и три alternatives. Это воспроизведённый pre-existing gap, первая concrete RED цель; см.21-results.json. Existing `_serialize_json_ld` уже экранирует `<`, `>`, `&`: сохранить helper, покрыть actual rendering, не вводить второй serializer.
Проверенные source observations: Organization/Activity detail сейчас возвращают title/description без entity JSON-LD; PlaceSitemap наследует общую i18n генерацию; `place_paths_by_language` возвращает три URL независимо от перевода. Окончательное решение о completeness должно использовать approved backend text, не slug presence и не client rules.

## 4. Acceptance перед DONE

На final source выполнить новый stage21 bounded suite + соседние регрессии, checks/migration consistency; новый QA label добавить после фактического создания tests и свежего discovery. Реальный локальный browser на isolated synthetic PostgreSQL: AZ/RU/EN ×320/360/390/768/1024/1280/1440, visible fallback/head/canonical/hreflang/JSON-LD, malformed text и archived detail/legacy URLs. Browser transport doubles отдельно от external Maps/CDN evidence.
Независимый реальный reviewer с canonical definition и bounded ownership проверяет final SHA/SEO/security/compatibility и собственные evidence. Self-review не считать независимым. Только после всех criteria обновить21 на DONE; иначе BLOCKED/REVIEW_PENDING с exact остатком.
Stage22+, full production/SEO audit-fix state-writing commands/commit/push/merge/deploy остаются NOT_RUN. Возобновление21 не требует повторного approval текущего scope.
