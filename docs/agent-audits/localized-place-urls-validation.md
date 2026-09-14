# Языковые URL мест — итог локальной реализации

2026-09-14. Режим APPROVED LOCAL IMPLEMENT: пользователь согласовал план и поручил основательно реализовать локально, серверный этап отложен до предоставления доступа. LOCAL HEAD `ef91dbe761f340a2c4d37bdc0b96638522aa6edf`, изменения находятся в WORKTREE. Production UNKNOWN, не подключались. Commit/push/deploy не выполнялись.

## Результат

Реализованы отдельные устойчивые URL AZ/RU/EN, единый построитель ссылок, 301 со старых URL, canonical/hreflang/sitemap/IndexNow, readonly-блок адресов в staff/volunteer и обновление существующей инструкции для ИИ. Legacy slug и pricing API сохранены. Схема JSON не расширялась ради URL.

Новый slug появляется при сохранении названия, только если ещё не записан. Переименование, повторный импорт и конкурентное сохранение не заменяют ранее записанное значение. Чтение страницы и пересчёт рейтинга не генерируют URL. Отсутствующий перевод использует legacy fallback. Backfill сохраняет существующие AZ-адреса и заполняет RU/EN из имеющихся переводов, не вызывает ИИ.

В ходе проверки дополнительно исправлены две связанные проблемы: отсутствующие тарифы в частичном JSON больше не очищают существующие, а RU-подписи нового блока не попадают в fallback AZ. Сохраняется явное очищение через `[]` и преобразование старых числовых цен. Копирование/открытие использует настроенный публичный origin.

## Изменения и владельцы

- Root: `models/place.py`, новый `services/place_urls.py`, migration `0113_place_localized_slugs.py`, флаг в `config/settings.py`, backfill command, core/backfill tests, план и release/validation документы; финальная сверка и контраст URL.
- `admin_urls`, каноническая роль frontend-admin: endpoint/ACL, admin и volunteer шаблоны/JS/CSS, инструкция и импорт, защищённый snapshot, точечное разрешение preview в volunteer middleware, переводы AZ/RU/EN, admin tests.
- `seo_urls`, каноническая роль seo-reviewer: detail redirect/context, IndexNow lifecycle, SEO tests; независимая сверка core и regression на GET.
- `browser_urls`, каноническая роль browser-qa: Chromium, browser regression script и отдельный browser report.

Предшествовавшие изменения списков админки, поиска, публичной шапки, иконок и теста сортировки сохранены. Общий diff включает их, поэтому не считать весь WORKTREE результатом этой задачи. В пересекающемся `domain_admin/place.py` добавлен только связанный endpoint; чужие изменения не откатывались.

## Изоляция

Новый PostgreSQL17 tmpfs-контейнер `kidsmap-url-test-db`, только loopback55439. Отдельные БД для backend-тестов и браузера, для финального root-runner имя БД и media включает PID. Settings под `/tmp/kidsmap-url-tests/`, `env -i`, `DJANGO_TESTING=1`, LocMem cache/email, временный media, без внешних ключей аналитики/геокодирования. Существующие локальные БД и production не использовались. Браузерные данные полностью синтетические.

## Выполненные проверки

**Финальный общий прогон: 705 tests, OK, 231.580s, exit 0.**

```bash
/tmp/kidsmap-url-tests/run-tests test \
  catalog.testcases.test_localized_place_urls \
  catalog.testcases.test_localized_place_backfill \
  catalog.testcases.test_localized_place_seo \
  catalog.testcases.test_localized_place_admin \
  catalog.testcases.test_volunteer_json_prompt \
  catalog.testcases.test_volunteer_admin \
  catalog.testcases.test_indexnow \
  catalog.testcases.pricing_plans_relational \
  catalog.testcases.test_place_json_and_pricing_modes \
  catalog.testcases.catalog \
  catalog.testcases.public \
  catalog.testcases.owner \
  catalog.testcases.admin \
  catalog.testcases.test_json_roundtrip_audit --noinput
```

Wrapper запускает `.venv/bin/python -m django` из `/tmp` с `src` в PYTHONPATH и изолированными settings; структура описана в release document. Сырой синтетический test output хранится локально в `/tmp/kidsmap-url-tests/final-isolated-suite.log`, не добавляется в репозиторий.

Дополнительно:

