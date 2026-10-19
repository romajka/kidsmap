# ANALYTICS-QA-15 — Резервная отправка при отказе Beacon

P2; CLOSED LOCAL; LOCAL WORKTREE, production NOT RUN.

Если sendBeacon возвращаетfalse, выполняется существующий keepalive fetch. Принятый Beacon не дублируется; missing/throw ветки сохранены. Условие отказа в браузере явно SIMULATED.

Первопричина, точные файлы, свежий RED и принятые границы: [план](../stages/beacon/IMPLEMENTATION_PLAN.md), [diff](../stages/beacon/implemented.diff). Итоговые проверки: [сводка](../verification.json), [backend](../evidence/final-backend.json), [отчёт](../REPORT.md). Историческая находка не использовалась вместо свежего воспроизведения.
