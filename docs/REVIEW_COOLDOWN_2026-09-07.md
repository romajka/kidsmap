# Несколько отзывов о месте и двухминутный таймер

## Итог и согласованный scope

Пользователь запросил проверку админки и возможность нескольких отзывов с таймером. После уточнения принят интервал **120 секунд между отзывами одного авторизованного пользователя об одном месте**. На другие места и для других пользователей ограничения независимы. Отзывы о сайте и специалистах сохраняют прежнее update/uniqueness-поведение. Ручная модерация не изменена.

Новые отзывы о месте создаются отдельными `PlaceReview(status='pending', is_approved=False)`. Старые тексты, авторы и решения модератора не перезаписываются. Все одобренные отзывы учитываются существующим алгоритмом рейтинга; модель «одна оценка на пользователя» не вводилась.

## Сервер и миграция

- `PlaceReviewCooldown(place,user,next_allowed_at)` с уникальной парой хранится независимо от отзывов. Удаление отзыва не обходит ожидание.
- Слот резервируется условным UPDATE внутри transaction.atomic, создание pending-записи входит в ту же транзакцию. Ошибка сохранения откатывает резервирование. Bootstrap уникальной пары вне claim transaction избегает SQLite read→write upgrade race.
- Повтор раньше срока: AJAX HTTP 429, Retry-After, code=review_cooldown, серверные временные метки. Обычный POST сохраняет messages→redirect; GET восстанавливает таймер.
- `0103_place_review_cooldown` создаёт gate, переносит стартовые сроки из существующих отзывов, снимает только unique_place_review_per_user, добавляет индекс place/user/created_at. Старые отзывы не удаляются и не меняются.
- Успешно применено только к подтверждённой локальной SQLite под /app. План включал неприменённые prerequisites 0101 (unique email, предварительно 0 duplicate groups) и 0102 (таблица volunteer revision); обе прошли. Данные аккаунтов не объединялись/удалялись. Production не изменялся.
- После появления нескольких отзывов обратное восстановление старого unique constraint потребует отдельного решения по истории; автоматическое удаление дублей при rollback не предусмотрено.

## UI

Общий flash/info-компонент, clock SVG, крупный MM:SS и тонкий progress. RU/AZ/EN. Таймер присутствует на AJAX success, после redirect и reload, а также при 429 из другой вкладки. Он рассчитывается от server_now и монотонного performance.now; изменение часов компьютера не сокращает ожидание. По истечении срока форма автоматически появляется. Черновик заблокированного запроса сохраняется; предупреждение об ожидании снимается при завершении таймера. Success-подтверждение полученного отзыва остаётся отдельно.

Изменён сетевой текст: больше нет ложного обещания, что повторная отправка обновит старый отзыв. Галочка анонимности ранее убрана; минимальная длина формы по-прежнему 3 символа, оценка обязательна.

## Админка

Проверено кодом, Django tests и реальным браузером на синтетической записи:
- просмотр карточки отзыва и полной формы;
- публикация → approved; скрытие → pending; отклонение → rejected;
- GET показывает подтверждение и не удаляет запись;
- POST с подтверждением удаляет; массовое удаление тоже требует подтверждения;
- одиночные/массовые операции пересчитывают rating_count/rating_avg;
- staff без нужных permissions получает 403 на approve/hide/reject/delete.

Функциональность админки уже была реализована; её код в этой задаче менять не потребовалось. Обычный выданный тестовый аккаунт не получает админских прав. Существующие права owner/team на модерацию также не изменены.

## Файлы

