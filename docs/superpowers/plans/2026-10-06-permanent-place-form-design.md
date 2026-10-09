# Permanent Place Form — Implementation Plan

> **For agentic workers:** этот план исполняется последовательно после согласования пользователем. Рекомендации writing-plans о subagent-driven-development, отдельных worktrees и коммитах здесь не применяются: пользователь запросил локальную работу без commit/push/deploy. До согласования разрешены только аудит, тесты и макеты.

**Goal:** сделать создание и редактирование постоянного места понятным и надёжным в кабинете владельца и админке, сохранив текущие серверные правила.

**Статус 2026-10-07:** пользователь согласовал реализацию; изменения интерфейса внедрены локально. Приёмка частичная, есть PP-01/02 FAIL и NOT RUN. [Отчёт и реальные скриншоты](/home/ramin/kidsmap/docs/qa/permanent-place-form-implementation-2026-10-07.md). Чекбоксы ниже отражают выполненную работу; открытые пункты не объявлены завершённой приёмкой.

**Architecture:** существующие Django forms, контроллеры, ServerDraft, photo workflow и публикационные редакции остаются источниками истины. Меняются представление, навигация, клиентское восстановление и подключение уже существующих обработчиков. Индикаторы обязательности получают требования из `place_readiness`, а окончательное решение принимает сервер.

**Tech Stack:** Django templates/forms, существующий JavaScript и CSS KidsMap, PostgreSQL на изолированном стенде, Chromium/Playwright.

**Spec:** [текущий аудит и дизайн](../../qa/permanent-place-form-design-2026-10-06.md), [интерактивный макет](../../qa/place-form-design-2026-10-06/prototype.html).

## Ограничения

- Только создание/редактирование постоянного Place в кабинете владельца и админке.
- Не изменять validation, publication/readiness checks, права, модели, migrations, source-version и moderation transitions.
- Place, Activity, OfferingGroup и PricingPlan сохраняют отдельные редакторы, ID и связи. Общий билет остаётся тарифом Place; занятия не обязательны для парка.
- Часы работы Place и расписание групп не объединять. Наследуемая Program остаётся общей программой, а локальные дополнения — локальными.
- Не вводить автосохранение в админке. В кабинете использовать работающий ServerDraft; новые фото требуют явного сохранения.
- RU/AZ/EN; ширины 360/390/768/1440; клавиатура; отсутствие горизонтального переполнения и перекрытых действий/ошибок.
- Сохранить существующие dirty/untracked изменения. Перед реализацией обновить manifest; не восстанавливать файлы целиком из HEAD.
- Без commit/push/deploy и обращений к production. Только `DJANGO_TESTING=1`, изолированные DB/cache/media/email и синтетические данные.

## Предлагаемый интерфейс

Владелец: четыре раздела — «О месте», «Адрес и контакты», «Занятия и цены», «Фото и проверка». Админка: пять разделов — «Основное», «Цена и возраст», «Локация и часы», «Фото», «Проверка»; служебные поля остаются отдельно. Это разделы одной формы, обязательного порядка и Next/Back нет.

На PC кабинет получает боковую навигацию с активным разделом; админка сохраняет свою навигацию по пяти разделам. На телефоне — доступный native select разделов, закреплённые действия и короткое состояние сохранения. Поле, выбранное через сводку ошибок, раскрывается, получает фокус и остаётся видимым над панелями.

Состояние сохранения отдельно от публикационного статуса: «ещё не сохранено», «есть изменения», «сохраняем», «текст и тарифы сохранены», «фото ещё не сохранены», ошибка связи и конфликт версии. В админке «сохранено» появляется только для реально сохранённой карточки; новая форма этого не обещает. Готовность при изменении данных не должна выдавать старое серверное решение за новую проверку.

Макеты содержат пример данных и обозначены как prototype. Сохранение/отправка в них не выполняются. Оболочка сайта и Jazzmin показана условно; её перестройка в scope не входит.

## Файлы и ответственность

