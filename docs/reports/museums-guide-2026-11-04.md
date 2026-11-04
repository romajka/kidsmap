# Музеи Баку для детей — локальная подготовка

Дата: 2026-11-04. LOCAL WORKTREE, на основе HEAD `b7659e79a25d2ae8d23cd505ec46755683223c09` с существующими чужими изменениями. Commit/push/deploy и публикация этого гида не выполнялись. Предыдущее разрешение на серверные исправления SEO не использовалось для публикации нового материала.

## Результат

- AZ `/parents/museums/`, RU `/ru/parents/museums/`, EN `/en/parents/museums/`.
- Локальное превью: <http://127.0.0.1:8791/ru/parents/museums/>. Сервер оставлен работающим для просмотра; это не production URL.
- Шесть отобранных музеев, выбор по интересам, план первого визита с дошкольником/школьником, checklist, семь FAQ и ссылки на источники.
- Названия, фотографии и ссылки берутся из публичных карточек. Редакционные подсказки локализованы отдельно. Выборка перепроверяет доступность, категорию и географию; скрытая карточка исключается без автоматической замены другим, не проверенным музеем.
- Canonical/hreflang/x-default, sitemap, Article/WebPage/BreadcrumbList, согласованные OG/Twitter/primaryImageOfPage, локализованные alt и адаптивные изображения. Дата публикации не выдумана. Ссылки на новый гид добавлены на главную, в семейный гид и общий блок гидов в футере.
- Нет обещания показа картинки в Google, индексации, позиций или цитирования AI-поиском. Эти внешние результаты для нового локального материала не измерялись.

## Источники и редакционный выбор

Просмотрены две страницы публичного каталога KidsMap с фильтрами `category=museums-culture&district=baku`: 19 мест. В гид отобраны:

| ID | Музей | Источник |
| --- | --- | --- |
| 324 | Азербайджанский национальный музей ковра | <https://azcarpetmuseum.az/plan-your-visit> |
| 320 | Азербайджанский национальный музей искусств | <https://www.nationalartmuseum.az/?lang=en> |
| 371 | Корабль-музей «Сураханы» | <https://surakhanishipmuseum.az/en/page/about-us> |
| 372 | Национальный музей истории Азербайджана | <https://azhistorymuseum.gov.az/en> |
| 287 | Музей миниатюрной книги | <https://minibooks.az/en/index.html> |
| 321 | Музей современного искусства | <https://azerbaijan.travel/modern-art-in-ancient-city> |

Описания коллекций проверены по официальным источникам и туристическому порталу; задания детям — редакционные идеи, а не обещание услуги музея. Цены, часы работы, возрастные ограничения, расписание мастер-классов и гарантии доступности в редакционном тексте не выдумывались.

Прямой автоматический HTTP-запрос получил 200 от сайтов искусства, истории и «Сураханы». Сайты ковра, миниатюрных книг и tourism вернули 403 для urllib; их материалы прочитаны через веб-поиск. Это ограничение автоматической проверки, а не доказательство неработающих пользовательских ссылок. Снимки проверки: `.tmp/museums-guide-20261104/sources-status.json`, `public-venue-links.json`, `preview-data.json`.

## Ассеты

Сгенерированы три оригинальные редакционные иллюстрации встроенным `image_gen.imagegen`, без имитации фотографий реальных музеев. Все изображения просмотрены. Промпты и параметры: [museums-guide-assets-2026-11-04.json](museums-guide-assets-2026-11-04.json).

| Назначение | Файл в `static/img/guides/` | Размер | Байты |
| --- | --- | --- | --- |
| Обложка | museums-hero.webp | 1536×1024 | 378530 |
| Обложка mobile | museums-hero-small.webp | 640×427 | 74774 |
| Первый визит | museums-first-visit.webp | 1536×1024 | 200134 |
| Первый визит mobile | museums-first-visit-small.webp | 640×427 | 43154 |
| Школьник | museums-discovery.webp | 1536×1024 | 308744 |
| Школьник mobile | museums-discovery-small.webp | 640×427 | 62532 |

Исходные PNG сохранены в `/home/ramin/.codex/generated_images/01a1a619-4659-7001-9e8a-47e7abb08a27/`:

