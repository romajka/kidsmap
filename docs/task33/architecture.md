# KidsMap №33 — архитектурный контракт

Зафиксировано 2026-09-29, LOCAL HEAD c52b871ce5c18656a9eaf9854e66255c2629364e. AS-IS ниже — source discovery, не runtime/production доказательство. Остальное — согласованный TO-BE. Source символы перепроверять перед каждым этапом: line numbers и миграционный leaf меняются.

## AS-IS: что переиспользовать

Place standalone уже существует; owner create/edit/submit — OwnerPlacesController в src/catalog/controllers/owner_places_controller.py. Текущий create назначает owner/created_by, а edit public Place пишет live поля и при draft скрывает карточку — последний путь переделывается в 08.
OwnerTeamMembership/Invitation работают на конкретный Place в models/owner.py. MANAGER сейчас умеет team.manage и moderation reviews — эти права меняются по решениям D03/D07. Null-place legacy grant не является сетью.
Owner/admin/volunteer серверный readiness уже общий: forms.py использует evaluate_form_readiness. Старое утверждение о серверном конфликте gate не считать текущим. Client rules/JS проверять отдельно.
VolunteerPlaceRevision — отдельный payload/base/version с transactional approval; полезная база для нового pipeline.
PricingPlan — relational plans + legacy JSON/scalar compatibility; replace_place_pricing_plans и signals требуют target-scoped адаптации.
Owner постоянная форма — permanent_place_form → includes/permanent_place_workspace; JS привязан к 7 шагам. Admin Place имеет свой пятираздельный editor. Calendar отсутствует.
Specialist/Event уже существуют, целевых Organization/Program/Activity/OfferingGroup в проверенном catalog source нет. Event содержит собственный адресный snapshot; историческую фильтрацию не делать через текущий Place district.
PlaceReview допускает несколько rows/account, SpecialistReview unique account/target и сейчас заменяет approved текст на pending. Business review moderation endpoints существуют и подлежат запрету.

## Сущности

Organization: переводимые identity/content, contacts, owner/creator, publication и verified ownership отдельно. 0 Places допустимо. Organization не физическая точка.
Place: прежняя identity/URL/owner/media/scalars, nullable Organization и confirmed venue связь. Непроверенная/ожидающая relationship хранится отдельно. Joined Place сохраняет своего direct owner. Nature business/public_space хранится как одобряемое сведение; owner не обходит contact readiness простым unchecked флагом. Отдельное operating state open/closed не равно publication/is_active: старый inactive не считать подтверждённо закрытым и не раскрывать его как архив. Новый closed state допускается только после подтверждения по moderation contract.
Program: одна Organization, общий approved текст/переводы/category, candidate version. Activity: один Place, optional Program и отдельные local fields. OfferingGroup: один Activity, age/format/language/text schedule/local conditions/teachers.
PricingPlan: exactly one FK target — Place либо OfferingGroup; group Place выводится через Activity. Stable IDs сохраняются. Age restrictions тарифа не теряются.
Location: подтверждённая физическая площадка. Place по одному адресу независимы. Обычная правка адреса не изменяет все остальные Place этой площадки. Event venue snapshot исторически независимо.
New business hierarchy soft archival/PROTECT; удаление Org не каскадно удаляет Place/Activity/reviews. Range/order/positive bounds проверяет DB; межтабличные Org/Program/Place инварианты — центральный locked service.

## Права

Author, управляющий owner, подтверждённое владение, publication и staff moderation — разные состояния. Создание обычным user даёт управление его NEW объектом, не verified badge. Volunteer author не становится бизнес-owner. Создание existing claim не публикует контент.
Place direct owner/grants остаются scoped. OrganizationGrant: account, active, canonical action set, selected_places либо all_network; selected links проверены на active принадлежность.
Отдельные Org edit/Program manage/branch create permissions. Team.manage/transfer owner-only. Business review actions reply/report, не approve/reject.
Join/detach/invitation/transfer блокируют и перечитывают current targets/owners/versions. Network доступ вычисляется по текущей связи, не копируется в постоянные Place memberships. Informational affiliation не authorizing.
После transfer team suspended/invitations canceled. Branch created by delegated actor принадлежит owner Org, created_by actor; selected scope не меняется. Отозванные права повторно проверяются также background workflow.
После detach approved общая Program часть материализуется в Activity с provenance, local IDs остаются; inherited contacts прекращаются без копирования/автоматического hiding.

## Редакции и черновики