| Файлы | Разрешённое изменение |
|---|---|
| `src/catalog/templates/pages/includes/owner_place_continuous.html` | починить атрибут общего тарифного редактора; navigation/action/status/error markup; компактные summaries сущностей |
| `src/catalog/templates/pages/includes/permanent_place_field.html` | видимые маркеры «для отправки», связи с ошибками; не менять `field.required` |
| `src/catalog/templates/pages/permanent_place_form.html` | подключение версии существующих CSS/JS при изменении |
| `src/catalog/templates/pages/owner_listing_type_select.html` | заменить только обещание пяти этапов постоянного места на четыре свободных раздела |
| `src/catalog/services/permanent_place_wizard.py` | уточнённые RU/AZ/EN подписи; новые подписи состояния и навигации. Проверить общего потребителя VolunteerPlaceForm |
| `src/catalog/services/permanent_place_rules.py` | presentation adapter к текущему `evaluate_form_readiness`; сериализация labels/anchors/counts, без новых проверок |
| `src/catalog/forms.py` | только presentation properties/help text OwnerPlaceEditForm/CreateForm; validation и save не менять |
| `static/js/owner_place_continuous.js` | восстановление текущего draft ID после reload, состояния подтверждённого сохранения, ошибки, navigation; подключить существующий photo save к явному действию |
| `static/js/owner_place_offerings.js` | только компактные раскрываемые редакторы Activity/Group/Plan и доступное раскрытие ошибки; JSON schema и сериализация без изменений |
| `static/css/pages/owner_place_continuous.css` | layout, sticky/nav, отступы scroll/focus, mobile; сохранить поля доступными при отключённом JS |
| `src/catalog/domain_admin/place.py` | только PlaceAdmin presentation context/summary; при необходимости вынести текущую сериализацию checklist в общий presentation helper. EventAdmin и validation не трогать |
| `src/catalog/templates/admin/catalog/place/change_form.html`, `form/header.html`, `form/_field.html`, `form/section_basics.html`, `form/section_location.html`, `form/section_media.html`, `form/section_verification.html` | navigation/status/copy/error/preview; не удалять carryover и служебные поля |
| `static/admin/js/kidsmap_place_form.js`, `static/admin/css/pages/kidsmap_place_form.css` | mobile select, достоверное сохранение, preview fallback, клавиатура языковых tabs; существующие hooks сохранения/публикации оставить |
| `static/admin/js/kidsmap_place_media.js` | локализовать относящиеся к форме сообщения; убрать ложное предупреждение, что отсутствие фото блокирует публикацию |
| `locale/{ru,az,en}/LC_MESSAGES/django.po` | новая copy; исправить RU «Удалить» → «Удалить» вместо «Удалил», проверить общих потребителей. Компилированные `.mo` только локально |
| `src/catalog/testcases/test_task33_place_continuous.py`, `permanent_place_wizard.py`, `place_readiness.py`, `test_localized_place_admin.py`, `test_task33_drafts.py` | содержательные регрессии существующих контрактов, без ослабления assertions |

Точные небольшие участки правок определяются по новой исходной SHA-сверке при начале реализации. Остальные файлы и бизнес-сервисы вне scope. Если понадобится менять серверные требования, остановиться и вынести отдельный вопрос, сохранив остальное выполненное.

## Задачи после согласования

### 1. Общие тарифы и правдивые подсказки

- [x] В локальном browser regression воспроизвести: кнопка добавления общего тарифа не создаёт строку; сохранённый тариф Place не отображается. Зафиксировать FAIL до правки.
- [x] Исправить в `owner_place_continuous.html` только ошибочную кавычку/атрибут: `class="pw-pricing" data-tariff-editor data-can-verify="0"`. После клика проверить редактируемый тариф и содержимое `pricing_plans`, затем сохранение и reload.
- [x] Переписать map hint, помощь AZ-name, translation hint, число разделов и фото-предупреждение по текущим правилам, перечисленным в spec. Не удалять координатные/файловые validators.
- [ ] RU «Удалить» проверить на форме места, мероприятия, специалиста, schedule editor и тарифах; исправлять каталог перевода, не копировать ошибку в отдельные templates.
  - Частично: PO и общие потребители по исходникам проверены; полный rendered проход Event/Specialist NOT RUN.
- [x] Проверить отсутствие ложного минимума 1200×1200: server принимает меньшие изображения; рекомендацию обозначить рекомендацией, лимиты брать из действующего image upload config.

### 2. Требования черновика и отправки

- [x] Использовать `evaluate_form_readiness(form, instance)` и текущие requirement `code/field/anchor/label/client_config`. Не вводить второй список правил на клиенте.
- [x] Показывать `required_count` из результата (сейчас 10), отдельные рекомендации и сводку блокирующих проблем. При несохранённых изменениях явно отделять прошлую серверную проверку от текущего ввода; submit проходит прежнюю серверную валидацию.
- [x] `name_az`, `description_az`, taxonomy/address/age и режимы цены/часов пометить «для отправки». Для Баку показывать условный district. Контакты — одно из допустимых средств, а не обязательный первый телефон; учесть public_space и подтверждённое наследование организации.
- [x] Запустить существующие Place readiness/form/publication tests. Пустой draft должен оставаться допустимым, опубликованная legacy-карточка — сохранять существующую compatibility policy.

### 3. Восстановление и состояние сохранения

- [x] Воспроизвести сохранение новой формы `?fresh=1` → HTTP 201 → reload → пустой ввод. Новый browser regression обязан сначала падать.
- [x] Сохранить безопасную ссылку на текущий draft ID/version в namespace текущего аккаунта/формы; после первого успешного save исключить повторное трактование reload как команды «новая форма». Restore загружает именно этот draft, а не произвольный первый target_id=null.
- [x] Не очищать более новый локальный ввод, если завершился более старый запрос. После save повторять сохранение при оставшемся dirty; «сохранено» только после ответа на актуальную версию. Проверить быстрый ввод на задержанном ответе.
- [x] Различать серверное сохранение, browser fallback/offline, pending file, 409 конфликт и отказ доступа. При конфликте не перезаписывать новую версию и не обещать сохранение; не вводить автоматическое слияние.
- [x] Явное сохранение с новыми фото направить в существующий `KidsMapPhotoEditor.save(submitter)` и `owner_photo_create_save/owner_photo_edit_save`. Сохранение текста не обозначать как сохранение фото. После ошибки/повтора проверять отсутствие дублей.
- [x] В админке сохранить ручной submit и существующий beforeunload. Проверить new/dirty/saving/saved/error; не создавать новый autosave или storage для админки.

