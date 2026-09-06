# Матрица постоянного места KidsMap: фактический контракт

Проверено 6 сентября 2026 года по **текущему рабочему дереву `C:\kidsmap`**, включая незакоммиченные изменения. Это описание реализации, а не желаемая спецификация и не утверждение о версии production. Источник истины — код и миграции. При изменении кода ручные разделы требуют повторного аудита.

## 1. Общие принципы

- Django `Place` хранит место; `PricingPlan`, `PlaceScheduleDay`, `PlaceScheduleInterval`, `PlacePhoto` — связанные записи. Новая публичная модель тарифов не вводилась.
- Ни модельные `blank/null/default`, ни зелёный индикатор формы сами по себе не определяют готовность к публикации.
- Различать валидацию формы, действие контроллера, административное действие, проверку значка «Проверено» и SQL-видимость каталога. Они **не полностью совпадают**.
- В этом срезе **нет поля `Place.price_mode`**, значений `free_entry_paid_services` как enum места и файла `place_readiness.py`. Поиск по моделям, сервисам, wizard, admin, SEO, importer и миграциям этого не обнаружил.
- `schedule_mode` имеет **четыре** значения. `always_open` отсутствует; круглосуточность задаётся для отдельных дней.
- 120 символов хотя бы в одном описании **всё ещё блокируют** строгую отправку, quality readiness и каталог. Это не только рекомендация SEO.
- Ручные правила ниже помечены как архитектурный аудит. Автоматический инвентарь в конце берёт поля, defaults и enums непосредственно из ORM; он не выводит бизнес-логику.

## Уровни валидации

### Owner draft

`OwnerPlaceCreateForm` / `OwnerPlaceEditForm(draft_save_only=True)` снимают `required` с полей. Можно не заполнять названия, описания, категорию, возраст, адрес/регион, телефон, фото, тарифы и содержательное расписание. Создание подставляет техническое название и fallback-категорию, если такая категория доступна: это не означает, что пользователь выбрал её. FK категории в БД остаётся обязательным.

Введённые значения проходят проверки типов, choices, длин, URL/телефонов, парности и диапазонов координат, возраста, связи подкатегории с категорией, тарифа и файлов. Неполный **добавленный тариф** не освобождается от валидации; можно сохранить пустой список тарифов. `offers_adult_classes=True` требует детский диапазон или открытую границу даже в черновике (`Place.clean`). Для расписания есть исключения: невалидный JSON может нормализоваться в пустой график, а в нерегулярных режимах ошибки скрытого недельного payload игнорируются; см. «Обнаруженные противоречия кода».

Создание: `status=draft`, `is_active=False`, `is_verified=False`, `published_at=None`, owner/created_by — текущий пользователь. При сохранении уже публичного места без явной отправки контроллер переводит его в `draft`, `is_active=False`. Черновое редактирование уже pending-карточки не обязательно меняет статус на draft.

### Owner submit for moderation

**Из мастера:** `publication_errors()` из `permanent_place_rules.py` плюс обычные проверки формы. При создании дополнительно вызывается `place_quality_check`; при редактировании — действие `submit_for_moderation` (кроме сохранения уже pending-карточки).

| Правило | Отправка из мастера |
|---|---|
| Название | Хотя бы одно непустое `name_az/name_ru/name_en`; AZ не является единственным допустимым |
| Описания | `description_az` непустое; хотя бы одно из трёх описаний после trim ≥120 символов |
| Таксономия | Категория обязательна; подкатегория может отсутствовать; выбранная должна соответствовать категории |
| Возраст | `age_from`; `age_to`, если не включён `age_open_ended` |
| Локация | `region`, `address`, пара `lat/lng`; для Баку — район; метро не требуется |
| Контакты | `phone1` обязателен и валиден; сайт/Instagram не заменяют его в этом пути |
| Фото | Именно `photo`; cover/галерея не заменяют его в строгой форме |
| Расписание | Для `regular`: текст или содержательный недельный график; для других режимов часы и примечания не обязательны |
| Цена | Активный основной структурированный тариф, включая `free` и `on_request`; исключение для существующей scalar-only карточки описано в разделе 7 |
| Качество текста | Запрещены отдельные тестовые токены из `contains_test_content` |

**Отдельная отправка сохранённой карточки из аккаунта:** `OwnerPlacesController.submit_for_moderation` проверяет `place_quality_check`, а не заново `publication_errors`. Значит, там применяются более мягкие требования к контакту, фото, возрасту, имени и району. Повторная pending-заявка отвергается. Это существенное различие путей, не универсальное правило owner-submit.

Успешная отправка создаёт/обновляет запрос модерации: `status=pending`, `is_active=False`, очищается `rejection_reason`. Она не публикует место. Сохранение уже pending-карточки через мастер оставляет её на модерации.

### Admin publication readiness

Отдельного сервиса `place_readiness.py` нет. Реальные уровни:

1. **`PlaceAdminForm.clean`:** нормализация тарифов и локации, модельные проверки; название берётся AZ → RU → EN → старое `name`. Если `is_active` либо `status=published` и нет действия `_save_draft`, `_refresh_coordinates_from_address`, `_unpublish_place`, вызывается тот же строгий `publication_errors`, что в мастере. `name_az` отдельно не требуется; подкатегория отдельно не требуется; 120 символов блокируют. `clean_location_fields` в этой форме по умолчанию требует регион/район при нечерновом сохранении.
2. **Действия `_handle_publish_submit`, `toggle_publication_view`, `mark_published`:** публикацию блокирует `place_quality_check().is_ready` — score ≥70 **и отсутствие всех errors**. Он требует имя с fallback, категорию, одно описание ≥120, один контакт из phone1/website/Instagram, адрес, обе координаты, хотя бы одну возрастную границу, цену, расписание, любое фото из photo/cover/gallery. Не требует отдельно AZ-описание, AZ-имя, подкатегорию, регион, район, `age_to` или `phone1`. При публикации: published/active, причина отклонения очищается, published_at ставится при отсутствии.
3. **`validate_place_card`:** отдельная проверка для `is_verified`, а не обязательный универсальный допуск к публикации. Проверяет фото, координаты, контакт (включая phone2/3), диапазон возраста, согласованность числовой минимальной цены, сохранённые интервалы; несоответствие района и языка даёт warnings. Не требует все поля строгого мастера.
4. **`public_place_queryset`:** отдельный SQL-допуск к каталогу/детальной странице. Не тождественен ни одному из предыдущих уровней, см. раздел 18.

Административное «Сохранить черновик» пропускает строгий publish-check и подставляет технические name/category. Простое изменение статуса в обычном save не заменяет явное действие публикации (`PlaceAdmin.save_model`). Полнота индикации в `PlaceAdmin._build_place_form_summary` не является серверным контрактом.

## 3. Place fields: как читать матрицу

Полный перечень **всех реальных полей**, включая `id`, тип, FK, default, null/blank, длину, choices и присутствие в базовых owner/admin forms находится в AUTO-GENERATED FACTS ниже. Здесь поля объединены по правилам, без повторения одной фразы в каждой строке.

| Группа Place | Пользовательская поверхность | Сохранение и публичное использование |
|---|---|---|
| `name_*`, `description_*` | Шаг 1, RU/EN раскрываются | Тексты карточки, поиск, SEO; точные fallback ниже |
| `category`, `subcategory` | Шаг 1; категория — визуальный выбор | FK, фильтры и навигация |
| `age_*`, `offers_adult_classes` | Шаг 2 | Возраст карточки/фильтров, детская и взрослая аудитория |
| `lesson_duration_minutes`, `lesson_format`, `lessons_per_week/month` | Дополнительные настройки шага 2 | Общие параметры места; не заменяют аналогичные свойства каждого тарифа |
| `district`, `metro`, `address`, `lat/lng` | Шаг 4; регион виртуальный | Адрес, фильтры, карта, маршруты, SEO |
| `phone1/2/3`, `instagram`, `website` | Шаг 5 | Контактные ссылки; дополнительные телефоны раскрываются |
| `schedule`, `schedule_mode`, `schedule_note_*` | Шаг 5 | Режим, текстовая совместимость и примечания |
| `extra_conditions*`, `additional_info*` | Дополнительно на шаге 5 | Переводы плюс старые общие тексты |
| `photo` | Шаг 6 | Главное изображение; заменяется/очищается через форму |
| `cover_photo` | Нет отдельного поля owner | Резервное изображение, owner edit сохраняет |
| Scalar prices, `pricing_plans_legacy` | Нет прямого ввода owner | Совместимость/производные значения; подробности ниже |
| Служебные поля | Не являются пользовательскими полями мастера | Исключения для технических temporary fields и эффектов действий разобраны ниже |

