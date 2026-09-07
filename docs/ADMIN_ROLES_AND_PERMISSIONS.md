# Роли и права админки KidsMap

Срез: 7 сентября 2026. LOCAL HEAD `dba2225c0e1d5c41a4406cf7cb9f9ce018b2c648` + рабочие изменения. Новая роль реализована локально; это **не подтверждение её включения в production**. Существующие четыре административных аккаунта сохранены. В рамках этой доработки их флаги, группы и permissions не менялись. Личность аккаунта владельца для первоначального запроса Superadmin остаётся неуточнённой.

## Как работать с волонтёрами

1. Superadmin открывает **Сотрудники админки → Добавить** и выбирает **Волонтёр — только свои места, публикация после проверки**.
2. Создаётся обычный Django User: `is_active=True`, `is_staff=True`, `is_superuser=False`, группа `KidsMap Volunteers`. Прямые model permissions не выдаются. Подмена `is_superuser` в POST создания с ролью volunteer не повышает права.
3. После входа в `/admin/` волонтёр попадает в **Мои места**. Доступны создание, сохранение черновика и отправка на проверку.
4. Superadmin открывает **Волонтёры → Изменения волонтёров**, видит сравнение текущего и предложенного содержимого, одобряет публикацию либо возвращает с обязательным комментарием.

Своими считаются только постоянные, неудалённые места с `created_by` этого волонтёра и без назначенного бизнес-владельца. Передача владельцу прекращает доступ волонтёра. Чужие места отсутствуют в его рабочем списке; прямые GET/POST к ним возвращают 404. Публичный каталог остаётся общедоступным — ограничение касается административных данных.

Волонтёр может менять сведения о месте, контакты, возраст, категории, основное/резервное фото, тарифы и расписание. Галерея дополнительных фотографий остаётся в обычной админке. Он не меняет автора, владельца, slug, рейтинги, verification-флаги, рекомендации главной, публикацию и удаление.

## Как сохраняется опубликованная версия

`VolunteerPlaceRevision` хранит одну текущую редакцию, исходный снимок, состояние (`draft/pending/approved/rejected`), номер версии, автора и решение проверяющего. Первое сохранение создаёт непубличный Place с `status=draft`, `is_active=False`. Последующие сохранения волонтёра меняют редакцию, а не публичный Place.

Одобрение — отдельный POST только активного staff-superuser. В одной транзакции блокируются Place и редакция, проверяются версия и исходный снимок, форма, общая publication readiness; только затем изменяются Place, тарифы и расписание и добавляется `PlaceChangeAudit`. Повторное/одновременное одобрение не применяется дважды. Если администратор изменил исходную карточку, старый черновик не может затереть его правки. Волонтёр может явно заменить свой черновик текущей версией и начать заново. Возврат на доработку не меняет опубликованное содержимое.

Новые фото проходят существующую нормализацию изображений и сохраняются под отдельными именами. Публичное фото не перезаписывается и не удаляется при редактировании черновика. История одобренных изменений остаётся в аудите Place; редакция не является архивом всех промежуточных черновиков. Автоматическая очистка неиспользованных файлов в эту задачу не входит.

## Фактическая модель доступа

Используется стандартный Django User/ModelBackend, `is_active`, `is_staff`, `is_superuser`, `user_permissions` и `groups`. Отдельной новой RBAC-системы нет.

**Модератор** и **Контент-менеджер** — существующие presets прямых permissions при создании сотрудника, а не сохранённое поле роли. После ручного изменения permissions пользователь может отличаться от preset. **Волонтёр** определяется членством в стандартной Django-группе. Группа создаётся при первом создании волонтёра; миграция не изменяет существующих пользователей и роли.

У Superadmin стандартные Django permissions не требуют ручного добавления всех разрешений/групп. Это не отменяет read-only audit-модели, singleton-ограничения настроек, readiness и другие явные бизнес-проверки проекта.

