# Производительность KidsMap: 28 сентября 2026

Исполнитель: `/root`, непосредственные измерения; без делегирования. Область: сервер, Django/PostgreSQL, публичная главная и каталог. Контракт: `.agents/rules/audit-contract.md`; рекомендации по областям release/backend/frontend. Это анализ, оптимизации не применены.

LOCAL HEAD и PRODUCTION: `3092e9b0d565c99c90048bba8ed727cfbd0a1136`. Production checkout чистый. В LOCAL WORKTREE параллельно изменяются `src/catalog/templates/pages/home.html` и `static/css/pages/home_redesign.css`; они сохранены и не входят в измеренный production snapshot. Интервал проверки: примерно 08:13–08:21 UTC.

## 1. Состояние области

| Evidence | Измерение | Результат |
|---|---|---|
| E1 | `uptime`, `nproc`, `free -m`, `df -h /opt`, `vmstat 1 5`, `/proc/pressure/*` | 4 CPU; load 0.34/0.46/0.40; RAM 7941 MB, available 6541 MB; диск 56%, свободно 65 GB. CPU idle 71–94%, I/O wait и steal 0% в выборке; memory/I/O pressure avg10/60/300 = 0. |
| E2 | Три последовательных `curl --compressed` на каждый внешний URL, `--max-time 25`, тело отброшено | Все 200. Главная TTFB 2.38–2.75 s; каталог AZ 2.45–2.67 s; каталог RU 2.18–2.27 s; health 0.22–0.28 s. Это короткая выборка, не p95. |
| E3 | Три `curl` напрямую `127.0.0.1:8000`, Host kidsmap.az, X-Forwarded-Proto https | Главная 2.49–2.65 s; каталог 1.89–2.07 s; health 3–8 ms. Размер HTML до gzip: главная 330326 bytes, каталог 384857 bytes. |
| E4 | RequestFactory → resolve(view) → render; execute_wrapper SQL timing | Главная 2.564 s, 35 SQL, суммарно SQL 0.798 s, максимум 235 ms. Каталог 1.905 s, 20 SQL, SQL 1.029 s, максимум 265 ms. |
| E5 | Chromium, desktop initial navigation и 390×844; Navigation/ResourceTiming, buffered LCP | Главная desktop: TTFB 3.30 s, FCP 4.04 s, load 13.10 s, ресурсы 12.30 MB/99 запросов. Mobile после очистки browser cache: TTFB 3.89 s, LCP 5.06 s, load 13.25 s, ресурсы 12.30 MB/87 запросов; изображения 11.66 MB, Google Maps 24 запроса. |
| E6 | cProfile, затем EXPLAIN FORMAT JSON без ANALYZE для медленных запросов | Главная: localize_address_text 72 вызова, cumulative 1.393 s в профиле; get_location_translation 6434 вызова; normalize_to_key 6792. Фильтры: cumulative 1.05 s на главной / 1.11 s в каталоге. SQL публичной карты 30.5 KB, исполнение 251 ms; запросы счётчиков фильтров 23.8 KB, 63–72 ms. JIT в выбранных планах отсутствует. |

Профилирование запускается отдельным Python-процессом внутри web-контейнера. Все SQL внутри явной `READ ONLY` транзакции, `statement_timeout=15s`, `lock_timeout=2s`. Redis в диагностическом процессе заменён LocMem через override_settings; production cache/config не изменены. Поэтому E4/E6 — стоимость view без production middleware, с отдельным диагностическим кэшем, а не полный сетевой запрос. cProfile добавляет overhead: его cumulative timings нельзя складывать или сравнивать напрямую с обычным временем ответа.

## 2. Сильные стороны

Запаса RAM, CPU и диска в проверенный период достаточно. PostgreSQL: один активный connection (сам диагностический запрос), ноль ожидающих Lock. DEBUG=false, PostgreSQL, RedisCache, CONN_MAX_AGE=60. Nginx 1.24.0: HTTP/2 и gzip работают; проверенный versioned CSS имеет `public,max-age=31536000,immutable`, media — `public,max-age=604800`. Включение gzip заново не является исправлением найденных задержек.

## 3. Реальные проблемы

**PERF-01 / P2 / production / высокая уверенность.** Главная передаёт 11.66 MB изображений на холодной мобильной загрузке (E5). Отдельные PNG карточек — 1.72–2.39 MB. Hero изображение 3024 px отображается шириной 180 px; следующие изображения 1920 px — шириной 143 px. В DOM img нет набора размеров srcset; существующий picture может выбирать WebP, но фактическая загрузка показывает оригиналы большого размера. Источник: committed `pages/home.html:115`, Place.public_image_url, gallery serialization. Влияние: большой трафик и поздняя загрузка. Owner: frontend + media pipeline. Следующий шаг: производные изображения и responsive markup, проверка сохранения оригиналов.

**PERF-02 / P2 / production + source / высокая уверенность.** Сбор HTML сам занимает около двух секунд и больше (E2–E4). `HomeController.build_context` собирает карту всех подходящих мест; `PlaceController._serialize_map_places` делает аналогичную работу. `localize_address_text` повторяет проход по словарям/regex для каждого адреса. Источники: `controllers/home_controller.py:37`, `controllers/place_controller.py:742`, `services/locations.py:398`. Owner: backend. Следующий шаг: отдельный кэш публичного map payload и оптимизация чистых helper-функций.

