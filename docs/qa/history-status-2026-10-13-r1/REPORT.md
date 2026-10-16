# Сверка истории модулей01–04 — 13 октября2026

Режим: сверка документов и точечное чтение source. Приложение/стенды/active_run не изменены, тесты и browser acceptance в этом запуске NOT RUN. Статусы ниже — доказательства соответствующих датированных отчётов, не новый production/runtime PASS.

## Текущий модульный реестр

| Модуль | Учтённые ID | Закрыто LOCAL по итоговым отчётам | Осталось в модульной очереди |
|---|---|---:|---:|
|01 Места|PLACE-QA-01–14|14|0|
|02 Организации|ORG-QA-01–05|5|0|
|03 Специалисты|SPEC-QA-01–04|4|0|
|04 Мероприятия|EVENT-QA-01–03|0|3 для свежего recheck|
|Итого по этим реестрам|26 пунктов|23|3|

PLACE-QA-08=CROSS-QA-03 и ORG-QA-02=ACCESS-QA-03 не добавляют отдельных исправлений. Общее compiled-locale дело пересекает несколько модулей;26 — число перечисленных модульных пунктов, а не абсолютное число всех уникальных первопричин за всю историю проекта.

Итоговые источники:
- [Модуль01, r6](../module01-full-2026-10-12-r6/REPORT.md),12октября: QA01–08 retained scoped results, QA09–14 CLOSED, LOCAL PASS.
- [Модуль02, r2](../module02-full-2026-10-13-r2/REPORT.md),13октября: ORG01–05 LOCAL accepted,248 unique backend tests,288 rendered states.
- [Модуль03](../module03-full-2026-10-13-r1/REPORT.md),13октября: SPEC01–04 CLOSED LOCAL,154 module methods accepted146+8 targeted supplement; source/runtime/preservation evidence.
- [Модуль04, historical audit](../module04-2026-10-10-r1/REPORT.md),10октября:3 OPEN P2. Новая ACCEPT-04 на этом ПК не выполнена. Современная isolated locale сборка в других модулях сама по себе EVENT-QA-01 не закрывает.

Остаток глобальной очереди11октября:73 групп задач для свежего recheck. В модуле02 принято4 исходных группы, в03 —3. Поэтому из той конкретной очереди остаётся66 групп /68 исторических ID. Дополнительно найденные QA09–14, ORG-QA-05, SPEC-QA-04 уже приняты и не увеличивают остаток. Это66 заданий для проверки, не66 подтверждённых неисправностей текущего checkout. Остальные модули здесь не аудировались. repair-index.json — исторический снимок, его73 не является актуальной суммой незакрытого после последующих repairs.

## Почему в старых документах проблем больше

- [Исходный обзор06октября](../content-entry-audit-2026-10-06.md):12 пронумерованных замечаний по четырём сущностям и общей UI copy.
- [Общая приёмка07октября](../content-entry-acceptance-2026-10-07.md):22 ACE-ID, часть описывает те же симптомы под другой нумерацией, часть — новые функциональные находки. ACE-19 — ошибка QA-фикстуры, не самостоятельный баг приложения.
- [Finalization07–08октября](../content-entry-finalization-2026-10-07.md):16 строк исправлений,18 ID за счёт объединённых ACE06/07 и ACE09/10; статус этих строк FIXED/PASS в том историческом запуске. Это не18 новых пунктов поверх22 и не современная глобальная приёмка.
- Поздние модульные отчёты переопределяют текущий статус конкретного scope. Старые task-файлы с текстом «следующий шаг: исправить» сохранены как история и автоматически не означают сегодняшний OPEN. Одновременно общий module PASS не закрывает старый отдельный пункт без поведения/evidence, соответствующих его требованиям.

## Исходные12 замечаний: найденная история выполнения

