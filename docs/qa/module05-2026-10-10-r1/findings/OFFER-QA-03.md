# OFFER-QA-03 — Сводка ошибки цены фокусирует выбор программы

OPEN · P2 · LOCAL C:/kidsmap · run module05-2026-10-10-r1 · HEAD8d188b316f800fbedf0b1e376905dfd4924cb1b6.
Роль: owner. Endpoint/URL: `/ru/account/places/5/edit/ → save-photos/`. Исполнитель /root, sequential AUDIT ONLY. Дефект приложения не исправлялся.
Classification: pre-existing baseline текущего WORKTREE. Регрессия относительно другого SHA/production NOT RUN. Для06 отдельно подтверждён ENVIRONMENT компонент existing .mo.

Шаги: Задать exact цену0, свернуть блоки занятия/группы/тарифа. Сохранить, затем нажать ссылку ошибки тарифа в сводке.

Ожидание: Нужные details раскрываются, фокус попадает в конкретное поле цены ошибочного тарифа.

Факт: 422 и ввод0 сохранены. После перехода activeElement — SELECT с data-offering-key=program_id; price не сфокусирован.

Причина / confidence: Подтверждённое несоответствие: fieldTarget ожидает activities[i].groups[j].pricing_plans[k].price и .price, а ошибка сервера имеет «Тариф1: поле price: …». Срабатывает fallback первого control. Confidence HIGH по наблюдаемому поведению; ограничения гипотез явно указаны.

Приоритет: На длинной форме ошибка внутри закрытых блоков остаётся труднодоступной; P2.

Область и зависимости: Структурированная адресация ошибок backend→owner form, сохранение localized текста, focus/details. Владельцы будущего решения: django-reviewer / frontend-reviewer / frontend-admin / database-reviewer по указанному слою; независимый запуск этих ролей не заявляется.

Доказательства свежего запуска:

- [functional4.result.txt](../functional4.result.txt)
- [hidden-price-error-390.png](../screenshots/hidden-price-error-390.png)

Source references: static/js/owner_place_continuous.js:161 fieldTarget; src/catalog/services/pricing_plans.py:normalize_pricing_plans. Snapshot и проверка неизменности: [snapshot](../snapshot.json), [verification](../verification.json).

Копируемый промпт для отдельного согласованного исправления:

```text
KidsMap: OFFER-QA-03, Сводка ошибки цены фокусирует выбор программы. Найди фактический checkout, прочитай AGENTS.md и canonical .agents. Отчёт: docs/qa/module05-2026-10-10-r1/findings/OFFER-QA-03.md. Старые screenshots/DB — только repro checklist; проверь новый HEAD/WORKTREE/active_run и свежий UI.
Сначала составь конкретный план области Структурированная адресация ошибок backend→owner form, сохранение localized текста, focus/details. Реализацию выполняй только в рамках явно согласованного пользователем scope. Не исправляй остальные findings попутно.
Согласуй машинный путь ошибки и UI-target без парсинга переведённого текста. При нескольких занятиях/группах/тарифах раскрой и сфокусируй конкретный erroneous input. Проверь Tab/Shift+Tab, mobile, hidden blocks, price/age/billing ошибки и сохранность ввода. Не меняй существующие assertions для зелёного результата.
Сохрани чужие изменения/active_run/стенды. Только DJANGO_TESTING=1 и собственные isolated DB/cache/media/private-media/email с вымышленными данными, без production credentials и внешних integrations. Без commit/push/deploy/production. Существующие assertions не ослаблять. Приложи exact commands/counts/exits и свежие browser screenshots/save/reload, докажи соответствие runtime WORKTREE; ограничения оставь NOT RUN.
```
