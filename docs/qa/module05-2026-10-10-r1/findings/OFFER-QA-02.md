# OFFER-QA-02 — В редакторе групп нет обязательных полей регулярного абонемента

OPEN · P2 · LOCAL C:/kidsmap · run module05-2026-10-10-r1 · HEAD8d188b316f800fbedf0b1e376905dfd4924cb1b6.
Роль: owner. Endpoint/URL: `/ru/account/places/5/edit/ → /ru/account/places/5/save-photos/`. Исполнитель /root, sequential AUDIT ONLY. Дефект приложения не исправлялся.
Classification: pre-existing baseline текущего WORKTREE. Регрессия относительно другого SHA/production NOT RUN. Для06 отдельно подтверждён ENVIRONMENT компонент existing .mo.

Шаги: В тарифе группы выбрать membership, положительную точную цену, billing_mode=recurring и billing_interval=month. Нажать сохранение. Раскрыть дополнительные поля и проверить доступный ввод.

Ожидание: Владелец может задать обязательное число периодов и сохранить поддержанный регулярный тариф.

Факт: POST422: billing_interval_count «Укажите количество периодов больше нуля». Количество доступных controls для billing_interval_count и quantity_unit равно0. При one_time все13 product types сохранились.

Причина / confidence: Подтверждённый разрыв UI/model: owner group advanced строит billing_mode/interval, но не count/cycles/quantity/unit. Позитивная installment запись через этот UI NOT RUN; отсутствие её controls подтверждено source. Confidence HIGH по наблюдаемому поведению; ограничения гипотез явно указаны.

Приоритет: Поддержанный recurring сценарий невозможно закончить через доступные controls; P2.

Область и зависимости: Owner group pricing editor/choices/copy; согласование с canonical PricingPlan validation. Не ослаблять DB constraints и существующие assertions. Владельцы будущего решения: django-reviewer / frontend-reviewer / frontend-admin / database-reviewer по указанному слою; независимый запуск этих ролей не заявляется.

Доказательства свежего запуска:

- [functional4.result.txt](../functional4.result.txt)
- [pricing.result.txt](../pricing.result.txt)
- [membership-missing-count-390.png](../screenshots/membership-missing-count-390.png)

Source references: static/js/owner_place_offerings.js:126–138; src/catalog/models/pricing_plan.py:128–135; src/catalog/services/pricing_plans.py:normalize_pricing_plans. Snapshot и проверка неизменности: [snapshot](../snapshot.json), [verification](../verification.json).

Копируемый промпт для отдельного согласованного исправления:

```text
KidsMap: OFFER-QA-02, В редакторе групп нет обязательных полей регулярного абонемента. Найди фактический checkout, прочитай AGENTS.md и canonical .agents. Отчёт: docs/qa/module05-2026-10-10-r1/findings/OFFER-QA-02.md. Старые screenshots/DB — только repro checklist; проверь новый HEAD/WORKTREE/active_run и свежий UI.
Сначала составь конкретный план области Owner group pricing editor/choices/copy; согласование с canonical PricingPlan validation. Не ослаблять DB constraints и существующие assertions. Реализацию выполняй только в рамках явно согласованного пользователем scope. Не исправляй остальные findings попутно.
Добавь согласованные с canonical pricing поля count/cycles/quantity/unit, условную видимость и сохранение значений. Обеспечь recurring и installment без фиктивных defaults. Проверь membership/month/count, installment/cycles, quantity/unit, переключение one_time, invalid0, RU/AZ/EN mobile/PC, native save и reload.
Сохрани чужие изменения/active_run/стенды. Только DJANGO_TESTING=1 и собственные isolated DB/cache/media/private-media/email с вымышленными данными, без production credentials и внешних integrations. Без commit/push/deploy/production. Существующие assertions не ослаблять. Приложи exact commands/counts/exits и свежие browser screenshots/save/reload, докажи соответствие runtime WORKTREE; ограничения оставь NOT RUN.
```
