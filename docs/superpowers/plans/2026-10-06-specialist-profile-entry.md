# Specialist Profile Entry Implementation Plan

> **For agentic workers:** Implement sequentially, task by task, after the user approves the selected scope. Use the existing TDD and verification skills. No commit/push/deploy; do not start additional agents or unrelated stages.

**Статус 2026-10-07:** A–D внедрены локально после разрешения пользователя. Свежая приёмка, скриншоты и NOT RUN: [отчёт](/home/ramin/kidsmap/docs/qa/specialist-profile-implementation-2026-10-07.md). Без commit/push/deploy. Checklist ниже оставлен как исходный план; точные выполненные проверки перечислены в отчёте.

**Goal:** Сделать предложение и заполнение специалиста возобновляемыми и понятными; устранить потери полей и локальных контактов, сохранив все границы личности, сотрудничества и документов.

**Architecture:** UI использует существующие формы и specialist_domain/specialist_documents. Места редактируются как набор SpecialistPracticeLocation, отдельно от общего профиля. Для автора нового предложения предлагается отдельная приватная working copy до отправки; она не даёт прав на Specialist.

**Tech Stack:** Текущие Django templates/forms/services, PostgreSQL, plain JS/CSS и locale RU/AZ/EN. Без нового UI framework, внешнего API, фонового автосохранения или общей переделки публикации.

**Spec:** [проверка и дизайн](/home/ramin/kidsmap/docs/qa/specialist-profile-design-2026-10-06.md). Макет: `/home/ramin/kidsmap/docs/qa/specialist-design-2026-10-06/prototype.html`.

## Global Constraints

- Только локальная изолированная среда, DJANGO_TESTING=1, отдельные DB/cache/media/private-media, network guards и синтетические аккаунты/файлы.
- Без commit/push/deploy. Перед работой перечитать AGENTS.md, active_run и git status; сохранить существующий dirty WORKTREE. Приложение до согласования не менять.
- RU/AZ/EN; ширины360/390/768/1440; Tab/ShiftTab/Space/Enter/Escape; фокус и ссылки на ошибки.
- Сохранить дедупликацию29 направлений, существующий поиск кабинета и кнопку первого draft-шага. Кабинет —5 этапов; admin —12 групп. Не удалять поля ради макета.
- Автор created_by не получает право редактировать Specialist/private documents. verified_person_user+person_verified_at, отдельные reviewer permissions и consent остаются источниками прав.
- Organization employment и practice_locations не объединять; никаких прямых organization_id/person assignments в обход доменных сервисов.
- Не менять требования к публикации, очной практике и документам ради UI. Admin и owner rules не унифицировать в этом scope.
- Никакого обещания server autosave. Рабочая копия браузера — отдельное восстановление, явное сохранение — серверный ответ.
- Макет демонстрационный: переключает разделы по одному. Реальная admin-форма сохраняет все12 групп в одном form, с anchor navigation и доступным фокусом; без переделки в обязательный wizard.
- У опубликованного Specialist owner-save меняет canonical status на draft/pending. Показать последствия, не внедрять candidate/live механизм.

## Состав согласования

| Блок | Результат | Изменение сервера |
|---|---|---|
| A. Admin и навигация | Поля не пропадают в AZ/EN;12 секций, mobile jump, error links | Исправление обработки unchecked is_active, без изменения требования active location |
| B. Места приёма | Несколько карточек, independent price/phone, история | Устранение автоматической перезаписи из общего профиля; атомарная запись разрешённого набора |
| C. Черновик и восстановление | Account-scoped local recovery; возобновляемое предложение | **Новая приватная working copy предложения**, одна локальная миграция; без новых прав на Specialist |
| D. Поля и понятные состояния | Образование/опыт, NULL vs0, publication hints, private docs labels | Дополнительные необязательные public text поля в форме;0-price rendering; ACL без расширения |

Рекомендуется согласовать A–D вместе, включая отдельный draft в C. Если C исключён, нельзя обещать автору продолжение сохранённого канонического proposal draft: существующий авторский GET editor возвращает404, и это сохранённая граница безопасности.

## Task 1. Стабильные admin-разделы и точное очное правило

**Modify:** `src/catalog/domain_admin/specialist.py`, `src/catalog/templates/admin/catalog/specialist/change_form.html`.

