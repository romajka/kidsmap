# ANALYTICS-QA-09 — API при отказе записи — дополнительный случай07

P2; MERGED → ANALYTICS-QA-07; CLOSED LOCAL; LOCAL WORKTREE, production NOT RUN.

API возвращает503 analytics_unavailable без фиктивной записи вместо500/неверной классификации. Общая первопричина и helper учитываются вместе с07.

Первопричина, точные файлы, свежий RED и принятые границы: [план](../stages/ingress/IMPLEMENTATION_PLAN.md), [diff](../stages/ingress/implemented.diff). Итоговые проверки: [сводка](../verification.json), [backend](../evidence/final-backend.json), [отчёт](../REPORT.md). Историческая находка не использовалась вместо свежего воспроизведения.
