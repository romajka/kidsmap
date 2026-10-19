# ANALYTICS-QA-05 — Честные состояния GA4

P2; CLOSED LOCAL; LOCAL WORKTREE, production NOT RUN.

Disabled/error/partial/missing-window дают недоступность и прочерк; успешный пустой ответ даёт0. Время обновления только после успешной загрузки, безопасный статус и клавиатурный retry.

Первопричина, точные файлы, свежий RED и принятые границы: [план](../stages/reporting/IMPLEMENTATION_PLAN.md), [diff](../stages/reporting/implemented.diff). Итоговые проверки: [сводка](../verification.json), [backend](../evidence/final-backend.json), [отчёт](../REPORT.md). Историческая находка не использовалась вместо свежего воспроизведения.
