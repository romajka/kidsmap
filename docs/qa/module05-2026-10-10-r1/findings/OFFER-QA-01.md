# OFFER-QA-01 — Удалённая группа остаётся публичной после одобрения

OPEN · P2 · LOCAL C:/kidsmap · run module05-2026-10-10-r1 · HEAD8d188b316f800fbedf0b1e376905dfd4924cb1b6.
Роль: owner → moderator → public. Endpoint/URL: `/ru/account/places/5/edit/; /admin/volunteer/review/5/; /ru/activities/2/`. Исполнитель /root, sequential AUDIT ONLY. Дефект приложения не исправлялся.
Classification: pre-existing baseline текущего WORKTREE. Регрессия относительно другого SHA/production NOT RUN. Для06 отдельно подтверждён ENVIRONMENT компонент existing .mo.

Шаги: Открыть опубликованное занятие с двумя группами 4–6/20 AZN и 12–15/80 AZN. Раскрыть вторую группу, нажать «Удалить группу», отправить форму на проверку. В административном review одобрить. Перезагрузить публичное занятие.

Ожидание: Вторая группа перестаёт показываться в активном предложении после одобрения; история может сохраняться.

Факт: Группа исчезла из nested_pricing формы, POST200 и одобрение прошли, но группа #3 с тарифом80 AZN осталась в DB без archived_at и в public DOM.

Причина / confidence: Подтверждённая причина: JS удаляет строку из массива, replacement обрабатывает только присланные activity/groups и не архивирует отсутствующие группы. Владение ID валидируется, но отсутствие строки не применяется. Confidence HIGH по наблюдаемому поведению; ограничения гипотез явно указаны.

Приоритет: Ограниченный неверный публичный контент после успешного решения модерации; P2. Потеря production данных не исследована.

Область и зависимости: Nested replacement/publication, archive/visibility semantics, owner editor. Зависимости: PricingPlan history, candidate/live и транзакция одобрения. Владельцы будущего решения: django-reviewer / frontend-reviewer / frontend-admin / database-reviewer по указанному слою; независимый запуск этих ролей не заявляется.

Доказательства свежего запуска:

- [lifecycle.result.txt](../lifecycle.result.txt)
- [state-removed-group.json](../state-removed-group.json)
- [removed-group-still-public-390.png](../screenshots/removed-group-still-public-390.png)

Source references: src/catalog/services/pricing_plans.py:532 replace_nested_pricing; static/js/owner_place_offerings.js:143. Snapshot и проверка неизменности: [snapshot](../snapshot.json), [verification](../verification.json).

Копируемый промпт для отдельного согласованного исправления:

```text
KidsMap: OFFER-QA-01, Удалённая группа остаётся публичной после одобрения. Найди фактический checkout, прочитай AGENTS.md и canonical .agents. Отчёт: docs/qa/module05-2026-10-10-r1/findings/OFFER-QA-01.md. Старые screenshots/DB — только repro checklist; проверь новый HEAD/WORKTREE/active_run и свежий UI.
Сначала составь конкретный план области Nested replacement/publication, archive/visibility semantics, owner editor. Зависимости: PricingPlan history, candidate/live и транзакция одобрения. Реализацию выполняй только в рамках явно согласованного пользователем scope. Не исправляй остальные findings попутно.
Обеспечь предусмотренное контрактом удаление/архивирование отсутствующей группы при одобрении полного nested payload. Не интерпретируй частичный import как очистку. Проверь также пропуск занятия, удаление тарифа, foreign IDs, атомарность, историю и повторное одобрение. Воспроизведи полный UI путь и reload публичной карточки.
Сохрани чужие изменения/active_run/стенды. Только DJANGO_TESTING=1 и собственные isolated DB/cache/media/private-media/email с вымышленными данными, без production credentials и внешних integrations. Без commit/push/deploy/production. Существующие assertions не ослаблять. Приложи exact commands/counts/exits и свежие browser screenshots/save/reload, докажи соответствие runtime WORKTREE; ограничения оставь NOT RUN.
```
