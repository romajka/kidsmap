# ORG-QA-01: актуальная база автосохранения организации — Implementation Plan

> Execution: follow this bounded plan sequentially with the applicable debugging, TDD and verification skills. User/project instructions override skill defaults concerning commits and delegation. No commit/push/deploy/production.

**Goal:** после одобрения организации новое редактирование сохраняется на сервере и восстанавливается в независимой browser context; реальные CAS/ACL конфликты остаются отказами.

**Architecture:** исправить выбор рабочего ServerDraft в `_detail_context`, сохранив существующие API и модерацию. Устаревший черновик остаётся отдельной записью; его нельзя автоматически перепривязать к новой базе. Проверка версии в `server_drafts.save` остаётся обязательной. Более новый candidate не перекрывается старым working draft.

**Tech stack:** Django / PostgreSQL, существующие Python tests и native Playwright browser, свежие RU/AZ/EN через `build_isolated_locales.py`.

## Scope и снимок

- Единственный ID: **ORG-QA-01**. Статус: CONFIRMED OPEN, PLAN READY; реализация NOT RUN, требуется одобрение этого документа.
- Checkout `/home/ramin/kidsmap`, branch `task33-progress`, HEAD `e4e05cc213b34e2d771ecb854901bfd016d1db51`; dirty snapshot в `entry.json`, active_run NONE.
- Recheck: [REPORT.md](REPORT.md), native create → autosave → submit → moderator approve → fresh edit → HTTP409 → независимая сессия теряет новый ввод. Live content_version=2, привязанный draft.source_version=1.
- Другие ORG/NETWORK findings, общие locale ошибки и module01 вне scope. Миграции, API/CAS, ACL, публикационный контракт и существующие assertions не меняются.

## Точные файлы будущей реализации

| Файл | Изменение |
| --- | --- |
| `src/catalog/controllers/organization_workspace.py` | Только `_detail_context`: выбирать draft этого actor/organization на текущих `source_version` и `SCHEMA_VERSION`; обеспечить приоритет более нового candidate перед старым draft при заполнении полей. |
| `src/catalog/testcases/test_org_qa01_autosave_base.py` | Новый небольшой regression набор для approve → fresh autosave, восстановления, подлинного конфликта и границ выбора draft. |
| `docs/qa/org-qa01-fix-2026-10-12-r1/*` | Новый уникальный отчёт, собственный runtime/profile, целевые команды, browser scripts/results/PNG manifest и handoff; если имя занято, следующий rN. |
| `docs/qa/continuation-and-repair-prompts-2026-10-11.md` | Только текущая строка статуса ORG-QA-01 со ссылкой на evidence. Исторические отчёты/88 prompt blocks сохранить. |

`organization_workspace.html`, `organization_workspace.js`, `server_drafts.py` и `publication.py` — источники проверки, **без изменения**. Новый текст интерфейса не нужен; PO/MO исходники не меняются. Для проверки собрать fresh изолированные MO в новом profile. Если понадобится менять приложение за указанными границами — отдельное согласование расширения.

## 1. Зафиксировать RED до patch

Создать только новый regression файл; использовать существующие TestCase/Client/organization/publication fixtures, изолированную PostgreSQL test DB. Не изменять существующие assertions.

1. Владелец создаёт рабочий draft через API на базе1, отправляет candidate через форму; модератор одобряет через актуальный review service (unit contract), organization становится базой2. GET формы не должен получать obsolete UUID/base1; свежий autosave через параметры формы должен создать новый draft (HTTP201), последующий update — HTTP200. Новый Client владельца получает сохранённое значение. Старый draft остаётся неизменным; autosave не меняет live/published данные.
2. Существующий подходящий draft на актуальной базе используется; более поздняя несовместимая запись и запись другого actor не вытесняют его. Добавить ветку несовместимой schema; actor/target ограничения не снимаются.
3. Отправленный candidate новее рабочего draft: при GET показывать candidate; его payload/version не менять. Свежий последующий working draft может показывать более новые пользовательские правки, сохраняя submitted candidate отдельно.
4. Два клиента редактируют один актуальный draft с одинаковым expected_version: первый сохраняется, второй получает409 с submitted_fields; новое значение победителя не затирается. Устаревший UUID/base1 также продолжает получать409.
5. Посторонний actor не получает и не обновляет private draft/organization; существующее поведение 403/404 сохранить.