- `exec-611b2c4f-b712-402f-829f-1c2ab92d033f.png` — hero;
- `exec-eeebc771-73fe-42dd-b84f-dad8c259deed.png` — first visit;
- `exec-fe1d1177-9451-4302-bea6-b47f11d125a0.png` — discovery.

Pillow использован только для изменения размера и экспорта WebP quality 82. На карточках — реальные фотографии из публичного KidsMap, скопированные только в изолированное preview media. Иллюстрации снабжены RU/AZ/EN alt, srcset, width/height; нижние изображения загружаются лениво. Декоративная миниатюра у ссылки в футере имеет пустой alt, название ссылки доступно текстом.

## Проверки

PASS: 70 Django-тестов, 9 JS-тестов, 12 состояний Chromium (3 языка × 375/768/1024/1440), 18 переходов в карточки. Изображения загружены, alt заполнены, якоря существуют, metadata image согласовано, горизонтального переполнения и ошибок страницы/HTTP в финальном прогоне нет. Проверены keyboard Enter, reduced motion, открытие FAQ по ссылке, входящие ссылки с главной/семейного гида. Без JS: 200, шесть карточек, нативный FAQ работает, переполнения нет.

На скриншоте обнаружено пересечение длинной надписи над заголовком и миниатюры: отступ изображения исправлен только у музейного гида на mobile. После этого повторён браузерный прогон с проверкой геометрии. Общие Django/JS-тесты после CSS-only правки не повторялись.

Точные команды:

```bash
.venv/bin/python .tmp/museums-guide-20261104/runner.py test catalog.testcases.test_museums_guide catalog.testcases.test_parent_guide_images catalog.testcases.test_parent_guides catalog.testcases.test_parks_guide catalog.testcases.test_home_parent_intent catalog.testcases.test_seo_indexability catalog.testcases.test_seo_landing_visibility catalog.testcases.test_search_previews --noinput --keepdb
NODE_PATH=/home/ramin/kidsmap/.tmp/phone-dom/node_modules node --test scripts/tests/parent_guide_links.test.cjs
/home/ramin/.codex/skills/playwright/scripts/playwright_cli.sh --session museums-guide run-code --filename .tmp/museums-guide-20261104/browser-check.js
/home/ramin/.codex/skills/playwright/scripts/playwright_cli.sh --session museums-guide run-code --filename .tmp/museums-guide-20261104/browser-extra.js
```

Логи: `.tmp/museums-guide-20261104/green-final.log`, `node.log`, `browser.log`, `browser-extra.log`. Скриншоты: `output/playwright/museums-guide-20261104/`.

Изоляция: runner очищает environment, выставляет `DJANGO_TESTING=1`, отдельные PostgreSQL `test_museums_guide_20261104` / `qa_museums_preview_20261104`, LocMem cache и локальное media. Preview использует публичные имена, описания, адреса, координаты, фотографии, localized URL и опубликованные JSON-LD часы/тарифы. Для миниатюрных книг без JSON-LD тарифа установлен локальный `on_request`, без числовой цены. Это ограниченный fixture для просмотра, не точная копия production taxonomy или всех правил билетов. Ни одна запись production не изменена.

Первичные отказы зафиксированы и разобраны: RED 404 до регистрации маршрута; fixture другого города требовал непротиворечивых координат; preview bulk insert не заполнил обязательные публичные поля/slug, они восстановлены из публичного снимка; браузерная проверка FAQ читала `open` до события `hashchange`, исправлена ожиданием состояния. Продуктовый JS для последнего случая не менялся, assertions не ослаблялись.

## Границы изменений

Новые: `parent_guide_museums.py`, `test_museums_guide.py`, `museums_planning.html`, `museums_guide.css`, шесть WebP, этот отчёт и provenance JSON.

Изменены: `parent_guide_content.py`, `controllers/parent_guides.py`, шаблон гида, ссылки главной и footer в `base.html`; в `site.css` только сетка footer-гидов 3→2 колонки под четыре карточки. Предсуществовавшие parks, specialist, mobile и image-SEO изменения сохранены. Сравнение с начальным dirty snapshot: `.tmp/museums-guide-20261104/task-only.diff`. `git diff --check` по изменённым tracked-файлам — PASS.

Production/deploy/Search Console/Google indexing: NOT RUN для нового гида. Следующий шаг после пользовательского просмотра — отдельная публикация согласованного материала.