**PERF-03 / P2 / production + source / высокая уверенность.** Счётчики категорий/подкатегорий/регионов/метро повторно выполняют сложный public_place_queryset с проверками текста, тарифа и расписания. Источники: `services/public_filter_options.py:85`, `services/content_quality.py:236`; E4/E6. Большой SQL обусловлен в том числе вложенными Lower/Replace/Concat для правил публичности, а не только недостатком индексов. Owner: backend/database. Следующий шаг: кэш агрегатов с корректной инвалидизацией, затем упрощение общей выборки с сохранением правил публикации.

**PERF-04 / P3 / production / средняя уверенность в выигрыше.** 24 Google Maps requests на главной в мобильной выборке. Google Maps — кандидат на загрузку при приближении карты к viewport или первом взаимодействии. Сам факт запросов подтверждён; отдельное влияние JS на CPU не измерено. Owner: frontend/maps.

## 4. Tech debt

На главной два top_popular запроса; выдача карточек не prefetch-ит тарифы/расписания так же, как карта. В E4 тарифная таблица упоминается в 18 SQL (включая подзапросы, это не 18 отдельных N+1 запросов). Кандидаты: переиспользование результатов, targeted prefetch, request-scoped SiteSettings. Они вторичны относительно изображений и публичных агрегатов.

Диагностический A/B только в отдельном процессе: memoization normalize_to_key/get_location_translation дала 2.012/2.021 s против baseline 3.119/2.305 s; cache hits 12681/misses 115. Это поддерживает гипотезу повторных вычислений; порядок и прогрев влияют на результат. Не является оценкой гарантированного ускорения и не проверяет все языковые/инвалидационные контракты. Рабочие Gunicorn-процессы не модифицированы.

## 5. Risks

Кэш должен разделять язык, публичные фильтры и версии данных. Общие данные можно кэшировать отдельно от пользовательского избранного, сессии и CSRF. Изменение публикации/тарифа/расписания должно сбрасывать соответствующий кэш. Сохранение большой страницы целиком без учёта этих контрактов не предложено. Упрощение public_place_queryset требует тестов всех правил публичности; отключать проверки качества ради скорости нельзя.

Сжимать оригиналы с потерями на месте не требуется: производные размеры хранить отдельно. Увеличение workers без нагрузочных замеров не устраняет дорогие вычисления одного запроса и может увеличить конкуренцию за CPU/DB.

## 6. Dead/legacy candidates

Удаление файлов, media или данных не исследовалось и не предлагается. Нулевое давление ресурсов в короткой выборке не доказывает отсутствие пиковых проблем.

## 7. Tests gaps

Выполнены: system metrics, bounded curl, read-only SQL timing/EXPLAIN, отдельный cProfile, диагностический memoization A/B, Chromium desktop/mobile cold/warm observations, headers, production snapshot/settings projection.

Не выполнены: нагрузочный тест, история метрик/пиков и p95/p99, реальное мобильное устройство/3G, JS CPU trace, сравнение до/после готовой оптимизации, полный аудит admin и всех detail pages. Каталог был открыт после главной с частично тёплым browser cache: load 6.38 s, LCP 3.32 s, transfer 2.85 MB; это не cold catalog benchmark. Browser loadEvent не равен времени полной визуальной готовности (mobile LCP может быть позже load).

Публичные browser GET могут запускать обычную аналитику сайта. Диагностика не меняла application files/config/env/schema/data, не деплоила и не перезапускала сервисы; SQL профилирование строго read-only. Нагрузочный тест на production не запускался.

## 8. Recommendations

1. **Первый этап: изображения.** Генерировать WebP/AVIF или качественно сжатые JPEG/WebP в размерах под hero/cards (например 320/640/960), подключить srcset/sizes, сохранить width/height и приоритет первого hero. Остальные слайды не подгружать все сразу; lazy loading проверять реальным Network trace, потому что сейчас он не мешает загрузить 11.66 MB. Замерить cold LCP и transfer при тех же viewport/cache условиях.
2. **Второй этап: backend cache и локализация.** Кэшировать публичный map payload и общие filter aggregates в уже существующем Redis с ограниченным TTL и событиями инвалидизации. Убрать повторное вычисление переводов/regex, добавить ограниченный кэш чистых функций с корректными language keys. Повторить direct-origin timing и query budget.
3. **Третий этап: запросы.** Упростить повторные public queryset/count вычисления; targeted prefetch карточек; по EXPLAIN оценить индексы только для конкретных операций. Денормализованная public-readiness модель возможна отдельным проектом после покрытия инвалидизации тестами.
4. **Затем Maps.** Отложенная загрузка SDK/данных по viewport/interactions с сохранением работы фильтров и мобильной карты.

Рекомендуемые критерии следующего этапа: главная существенно меньше текущих 12.3 MB; origin TTFB цель <500 ms на прогретых публичных данных; cold LCP цель <2.5 s в согласованном профиле измерения. Это цели приёмки, не обещание результата текущего аудита. Апгрейд VPS сейчас не обоснован наблюдениями; решение о мощности принимать после application optimization и off-production load test.

Первичные справочники: [Django optimization](https://docs.djangoproject.com/en/6.0/topics/db/optimization/), [Django cache](https://docs.djangoproject.com/en/6.0/topics/cache/), [responsive images](https://web.dev/learn/images/responsive-images). Получены Context7 и прямым чтением документации; рекомендации выше привязаны к измерениям KidsMap.

## 9. P0/P1/P2/P3

P0/P1 аварий по этому аудиту не установлено. P2: PERF-01/02/03 — изображения, вычисления публичной карты, повторные агрегаты. P3: PERF-04 — Maps; targeted prefetch и повторные настройки. Приоритет внедрения: изображения → публичные backend данные → оставшиеся query/Maps улучшения. Изменения сервера для этой задачи не применялись.