Один approved content source и отдельные candidates с schema_version/base source version/author/moderation. Legacy base fields должны продолжать отражать approved public данные; draft не пишет их.
Сумма цены/расписание применяются на explicit save; dependent price+conditions package gated целиком. Patch approval не затирает независимые свежие поля. Program approved pointer распространяется атомарно по active links, cache invalidation after commit.
Draft API принимает allowlisted entity type, draft_id, schema_version и expected version; возвращает draft_id/version/saved_at/status/errors. Stale update — 409 с сохранённым вводом; validation — структурированные ошибки; чужой target — отказ по существующему security contract.
Incomplete create draft не требует invented name/age/price; idempotent draft materialization не создаёт повторные business objects. Фото связано с draft после успешного upload. Server draft доступен только текущему разрешённому actor; browser fallback keyed account/object.
Public UI: published + pending edits одновременно; new pending; rejected reason; browser-only vs server saved; unavailable save; conflict; empty state. Никаких fake процентов readiness.

## Публикация и готовность

Readiness/config единственная серверная. AZ approved content требуется у новых карточек, не массовое снятие старых. Photo и coordinates optional. Business contact: local или active approved inherited phone/WhatsApp/website; public-place может без contacts.
Для age/price/schedule используются явные existing known/unknown/on_request/free режимы, не fake нули. Class age/text schedule относятся к группе, opening hours к Place. Draft type/relationship/file validation действует и без полного readiness.
Старый published compatibility path поддерживается. Published status, public visibility, verified ownership и information badge не смешивать.

## Тарифы

Target-scoped replacement никогда не удаляет plans другой цели; supplied foreign ID отвергается; fingerprints не переиспользуются между targets. v1 Place editor/import работает с direct plans, новый nested versioned contract с Activity/groups.
Signals принимают как direct, так и group target и находят owning Place через resolver. Один summary для editor/details/cards/map/SEO и compatibility projection. Untouched scalar-only Place fallback сохраняется; draft Activity сам по себе не очищает старую цену.
Trial/single/membership одной группы — один block; regular amount с unit, обязательные fees отдельно, free trial не free program. Currency не зависит от locale. Conditions confirmation отдельная дата; неизвестное время не выдумывать.

## Отзывы

Сохраняем typed PlaceReview/SpecialistReview; новые ActivityReview/EventReview. Отдельные typed revision models и общий service; GenericForeignKey и второй ReviewThread не вводить.
Head известного(account,target): latest approved source, иначе latest source; effective order (moderated_at if present else created_at, pk). Исторического approval time не придумывать. Siblings marked archive с stable IDs/links; unknown/null-account отдельные identities.
Unique only known-account current heads после backfill. Каждый исходный текст имеет baseline revision. Existing reaction IDs остаются привязаны к исходной revision, новые reaction uniqueness/counts по revision. Не объединять sibling reactions.
Head имеет approved current revision и candidate; pending/rejected не вытесняют current. Rating — current approved account contributions, архив не double count. Org feed маркирует target без общего балла.
Cooldown сохраняется. Owner reply/report только; staff approval versioned. Account deletion/anonymization покрывает revisions/new types и reactions без изменения действующей retention политики.

## Специалисты

Person claim проверяет KidsMap; предлагаемая Org не получает person ownership. Employment: role/start/end и оба confirmations. Invitation/current Place FK не доказательство employment. Online PracticeLocation история не удаляется.
Identity documents always private. Specialist chooses public certificate + KidsMap approval. Dedicated reviewer permission, private filesystem/storage; download endpoint checks state/access, direct /media path не обходит проверку. Production перенос media — отдельный release operational action, не автоматическая data migration.

## События

Organizer exactly one Organization или подтверждённый Specialist; format physical/online; venue не выдаёт permissions. Event publication отдельно от occurrence/cancel/reschedule/history. Одно проведение — один ID.
Dates aware, Asia/Baku. Period overlap event.start < period.end AND event.end > period.start; local boundaries, default upcoming. Approved canceled/past detail остаётся public; private/draft/rejected/deleted закрыты.
Approved venue/address/coords snapshot не меняется от Place edit. Unknown historic location не backfill текущим. Архивный district filter только по snapshot.
/events/ query: view=list|calendar, month=YYYY-MM, date=YYYY-MM-DD; list date_from/date_to. Calendar весь filtered month, list pagination отдельно. Mode/month/day сохраняют q/category/age/format и допустимые existing filters. Mobile day selector+day list. Generated series и registration/payment вне scope.

## Поиск, карта и языки

