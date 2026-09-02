# Полный аудит карточки места KidsMap

Дата: 2026-09-01. Код и данные не менялись. Проверена рабочая SQLite `db.sqlite3` только запросами `SELECT`; Django-тесты и сервер не запускались: в окружении нет установленного Django. Визуальная проверка браузером не выполнена.

## 1. Краткое резюме

Это Django-приложение. Публичная карточка доступна только для `Place(is_active=True, status=published, deleted_at IS NULL)`. Главный URL `/place/<pk>-<slug>/`; старый `/place/<pk>/` делает permanent redirect. Страница двухколоночная на desktop, с основной информацией справа и галереей/тарифами/отзывами слева; на mobile порядок остаётся DOM-порядком, а CTA становятся fixed bottom bar.

Новая модель тарифов `PricingPlan` и структурные `PlaceScheduleDay/Interval` уже используются. Однако в `Place` остались legacy JSON/ценовые поля, а форма владельца не даёт редактировать `phone2`, `phone3`, `cover_photo`, `age_open_ended`, локализованные условия и custom price badge. Это главное ограничение редизайна: нельзя считать, что «одно поле = один отображаемый блок».

## 2. Карта файлов и зависимостей

| Назначение | Файл | Класс/функция/селектор | Строки | Используется сейчас? | Комментарий |
|---|---|---|---:|---|---|
| URL | `src/catalog/urls.py` | `place_detail`, `place_detail_legacy` | 158–159 | Да | Канонический путь содержит ID и slug. |
| Public view | `src/catalog/views.py` | `place_detail` | 321–337 | Да | Добавляет pricing summary и claim context. |
| Контекст | `src/catalog/controllers/place_controller.py` | `build_detail_context` | 797–838 | Да | SEO, карта, отзывы, GA event, favorite state. |
| Доступ к place | тот же | `get_active_place_with_gallery` | 786–795 | Да | `select_related(category)`, prefetch gallery/events/schedule/pricing. |
| Шаблон | `src/catalog/templates/catalog/place_detail.html` | `detail-page` | 1–895 | Да | Один основной шаблон. |
| Include | `catalog/includes/breadcrumbs.html` | breadcrumbs | template:27 | Да | Видимые breadcrumbs. |
| Include | `catalog/includes/review_item.html` | review row/reactions | template:338 | Да | Отзыв + голосование. |
| CSS | `static/css/pages/detail.css` | `.detail-page`, media queries | 1–2589 | Да | Подключён с `?v=5`; содержит старые селекторы тоже. |
| Галерея | `static/js/place_gallery.js` | Swiper init | 1–93 | Да | Swiper 12.2.0, стрелки, thumbs, счётчик; lightbox нет. |
| Inline JS | `place_detail.html` | tariffs toggle, stars, fallback | 813–894 | Да | Хрупко привязан к id/classes. |
| Общий JS | `base.html` | tracking/like/auth-required | см. base scripts | Да | Обрабатывает `data-track-*`, likes. |
| Цена | `services/pricing_plans.py` | `build_pricing_summary`, `build_public_price_summary` | 461, 763 | Да | Серверный источник UI/JSON. |
| Расписание | `services/place_schedule.py` | public row/summary builders | см. файл | Да | Нормализует 7 дней и интервалы. |
| SEO | `services/seo.py` | `build_place_seo_payload` | 348–451 | Да | LocalBusiness, BreadcrumbList, map URL. |
| Валидация карточки | `services/place_card_validation.py` | `validate_place_card` | 87+ | Да, admin/command | Не блокирует отображение. |
| API | `views.py` | `place_pricing_api` | 46–69 | Статус неясен | Есть view, но URL в `catalog/urls.py` не найден: с текущим роутингом недоступен. |