- `check`: no issues; `makemigrations --check --dry-run`: no changes detected.
- Все миграции, включая0113, применены на пустой временной PostgreSQL-базе.
- `node --check` для нового URL JS, JSON importer и browser script: exit0.
- `msgfmt --check` для AZ/RU/EN: exit0. Переводы скомпилированы локально; штатный Docker/release pipeline уже содержит compilemessages.
- Scoped `git diff --check` и проверка whitespace новых файлов: PASS. Общий diff-check ранее отмечал чужую пустую строку EOF в `test_place_sorting_and_filtering.py`; её не меняли.
- Backfill на205 синтетических legacy drafts: dry-run205 кандидатов/0 записей; apply порциями100 —205 изменений/0 конфликтов; повторный dry-run0 кандидатов. AZ сохранён, остальные поля не массово переписаны.
- Браузер:75 сочетаний public/admin add/edit/volunteer add/edit ×AZ/RU/EN ×390/768/1024/1280/1440; canonical/hreflang, copy/reset, readonly URL, import/save/localStorage-clear/reload, старые301, сохранение URL и тарифные сценарии. Подробности и границы в browser report.
- После реального сохранения родитель отдельно проверил БД: все3 импортированных имени сохранены, все3 исходных slug не изменены.
- Финальный мобильный блок визуально проверен родителем; код адресов тёмный, измеренный контраст14.63:1. Более ранний пустой screenshot исключён из доказательств.

## RED → GREEN и исправления

1. До реализации тесты показали одинаковые окончания URL для всех языков; после модели/сервиса — правильные языковые пути.
2. Тесты backfill сначала показали отсутствие команды, затем проверили dry-run/apply/идемпотентность/продолжение.
3. Независимая сверка обнаружила генерацию URL на GET через refresh_rating_stats. Regression сначала зафиксировал изменение пустых slug, затем прошёл после ограничения генерации content-save.
4. PostgreSQL подтвердил проблему слишком длинного legacy slug; теперь он остаётся fallback без обрезки и ошибки сохранения.
5. Браузер воспроизвёл потерю тарифов при JSON только с названиями. Regression затем прошёл для отсутствующего списка, явного `[]` и старой числовой цены.
6. RU fallback и неправильный origin clipboard покрыты regression tests и финальной браузерной проверкой.

Один ранний ожидаемый русский slug в новом тесте был исправлен с `muzey` на `muzei` после проверки существующей таблицы: `й → i`; транслитерация приложения не менялась ради теста.

## Ошибки тестового окружения, не скрытые как PASS

- Первоначальный запуск `manage.py` из корня затенил `src/config` compatibility-пакетом. Wrapper переведён на `python -m django` с правильным import path.
- Раннее пересечение двух backend suites на одной тестовой БД вызвало deadlock при flush и ошибку счётчика админки. После уникальных имён тест отдельно и итоговый общий прогон прошли.
- Первый общий прогон703 завершился двумя map failures: браузерная fixture создала физическое фото в общем временном media, хотя тесты ожидали отсутствующий файл. Media разделён по PID; оба теста отдельно и итоговые705 прошли. Утверждения тестов не изменялись ради зелёного результата.
- Неполная синтетическая карточка сначала не сохранялась через админку. Fixture дополнена валидной локацией, таксономией, расписанием и тарифом; сохранение затем проверено с очисткой localStorage и чтением БД.

## Ограничения и следующий этап

Браузерные внешние интеграции блокировались; отсутствующий icon font давал overflow public1024. В отдельной проверке только шрифты разрешены; финальный повтор с загруженным шрифтом не воспроизвёл overflow. Это не всесторонняя offline/font-failure проверка публичной шапки. Реальный Google OAuth, карты, поисковое индексирование, другие браузерные движки и полный WCAG audit не заявляются проверенными.

Production migration/backfill, nginx/TLS/www, Search Console и конкретный recovery build остаются будущим серверным этапом. После публичной выдачи301 нельзя просто выключать feature flag или откатывать resolver на старый код — сохранить направление old→new и подготовить совместимое восстановление на staging.

Рекомендация: локальная часть готова; переходить к серверному release только после получения доступа и проверки фактической версии/данных. Порядок: [release](localized-place-urls-release.md). Браузерные детали: [browser report](localized-place-urls-browser.md).