## 4. Rule group: Names and descriptions

| Поле | Правило / использование |
|---|---|
| `name` | Реальное обязательное модельное поле; owner не вводит напрямую. Форма вычисляет из переводов, для draft есть технический fallback; admin имеет HiddenInput |
| `name_az`, `name_ru`, `name_en` | Максимум 255. Для строгой отправки достаточно одного; ни admin form, ни quality action не требуют исключительно AZ |
| `description_az` | Непустое для строгой формы; длина может быть <120, если другое описание проходит порог |
| `description_ru`, `description_en` | Переводы могут отсутствовать; одно из них может выполнять требование длины |

`name_i18n`: EN → name_en/name_ru/name; AZ → name_az/name_ru/name; RU → name_ru/name. `description_i18n` возвращает только выбранный язык без fallback. Поэтому готовность одного описания не гарантирует описание на всех языках публичной страницы.

`place_quality_check` использует trimmed-длину; SQL `Length` и `place_catalog_visibility_reasons` — длину сохранённого текста без trim. Метка ошибки `missing_name` предлагает AZ, но её фактическая проверка допускает fallback. Генератор JSON-подсказки рекомендует минимум 120 на каждом языке; это более строгая редакторская рекомендация, не правило серверной обязательности каждого перевода.

## 5. Taxonomy

`category` — FK на `Category.code` (PROTECT); `subcategory` — nullable FK на `Subcategory` (SET_NULL). Это записи БД, а не неизменяемый список из `Place.CATEGORY_CHOICES`. Owner использует активные категории/подкатегории, локализованные подписи и зависимый выбор; при edit также сохраняет возможность выбрать текущую запись, даже если она неактивна. Старое текстовое значение подкатегории может преобразовываться в ID. Admin queryset шире, включая неактивные записи.

| Этап | category | subcategory |
|---|---|---|
| Owner draft | Можно не выбрать; контроллер подставляет fallback, если доступен | Может отсутствовать; выбранная проверяется |
| Owner wizard submit | Обязательна | Может отсутствовать; принадлежность проверяет owner clean |
| Admin form / publication actions | Категория требуется для готовности | Отдельного требования наличия нет; нельзя документировать её как обязательную admin readiness |

Клиентская зависимость не заменяет серверную проверку. У `Place.clean` нет проверки принадлежности subcategory к category; такая проверка явно есть в owner form. Это различие отмечено в разделе «Обнаруженные противоречия кода».

## 6. Audience / age

- Диапазон: age_from ≤ age_to, обе границы для строгой формы. Открытая граница: `age_open_ended=True`, age_to очищается; пустой age_from нормализуется к 0. «Все возрасты» = age_from=0 + открытая граница.
- `offers_adult_classes=False` по умолчанию. True означает дополнительные взрослые занятия при существующей детской возрастной информации, не «только взрослые».
- Длительность и частоты места могут отсутствовать. Place lesson_format: пусто / group / individual. `open_visit` существует у PricingPlan, но не является choice этого поля Place.
- Более мягкий quality-check принимает хотя бы одну границу и не применяет весь контракт возрастного режима мастера.

## 7. Pricing / price_mode / on_request

### Проверка ожидаемого price_mode

| Ожидаемое значение Place.price_mode | Фактическая реализация в этом срезе |
|---|---|
| `tariffs` | Поля/enum/default нет. Для нового места строгая форма фактически требует основной тариф |
| `free` | Режима места нет. Бесплатность задаётся `PricingPlan.price_kind=free`, price=0; пустой список не освобождает от тарифа |
| `free_entry_paid_services` | Режима места нет. Можно моделировать бесплатный основной admission + addon, но это комбинация тарифов, не специальная ветка readiness |
| `events` | Ценового режима нет. `schedule_mode=events` относится к расписанию и **не отменяет** цену Place; Event имеет собственные поля цены |

У `PricingPlan` нет связи с несуществующим price_mode. В owner/admin/SEO/import нет такой логики. Перечисленные ожидаемые режимы нельзя использовать как действующий контракт до реализации отдельной задачи.

### Основная цена

Новый строгий submit требует хотя бы один валидный активный `charge_role=primary` тариф. `addon`, `deposit`, `registration_fee` не выполняют это требование даже при `is_required=True`. До 12 тарифов суммарно, включая неактивные и доплаты.

Исключение `publication_errors`: существующая запись с PK, пустым переданным списком, без relational rows и хотя бы одним non-null scalar price допускается как legacy. Это не исключение для новой карточки. Quality/SQL отдельно допускают scalar prices, а не только структурированные тарифы. `custom_price_badge_*` не проходит за цену ни в строгом валидаторе, ни в quality/SQL.

`sync_legacy_price_fields`: только active primary AZN дают `price_from=min(low)`, `price_to=max(high)`. on_request не даёт числовых границ. Частные поля 1 урок/месяц/8 уроков заполняются при совпадении продукта, billing и quantity. Сигналы PricingPlan и replace-сервис запускают синхронизацию. Нет primary numeric AZN → соответствующие scalars становятся NULL.

`build_public_price_summary`: сначала ручная надпись; затем primary AZN; затем legacy price_from/to при отсутствии активных primary вообще. Только free → «Бесплатно». Free + paid → 0–максимум. Free + on_request без paid → «Цена уточняется». Только foreign-currency primary → надпись без числового AZN-диапазона. Наличие relational primary прекращает старый fallback.

Числовой фильтр `CatalogFilters.apply` (`services/filtering.py`) использует минимальный **платный** active primary AZN exact/from/range >0, а не надпись и не бесплатный тариф. `on_request` не превращается в 0; legacy-only/free-only тоже не дают такую числовую цену. Полный диапазон UI 0–500 трактуется как отсутствие фильтра.

### on_request

Это действующий структурированный `PricingPlan.price_kind`, с product_type и ролью, `price/price_min/price_max=NULL`. Owner разрешает его; активный основной тариф проходит строгую readiness, quality и public catalog. SEO не выдумывает числовую Offer для него.

Смысл: подтверждённая услуга, стоимость которой действительно уточняется по запросу. Подсказка JSON importer прямо запрещает подменять им ненайденные цены: если цен нет, пустой список + editor_review.missing_fields. Сервер проверяет структуру, но **не способен подтвердить источник утверждения**; source_url остаётся необязательным.

Публичная надпись неоднозначна: `build_public_price_summary` также возвращает kind=on_request/source=none при полном отсутствии данных и при невозможности AZN-сводки. **Текст «Цена уточняется» не доказывает наличие тарифа on_request.** Проверять записи и source, а не текст плашки.

## 8. PricingPlan: параметры и зависимости

Точные поля, enum-коды, defaults и DB constraints — в автотаблице. Канонический список содержит 13 product_type; «пакет» — UI/compatibility-представление lesson с quantity/package_sessions, не 14-й модельный product_type.

| Поля | Нормализация / зависимость | Owner / public |
|---|---|---|
| `product_type`, `charge_role` | addon/registration_fee/deposit требуют одноимённую роль; остальные primary. Проверка clean + DB constraint | В редакторе выбирается услуга; роль определяется типом |
| `lesson_format` | Пусто, open_visit/group/individual | Формат тарифа, отдельно от Place.lesson_format |
| `billing_mode` | one_time / recurring / installment | Оплата |
| `billing_interval/count`, `billing_cycles` | Recurring: период day/week/month/year и count>0, cycles=NULL. Installment: cycles>0, period пуст. One_time: оба вида периодов очищаются | Условные поля |
| `price_kind`, `price/min/max` | exact: price>0; free: price=0; from: min>0; range: обе границы ≥0, min≤max; on_request: все NULL. Несовместимые суммы очищаются | Визуальный выбор цены |
| `currency` | Default AZN; trim/upper, максимум 3 символа; модели не задан enum валют | Нечисловые foreign цены не смешиваются с AZN-сводкой |
| `quantity`, `quantity_unit` | Пара; если дано положительное quantity без unit, clean может подставить unit по продукту. Unit без quantity — ошибка | Объём услуги |
| `sessions_per_week/month` | Если заданы, >0 | Частота внутри тарифа |
| `is_unlimited` | Boolean; название поля именно is_unlimited, не unlimited. Нет общего модельного XOR с quantity/частотой | Показ безлимита; не приписывать несуществующий запрет сочетаний |
| `validity_interval/count` | Вместе; положительный count | Относительный срок |
| `valid_from/until` | Необязательные даты, from≤until при наличии обеих | Календарные условия; текущая дата сама по себе не исключает тариф из public price |
| `audience_type`, `age_from/to` | Default all; возраста неотрицательны, from≤to | Аудитория тарифа |
| `min_people/max_people` | Заданные значения >0; min≤max | Число участников |
| `day_type` | any/weekday/weekend/holiday | Условие, не фильтр активности по сегодняшнему дню |
| `title_az/ru/en`, `conditions_az/ru/en` | Заголовки до 160, условия TextField; необязательны; публичный fallback по языкам | Дополнительные переводы |
| `is_required`, `is_active` | Default False / True; required не превращает доплату в primary | Обязательность платежа и видимость |
| `source_url` | Необязательный URL | Принимается редактором/serializer; не источник автоматической проверки истинности |
| `sort_order` | Сервис replace переписывает индексом порядка массива | Порядок тарифов |
| `verified_at` | Staff-owned; owner normalize удаляет присланное значение; у сохранённой строки оно сохраняется | Не доступно владельцу; оговорка admin-пути в разделе «Обнаруженные противоречия кода» |
| `id`, `place`, `created_at`, `updated_at` | ID matching в пределах данного place; timestamps системные | Чужой ID не даёт изменить чужую строку; может не совпасть и привести к новой записи |

