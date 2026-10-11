# OFFER-QA-05 — Мобильный статус группы требует горизонтального скролла внутри вкладки

OPEN · P3 · LOCAL C:/kidsmap · run module05-2026-10-10-r1 · HEAD8d188b316f800fbedf0b1e376905dfd4924cb1b6.
Роль: admin-editor. Endpoint/URL: `/admin/catalog/offeringgroup/2/change/`. Исполнитель /root, sequential AUDIT ONLY. Дефект приложения не исправлялся.
Classification: pre-existing baseline текущего WORKTREE. Регрессия относительно другого SHA/production NOT RUN. Для06 отдельно подтверждён ENVIRONMENT компонент existing .mo.

Шаги: Зайти staff с platform review permission и явным place.edit grant. Открыть вкладку «Состояние» группы при390px в RU/EN.

Ожидание: Полный статус публикации читается сразу и переносится внутри панели.

Факт: Badge шириной246.5px доx363.5 внутри tab-pane доx322 и шириной254px. Таб имеет overflow-x:auto и scrollWidth296. Конец статуса обрезан в начальном положении. Горизонтальная прокрутка теоретически доступна; недоступность навсегда не утверждается.

Причина / confidence: Подтверждённая причина: nowrap badge шире ограниченной мобильной панели; scrollable tab обрезает начальное отображение. Общий document.scrollWidth при этом нормальный. Confidence HIGH по наблюдаемому поведению; ограничения гипотез явно указаны.

Приоритет: Полировка читаемости рабочего статуса, сохранение/права не блокируются; P3.

Область и зависимости: Admin status badges/BusinessEditor responsive layout; остальные entity forms. Владельцы будущего решения: django-reviewer / frontend-reviewer / frontend-admin / database-reviewer по указанному слою; независимый запуск этих ролей не заявляется.

Доказательства свежего запуска:

- [badge-diagnostic.result.txt](../badge-diagnostic.result.txt)
- [clipping.result.txt](../clipping.result.txt)
- [admin-group-badge-crop-390.png](../screenshots/admin-group-badge-crop-390.png)
- [admin-group-en-badge-crop-390.png](../screenshots/admin-group-en-badge-crop-390.png)

Source references: static/admin/css/kidsmap_admin_components.css:252; src/catalog/domain_admin/business.py:118 publication_badge. Snapshot и проверка неизменности: [snapshot](../snapshot.json), [verification](../verification.json).

Копируемый промпт для отдельного согласованного исправления:

```text
KidsMap: OFFER-QA-05, Мобильный статус группы требует горизонтального скролла внутри вкладки. Найди фактический checkout, прочитай AGENTS.md и canonical .agents. Отчёт: docs/qa/module05-2026-10-10-r1/findings/OFFER-QA-05.md. Старые screenshots/DB — только repro checklist; проверь новый HEAD/WORKTREE/active_run и свежий UI.
Сначала составь конкретный план области Admin status badges/BusinessEditor responsive layout; остальные entity forms. Реализацию выполняй только в рамках явно согласованного пользователем scope. Не исправляй остальные findings попутно.
Обеспечь чтение полного статуса без внутренней горизонтальной прокрутки. Сохрани статусную семантику, focus и размер контролов. Проверь Program/Activity/Group, длинные RU/AZ/EN подписи и все6 ширин, включая open tabs. Учитывай что root overflow detector не ловит этот случай.
Сохрани чужие изменения/active_run/стенды. Только DJANGO_TESTING=1 и собственные isolated DB/cache/media/private-media/email с вымышленными данными, без production credentials и внешних integrations. Без commit/push/deploy/production. Существующие assertions не ослаблять. Приложи exact commands/counts/exits и свежие browser screenshots/save/reload, докажи соответствие runtime WORKTREE; ограничения оставь NOT RUN.
```