- `src/catalog/models/review.py`, узкое дополнение экспорта в `models/__init__.py`.
- `src/catalog/migrations/0103_place_review_cooldown.py`.
- `src/catalog/services/place_review_submission.py`, `review_use_cases.py`.
- `src/catalog/controllers/place_controller.py`, `src/catalog/views.py`.
- `src/catalog/templates/catalog/place_detail.html`.
- `src/catalog/templates/catalog/includes/review_cooldown.html`, `review_submission_notice.html`.
- `static/js/review_submission.js`, добавленные правила в `static/css/site.css`.
- `locale/{ru,az,en}/LC_MESSAGES/django.po`; локальные .mo скомпилированы.
- `src/catalog/testcases/test_place_review_cooldown.py`, адаптация `test_review_confirmation.py` к нескольким place reviews без ослабления site/specialist контрактов.
- `scripts/test_review_cooldown.cjs`.
- План `docs/superpowers/plans/2026-09-07-repeat-place-reviews.md`, этот отчёт.

Прежние dirty changes Google/volunteer/header/pricing не переписывались. Commit/push/deploy не выполнялись.

## Проверки

**54 tests, OK**, 49.017s, изолированная SQLite, LocMem cache, окружение очищено, DJANGO_TESTING=1:

```bash
env -i PATH="$PATH" DJANGO_TESTING=1 DJANGO_DEBUG=1 DATABASE_URL=sqlite:////tmp/kidsmap-review-tests.sqlite3 .venv/bin/python manage.py test catalog.testcases.test_review_confirmation catalog.testcases.test_place_review_cooldown catalog.testcases.public.TestReviewEnhancements catalog.testcases.auth_access catalog.testcases.admin.ReviewAdminModerationTests catalog.testcases.admin.TestReviewRatingSyncAndAdminBulkActions --noinput
```

Новый regression до реализации: ожидался 429 на 119-й секунде, получен 200. После реализации: граница 119/120, сохранение approved history, отдельный pending, независимость пользователей/мест, delete-resistant cooldown, rollback при save error, отсутствие таймера после validation error, восстановление GET, delete/bulk delete/permissions — PASS.

Chromium, отдельный localhost:18763 с synthetic fixtures и сокращённым тестовым интервалом **3 секунды**:

```bash
PLAYWRIGHT_MODULE=/home/ramin/.npm/_npx/31e32ef8478fbf80/node_modules/playwright CHROMIUM_EXECUTABLE=/home/ramin/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome REVIEW_BROWSER_CONFIG=/tmp/review-browser-config.json node scripts/test_review_submission.cjs
PLAYWRIGHT_MODULE=/home/ramin/.npm/_npx/31e32ef8478fbf80/node_modules/playwright CHROMIUM_EXECUTABLE=/home/ramin/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome REVIEW_BROWSER_CONFIG=/tmp/review-browser-config.json node scripts/test_review_cooldown.cjs
```

Оба exit 0: прежняя полная матрица RU/AZ/EN × 375/768/1024/1440, errors/retry; новый timer success/reload/expiry, wall-clock tampering, прямой ранний POST 429/Retry-After, реальные конкурентные HTTP-запросы **200 + 429**, устаревшая вкладка сохраняет черновик и после ожидания отправляет новый отзыв. JS pageerror 0. Скриншот `/tmp/review-cooldown-mobile.png` просмотрен (на тестовом стенде показывает 00:03).

`node /tmp/review-admin-browser.cjs` — отдельная синтетическая запись, реальные editor/approve/hide/reject/delete pages и подтверждения: PASS, JS exceptions 0.

Пользовательский `localhost:8000`: runtime cooldown_seconds=120, migration0103 applied=True; place304 и login HTTP200. Local Gunicorn workers перезагружены. В браузере полный двухминутный цикл на пользовательском аккаунте не выполнялся: он проверен на изолированном стенде с тем же кодом и коротким интервалом.

`makemigrations catalog --check --dry-run`: No changes detected. `git diff --check`, node syntax и msgfmt checks: exit0.

## Ограничения

PostgreSQL-конкурентность отдельно не запускалась; конкурентные HTTP tests проведены на файловой SQLite. Гостевой режим, если его отдельно включить, сохраняет прежнюю логику и не покрывается новым per-user timer. Без JavaScript countdown не тикает; серверное ограничение остаётся действующим. Ранее отмеченный localhost page-transition error вне формы этой задачей не исправлялся.