Middleware/context processors: `catalog/context_processors.py` включает язык/настройки для публичных URL; специальный context processor карточки не найден. Template tags: `{% load catalog_i18n %}`; использованы `review_count`, стандартные i18n/static. Отдельного AJAX карточки кроме общего POST favorite/reaction не найдено.

## 3. Путь данных

`SQLite → Place + Category/Subcategory + PlacePhoto + PricingPlan + PlaceScheduleDay/Interval + PlaceReview → owner/admin/import → published queryset → PlaceController.build_detail_context → place_detail.html → detail.css/place_gallery.js/base JS`.

Заполнение: админ использует `src/catalog/domain_admin/place.py`; владелец — `OwnerPlaceCreateForm/OwnerPlaceEditForm` и `OwnerPlacesController`; импорт — `management/commands/import_places.py`; демо/seed — `seed_catalog_demo_places.py`; тарифы сохраняет `replace_place_pricing_plans` (удаляет отсутствующие записи и синхронизирует legacy поля). Публикация/черновик/moderation: URL/actions `urls.py:132–141`, views `views.py:852,1105,1161,1174,1187`.

## 4. Модели и поля

Обозначения: `R` — required на уровне модели, `B` — blank, `N` — null. Там, где не указан default, его нет. Поле показывается только если соответствующее условие ниже выполняется.

### Place (`models/place.py:27–583`)

| Поля | Тип / blank/null / default | Заполнение и публичное использование |
|---|---|---|
| `id` | Auto PK | URL, analytics. |
| `name` | Char(255), R | технический fallback; H1 использует `name_i18n`. |
| `slug` | Slug(255), B, unique, `''` | генерируется `save()`; canonical URL. |
| `name_az,name_ru,name_en` | Char(255), B, `''` | owner/admin/import; H1/SEO. AZ→RU→name; EN→RU→name; RU→name. |
| `description_az,ru,en` | Text, B, `''` | lead только exact language; fallback отсутствует. |
| `category` | FK Category.code, R, PROTECT | всегда highlight/chip/breadcrumb/SEO. |
| `subcategory` | FK Subcategory, B/N, SET_NULL | highlight только если есть. |
| `age_from,age_to` | PositiveSmallInt, B/N | highlight/chip; `age_from>age_to` запрещён model clean. |
| `age_open_ended` | Bool, default false | проверяется при adult validation, **не учитывается** `age_display` (достаточно age_from для `+`). |
| `offers_adult_classes` | Bool false | note рядом с возрастом; требует детский диапазон. |
| `district,metro,address` | Char(100/100/255), B | chip/contacts/address highlight; map зависит только от coords. |
| `phone1,phone2,phone3` | Char(50), B | `phone_numbers` removes exact duplicates; phone1 CTA/WhatsApp. |
| `owner,created_by` | FK user, B/N, SET_NULL | права; не рендерятся публично. |
| `cover_photo,photo` | File, B/N | photo предпочтительнее; cover только fallback; gallery then `PlacePhoto`. |
| `instagram` | Char(255), B | CTA/contacts/SEO sameAs; URL normalizes `@`/domain. |
| `website` | URLField, B | contacts/SEO sameAs; URL normalizes scheme. |
| `schedule` | Text, B | legacy textual schedule. |
| `schedule_mode` | choices `regular/by_appointment/variable/events`, default regular | label in unified block. |
| `schedule_note_az,ru,en` | Text, B, `''` | exact language; RU legacy fallback, AZ/EN no fallback. |
| `lesson_duration_minutes` | PositiveSmallInt B/N | highlight and summary; `0` hidden. |
| `lesson_format` | `group/individual`, B | legacy; pricing summary may use tariff format. |
| `lessons_per_week,lessons_per_month` | PositiveSmallInt B/N | used pricing summary, not standalone UI. |
| `pricing_plans_legacy` | JSON B, `[]`, DB `pricing_plans` | fallback only if no relational rows; legacy. |
| `is_temporary,temporary_start,temporary_end` | Bool false / datetime B/N | catalogue filtering; no distinct card badge confirmed. |
| `lat,lng` | Float B/N | map only when both exist. |
| `price_from,price_to,price_per_lesson,price_per_month,price_per_8_lessons` | Decimal(10,2) B/N | derived from relational active primary AZN plans; legacy fallback. |
| `extra_conditions,additional_info` + `_az/_ru/_en` | Text B | unified footer; RU base fallback only. |
| `custom_price_badge_az,ru,en` | Char(120) B | Status неясен: есть в model/migration, detail template не использует. |
| `likes_count,rating_avg,rating_count` | positive/float defaults 0 | cached stats; review signals recalculate. |
| `is_home_recommended,home_recommended_order` | Bool false/int 0 | home only. |
| `is_active,is_verified,status` | Bool false/Bool false/choices draft,pending,published,rejected default published | public gate: active+published+not deleted. Verified not shown here. |
| `rejection_reason,last_verified_at,published_at,deleted_at,deleted_by,created_at,updated_at` | text/date/FK/timestamps | service/admin lifecycle; not public UI. |