**Tests:** отдельный `src/catalog/testcases/test_specialist_entry_admin.py`.

- [ ] Зафиксировать failing tests: inventory всех editable/readonly полей в admin add/change для RU/AZ/EN; имя, стаж, направления не пропадают. Проверять исходный configured набор, не зашить урезанный перечень макета.
- [ ] Добавить untranslated ключи/metadata групп, сохранив все12 fieldsets и локализованные заголовки. Шаблон не ищет русские подстроки в display names.
- [ ] Зафиксировать failing inline cases: unchecked active, удалённая строка, пустая строка, wrong region, только история, валидное место, online без места.
- [ ] Определять active location по валидированным inline данным и DELETE/is_active; повторно использовать existing model clean и требование region. Убрать false-positive отсутствующей галочки, не вводить новые mandatory поля.
- [ ] Проверить, что обычный change_specialist не получает document inline/count/download, dedicated reviewer сохраняет предусмотренный доступ.
- [ ] Пройти targeted tests. Результат этапа: весь field inventory на всех языках и прежнее требование активной очной практики.

## Task 2. Навигация, ошибки и видимое сохранение

**Modify:** `static/admin/js/specialist_admin.js`, `static/admin/css/pages/specialist_form.css`, admin template; `static/js/specialists.js`, `static/css/pages/specialists.css`, `src/catalog/templates/pages/owner_specialist_create.html`.

- [ ] PC оставить aside12 anchors, mobile добавить доступный select «Раздел формы» и текущий раздел. Не связывать selection/sessionStorage с текстом заголовка; ключ при необходимости привязан к actor/entity.
- [ ] Разделы в admin не удалять и не держать только в JS hidden staging container: progressive enhancement должен оставлять поля доступными и при failed script.
- [ ] Сводка ошибок: раздел, номер строки места, конкретный field link. Переход раскрывает нужную группу, прокручивает и ставит фокус в ошибочный control; aria-invalid/aria-describedby, focus-visible.
- [ ] Нижняя панель действий с reserved space/safe-area; фокусируемое поле не оказывается под панелью. В admin сохраняется обычный save со status из группы модерации; новая owner-submit политика не добавляется.
- [ ] UI state machine: pristine server state → dirty → saving → saved/error/conflict. Saving не считается saved; timestamp обновляется только после успешного response. На ошибке все введённые значения остаются.
- [ ] Для опубликованного профиля перед сохранением/отправкой видимое объяснение действующего снятия с public до проверки. Для нового/draft/pending/rejected состояния — точный server status и rejection reason, без «уже обработано» на новой анкете.
- [ ] Пройти keyboard и mobile smoke; не делать owner-этапы новыми admin требованиями.

## Task 3. Несколько мест и независимые филиальные данные

**Modify:** `src/catalog/forms.py` (тонкая интеграция), новый узкий `src/catalog/forms_specialist_locations.py`, `src/catalog/services/owner_specialist_use_cases.py`, `src/catalog/controllers/specialist_workspace.py`, owner/admin templates, specialist JS/CSS.

**Tests:** новый `src/catalog/testcases/test_specialist_entry_locations.py`.

- [ ] До нового поиска проверить контракт видимости выбранных Place и существующие permission helpers. Зафиксировать публичное место, доступное собственное, чужое private/deleted, уже связанную скрытую карточку. Не открыть новую видимость через autocomplete. Если существующая политика не определена, вынести этот пункт на отдельное решение; не угадывать права.
- [ ] Failing regression: сохранить bio/общую цену/phone при двух местах с35/60AZN и разными телефонами; локальные значения и row IDs должны сохраниться.
- [ ] Bound formset существующих practice_locations: scope specialist, нельзя подставить row ID другого человека. На mobile карточки вместо широкой таблицы; Add создаёт новую строку, корректно обновляет management fields и фокусирует адрес.
- [ ] У каждой строки: Place либо собственный адрес, region, optional district/metro/coordinates/schedule, price_per_session, phone, is_primary, is_active. Пустая строка игнорируется. Формат/история управляются явно.
- [ ] Сервис сохраняет профиль и валидированный набор атомарно, с existing person authority и expected_updated_at. Не копировать profile.price_from/phone в loc на обычном save. Новый ряд не наследует значения молча.
- [ ] Preserve current history semantics: выключение/смена адреса не стирает прошлую практику; online отключает активные места. При возврате показать историю для явного выбора, не включать все автоматически.
- [ ] Версия родительского профиля должна учитывать изменения мест через поддерживаемые entry points, чтобы stale owner form не затёрла актуальные локальные значения. Admin конкурентный сценарий проверить отдельно; не обходить existing updated_at или consent epochs.
- [ ] Existing contact/price submit requirements остаются общими; заполненный local phone не заменяет обязательный general phone/WhatsApp. Хотя бы одно активное очное место остаётся обязательным.
- [ ] Пройти0/NULL/несколько мест, invalid input, historical rows, tampered IDs и owner-versus-other roles.

