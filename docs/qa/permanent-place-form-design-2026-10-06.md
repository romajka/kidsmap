# Постоянное место: перепроверка и дизайн — 2026-10-06

**Режим: AUDIT / DESIGN, ожидается согласование scope. Application-код не изменён.** Проверено создание и редактирование в кабинете владельца и админке; выполнены локальные тесты и браузерная перепроверка. Макеты показывают предложение, а не реализованную форму.

## Срез и безопасность

- LOCAL HEAD: `2da9d33abbc53d1ac71bcb7e15a0170bef6277d5`, ветка `task33-progress`. Проверялся dirty WORKTREE, включая уже сделанные в этой беседе исправления Event.
- Прочитаны AGENTS.md, canonical orchestrator/architecture/source-of-truth/audit contract и `docs/qa/content-entry-audit-2026-10-06.md`. Применены kidsmap-ui-design, frontend-design и writing-plans. Работа выполнена последовательно одним исполнителем; независимого specialist review не заявляем.
- Стенд: `http://localhost:8781`, guarded manual settings, `DJANGO_TESTING=1`, socket PostgreSQL `qa_stage04`; tests используют отдельную `test_qa_stage04`, LocMem cache и тестовые media. Контейнер без внешней сети/DB ports; production credentials и внешние интеграции не используются.
- Использованы только синтетические `demo_owner/demo_moderator` и Place 1 стенда. Создан один новый private ServerDraft для проверки autosave/reload. Существующие Place не сохранялись и не публиковались. Фото-dialog открывался и отменялся.
- Stand 8780 не использовался: исторический процесс не доказывает текущий source. Static prototype на `127.0.0.1:8782` не имеет API/save.
- До работы записан SHA manifest 4415 tracked/nonignored файлов: `.tmp/place-form-design-20261006/before-manifest.json`. Итоговая SHA-сверка: все 4415 исходных файлов сохранились без изменений; новые файлы только в docs. [Результат сверки](place-form-design-2026-10-06/preservation-results.json). Git operations commit/push/deploy не выполнялись.
- Codebase Memory: project ready, root `/home/ramin/kidsmap`; найденные symbols сверены с source. Индекс сообщил partial parse owner template на строке 31; повреждённая разметка проверена непосредственно и в DOM. Граф — навигация, а не доказательство отсутствия кода.

## Что уже исправлено относительно прежнего аудита

| Наблюдение | Текущая проверка |
|---|---|
| Ширина формы места | На 48 GET-страницах нет горизонтального overflow при 360/390/768/1440 в RU/AZ/EN. Старое замечание не воспроизведено; исправление ширины целиком не требуется |
| «Мастер» владельца | Уже одна continuous form с четырьмя разделами и anchors. Mandatory Next/Back нет |
| Сохранение владельца | Уже есть реальный ServerDraft API, autosave текста/тарифов/структурных часов и localStorage fallback. Есть ошибка восстановления нового ввода, описанная ниже |
| Готовность админки | Уже 10 серверных пунктов, корректное `0 из 10` у пустой формы, сводка и ссылки к полям. Не нужно переписывать весь checklist |
| Длинная админская форма | Уже есть five-section nav, accordion, «Свернуть/раскрыть всё», error focus и beforeunload |
| Занятия/группы | Уже существуют nested редакторы, inherited program/local activity, group price, отдельные ID и candidate workflow. Эти границы сохраняем |

Это результаты текущего WORKTREE. Исторический stage13 PASS использован лишь как указатель на реализацию и не заменяет текущую проверку.

## Подтверждённые проблемы

