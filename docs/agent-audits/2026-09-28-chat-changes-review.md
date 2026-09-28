# Проверка изменений чата — 28 сентября 2026

Execution identity: основной Codex, последовательная проверка backend и rendered UI, без независимых subagents. Контракт: `.agents/agents/kidsmap-orchestrator/agent.md`. Режим: AUDIT, application fixes не выполнялись.

LOCAL HEAD: `ef949ea99a7635076e4477a29d42b0a5d63796d4`, ветка `seo-indexability-20260916`. Проверено **dirty WORKTREE**, а не только HEAD. Production: UNKNOWN, не подключались, не изменяли. FAQ/contacts и прочие ранее существовавшие изменения сохранены; авторство всех dirty UI-файлов по одному Git diff установить нельзя.

## 1. Состояние области

Проверены новые SLA-поля/сервис, предотвращение дублей, удаление волонтёрских карточек, общий редактор ревизии, фотографии, readiness и локализация. Удаление аккаунта проверено существующими тестами; включение утверждённой политики и production scheduler не подтверждены.

**Вердикт: изменения пока не готовы к релизу.** Есть воспроизводимые функциональные и визуальные дефекты. Наличие плана или трёх тестов расчёта SLA не означает готовую очередь модерации.

## 2. Сильные стороны

- Volunteer/Admin открывают рабочую ревизию; в реальном локальном браузере оба показали возраст `1–6`, готовность `3 / 12` для одной синтетической карточки. Целевые тесты общей формы, audit и конфликтов версий прошли.
- Простой повтор создания с тем же именем отклоняется; браузер показывает ошибку и ссылку на существующую карточку.
- Изолированный повторный прогон: 146 тестов, **144 passed, 1 failed, 1 skipped**. Это не полностью зелёный набор.
- `makemigrations --check --dry-run`: No changes detected. Миграция 0115 применялась при создании disposable SQLite DB.
- `git diff --check` и `node --check static/admin/js/volunteer_place_form.js`: exit 0.
- При установившемся layout на 375/768/1024/1440 px ширина документа равна viewport; общего горизонтального скролла не обнаружено. Это не исключает внутреннего обрезания отдельных компонентов.

## 3. Реальные проблемы

Все findings относятся к LOCAL dirty WORKTREE. Confidence high, кроме явно source-only/operational пунктов.

### F01 — P1: удаление черновика возвращает 403

Source: `src/catalog/volunteer_middleware.py:29–34`, новый URL в `src/catalog/domain_admin/volunteer.py:get_urls`.

`volunteer_delete` отсутствует в whitelist. `test_volunteer_can_soft_delete_own_draft` ожидает 302, получает 403. Браузерный сценарий: «Удалить черновик» → confirm → 403. Следующий шаг, владелец backend/security: согласованно исправить ACL и обработчик; не разрешать URL отдельно от F02.

### F02 — P1: обработчик удаления не проверяет допустимый статус

Source: `src/catalog/domain_admin/volunteer.py:72–91`.

Фильтр проверяет автора, отсутствие владельца/удаления и тип карточки, но не статус Place или ревизии. На синтетической **pending revision** прямой вызов view вернул 302 и установил `deleted_at`. Это диагностический вызов в обход middleware, не свидетельство доступной production-эксплуатации: обычный HTTP сейчас блокирует F01.

Также используется `select_for_update()` вне `transaction.atomic`; `ATOMIC_REQUESTS` не включён. На PostgreSQL открытие этого пути без дополнительной транзакции приведёт к ошибке при оценке queryset. SQLite эту проверку блокировки не воспроизводит. Удаление и audit сейчас не объединены одной транзакцией.

Следующий шаг, backend/security: единое серверное правило «свой draft/rejected, не pending/live», транзакция вокруг проверки/soft-delete/audit, тесты запрещённых статусов и PostgreSQL. Скрытая кнопка не заменяет серверную защиту.

### F03 — P1: дубли проверяются по старой Place, а не по рабочей ревизии

Source: `src/catalog/services/place_duplicates.py:21–39`; актуальные значения хранятся в `VolunteerPlaceRevision.payload`.

В fixture изменён `payload.name_az`, создан кандидат с новым именем; `find_creator_duplicate` вернул отсутствие дубля. После переименования можно вновь создать ту же рабочую карточку. Проверка адресов/координат тоже читает live Place: различающиеся адреса в сохранённой ревизии не дают разрешить филиал (diagnostic: `branch_override_allowed=False`).

Алгоритм дополнительно берёт только первое совпадение: нельзя безопасно разрешать новый филиал, не проверив совпадение с остальными. Последнее — source finding, отдельный HTTP/concurrency тест не запускался.

Следующий шаг, backend: сравнивать действующую рабочую проекцию всех совпадающих карточек; проверить rename, несколько филиалов и локализованные имена.

