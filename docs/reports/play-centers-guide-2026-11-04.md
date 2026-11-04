# Игровые центры Баку для детей

2026-11-04 · LOCAL WORKTREE. Гид подготовлен для просмотра, не опубликован. Production, commit/push/deploy не выполнялись. Предыдущие музеи/парки и прочие изменения рабочего дерева сохранены.

Превью: <http://127.0.0.1:8792/ru/parents/play-centers/>. AZ: `/parents/play-centers/`, EN: `/en/parents/play-centers/`. Локальный сервер оставлен работающим.

## Содержание

Шесть центров разных форматов, выбор филиала, два плана визита, checklist и семь вопросов родителей: маленькие дети, школьники, стоимость, сопровождение, день рождения, дождь, шум/свет. Три языка и три оригинальные иллюстрации. Карточки и ссылки добавлены на главную, в семейный гид и общий footer.

Отобранные ID: 78 Moka Kids — Zefir Mall, 72 Kinderland, 74 Hello Park — Crescent Mall, 75 Amburan Kids, 356 Happyland — Dəniz Mall, 358 Bricobilandia — Dəniz Mall. Публичный каталог с фильтром FUN/kids-play-centers/Baku на момент проверки содержал 17 уникальных ссылок, собранных с трёх страниц. Это подборка форматов, не рейтинг и не полный список города.

Выборка ограничена активной подкатегорией игровых центров, публичностью и географией Баку. При скрытии/смене категории карточка исключается без случайной замены другим развлечением. Кнопка каталога сохраняет реальный ID подкатегории текущей базы. При отсутствии активной подкатегории ссылка не расширяется до всей категории FUN.

## Источники

- Moka Kids: <https://mokakids.az/ru>
- Kinderland: <https://www.kinderland.az/?hl=ru>
- Hello Park / оператор: <https://caspianentertainment.com/>
- Amburan Kids: <https://amburanmall.az/en/amburan-kids/>
- Happyland: <https://denizmall.az/en/entertainment/for-kids/happyland/>
- Bricobilandia: <https://www.denizmall.az/en/shop-and-dine/services/bricobilandia/>

Проверены официальные страницы операторов/торговых центров. Kinderland указывает 3–14 на собственном RU-сайте и 4–14 на сайте оператора; фиксированная возрастная граница в редакционном тексте не утверждается. Не придуманы цены, графики, наличие присмотра, льготы или гарантии безопасности. Советы по планированию отделены от описаний услуг.

Имена/адреса/описания/изображения взяты из публичного KidsMap. Несколько существующих обложек каталога имеют AI-происхождение; они не названы в отчёте настоящими фотографиями. Сами записи и изображения production не менялись. Новые редакционные иллюстрации не изображают конкретные реальные интерьеры.

## Ассеты и SEO

Промпты: [play-centers-assets-2026-11-04.json](play-centers-assets-2026-11-04.json). Инструмент: встроенный `image_gen.imagegen`; все три результата визуально просмотрены. Pillow — только экспорт/масштабирование, без смыслового редактирования.

| Файл в `static/img/guides/` | Размер | Байты |
| --- | --- | --- |
| play-centers-hero.webp | 1536×1024 | 345218 |
| play-centers-hero-small.webp | 640×427 | 66058 |
| play-centers-first-visit.webp | 1536×1024 | 306254 |
| play-centers-first-visit-small.webp | 640×427 | 56788 |
| play-centers-together.webp | 1536×1024 | 343032 |
| play-centers-together-small.webp | 640×427 | 66858 |

Исходники в `/home/ramin/.codex/generated_images/01a1a619-4659-7001-9e8a-47e7abb08a27/`: `exec-150e2b58-7a3d-4cb0-ac03-0eb34f4b56bc.png`, `exec-2669753b-5c97-43f6-8cde-20e4c900e2ef.png`, `exec-546241c2-13ea-4da0-86c6-35350fed6969.png`.

WebP quality82, responsive srcset, корректные размеры и RU/AZ/EN alt; декоративные картинки рядом с текстом ссылки имеют пустой alt. Canonical/hreflang/x-default, sitemap, Article/WebPage/BreadcrumbList и OG/Twitter используют существующую архитектуру. Дата публикации не выдумана. Показ изображений в Google, индексация и AI-цитирование не проверялись и не обещаются.