## Task 4. Приватная рабочая копия предложения

**Create (предложено; только после согласования C):** `src/catalog/models/specialist_proposal_draft.py`, `src/catalog/services/specialist_proposal_drafts.py`, `src/catalog/testcases/test_specialist_proposal_drafts.py`, одна новая миграция с номером после актуальной migration graph.

**Modify:** model export, controller/urls и workspace index/template для продолжения предложения. Не переписывать generic publication/server_drafts contract.

- [ ] Failing tests: first-step empty draft, partial invalid-for-submit draft, exit/login/reload, other actor read/write404, author cannot access Specialist editor/documents, double Send and stale version.
- [ ] Рабочая копия: owner actor, payload только allowlisted public proposal fields, version, timestamps, optional private temporary validated photo, submitted_specialist reference. Никаких документов личности, claim authority или employment consent.
- [ ] Draft validation допускает те же неполные поля, что current draft form, с текущей проверкой типов/ссылок/фото. Publish/submit validation остаётся existing OwnerSpecialistForm submit contract.
- [ ] «Сохранить черновик» с первого и остальных шагов явно сохраняет working copy; redirect на её resume. Workspace показывает имя/статус и «Продолжить предложение» только автору до отправки.
- [ ] Temporary photo ownership приватно; original/saved photo reload показывается только автору. Не использовать guarded document route для другого типа файла. Оставить2MB validation, private storage и bounded replacement; не создавать внешнюю storage/cleanup automation.
- [ ] Send под actor/draft locks проверяет version и формирует Specialist ровно один раз с created_by; verified_person_user/owner/verification anchors не присваиваются. Повтор после успеха возвращает уже созданное предложение. Рабочая копия становится readonly; profile ACL остаётся прежней.
- [ ] Старые канонические draft proposals не конвертировать в author-owned profile. Показать их текущий статус/информацию; claim только по отдельному заявлению самого человека.
- [ ] Применить новую миграцию только на isolated test DB; проверить fresh DB и существующие legacy proposals. Production migration/deploy не выполнять.

## Task 5. Безопасное восстановление ввода

**Modify:** owner template/JS и workspace controller context; новый маленький JS module допустим для recovery, без library dependencies.

- [ ] Failing browser checks из текущего отчёта: existing name refresh, cross-account new draft leakage, server updated_at conflict.
- [ ] Ключ включает actor ID, new draft/profile ID, schema version и base revision. Actor из session context, не из произвольного query parameter. Allowlist полей, одинаковая форма через5 шагов и места.
- [ ] Не восстанавливать общий legacy `..._new` без actor provenance. Не записывать файлы, ID documents, file URLs, CSRF/permission/claim/document tokens. Не копировать текст одного аккаунта в другой.
- [ ] Восстановление — явный выбор с отличиями от актуальной server state. При base-version conflict не подставлять stale token; показать сравнение/обновление, сохранив локальный текст.
- [ ] После успешного явного save очистить соответствующую copy. После409/validation/network error сохранить unsaved текст; сообщения различают local recovery и сохранение в БД.
- [ ] Storage unavailable/quota/private browsing: форма сохраняется обычным серверным действием, UI не обещает локальную копию, которой нет.
- [ ] Проверить несколько вкладок/двух аккаунтов и новый working draft; не выдавать local recovery за server autosave.

## Task 6. Публичные сведения, точные требования и приватность

**Modify:** OwnerSpecialistForm optional fields, owner/admin/workspace templates, `src/catalog/specialist_forms.py` scoped labels, `src/catalog/templates/catalog/specialist_detail.html`, locale strings AZ/EN (RU через source labels).

