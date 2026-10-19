# ANALYTICS-QA-12 — Нечисловой и слишком длинный numeric ID

P2; CLOSED LOCAL; LOCAL WORKTREE, production NOT RUN.

Неконвертируемый Unicode и5000-значный ID дают400 без записи вместо500. Чужие размеры/идентичности из payload не принимаются.

Первопричина, точные файлы, свежий RED и принятые границы: [план](../stages/payload/IMPLEMENTATION_PLAN.md), [diff](../stages/payload/implemented.diff). Итоговые проверки: [сводка](../verification.json), [backend](../evidence/final-backend.json), [отчёт](../REPORT.md). Историческая находка не использовалась вместо свежего воспроизведения.