Methods/properties: gallery ordering and safe existence `260–308`; age `311–318`; localization `201–229,398–409`; phone dedupe `388–396`; schedule `443–470`; public/publication state `481–510`; soft delete `512–530`; slug/URL `544–583`; `refresh_rating_stats` aggregate `580–583`. Important: `description_i18n` has no fallback but name does.

### Связанные модели

| Модель.поле(группа) | Тип/ограничения | Где используется |
|---|---|---|
| `Category.code,name,name_az/ru/en,icon,color_bg,color_text,is_active,order,deleted_*` | code PK; active manager filters active/nondeleted | category label/icon/color; `name_i18n` fallback to `name`, `models/category.py:86–199`. |
| `Subcategory.category,code,name,name_az/ru/en,icon,is_active,order,deleted_*` | category PROTECT; code unique | one optional subcategory; no multi-category/subcategory relation. |
| `PlacePhoto.place,image,caption,order` | FK CASCADE; order default 0 | gallery image file, caption **not rendered**, `models/place.py:591–612`. |
| `PlaceScheduleDay.place,weekday,is_closed,is_24_hours,order` | one day state; weekdays mon–sun | structured schedule. |
| `PlaceScheduleInterval.schedule_day,start_time,end_time,order` | FK day (CASCADE), interval order | multiple periods/breaks; renderer groups days only when rows equal. |
| `PricingPlan` | full matrix below | current tariff source. |
| `PlaceReview.place,user,author_name,is_anonymous,rating,text,contains_profanity,likes_count,dislikes_count,is_approved,status,rejection_reason,session_key,created_at,updated_at` | unique `(place,user)`; score 1–5 coerced; status approved/pending/rejected | public queryset only approved; author must be auth for UI. |
| `PlaceReviewReaction.review,user,session_key,value,created_at,updated_at` | unique per user or anonymous session; value ±1 | included review item; save/delete refreshes counts. |
| `PlaceLike.place,user,session_key,created_at` | unique per user/session | favorite, auth-only UI despite anonymous schema support. |
| `PlaceOwnershipRequest`, `OwnerTeamMembership`, `OwnerTeamInvitation`, `PlaceChangeAudit` | ownership/team/audit models | management permissions; ownership claim block deliberately absent from card test. |
| `Event`, `Specialist` | independent entities | prefetched `events` but no display in template: likely leftover/future coupling. |

### PricingPlan (`models/pricing_plan.py:11–251`)

