# Кабинет волонтёра: реализация и проверка

Дата: 2026-09-07. Срез: dirty LOCAL WORKTREE поверх `dba2225c0e1d5c41a4406cf7cb9f9ce018b2c648`. Production для этой доработки не менялся. Пользователи, пароли и назначения ролей не менялись. Существующие независимые изменения рабочей копии сохранены.

## 1. Как определяется своё место

Единственный контракт — `services/volunteer_places.py::own_places(user)`: активный staff из стандартной Django-группы `KidsMap Volunteers`, `Place.created_by=user`, `owner IS NULL`, `deleted_at IS NULL`, `is_temporary=False`. Superuser не считается ограниченным волонтёром. После передачи владельцу место исчезает из workspace. `created_by` не даёт права owner публичного кабинета. Новая RBAC/ownership/status-модель не добавлена.

## 2. Object permissions

Список, поиск, счётчики, пагинация, просмотр, редактирование и фото начинаются с ограниченного queryset. Чужой объект на workspace detail/edit/photo возвращает 404, включая GET/POST. Сохранение повторно проверяет доступ в сервисе. Поля автора, владельца, статуса публикации, удаления и административных признаков исключены из входного контракта формы. Версия редакции и исходный snapshot защищают от устаревшего сохранения и одобрения.

## 3. Защищённые маршруты

| Маршрут / область | Правило |
|---|---|
| `/admin/volunteer/` | Только собственные permanent places; поиск и все цифры в том же queryset |
| `/admin/volunteer/add/` | Создание от текущего пользователя, непубличный draft |
| `/admin/volunteer/<id>/` | Просмотр только своего объекта; чужой ID — 404 |
| `/admin/volunteer/<id>/edit/` | GET/POST только своего объекта; явный action allowlist |
| `/admin/volunteer/<id>/photo/main/`, `.../cover/` | Проверка своего Place перед чтением файла, private/no-store/nosniff |
| `/admin/volunteer/review/`, `.../review/<id>/` | Проверка и решение только Superadmin |
| Обычный Django admin, Place changelist/change/delete/bulk, autocomplete, add-choice | VolunteerAccessMiddleware запрещает даже при случайном назначении широких Django permissions |
| Owner routes, ownership request, owner photo upload/reorder/delete/cover, документы специалиста | Закрыты для волонтёра; локализованные варианты также учитываются |
| Public detail/pricing/phone API | Непубличные карточки не выдаются; опубликованные страницы остаются публичными |

Обёртка `admin.site.admin_view` сохраняет staff/auth/CSRF и cache policy. Middleware оставляет только workspace, вход/выход и смену собственного пароля. Скрытие меню дополняет backend, не заменяет его.

## 4–5. Возможности и запреты

| Действие | Волонтёр | Superadmin |
|---|---|---|
| Создать своё постоянное место | Да | Да |
| Посмотреть/изменить свою рабочую карточку | Да, через редакцию | Да |
| Сохранить неполную карточку | Да, при минимально валидной форме | Да |
| Отправить на проверку, прочитать замечания, исправить | Да | Да |
| Просмотреть/изменить чужие непубличные карточки | Нет | Да |
| Опубликовать / снять с публикации / модерировать | Нет | Да |
| Удалить место | Нет | Да |
| Сменить автора/owner/admin flags через workspace | Нет | Управление через штатную админку |
| Пользователи, сотрудники, groups/permissions, SEO, настройки, справочники | Нет | Да |
| Owner-кабинет / его API | Нет | Отдельная существующая owner policy |

## 6. Модерация и состояние

Используются существующие `Place` и `VolunteerPlaceRevision`. Правки хранятся в payload редакции; публичная версия не меняется до одобрения Superadmin. Поток: draft → pending → approved либо rejected → исправление → pending. Замечание сохраняется при промежуточном сохранении исправлений; при новой отправке начинается следующий цикл проверки. Одобрение атомарно проверяет версию, snapshot и каноническую готовность, затем применяет данные/тарифы/расписание/фото.

Статус dashboard вычисляется, а не записывается в новую колонку: текущая draft/pending/rejected редакция приоритетна; затем live published+active, pending/rejected Place, published+inactive («Снято с публикации»), иначе draft. Поэтому опубликованное место с ожидающими правками входит в «На модерации», а рядом явно написано, что прежняя версия остаётся на сайте. Счётчики описывают текущее состояние, не историю всех отправок.

Готовность берётся из существующего `place_readiness`, включая предложенное расписание. Список недостающего ведёт к полям того же мастера. Пересчёт — после серверного сохранения; отдельного клиентского readiness-контракта нет.

## 7. Файлы доработки workspace