### F04 — P2: подтверждение отдельного филиала недоступно

Source: `src/catalog/volunteer_forms.py:VolunteerPlaceForm.create_as_distinct_branch`, `templates/admin/volunteer/place_form.html`.

Поле объявлено HiddenInput, но вообще не отрисовано в форме. DOM проверен в браузере: `[name=create_as_distinct_branch]` отсутствует. Ни checkbox, ни отдельного подтверждения нет. Пользователь не может выполнить утверждённый сценарий создания филиала; подстановка параметра вручную — не UI.

Следующий шаг, backend/frontend-admin: видимое явное подтверждение после показа найденных совпадений, серверное сравнение адресов/координат и audit решения.

### F05 — P2: заблокированный дубль оставляет загруженное фото

Source: `src/catalog/services/volunteer_places.py:173–189`.

Файл сохраняется **до** проверки дубля. Синтетический JPEG 1200×1200 + повторное имя: HTTP 200 с non-field error, новая карточка не создана, но в изолированном media появился один файл. Откат DB-транзакции файл не удаляет.

Следующий шаг, backend/media: проверка до записи файлов либо гарантированная компенсация; тест на отсутствие новых файлов при отклонении дубля.

### F06 — P2: мобильный readiness-блок обрезает процент

Source: `static/admin/css/pages/volunteer_place_form.css:107–155`, `place_form.html:34–48`.

На 375 px внутренний размер banner: clientWidth=276, scrollWidth=291. Badge не сжимается, остаётся в горизонтальном flex; текст слева превращается в узкую колонку, правый конец процента обрезается. Screenshot: `output/playwright/chat-review-verification-375.png`. На desktop этого обрезания не обнаружено.

Следующий шаг, frontend-admin: мобильная вертикальная компоновка и перенос badge, затем повторная browser-проверка RU/AZ/EN. CSS также использует `__body`, тогда как новый template содержит `__head`; привести selectors/markup в соответствие.

### F07 — P2: новые тексты проверки не переведены

Source: `place_form.html:38–44,48,71`; новые переводные строки без соответствующего результата в catalogs.

Браузер `html lang=az`: заголовок «Требуется доработка карточки» и длинное пояснение остаются русскими, соседние элементы азербайджанские. В EN этот заголовок также русский. Один `{% translate %}` не обеспечивает перевод.

Следующий шаг, localization/frontend-admin: дополнить и скомпилировать AZ/EN catalogs, проверить warning и ready states, duplicate/delete сообщения.

### F08 — P2: поля фото потеряли accessible labels

Source: `place_form.html:93,109,118` и поле cover_photo ниже.

Заголовки заменены на span. В DOM оба file-input: `labels.length=0`, aria-label/aria-labelledby отсутствуют. Скринридер не может отличить главное фото от обложки. Helpers/errors также не связаны с полями новой разметкой.

Следующий шаг, frontend-admin: `<label for="id_photo">`/`id_cover_photo`, связанные descriptions/errors, повторная проверка клавиатурой и accessible names.

### F09 — P2: SLA — незавершённая интеграция

Source: `services/moderation_sla.py`, `models/place.py`, `models/review.py`, `controllers/owner_places_controller.py:679`, `services/place_review_submission.py:58`, `services/reactions.py:84`.

`calculate_sla` вызывают только unit-тесты. Нет общей очереди, фильтров, deadline-индикаторов, пользовательских сроков и полной обработки needs-changes/resubmit. SpecialistReview не получил SLA-поля. Даты устанавливаются лишь в некоторых submit-путях; resolution и все остальные submit-пути не подключены. Для старых pending записей нет backfill/определённого fallback; `calculate_sla('place', None)` вызывает TypeError (локальный diagnostic).

Документ SLA называет 72/24 часа и 50/80% «Approved policy», но в видимой переписке утверждён план, не эти конкретные числа. Settings содержит эти числа литералами. Не выдавать их пользователям за согласованное обещание без подтверждения.

Следующий шаг, backend/frontend-admin: закончить утверждённый scope, отдельно зафиксировать сроки, подключить все lifecycle paths и протестировать реальные очереди/границы/права.

## 4. Tech debt

Deletion UI и backend имеют разные predicates: UI требует draft Place и draft/rejected revision либо отсутствие revision, view требует наличие revision и игнорирует статусы. Проверка имени линейно перебирает карточки автора. План предотвращения дублей содержит псевдокод тестов, а не выполненные concurrent checks.

## 5. Risks

- Нельзя исправить F01 простым добавлением URL в whitelist: это откроет F02.
- PostgreSQL блокировки/конкурентное создание не подтверждены SQLite-проверкой; пропуск теста не PASS.
- Account deletion по умолчанию fail-closed (`settings.py:183–193`). Существующий код/тесты не подтверждают включение согласованной политики, cadence cron или фактическое истечение всех backups за 15 дней. Production configuration/schedules UNKNOWN.
- Проверка не является юридической экспертизой retention policy или подтверждением production cleanup.

