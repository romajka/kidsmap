# ANALYTICS-QA-07 — Изоляция отказов записи аналитики

P2; CLOSED LOCAL; LOCAL WORKTREE, production NOT RUN.

Optional writes имеют отдельный atomic/savepoint; DatabaseError перехватывается снаружи с безопасным предупреждением. Публичные карточки и бизнес-действия продолжают работать; ошибки каталога/ACL/программирования не скрываются.

Первопричина, точные файлы, свежий RED и принятые границы: [план](../stages/ingress/IMPLEMENTATION_PLAN.md), [diff](../stages/ingress/implemented.diff). Итоговые проверки: [сводка](../verification.json), [backend](../evidence/final-backend.json), [отчёт](../REPORT.md). Историческая находка не использовалась вместо свежего воспроизведения.