| Старый ID | Что было | Найденное выполнение / статус |
|---|---|---|
|EVENT-ADM-01|Неверные RU подписи владельца/площадки|[event-admin-fix06.10](../event-admin-fix-2026-10-06.md): исправлены PO и тогдашняя сборка. Позднее EVENT-QA-01 снова подтверждает stale MO с этими неверными подписями. Значит исторический source fix есть, окончательно новое Event runtime пока не принято.|
|EVENT-ADM-02|0из0 и ложный обработанный статус|Тот же fix: отдельный progress adapter, серверный checklist, «Новая карточка», сохранённый lifecycle status. Исторически исправлено/проверено. Повтор входит в ACCEPT-04.|
|EVENT-ADM-03|Select2/медиа685px на390|Тот же fix: scoped #event_form CSS; поздний module04 root geometry PASS. Исторически исправлено, новая проверка04 ещё NOT RUN.|
|SPEC-01 / EVENT-A11Y|Event online/offline без native keyboard semantics|[owner-event implementation07.10](../owner-event-implementation-2026-10-07.md): fieldset/radio, Space/arrows/focus. Поздний module04 отмечает native radio/Space. Исторически исправлено; не Specialist finding.|
|PLACE-01|Противоречивое требование точки карты|[Place implementation07.10](../permanent-place-form-implementation-2026-10-07.md) и[final module01](../module01-full-2026-10-12-r6/REPORT.md): необязательная точка, manual/range/0/0 и publication gates. LOCAL acceptance соответствующего поведения есть.|
|PLACE-02|Fallback обещан как сохранённый перевод|Те же reports: blank EN сохраняется blank, public AZ fallback отделён от сохранённых языков. LOCAL acceptance есть.|
|PLACE-03|Длинная форма/неясная навигация|Place implementation и текущий01: section navigation, error jumps, keyboard/sticky/long-text/native lifecycle. Scope принят; абсолютная длина страницы сама по себе не новый bug.|
|ORG-01|Name az и неясные save actions|[Organization implementation07.10](../organization-management-implementation-2026-10-07.md), текущие ORG-QA-04 locale repairs и full02. Соответствующие UI/сохранение приняты LOCAL.|
|ORG-02|Нет поиска/массового подключения готовых мест|Organization implementation и full02: search/preview/mixed batch,10 существующих карточек без пересоздания, согласия/readback/detach. Принято LOCAL.|
|ORG-03|Editor/Manager и преждевременное «создать отдельно»|Organization implementation/последующие org UI repairs/full02. Точечный source13.10: allow_separate отображается только внутри branch_duplicate_detected; старое условие больше не безусловно. Это source proof, не отдельный свежий browser recheck этого текста.|
|SPEC-02|Неудобная specialist admin navigation/широкие места приёма|[Specialist implementation07.10](../specialist-profile-implementation-2026-10-07.md): согласованный scope A–D, admin12sections/navigation/search/practice locations; finalization исправляет дополнительный nav clipping; текущий03 проверяет admin/mobile/public/person. Это реализация исторического UX scope, не обещание отсутствия любой возможной UX-проблемы.|
|COMMON-01|Смешанные UI языки/неподтверждённые обещания|Owner-event implementation прямо убирает обещания качества/регистрации/рассылки; соответствующая копия исторически исправлена. Полная межмодульная локализация не CLOSED: EVENT-QA-01/03 и остальные SITE/PUBLIC scopes ещё в очереди. Не закрывать COMMON01 целиком по PASS первых трёх модулей.|

## Мероприятия: что нельзя пропустить в новом recheck

Проверить не только3 новых repair prompts, но и старые сценарии:
- EVENT-ADM01–03 и EVENT-A11Y/SPEC01;
- ACE05 partial-draft category500, ACE06/07 venue geography/coordinates, ACE08 keyboard format, ACE09 public language fallback, ACE16 mobile arrow glyphs, ACE21 stale administrative save;
- Event-specific portions of CE-GET, CE-NULL, CE-GALLERY-FIRST, CE-GALLERY-KEYS from finalization;
- COMMON01 обещания/терминология; все8 acceptance contract points, lifecycle/roles/security/negative cases и NOT RUN из historical module04.

Для координат/fallback/adminCAS/галереи есть исторические FIXED reports. Они служат regression checklist, не разрешают повторные patches без актуального воспроизведения/конкретного плана.

## Предел точного счёта

26/23/3 — проверяемая арифметика именно текущих модульных ID01–04.12/22/16 относятся к разным историческим обзорам, перекрываются и не складываются. Единая таблица alias/root-cause для всех ранних ACE/PP/CE и поздних QA отсутствует; потому «общее уникальное число всех багов за всю историю» по этим документам без дополнительной полной классификации UNKNOWN. Общая межмодульная копия/непроверенные сценарии не исчезают из-за LOCAL PASS01–03.

Никаких исправлений приложения, запусков тестов/стендов, commit/push/deploy/production в этой сверке. Следующий разрешённый этап по отдельному поручению — PLAN/recheck module04, с указанным расширенным историческим checklist.
