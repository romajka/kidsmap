# Модуль07 — план свежего аудита

AUDIT ONLY. Один /root последовательно выполняет orchestrator/security/frontend/browser обязанности. Ownership: только docs/qa/module07-2026-10-10-r1, свой ignored scratch/контейнер/HTTP/browser и строка07. Без application/rules/migration/assertion edits, production/commit/push/deploy. Исторические отчёты только checklist.

- [x] Snapshot HEAD/WORKTREE/active_run/source hashes; canonical docs и graph/source auth/access map.
- [x] Новый PG55438/HTTP8820; DJANGO_TESTING=1, отдельные DB/testDB/cache/media/private-media/email/cookies и вымышленные роли/объекты.
- [x] Native registration/confirmation/login/logout/reset/profile; invalid/duplicate/normalized data, replay/expired tokens, CSRF/redirect/session, локальные OAuth ошибки. Email и tokens только ignored scratch/in-memory, без внешней интеграции.
- [x] Native Place team invite/accept/reject/cancel/role/remove и открытая вкладка; Organization API contract отдельно от наличия UI. Матрица роль×действие×сущность и denial HTTP/no-side-effects.
- [x] Account deletion native request/confirm/cancel; собственный delete fixture lifecycle по implemented flow. Private docs/consent/download/media/cache, IDs/owner/role scopes.
- [x] Native RU/AZ/EN ×360/390/768/1024/1280/1440, empty/filled/error/loading/modal/keyboard/long text/geometry/console/network и PNG.
- [x] Unchanged targeted tests/native exits; findings ACCESS-QA с отдельными repair prompts, nine-section report, matrix/evidence/PNG hashes/limitations. Final source/runtime/foreign preservation; строка07 и handoff08. Модуль13 последним.

Завершено как AUDIT DONE — FAIL. Ограничения/NOT RUN в REPORT.md и coverage-gaps.json; пять P2 не исправлялись. Final verification exit0.