### 4. Навигация, длинные редакторы, клавиатура

- [x] Реализовать предложенные PC/mobile navigation, активный раздел, видимое состояние и действия; сохранить свободный переход и существующие anchors.
- [x] Раскрытие дополнительных переводов, групп и тарифов должно сокращать заполненную форму, оставляя summary названия/возраста/времени/цены. Скрытые ошибки раскрывать автоматически; не менять значения при раскрытии.
- [x] Сводка ошибок получает фокус; ссылки ведут к конкретному полю, включая details, language pane и вложенный group/plan. Inline errors связываются через `aria-describedby`; label остаётся доступным.
- [x] Языковые tabs админки: ArrowLeft/Right, Home/End, roving tabindex, Enter/Space, выбранный panel и возврат фокуса. Для mobile section select использовать native keyboard behaviour.
- [ ] Проверить Tab/Shift+Tab, Enter/Space, Escape, reduced motion, sticky header/footer и последние поля на 360/390/768/1440. Отдельно открыть taxonomy dropdown, date/price controls и карту.
  - Частично: 24 keyboard/error состояния прошли; Escape каждого dropdown, внешняя карта и все дополнительные controls NOT RUN.

### 5. Предпросмотр и жизненный цикл

- [x] Name/description в preview использовать тот же fallback, что `public_presentation.translated`: выбранный язык → AZ, без записи в пустые RU/EN поля. Для legacy Place сохранить действующий legacy fallback.
- [ ] Использовать существующую серверную нормализацию полного preview там, где она доступна по текущим правам; не давать владельцу staff-only endpoint. Новый preview endpoint не входит в scope.
  - Существующие preview/hooks сохранены; новый owner endpoint не добавлялся. Полный server-normalized owner preview не заявляется.
- [x] Дать явные подписи New/Draft/Pending/Published/Rejected/Changes requested. Для опубликованного Place показывать live и candidate раздельно. Черновик и pending не подменяют live.
- [x] Не обещать публикацию при сохранении. Owner submit остаётся отправкой на модерацию, admin publish работает по существующим правам и переходам.

### 6. Приёмка и сохранность

- [ ] На синтетических данных пройти четыре типа: общественный парк; платная студия без Activity с общим билетом; центр с местным Activity, двумя Group и разными PricingPlan; событийная площадка с schedule/price modes без выдуманного события. Дополнительно филиал подтверждённой организации с inherited contact/program.
  - Четыре типа и подтверждённый филиал пройдены; отдельный price_mode=events отсутствует в owner UI и NOT RUN.
- [ ] Для create и edit: неполный текстовый draft, explicit draft с фото, reload, исправление form errors, повтор сохранения/отправки, moderation approval, публичная карточка на RU/AZ/EN. Проверить blank RU/EN остаются blank в записи, при этом публичный fallback отображается.
  - Текстовые циклы пройдены; photo submit имеет PP-01 FAIL, direct admin publish NOT RUN.
- [ ] Для published edit: live не меняется до approval; после approval apply Group/Plan работает атомарно. Admin draft новых nested tariffs сохраняет текущую границу: вложенные данные требуют уже существующий Place, не обходить её ради UI.
  - Owner live/candidate и атомарное применение Group/Plan проверены; создание nested tariffs из новой admin-формы браузером не завершено.
- [x] Пройти 2 интерфейса × 2 create/edit × 3 языка × 4 ширины = 48 базовых страниц; состояния ошибки/сохранения/фото и клавиатуру проверять отдельными сценариями. Все actions только локальные.
- [x] Запустить targeted команды из spec плюс `test_task33_pricing`, `test_task33_publication`, `test_task33_public_details`, `photo_workflow` и `test_volunteer_dashboard` для общих потребителей. Не объявлять полный suite зелёным без его запуска.
- [x] Сохранить screenshots PC/mobile, машинные результаты, точный log/count/commands и NOT_RUN. Проверить исходный manifest, HEAD и отсутствие чужих затронутых участков.

## Самопроверка плана

Все четыре противоречия уточнены по действующим серверным требованиям; согласованные UI-правки выполнены. 183 targeted tests, 48 базовых страниц, 24 keyboard/error состояния и 24 public страницы прошли. Полная приёмка не пройдена: потеря главного фото при отправке, legacy moderation и ограничения candidate gallery вынесены в отдельные серверные задачи; непроверенные сценарии перечислены в отчёте. Другие планы не запускались, commit/push/deploy не выполнялись.