## 6. Dead/legacy candidates

Не удалялись. Неподключённый SLA-сервис — incomplete feature, не основание удалить его. Неиспользуемые `__body` selectors нового блока — кандидат на согласование с markup, не глобальный CSS cleanup.

## 7. Tests gaps

Не выполнены: PostgreSQL lock/concurrency, полный owner/admin/public regression suite, реальный account-deletion email/cancel/purge browser flow, production migrations/config/scheduler/backups. Google Maps ключ отключён на local fixture, внешняя карта не проверена. Обратное редактирование admin→volunteer покрыто tests, но полный browser-save roundtrip не запускался. Публичные FAQ/contacts с ранее существовавшими dirty изменениями не сертифицированы этим ограниченным review.

Executed:

```text
env -u DATABASE_URL -u LEGACY_DATABASE_URL -u REDIS_URL DJANGO_DEBUG=1 DJANGO_TESTING=1 GOOGLE_MAPS_API_KEY='' GOOGLE_MAPS_MAP_ID='' INDEXNOW_ENABLED=0 .venv/bin/python manage.py test catalog.testcases.test_volunteer_admin catalog.testcases.test_moderation_sla --noinput --verbosity 1
→ 50 tests: 48 passed, 1 failed, 1 skipped.

env -u DATABASE_URL -u LEGACY_DATABASE_URL -u REDIS_URL DJANGO_DEBUG=1 DJANGO_TESTING=1 INDEXNOW_KEY='' .venv/bin/python manage.py test catalog.testcases.test_account_deletion catalog.testcases.test_volunteer_dashboard catalog.testcases.test_review_confirmation catalog.testcases.test_place_review_cooldown catalog.testcases.place_readiness --noinput --verbosity 1
→ 96 passed.

env -u DATABASE_URL -u LEGACY_DATABASE_URL -u REDIS_URL DJANGO_DEBUG=1 DJANGO_TESTING=1 INDEXNOW_KEY='' GOOGLE_MAPS_API_KEY='' .venv/bin/python /tmp/kidsmap-chat-review-ux0n43/checks.py
→ combined 146 tests, 101.197 seconds: 144 passed, 1 failed, 1 skipped; exit 1.
```

Последний запуск — определяющий: wrapper до django.setup задаёт SQLite memory test DB, отдельный `/tmp/.../test-media`, LocMem email/cache и отключённый IndexNow. Первые два прямых запуска не переопределяли MEDIA_ROOT глобально и не используются как доказательство полной media isolation. Общий сбой тот же: `VolunteerAccessTests.test_volunteer_can_soft_delete_own_draft`, 403 != 302.

Также executed `makemigrations --check --dry-run` с DJANGO_TESTING=1/SQLite: exit 0; `git diff --check`: exit 0; `node --check static/admin/js/volunteer_place_form.js`: exit 0.

Локальный browser fixture: `/tmp/kidsmap-chat-review-ux0n43/server.py`, SQLite `/tmp/.../db.sqlite3`, отдельные media, только вымышленные пользователи/карточка, loopback `127.0.0.1:8769`, email/analytics/IndexNow/Google Maps отключены. Никаких production credentials/data. Diagnostic scripts изменяли только эти synthetic fixtures. Playwright CLI, Chromium, RU/AZ/EN. Console проверенных editor страниц: 0 errors; после intentional 403 ожидается HTTP error. Первоначальный вход без next перенаправил на 404 `/accounts/profile/`; это вне изменённого scope, baseline attribution не установлена.

Артефакты browser QA (ignored local files): `output/playwright/chat-review-{375,768,1024,1440}.png`, `chat-review-verification-{375,1440}.png`, `chat-review-photo-{375,1440}.png`, `chat-review-admin.png`, `chat-review-duplicate.png`, `chat-review-az.png`, `chat-review-en.png`, `chat-review-delete-403.png`.

## 8. Recommendations

Сначала F01/F02 единым исправлением и негативными ACL-тестами. Затем ревизии/филиалы/media в duplicate-flow, потом mobile/localization/accessibility. SLA завершать как отдельную интеграционную работу. После этого повторить targeted suite, PostgreSQL проверки и browser roundtrip. Production release не выполнять по нынешнему результату.

## 9. Приоритеты

- P0: не обнаружено, production не проверен.
- P1: F01/F02/F03 — ключевой deletion/duplicate контракт.
- P2: F04–F09 — недоступный branch flow, media leak, mobile clipping, localization, accessibility и неполный SLA.
- P3: selector/predicate drift и уточнение документации; не подменяют исправление P1.

Application code не исправлялся, чужие изменения не откатывались, commit/push/deploy не выполнялись. Следующий шаг — исправления в уже утверждённом implementation scope с failing regression tests и повторной проверкой.
