# SOCIAL-QA-08 Implementation Plan

> Execution: один lead django-reviewer; frontend-reviewer/security-reviewer/browser-qa проверки выполнены последовательно тем же /root. Это не независимые аудиты. Работать по шагам; отдельные subagents не требуются. Project guide задаёт расположение плана и запрет commit/push/deploy.

**Goal:** Собственное недоступное приглашение оставляет полноценный локализованный inbox с понятным сообщением и ссылкой возврата при сохранении HTTP403 и отказа в выдаче доступа.

**Architecture:** Обработчик accept_invitation сохраняет текущие _mine/login/POST/CSRF/service guards. В существующем except вызывается уже используемый reject flow helper _render_inbox(error='invitation_unavailable',status=403). Он повторно читает собственный текущий inbox и использует существующий account_notifications template, role=alert, RU/AZ/EN copy и navigation link. Никакой exception text в UI.

**Tech Stack:** Python3.12.15, Django6.0.2, PostgreSQL17.11; native Chromium155.0.8059.12. Fresh isolated locale MO RU/AZ/EN.

**Spec:** ../module09-2026-10-10-r1/findings/SOCIAL-QA-08.md, ../module09-2026-10-10-r1/repair-prompts/SOCIAL-QA-08.txt и PLAN SOCIAL-QA-08 в ../continuation-and-repair-prompts-2026-10-11.md. Отчёт этого run и candidate-manifest.json определяют текущий snapshot.

## Global Constraints

- Только PLAN, application patch пока не одобрен. До implementation нужно одобрение точного двухфайлового scope; уже данное одобрение этого scope не спрашивать повторно.
- HEAD852938d96764ae315b92859e3651e5ea62054a36; ветка codex/module09-transfer-2026-10-16-r1. Dirty WORKTREE03–07 сохранить. Source-entry1022 должен совпасть перед patch, после добавления теста ожидается1023.
- Без reset/clean/stash/переключения грязного checkout/commit/push/deploy/production/автоматического active_run. Старые QA scripts не запускать автоматически.
- DJANGO_TESTING1, свои изолированные DB/cache/media/private-media/email, fictional data, очищенный env без production credentials; только внутренний network, localhost browser allowlist. Fresh own RU/AZ/EN MO + manifest verify + sole LOCALE_PATHS до django.setup.
- Не менять existing assertions ради green. Full module09 corpus только после SOCIAL01–09; глобальный корпус отдельно в конце.
- Старые PNG не догружать. Новые proof этого run самостоятельны; production applicability UNKNOWN.

## Task1 — source gates и RED

- [ ] Прочитать REPORT/results/verification/source-entry/candidate-manifest и полученное human approval. Проверить все1022sourcehashes, HEAD/branch/task33-progress/index/dirty/active_run NONE/sharedMO/.cbmignore/priorpackages/entrycontainers.
- [ ] Подтвердить ownership/isolation свежего own08 app/PG/internalnet. Reuse разрешён только после проверки фактических IDs, RO repository mount и текущих source/template/runtime/locale origins. Новый implementation server должен загрузить новые исходники; не использовать старый импорт контроллера.
- [ ] На неизменившемся source использовать native RED и nine-method RED этого run. Browser response body0; Chromium может показать chrome-error://chromewebdata/ вместо полностью белой страницы. Оба лишены app feedback/navigation. Изменение snapshot требует affected fresh reproduction.
- [ ] Candidate tests исполняются из ignored scratch candidate_tests.SocialQA08InvitationFeedbackTests до patch, приложение не содержит нового файла. RED — meaningful missing-copy failures, не harness failures.

## Task2 — exact two-file patch

**Modify:** src/catalog/controllers/workflow_notifications.py, import и существующий except в accept_invitation около83.

**Create:** src/catalog/testcases/test_social_qa08_invitation_feedback.py (полный кандидат candidate_tests.py,9методов).

Полный diff — proposed.diff. Полный controller — candidate-workflow_notifications.py. SHA — candidate-manifest.json. Минимальное изменение:

~~~python
# Existing except tuple and service call unchanged:
return _render_inbox(request, error='invitation_unavailable', status=403)
~~~

Удаляется только ставший неиспользуемым import HttpResponseForbidden. Новых helper/routes/strings/templates/CSS/JS/PO/schema/services не требуется.

