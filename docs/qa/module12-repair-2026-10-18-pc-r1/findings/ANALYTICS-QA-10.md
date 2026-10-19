# ANALYTICS-QA-10 — Отказ служебного ingress-счётчика — дополнительный случай07

P2; MERGED → ANALYTICS-QA-07; CLOSED LOCAL; LOCAL WORKTREE, production NOT RUN.

Ошибка вспомогательного счётчика не ломает уже сохранённое событие. Общая граница persistence учитывается вместе с07.

Первопричина, точные файлы, свежий RED и принятые границы: [план](../stages/ingress/IMPLEMENTATION_PLAN.md), [diff](../stages/ingress/implemented.diff). Итоговые проверки: [сводка](../verification.json), [backend](../evidence/final-backend.json), [отчёт](../REPORT.md). Историческая находка не использовалась вместо свежего воспроизведения.
