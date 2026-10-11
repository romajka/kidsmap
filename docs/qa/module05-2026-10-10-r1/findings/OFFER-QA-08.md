# OFFER-QA-08 — Причина окончательного отказа программы не видна владельцу

OPEN · P2 · LOCAL C:/kidsmap · run module05-2026-10-10-r1 · HEAD8d188b316f800fbedf0b1e376905dfd4924cb1b6.
Роль: moderator → owner. Endpoint/URL: `/admin/volunteer/moderation/content/1/ → /ru/account/organizations/1/programs/1/`. Исполнитель /root, sequential AUDIT ONLY. Дефект приложения не исправлялся.
Classification: pre-existing baseline текущего WORKTREE. Регрессия относительно другого SHA/production NOT RUN. Для06 отдельно подтверждён ENVIRONMENT компонент existing .mo.

Шаги: Владелец отправляет изменение описания программы. Moderator выбирает «Отклонить» с причиной. Владелец открывает/перезагружает программу. Отдельно пройти исправление, повторную отправку и одобрение.

Ожидание: Владелец видит сохранённую причину решения и предложенный текст для осознанного исправления.

Факт: DB revision1 status=declined, review_note «Uydurma OFFER08 reason: clarify program text». Owner видит только чип «Отклонено», причина отсутствует; input description показывает прежнее approved «Uydurma corrected after review», а не предложенный текст. Correction/resubmit/reapproval в предыдущем native цикле прошли.

Причина / confidence: Подтверждённая причина: final_reject сохраняет status=declined, template показывает review_note только для rejected; _context overlay payload тоже ограничен draft/pending/rejected. Confidence HIGH по наблюдаемому поведению; ограничения гипотез явно указаны.

Приоритет: Нельзя понять отказ и продолжить исходное предложение по причине решения; P2, live публикация при этом сохраняется.

Область и зависимости: Program owner candidate lifecycle/status rendering/forms; moderation decision contract. Зависимости: различие return/rejected и final reject/declined. Владельцы будущего решения: django-reviewer / frontend-reviewer / frontend-admin / database-reviewer по указанному слою; независимый запуск этих ролей не заявляется.

Доказательства свежего запуска:

- [rejection.result.txt](../rejection.result.txt)
- [rejection-repro.result.txt](../rejection-repro.result.txt)
- [state-final.json](../state-final.json)
- [program-declined-reason-missing-390.png](../screenshots/program-declined-reason-missing-390.png)

Source references: src/catalog/templates/pages/program_editor.html:9; src/catalog/controllers/program_workspace.py:52 _context; src/catalog/services/publication.py:408; services/volunteer_proposals.py:37. Snapshot и проверка неизменности: [snapshot](../snapshot.json), [verification](../verification.json).

Копируемый промпт для отдельного согласованного исправления:

```text
KidsMap: OFFER-QA-08, Причина окончательного отказа программы не видна владельцу. Найди фактический checkout, прочитай AGENTS.md и canonical .agents. Отчёт: docs/qa/module05-2026-10-10-r1/findings/OFFER-QA-08.md. Старые screenshots/DB — только repro checklist; проверь новый HEAD/WORKTREE/active_run и свежий UI.
Сначала составь конкретный план области Program owner candidate lifecycle/status rendering/forms; moderation decision contract. Зависимости: различие return/rejected и final reject/declined. Реализацию выполняй только в рамках явно согласованного пользователем scope. Не исправляй остальные findings попутно.
Согласуй отображение declined/rejected с canonical review semantics: причина, текущие и предложенные тексты, доступное дальнейшее действие. Не переименовывай бизнес-статусы только ради UI. Проверь approve/return/final reject, owner reload, correction/resubmit, AZ/RU/EN, mobile/PC и неизменность live до одобрения.
Сохрани чужие изменения/active_run/стенды. Только DJANGO_TESTING=1 и собственные isolated DB/cache/media/private-media/email с вымышленными данными, без production credentials и внешних integrations. Без commit/push/deploy/production. Существующие assertions не ослаблять. Приложи exact commands/counts/exits и свежие browser screenshots/save/reload, докажи соответствие runtime WORKTREE; ограничения оставь NOT RUN.
```