`normalize_pricing_plans` → `PricingPlan.full_clean` → transactional `replace_place_pricing_plans`; `PricingPlan.save` тоже вызывает full_clean. Существующие ID сопоставляются в пределах места, без ID возможен matching fingerprint. Отсутствующие в итоговом массиве строки удаляются; sort_order назначается заново. Поэтому «все ID всегда сохраняются» неверно при реальном удалении/замене.

## 9. Location

`region` — **виртуальное поле формы**. В БД одна строка `Place.district`: для Баку ключ `baku_*`, вне Баку — ключ региона (`ganja` и т. п.). `init_location_fields` выполняет обратное преобразование. District, metro и address не FK на географические модели.

Owner draft может оставить локацию пустой. Owner submit требует регион, адрес, координаты и район Баку. Admin form имеет собственный вызов clean_location_fields; quality-действия отдельно район/регион не требуют. Cross-region POST (например ganja + baku_yasamal) отвергается. Metro необязательно; UI скрывает и очищает его вне Баку, но это не универсальное правило модели.

Координаты: обе отсутствуют либо обе заданы; конечные числа; широта [-90,90], долгота [-180,180]. Строгая отправка требует точку. Центр карты по умолчанию не считается выбором. Google Maps / Leaflet позволяют выбрать/переместить точку; геолокация вызывается по нажатию; ручные поля остаются при ошибке карты. Изменение адреса показывает запрос проверки точки, но не заменяет уже заданные координаты автоматически. Явный refresh может заменить их; серверный geocoding использует Google repository и настройку ключа.

**Уже реализовано:** `district_geometry.district_for_coordinates` по локальному `data/baku_districts.geojson`; `validate_place_card` выдаёт warning `DISTRICT_COORDINATE_MISMATCH`, когда определён другой район Баку. Это не блокирующая ошибка строгой owner-формы и не автоматическая запись района. Координаты вне примерных границ Азербайджана — warning verification-проверки, не запрет модели.

**FUTURE / PLANNED (не реализовано в мастере):** автоматически выбирать/предлагать район при перемещении маркера. Наличие offline lookup не означает, что такая UI-функция уже работает.

## 10. Contacts и дополнительный текст

Phone1 обязателен только в строгой отправке; phone2/3 необязательны, при вводе проверяются как азербайджанские номера. `phone_numbers` выдаёт непустые уникальные номера в порядке 1→2→3. Website — URLField; Instagram хранит строку, helper строит URL из username/@name/ссылки. Нельзя обещать Instagram такую же валидацию, как URLField.

`extra_conditions_*`, `additional_info_*` на AZ/RU/EN доступны владельцу. Старые поля без суффикса тоже доступны в дополнительных настройках; они не удалены и не являются staff-only. `_localized_text` использует legacy fallback **только для RU**, если соответствующий RU перевод пуст.

## 11. Schedule

Default `schedule_mode=regular`; поле существует с миграции 0096. Owner при пропуске режима использует текущий/default; модельный blank=False не означает отдельную обязательную ручную операцию выбора.

| Режим | Что вводится | schedule_days / intervals | schedule_note_* | Owner submit / Admin readiness |
|---|---|---|---|---|
| `regular` | Недельный график либо текст schedule | Строгой форме нужен содержательный график, если нет текста. Для открытого дня интервалы либо is_24_hours | Необязательны | Да при наличии графика/текста. Quality принимает факт связанных дней, не проверяя содержательность каждого |
| `by_appointment` | Выбор режима «по записи» | Не требуются; существующие строки сохраняются и не синхронизируются при этом режиме | Необязательны | Да без фиктивных часов |
| `variable` | Выбор меняющегося графика | Не требуются; прежний недельный график сохраняется | Необязательны, несмотря на рекомендацию importer добавить пояснение | Да |
| `events` | Выбор «по мероприятиям» | Не требуются; прежние строки сохраняются | Необязательны | Да даже без будущих Event; цена Place всё равно нужна |
| `always_open` | **Нет такого choice** | Для круглосуточности: regular + is_24_hours у нужных дней | — | Не принимать как существующий режим |

Хранение: Place.schedule_mode и 3 текстовых note; PlaceScheduleDay(place,weekday,is_closed,is_24_hours,order); PlaceScheduleInterval(schedule_day,start_time,end_time,order). Уникальность place+weekday в БД. Неделя mon…sun. В JSON intervals имеют `start/end`, а не модельные `start_time/end_time`.

Нормализация: закрытый день очищает интервалы и 24h; 24h очищает интервалы. Открытый обычный день требует хотя бы один валидный интервал HH:MM; равные границы, переход через полночь и пересечения запрещаются; повторы интервалов устраняются. Неизвестные дни/лишние структуры могут отбрасываться, не всегда вызывают ошибку.

`save_schedule` синхронизирует только regular. `sync_place_schedule` удаляет прежние дни и создаёт новые при содержательном графике: **ID дней/интервалов не сохраняются**. Несодержательный график удаляет строки, но не legacy `schedule`. Публичные rows/summary/open_status используют режим; events может показывать ближайшие события. Старый текст schedule остаётся compatibility field.

## 12. Media

| Поле | Owner | Admin / public |
|---|---|---|
| `photo` | Загрузка/замена/очистка; обязательно для строгого submit | Главное; первым в каталоге, карте и галерее |
| `cover_photo` | В форму не входит; сохраняется при edit | Fallback при отсутствии пригодного главного фото; не отдельная обложка поверх главного |
| `PlacePhoto.image` | До 10 дополнительных файлов с учётом сохранённых и помеченных на удаление | Gallery inline; fallback после главного и cover |
| `PlacePhoto.caption/order` | Нет отдельных элементов редактирования; существующие сохраняются | Admin inline редактирует; order определяет порядок gallery |

Owner принимает JPG/PNG/WEBP до 2 MiB; HEIC/HEIF до 15 MiB с серверной конвертацией и проверкой изображения. Это ограничения owner helper, не DB constraint FileField и не универсальное описание любого импорта. Gallery limit задают owner form и admin inline; сама модель не ограничивает число строк десятью.

Quality/admin publication actions допускают photo **или** cover **или** gallery; строгий admin form может потребовать именно photo. `public_image_file`/`gallery_files` дополнительно проверяют наличие файлов в storage; quality проверяет ссылку/строку, а не реальное существование файла.

Изменение Place, тарифов и расписания в owner controller выполняется внутри `transaction.atomic`. При успешном edit удаление строки gallery выполняется в транзакции, физического файла — через `transaction.on_commit`. Старое главное фото при замене/очистке тоже удаляется после commit. Невалидная форма не применяет помеченные удаления; ошибки загрузки вызывают rollback и попытку cleanup. Файловое хранилище само по себе не транзакционно: не обещать абсолютное отсутствие orphan-файлов при любых сбоях процесса.

Существуют отдельные действия удаления gallery; они не равнозначны отложенной отметке в wizard. Полная карточка удаляется мягко с deleted_*; её строки и медиа не описываются как немедленно уничтоженные.

## 13. Owner / moderation fields и побочные эффекты

`moderation_note` — виртуальное поле только создания, максимум 500; попадает в `PlaceOwnershipRequest.note`, не в Place. `PlaceChangeAudit` сохраняет изменения и источник owner_panel/admin/system. Schedule/pricing audit сериализует содержимое отдельно.

