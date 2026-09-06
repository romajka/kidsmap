# Business rules: фактический контракт KidsMap

Срез: 2026-09-06. **LOCAL:** `main`, `df6fef3` + изменённые и untracked файлы. **PRODUCTION:** чистый `86a0b8c`, ветка `readiness-legacy-migration`, catalog до `0100` по отдельной проверке оркестратора. Описанные ниже строки относятся к LOCAL; совпадение каждого поведения с production не предполагается. Production агрегаты здесь **UNKNOWN**, см. отдельный database audit.

## Публикация места

- Модель и enum: `src/catalog/models/place.py:27` (`Place`), статусы draft/pending/published/rejected. Статус, `is_active`, `deleted_at` и готовность — разные признаки.
- Основная проверка хранимой карточки: `services/place_readiness.py:568` (`evaluate_place_readiness`); формы admin: `:680` (`evaluate_form_readiness`). Все пути ниже начинаются от `src/catalog/`, если не указан иной корень.
- Readiness требует AZ-название и AZ-описание, категорию и соответствующую подкатегорию, район/регион, адрес, координаты, возраст, телефон1, цену, расписание и основное фото (`place_readiness.py:156–300`).
- Описание короче 120 символов даёт совет, но не блокирует readiness (`:164`, `:424`). Тестовые токены блокируют; это не простая подстрока `test`.
- Открытая возрастная граница заменяет `age_to`; координаты должны быть парой в допустимых диапазонах. Instagram/сайт не заменяют phone1 для readiness.
- `content_quality.py:416` (`place_quality_check`) — адаптер readiness для старого интерфейса score/errors. Не создавать вторую независимую проверку в нём.
- Admin `domain_admin/place.py:268` использует readiness. Уже опубликованная активная карточка имеет намеренную совместимость при обычном сохранении (`:269–286`), чтобы перенос legacy не блокировал её редактирование. Это не разрешение публиковать новую неполную карточку.
- Проверка значка «Проверено» `services/place_card_validation.py:87` (`validate_place_card`) отличается от публикации. Не приравнивать badge к статусу или наличию всех полей.
- Public SQL `services/content_quality.py:236` (`public_place_queryset`) мягче readiness: published/active/not deleted, адрес, контакт, возраст, цена, описание, расписание; учитывает временные карточки, feature flag, истечение и junk. Старые текстовые расписания и scalar цены сохраняют публичную совместимость.
- `published_place_queryset` (`content_quality.py:355`) проверяет только публикацию/активность/удаление. Его нельзя автоматически подменять строгим queryset: сначала установить назначение endpoint.

## LOCAL: незавершённый owner wizard

- `forms.py:1469` вызывает untracked `services/permanent_place_rules.py:15` (`publication_errors`) при отправке из owner-формы.
- Этот путь требует 120 символов описания и тариф, не учитывая освобождение free/free-entry/events от тарифов. Это реальное LOCAL расхождение с readiness, а не утверждение о production.
- Отдельная отправка сохранённой карточки вызывает `place_quality_check` (`controllers/owner_places_controller.py:877`). Одинаковое название действия ещё не означает одинаковую проверку.
- Создание/редактирование выполняются в транзакциях (`owner_places_controller.py:432`, `:605`); submit (`:852`) переводит карточку в pending, а не публикует её.
- Черновое сохранение снимает обязательность полей, но не отменяет проверки введённых типов, связей, диапазонов, файлов. Технические defaults не означают пользовательский выбор.
- Не исправлять обнаруженную рассинхронизацию в аудитном запуске. Backend + public UI + data-quality должны согласовать единый контракт в отдельном плане.

## Цена и расписание