Matched conditions в одном Activity/group; one Place result. General admission Place поддерживается без fictitious Activity. Mixed legacy reader не даёт ложного conjunction или double result. Cards show matched groups; detail остальные отдельно.
Техническая реализация19: Activity taxonomy читается только из approved `program_snapshot.category_id` и явно известного `subcategory_id`; Place category не назначается автоматически всем занятиям. Текущий Program writer содержит category, но не subcategory; standalone writer не содержит Activity taxonomy. Неизвестное соответствие консервативно исключается из точного category+age поиска; общий каталог, age-only по реальной Group и прямые страницы остаются. Place-only age matching разрешён для approved public_space или действующего direct admission tariff. Category-only legacy browsing сохраняется без published Activity. Options считают distinct Place по тому же mixed reader. Batch presentation имеет request-local trust markers с обязательным снятием; direct contact/detail resolver сохраняет fresh visibility/affiliation checks. Старые price parameters принимаются, но не фильтруют и не сортируют; normalized navigation не заявляет ценовой фильтр.

Org detail/discovery по имени и из Place, без отдельного directory. Map confirmed shared venue ≠ visual coordinate cluster. No coords сохраняет list.
Техническая реализация20: общий map_payload группирует только active confirmed Location + explicit Place venue confirmation, numeric point key venue:id с independent members. List/map и homepage GET map API используют PlaceListFilters/prepare_cards; counts businesses отдельно от physical pins, no/invalid coords остаются в list. Address-only venue не заимствует чужие координаты. Address/coordinate save либо approved publication patch отсоединяет только изменённый Place; shared Location и исторические Event не переписываются. Frontend map request отменяет старый response, очищает stale markers/popup, routes содержат только numeric public destination.
AZ fallback marked, incomplete RU/EN canonical на AZ без standalone hreflang/sitemap. Genuine content translation включает собственные взаимные language URLs. Old URLs сохраняются либо same-language direct redirect; исторические Place страницы 200 с отметкой, без default массового noindex.
Общие prices/contacts/translations/visibility возвращают metadata source для editor; frontend enums из backend. Existing analytics subject identity использовать, не фабриковать старые organization/activity events.

## Уведомления

Cabinet workflow inbox + durable EmailOutbox. Dedupe event kind/entity/version/recipient, retry и sent state. Transaction rollback не отправляет фиктивный event; SMTP failure не отменяет business action. Action link требует login/current rights/CSRF на POST.
Не отправлять реальные письма в тестах и текущем документальном запуске. Runner и operational расписание готовятся для отдельно порученного release, не меняют production cron.

## Экраны

Общая account navigation; Place continuous form четыре секции. Organization overview/branches/programs/team/about. Empty/draft/pending/rejected/conflict/live+pending separate states. Program impact list, contact provenance, branch selected/all scope явно. Admin плотный workspace со current/candidate diff и отдельными publication/ownership badges.
Макеты обязательны: этапы 02–03 до schema/business implementation; дополнительные Specialist screens перед 25. UI tokens/Material Symbols действующие, no новый framework/fonts. Макеты не являются functional/browser-QA доказательством production.

## Данные и перенос

Expand → compatible reader/writer → isolated conversion → cohort enable. Rule map source type/id/rule version/piece key → target; unique key, fingerprint и checkpoint. Dry-run truly no write. Apply одна source conversion с checkpoint в одной транзакции, stale source manual review.
IDs/URLs/media/favorites/reactions/proposals сохраняются. Никакого guess по names/coords/price text. Угаданные старые groups/owners не появляются. Manual review не останавливает весь каталог.
После новых writes старый binary без совместимого reader не rollback target. Disable new writes/UI, сохранить новое, compatible binary или repair forward. Reverse schema/вчерашний dump с потерей нового не считать восстановлением.

## Проверки и выпуск

Stage 04 создаёт isolated PostgreSQL runner/fixtures; DJANGO_TESTING=1, explicit overrides DB/media/email, disabled integrations. Проверить labels/discovery, commands/counts/errors и same fixture query baseline.
Code stages: meaningful negative/domain/integration/concurrency; changed UI browser AZ/RU/EN 320/360/390/768/1024/1280/1440. Scope reviewers real execution identity; source inspection/stubs не rendered/external success.
Release blockers: потеря данных, чужой доступ, wrong review target, false search match, contradictory price, broken old URLs, private docs leak. Existing baseline failures отделять от regressions, не ослаблять assertions ради green.
R1 и R2: isolated conversion/recovery с post-switch records и отдельные release пакеты. Production deploy/backup/restart/schema/config changes и push main в этих промптах не разрешены.