- Новые: `src/catalog/services/volunteer_dashboard.py`, `src/catalog/testcases/test_volunteer_dashboard.py`.
- Backend: `src/catalog/domain_admin/volunteer.py`, `src/catalog/domain_admin/__init__.py`, `src/catalog/volunteer_middleware.py`, `src/catalog/services/volunteer_places.py`, `src/catalog/volunteer_forms.py`.
- Общий мастер: новый `src/catalog/templates/pages/includes/permanent_place_workspace.html`; существующие `src/catalog/templates/pages/permanent_place_form.html`, `static/js/permanent_place_wizard.js`.
- UI: `src/catalog/templates/admin/volunteer/{base,index,edit,detail,place_card,editor_status,icon}.html`, `templates/admin/base.html`, `static/admin/css/pages/volunteer.css`.
- Переводы: `locale/{az,en,ru}/LC_MESSAGES/django.po`.
- Документы: этот отчёт, `docs/ADMIN_ROLES_AND_PERMISSIONS.md`, `docs/superpowers/plans/2026-09-07-volunteer-workspace-ux.md`.

Полный `git status` содержит также более раннюю реализацию роли/профиля сотрудника и независимые доработки отзывов/header/auth. Этот список относится именно к текущему workspace UX.

## 8. Что изменено визуально

Заголовок и основная CTA, собственная статистика, вкладки статусов, поиск, пагинация по 12 мест; карточки с фото, категорией/подкатегорией, адресом, статусом, готовностью, обновлением и действием по состоянию. Отдельные состояния первого входа и пустого поиска. Замечания модератора остаются видны в карточке и просмотре. Минимальное меню с именем/аватаром/ролью. SVG, фирменные цвета, focus/reduced-motion и мобильная компоновка.

Создание/изменение использует общий семишаговый permanent-place wizard: существующие поля, тарифы, расписание, карта и навигация. Ограниченная VolunteerForm остаётся адаптером текущего proposal-сервиса. Owner-форма продолжает использовать свой photo adapter; волонтёр загружает главное фото/обложку обычным multipart POST. Owner API для него не открывались. Локальное сохранение волонтёрского payload в localStorage выключено. Уведомления идут через существующие Django messages админки.

## 9. Security / regression tests

Финальная команда на изолированной SQLite:

```sh
.venv/bin/python scripts/check_volunteer_admin.py \
  catalog.testcases.test_volunteer_dashboard \
  catalog.testcases.test_volunteer_admin \
  catalog.testcases.permanent_place_wizard \
  catalog.testcases.photo_workflow \
  catalog.testcases.owner.TestPlaceScopedAccessIsolation \
  catalog.testcases.owner.TestCreatedByIsAuditOnly \
  catalog.testcases.test_staff_profile
```

Результат: 94 теста, OK, 1 PostgreSQL-only пропущен, 61.553 s. Log: `/tmp/kidsmap-workspace-final-tests.log`.

Та же команда с `--postgres` сразу после имени runner выполнена на одноразовом PostgreSQL 17 в tmpfs (`127.0.0.1:55446`): **94/94 OK, без пропусков, 67.940 s**, включая конкурентную модерацию. Log: `/tmp/kidsmap-workspace-postgres.log`. Django check и makemigrations --check --dry-run: No issues / No changes detected. `git diff --check`, `node --check static/js/permanent_place_wizard.js`, `msgfmt --check` для AZ/EN/RU успешны.

Проверяются A/B isolation, поиск/счётчики/пагинация, чужой GET/POST/AJAX/локализованные URL, bulk/delete/autocomplete, случайные широкие permissions, ownership/admin-field spoofing, private public APIs, photo routes, owner API, handover/deleted/temporary исключения, superadmin обеих карточек, CSRF, stale versions, readiness, публичная старая версия, возврат и повторная отправка, сохранение замечания в draft, штатный owner wizard и профиль сотрудника. Два новых дефекта сначала воспроизведены тестами: потеря замечания после draft и 405 вместо 404 при чужом POST на новые preview/photo routes.

Runner очищает окружение до settings, выставляет DJANGO_TESTING=1, изолирует DB/cache/media/mail и блокирует неожиданные HTTP-запросы. Production credentials/data не используются. Полный проектный suite в этой итерации не запускался; прежние 14 baseline-падений общего admin-suite описаны в документе ролей.

## 10. Browser QA

Реальный headless Chromium на отдельной синтетической fixture: создание draft → отправка → возврат Superadmin с замечанием → исправление → повторная отправка. Проверены pending preview, опубликованная прежняя версия, чужой URL 404, поиск/фильтры, переход из readiness к полю, пустой кабинет и общий семишаговый мастер. Owner входит через публичную форму и использует прежний мастер/photo adapter.

AZ/EN/RU переключены настоящим языковым меню; на каждом языке проверены 1920/1440/1280/1024/768/390/360 px. Горизонтального overflow и JS page errors не обнаружено. Дополнительно шаги мастера проверены на desktop/tablet/mobile. Логи: `/tmp/kidsmap-dashboard-browser.log`, `/tmp/kv-language-owner.log`. Снимки: `/tmp/kv-dashboard-final-desktop.png`, `/tmp/kv-dashboard-viewport.png`, `/tmp/kv-wizard-mobile.png`, `/tmp/kv-dashboard-empty.png`. Это локальные артефакты, не production evidence и не постоянное хранилище.

## 11. Остаточные ограничения

