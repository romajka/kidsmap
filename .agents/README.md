# KidsMap: единая команда Codex

Начать с [current snapshot](knowledge/current-snapshot.md), [source-of-truth](knowledge/source-of-truth.md), [registry](registry.json) и [engineering contract](rules/engineering-contract.md).

## Запуск

Пример: «Используй kidsmap-orchestrator. AUDIT: что затронет изменение PricingPlan? Выбери одного lead и нужную поддержку, проверь source, верни handoff без исправлений».

- `.codex/agents/*.toml` — native точки входа текущего Codex; каждая читает единственную каноническую `.agents/agents/<id>/agent.md`. Это адаптеры, не вторая система.
- Новый локальный сеанс обнаруживает TOML. В текущем runtime координатор читает definition и передаёт его доступному subagent. Наличие файла не доказывает загрузку в уже открытой сессии.
- Модель, reasoning, MCP и permissions наследуются от родителя; роль не выдаёт себе дополнительные права. Максимум три параллельных специалиста, каждый с отдельным scope/output.
- Если delegation недоступен, явно выполнить роли последовательно; не называть это независимым запуском.
- AUDIT по умолчанию. APPROVED IMPLEMENT использует уже согласованный scope; не спрашивать повторно. Эта задача разрешает только agent-system документы/конфигурацию/отчёты.

## Активный состав

|ID|Ответственность|
|---|---|
|kidsmap-orchestrator|Классификация, lead/support, проверки и сверка handoff|
|django-reviewer|Backend, pricing/schedule/readiness, owner/moderation/volunteer|
|database-reviewer|PostgreSQL, constraints/indexes, legacy/data migration/cleanup planning|
|frontend-admin|Staff/volunteer dashboard, редакторы, modal/toast, accessibility|
|frontend-reviewer|Public catalog/card/detail/map, owner/account и RU/AZ/EN|
|seo-reviewer|Indexability, metadata, schema, sitemap/robots и SEO engine|
|security-reviewer|Auth/OAuth, object ACL, uploads/import и trust boundaries|
|integration-reviewer|QA automation, инварианты, regression/baseline|
|browser-qa|Реальный DOM, console/network, responsive/focus|
|release-reviewer|Docker/nginx, preflight, backup/rollback и release|
|analytics-reviewer|Tracking/funnel/GA reporting, периоды и privacy|

Отдельные cleanup и performance роли не нужны: данные принадлежат database-reviewer, бизнес-смысл — Django; performance измеряют владельцы слоя. Analytics оставлен из-за реальной подсистемы, не ради количества.

[Inventory](../docs/agent-audits/AGENT_INVENTORY.md) хранит решения по старым ролям; четыре inactive definitions и семь package copies сохранены, не dispatch. Knowledge — общий компактный слой; workflows — семь сценариев с lead/support/order/verification. Codebase Memory проверяется в runtime и используется до широкого source exploration; graph не абсолютный источник.

[План и границы](../docs/agent-audits/TEAM_UPGRADE_PLAN.md), [проверка команды](../docs/agent-audits/TEAM_VALIDATION.md), [итог](../docs/agent-audits/MASTER_AUDIT.md). Отчёты September6 — история; сегодняшняя production версия UNKNOWN.