**Одобрение заявки не равно явной публикации Place:** `PlaceOwnershipRequest.apply_moderation` при APPROVED назначает owner и is_active=True, но не устанавливает Place.status=published и published_at и не вызывает quality-check. Поэтому новая pending-карточка после одного лишь одобрения заявки может оставаться невидимой. При REJECTED меняются поля самой заявки, а не автоматически Place.status/rejection_reason. Отдельное действие публикации Place имеет собственный контракт. `set_publication_state` в аккаунте требует служебное право, ранее одобренную заявку и quality readiness.

Права пользователя не позволяют передать owner/status/verification через произвольный POST. Но действия контроллера **меняют** служебные поля: назначают владельца при создании, снимают публикацию при draft-edit, ставят pending при отправке, очищают rejection_reason, заполняют deleted_* при удалении. Поэтому прежняя общая фраза «все административные поля всегда сохраняются при owner edit» неточна.

## 14. Admin-only / system fields

| Поле/группа | Кто меняет; owner POST | Что происходит при owner edit | Публичное использование |
|---|---|---|---|
| `status`, `is_active` | Admin actions/контроллер; не owner fields | Меняются по workflow, не по присланным значениям | Главный статусный допуск |
| `is_verified`, `last_verified_at` | Admin verification; не owner fields | Напрямую сохраняются, owner не устанавливает | Значок проверки / сведения о проверке |
| `owner` | Система создания/передачи/одобрения; admin | Произвольный POST игнорируется; текущий owner не заменяется обычным edit | Права управления, не описание места |
| `created_by` | Создание системой/admin | Сохраняется как аудит; не постоянное право после передачи owner | История/права fallback при owner=NULL |
| `is_home_recommended`, `home_recommended_order` | Admin; не owner fields | Обычный owner edit напрямую не меняет | Отбор/порядок главной |
| `rejection_reason` | Модерация/контроллер | При отправке очищается; не свободный owner ввод | Причина в аккаунте |
| `published_at` | Система публикации; readonly display | На создании NULL; в обычном edit явно не перезаписывается | Метаданные, admin |
| `deleted_at`, `deleted_by` | Действия soft-delete/restore; readonly в admin | Обычный edit не назначает; разрешённое удаление назначает | Исключение из публичных выборок |
| `rating_avg`, `rating_count`, `likes_count` | Системная статистика; readonly в PlaceAdmin | Не принимаются owner form | Публичные рейтинг/реакции |
| `custom_price_badge_az/ru/en` | Admin редактор/JSON import; не owner fields | Сохраняются | Приоритетная ручная надпись; readiness и SEO Offer не заменяет |
| `is_temporary`, `temporary_start/end` | Есть в общей OwnerPlaceForm, **но permanent views принудительно ставят пустые значения до валидации** | Не считать безопасностью только исключение из Meta.fields: здесь защита находится в view | Legacy временные Place; Event имеет отдельный поток |
| `slug` | Генерация при пустом значении; PlaceAdmin readonly | Owner не редактирует, существующий сохраняется | URL, SEO |
| `created_at`, `updated_at` | Система; auto_now_add/auto_now | created сохраняется, updated меняется | Метаданные/порядок |
| `PricingPlan.verified_at` | Staff/service; owner удалён из normalized payload | Сохраняется у сопоставленной существующей строки; при удалении строки исчезает вместе с ней | Serializer может отдавать, owner UI не редактирует |

## 15. Legacy / Compatibility

Статусы ниже — оценка роли в **текущем коде**, не объявление о принятом удалении. Ничего не удалено.

| Поле / интерфейс | STATUS | CAN REMOVE NOW? | Почему |
|---|---|---|---|
| `pricing_plans_legacy` (DB column `pricing_plans`) | compatibility | no | Getter возвращает JSON при отсутствии relational rows; миграционная команда читает его |
| `price_from`, `price_to` | compatibility | no | Производная AZN-сводка плюс fallback старых карточек, quality/SQL и verification |
| `price_per_lesson`, `price_per_month`, `price_per_8_lessons` | compatibility | no | Derived sync, старые карточки, importer и публичные compatibility helpers |
| `schedule` | compatibility | no | Строгая форма и public принимают текст без структурированных дней |
| `extra_conditions`, `additional_info` | compatibility | no | Owner редактирует, RU public fallback, JSON importer |
| `cover_photo` | compatibility | no | Рабочий fallback и допуск фото в quality; сначала нужен аудит данных и перенос |
| `name` | active | no | Обязательное хранилище fallback, slug/представление/импорт |
| Place `lesson_*`, `lessons_per_*` | active | no | Общие свойства места остаются в форме и public, не объявлены deprecated |
| Place `is_temporary`, `temporary_start/end` | compatibility | needs data audit | Существуют отдельные Event, но legacy Place ещё участвуют в фильтрах срока/фичи |
| JSON `payment_type`, `package_sessions`, старые name/frequency | compatibility | no | Нормализатор преобразует прежние payload в канонические тарифы |

Наличие новой структуры само по себе не доказывает возможность удаления столбцов. В этом аудите нет data-migration и нет утверждения, что legacy-данных уже не осталось.

## 16. Related / virtual fields и JSON import/export

| Поле/структура | Транспорт / назначение |
|---|---|
| `region` | Виртуальный выбор, преобразуется в district |
| `pricing_plans` | Python property Place и JSON field формы; не путать с legacy DB column; pending → relational save |
| `structured_schedule` | Скрытый JSON, динамически добавляется mixin; days/intervals пересоздаются |
| `gallery_images`, `delete_gallery_ids` | Новые файлы и проверенные ID фотографий данного места |
| `moderation_note` | Только create → запрос модерации |
| `form_action` | save_draft/save_draft_exit/save_and_publish/check_coordinates/refresh_coordinates в соответствующих views; не модельное поле |
| `draft_client_key`, CSRF | Восстановление/защита формы, не поля Place |
| `editor_kind`, `payment_type`, `package_sessions` | Представление редактора/compatibility, не отдельные model fields |
| `editor_review` импортируемого JSON | Заметки редактору на клиенте; не публикационные данные Place |

**Admin JSON importer:** `static/admin/js/kidsmap_place_json_import.js` заполняет элементы формы, нормализует aliases; серверный `validate_pricing_import_view` проверяет pricing_plans/tariffs до сохранения. Старые 1 урок/месяц/8 уроков могут стать тарифами, но price_from/to не создают тариф из-за неизвестного продукта. Фактическое сохранение проходит admin form, а не отдельную свободную API-запись Place. Импорт не загружает картинки по произвольным URL автоматически.

**Export:** `PlaceAdmin.export_place_json_view` экспортирует имена/описания, category/subcategory, age_from/to, address/district/metro, phone1/Instagram/website, schedule_mode/notes, custom badges и serialized relational pricing_plans. Это **не полный backup**: нет lat/lng, age_open_ended, phone2/3, schedule_days/legacy schedule, фото, взрослых, большинства дополнительных текстов и служебных данных. Legacy JSON без relational rows не экспортируется как тарифы. Export→import не гарантирует полный round-trip. Отдельно `management/commands/import_places.py` — **CSV**, не JSON: пишет старые scalar prices через update_or_create, без полного workflow формы.

## 17. Permissions

- `ensure_owner_permission` проверяет аутентификацию, не роль UserProfile. Доступ ограничивается конкретным местом.
- Прямой owner имеет права manager; created_by даёт fallback только при owner=NULL. После передачи владельца автор не сохраняет права только на основании авторства.
- Активная place-scoped membership: MANAGER — просмотр/редактирование/статистика/отзывы/команда; EDITOR — просмотр/редактирование; MODERATOR — просмотр/статистика/отзывы. Overrides определяются membership. Старые owner-wide записи без place не предоставляют глобального доступа.
- `place.publish` не входит в обычные owner/manager права. Staff publication требует `catalog.change_place`, superuser разрешён.
- Создание ограничено 10 текущими непосредственно управляемыми неудалёнными местами. Чужой place недоступен через managed repository; удалённый не редактируется. Подмена ID gallery ограничена choices данного place, тарифные записи выбираются по этому place.
- Постоянные и временные события расходятся в `views.py`: permanent POST принудительно очищает temporary flags; временные мероприятия/специалисты используют свои формы.

## 18. Public usage / visibility / SEO