| ID / уровень | Факт и первопричина | Предложение |
|---|---|---|
| PLACE-D01 / P1 | Владелец: «Добавить тариф» не делает ничего; сохранённый общий тариф не виден. В `owner_place_continuous.html:31` незакрыта кавычка class, `data-tariff-editor` стал частью class. `permanent_place_pricing.js:3–4` прекращает работу без hook. DOM hook=false, строк до/после клика=0 | Починить один атрибут, сохранить существующий editor/JSON/validators |
| PLACE-D02 / P1 | Новая форма открывается с `fresh=1`. Autosave вернул HTTP 201; reload показал пустые name/status. Без fresh тот же draft восстанавливается. `owner_place_continuous.js:48–50` skips restore, а success save удаляет local reference | Сохранить current draft identity после success и правильно обработать fresh при первом открытии / reload. Проверить быстрый ввод и stale requests |
| PLACE-D03 / P2 | Owner copy одновременно «точка необязательна» и «обязательно для отправки». Противоречат `ui_copy.optional_map` и `ui_copy.map_hint`. Реальные requirements исключают coordinates/photo | Одно объяснение: точка optional; введённая пара координат должна быть корректной |
| PLACE-D04 / P2 | AZ-name подсказка обещает любое название на одном языке, а publish требует AZ. Admin basics обещает автоматические переводы, verification отрицает их создание | Отделить draft от submission, объяснить display fallback без записи переводов |
| PLACE-D05 / P2 | Type selection обещает пять этапов Place; фактическая owner form имеет четыре раздела; внутренний `build_steps` содержит семь подблоков | Указать «4 раздела · свободное заполнение». Admin имеет пять разделов и служебный блок, не этапы мастера |
| PLACE-D06 / P2 | Пустая новая admin card сразу говорит «Все изменения сохранены». Dirty tracker устанавливает saved при равенстве initialSnapshot, даже если объекта ещё нет | New/idle отдельно от saved; saved только подтверждённое сохранение |
| PLACE-D07 / P2 | Owner обязательные badges скрыты и не инициализируются continuous JS. Admin помечает первый phone обязательным, хотя подходит website/другой контакт или valid inheritance; public_space может без контакта | Marker «для отправки» на основании server presentation, conditional contact group |
| PLACE-D08 / P2 | Owner actions только в конце; mobile navigation `position:static`. Форма create RU360 высотой 8180px, edit RU360 — 16352px. Поля Activity/Group/Plan развёрнуты даже для просмотра | Persistent navigation/actions; компактные entity summaries, раскрытие редактирования/ошибки, сохранение текущих данных |
| PLACE-D09 / P2 | Admin RU preview при заполненном AZ и пустом RU показывает «—». `refreshPreview` берёт только выбранное поле. Публичный `translated()` читает selected → AZ → legacy Place. Owner preview всегда предпочитает AZ и не показывает выбранный язык | Preview с тем же fallback и пометкой языка; не заполнять RU/EN программно |
| PLACE-D10 / P2 | Admin AZ фото-dialog остаётся русским и обещает, что удаление фото нарушит требования публикации. Source `kidsmap_place_media.js:191–196`; браузер подтверждает. Подсказка «минимум1200×1200» не соответствует minimum серверного validator | Локализовать сообщения; optional main photo; 1200px — рекомендация, действующие upload limits не менять |
| PLACE-D11 / P2 | New owner button «Сохранить черновик» вызывает только ServerDraft save; pending photo исключено из payload. Copy browser_saved советует эту кнопку для фото. Это видно в source; browser upload/save отдельно не выполнялся | Подключить имеющийся явный photo save к действию, различать text saved / photos pending |
| PLACE-D12 / P2 | Admin language tab AZ не меняется по ArrowRight; Tab достигает RU. В `bindLanguageGroup` есть только click. Owner error summary даёт английское browser validation сообщение в RU | Полный tab keyboard contract; локализованные ошибки, focus summary/target и `aria-describedby` |
| PLACE-D13 / P3 | RU каталог содержит `msgid "Удалить" → msgstr "Удалил"` (`django.po:1142`). Текст виден в admin main photo | Исправить shared translation и проверить Place/Event/Specialist, расписания и тарифы. Бизнес-операции не менять |

D11 проверен wiring/source, а не полноценным upload сценарием. Не смешивать это с браузерным подтверждением обработки файла. Карта на изолированном стенде недоступна без provider; это ограничение среды, не доказанный новый дефект карты.

## Разбор всех блоков

