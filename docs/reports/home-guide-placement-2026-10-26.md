# Гид после блока интересов

26.10.2026. По уточнению пользователя прежнее положение гида под первым экраном заменено. LOCAL dirty WORKTREE, HEAD `1b0acf8c6d03e71d8516cfb92c19018db1426ebf`. Production/commit/push/deploy не выполнялись.

Новый визуальный порядок: **первый экран → карта и поиск → рекомендации → «Чем увлечён ваш ребёнок?» → семейный гид → «Как это работает»**. Гид оставлен отдельным блоком, поскольку выбор занятий по интересам и планирование семейной прогулки решают разные задачи. Прежние SEO-тексты и ссылки сохранены.

Изменены только `templates/pages/home.html` (перемещён include, CSS cache key `20261026_parent_guide_r2`), `static/css/pages/home_layout.css` (`order: 4` после интересов с тем же order) и существующая проверка порядка в `test_home_parent_intent.py`. Include расположен вне условия наличия категорий: при пустом каталоге гид остаётся доступным.

Проверки:

- Первый запуск RED был прерван ошибкой окружения: PostgreSQL ещё не создал socket. После `pg_isready` тест повторён: 3 ожидаемых падения для старого порядка на AZ/RU/EN.
- GREEN: `.venv/bin/python /tmp/kidsmap-parent-seo-20261026/run-tests.py placement_green catalog.testcases.test_home_parent_intent` — **5 PASS**, 6,112 с. Изолированный PostgreSQL без сети, синтетические данные и отдельные cache/media/cookies; production credentials не использовались.
- Реальный браузер: **AZ/RU/EN × 390/768/1024/1280/1440 = 15 состояний**. По bounding rectangles проверена вся цепочка секций, фактическая ширина, отсутствие горизонтальной прокрутки и один экземпляр гида. Desktop/mobile скриншоты просмотрены. Console errors: 0; server log без 404/Traceback.
- `git -c core.whitespace=cr-at-eol diff --check`: PASS. По SHA-256 подтверждено, что семейный контент, метаданные и переводы из предыдущей задачи не менялись.
- Полный набор приложения и production QA не запускались: изменение касается расположения одного блока. Изолированный стенд после проверки остановлен.

Доказательства: `/tmp/kidsmap-guide-placement-20261026/`; скриншоты `/home/ramin/kidsmap/.tmp/guide-placement-20261026/screenshots/`.


## Уменьшение отступов, 26.10.2026

По следующему замечанию пользователя убрано сложение margin и padding вокруг гида. На desktop фактически было 68px от секции интересов до гида и 130px от нижнего края гида до заголовка «Как это работает». Теперь **24px сверху и 32px до следующего заголовка**.

Изменены только `home_layout.css`: нижний margin гида 0, нижний margin интересов 0, margin-top шагов 24px и padding-top 8px; CSS cache key в `home.html` обновлён на `20261026_parent_guide_r3`. Порядок, тексты и ссылки сохранены.

Проверено в реальном браузере AZ/RU/EN × 390/768/1024/1280/1440: 15 состояний, во всех расстояния 24px/32px, правильный порядок и отсутствие горизонтальной прокрутки. Desktop/mobile скриншоты просмотрены, console errors 0, server log без 404/Traceback. `git -c core.whitespace=cr-at-eol diff --check`: PASS. Новые unit tests для CSS-интервала не добавлялись; прежние 5 Django PASS относятся к проверке размещения выше. Изолированный PostgreSQL и синтетические данные; production не менялся.

Доказательства: `/tmp/kidsmap-guide-spacing-20261026/`, скриншоты `/home/ramin/kidsmap/.tmp/guide-spacing-20261026/screenshots/`.