| Роль | Назначение / просмотр | Создавать | Редактировать свои | Редактировать чужие | Удалять | Публиковать | Модерировать | Пользователи / сотрудники | Системные настройки |
|---|---|---|---|---|---|---|---|---|---|
| Superadmin | Все зарегистрированные области | Да, кроме явно read-only/singleton-моделей | Да | Да | Да, с существующими защитами | Да, при readiness | Да, включая редакции волонтёров | Да | Да |
| Волонтёр | Только свои места в рабочей админке | Места-черновики | Только предложенные изменения | Нет | Нет | Нет; отправляет на проверку | Нет | Нет | Нет |
| Модератор (preset) | Места, события, отзывы о местах/сайте, заявки на владение | Нет | Только доступные отзывы/заявки | Те же отзывы/заявки | Нет | Не места/события | Отзывы и заявки на владение | Нет | Нет |
| Контент-менеджер (preset) | Места, события, категории, подкатегории, фото и разделы настроек ниже | Места, события, категории, подкатегории, фото | Да, в разрешённых моделях | Да, в разрешённых моделях | Только PlacePhoto и SiteGalleryImage по preset | Места и события | Может менять статусы мест/событий; не отзывы и не редакции волонтёров | Нет | **Да: существующий preset это разрешает** |
| Staff без permissions | Вход в admin, существующий dashboard | Нет по стандартным model permissions | Нет по стандартным model permissions | Нет по стандартным model permissions | Нет | Нет | Нет | Нет | Нет по model permissions |
| Пользователь / бизнес-владелец | Публичное содержимое и собственные доступные места в кабинете | Через существующий owner-поток | По object-scoped правам | Только явно доступные места команды | По существующему `place.edit` (soft delete) | Нет без отдельного staff-разрешения | По правам команды конкретного места | Только команда места при `place.team.manage` | Нет |
| Anonymous | Только публичное содержимое | Нет | Нет | Нет | Нет | Нет | Нет | Нет | Нет |

Примечание к staff без permissions: кастомный dashboard и счётчики доступны шире обычных ModelAdmin. Это существующая особенность, а не обещание полной изоляции старых staff-аккаунтов. Для волонтёров стандартный dashboard закрыт, общие счётчики и ссылки не выводятся.

| Область | Superadmin | Модератор preset | Контент-менеджер preset | Волонтёр |
|---|---|---|---|---|
| Django admin | Все разрешённые моделью операции | По preset | По preset | Только workspace, свой пароль и выход |
| Роли / permissions / создание superuser | Поля прав пользователей и создание сотрудника | Нет | Нет | Нет |
| SEOAuditRun / SEOIssue / SEOChange | Да, с read-only ограничениями | Нет | Нет | Нет |
| Category / Subcategory | Да | Нет | Просмотр / добавление / изменение | Выбор существующих в своей форме; управление запрещено |
| Region / District / MetroStation / специализации | Да | Нет | Не включены в preset | Управление запрещено |
| Настройки branding/about/contacts/footer/empty-state и SiteSettings | Да | Нет | Просмотр / изменение | Нет |
| Visibility settings / Analytics / CatalogContentSettings | Да | Нет | Не включены в preset | Нет |
| События | Да | Просмотр | Добавление / изменение / публикация | Нет |
| Специалисты и их отзывы | Да | Не включены в preset | Не включены в preset | Нет |
| Документы специалистов | Существующий staff/owner/public ACL | Старый ACL допускает staff | Старый ACL допускает staff | Download endpoint запрещён |
| Отзывы о местах / сайте | Да | Просмотр / изменение / модерация | Нет | Нет |
| Заявки на владение | Да | Просмотр / изменение / решение | Нет | Нет |
| Рекомендации на главной | Да | Нет | Через `change_place` | Нет |
| Аудит / служебные данные | По ограничениям модели | Не включены в preset | Не включены в preset | Нет |

Роли команды места из `place_access.py` не являются сотрудниками админки:

| Роль команды | Просмотр | Изменение | Статистика | Модерация отзывов | Управление командой | Публикация по умолчанию |
|---|---|---|---|---|---|---|
| MANAGER / прямой владелец | Да | Да | Да | Да | Да | Нет |
| MODERATOR | Да | Нет | Да | Да | Нет | Нет |
| EDITOR | Да | Да | Нет | Нет | Нет | Нет |

`created_by` подменяет владельца только пока у места нет `owner`. Старые team memberships с `place=NULL` не расширяют права. У волонтёра этот альтернативный owner-доступ намеренно запрещён: все его изменения проходят через редакции.

## Ограничения на backend

