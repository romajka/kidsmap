# Старые ссылки карточек: локальное исправление

Дата: 2026-10-09. Исполнитель: Codex /root, последовательно, без независимых агентов.
Авторизация: пользователь подтвердил локальные 301 для старых адресов, AZ/RU/EN, отсутствие циклов и 404 для непубличных/удалённых карточек.
Срез: LOCAL HEAD `2da9d33a`, `task33-progress`, dirty WORKTREE. `active_run: NONE` при preflight; этапы Task33 не запускались. Production revision UNKNOWN.

## Подтверждённая причина

Search Console (прочитан 9 октября, обновление отчёта 4 октября): 442 адреса с 404. Проверенные примеры имеют старый корневой формат `/<id>-<slug>/`.
`https://kidsmap.az/ru/67-bakinskiy-klub-edinoborstv/` возвращает 404, а актуальный `https://kidsmap.az/ru/place/67-bakinskii-klub-edinoborstv/` — 200.
Старый `https://www.kidsmap.az/42-sportivnyy-klub-umbaev/` после нормализации хоста возвращает 404; актуальная RU-карточка ID42 из sitemap возвращает 200.
Маршрут старого корневого формата отсутствовал в `catalog.urls`.
Выборка подтверждает проблему этого формата, а не причину всех 442 исключений.

## Изменение

- `src/catalog/urls.py`: последний, ограниченный корневой маршрут `^(?P<pk>[0-9]+)-(?P<slug>[^/]+)/$` ведёт в существующий `place_detail_legacy`.
- `src/catalog/views.py:place_detail_legacy`: принят необязательный старый slug. Обработчик использует прежний lookup по ID: published, active, deleted_at IS NULL; URL строится существующим языковым контрактом модели.
- `src/catalog/testcases/test_legacy_root_place_redirects.py`: 6 новых интеграционных тестов. Проверяют AZ/RU/EN, GET/HEAD, включённые и выключенные localized URLs, один 301 с конечным 200, draft/inactive/deleted/missing и некорректные адреса без раскрытия Location.

DB/schema/business visibility/canonical/robots/noindex не изменены. Существовавшие dirty изменения сохранены; собственный delta проверен относительно `.tmp/seo-legacy-20261009/{views,urls}.py`.

## Проверки

RED, до изменения приложения:

```bash
python3 docs/task33/qa04/run.py --output /tmp/kidsmap-seo-legacy-red-20261009 --label catalog.testcases.test_legacy_root_place_redirects
```

6 tests, 7 failures с учётом subtests, 0 errors, 0 skipped: старые ссылки не давали 301. Отсутствие маршрута воспроизведено. Cleanup PASS.

GREEN:

```bash
python3 docs/task33/qa04/run.py --output /tmp/kidsmap-seo-legacy-green-20261009 --label catalog.testcases.test_legacy_root_place_redirects --label catalog.testcases.test_localized_place_seo --label catalog.testcases.test_seo_indexability
```

28/28 PASS, 0 failures/errors/skipped, exit0. Django check и makemigrations --check --dry-run PASS. Disposable PostgreSQL17.10, network none, DJANGO_TESTING=1, Unix socket, LocMem cache/email, isolated media, network/libpq guards, внешние credentials отсутствуют. Cleanup PASS.
Хеши трёх файлов приложения/тестов зафиксированы в `.tmp/seo-legacy-20261009/source-sha256.json`, после проверки совпадают.

## Границы

Production deployment, commit, push, Search Console validation/indexing requests, полный project suite и rendered browser QA NOT RUN. На production старые ссылки останутся 404 до отдельной выкладки.
Нормализация www/default-language-prefix/query может добавлять существующие промежуточные редиректы; новые тесты доказывают один переход для чистых старых AZ/RU/EN URL на основном хосте.
Спорные Google canonical и прочие группы исключений — отдельный scope. Перенаправлять удалённые карточки на главную не следует.
