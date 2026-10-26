# Parent intent homepage implementation plan

**Goal:** дать родителю заметный путь с главной в существующий гид по Баку и согласовать метаданные с реальным каталогом.

**Authorization:** выбранные пользователем пункты 1–3; LOCAL implementation, Search Console read-only. Без публикации мест, deploy, commit и push. Сохранить все прежние dirty файлы.

**Architecture:** существующие home template/SEO service; отдельный include для компактного блока сразу после hero. Локализованные обычные ссылки ведут в существующие гиды и FAQ. Новые URL, таблицы и JS не нужны.

**Files:** `src/catalog/templates/pages/home.html`, новый `pages/includes/home_parent_guide.html`, `static/css/pages/home_layout.css`, `src/catalog/services/seo.py`, три gettext каталога, новый `src/catalog/testcases/test_home_parent_intent.py`.

- [x] Сначала регрессия: на AZ/RU/EN блок находится в main после hero и до рекомендаций, содержит локализованные ссылки на гид, его FAQ и спорт. Метаданные соответствуют широкому каталогу; canonical/hreflang сохраняются.
- [x] Проверить RED в изолированном PostgreSQL с отключёнными внешними интеграциями.
- [x] Добавить include с H2 «Куда сходить с ребёнком в Баку», описанием парков/музеев/игровых центров, основным CTA и тремя ссылками на дождь/бесплатно/выходные. Использовать существующую иллюстрацию и брендовые tokens, без анимации.
- [x] Расширить homepage title/description и название featured ItemList; перевести новые строки на AZ/EN/RU без перезаписи существующих переводов. Существующий H1 гида уже отвечает запросу и сохраняется.
- [x] GREEN: новый тест, parent guides, site brand/schema. Проверить gettext и whitespace.
- [x] Rendered QA: AZ/RU/EN × 390/768/1024/1280/1440; ширина, читаемость, focus, переходы/якоря, console/static errors. Сохранить скриншоты.
- [x] Search Console: Web, 25.07–24.10.2026, Азербайджан; записать доступные похожие запросы и страницы. Показы сайта не считать частотностью рынка. Отдельно проверить гиды без фильтра страны.
- [x] Краткий отчёт с точными командами, результатами и приоритетами. Production не изменять.

Browser finding: FAQ fragments selected a closed disclosure. Scope extended only to `static/js/parent_guides.js`, its template cache key, and `scripts/tests/parent_guide_links.test.cjs`: open the matching FAQ on initial hash/hashchange independently of motion. Node RED 4/8 failures, then GREEN 8/8.


## Коррекция размещения по запросу пользователя, 26.10.2026

Пользователь уточнил: семейный гид слишком высоко и отодвигает основной поиск. Перенести отдельный блок сразу после «Чем увлечён ваш ребёнок?» и перед «Как это работает». Сохранить SEO-тексты и ссылки. Меняются только include в `pages/home.html`, `order` в `home_layout.css`, cache key и проверка порядка в `test_home_parent_intent.py`.

- [x] RED: рекомендации и интересы предшествуют гиду в серверном HTML на AZ/RU/EN.
- [x] Переместить include после `home-discover`, задать `order: 4` (одинаковый с discover; DOM сохраняет последовательность), обновить CSS cache key.
- [x] GREEN: весь `test_home_parent_intent`, whitespace; browser AZ/RU/EN × пять ширин, визуальный и DOM-порядок hero → карта → рекомендации → интересы → гид → шаги. Проверить сохранение блока при пустом каталоге.
- [x] Сохранить скриншот и краткий отчёт. LOCAL only, без deploy/commit/push.


## Коррекция отступов по запросу пользователя, 26.10.2026

Только `home_layout.css` и его cache key в `home.html`: убрать сложение нижнего margin гида, верхнего margin и padding блока шагов. Оставить около 32px от края гида до следующего заголовка; около 24px от интересов до гида. Порядок и SEO-тексты сохраняются. Проверка реальными bounding rectangles до/после, AZ/RU/EN × пять ширин, desktop/mobile screenshot. Новые unit tests для CSS-отступа не добавляются; production не меняется.