- `VolunteerAccessMiddleware` проверяет разрешённый маршрут, включая `/ru/admin/` и `/en/admin/`. Обычные admin URLs, actions, autocomplete, owner-потоки и документы специалистов запрещены даже при случайно добавленных model permissions.
- Сами workspace-сервисы повторно проверяют активность/staff/группу, автора места и назначенного владельца. Сервисы owner/place permissions также не дают волонтёру обойти workspace.
- Поля редакции заданы allowlist; переданные `owner`, `created_by`, `status`, `is_active`, `is_verified`, `is_superuser` не становятся редактируемыми полями.
- CSRF обязателен. GET не публикует. У волонтёра нет действия удаления. Одобрение доступно только Superadmin, без делегирования старому preset модератора.

## Найденное наследие — без автоматического изменения

1. Контент-менеджер имеет `change_sitesettings` и права изменения нескольких разделов настроек. Это шире чистого наполнения контентом; пересмотр требует отдельного решения. Preset сохранён.
2. Обычный staff-флаг в старом ACL допускает чтение документов специалистов; стандартный dashboard выдаёт общие счётчики. Для новой роли оба пути закрыты; общие правила остальных сотрудников не переписаны.
3. Group снят с регистрации в Django admin; существующие формы редактируют `user_permissions`, но не дают отдельный экран управления группами. Новая роль выбирается при создании сотрудника. Не следует вручную выдавать ограниченным сотрудникам `change_user` / `change_staffaccessuser`: старые формы содержат `is_superuser`, а object-level ограничения на редактирование прав требуют отдельного общего аудита.
4. Старые presets moderator/content_manager не хранят название роли, список сотрудников обычно показывает общее «Админ». Волонтёр теперь подписан отдельно.
5. Устаревшие глобальные роли UserProfile удалены миграцией 0097; исторические миграции не означают действующую роль. Legacy team memberships сохранены. Новых удалений пользователей/ролей эта доработка не делает.
6. Исправлено локально в профиле сотрудника: `StaffAccessUserAdmin.save_model` выставляет активность и staff только при создании. На редактировании сохраняются выбранные флаги. Несуперадмин не может менять flags/groups/permissions в этой форме или редактировать аккаунт/пароль суперпользователя. Это не аудит всех альтернативных auth.User/UserProfile routes.

## Проверка и воспроизведение

Изоляция: Python 3.12, Django 6.0.2; `DJANGO_TESTING=1` до загрузки settings, очищенное environment, одноразовые DB/media, LocMem cache/email, IndexNow выключен, неожиданный внешний HTTP запрещён. Production credentials, данные и media не использовались.

Проверки выполнялись через `scripts/check_volunteer_admin.py` (ранние эквивалентные runner-файлы находились в `/tmp`). SQLite подходит для быстрых HTTP-тестов; тест блокировок выполняется только на PostgreSQL.

```bash
.venv/bin/python scripts/check_volunteer_admin.py
```

Для отдельного локального PostgreSQL 17:

```bash
docker run --rm -d --name kidsmap-volunteer-tests-20260907 --tmpfs /var/lib/postgresql/data -e POSTGRES_HOST_AUTH_METHOD=trust -e POSTGRES_DB=volunteer_tests -p 127.0.0.1:55446:5432 postgres:17-alpine
.venv/bin/python scripts/check_volunteer_admin.py --postgres catalog.testcases.test_volunteer_admin catalog.testcases.admin.UserAdminUXTests catalog.testcases.admin.TestAdminSidebarStructure catalog.testcases.owner.TestPlaceScopedAccessIsolation catalog.testcases.owner.TestCreatedByIsAuditOnly
docker stop kidsmap-volunteer-tests-20260907
```

Подробные результаты финального среза приведены ниже. Общий suite не объявляется зелёным: исходные падения сохраняются. Браузерные проверки выполнены в отдельном Chromium на синтетических пользователях/местах, не в production.

| Проверка | Результат |
|---|---|
| Финальная команда PostgreSQL выше: новые тесты + UserAdminUXTests, TestAdminSidebarStructure, TestPlaceScopedAccessIsolation, TestCreatedByIsAuditOnly | **64 tests, OK, 86.374 s, exit 0** |
| `check`; `makemigrations --check --dry-run` в том же запуске | No issues; No changes detected |
| Общий прогон в ходе работы: volunteer/admin/owner/auth_access/auth_flow/place_readiness | 361 tests, 662.222 s: **347 прошли, 14 упали** |
| Повтор только этих 14 тестов в отдельной копии без изменений роли | **Те же 14 падений**, 37.376 s; наборы совпали |
| Реальный Chromium: изменение названия и тарифа → review → публикация, затем создание черновика | PASS; зависимые подкатегории работают; JS page errors отсутствуют |
| Языки и адаптивность рабочего раздела | AZ/EN/RU проверены реальным переключателем, в том числе подпись отправки; 375 / 768 / 1024 / 1440 px, без горизонтального overflow и JS page errors |
| gettext и diff | `msgfmt --check` AZ/EN/RU; `git diff --check` — exit 0 |

