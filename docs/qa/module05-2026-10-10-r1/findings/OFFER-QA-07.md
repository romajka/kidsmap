# OFFER-QA-07 — Обычный адрес редактора молча восстанавливает устаревшую рабочую копию

OPEN · P2 · LOCAL C:/kidsmap · run module05-2026-10-10-r1 · HEAD8d188b316f800fbedf0b1e376905dfd4924cb1b6.
Роль: owner. Endpoint/URL: `/ru/account/places/6/edit/; /ru/api/drafts/`. Исполнитель /root, sequential AUDIT ONLY. Дефект приложения не исправлялся.
Classification: pre-existing baseline текущего WORKTREE. Регрессия относительно другого SHA/production NOT RUN. Для06 отдельно подтверждён ENVIRONMENT компонент existing .mo.

Шаги: На чистой синтетической карточке в отдельной сессии создать unsaved Activity A и дождаться server autosave. В другой fresh сессии создать валидные Activity/Group B, явно сохранить, отправить и одобрить. В новой сессии открыть обычный /edit/ без fresh=1, сравнить с новым fresh=1 редактором.

Ожидание: Устаревшая server working copy не подменяет актуальную карточку без предупреждения о версии и явного решения пользователя.

Факт: Обычный URL восстановил OLD unsaved activity A с пустыми group/price и без актуальных ID. Fresh URL показывает approved B Activity4/Group5/35 AZN. UI сообщает «Текст и тарифы сохранены на сервере». Source version формы3, выбранной draft1; conflict отсутствует. Обычный reload fresh=1 ранее прошёл — разные пути не смешаны.

Причина / confidence: Подтверждённая причина: server restore выбирает не materialized рабочую копию и применяет fields без сравнения detail.source_version с form sourceVersion. Explicit save помечает только текущую копию, старые остаются resumable. Local-cache version check есть, но не выполняет эту проверку для fetched server copy. Confidence HIGH по наблюдаемому поведению; ограничения гипотез явно указаны.

Приоритет: Владелец редактирует устаревшее дерево вместо сохранённого; риск повторного создания/перезаписи при последующей валидной отправке. Сам факт production потери данных NOT RUN; P2.

Область и зависимости: ServerDraft lifecycle/version checks, owner restoration UX, candidate/live и multiple sessions. Не очищать все черновики вслепую. Владельцы будущего решения: django-reviewer / frontend-reviewer / frontend-admin / database-reviewer по указанному слою; независимый запуск этих ролей не заявляется.

Доказательства свежего запуска:

- [restore.result.txt](../restore.result.txt)
- [restore-read.result.txt](../restore-read.result.txt)
- [state-final.json](../state-final.json)
- [normal-edit-old-copy-after-publish-390.png](../screenshots/normal-edit-old-copy-after-publish-390.png)
- [fresh-edit-approved-copy-after-publish-390.png](../screenshots/fresh-edit-approved-copy-after-publish-390.png)

Source references: static/js/owner_place_continuous.js:73 restore; src/catalog/services/server_drafts.py:198 mark_explicit_save. Snapshot и проверка неизменности: [snapshot](../snapshot.json), [verification](../verification.json).

Копируемый промпт для отдельного согласованного исправления:

```text
KidsMap: OFFER-QA-07, Обычный адрес редактора молча восстанавливает устаревшую рабочую копию. Найди фактический checkout, прочитай AGENTS.md и canonical .agents. Отчёт: docs/qa/module05-2026-10-10-r1/findings/OFFER-QA-07.md. Старые screenshots/DB — только repro checklist; проверь новый HEAD/WORKTREE/active_run и свежий UI.
Сначала составь конкретный план области ServerDraft lifecycle/version checks, owner restoration UX, candidate/live и multiple sessions. Не очищать все черновики вслепую. Реализацию выполняй только в рамках явно согласованного пользователем scope. Не исправляй остальные findings попутно.
Устрани молчаливое применение устаревшей server copy: версия карточки/кандидата, явный выбор восстановления, scope actor+target, завершение старых copies при explicit save с сохранением нужного ввода. Проверь два разных browser contexts, обычный /edit/, fresh=1, logout/login, reload после draft/save/approval, server/local conflicts и отсутствие потери новых B данных.
Сохрани чужие изменения/active_run/стенды. Только DJANGO_TESTING=1 и собственные isolated DB/cache/media/private-media/email с вымышленными данными, без production credentials и внешних integrations. Без commit/push/deploy/production. Существующие assertions не ослаблять. Приложи exact commands/counts/exits и свежие browser screenshots/save/reload, докажи соответствие runtime WORKTREE; ограничения оставь NOT RUN.
```