`public_place_queryset`: active + published + not deleted, категория/адрес, schedule_mode≠regular либо текст/наличие schedule_days, контакт phone1/Instagram/website, хотя бы одна возрастная граница, scalar price либо relational active primary price (on_request включён), описание ≥120, отсутствие тестовых токенов. Legacy temporary дополнительно фильтруются по feature flag и сроку. **В SQL нет обязательности name_az, description_az, subcategory, district, координат и фото.**

`published_place_queryset` и `Place.is_public` проверяют только состояние. `is_map_ready` дополнительно требует обе координаты; это не весь catalog-quality gate. Публичные repository используют `public_place_queryset`, карточка — public_image, age_display, price summary; detailed тарифы сохраняют условия/валюту/частоты.

SEO `build_place_seo_payload`: имя/описание выбранного языка, public image, адрес, phone1, geo, рейтинг, ссылки. Offer создаётся из active primary **exact/free/range**, со своей валютой. `from` и `on_request` пропускаются. Ручная надпись не выдаётся за числовую Offer, отсутствующий price_mode не интерпретируется. Каталог, sitemap и landing visibility следует проверять по их собственным queryset, а не только статусу.

## 19. Миграции и верификация

Существенные миграции: 0001 базовый Place; 0002 переводы; 0004/0005 фото; 0032 общие дополнительные поля; 0034 soft-delete; 0040 статусы; 0050 иерархические ключи районов; 0051 структурированное расписание; 0062 старые тарифы/параметры занятий; 0067 взрослые; 0068 дополнительные телефоны; 0069 переводы дополнительных полей; 0076 рекомендации; 0077 открытый возраст; 0078 created_by; 0084 relational PricingPlan/переименование legacy поля; 0085 pricing constraints; 0091 custom badges; 0092/0093 place-scoped access; 0096 **четыре** schedule modes; 0097 удаление прежних профильных ролей.

Автоблок сравнивает ORM с конечным состоянием миграций **на диске**. Это не проверка применённости миграций production.

Результат текущей проверки: **131 поле** (Place 73, PricingPlan 42, PlaceScheduleDay 6, PlaceScheduleInterval 5, PlacePhoto 5), параметры и enums совпадают с migration state. `scripts/place_wizard_matrix.py --check` — PASS; `manage.py makemigrations --check --dry-run` — No changes detected. Повторная генерация детерминирована и не меняет ручные разделы.

**38 целевых Django-тестов прошли:** все 16 из `catalog.testcases.permanent_place_wizard`, все 16 из `catalog.testcases.pricing_plans_relational` и 6 методов `PlaceCardValidationTests`: `test_requires_photo_coordinates_and_contact`, `test_rejects_reversed_age_and_invalid_coordinates`, `test_compares_card_price_with_active_primary_tariff`, `test_paid_addon_does_not_make_free_primary_price_invalid`, `test_rejects_invalid_structured_schedule`, `test_offline_baku_polygon_lookup_detects_district_mismatch`. Запуск через `.tmp/run_place_tests.py` (обёртка Django runner, отдельная тестовая БД, ускоренный password hasher); лог `.tmp/place-matrix-tests.log`. Полный regression и изменения рабочей базы не выполнялись. Тесты подтверждают конкретные перечисленные сценарии, не доказывают отсутствие всех найденных противоречий.

## Обнаруженные противоречия кода

Это findings текущей реализации; код в рамках синхронизации документа **не исправлялся**.

| Проблема | Файлы и текущее поведение | Рекомендуемое решение для отдельной задачи |
|---|---|---|
| Разные пути одной публикации | permanent_place_rules + forms/admin versus controller submit / admin actions + content_quality: различаются phone1, photo, age, AZ description, район | Явно закрепить intended уровни и решить, должен ли отдельный submit использовать строгую owner readiness |
| Catalog/quality не идентичны | content_quality SQL не требует имя/координаты/фото; Python quality требует. Text trim и наличие дней тоже различаются | Согласовать или назвать отдельные гарантии каждого допуска; не обещать полную эквивалентность |
| Битый schedule payload не всегда отвергается | parse_schedule_payload возвращает defaults при ошибке JSON; mixin игнорирует errors для non-regular | Уточнить контракт отказа от повреждённых данных; сохранить compatibility осознанно |
| Надпись on_request не доказывает структурированный тариф | build_public_price_summary возвращает похожую плашку при source=none/foreign | Различать отсутствие данных и подтверждённую стоимость по запросу в отображении/структурированных данных |
| Подкатегория: неравная серверная проверка | Owner clean проверяет принадлежность, Place.clean — нет; admin UI фильтрует, но это не server guarantee | Добавить серверную проверку в согласованном общем слое отдельным изменением |
| Admin verified_at может теряться по пути Place.save | Admin normalizes allow_verified=True, но Place.save вызывает replace без allow_verified; тот снова удаляет verified_at из входа | Явно передать staff-контекст в контролируемый save path; owner защиту сохранить |
| Экспорт неполный | export_place_json_view пропускает перечисленные в разделе 16 поля; importer шире export | Назвать формат частичным либо добавить версионированный полный export/round-trip тест |
| Scalar-only admin edit | Owner избегает pending=[] при пустых relational rows, admin безусловно задаёт pricing_plans=[]; save может обнулить scalar legacy | Отдельно проверить сохранение старых админ-карточек и принять migration policy |
| Минимальная цена в verification не разделяет валюты | validate_place_card собирает числовые primary всех валют, sync_legacy — только AZN | Привести проверку к валютному контракту summary/sync |
| Показ диапазона с нулевой нижней границей | PricingPlan допускает range 0–N; build_public_price_summary считает paid только low>0 и может показать «уточняется» | Добавить отдельный кейс numeric range с нулевой нижней границей |
| Формулировка quality name | missing_name label говорит «на азербайджанском», проверка принимает fallback | Согласовать подпись с фактическим условием |
| Одобрение заявки не завершает публикацию нового Place | models/owner.py: apply_moderation включает is_active, но не меняет pending на published и не ставит published_at; комментарий обещает немедленную публикацию | Разделить владение/публикацию либо явно провести согласованную readiness и переход статуса |
| Admin add/edit показывают разные дополнительные тексты | ADD_FIELDSETS содержит переводы extra_conditions_*/additional_info_*, edit fieldsets — общие legacy поля; наличие в PlaceAdminForm не гарантирует видимость | Согласовать наборы редакторов, сохранив legacy fallback и существующие переводы |

Ожидаемые price_mode/always_open/отмена порога120 из запроса не обнаружены в этом дереве. Это **расхождение ожидаемой версии с кодом**, а не повод придумывать поля или менять бизнес-логику в документационной задаче.

## 21. Генератор и правила использования AI-агентами

Старый `scripts/place_wizard_matrix.py` разбирал AST полей, но вручную приписывал каждой группе обязательность, видимость и сохранность. Он мог перезаписать документ устаревшими бизнес-правилами и не раскрывал фактические значения ссылочных enums.

Теперь скрипт получает полные local_fields из Django ORM, раскрывает enum-коды, defaults/FK/constraints, сверяет параметры с migration state и обновляет **только** блок между маркерами. Ручная архитектурная часть не генерируется и не переписывается. Нет классификации любого `price*` как legacy по префиксу. `--check` ничего не записывает и сигнализирует рассинхронизацию; повреждённые/отсутствующие маркеры приводят к отказу, а не потере документа.

```powershell
.venv/Scripts/python.exe scripts/place_wizard_matrix.py
.venv/Scripts/python.exe scripts/place_wizard_matrix.py --check
```

Документ пригоден как knowledge source **для этого среза** с обязательным учётом пути workflow и findings. Автоматическая актуальность полей не подтверждает актуальность ручных правил. При новой миграции/изменении validator/controller заново открыть указанные ниже источники и пересмотреть соответствующие правила.

<!-- BEGIN AUTO-GENERATED MODEL FACTS -->

## AUTO-GENERATED FACTS: полная структура моделей

Источник: Django `_meta.local_fields`, `base_fields` форм и конечное состояние миграций на диске. Это не требования публикации. `blank=False` не равнозначно обязательности в черновике. «Owner / Admin form» означает наличие в базовом классе формы, а не видимость в шаблоне, доступность по правам или принятие HTTP POST после обработки view. «Admin add/edit» — присутствие в штатных fieldsets (дополнительные редакторы/шаблоны описаны вручную). Автоматический `id` включён.

Листья графа миграций catalog: `0100_place_price_mode`.

### Place — 74 полей