- [ ] git apply --check --ignore-space-change docs/qa/social-qa08-recheck-2026-10-17-pc-r1/proposed.diff
- [ ] После gates и approval: git apply --ignore-space-change docs/qa/social-qa08-recheck-2026-10-17-pc-r1/proposed.diff
- [ ] Сверить exact candidate hashes, source1023 и остальные1021 исходных файлов побайтно прежние. Существующие dirty03–07 patches не менять.
- [ ] _mine foreign/missing/current-email gate остаётся до except и сохраняет404. Login/POST/CSRF guards прежние. Service transaction, grant/owner/email/expiry/scope проверки и owner workflow прежние. Никаких grants/read_at/outbox mutations в error rendering.
- [ ] Generic copy не раскрывает причину исключения или чужую запись. Unsupported notification entity_type сохраняет текущий PermissionDenied path.

## Task3 — один targeted GREEN и native acceptance

- [ ] New9 методов + affected3 existing методов выполнить одним запуском после approval:

~~~text
catalog.testcases.test_social_qa08_invitation_feedback.SocialQA08InvitationFeedbackTests
catalog.testcases.test_task33_notifications.WorkflowIntegrationTests.test_invitation_inbox_post_only_recipient_scoped_and_revocation_suppresses_mail
catalog.testcases.test_task33_notifications.WorkflowIntegrationTests.test_changed_email_cannot_read_old_address_notification
catalog.testcases.test_task33_notifications.WorkflowIntegrationTests.test_csrf_required_for_inbox_actions
~~~

- [ ] Expected12 unique methods GREEN. Новые тесты: cancelled для обоих типов RU/AZ/EN; expired; stale ownership; missing invite при own notice; повтор accepted без regrant; foreign/nonexistent404; changed-email404; anonymous/GET/CSRF guards; valid invitation302/one grant. Existing tests/assertions не редактировать. Real SMTP NOTRUN; locmem delivery только existing isolated test.
- [ ] Повторить ту же native матрицу36cells: place/organization×RU/AZ/EN×360/390/768/1024/1280/1440. Владелец приглашает через реальную форму; получатель держит inbox; владелец реально отменяет; получатель keyboard focus/Enter нажимает stale Accept. Никакой подмены endpoint response/DOM/candidate rendering до approval.
- [ ] Status403, CANCELED, memberships/grants0 и unchanged counts должны остаться PASS; localized role=alert/account shell/inbox link должны стать PASS. После patch браузер получает настоящий HTML вместо собственного Chromium error page; requestfailed signature empty403 должна исчезнуть. Не «зелёнить» сменой expected status или обходом native flow.
- [ ] На error document использовать реальную existing inbox navigation ссылку: keyboard focus/Enter или native click → GET inbox200 → reload200 → cancelled Accept отсутствует. Проверить все три локали, scroll/focus/overflow/icons/static/fonts, console/pageerrors/network, native screenshots после finite wait.
- [ ] Small native controls для foreign ID404, changed email404, GET405, unauth redirect, CSRF403 и current invitation success плюс Place/Organization grants readback. Scopeownfixtures only. Если поведение основного чужого сайта отличается — зафиксировать отдельно, не расширять patch.
- [ ] Error helper читает до100 собственных уведомлений; это дополнительный read-only render, не изменение permission/model contract. Все отсутствующие/expired/stale cases используют generic existing text, privacy сохранена.

## Task4 — closure/preservation/stop

- [ ] Новый unique fix-run docs/qa/social-qa08-fix-…: approval, actual diff, RED→GREEN, exact commands/exits/counts, source/runtime/locale manifests, PNG/console/network, preparation failures отдельно, NOTRUN.
- [ ] Проверить source1023/1021unchanged, current previous packages bytes/manifests, entrycontainer ID/name/state, refs/index/activeNONE/sharedMO/.cbmignore. Whole-machine process continuity не выводить из Docker snapshot.
- [ ] Дописать отдельную guide closure note с обратной проверкой прежних bytes. Закрывать только фактически прошедший SOCIAL08; module09 OPEN. SOCIAL09/fullACCEPT09/global/module10 не начинать автоматически.

## Self-review / approval boundary

Точный scope: controller + один новый regression file. Существующий шаблон уже содержит нужный UX, перевод и recovery link; изменение общего handler403, service guards или UI assets не требуется. Native RED не подменяет future GREEN. PLAN не означает реализацию; candidate-live execution NOTRUN. После review требуется одобрение этого плана по правилам PLAN→IMPLEMENT в guide/AGENTS.md.
