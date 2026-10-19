# SITE-QA-08: responsive общих настроек — Implementation Plan

> **For agentic workers:** выполнять inline, последовательно по чекбоксам; сохранять исходный dirty WORKTREE. Канонические ограничения проекта имеют приоритет над общими примерами skill. Применение только после одобрения этого конкретного плана.

**Goal:** заполненные общие формы настроек помещаются в viewport, а пользователь с правом изменения может сохранить их на телефоне.

**Architecture:** восстановить Bootstrap-колонку общего template root для всех его действующих потребителей. Подключить отдельный CSS только к этому шаблону и ограничить правила новым маркером `km-settings-form-page`; размер поля, перенос пути и file/Select2 layout исправляются без маскирования overflow. Mobile actions восстанавливаются только при существующем Django `has_change_permission`.

**Tech Stack:** действующие Django6.0.2 / Jazzmin / Bootstrap / vanilla CSS / Chromium Playwright CLI. Новых библиотек нет.

**Spec:** [SITE-QA-08](../module10-2026-10-10-r1/findings/SITE-QA-08.md), [fresh report](REPORT.md), [candidate-manifest](candidate-manifest.json), [exact proposed diff](proposed.diff). Последний diff и его SHA — точный предлагаемый scope, кандидат лежит только внутри этого QA-пакета.

## Global Constraints

- LOCAL HEAD `852938d96764ae315b92859e3651e5ea62054a36`, branch `codex/module09-transfer-2026-10-16-r1`; dirty WORKTREE является исходной точкой. Не применять diff от чистого HEAD поверх чужих изменений.
- Не commit/push/deploy/production, не reset/clean/stash/branch switch, не менять active_run NONE, индекс, .cbmignore, shared MO или старые пакеты/стенды.
- DJANGO_TESTING=1; очистить inherited env до django.setup. Собственные normal/test DB, cache, media/private-media, locmem email; внешние интеграции выключены. Текущие AZ/RU/EN PO собирать только в собственные locales.
- Backend, модели, миграции, права, JS, PO, общая shell CSS и Place/Event templates не меняются. SITE20 readonly desktop Save, SITE11 copy и другие findings сохраняются открытыми. Полное принятие модуля10 пока не выполнено.
- Не скрывать overflow через overflow-x:hidden, не уменьшать шрифты, не подменять native input/POST, не ослаблять assertions. После применения нужен actual-source GREEN без DOM/CSS/transport injection.

## Task 1: применить точный двухфайловый кандидат и проверить

**Files:**

- Modify: `src/catalog/templates/admin/catalog/shared_settings_change_form.html:7` и root на строке15 исходного файла.
- Create: `static/admin/css/pages/kidsmap_settings_forms.css`.
- Test/evidence: отдельный новый `docs/qa/site-qa08-fix-<дата>-<уникальный-run>/`; PLAN-пакет остаётся неизменным после sealing. Никаких других application/test-source файлов этот scope не разрешает.

**Interfaces:** template получает стандартный Django `has_change_permission`; выдаёт существующую форму, её прежние поля, revision token, `enctype`, имена `_continue`/`_save` и native submit. CSS потребляется только через добавленный template link и новые классы. Все9 активных потребителей подтверждены runtime registry в evidence/static-runtime.json: branding/about/contacts/footer/empty-state/visibility/analytics/gallery/catalog-content. Неактивные proxy packages не активировать.

- [ ] **Step 1: зафиксировать свежий entry и изолированный actual-source RED.**

Пересчитать1032 исходных SHA и проверить совпадение с source-final.json этого пакета, current template SHA и отсутствие нового CSS в приложении. При drift пересмотреть только затронутые выводы, не применять старый diff вслепую. Проверить refs/index, manifests старых пакетов, active_run и идентичность чужих контейнеров. Создать отдельный новый runtime; PLAN33570/его БД/профиль оставить нетронутыми. Точные безопасные setup/runtime/seed образцы сохранены в этом пакете; новые имена/порт выбрать и проверить заново.

Скопировать подготовленный browser-acceptance.js в новый пакет, заменить только own base URL/output/session; сохранить исходник и diff harness. Это **подготовленный, ещё не запущенный** actual-source сценарий, без addStyleTag/classList.add. На unchanged source он должен подтвердить overflow/overlap/недоступные mobile actions. Native GET измеряет реальные document/field/card/action rects, язык, HTTP и отсутствие fixture writes. Использовать те же assertions до/после, дождаться load/инициализации sidebar. Провести9 форм ×AZ/RU/EN ×360/390/768/1024/1280/1440. Для readonly catalogue дополнительно18 случаев: на mobile кнопки сохраняют исходное скрытое состояние, поля readonly, данные не меняются.

- [ ] **Step 2: применить только exact proposed.diff.**

Перед применением проверить SHA из candidate-manifest.json и `git apply --check <абсолютный proposed.diff>`. Следующие две строки описывают изменение шаблона; полный точный CSS находится в candidate/static/admin/css/pages/kidsmap_settings_forms.css и proposed.diff:

