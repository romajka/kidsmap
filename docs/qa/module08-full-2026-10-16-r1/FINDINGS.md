# Новые findings полного ACCEPT-08

| ID | Приоритет | Факт | Scope approval |
|---|---|---|---|
| [MOD-QA-09](findings/MOD-QA-09.md) | P3 | Счётчик drawer остаётся русским в AZ/EN | [3file PLAN](findings/MOD-QA-09-PLAN.md), pending |
| [MOD-QA-10](findings/MOD-QA-10.md) | P3 | Loading/success publication toasts имеют RU literals | [6file PLAN](findings/MOD-QA-10-PLAN.md), pending |
| [MOD-QA-11](findings/MOD-QA-11.md) | P2 | Terminal content detail не показывает сохранённую причину | [2file PLAN](findings/MOD-QA-11-PLAN.md), pending |

Это новые причины модуля08. Модуль09 не запускался. MOD-QA-01–08 остаются scoped CLOSED LOCAL. Приложение в этом ACCEPT не исправлялось. Единственный зависший собственный renderer — отдельный UNKNOWN runtime incident, не новый доказанный application finding; свежий AZ390repro PASS. Исторические/неподтверждённые ожидания в harness-corrections.md не выданы за новые баги.