- `Place.price_mode` существует (`models/place.py:149`): tariffs, free, free_entry_paid_services, events. Последние три обходят требование тарифа в readiness (`place_readiness.py:252`).
- `PricingPlan` — реляционный источник тарифов (`models/pricing_plan.py:11`). `services/pricing_plans.py:182` нормализует вход; `:295` заменяет связанные записи; `:461` строит публичный summary.
- `Place.pricing_plans` — compatibility property, не JSONField: pending payload → связанные тарифы → legacy JSON fallback (`models/place.py:360`). Сам JSON хранится в `pricing_plans_legacy`, DB-колонка всё ещё `pricing_plans`.
- Scalar `price_*` участвуют в публичном fallback и синхронизируются из тарифов (`pricing_plans.py:345`, `models/pricing_plan.py:247`). Нельзя удалить их по названию legacy.
- Цена exact/free/from/range/on_request, валюта, charge_role и active — разные измерения; проверять ограничения БД и нормализатор, а не только текст summary.
- Пять режимов расписания: regular, always_open, by_appointment, variable, events (`models/place.py:28`). Не путать режим always_open и круглосуточный отдельный день.
- Regular для новой readiness требует содержательных структурированных дней; старый текст даёт `legacy_schedule_not_migrated` (`place_readiness.py:276`). Другие режимы не требуют будущего Event.
- `services/place_schedule.py:300` валидирует интервалы, `:415` синхронизирует дни. Некорректный JSON в парсере `:202` превращается в default payload; влияние на сохранённые дни требует отдельной проверки.

## Доступ и владение

- `UserProfile` больше не содержит роль владельца: phone/avatar/gender (`models/user.py:19`), удаление legacy полей — migration `0097_drop_legacy_userprofile_roles.py`.
- `services/owner_place_use_cases.py:25` — только проверка аутентификации. Права вычисляются для каждого Place; нельзя вернуть глобальную роль как shortcut.
- Владельцу даются права на его карточку; `created_by` даёт права только пока owner отсутствует (`services/place_access.py:54`). После передачи creator остаётся историей, а не полномочием.
- MANAGER/MODERATOR/EDITOR имеют разные наборы прав; ни один из этих наборов сам по себе не разрешает публикацию (`place_access.py:26`). Публикация требует `catalog.change_place` либо superuser (`:78`).
- Активная team membership привязана к конкретному Place. Старые null-place memberships сохраняются, но не дают доступ (`owner_place_use_cases.py:61`).
- Ownership request доступен авторизованному пользователю; повторный pending для applicant/place ограничен (`services/ownership_use_cases.py:24`, `models/owner.py:79`).
- Модерация ownership атомарна и блокирует строку заявки (`models/owner.py:94`). Одобрение меняет owner и active, пишет аудит; глобальная роль не назначается. Одновременные разные заявки на одно место требуют отдельной проверки блокировки Place.

## Пользователи и контент

- Локальная регистрация создаёт inactive User и профиль (`controllers/auth_controller.py:74`); OTP хранится хэшем, имеет TTL, cooldown и лимит попыток (`services/email_verification.py`). Email подтверждение активирует учётную запись через существующий flow.
- Google OAuth — LOCAL untracked `google_auth.py`, allauth и migration0101; это не доказательство включения на production. Identity linking и уникальность нормализованного email требуют совместного security/database review.
- Profile email change и OTP verification — разные операции; не считать любую текущую email автоматически подтверждённой (`AuthController.update_user_profile_from_form`).
- Public rating от Place/SiteReview использует status + approval + диапазон rating + junk filter (`content_quality.py:365`); approved feed/reactions имеют отдельный queryset (`:395`).
- Отдельный Event (`models/place.py:698`) сосуществует с временным Place. Owner Event редактирует только свой draft/rejected; pending/published заблокированы для POST (`controllers/owner_events_controller.py:58`).
- Specialists имеют собственные review, location и schedule модели (`models/specialist.py`). Это не proxy над Place.
- Specialist documents: staff/owner либо verified+public diploma/certificate (`views.py:1814`). Не расширять этот доступ и отдельно сверять защиту прямого media URL.
- Фото нормализуются сервисом image_uploads; LOCAL AJAX photo flow добавляет authenticated POST, cache lock и retry ID (`photo_views.py:50`, `:74`). Удаление старых файлов в owner controller отложено до commit (`:680`, `:685`, `:940`).

## Документация и решения

`AI_HANDOFF.md` полезен как история, но его global owner-role описание устарело. Untracked `docs/PERMANENT_PLACE_FIELD_MATRIX.md` противоречит текущему коду по price_mode, наличию readiness, режимам расписания и 120 символам. Эти заявления не являются AS-IS. Перед изменениями сверять код, миграции, БД и public/admin поведение; cleanup и production writes требуют отдельного плана и разрешения.
