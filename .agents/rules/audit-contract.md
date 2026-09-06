# Общий контракт аудита

Первый запуск active ролей — AUDIT ONLY: source/diff, read-only server/catalog/aggregate inspection, безопасные изолированные локальные проверки и запись назначенного отчёта. Никаких fixes/deletions/commit/push. Preserve prior worktree changes.

Production SQL: READ ONLY transaction, statement_timeout15–20s, lock_timeout2s. Не выгружать user/session/event payloads. Не создавать server temp DB/fixtures/backups. Не запускать SEO audit/fix/deploy/release/backup без проверки side effects. Некоторые dry-run сохраняют metadata. Browser QA на локальной copied fixture DB: production GET/JS analytics тоже может записать события. Google Cloud session вне аудита.

Local tests: DJANGO_TESTING=1, disposable DB/media, LocMem cache/email, выключенные внешние интеграции; не наследовать production DATABASE_URL/Redis. Допустимы ignored local scratch fixtures/logs; они не Git deliverables. Stubs и blocked transport явно отметить.

## Девять обязательных разделов отчёта

Начало: роль, дата, execution identity, definition path, LOCAL/PRODUCTION snapshot и scope.

1. Состояние области.
2. Сильные стороны.
3. Реальные проблемы.
4. Tech debt.
5. Risks.
6. Dead/legacy candidates со статусом, без удаления.
7. Tests gaps.
8. Recommendations.
9. P0/P1/P2/P3.

Finding: ID, environment, severity/impact, source file:line/symbol или production E1–E6, verification/reproducibility, confidence, owner/dependencies и следующий шаг. Отдельно executed / not run / blocked. Root-produced live evidence использовать с attribution; не утверждать личное подключение, если его не было. Не обязательно находить проблему в каждой области.

## Приоритеты и пределы доказательств

- P0: подтверждённая текущая критическая авария/компрометация; не назначать по одному source паттерну.
- P1: высокий риск безопасности/потери данных/ключевого контракта с конкретным trigger и evidence.
- P2: ограниченная ошибка, integration gap или обоснованный риск с явно непроверенной частью.
- P3: поддерживаемость/полировка/документация без срочной production аварии.

Source exploit surface ≠ production exploitation; gzip integrity ≠ restore; published status ≠ public visible;0rows ≠ dead code; mocked Google ≠ real OAuth; Django tests ≠ browser QA. Обосновать severity эффектом, не названием роли.

## Handoff и approval

Orchestrator сверяет дубли/противоречия/false positives в MASTER_AUDIT и cleanup-candidates. Findings не разрешают fixes. Ambiguity → manual_review, не assume-product/owner. Future destructive production: AUDIT → PLAN → DRY RUN → BACKUP → USER APPROVAL → APPLY → VERIFY. Согласованный scope не требует повторного разрешения на каждый шаг.