| Поле | Тип | ORM facts / точные значения choices | Owner / Admin form | Admin add/edit |
|---|---|---|---|---|
| `id` | BigAutoField | blank=True; null=False; default=—; primary_key=True; unique=True | нет / нет | нет / нет |
| `name` | CharField | blank=False; null=False; default=—; max_length=255 | нет / да | нет / нет |
| `slug` | SlugField | blank=True; null=False; default=''; max_length=255; unique=True | нет / да | нет / нет |
| `name_ru` | CharField | blank=True; null=False; default=''; max_length=255 | да / да | да / да |
| `name_en` | CharField | blank=True; null=False; default=''; max_length=255 | да / да | да / да |
| `name_az` | CharField | blank=True; null=False; default=''; max_length=255 | да / да | да / да |
| `description_ru` | TextField | blank=True; null=False; default='' | да / да | да / да |
| `description_en` | TextField | blank=True; null=False; default='' | да / да | да / да |
| `description_az` | TextField | blank=True; null=False; default='' | да / да | да / да |
| `category` | ForeignKey | blank=False; null=False; default=—; db_column=category; to=catalog.Category; target=code; on_delete=PROTECT; related_name=None | да / да | да / да |
| `subcategory` | ForeignKey | blank=True; null=True; default=—; to=catalog.Subcategory; target=id; on_delete=SET_NULL; related_name=None | да / да | да / да |
| `age_from` | PositiveSmallIntegerField | blank=True; null=True; default=— | да / да | да / да |
| `age_to` | PositiveSmallIntegerField | blank=True; null=True; default=— | да / да | да / да |
| `age_open_ended` | BooleanField | blank=False; null=False; default=False | да / да | да / да |
| `offers_adult_classes` | BooleanField | blank=False; null=False; default=False | да / да | да / да |
| `district` | CharField | blank=True; null=False; default=—; max_length=100 | да / да | да / да |
| `metro` | CharField | blank=True; null=False; default=—; max_length=100 | да / да | да / да |
| `address` | CharField | blank=True; null=False; default=—; max_length=255 | да / да | да / да |
| `phone1` | CharField | blank=True; null=False; default=—; max_length=50 | да / да | да / да |
| `phone2` | CharField | blank=True; null=False; default=''; max_length=50 | да / да | да / да |
| `phone3` | CharField | blank=True; null=False; default=''; max_length=50 | да / да | да / да |
| `owner` | ForeignKey | blank=True; null=True; default=—; to=auth.User; target=id; on_delete=SET_NULL; related_name=managed_places | нет / да | да / да |
| `created_by` | ForeignKey | blank=True; null=True; default=—; to=auth.User; target=id; on_delete=SET_NULL; related_name=created_places | нет / да | нет / нет |
| `cover_photo` | FileField | blank=True; null=True; default=—; max_length=100 | нет / да | да / да |
| `photo` | FileField | blank=True; null=True; default=—; max_length=100 | да / да | да / да |
| `instagram` | CharField | blank=True; null=False; default=—; max_length=255 | да / да | да / да |
| `website` | CharField | blank=True; null=False; default=—; max_length=200 | да / да | да / да |
| `schedule` | TextField | blank=True; null=False; default=— | да / да | да / да |
| `schedule_mode` | CharField | blank=False; null=False; default='regular'; max_length=20; choices='regular', 'always_open', 'by_appointment', 'variable', 'events' | да / да | да / да |
| `schedule_note_az` | TextField | blank=True; null=False; default='' | да / да | да / да |
| `schedule_note_ru` | TextField | blank=True; null=False; default='' | да / да | да / да |
| `schedule_note_en` | TextField | blank=True; null=False; default='' | да / да | да / да |
| `lesson_duration_minutes` | PositiveSmallIntegerField | blank=True; null=True; default=— | да / да | да / да |
| `lesson_format` | CharField | blank=True; null=False; default=''; max_length=16; choices='group', 'individual' | да / да | нет / нет |
| `lessons_per_week` | PositiveSmallIntegerField | blank=True; null=True; default=— | да / да | нет / нет |
| `lessons_per_month` | PositiveSmallIntegerField | blank=True; null=True; default=— | да / да | нет / нет |
| `pricing_plans_legacy` | JSONField | blank=True; null=False; default=builtins.list(); db_column=pricing_plans | нет / нет | нет / нет |
| `is_temporary` | BooleanField | blank=False; null=False; default=False | да / да | нет / нет |
| `temporary_start` | DateTimeField | blank=True; null=True; default=— | да / да | нет / нет |
| `temporary_end` | DateTimeField | blank=True; null=True; default=— | да / да | нет / нет |
| `lat` | FloatField | blank=True; null=True; default=— | да / да | да / да |
| `lng` | FloatField | blank=True; null=True; default=— | да / да | да / да |
| `price_mode` | CharField | blank=False; null=False; default='tariffs'; max_length=32; choices='tariffs', 'free', 'free_entry_paid_services', 'events' | нет / да | да / да |
| `price_from` | DecimalField | blank=True; null=True; default=—; max_digits=10; decimal_places=2 | нет / нет | нет / нет |
| `price_to` | DecimalField | blank=True; null=True; default=—; max_digits=10; decimal_places=2 | нет / нет | нет / нет |
| `price_per_lesson` | DecimalField | blank=True; null=True; default=—; max_digits=10; decimal_places=2 | нет / нет | нет / нет |
| `price_per_month` | DecimalField | blank=True; null=True; default=—; max_digits=10; decimal_places=2 | нет / нет | нет / нет |
| `price_per_8_lessons` | DecimalField | blank=True; null=True; default=—; max_digits=10; decimal_places=2 | нет / нет | нет / нет |
| `extra_conditions` | TextField | blank=True; null=False; default=— | да / да | нет / нет |
| `additional_info` | TextField | blank=True; null=False; default=— | да / да | нет / нет |
| `extra_conditions_az` | TextField | blank=True; null=False; default='' | да / да | да / да |
| `extra_conditions_ru` | TextField | blank=True; null=False; default='' | да / да | да / да |
| `extra_conditions_en` | TextField | blank=True; null=False; default='' | да / да | да / да |
| `additional_info_az` | TextField | blank=True; null=False; default='' | да / да | да / да |
| `additional_info_ru` | TextField | blank=True; null=False; default='' | да / да | да / да |
| `additional_info_en` | TextField | blank=True; null=False; default='' | да / да | да / да |
| `custom_price_badge_az` | CharField | blank=True; null=False; default=''; max_length=120 | нет / да | нет / нет |
| `custom_price_badge_ru` | CharField | blank=True; null=False; default=''; max_length=120 | нет / да | нет / нет |
| `custom_price_badge_en` | CharField | blank=True; null=False; default=''; max_length=120 | нет / да | нет / нет |
| `likes_count` | PositiveIntegerField | blank=False; null=False; default=0 | нет / да | нет / нет |
| `rating_avg` | FloatField | blank=False; null=False; default=0 | нет / да | нет / нет |
| `rating_count` | PositiveIntegerField | blank=False; null=False; default=0 | нет / да | нет / нет |
| `is_home_recommended` | BooleanField | blank=False; null=False; default=False | нет / да | да / да |
| `home_recommended_order` | PositiveSmallIntegerField | blank=False; null=False; default=0 | нет / да | да / да |
| `is_active` | BooleanField | blank=False; null=False; default=True | нет / да | да / да |
| `is_verified` | BooleanField | blank=False; null=False; default=False | нет / да | да / да |
| `status` | CharField | blank=False; null=False; default='published'; max_length=16; choices='draft', 'pending', 'published', 'rejected' | нет / да | да / да |
| `rejection_reason` | TextField | blank=True; null=False; default='' | нет / да | да / да |
| `last_verified_at` | DateTimeField | blank=True; null=True; default=— | нет / да | нет / нет |
| `published_at` | DateTimeField | blank=True; null=True; default=— | нет / да | нет / нет |
| `deleted_at` | DateTimeField | blank=True; null=True; default=— | нет / да | нет / да |
| `deleted_by` | ForeignKey | blank=True; null=True; default=—; to=auth.User; target=id; on_delete=SET_NULL; related_name=deleted_places | нет / да | нет / да |
| `created_at` | DateTimeField | blank=True; null=False; default=—; auto_now_add=True | нет / нет | да / да |
| `updated_at` | DateTimeField | blank=True; null=False; default=—; auto_now=True | нет / нет | да / да |

Model ordering: `('-created_at',)`.


### PricingPlan — 42 полей

