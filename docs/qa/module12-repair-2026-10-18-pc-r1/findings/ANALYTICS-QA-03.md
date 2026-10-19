# ANALYTICS-QA-03 — Допустимый Origin с портом

P2; CLOSED LOCAL; LOCAL WORKTREE, production NOT RUN.

Сохраняется полная authority запроса и явно доверенных origins. Чужие host/port и HTTPS downgrade отклоняются.

Первопричина, точные файлы, свежий RED и принятые границы: [план](../stages/ingress/IMPLEMENTATION_PLAN.md), [diff](../stages/ingress/implemented.diff). Итоговые проверки: [сводка](../verification.json), [backend](../evidence/final-backend.json), [отчёт](../REPORT.md). Историческая находка не использовалась вместо свежего воспроизведения.
