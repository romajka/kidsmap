# Подтверждение отправки отзывов — 2026-09-07

Реализовано в LOCAL WORKTREE поверх HEAD `dba2225c`. Production не проверялся и не изменялся. Исходные изменения каталога, CSS и Google OAuth сохранены; commit/push/deploy не выполнялись.

## Поведение

Все три формы (место, сайт, специалист) используют общий JS-обработчик и существующие flash/toast-компоненты. После подтверждённого успешного JSON-ответа форма очищается и скрывается, фокус переходит к постоянному сообщению. Дополнительно показывается toast на 9 секунд. Срок модерации не обещается. RU/AZ/EN используют gettext.

В процессе запроса повторный submit блокируется синхронно; после успеха повторная отправка той же формы заблокирована. Validation, network, timeout (30 секунд), malformed response и server errors не вызывают success, введённый текст остаётся в форме. Неоднозначный сетевой результат описывается как отсутствие подтверждения, а не гарантированная потеря отзыва. Повторный запрос авторизованного пользователя обновляет существующую запись по прежнему правилу.

Обычный POST поддерживает Django messages → redirect → GET. Уведомление показывается рядом с отзывами, включая страницу места, где общий base.html ранее полностью скрывал сообщения. Refresh после redirect не повторяет POST. Без JS сетевую ошибку навигации обрабатывает браузер; сохранение текста при ошибке гарантируется AJAX-обработчиком.

## Модерация

`PlaceReview`, `SiteReview`, `SpecialistReview` хранят `status`, `is_approved`, `rejection_reason`. Публичная отправка оставляет `pending`, `is_approved=False`; модератор публикует переводом в `approved`. Есть `rejected`. Публичные выборки исключают неодобренные отзывы. Модерация мест доступна через admin и существующие проверки прав owner/team; права не менялись. Автоматическое скрытие нецензурных слов сохранено и не означает автоматического одобрения.

Обнаружено и исправлено промежуточное сохранение PlaceReview как approved перед переводом в pending: теперь create/update получает pending сразу. Регрессионный тест до исправления наблюдал `[('approved', True), ('pending', False)]`, после — только pending. Это защита существующей ручной модерации; defaults моделей, миграции и стратегия модерации не менялись. Прямое создание PlaceReview/SiteReview через ORM по-прежнему требует явного выбора статуса — их исторические defaults approved сохранены.

Позже можно отдельно выбрать: ручную проверку всех отзывов (текущий вариант), мгновенную публикацию с последующей проверкой или автопубликацию только доверенным пользователям. Сейчас ни один новый вариант не включён.

## Изменённые файлы этой задачи

- `src/catalog/views.py` — общий JSON/POST response для трёх endpoints.
- `src/catalog/services/review_use_cases.py` — текст подтверждения места/сайта.
- `src/catalog/services/reactions.py` — pending с первого сохранения отзыва о месте.
- `src/catalog/templates/base.html` — подключение JS, общий toast event, исключение двойного flash.
- `src/catalog/templates/catalog/place_detail.html` — подключение подтверждения и формы.
- `src/catalog/templates/catalog/specialist_detail.html` — то же для специалиста.
- `src/catalog/templates/pages/site_reviews.html` — то же для сайта.
- `src/catalog/templates/catalog/includes/review_submission_notice.html` — общий постоянный notification, SVG-иконка без внешнего шрифта.
- `static/js/review_submission.js` — submission state, ошибки, duplicate lock.
- `static/css/site.css` — только добавленные в конце правила hidden и типографики notification; ранее существовавший diff сохранён.
- `locale/{ru,az,en}/LC_MESSAGES/django.po` — пять новых строк на язык; локальные игнорируемые `.mo` скомпилированы.
- `src/catalog/testcases/test_review_confirmation.py` — backend/redirect/visibility regression tests.
- `scripts/test_review_submission.cjs` — Chromium integration checks на локальных синтетических fixtures.
- `docs/superpowers/plans/2026-09-07-review-confirmation.md` — план.
- Этот отчёт.

## Проверка

Django: **28 tests, OK**, SQLite in-memory test DB, `DJANGO_TESTING=1`, LocMem cache, environment cleared, no production credentials. Exact command:

```bash
env -i PATH="$PATH" DJANGO_TESTING=1 DJANGO_DEBUG=1 DATABASE_URL=sqlite:////tmp/kidsmap-review-tests.sqlite3 .venv/bin/python manage.py test catalog.testcases.test_review_confirmation catalog.testcases.public.TestReviewEnhancements --noinput
```

Проверены: POST confirmation/refresh/RU/AZ/EN; AJAX success/duplicate/validation во всех трёх endpoints; pending с первого сохранения; отсутствие публикации pending; отсутствие success при ошибках/истёкшей сессии; существующие tests отзывов. До реализации новые тесты воспроизводили отсутствие подтверждения и JSON-контракта.