## Проверки

- PASS: 76 Django-тестов общей выборки; после последней правки трёх названий направлений — отдельный повтор 6 тестов нового гида.
- PASS: 9 JS-тестов поведения guide links.
- PASS: 12 состояний браузера, AZ/RU/EN ×375/768/1024/1440. Шесть карточек, корректные alt информативных изображений, существующие якоря, нет горизонтального overflow или пересечения обложки с текстом заголовка.
- PASS: все 10 изображений внутри гида загружены в проверенном EN DOM; переход к FAQ раскрывает ответ, Enter закрывает ответ с фокусом на summary. Проверены мобильный заголовок, карточки, обе большие иллюстрации и footer. Ошибок/warnings в проверенном browser console нет.
- PASS: 3 страницы с серверным HTML и 28 уникальных URL карточек/ассетов вернули 200; `.tmp/play-centers-guide-20261104/http.json`.
- PASS: `git diff --check` для изменённых tracked-файлов.
- No-JS: серверное содержимое проверено; отдельный браузер с отключённым JS не запускался. Reduced-motion: покрыт существующими JS-проверками, отдельная эмуляция браузера в этом шаге не выполнена.

Команды:

```bash
.venv/bin/python .tmp/play-centers-guide-20261104/runner.py test catalog.testcases.test_play_centers_guide catalog.testcases.test_museums_guide catalog.testcases.test_parent_guide_images catalog.testcases.test_parent_guides catalog.testcases.test_parks_guide catalog.testcases.test_home_parent_intent catalog.testcases.test_seo_indexability catalog.testcases.test_seo_landing_visibility catalog.testcases.test_search_previews --noinput --keepdb
.venv/bin/python .tmp/play-centers-guide-20261104/runner.py test catalog.testcases.test_play_centers_guide --noinput --keepdb
NODE_PATH=/home/ramin/kidsmap/.tmp/phone-dom/node_modules node --test scripts/tests/parent_guide_links.test.cjs
.venv/bin/python .tmp/play-centers-guide-20261104/http_check.py
```

Логи: `.tmp/play-centers-guide-20261104/green-final.log`, `green-final-targeted.log`, `node.log`. Браузерная проверка выполнена через CUA, фактические результаты в текущем чате.

RED: шесть тестов возвращали 404 до реализации. Первый общий прогон выявил потерянный `#guide-topics` в параллельно обновлённой главной. Новая карусель сохранена, добавлена карточка игровых центров и восстановлена полезная ссылка «Все варианты отдыха»; следующий общий прогон зелёный. Проверка пересечения заголовка уточнена до геометрии текстовых строк: исходная проверка учитывала пустой padding, зарезервированный под миниатюру. Пустой alt декоративной иконки не считается ошибкой.

## Изоляция и границы

Runner очищает environment, включает `DJANGO_TESTING=1`, использует `test_play_centers_guide_20261104`, отдельные media/cache. Preview DB `qa_play_centers_preview_20261104` содержит шесть fixtures из публичного JSON-LD; карточки не являются полным зеркалом production. Взяты публичные адреса/координаты/названия/описания/URL/часы и доступные Offer; неизвестная цена — on_request. Географические подписи fixture упрощены до Баку, подкатегория имеет локальный ID37 вместо production102. Эти числа не hardcoded в публичном controller.

Новые файлы: `parent_guide_play_centers.py`, `test_play_centers_guide.py`, шесть WebP, provenance и отчёт. Изменены registry/controller, шаблон guide, base/footer, homepage guide include и общий planning CSS. Планировочный блок музеев переиспользуется через `guide.planning`; существующий музейный гид входит в регрессию. Другие редакционные материалы не публиковались. Снимки до изменений и diff находятся в `.tmp/play-centers-guide-20261104/`; для главной отдельно сохранён актуальный параллельно изменённый вариант перед интеграцией.

Публикация — после пользовательского просмотра. Production/Search Console/indexing: NOT RUN.