- [ ] Добавить необязательные name_alt / education_az/ru/en / experience_info_az/ru/en в существующую public data форму. Стаж числом остаётся отдельным, необязательным полем; input min0 и подсказкаNULL≠0.
- [ ] Сохранить текущий grouped directions search. Добавить явный label/описание поиску, именованные aria-label remove buttons, live result/selected count без изменения кодов или дублирования направлений. В admin применить пригодный для mobile control над тем же M2M set.
- [ ] Отделить языки консультации от языков bio/образования. Не генерировать отсутствующие переводы, не сохранять отображаемый fallback как введённый перевод.
- [ ] Readiness/ошибки derive из реально действующего form action. Owner: name/format/direction/bio/contact/language + conditional offline location. Admin: его текущие правила. Recommendation photo/experience/price/certificate не блокирует отправку.
- [ ] Public rendering price uses None/0 distinctions for general and per-location values.0AZN не исчезает; empty price не превращается в0. Пустой стаж не показывается как0; existing0-лет renderer сохраняется.
- [ ] Copy разграничивает author/person/legacy owner/location/employment. Employment `role` подписывается как должность/вид сотрудничества; роли permissions не переименовывать глобальным переводом «Роль».
- [ ] Documents UI person-only, identity always private; reviewer видит только разрешённую проверку. Автор предложения и обычный admin не получают file metadata/count или consent control. Админский reviewer не ставит public checkbox от имени человека.
- [ ] Certificate consent/status/person verification представлены отдельно. Upload/review/choice/download используют действующие specialist_documents/claim workflow; не подставлять file.url. Проверить, что admin inline путь не обходит существующую token/epoch актуальность; если подтвердится отдельный backend bypass, сначала описать и согласовать его узкий scope.
- [ ] Invitations показывают две стороны, сроки, status, версии; не auto-confirm, не auto-add location. Отклонение/отмена сохраняет историю.

## Task 7. Приёмка согласованной реализации

**Local evidence:** новый acceptance report и screenshots внутри specialist-design folder; отдельный fixture namespace/marker на каждый flow. Старые audit/screenshots не выдавать за приёмку нового кода.

- [ ] Сервер: штатные8 suites из отчёта + новые регрессии выше. Если missing EDU fixture повторяется, исправлять только isolated setup, не assertions. Сохранить stdout/exit/count. Сверить actual migration state отдельно от baseline warning.
- [ ] Proposal: пустой первый шаг → save working draft → refresh → exit/login → resume → validation errors → submit → repeat submit. Убедиться в одном Specialist и отсутствии author profile/document прав.
- [ ] Verified person: online/offline/both; три места с разными ценами/телефонами; save draft/refresh; change general contact; deactivate/primary/history; null and0experience/price; owner version conflict.
- [ ] Moderation: submit pending, approve/reject with reason, edit published with visible warning, public card status and all local prices/contacts. Admin requirements не стали owner rules.
- [ ] Identity: proposal author / unrelated user / verified person / ordinary editor / dedicated claim reviewer; request/approve/reject/stale claim; нет inferred ownership из одинакового имени или файла.
- [ ] Documents: identity/diploma/certificate; upload pending; consent true/false; approve/reject; revoke; inactive person/unpublished profile; anonymous, author, organisation owner/grantee, ordinary admin, dedicated document reviewer; download headers/cache and storage route protections.
- [ ] Employment: organisation invitation, обе стороны по отдельности, repeat/stale version, changed org ownership, cancel/history, no file access or location assignment.
- [ ] Browser grid RU/AZ/EN ×360/390/768/1440: proposal/person/admin add/change, locations, docs/invites, errors/review. Exact field inventory AZ/EN, visible focus, keyboard navigation, native controls and file errors. Общий document width≤viewport; tables/cards не прячут обязательные controls.
- [ ] Capture before/after PC/mobile и machine-readable matrix. Отдельно перечислить real devices/screen reader/external storage/HEIC/full-suite, если не выполнены.
- [ ] Hash compare стартового манифеста: существующие чужие файлы не изменены, кроме явно согласованных application edits. Git HEAD/branch не менялись; без commit/push/deploy.

## Definition of done

Только выбранный пользователем A–D scope реализован и свежие проверки проходят; нет расширения author/document/employment прав и потери локальных данных; состояние сохранения соответствует реальному ответу сервера. Нереализованные пункты отмечены отдельно. Текущий документ и интерактивный макет сами по себе implementation acceptance не являются.
