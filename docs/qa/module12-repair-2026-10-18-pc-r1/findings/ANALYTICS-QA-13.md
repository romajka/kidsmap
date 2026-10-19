# ANALYTICS-QA-13 — Некорректный необязательный Referer

P2; CLOSED LOCAL; LOCAL WORKTREE, production NOT RUN.

Ошибка разбора optional referrer даёт пустой domain без отказа допустимого события; нормальный referrer хранится только как hostname.

Первопричина, точные файлы, свежий RED и принятые границы: [план](../stages/payload/IMPLEMENTATION_PLAN.md), [diff](../stages/payload/implemented.diff). Итоговые проверки: [сводка](../verification.json), [backend](../evidence/final-backend.json), [отчёт](../REPORT.md). Историческая находка не использовалась вместо свежего воспроизведения.
