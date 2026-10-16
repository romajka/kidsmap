# Превью карточки в оформлении сайта

Локальное исправление по прямому запросу пользователя. Production не открывался
и не изменялся; коммита, push и deployment нет. Ветка `task33-progress`, LOCAL HEAD
`e4e05cc213b34e2d771ecb854901bfd016d1db51`; проверялся текущий dirty WORKTREE.

## Что доступно

«Превью на сайте» добавлено в список заявок, форму заявки и полный экран проверки.
Превью использует `catalog/place_detail.html`, настоящий header/footer,
`detail.css`, публичную галерею, телефонные controls, форматирование цен,
расписания и групп. Это отдельный защищённый GET admin route, а не публикация.
Панель превью показывает отправленную/текущую версию, устаревание, переключатели
AZ/RU/EN и возврат в проверку с сохранением фильтра списка.

Данные кандидата восстановлены только в памяти: полный snapshot + patch,
галерея/расписание/прямые и групповые тарифы. Публичные правила скрывают
неопубликованные старые направления. Новые направления из отправленного дерева
отображаются по существующему правилу их публикации при применении дерева.
Главное фото, обложка и gallery следуют настоящему публичному правилу: обложка
служит fallback, когда главного фото нет, и не дублируется в галерее.

Посетитель в превью отображается как гость; staff session сохраняется.
Галерея работает настоящим Swiper. Раскрытие телефона использует тот же
публичный JS, получая защищённые данные из HTML превью без POST и статистики.
Избранное переключается локально, POST форм блокируются. Shared controls
показывают будущий публичный URL, не приватный admin URL. Ссылки на направления
неопубликованного родителя остаются внутри превью и не ведут к публичному 404.

Tracking/rating writes, GA и AI-referral tracking отключены только в превью.
Отложенные analytics session events не извлекаются. Private no-store и
noindex/nofollow/noarchive headers обязательны. Обычный публичный маршрут и
ограничения на доступ к неопубликованным карточкам сохранены.

Дополнительно исправлены два подтверждённых случая внутри превью:

- при удалении тарифов старые scalar prices не должны возвращаться; общий чистый
  `legacy_price_values` используется и для сохранённых тарифов, и для кандидата;
- начальный `scrollIntoView` галереи закрывал toolbar fixed-шапкой. Только в
  превью автоматическая прокрутка на init отключена; действия листания сохранены.
  Cross-document view transitions отключены в превью после motion.css, чтобы
  переключения языка/возврат не вызывали Chrome transition errors.

## Доказательства

- `tests-final.txt`: **57 тестов PASS**, 59.410 s — 11 новых, 20 тестов полного
  просмотра, 8 ownership regressions, 18 pricing/group regressions.
- `read-only-alone.txt`: отдельный запуск GET preview в PostgreSQL READ ONLY,
  1 PASS, без зависимости от прогрева предыдущими тестами.
- `browser-result.json`: **142 PASS**, Chrome 153.0.8010.36; RU/AZ/EN ×
  360/390/768/1024/1280/1440 px. Console/page errors 0, HTTP >=400 0,
  записывающих запросов после входа 0.
- Нативный путь: список → проверка → превью → галерея/телефон/избранное →
  переключение языка → возврат → текущая версия → превью.
- Проверены private ACL, POST 405, неопубликованный public 404, submitted/current
  версии, цена/расписание/группы, новые и очищенные деревья, публичная parity для
  опубликованной карточки и сохранение staff session.
- Django check, git diff --check, JS/Python syntax и свежие каталоги RU/AZ/EN PASS.
- `source-hashes.json`, `screenshots.json`, `locale-manifest.json` привязывают
  доказательства к версии источников и изображений. `failure.png` исторический,
  исключён из текущего списка скриншотов.

Начальная красная проверка: 7 новых FAIL (маршрут отсутствовал); 20 ранее
существующих тестов попали в этот запуск через импорт fixture-класса, позднее
заменённый импортом модуля. Отдельная красная проверка удаления цены сохранена
в `price-removal-before.txt`. Ошибки harness исправлены без ослабления проверки:
использован настоящий ключ numeric amount, ожидание decode и fast-forward
finite animations при скриншоте средствами Playwright. Декодирование ограничено
видимым фото: lazy изображения вне экрана не должны задерживать снимок. Широкое ожидание всех
анимаций было прервано: фоновые анимации не должны блокировать скриншот.
Два промежуточных запуска общих тестов были прерваны;
итоговый запуск полностью выполнил все 57 тестов в одном процессе.

Команды (cwd `/home/ramin/kidsmap`):

```bash
.tmp/ownership-preview-fix-2026-10-14/venv/bin/python docs/qa/ownership-preview-fix-2026-10-14/runtime.py test catalog.testcases.test_ownership_site_preview catalog.testcases.test_ownership_admin_preview catalog.testcases.test_task33_ownership.ExistingOwnershipBreakTests catalog.testcases.test_task33_ownership.OwnershipEndpointTests catalog.testcases.test_offer_qa01_group_removal catalog.testcases.test_offer_qa09_partial_review_pricing --keepdb
python3 docs/qa/ownership-site-preview-2026-10-14/drive_browser.py
python3 scripts/build_isolated_locales.py verify --manifest .tmp/ownership-preview-fix-2026-10-14/locales-site-preview/manifest.json
.tmp/ownership-preview-fix-2026-10-14/venv/bin/python docs/qa/ownership-preview-fix-2026-10-14/runtime.py check
node --check static/js/place_site_preview.js
node --check static/js/place_gallery.js
node --check static/js/place_phone_reveal.js
git diff --check
```

## Границы

Переиспользован только собственный изолированный стенд предыдущего исправления:
вымышленные пользователи/карточка/фотографии, отдельные PostgreSQL/test DB,
LocMem cache/email, собственные media и sessions, DJANGO_TESTING=1, allowlist
окружения и backend transport только к своему loopback PostgreSQL. Внешние
браузерные интеграции заглушены. Для проверки групп опубликовано только
вымышленное направление стенда; его родительская карточка осталась pending.
Пароли не включены в артефакты; исходный dotenv/production credentials не читались.

NOT RUN: реальная карточка #351 и production, полный suite, реальные Google Maps,
геокодинг, email, внешние переходы/звонки, Firefox/WebKit, physical devices и
screen reader. Существующие dirty изменения и исправление меню сохранены.
Работа одним агентом. Для выпуска нужны штатные сборка static и компиляция PO;
репозиторные MO не переписывались ради стенда. Предыдущий отчёт полного
просмотра описывает предыдущий снимок; текущий снимок находится в этой папке.

После проверки остановлены только собственные server/browser/PostgreSQL стенда.
Скриншот передан в панель Codex (queued).