Fields: `place` FK CASCADE; `product_type` required (admission, visit, lesson, membership, course, camp, event, excursion, tour, rental, addon, registration_fee, deposit); `lesson_format` B (open_visit/group/individual); `charge_role` primary/addon/registration_fee/deposit default primary; `billing_mode` one_time/recurring/installment default one_time; `billing_interval` day/week/month/year B; `billing_interval_count,billing_cycles` B/N; `price_kind` exact/free/from/range/on_request default exact; `price,price_min,price_max` Decimal B/N; `currency` Char(3) default AZN; `quantity,quantity_unit,sessions_per_week,sessions_per_month` B/N; `is_unlimited` false; validity fields; audience child/adult/family/etc; age/min-max people/day type; AZ/RU/EN title/conditions (title 160 chars); required/active/order; `verified_at`, `source_url`, timestamps.

DB/model validation is strict: nonnegative numbers, range ordering, kind-to-price shape, recurring vs installment fields, quantity pairs, date/age/people ordering, charge-role pairing (`pricing_plan.py:101–230`). Limit user payload to 12 (`services/pricing_plans.py:182–291`). `title_i18n` and `conditions_i18n` do fall back AZ→RU→EN (`236–242`). Price synchronizer updates Place legacy values only from active primary AZN plans (`services/pricing_plans.py:345+`).

## 5. Формы, права и lifecycle

`OwnerPlaceEditForm` fields: name/description in three languages, category/subcategory, age from/to, adult flag, region/district/metro/address, hidden lat/lng, **phone1 only**, instagram/website, schedule/mode/notes, duration/format/frequency, hidden pricing JSON, conditions/info, temporary dates, photo, extra gallery upload (`forms.py:848–1044`). Create inherits it (`1436+`). On submit for moderation it requires `name_az, description_az, category, age_from, age_to, address, phone1, photo` (`1098–1111`); schedule can be required by mode flag. Validation includes age 0–18 UI errors, URL, coordinates/location normalization and pricing parsing. Gallery hint permits max 10 uploads, HEIC conversion.

Admin is broader and can manage status, legacy contact/photo fields and audit/validation; exact form layout is `domain_admin/place.py`, not public template. Import maps are in `management/commands/import_places.py`. Status changes: draft → submit pending → moderation published/rejected; separately published can be inactive/unpublished or soft-deleted. Public view has no edit/manage button for owner/editor/moderator/admin.

Mismatches: model permits `phone2/phone3` publicly but owner form cannot edit them; model has base/localized conditions but form exposes base only; `cover_photo`, `age_open_ended`, custom badge and `is_verified` absent owner form; `pricing_plans_legacy` remains fallback; `photo` required for owner submission but not model/public logic.

## 6. Матрица отображения

| Блок | Показывается | Варианты / fallback |
|---|---|---|
| H1 | always | i18n name fallback; unlimited `Char(255)`, wraps naturally. |
| Description | exact-language nonempty | `linebreaksbr`; no AZ/EN/RU fallback, so absent block. |
| Gallery | `gallery_files()` nonempty | photo → cover only if photo absent → ordered gallery. 1 no arrows/thumbs/counter; >1 all. File missing is excluded server-side; client fallback placeholder on img error. No fullscreen/lightbox. |
| Price/schedule | any price/plans/rows/text/note/info | unified card; first 3 plans visible, toggle rest. On-request likely headline label but no numeric amount. |
| Age | `age_display` | `a–b`, `a+`, or `b`; `0+` works; no age hidden. Adult classes note only with a valid child range. |
| Highlights | category always; rest conditional | address truncated 58 chars; subcategory optional. |
| Contacts | card always | phone list deduped, IG/address/site optional; empty explanatory state. WhatsApp generated from `phone1` blindly. |
| Map | both lat/lng | Google iframe + directions; address alone yields no map. |
| Reviews | always | cached rating shows 0.0/no reviews; approved reviews only, sort GET; no pagination in template. |
| Favorite | all users | auth gets POST/AJAX; guest gets login trigger. |
| Service/owner data | never | verified, dates, owner, moderation, source, ads/chat report-change absent in card. |