| Поле | Тип | ORM facts / точные значения choices | Owner / Admin form | Admin add/edit |
|---|---|---|---|---|
| `id` | BigAutoField | blank=True; null=False; default=—; primary_key=True; unique=True | — (связанная модель) | связанный редактор |
| `place` | ForeignKey | blank=False; null=False; default=—; to=catalog.Place; target=id; on_delete=CASCADE; related_name=pricing_plan_records | — (связанная модель) | связанный редактор |
| `product_type` | CharField | blank=False; null=False; default=—; max_length=32; choices='admission', 'visit', 'lesson', 'membership', 'course', 'camp', 'event', 'excursion', 'tour', 'rental', 'addon', 'registration_fee', 'deposit' | — (связанная модель) | связанный редактор |
| `lesson_format` | CharField | blank=True; null=False; default=—; max_length=16; choices='open_visit', 'group', 'individual' | — (связанная модель) | связанный редактор |
| `charge_role` | CharField | blank=False; null=False; default='primary'; max_length=24; choices='primary', 'addon', 'registration_fee', 'deposit' | — (связанная модель) | связанный редактор |
| `billing_mode` | CharField | blank=False; null=False; default='one_time'; max_length=16; choices='one_time', 'recurring', 'installment' | — (связанная модель) | связанный редактор |
| `billing_interval` | CharField | blank=True; null=False; default=—; max_length=8; choices='day', 'week', 'month', 'year' | — (связанная модель) | связанный редактор |
| `billing_interval_count` | PositiveSmallIntegerField | blank=True; null=True; default=— | — (связанная модель) | связанный редактор |
| `billing_cycles` | PositiveSmallIntegerField | blank=True; null=True; default=— | — (связанная модель) | связанный редактор |
| `price_kind` | CharField | blank=False; null=False; default='exact'; max_length=16; choices='exact', 'free', 'from', 'range', 'on_request' | — (связанная модель) | связанный редактор |
| `price` | DecimalField | blank=True; null=True; default=—; max_digits=10; decimal_places=2 | — (связанная модель) | связанный редактор |
| `price_min` | DecimalField | blank=True; null=True; default=—; max_digits=10; decimal_places=2 | — (связанная модель) | связанный редактор |
| `price_max` | DecimalField | blank=True; null=True; default=—; max_digits=10; decimal_places=2 | — (связанная модель) | связанный редактор |
| `currency` | CharField | blank=False; null=False; default='AZN'; max_length=3 | — (связанная модель) | связанный редактор |
| `quantity` | PositiveSmallIntegerField | blank=True; null=True; default=— | — (связанная модель) | связанный редактор |
| `quantity_unit` | CharField | blank=True; null=False; default=—; max_length=16; choices='entry', 'visit', 'lesson', 'minute', 'hour', 'day', 'week', 'month', 'course', 'event', 'camp_shift', 'person', 'family', 'group' | — (связанная модель) | связанный редактор |
| `sessions_per_week` | PositiveSmallIntegerField | blank=True; null=True; default=— | — (связанная модель) | связанный редактор |
| `sessions_per_month` | PositiveSmallIntegerField | blank=True; null=True; default=— | — (связанная модель) | связанный редактор |
| `is_unlimited` | BooleanField | blank=False; null=False; default=False | — (связанная модель) | связанный редактор |
| `validity_interval` | CharField | blank=True; null=False; default=—; max_length=8; choices='day', 'week', 'month', 'year' | — (связанная модель) | связанный редактор |
| `validity_interval_count` | PositiveSmallIntegerField | blank=True; null=True; default=— | — (связанная модель) | связанный редактор |
| `valid_from` | DateField | blank=True; null=True; default=— | — (связанная модель) | связанный редактор |
| `valid_until` | DateField | blank=True; null=True; default=— | — (связанная модель) | связанный редактор |
| `audience_type` | CharField | blank=False; null=False; default='all'; max_length=12; choices='all', 'child', 'adult', 'family', 'group' | — (связанная модель) | связанный редактор |
| `age_from` | PositiveSmallIntegerField | blank=True; null=True; default=— | — (связанная модель) | связанный редактор |
| `age_to` | PositiveSmallIntegerField | blank=True; null=True; default=— | — (связанная модель) | связанный редактор |
| `min_people` | PositiveSmallIntegerField | blank=True; null=True; default=— | — (связанная модель) | связанный редактор |
| `max_people` | PositiveSmallIntegerField | blank=True; null=True; default=— | — (связанная модель) | связанный редактор |
| `day_type` | CharField | blank=False; null=False; default='any'; max_length=12; choices='any', 'weekday', 'weekend', 'holiday' | — (связанная модель) | связанный редактор |
| `title_az` | CharField | blank=True; null=False; default=—; max_length=160 | — (связанная модель) | связанный редактор |
| `title_ru` | CharField | blank=True; null=False; default=—; max_length=160 | — (связанная модель) | связанный редактор |
| `title_en` | CharField | blank=True; null=False; default=—; max_length=160 | — (связанная модель) | связанный редактор |
| `conditions_az` | TextField | blank=True; null=False; default=— | — (связанная модель) | связанный редактор |
| `conditions_ru` | TextField | blank=True; null=False; default=— | — (связанная модель) | связанный редактор |
| `conditions_en` | TextField | blank=True; null=False; default=— | — (связанная модель) | связанный редактор |
| `is_required` | BooleanField | blank=False; null=False; default=False | — (связанная модель) | связанный редактор |
| `is_active` | BooleanField | blank=False; null=False; default=True | — (связанная модель) | связанный редактор |
| `sort_order` | PositiveSmallIntegerField | blank=False; null=False; default=0 | — (связанная модель) | связанный редактор |
| `verified_at` | DateTimeField | blank=True; null=True; default=— | — (связанная модель) | связанный редактор |
| `source_url` | CharField | blank=True; null=False; default=—; max_length=200 | — (связанная модель) | связанный редактор |
| `created_at` | DateTimeField | blank=True; null=False; default=—; auto_now_add=True | — (связанная модель) | связанный редактор |
| `updated_at` | DateTimeField | blank=True; null=False; default=—; auto_now=True | — (связанная модель) | связанный редактор |

Model ordering: `('sort_order', 'id')`.

- DB constraint `pricing_price_nonnegative`: `<CheckConstraint: condition=(OR: ('price__gte', 0), ('price__isnull', True)) name='pricing_price_nonnegative'>`.
- DB constraint `pricing_min_nonnegative`: `<CheckConstraint: condition=(OR: ('price_min__gte', 0), ('price_min__isnull', True)) name='pricing_min_nonnegative'>`.
- DB constraint `pricing_max_nonnegative`: `<CheckConstraint: condition=(OR: ('price_max__gte', 0), ('price_max__isnull', True)) name='pricing_max_nonnegative'>`.
- DB constraint `pricing_range_order`: `<CheckConstraint: condition=(OR: ('price_min__lte', F(price_max)), ('price_min__isnull', True), ('price_max__isnull', True)) name='pricing_range_order'>`.
- DB constraint `pricing_kind_values`: `<CheckConstraint: condition=(OR: (AND: ('price__gt', 0), ('price_kind', 'exact'), ('price_max__isnull', True), ('price_min__isnull', True)), (AND: ('price', 0), ('price_kind', 'free'), ('price_max__isnull', True), ('price_min__isnull', True)), (AND: ('price__isnull', True), ('price_kind', 'from'), ('price_max__isnull', True), ('price_min__gt', 0)), (AND: ('price__isnull', True), ('price_kind', 'range'), ('price_max__isnull', False), ('price_min__isnull', False)), (AND: ('price__isnull', True), ('price_kind', 'on_request'), ('price_max__isnull', True), ('price_min__isnull', True))) name='pricing_kind_values'>`.
- DB constraint `pricing_billing_values`: `<CheckConstraint: condition=(OR: (AND: ('billing_cycles__isnull', True), ('billing_interval', ''), ('billing_interval_count__isnull', True), ('billing_mode', 'one_time')), (AND: ('billing_cycles__isnull', True), ('billing_interval__in', ('day', 'week', 'month', 'year')), ('billing_interval_count__gt', 0), ('billing_mode', 'recurring')), (AND: ('billing_cycles__gt', 0), ('billing_interval', ''), ('billing_interval_count__isnull', True), ('billing_mode', 'installment'))) name='pricing_billing_values'>`.
- DB constraint `pricing_quantity_pair`: `<CheckConstraint: condition=(OR: (AND: ('quantity__isnull', True), ('quantity_unit', '')), (AND: ('quantity__gt', 0), (NOT (AND: ('quantity_unit', ''))))) name='pricing_quantity_pair'>`.
- DB constraint `pricing_validity_pair`: `<CheckConstraint: condition=(OR: (AND: ('validity_interval', ''), ('validity_interval_count__isnull', True)), (AND: ('validity_interval_count__gt', 0), (NOT (AND: ('validity_interval', ''))))) name='pricing_validity_pair'>`.
- DB constraint `pricing_age_order`: `<CheckConstraint: condition=(OR: ('age_from__isnull', True), ('age_to__isnull', True), ('age_from__lte', F(age_to))) name='pricing_age_order'>`.
- DB constraint `pricing_people_order`: `<CheckConstraint: condition=(OR: ('min_people__isnull', True), ('max_people__isnull', True), ('min_people__lte', F(max_people))) name='pricing_people_order'>`.
- DB constraint `pricing_date_order`: `<CheckConstraint: condition=(OR: ('valid_from__isnull', True), ('valid_until__isnull', True), ('valid_from__lte', F(valid_until))) name='pricing_date_order'>`.
- DB constraint `pricing_charge_role`: `<CheckConstraint: condition=(OR: (AND: ('charge_role', 'addon'), ('product_type', 'addon')), (AND: ('charge_role', 'registration_fee'), ('product_type', 'registration_fee')), (AND: ('charge_role', 'deposit'), ('product_type', 'deposit')), (AND: ('charge_role', 'primary'), (NOT (AND: ('product_type__in', ('addon', 'registration_fee', 'deposit')))))) name='pricing_charge_role'>`.