Chromium: реальная Django-страница на отдельном `127.0.0.1:18763`, отдельная `/tmp/review-preview.sqlite3` с синтетическими локальными fixtures, production credentials отсутствуют. RUN:

```bash
PLAYWRIGHT_MODULE=/home/ramin/.npm/_npx/31e32ef8478fbf80/node_modules/playwright CHROMIUM_EXECUTABLE=/home/ramin/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome REVIEW_BROWSER_CONFIG=/tmp/review-browser-config.json node scripts/test_review_submission.cjs
```

PASS: RU/AZ/EN × 375/768/1024/1440 px; один запрос при двойном submit; успех без navigation; форма скрыта только после success; notification помещается в viewport; реальные формы сайта/специалиста; validation error с настоящего backend; network/server errors через browser routing; текст сохранён; нет JS pageerror. Скриншоты `/tmp/review-{ru,az,en}-{375,768,1024,1440}.png`; мобильный RU просмотрен визуально. Внешние ресурсы намеренно блокировались: ошибки загрузки карт/виджетов не являются JS-исключениями приложения.

`git diff --check`, `node --check` для обоих JS, `msgfmt --check` RU/AZ/EN — exit 0.

Ограничения: PostgreSQL-конкурентность и production не проверялись; отключённые внешние карты/виджеты не сертифицированы. Новая защита предотвращает двойной submit в одном браузерном состоянии; существующие уникальные constraints для авторизованных пользователей сохранены. Гостевая конкурентная отправка при отдельном включении гостевых отзывов не покрывается.

## Follow-up: localhost:8000 returned 500

User reported 500 on `/place/304-raduga-kids-center/`. Local `kidsmap-web` actually mounts the full working tree at `/app`, while its installed packages predate the existing Google auth code. Filtered traceback confirmed `ModuleNotFoundError: No module named 'allauth'`. Installed the already pinned `django-allauth[socialaccount]==65.19.2` inside that local container, then sent HUP to its Gunicorn master to reload current settings/workers. No database/schema changes, application source changes or production actions.

Verified subsequent HTTP 200 for the exact AZ place URL, RU place URL, `/ru/auth/login/`, and `/static/js/review_submission.js`. Chromium rendered the place and login pages successfully. This fixes the current local container; dependency is already in requirements.txt, so future image recreation should build from current requirements rather than reuse the old image. Login credentials and authenticated login were not tested in this follow-up.

## Follow-up: заполненный текст при невыбранной оценке

Воспроизведён пользовательский сценарий: 32 символа текста, rating пустой, submit disabled, но подсказка ошибочно «Можно отправлять — готово». Новый Chromium-тест упал на этом фактическом поведении до исправления.

Исправления:
- Готовность теперь учитывает оценку 1–5, длину 20–1000 и отсутствие активного запроса. При заполненном тексте без оценки выводится «Выберите оценку звёздами, чтобы отправить отзыв.» с естественными AZ/EN переводами.
- Обязательность оценки и причины блокировки связаны через ARIA с полями/кнопкой; textarea получила доступное имя, подсказка объявляется как status.
- Подсказки-чипы больше не увеличивают текст сверх maxlength; восстановление страницы/reset синхронизирует звёзды и кнопку.
- После ошибки запроса восстанавливаются исходные элементы кнопки, включая иконку; готовность пересчитывается по актуальным полям. Отдельный regression test сначала выявил, что после ошибки пустая форма разблокируется.
- Удалена неработающая галочка скрытия имени: существующие model.save и тест `test_review_models_disable_anonymous_flag_and_keep_author_name` принудительно отключают анонимность. Вместо ложного обещания указано, что используется имя аккаунта. Backend-политика не менялась.

Дополнительные изменённые файлы: `src/catalog/testcases/auth_access.py` — две проверки старого текста обновлены на новый утверждённый заголовок+пояснение и явно используют RU URL. Проверки автора, pending, is_approved и аналитики сохранены. Это адаптация к изменённому пользовательскому контракту, не ослабление проверок. Сопутствующая работа над header/base присутствовала до этого follow-up и не редактировалась.

Свежая проверка: **38 Django tests, OK**, exit 0:

```bash
env -i PATH="$PATH" DJANGO_TESTING=1 DJANGO_DEBUG=1 DATABASE_URL=sqlite:////tmp/kidsmap-review-tests.sqlite3 .venv/bin/python manage.py test catalog.testcases.test_review_confirmation catalog.testcases.public.TestReviewEnhancements catalog.testcases.auth_access --noinput
```

Дополнительно проверены во всех трёх endpoints: нечисловая/дробная/пустая/вне диапазона оценка; превышение backend-лимита 5000; отсутствие текста по действующим правилам (место/специалист требуют текст, сайт допускает только оценку); CSRF 403 без записи; публикация approved, повторное редактирование → pending, отсутствие дубля, невидимость pending/rejected. Backend-ограничения текста не менялись: UI места 20–1000, backend принимает непустой текст до 5000.