Price cases: relational active primary AZN bounds determine aggregate. `free=0`, exact `price>0`, from requires `price_min>0`, range requires both, on_request numeric null. Mixed free/paid can aggregate min 0; multiple currencies are storable but legacy Place aggregate excludes non-AZN. UI always shows plan `price_str`; exact formatting/localization occurs service-side. Catalog/map use `place.card_price_badge`; detail uses `pricing_summary`: possible discrepancy with secondary/non-AZN plans and legacy records.

Schedule supports regular/by appointment/variable/events, seven weekdays, closed/24h, several intervals. It is data-level distinct from lesson schedule only by `schedule_mode`/wording; there is no separate business-hours model. `schedule` text is legacy fallback. Seasonal dates exist only on Place and do not alter rows automatically.

## 7. Interaction matrix

| Element | Who | Action/backend | Tracking/result |
|---|---|---|---|
| Gallery/thumb/arrow | everyone | Swiper client, no backend | counter/thumb sync; keyboard provided by Swiper defaults; no GA event. |
| Tariffs toggle | everyone | inline JS only | expands all hidden after third; no loading/event. |
| Call/WhatsApp/IG/map | everyone when data | external `tel:`, wa.me, IG, Google directions | `cta_call`, `cta_whatsapp`, `cta_instagram`, `cta_map`, params place id/source (`template:424–510,749–762`). |
| Favorite | auth / guest | POST `/place/<id>/like/`; guest login | event `favorite_toggle`, `place_id,page_type,action` (`views.py:341–369`). |
| Review submit | auth | POST `/place/<id>/review/`; rating + required text | moderation/result redirect; review action tracked server-side. |
| Sort | everyone | GET `review_sort` | full reload; values from `REVIEW_SORT_CHOICES`. |
| Like/dislike review | auth/anonymous depending controller | POST `/place-review/<id>/vote/` | re-counts reaction; exact GA event status unclear. |
| Map iframe | everyone with coords | Google embed | no explicit map load event. |

No page ad, chat, report-change, organization response, gallery fullscreen, contact copy, site CTA, or card-management interaction is present.

## 8. SEO, i18n, accessibility, analytics

SEO: title/meta/OG image/Twitter image at template `4–14`; JSON-LD BreadcrumbList + LocalBusiness. Canonical/hreflang/robots are inherited from `base.html`/settings; inspect showed no card-local override. Canonical slug redirect works. Unpublished card 404s because queryset gate, hence not indexable through this view. Schema uses only primary phone/address, addCountry AZ, geo only coords, offers excludes `from` prices (`seo.py:365–423`).

I18n: Django PO files `locale/az|ru|en/LC_MESSAGES/django.po`; template mixes `{% trans %}` with hardcoded AZ/RU/EN ternaries. Key defect: many detailed-card labels are inline and therefore not PO keys; `WhatsApp`/Instagram intentionally untranslated. Content fallback differs by field: names robust; descriptions no fallback; schedule/extra info fallback to base only in RU; tariff title/conditions robust cross-language fallback. This causes real blank AZ/EN sections despite RU source.

Accessibility: one H1, section H2 and nested H3/H4 (tariff groups); image main alt is place name, backdrop alt empty, thumbnails repeat place name. Buttons have aria labels; counter live region. Risks: description gets `<p>` inside `<p>` (`template:556–560`) due `linebreaksbr`; map iframe title must be confirmed from lines 638+; no visible focus audit/browser run; external CSS uses color-only rating stars; no lightbox keyboard because no lightbox.

Analytics: page-open context event `place_open` with `page_type=place_detail, place_id, place_category, has_phone, has_instagram, has_coordinates` (`place_controller.py:825–837`) and server visit tracking. CTA attributes above are forwarded by shared tracking code. No explicit gallery/review/reaction/ad impression event found.

## 9. Реальные данные (SQLite snapshot)

