# ANALYTICS-QA-14 — Изоляция отказов чтения агрегатов

P2; CLOSED LOCAL; LOCAL WORKTREE, production NOT RUN.

Owner получает unavailable200; независимый GA продолжает работать. Atomic/savepoint восстанавливает транзакцию после реальной SQL ошибки.

Первопричина, точные файлы, свежий RED и принятые границы: [план](../stages/readfailure/IMPLEMENTATION_PLAN.md), [diff](../stages/readfailure/implemented.diff). Итоговые проверки: [сводка](../verification.json), [backend](../evidence/final-backend.json), [отчёт](../REPORT.md). Историческая находка не использовалась вместо свежего воспроизведения.
