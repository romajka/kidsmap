# ORG-06 Organization Form Copy Implementation Plan

> **For agentic workers:** Выполнять последовательно в этом чате, без subagents/commit/push/deploy. Пользователь поручил следующий ORG-06 сообщением «дальше» после ORG-05; действующая авторизация сохранена. Статус: IMPLEMENTED LOCAL; отчёт docs/qa/org-06-fix-2026-10-08.md. Прежний auto-focus создания отмечен FAIL вне scope.

**Goal:** Локализовать подписи создания/редактирования организации и объяснить version conflict без потери ввода и ослабления CAS.

**Architecture:** Labels задаются двум существующим формам из RU/AZ/EN catalog. Пять существующих version checks получают стабильные error codes, сохраняя message/условия/порядок. Только owner organization transport переводит их в пользовательский текст. При 409 ссылка открывает текущие сохранённые данные в новой вкладке с явным `?current=1`; этот GET не подставляет ServerDraft/sessionStorage, не удаляет их и не меняет validation/ACL.

**Tech Stack:** Django forms/templates, существующие gettext catalogs, PostgreSQL QA, vanilla JS, jsdom, Chromium CLI.

**Spec:** [ORG-06 prompt](../../qa/organization-deep-audit-2026-10-08/prompts/org-06.md).

## Global Constraints

- Только DJANGO_TESTING=1, isolated DB/cache/media/private-media/email, вымышленные данные, внешние интеграции отключены.
- Сохранить dirty WORKTREE и ORG-01–05. HEAD `2da9d33abbc53d1ac71bcb7e15a0170bef6277d5`.
- Не менять required/max_length/status/ownership/affiliation/publication/authorization/ServerDraft/CAS. Не назначать organization_id напрямую.
- Отдельные findings, shared error-summary, ветка создания филиала и admin editor не меняются.
- Существующие дубли gettext не исправлять. Добавить только нужные записи; runtime MO обновить с проверкой сохранности всех прежних entries.

## Task 1: RED и свежая перепроверка

**Files:** новые `src/catalog/testcases/test_organization_form_copy.py`, `scripts/test_organization_current_data.cjs`.

- [x] Create POST без AZ в RU/AZ/EN:400, label `Название организации (AZ)` / `Təşkilatın adı (AZ)` / `Organization name (AZ)`, введённые контакты/переводы остаются.
- [x] Две последовательные отправки одного candidate version:302/409. Ошибка локализована, B в bound form, A в DB, версии B не обновляются автоматически. Повтор B снова409.
- [x] Current GET показывает A вместо личного ServerDraft B, а обычный GET сохраняет прежнее восстановление B. Прямой чужой GET/POST/`?current=1`404; запрос без CSRF403.
- [x] Все пять canonical conflict codes имеют локализованное отображение. Unknown expected validation exception получает безопасную общую ошибку; техническая detail не выводится.
- [x] JS real-script RED: `data-org-current-data` не подставляет cached B и не стирает его; обычный GET восстанавливает, invalid POST сохраняет bound input как в ORG-05.

## Task 2: минимальная реализация

**Files:** `src/catalog/controllers/organization_workspace.py`, `src/catalog/services/publication.py`, `src/catalog/templates/pages/organization_workspace.html`, `static/js/organization_workspace.js`, `locale/{ru,az,en}/LC_MESSAGES/django.po` (+локальные MO).

- [x] Labels для name_az/name_ru/name_en используют существующий `Название организации (%(language)s)`; description существующий `Описание организации (%(language)s)`. Контакты/отдельная организация/hidden versions/submit получают явные переведённые labels.
- [x] Propose сохраняет существующий raw message, добавляет только `code` для schema/source/candidate version/dependency/source conflicts. Пример: `raise ValidationError('Candidate version conflict.', code='candidate_version_conflict')`.
- [x] Controller показывает conflict copy по code; form nonfield error хранит тот же code и возвращает прежний409. Чужие права не превращаются в доступ к форме.
- [x] Candidate conflict RU: «Изменения уже сохранены в другой вкладке или другим редактором. Ваш ввод остался в форме. Скопируйте нужный текст и сравните его с актуальными данными перед повторной отправкой.» AZ/EN имеют равнозначный текст. Source/schema/dependency errors объясняют соответствующую причину с тем же сохранением ввода.
- [x] При conflict summary содержит обычную ссылку `target="_blank" rel="noopener"` на detail`?current=1` — «Открыть актуальные данные» / «Aktual məlumatları aç» / «Open current data». Исходный ввод остаётся в первой вкладке.
- [x] Detail current GET не подставляет личный ServerDraft, передаёт `data-org-current-data`. JS обычный local restore выполняет только без этого marker. Копия/версии/права не стираются и не обновляются обходным путём.
- [x] GREEN новые тесты + прежние organization/publication/drafts/JS tests. Прежние утверждения тестов не меняются.

## Task 3: browser и handoff

- [x] Собственные synthetic organizations, snapshot прежних domain rows, HEAD/WORKTREE/runtime source SHA.
- [x] RU/AZ/EN×360/390/768/1024/1280/1440: native invalid create/editor, text/focus/ARIA/keyboard/overflow. Negative harness обходит required/maxlength намеренно.
- [x] Для каждого языка: successful create, repeated invalid, corrected submission→pending, two tabs409→current link→compare/retry; old B и winner A сохраняются, foreign404. No-JS ссылки и current view.
- [x] PC/mobile screenshots, fresh exact tests/commands/results, own local.diff, source/DB preservation, NOT RUN. Прежний ViewTransition console defect и global duplicate msgfmt отмечены отдельно.
- [x] Закрыть собственный active_run/browser; оставить isolated QA8788, остановиться после ORG-06.