| Блок | Действующее поведение / предложенная точечная правка |
|---|---|
| Название и переводы | AZ обязателен при отправке. RU/EN optional; пустые поля остаются пустыми. Показать это рядом с языками, сохранить введённые переводы при переключении |
| Описание | Для публикации нужен непустой AZ, тестовый текст отклоняется. 120 символов — quality advice, не minimum. Не превращать рекомендацию в required |
| Категория/подкатегория | Subcategory связана с выбранной Category; dependent picker и server mismatch validation уже есть. У Place и Activity своя taxonomy, «скопировать» остаётся явным действием |
| Адрес и карта | Для publish нужны адрес и город/регион; для Баку district. Metro optional. Pin optional, но partial/nonfinite/out-of-range координаты отклоняются даже в draft. Предлагается один текст и раскрываемые manual coordinates |
| Контакты | Для business хотя бы допустимый телефон/WhatsApp/website либо контакт текущей подтверждённой организации. Public_space может без контакта. Instagram не подменяет publication contact. Не заставлять заполнять phone1 при действующем сайте |
| Часы работы | Regular требует хотя бы один открытый день/интервал. Другие существующие modes имеют свой контракт. Старый text schedule не заменяет structured days. Не смешивать с group times |
| Занятия | Place может без Activity. Shared Program и местное Activity различаются; program master не изменяется этим редактором. Свернуть редактор в summary, раскрывать для правки |
| Группы | Возраст, язык, формат, преподаватели, условия и schedule принадлежат Group. Не переносить их в Place. При ошибке раскрывать конкретную группу |
| Возраст | От + до либо open-ended. При open-ended пустой «от» нормализуется сервером к 0. Для всех возрастов — 0+. У групп свои возрастные диапазоны и проверки |
| Тарифы | Общий вход — PricingPlan Place; занятия — планы групп. Active usable primary plan либо существующий допустимый price_mode; legacy scalar/custom badge не заменяют canonical readiness. Owner free plan доступен после восстановления editor; новые price modes в owner не добавляем |
| Фото | Главное фото и до 10 gallery отдельно. Фото optional для publication, но выбранный файл проходит действующие validators/processing. Текстовый autosave не сохраняет binary-файлы; file reselect после несохранённого reload обязателен |
| Предпросмотр | В админке уже есть normalized full preview и постоянные URL. Предлагается корректный inline language fallback. Не обещать пиксельную идентичность inline mini-card полной detail page |
| Отправка | Owner создаёт candidate на модерацию; saved draft не публикует. Admin uses existing permissions/actions. Кандидат не скрывает live. Показывать реальные ошибки с конкретными links |

## Четыре противоречия — окончательные ответы по текущему серверу

**Точка на карте не обязательна.** `PLACE_READINESS_REQUIREMENTS` фильтрует coordinates и photo. Если координаты введены, формы продолжают проверять пару/диапазоны. Отсутствие pin не снимает требований к адресу/региону; карта без координат не получает реальную геометку.

**Автоперевод не создаётся.** `public_presentation.translated()` отображает выбранное поле, затем AZ (для legacy Place ещё legacy column). Это чтение, а не заполнение RU/EN. Старые model helpers имеют свои legacy fallback; не менять их глобально в этой задаче. Новый preview ориентируется на опубликованное presentation.

**Этапов мастера нет.** Owner: четыре свободных раздела, внутри семь подблоков. Admin: пять основных разделов плюс служебные поля. Пять «этапов» на странице выбора Place — устаревшая copy.

**Черновик и публикация требуют разного.** Private ServerDraft принимает неполные поля, сохраняя schema/type/access/version constraints; сами по себе они не создают публичный Place. Явный Place draft снимает publication-required, но не отменяет validators уже введённых данных. Отдельный materialize API имеет своё условие name+category; его не подключаем обходным способом и не меняем. Owner photo-save уже использует обычный `create_place(...draft_save_only=True)`.

Публикационный checklist сейчас содержит **10 пунктов**:

1. Название AZ.
2. Описание AZ.
3. Категория.
4. Соответствующая подкатегория.
5. Город/регион и район для Баку.
6. Адрес.
7. Возраст от/до или open-ended.
8. Допустимая цена/тариф/существующий price mode.
9. Допустимый контакт с исключением public_space и valid inheritance.
10. Часы работы по существующему mode.

Checklist не заменяет остальные проверки формы, прав, версий и вложенных сущностей. В админке ordinary Save неопубликованной карточки отличается от `_save_draft`; legacy compatibility уже опубликованных карточек сохраняется. Не менять эти серверные исключения для красоты индикатора.

Состояние карточки и сохранение должны быть раздельны:

| Состояние | Copy / действие |
|---|---|
| New | «Новая карточка · ещё не сохранена» |
| Draft | «Черновик» + последнее подтверждённое сохранение / несохранённые изменения |
| Pending | «На модерации»; существующая live версия остаётся видна |
| Published | «Опубликовано»; редактируемый candidate показан отдельно |
| Rejected | «Отклонено» + текущая причина, без обещания публикации |
| Changes requested | «Нужна доработка» + замечания и переход к ним |

## План и макеты

Рекомендуемый scope: исправления D01–D13 и существующей навигации/предпросмотра, без нового wizard, новой модели или нового publication API. [Конкретный план и границы файлов](../superpowers/plans/2026-10-06-permanent-place-form-design.md).