| Показатель | Значение |
|---|---:|
| Всего places / public | 76 / 68 |
| Статусы | 68 published+active, 1 published+inactive, 7 draft+inactive; pending/rejected 0 |
| Без coords / района / метро | 11 / 27 / 51 |
| Без phone1 / Instagram / website | 5 / 51 / 52 |
| Без main photo / без gallery rows | 49 / 53 |
| Gallery rows | 23 places with 1–5; 0 with 6+ |
| Без возраста / без address | 5 / 5 |
| Без AZ description / AZ name | 6 / 3 |
| Relational tariffs | 5 rows; 74 places none; 2 places with 2–3; all 5 active exact |
| Reviews | 71, all approved |

Representative safe public scenarios: `232 / demo-full-sport-academy` — 4 gallery images, full demo; `235 / showcase-art-studio` — 3 images; `240 / baku-boulevard-amusement-park` — 3 images; `217 / district-3` — published but inactive, so inaccessible; `218 / auc` — draft and inaccessible; `233 / draft-before-category-final-check` — long title draft, sparse data. No 6+ gallery, 4–12/12+ tariffs, pending/rejected place, range/from/free/on-request price scenario exists in this DB. `age_from > age_to` conflicts were not found in the read-only SQL snapshot.

## 10. Design and responsive structure

DOM order: left column breadcrumbs → H1/gallery → price/schedule → highlights → reviews; right column hero chips → CTA/description → contacts → map → service notes → mobile sticky. Desktop visual two columns changes perceived order: right-column CTA/description appears alongside gallery. CSS base `detail.css:26+`; gallery is 4:3 at mobile (`1912–1925`); max-width 760 changes to one column and fixed sticky bar (`2000–2030`); <=420 reduces H1 to 27–34px and thumb to 72px (`2032–2073`). Unified pricing desktop >=900 has special grid only no-plans+schedule (`2426–2497`). Exact browser pixel widths/container computed values: **Статус неясен** without running page; do not treat source rules as visual validation.

Desktop 1440/laptop 1024–1280: two columns, cards white/green border 18–20px, gallery thumbs under hero image, side CTA then contacts/map. Tablet around 768 crosses to one column per `max-width:760`, so 768 likely remains desktop layout. Mobile 360–430: DOM blocks stack, gallery 4:3, bottom two-button fixed phone+WhatsApp only when phone exists; it can overlap content without adequate safe-area/scroll padding verification.

## 11. Debt, bugs, risks

1. `age_open_ended` not used by display; values can confuse editors.
2. Description exact-language only versus title fallback is a tangible content gap.
3. WhatsApp renders for any phone1, no WhatsApp flag/validation; extra phone buttons are calls only.
4. Public form mismatch makes existing phone2/3 and cover photo hard to maintain.
5. `PlacePhoto.caption` unused; `events` prefetch unused; `pricing_plans_legacy` and scalar price fields are legacy compatibility.
6. Pricing UI hides after 3 even though validation permits 12; grouped H4 may appear among hidden plan rows awkwardly.
7. Detail template has inline styles (`display:none`) and inline JS, CSS contains obsolete `.detail-pricing-*` selectors not used by current unified markup.
8. `place_pricing_api` has no route found: orphan functionality.
9. Map embed is third party and no graceful map UI state except hiding entire section.
10. Detail context mutates database by self-healing stale rating stats (`place_controller.py:805–806`) on GET: an unexpected write path.
11. Tests depend on exact class names/text: especially gallery, breadcrumbs, map, star picker and translations.

## 12. Tests

Relevant tests: `testcases/public.py`: `test_place_detail_page_includes_breadcrumb_and_aggregate_rating_schema` (916), visible breadcrumbs (983), map/directions (1011), all phones (1037), star picker localization (2001), schedule/pricing (2183/2217), no owner claim (2238), disclaimer (2263), free price (2307), Swipe gallery (2333), AZ labels (2499), guest review copy (2593). `adult_classes.py:215`, `tracking.py:162`, `admin.py:3426` rating repair, `owner.py:961` legacy redirect. No screenshot/visual/responsive test found. Preserve/update these contracts with any redesign.