- Проверенные workspace/API маршруты не позволяют получить или изменить чужую непубличную карточку, зная её Place ID. Это не утверждение о полном аудите всех маршрутов проекта.
- **Общее media-хранилище остаётся публичным по точному URL файла.** `deploy/nginx/kidsmap.az.conf` отдаёт `/media/` через alias без проверки пользователя. Protected photo endpoint закрывает доступ по чужому Place ID, но не отзывает существующий прямой media URL. Для конфиденциальности самих proposal-фото нужен отдельный private storage и согласованная схема выдачи/публикации; здесь она не внедрена. Production-конфигурация в этой итерации не проверялась.
- Чужая уже опубликованная карточка доступна всем на публичном сайте — это сохранённая public policy, не доступ к её draft/proposal.
- Volunteer upload поддерживает главное фото и обложку, не полную owner-галерею. Не добавлены новая история модерации или отдельная модель статусов.
- Проверка на production, полный penetration test, полный browser-аудит owner/admin, нагрузочные проверки и релиз не выполнялись. Не следует выкладывать весь dirty worktree целиком.

Локальный предпросмотр `http://127.0.0.1:8766/admin/` перезапущен с сохранённой синтетической базой. Вход reviewer/volunteer проверен реальным Chromium; volunteer dashboard и семь шагов мастера доступны, JS errors отсутствуют. Одноразовые PostgreSQL и QA-сервер 8767 остановлены; 8766 оставлен для проверки пользователем.

## Уточнение пользователя: административная форма вместо owner-мастера

2026-09-07, следующий локальный этап. По новому скриншоту пользователя volunteer edit/add переведены с семишагового owner-shell на административную форму из пяти разделов: Основное, Цена и возраст, Локация, Фото, Проверка. Предыдущее описание семи шагов выше относится к предыдущей итерации; owner-кабинет сохраняет свой мастер.

Переиспользованы admin `kidsmap_place_form.css`, section/nav/field и language markup; существующие restricted VolunteerPlaceForm, редактор тарифов, расписание и карта. Новый `services/volunteer_editor.py` подготавливает только presentation context, включая каноническую готовность. Сохранение/отправка по-прежнему идут через proposal service. Статус, публикация, verified, owner/creator и ordinary admin actions не добавлены.

Инструкция — доступный modal с шестью шагами по заполнению и модерации, AZ/RU/EN; Escape закрывает его и возвращает фокус. Это инструкция сотруднику, не JSON prompt/import из суперадминской формы. JSON import/export и глобальный поиск дублей не открывались. Тексты явно объясняют серверный пересчёт готовности после сохранения. Вкладки языков поддерживают стрелки/Home/End; есть сворачивание/раскрытие разделов, ссылки к полям ошибок/readiness, предупреждение о несохранённых изменениях, preview нового главного фото. Дополнительные поля находятся в раскрывающихся блоках; каждое поле restricted form присутствует ровно один раз.

Файлы этого этапа: новые `src/catalog/services/volunteer_editor.py`, `src/catalog/templates/admin/volunteer/place_form.html`, `static/admin/js/volunteer_place_form.js`, `static/admin/css/pages/volunteer_place_form.css`; обновлены `domain_admin/volunteer.py`, `templates/admin/volunteer/edit.html`, общий `templates/admin/catalog/place/form/section_basics.html` (только условный текст volunteer), `testcases/test_volunteer_dashboard.py`, план `2026-09-07-volunteer-admin-form.md` и этот отчёт.

Проверки:

- UI contract сначала упал на отсутствии нового административного шаблона. Теперь дополнительно проверяет пять разделов, инструкцию, ровно одно вхождение каждого разрешённого поля и отсутствие privileged controls/endpoints.
- Команда из раздела 9 (те же семь labels, SQLite): **94 tests OK, 1 PostgreSQL-only skip, 60.865 s**. `/tmp/kv-admin-form-final-tests.log`. DB locking/moderation backend в этом этапе не менялся; PostgreSQL повторно не запускался.
- После финальной группировки дополнительных полей: `scripts/check_volunteer_admin.py catalog.testcases.test_volunteer_dashboard` — **14/14 OK, 5.326 s**, `/tmp/kv-admin-form-last-tests.log`.
- Реальный Chromium: create → draft, existing draft → submit, язык полей, instruction/Escape/focus, collapse/expand, age-open-ended, добавление тарифа; 1920/1440/1280/1024/768/390/360 без горизонтального page overflow и pageerror. AZ/EN/RU дополнительно на 1440/768/360. Логи `/tmp/kv-admin-form-browser.log`, `/tmp/kv-admin-form-languages.log`, снимки `/tmp/kv-admin-form-top.png`, `/tmp/kv-admin-form-small.png`.
- `git diff --check` и `node --check static/admin/js/volunteer_place_form.js` успешны. Новые копии UI переводятся через существующий trilingual helper, дополнительных PO-строк нет.

Ограничение public media из раздела 11 остаётся. Production не менялся. Локальный preview 8766 использует сохранённую базу и прежние тестовые аккаунты.