Целевые тесты проверяют в том числе чужие GET/POST, случайно выданные широкие permissions, подмену автора/статуса/флагов, запрет owner/download обходов, CSRF, сохранение прежней публичной версии и фото, readiness, возврат/повторную отправку, потерю доступа после передачи владельцу, устаревшие формы, повторное и конкурентное одобрение, создание волонтёра через штатную форму, malformed schedule, неверные контакты/изображения/подкатегории, выбор языка и отсутствие дублирующихся полей.

Исходные 14 падений — старые проверки в `catalog.testcases.admin`:

- `TestAdminChangelistUI.test_shared_search_panel_rendered_in_all_models`.
- `TestAdminOwnershipModerationUX`: `test_admin_index_dashboard_summary_uses_real_database_counts`, `test_admin_place_changelist_renders_filter_select_options`, `test_place_admin_change_form_shows_visibility_controls`, `test_place_admin_changelist_searches_by_azerbaijani_name`, `test_place_admin_changelist_shows_stats_and_quick_filter_counts`, `test_place_admin_changelist_uses_compact_search_panel`, `test_place_admin_restore_view_confirms_and_restores_place`, `test_place_admin_shows_coordinates_and_map_readiness_statuses`, `test_place_review_admin_change_form_shows_full_text_panel`, `test_site_users_changelist_shows_profile_details`, `test_user_change_form_has_no_groups_block`.
- `TestAdminTemporaryEventInputs`: `test_place_change_page_renders_single_compact_datetime_inputs`, `test_place_changelist_filters_by_staff_member_who_added_card`.

Assertions этих тестов не менялись. Baseline восстановил из HEAD только исходно чистые файлы, изменённые этой задачей; независимые рабочие изменения сохранены. Новая таблица редакций не требует копирования реальных данных для проверки. Полный suite, полный аудит старых ручных permissions и production/browser проверка реальных аккаунтов не выполнены.

После проверок одноразовый PostgreSQL-контейнер удалён, локальный браузерный сервер остановлен. Production-сервисы не перезапускались.

## Файлы этой задачи и включение

- Роль / границы: `services/staff_roles.py`, `volunteer_middleware.py`, `services/place_access.py`, `services/owner_place_use_cases.py`, `domain_admin/user.py`, `src/config/settings.py`.
- Редакции: `models/volunteer.py`, экспорт в `models/__init__.py`, миграция `0102_volunteer_place_revision.py`, `services/volunteer_places.py`, `volunteer_forms.py`.
- UI / маршруты: `domain_admin/volunteer.py`, `domain_admin/__init__.py`, `templates/admin/volunteer/*.html`, `templates/admin/base.html`, условие в существующем `pricing_editor.html`, `static/admin/css/pages/volunteer.css`; AZ/EN/RU сообщения в gettext-каталогах. `src/config/middleware.py` учитывает выбранный язык только для нового workspace; остальная админка сохраняет прежнее правило URL-языка.
- Проверки: `testcases/test_volunteer_admin.py`, `scripts/check_volunteer_admin.py`; этот документ и `docs/superpowers/plans/2026-09-07-volunteer-admin.md`.

Миграция 0102 добавляет таблицу, не меняя пользователей. Перед включением нужны согласованный релиз, применение миграции, сборка static/gettext и проверка входа/создания/проверки на сервере. В текущем общем worktree есть независимые изменения отзывов и миграция 0103, уже ссылающаяся на 0102: нельзя выкладывать весь dirty tree как будто это только роль волонтёра. Исходный production-срез нужно проверить заново перед release. Перезапуск, deploy, commit и push для этой доработки не выполнялись.

Источники правил: `models/user.py`, `domain_admin/user.py::ADMIN_ROLE_PERMISSION_PRESETS`, `domain_admin/place.py`, `domain_admin/site.py`, `domain_admin/seo.py`, `proxy_apps/catalog_moderation/admin.py`, `services/place_access.py`, `controllers/owner_places_controller.py`, `views.py::serve_specialist_document`, новые файлы выше. Документ описывает реально прочитанный код; соответствие каждой старой функции текущему production image отдельно не утверждается.


