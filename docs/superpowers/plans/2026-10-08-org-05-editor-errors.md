# ORG-05 Organization Editor Errors Implementation Plan

> **For agentic workers:** Выполнять последовательно в текущем чате; без subagents и commit/push/deploy. Пользователь поручил следующий пункт после ORG-04 сообщением «дальше»; scope — только готовый prompt ORG-05. Статус: IMPLEMENTED LOCAL — ORG-05 завершён; отчёт docs/qa/org-05-fix-2026-10-08.md. Отдельного изменения API/lifecycle здесь нет.

**Goal:** Показывать все ошибки отклонённого POST редактора, сохранять именно отправленный ввод, давать фокус и переход к ошибке.

**Architecture:** Bound candidate_form остаётся источником полей и ошибок. Шаблон выводит summary/field/hidden/nonfield errors с существующими ограничениями; маленькая добавка editor JS управляет focus и сохраняет bound input вместо подстановки старого sessionStorage. Автосохранение, CAS и публикация сохраняют существующий механизм.

**Tech Stack:** Существующие Django forms/templates, native links/focus, текущий JS и CSS, PostgreSQL QA, jsdom и Chromium CLI.

**Spec:** [ORG-05 prompt](../../qa/organization-deep-audit-2026-10-08/prompts/org-05.md).

## Global Constraints

- Только DJANGO_TESTING=1; isolated PostgreSQL/cache/media, вымышленные данные, без внешних интеграций.
- Сохранить текущий dirty WORKTREE и ORG-01/02/03/04; HEAD2da9d33abbc53d1ac71bcb7e15a0170bef6277d5.
- Не менять max_length/required/schema/ACL/canonical transitions/publication/ownership/CAS/ServerDraft validations.
- ORG-06 technical labels и тексты lifecycle ошибок не переписывать; summary может использовать существующие form labels.
- Не добавлять автосохранение/новые поля/новые протоколы. Отправка → ошибка остаётся400 либо409 согласно нынешнему контракту.

## Файлы

- `src/catalog/templates/pages/organization_workspace.html`: summary и все errors только candidate editor, ID/error associations и marker bound errors.
- `src/catalog/controllers/organization_workspace.py`: только widget presentation attrs для error IDs, если существующий renderer не обеспечивает связи; ограничения форм не менять.
- `static/js/organization_workspace.js`: summary focus/target focus и приоритет bound error-response над старым local recovery. ORG-02 queue/CAS и ORG-03 create receipt не изменять.
- `static/css/pages/organization_workspace.css`: только summary/field error wrapping, focus и scroll offset при подтверждённой необходимости.
- `src/catalog/testcases/test_organization_editor_errors.py`, `scripts/test_organization_editor_errors.cjs`: regressions rendering/retention/errors/ACL/conflict.
- Новые report/evidence/screenshots и журнал состояния.

## Task1: свежая перепроверка и RED

- [x] Guarded PostgreSQL negative POST: name_ru/name_en256,phone/whatsapp51,invalid website; все locales. Проверить400, bound values, отсутствие live/candidate mutations, наличие каждого field error и target.
- [x] Hidden expected_version/revision_version и version nonfield errors: не теряются, ссылки не ведут на невидимые поля.
- [x] JS RED: старый recovery не заменяет bound input; current snapshot остаётся в sessionStorage для reload, без запроса ServerDraft при загрузке400.
- [x] JS RED: summary получает focus, ссылка фокусирует поле; clean GET продолжает прежнее восстановление.

## Task2: минимальная реализация и GREEN

- [x] В error summary `id=org-editor-errors`, `role=alert`, `tabindex=-1`, `data-org-error-summary`; вывести каждый field error и nonfield error. Для visible fields — anchor к `field.id_for_label` и data-org-error-target; hidden errors — plain text без ссылки на hidden input.
- [x] У каждого visible widget вывести errors в контейнере с ID; `aria-invalid=true` и `aria-describedby` указывают на существующие error IDs. Сохранить другие descriptions.
- [x] `data-org-server-errors` помечает bound form errors. Editor JS: при marker не подставлять старую local.fields; записать текущие posted fields в существующий recovery key. Не отправлять новый autosave при загрузке, не сбрасывать source/version/CAS.
- [x] Focus summary после восстановления; click/keyboard activation ссылки вызывает target.focus/scrollIntoView. Без JS anchors и ошибки остаются доступными.
- [x] GREEN regressions + existing JS autosave/creation14; server workspace/creation/drafts/join/detach families. Исправление отказа → pending candidate, live данные неизменны; conflict не перезаписывает winning candidate.

## Task3: rendered acceptance и handoff

- [x] Новые synthetic организации в local QA; зафиксировать старые domain hashes и version/runtime source manifest.
- [x] RU/AZ/EN×360/390/768/1024/1280/1440: реальный native400 с намеренным обходом maxlength/validation в harness; текст/links/ARIA/focus/geometry/values, PC/mobile screenshots.
- [x] Native исправление/отправка, repeated errors, reload recovery, two-tabs409, foreign404, keyboard Tab/Enter, no-JS rendering и private storage unavailable.
- [x] Fresh source/runtime/SHA preservation/local.diff/report/NOT RUN; ViewTransition/старый msgfmt duplicate не чинить.
- [x] Закрыть собственный active_run и browser session, оставить изолированный стенд. Остановиться после ORG-05.