```django
<link rel="stylesheet" href="{% static 'admin/css/pages/kidsmap_settings_forms.css' %}">
<div id="content-main" class="km-place-form-page km-settings-form-page col-12{% if has_change_permission %} km-settings-form-page--editable{% endif %}">
```

Link следует непосредственно после shell stylesheet; root заменяется на месте, остальные байты исходника сохраняются. Кандидат нового CSS содержит: min-width0 для sections/fieldset; minmax(0,1fr) для внутренних grid; wrapping file/URL text; ограничение file input; file-row override, отделяющий clear-checkbox от boolean layout; Select2 width/min-width; shrinking/caps для boolean help text, вертикальный boolean row до760px; editable-only mobile actions до760px. Применять весь сохранённый diff, а не пересоздавать приблизительную версию по описанию. Затем проверить SHA обоих файлов, отсутствие прочих source changes и `git diff --check`. Перезапустить только собственный source-loaded сервер, сохранив новый fixture/profile.

- [ ] **Step 3: actual-source GREEN и функциональные состояния.**

Повторить неизменённый actual-source acceptance. Во всех9×3×6 случаях document.scrollWidth≤viewport, видимые inputs/file/select2 внутри viewport, карточки внутри main и без пересечения actions; доступно ровно две кнопки у editable. Проверить нативный label click, Tab/Shift+Tab, видимый focus, раскрытие Select2 и Escape на390/1440, включая длинный option/имя файла. Провести native mobile `_continue` и `_save` с save→reload: branding с длинным действительным filename/выбранным PNG, footer/email, gallery image/add, catalogue nested Unicode JSON; AZ/RU/EN360/390. Сверить точные сохранённые значения, ожидаемый LogEntry и публичные локальные соответствующие значения там, где имеется public consumer. Если другая известная ошибка блокирует public проверку — оставить NOT RUN/отдельный finding, не расширять patch.

Negative cases: malformed JSON в каждом из3 полей, неверный email, невалидный файл; native POST возвращает реальную bound form/field errors, введённые значения сохранены, backend/log/media неизменны; затем native valid retry. Проверить длинный путь в существующем clearable file widget, new file input и Select2 dropdown/error. После check восстановить synthetic fixture только native save. Viewer: GET200/readonly/no write, запрещённый local POST403; denied GET403. Не считать UI скрытие ACL.

Запустить105 существующих backend regression methods по точным labels:

```text
catalog.testcases.test_site_qa19_catalog_content
catalog.testcases.public.TestCatalogContentSettingsWiring
catalog.testcases.test_site_qa06_media_validation
catalog.testcases.test_site_qa01_media_permissions
catalog.testcases.test_site_qa15_settings_concurrency
catalog.testcases.admin.TestSiteGalleryImageAdminMedia
catalog.testcases.admin.TestAdminSidebarStructure
catalog.testcases.test_public_section_switches
```

Команда через собственный runtime: `docker exec <new-owned-app> python <new-owned-runtime.py> test <эти8labels>`; свежая отдельная test DB/cache/media с проверкой env/source/locales до импорта Django. В105 тестах не менять assertions. Проверить retained SITE01/06 media ACL/validation, SITE15 stale409/revision и SITE19 labels. Place/Event: scoped stylesheet не подключён и маркер отсутствует, их controls/layout до/после не меняются; shared root потребители все перечислены выше. Отдельно зафиксировать native network/static200 для нового CSS и отсутствие неожиданных local4xx/pageerrors; blocked external fonts явно классифицировать.

- [ ] **Step 4: evidence и решение по статусу.**

Сохранить snapshot, точные команды/exit/counts, исходный RED, actual-source GREEN, PNG, source/diff и artifact manifests. Повторить preservation33prior-packages плюс этот sealed PLAN. Guide/MASTER дополнить append-only после успешных проверок. Только при полном выполнении acceptance закрыть SITE08 LOCAL; известные SITE20/SITE11 и независимые findings не закрывать. Без commit/push/deploy. Любая потребность изменить третий application file или иной контракт означает новый согласованный scope.

## Self-review и риски

Все части исходного mobile bounds требования сопоставлены с file/text/fieldset/Select2 и native long/error controls выше. Утрата Bootstrap column у остальных shared consumers совпадает по механизму с уже закрытым SITE21; col-12 для каталога сохраняется. Shared CSS на5000+ строк содержит специальные Place/Event и boolean rules: отдельный stylesheet/marker исключает глобальное переопределение. `:has()` уже используется действующим shell; новых browser floors план не вводит.

Восстановление mobile actions сознательно ограничено стандартным has_change_permission; это не repairSITE20 и не изменение ACL. Данные и права требуют отдельного backend acceptance после применения. DOM-прототип, его откат и template compile не являются applied-source GREEN. Первый неполный прототип и диагностические результаты сохранены, проверки не ослаблялись. Выполнение будущего исправления — inline; недоступные superpowers workflow skills или независимые subagents не заявляются.

**Approval gate:** конкретно эти два файла и сохранённый proposed.diff. Основание — AGENTS.md: «Future implementation requires a concrete plan and user approval for its scope». Текущее «дальше» разрешает этот recheck/PLAN; прошлое разрешение SITE21 не распространяется на новый patch.