### PlaceScheduleDay — 6 полей

| Поле | Тип | ORM facts / точные значения choices | Owner / Admin form | Admin add/edit |
|---|---|---|---|---|
| `id` | BigAutoField | blank=True; null=False; default=—; primary_key=True; unique=True | — (связанная модель) | связанный редактор |
| `place` | ForeignKey | blank=False; null=False; default=—; to=catalog.Place; target=id; on_delete=CASCADE; related_name=schedule_days | — (связанная модель) | связанный редактор |
| `weekday` | CharField | blank=False; null=False; default=—; max_length=3; choices='mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun' | — (связанная модель) | связанный редактор |
| `is_closed` | BooleanField | blank=False; null=False; default=True | — (связанная модель) | связанный редактор |
| `is_24_hours` | BooleanField | blank=False; null=False; default=False | — (связанная модель) | связанный редактор |
| `order` | PositiveSmallIntegerField | blank=False; null=False; default=0 | — (связанная модель) | связанный редактор |

Model ordering: `('order', 'id')`.

- DB constraint `unique_place_schedule_weekday`: `<UniqueConstraint: fields=('place', 'weekday') name='unique_place_schedule_weekday'>`.

### PlaceScheduleInterval — 5 полей

| Поле | Тип | ORM facts / точные значения choices | Owner / Admin form | Admin add/edit |
|---|---|---|---|---|
| `id` | BigAutoField | blank=True; null=False; default=—; primary_key=True; unique=True | — (связанная модель) | связанный редактор |
| `schedule_day` | ForeignKey | blank=False; null=False; default=—; to=catalog.PlaceScheduleDay; target=id; on_delete=CASCADE; related_name=intervals | — (связанная модель) | связанный редактор |
| `start_time` | TimeField | blank=False; null=False; default=— | — (связанная модель) | связанный редактор |
| `end_time` | TimeField | blank=False; null=False; default=— | — (связанная модель) | связанный редактор |
| `order` | PositiveSmallIntegerField | blank=False; null=False; default=0 | — (связанная модель) | связанный редактор |

Model ordering: `('order', 'id')`.


### PlacePhoto — 5 полей

| Поле | Тип | ORM facts / точные значения choices | Owner / Admin form | Admin add/edit |
|---|---|---|---|---|
| `id` | BigAutoField | blank=True; null=False; default=—; primary_key=True; unique=True | — (связанная модель) | связанный редактор |
| `place` | ForeignKey | blank=False; null=False; default=—; to=catalog.Place; target=id; on_delete=CASCADE; related_name=gallery | — (связанная модель) | связанный редактор |
| `image` | FileField | blank=False; null=False; default=—; max_length=100 | — (связанная модель) | связанный редактор |
| `caption` | CharField | blank=True; null=False; default=—; max_length=255 | — (связанная модель) | связанный редактор |
| `order` | PositiveIntegerField | blank=False; null=False; default=0 | — (связанная модель) | связанный редактор |

Model ordering: `('order', 'id')`.


Сверка перечисленных типов полей, defaults, choices и параметров с конечным состоянием миграций: совпадает.

<!-- END AUTO-GENERATED MODEL FACTS -->

## Source of truth map

Все пути относительно корня репозитория; имена функций позволяют найти правило без зависимости от сдвига строк.

| Область | Source of truth |
|---|---|
| Модели / defaults / enums | `src/catalog/models/place.py`, `src/catalog/models/pricing_plan.py`; `src/catalog/migrations/` |
| Publication readiness | `src/catalog/services/content_quality.py`: place_quality_check/QualityCheck; `src/catalog/domain_admin/place.py`: PlaceAdminForm.clean, _handle_publish_submit, toggle_publication_view, mark_published. Отдельного place_readiness.py нет |
| Owner wizard validation | `src/catalog/forms.py`: OwnerPlaceEditForm/OwnerPlaceCreateForm; `src/catalog/services/permanent_place_rules.py`: publication_errors/client_rules |
| Wizard UI | `src/catalog/services/permanent_place_wizard.py`; `src/catalog/templates/pages/permanent_place_form.html`; `static/js/permanent_place_wizard.js`; `static/css/pages/permanent_place_wizard.css` |
| Pricing | `src/catalog/models/pricing_plan.py`; `src/catalog/services/pricing_plans.py`: normalize/replace/sync/build_public_price_summary; `static/js/owner_pricing_plans.js` |
| Price modes | Поле Place.price_mode отсутствует; существующие price_kind — PricingPlan; существующий schedule_mode не является price_mode |
| Числовые фильтры | `src/catalog/services/filtering.py`: CatalogFilters.apply |
| Schedule modes | `src/catalog/models/place.py`; `src/catalog/migrations/0096_place_schedule_modes.py`; `src/catalog/forms.py`: PlaceScheduleEditorFormMixin; `src/catalog/services/place_schedule.py`; `static/js/kidsmap_schedule_editor.js` |
| Location | `src/catalog/services/locations.py`, `geocoding.py`, `district_geometry.py`; `src/catalog/repositories/geocoding_repositories.py`; `static/js/owner_place_map_picker.js`; `src/catalog/data/baku_districts.geojson` |
| Taxonomy | `src/catalog/models/category.py`; owner/admin form queryset и clean; `static/js/kidsmap_dependent_subcategory.js` |
| Media | Place.public_image_file/gallery_files; `src/catalog/forms.py`: _validate_uploaded_image; `src/catalog/controllers/owner_places_controller.py`: create_place/save_edit_form; `src/catalog/repositories/django_repositories.py`; PlacePhotoInline |
| Permissions | `src/catalog/services/place_access.py`, `owner_place_use_cases.py`; `src/catalog/controllers/owner_places_controller.py`; managed repository в `src/catalog/repositories/django_repositories.py` |
| Moderation / POST | `src/catalog/views.py`: permanent create/edit; `src/catalog/controllers/owner_places_controller.py`: create_place/save_edit_form/submit_for_moderation; `src/catalog/domain_admin/place.py`; `src/catalog/models/owner.py`: PlaceOwnershipRequest.apply_moderation; `src/catalog/domain_admin/owner.py` |
| Значок «Проверено» | `src/catalog/services/place_card_validation.py`: validate_place_card; PlaceAdminForm и mark_verified |
| Public visibility | `src/catalog/services/content_quality.py`: public_place_queryset, published_place_queryset, place_catalog_visibility_reasons; `src/catalog/repositories/django_repositories.py` |
| SEO | `src/catalog/services/seo.py`: build_place_seo_payload; `src/catalog/services/seo_landing_visibility.py`; `src/catalog/sitemaps.py` |
| JSON importer/export | `static/admin/js/kidsmap_place_json_import.js`; `src/catalog/domain_admin/place.py`: validate_pricing_import_view/export_place_json_view |
| CSV/legacy migration | `src/catalog/management/commands/import_places.py`, `migrate_pricing_plans.py`; migrations 0084/0085 |
| Тесты | `src/catalog/testcases/permanent_place_wizard.py`, `pricing_plans_relational.py`, `place_card_validation.py`, `place_taxonomy_admin.py`, `owner.py` |
| Автоматическая сверка документа | `scripts/place_wizard_matrix.py` — ORM и disk migration facts; ручные разделы остаются code-review responsibility |