Команда RED/GREEN:

```text
.venv/bin/python docs/qa/<новый-fix-run>/runtime.py test catalog.testcases.test_org_qa01_autosave_base
```

RED должен показывать именно привязку устаревшего draft/выбор полей, не environment/discovery failure. Сохранить точные count/exit/result.

## 2. Минимальный patch

В запрос выбора добавить `source_version=org.content_version` и `schema_version=SCHEMA_VERSION` **до** `.order_by('-saved_at').first()`. Нет подходящего draft → `server_draft=None`; существующий template уже выводит пустой draft_id / expected_version=0, API создаёт новый draft на текущей базе.

Сохранить существующий приоритет candidate. При активном revision (`draft/pending/rejected`, как в текущем controller) накладывать draft.fields лишь когда рабочий draft не старше `revision.updated_at`; более новый candidate остаётся видимым. `current=1` продолжает запрещать overlay. Старые private rows/sessionStorage не удалять, версии не повышать принудительно.

## 3. GREEN и affected consumers — один точечный прогон

Помимо нового regression набора:

```text
.venv/bin/python docs/qa/<новый-fix-run>/runtime.py test catalog.testcases.test_task33_organization_workspace catalog.testcases.test_task33_drafts catalog.testcases.test_organization_editor_errors
```

Дополнительно конкретные tests `catalog.testcases.test_task33_publication.PublicationTests.test_schema_and_source_conflicts_do_not_write` и `catalog.testcases.test_task33_publication.PublicationTests.test_approval_changes_only_patch_and_uses_new_version` (имя класса сверено по текущему source). Повторять только при patch/failure. Полный module02 ACCEPT-02 после завершения задач модуля, полный проект — в конце очереди.

## 4. Native browser acceptance этого ID

Собственный новый изолированный profile, DJANGO_TESTING=1, уникальные DB/cache/media/private-media/email/session cookie/browser session; fresh locale manifest до django.setup, единственный LOCALE_PATHS. Не копировать .env и не присваивать active_run. Исходники работающего процесса должны совпасть с текущим WORKTREE.

- RU/AZ/EN ×390/1440: native create → autosave → submit → admin approve → edit → server autosave → reload и независимая browser context. Это целевая проверка поведения, не full responsive module acceptance.
- Для каждой ветки сохранение видимого ввода, статус autosave на выбранном языке, фокус/клавиатура в затронутой форме. Реальный stale save/conflict в двух контекстах:409 сохраняет ввод, не повреждает победителя; последующее восстановление не маскировать same-tab sessionStorage.
- Native submit/review и публичный reload: правки не становятся live до одобрения; readback только READ ONLY с statement/lock timeout. ORM не заменяет проверяемые переходы.
- Screenshots success/conflict/fresh-context, console/pageerror/network. Блокированные external fonts записать как environment limitation, внешние интеграции NOT RUN. Не считать HTTP200/source inspection доказательством UI.

## 5. Отчёт и закрытие

В новом REPORT: snapshot/source match, RED/GREEN exact commands/exits/counts, cause/diff, browser matrix/results/PNG hashes, live/draft/candidate readback, baseline/environment/harness ограничения, сохранность старых стендов/WORKTREE/active_run, NOT RUN.

Закрыть только ORG-QA-01 при выполненном acceptance. Module02 остаётся IN PROGRESS, ACCEPT-02 NOT RUN. После согласованного исправления рекомендовать следующий отдельный PLAN модуля02; автоматически его не запускать.