**Chromium PASS** (`scripts/test_review_submission.cjs`, команда выше):
- RU/AZ/EN: пустая форма, текст без рейтинга, выбор каждой оценки 1–5, пробелы, границы 19/20/1000 символов, чип на максимальной длине, ArrowLeft и aria-checked.
- Изменение полей во время запроса + server error: disabled соответствует актуальной валидности, SVG кнопки сохранён.
- Реальный click по кнопке, защита от повторного submit, success без navigation, постоянное сообщение, скрытие формы: RU/AZ/EN × 375/768/1024/1440.
- Успешные реальные формы сайта и специалиста.
- Validation/network/500/malformed-200/CSRF/30s-timeout: success отсутствует, текст сохранён. Повторная успешная отправка после validation/network/500/malformed проверена.
- Нет JS pageerror. Внешние ресурсы блокировались намеренно.

**Настоящий пользовательский localhost:8000:** Gunicorn workers мягко перезагружены, вход выданным тестовым аккаунтом проверен браузером. На `/place/304-raduga-kids-center/` воспроизведён текст без рейтинга: AZ-подсказка корректна, после выбора 5 звёзд кнопка активна. Отзыв этим аккаунтом не отправлялся и не перезаписывался. Скриншот формы `/tmp/review-local-missing-rating.png` просмотрен визуально. JS pageerror: 0.

`git diff --check`, `node --check` обоих JS, `msgfmt --check` трёх каталогов — exit 0. Production не менялся. Проверки по-прежнему не сертифицируют конкурентность PostgreSQL, внешние виджеты и всю систему вне перечисленных сценариев.

## Минимум текста: 3 символа

По запросу пользователя минимум в форме места снижен с 20 до 3 символов; максимум 1000 и требование оценки сохранены. Подсказки обновлены RU/AZ/EN, `.mo` скомпилированы, локальные workers перезагружены. Browser regression до изменения: три символа оставляли кнопку disabled. После: проверка на localhost RU/AZ/EN — два символа блокируются, три принимаются при выбранной оценке, без оценки кнопка disabled. Отзывы тестом не отправлялись. В `scripts/test_review_submission.cjs` границы обновлены с 19/20 на 2/3. Backend-проверки и модерация не менялись. Предыдущие упоминания 20 в отчёте относятся к историческому состоянию.

Ограничение проверки минимума: все assertions границ 2/3 и переводов прошли, но общий финальный assert отсутствия pageerror завершил browser script с exit 1 из-за `Transition was skipped` при переключении языков (также с reducedMotion). Ошибка перехода страницы не исправлялась в задаче изменения длины; успешный полный JS-regression для этого последнего запуска не заявляется.

## Явное предупреждение при отправке без звёзд

По дополнительному запросу пользователя кнопка теперь доступна при заполненном тексте (3–1000 символов), даже если оценка пока не выбрана. Нажатие без оценки показывает общий `flash-warning` + toast: «Чтобы отправить отзыв, выберите оценку от 1 до 5 звёзд.» (RU/AZ/EN). Запрос не отправляется; текст сохраняется; фокус переводится на первую звезду; группа получает aria-invalid. После выбора корректной оценки предупреждение у формы скрывается, aria-invalid снимается. Проверка backend/moderation не менялась.

Изменения: place_detail.html, review_submission.js, review_submission_notice.html, три PO-каталога, браузерный regression script. Новый browser regression сначала падал на disabled-кнопке, после исправления PASS для RU/AZ/EN: активная кнопка без оценки, точный локализованный warning, role=alert, фокус, ноль POST, сохранение текста, снятие предупреждения после выбора звёзд. Остальная расширенная Chromium suite также PASS (включая mobile/desktop, success, duplicate, server/network/malformed/CSRF/timeout). Девять целевых Django tests `catalog.testcases.test_review_confirmation` — OK, 4.571s, изолированная SQLite, DJANGO_TESTING=1.

На localhost:8000 workers обновлены. Браузер с выданным тестовым аккаунтом подтвердил показ уведомления, ноль POST и снятие предупреждения после выбора оценки; скриншот `/tmp/review-local-rating-warning.png` просмотрен. Общий assertion pageerror локального check снова зафиксировал ранее отмеченный `Transition was skipped` после входа (exit 1); эту ошибку перехода вне формы не скрываем и не объявляем полный local check зелёным. Изолированный Chromium suite завершился с exit 0 и без JS pageerror. Production не затрагивался.

## Последующее изменение политики повторных отзывов

По новому запросу пользователя place reviews больше не обновляют старую запись: несколько отдельных отзывов, пауза 120 секунд на пользователя/место. Детали и актуальная проверка — `docs/REVIEW_COOLDOWN_2026-09-07.md`. Старые разделы этого отчёта про единственную place-запись описывают историческое поведение.