## 13. Ограничения и неясности

* Статус неясен: actual admin field exposure/import schema beyond source inspection; must inspect rendered admin and importer mappings before implementation.
* Статус неясен: canonical/hreflang/robots exact output and focus/contrast/browser layout — Django missing prevented server/browser run.
* Статус неясен: whether a separate URL for `place_pricing_api` is registered in a project-level router not found by repository search.
* No database claim was made about broken remote images: `gallery_files()` checks configured storage, but browser network was not run.

# ПАКЕТ ДАННЫХ ДЛЯ ДРУГОГО ИИ

Обязательны: H1/name, category, public gating; everything else optional. Possible blocks: breadcrumbs, gallery/placeholder, CTA, description, location/rating/category/age/format highlights, unified price+schedule+tariffs+notes, contacts, map, reviews, favorite, mobile sticky CTA. Hide description, map, each contact channel, age, price/schedule and optional highlights when source absent; show gallery placeholder when no valid file; reviews/contact containers remain with empty state.

Keep: canonical ID-slug URL and redirect; public status gate; Swiper gallery and error fallback; phone1 call/auto-WhatsApp; map directions from both coordinates; all phone numbers in contacts; favorite login/POST behavior; review submit/sort/reactions; 3-language content and their **current** inconsistent fallbacks; rich tariff rules and max 12; structured schedule multi-interval/closed/24h; schema/analytics attributes and current test selectors.

Long data: name 255, address 255, IG/site URLs 255, unlimited text descriptions/conditions/notes, tariff title 160, many schedule intervals. Desktop uses two columns; mobile stacks DOM and retains fixed bottom phone/WhatsApp CTA. Existing edge cases: 53 no gallery, 11 no coords, 51 no metro/Instagram, 74 no relational tariffs, six missing AZ description, five no age/address/phone1; no current real examples of 6+ images, >3 tariffs, price kinds other than exact, or non-published pending/rejected states.

## Приложение A. Проверка production (2026-09-01)

После первого аудита открыты реальные страницы `https://kidsmap.az` через браузер. Это приоритетнее локального SQLite-снимка; production и локальная база не совпадают.

Подтверждённые живые сценарии:

| URL / состояние | Что подтверждено |
|---|---|
| `/place/80-baki-zooloji-parki/` desktop | 6 изображений, Swiper с предыдущей/следующей стрелкой, счётчик и 6 миниатюр; цена `0–15 ₼`; два объединённых диапазона часов; 9 тарифов: первые 3 видимы, кнопка «показать все» `+6`; age `0+`; пустые отзывы; все CTA; карта; дополнительная информация; disclaimer; рекламный слот; chat iframe. |
| Та же страница 390×844 | DOM stack, тот же контент; фиксированная bottom bar «Звонок / WhatsApp»; отдельный чат поверх страницы. Это обязательные mobile состояния. |
| `/place/73-sonic-athletics-club-2/` desktop | 4 фото; фиксированная цена `120 AZN`; 7 разных дней включая «Закрыто»; одновременно structured schedule **и** дублирующий текстовый schedule; duration 60 minutes; пустые отзывы; без website в contacts. |

Критические исправления к разделам 9–10: на production есть 6+ фото и >3 тарифов, хотя локальная SQLite этого не содержит. На живых карточках реально показаны служебный блок «Дополнительная информация» (format + added date), disclaimer, реклама и чат; они не должны быть потеряны при редизайне. Названия навигации/часть aria-label в AZ, но `navigation` accessibility name остаётся по-русски «Хлебные крошки»: это подтверждённое смешение языков. В production на карточке с structured schedule отображается дублирующий свободный текст расписания — это отдельный контентный edge case, а не безопасно удаляемый визуальный дубль без продуктового решения.