- [Открыть интерактивный макет владельца](http://localhost:8782/docs/qa/place-form-design-2026-10-06/prototype.html?view=owner&lang=ru).
- [Открыть интерактивный макет админки](http://localhost:8782/docs/qa/place-form-design-2026-10-06/prototype.html?view=admin&lang=ru&state=empty).
- [Owner PC](place-form-design-2026-10-06/proposed-owner-pc.png), [Owner mobile / ошибка](place-form-design-2026-10-06/proposed-owner-mobile.png).
- [Admin PC](place-form-design-2026-10-06/proposed-admin-pc.png), [Admin mobile / адрес](place-form-design-2026-10-06/proposed-admin-mobile.png).
- [Activity → Group → PricingPlan на PC](place-form-design-2026-10-06/proposed-offerings-pc.png).
- Исходный [HTML макета](place-form-design-2026-10-06/prototype.html) можно открыть локально; новые сохранения/публикации здесь отключены.

PC owner получает rail, mobile — select разделов, доступные действия и состояние внизу. Admin nav/accordion используется повторно. Inline errors раскрывают нужный section/details/language/group, затем focus. Старые поля/служебные настройки не удаляются. Progressive summaries сокращают высоту без сокращения данных.

## Выполненные проверки

**Текущая application-версия:** 48 GET-страниц = owner/admin × create/edit × RU/AZ/EN × 360/390/768/1440. Все HTTP200; 0 horizontal overflow, 0 pageerror, 0 same-origin HTTP400+. Дополнительно real ServerDraft save/reload, без fresh restore, неработающая direct tariff button, client error jump/focus, admin preview и AZ photo warning, language-tab keyboard. [Машинная матрица](place-form-design-2026-10-06/current-browser-results.json), [результаты flow](place-form-design-2026-10-06/flow-results.json).

**Макет:** 72 browser cases = 2 interfaces × 3 languages × 4 widths × 3 states (empty/edit/error). HTTP200, 0 overflow/pageerror/missing asset. В шести owner/admin × RU/AZ/EN сценариях на390 проверены keyboard error jump, section selection, modal Enter/Escape/focus return, Tab/Shift+Tab footer. [Результаты макета](place-form-design-2026-10-06/prototype-browser-results.json). Это проверки prototype, не приёмка будущей реализации.

**Сервер:** свежий запуск **88 tests, PASS**, exit0:

```bash
.venv/bin/python .tmp/event-admin-fix-20261006/run.py \
  catalog.testcases.test_task33_place_continuous \
  catalog.testcases.test_task33_drafts \
  catalog.testcases.place_readiness \
  catalog.testcases.permanent_place_wizard \
  catalog.testcases.test_localized_place_admin
```

Тесты проверяют current create/edit, public_space без photo/pin/contact, business с website, AZ без RU/EN, typed/incomplete drafts, stale version/access/CSRF, nested data, часы/координаты и admin preview. Это не browser full-flow. Log: `.tmp/place-form-design-20261006/tests.log`; durable summary: [test-results.json](place-form-design-2026-10-06/test-results.json).

System check: no issues. Launcher сообщил о model changes, не отражённых в migrations; миграции не создавались/менялись, это отдельный факт исходного WORKTREE. PASS этих тестов не доказывает отсутствие schema drift.

Текущие screenshots до реализации: [Owner PC](place-form-design-2026-10-06/current-owner-pc.png), [Owner mobile](place-form-design-2026-10-06/current-owner-mobile.png), [Admin PC](place-form-design-2026-10-06/current-admin-pc.png), [Admin mobile](place-form-design-2026-10-06/current-admin-mobile.png), [Owner error mobile](place-form-design-2026-10-06/current-owner-error-mobile.png).

## Не проверено / следующий шаг

До согласования не реализованы UI исправления. Не выполнена будущая E2E-приёмка разных типов Place с photo upload/retry, сохранением через новую кнопку, модерацией и проверкой новой публичной карточки. Ни одна существующая live карточка не изменялась.

Не выполнены полный suite, реальная геолокация/внешний поиск/tiles/Google, физические мобильные устройства, screen reader, Safari/Firefox и production. Current keyboard проверка ограничена указанными действиями; полноценная проверка всех редакторов запланирована после реализации.

Следующий шаг — согласовать предложенный scope/макеты. После согласования выполнить только задачи плана и обновить этот отчёт результатами реальной приёмки.
