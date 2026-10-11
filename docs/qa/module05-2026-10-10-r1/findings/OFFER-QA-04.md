# OFFER-QA-04 — Кнопки расписания выходят за границы формы при1024px

OPEN · P2 · LOCAL C:/kidsmap · run module05-2026-10-10-r1 · HEAD8d188b316f800fbedf0b1e376905dfd4924cb1b6.
Роль: owner. Endpoint/URL: `/ru/account/places/5/edit/; режим часов regular`. Исполнитель /root, sequential AUDIT ONLY. Дефект приложения не исправлялся.
Classification: pre-existing baseline текущего WORKTREE. Регрессия относительно другого SHA/production NOT RUN. Для06 отдельно подтверждён ENVIRONMENT компонент existing .mo.

Шаги: Открыть заполненные часы работы в RU или AZ, viewport1024×950, с обычными буднями и несколькими интервалами понедельника. Прокрутить к расписанию.

Ожидание: «+ Интервал» и «Копировать» доступны целиком в пределах формы.

Факт: Ряд заканчивается x941, copy-area доx1084.83, кнопка доx1084.83 при viewport1024. В screenshot «+ Интервал» обрезана, «Копировать» скрыта справа.8 visual rows матрицы FAIL. EN1024 в прежней матрице имел иной восстановленный режим, поэтому тот case не доказывает исправность regular EN.

Причина / confidence: Подтверждена геометрия и rendered clipping. Гипотеза CSS причины: четыре grid-колонки с минимальными ширинами плюс owner sidebar и nowrap copy-area превышают доступную ширину. Точный минимальный CSS patch не реализовывался. Confidence HIGH по наблюдаемому поведению; ограничения гипотез явно указаны.

Приоритет: Часть управления часами недоступна в обычном размере окна; P2.

Область и зависимости: Owner schedule responsive CSS с учётом actual content width; shared component/admin consumers. Владельцы будущего решения: django-reviewer / frontend-reviewer / frontend-admin / database-reviewer по указанному слою; независимый запуск этих ролей не заявляется.

Доказательства свежего запуска:

- [matrix.result.txt](../matrix.result.txt)
- [diagnostics.result.txt](../diagnostics.result.txt)
- [owner-diagnostic-ru-1024.png](../screenshots/owner-diagnostic-ru-1024.png)
- [owner-schedule-copy-crop-1024.png](../screenshots/owner-schedule-copy-crop-1024.png)

Source references: static/css/components/kidsmap_schedule_editor.css:302; static/css/pages/permanent_place_wizard.css:5. Snapshot и проверка неизменности: [snapshot](../snapshot.json), [verification](../verification.json).

Копируемый промпт для отдельного согласованного исправления:

```text
KidsMap: OFFER-QA-04, Кнопки расписания выходят за границы формы при1024px. Найди фактический checkout, прочитай AGENTS.md и canonical .agents. Отчёт: docs/qa/module05-2026-10-10-r1/findings/OFFER-QA-04.md. Старые screenshots/DB — только repro checklist; проверь новый HEAD/WORKTREE/active_run и свежий UI.
Сначала составь конкретный план области Owner schedule responsive CSS с учётом actual content width; shared component/admin consumers. Реализацию выполняй только в рамках явно согласованного пользователем scope. Не исправляй остальные findings попутно.
Исправь responsive композицию schedule controls в continuous owner form при1024 и соседних размерах. Проверь regular, несколько интервалов, длинные AZ/RU labels, open copy popup, keyboard, sticky sidebar и widths360/390/768/1024/1280/1440. Не меняй schedule/business rules.
Сохрани чужие изменения/active_run/стенды. Только DJANGO_TESTING=1 и собственные isolated DB/cache/media/private-media/email с вымышленными данными, без production credentials и внешних integrations. Без commit/push/deploy/production. Существующие assertions не ослаблять. Приложи exact commands/counts/exits и свежие browser screenshots/save/reload, докажи соответствие runtime WORKTREE; ограничения оставь NOT RUN.
```