## Профиль сотрудника — локальное дополнение 2026-09-07

- Страница существующего `StaffAccessUser` теперь показывает данные аккаунта, профиль, доступ и созданные места. Используются штатные Django ModelForm/inline/CSRF/права просмотра и изменения.
- Список сотрудников распознаёт группу волонтёров и поддерживает фильтр. Количество мест считается по `Place.created_by`, включая удалённые, а не по owner. Владение местом само по себе не означает авторство.
- Метрики мест: всего создано, опубликовано (published + active), draft, pending, rejected, снято с публикации (published + inactive), soft-deleted. Удалённые входят только в total/deleted.
- Правки draft/pending/rejected считаются отдельно по текущему `VolunteerPlaceRevision` неудалённого места. Это текущее состояние, не историческое количество отправок. Опубликованное место с ожидающими правками входит в обе соответствующие метрики.
- Таблица ограничена автором профиля, имеет поиск по AZ/RU/EN названию, фильтр и страницы по 15 мест. Статистика остаётся общей при поиске. Ссылка на изменение места доступна только при model/object permission; review — только суперадмину.
- Смена группы/индивидуальных permissions находится в раскрывающемся разделе доступа. Сохранение обычных данных не назначает новую роль и не очищает существующие permissions. Группа волонтёров остаётся обычной Django group; новая RBAC не добавлена.
- Проверка: `.venv/bin/python scripts/check_volunteer_admin.py catalog.testcases.test_staff_profile catalog.testcases.test_volunteer_admin catalog.testcases.admin.UserAdminUXTests catalog.testcases.owner.TestPlaceScopedAccessIsolation catalog.testcases.owner.TestCreatedByIsAuditOnly` — 67 тестов, 66 успешно, 1 PostgreSQL-only тест пропущен на SQLite, 83.833 s. Проверки Django и отсутствие новых миграций успешны. Log вне репозитория: `/tmp/kidsmap-staff-final-tests.log`.
- Scope: dirty LOCAL WORKTREE; production не менялся. Предыдущие несвязанные изменения сохранены.
- После уточнения переводов повторены профиль и UserAdminUXTests: 20/20 успешно, 38.373 s (`/tmp/kidsmap-staff-final-locale-tests.log`). В реальном Chromium проверены сохранение имени с восстановлением исходного значения, раскрытый доступ, переключатель AZ/EN/RU и ширины 375/768/1024/1440; overflow и pageerror отсутствуют. Логи `/tmp/kidsmap-staff-browser.log`, `/tmp/kidsmap-staff-languages.log`; изображения `/tmp/kidsmap-staff-desktop-final.png`, `/tmp/kidsmap-staff-viewport.png`. Все PO проходят `msgfmt --check`, `git diff --check` успешен.
- Файлы дополнения: `domain_admin/user.py`, новый `services/staff_activity.py`, новый `templates/admin/catalog/staffaccessuser/change_form.html`, staff change_list и существующий user change_form (описания ролей при создании), новый `static/admin/css/pages/staff_profile.css`, `config/middleware.py` (выбор языка в staff-разделе), `locale/{az,en,ru}/LC_MESSAGES/django.po`, новый `testcases/test_staff_profile.py`, этот документ и план `docs/superpowers/plans/2026-09-07-staff-profile.md`.

## Кабинет волонтёра — локальная UX-доработка 2026-09-07

Добавлены собственные счётчики/поиск/статусы, карточки с готовностью и замечаниями, защищённые preview/photo routes и общий permanent-place wizard. Ownership и модерация сохранены; замечание больше не теряется при промежуточном сохранении исправлений. Финально: SQLite 94 tests OK (1 PostgreSQL-only skip), PostgreSQL 17 94/94 OK; браузер AZ/EN/RU, 360–1920 px, owner smoke. Полный отчёт с файлами, командами и ограничением публичного media-хранилища: [VOLUNTEER_WORKSPACE_AUDIT_AND_UX.md](VOLUNTEER_WORKSPACE_AUDIT_AND_UX.md). Production не менялся.

По следующему уточнению пользователя add/edit волонтёра используют административную форму из пяти разделов с инструкцией; owner-мастер остаётся отдельным интерфейсом. Restricted form/proposal backend и права не изменились. Подробности и новые проверки — в разделе «Уточнение пользователя: административная форма вместо owner-мастера» отчёта workspace.
