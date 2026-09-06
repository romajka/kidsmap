# KidsMap: единая система специалистов

Начать с [architecture](knowledge/architecture.md), [source-of-truth](knowledge/source-of-truth.md), [registry](registry.json). [Inventory](../docs/agent-audits/AGENT_INVENTORY.md) объясняет disposition всех13existing+7duplicate definitions.

## Как запускать

Корневой AGENTS.md направляет к11active ролям. Orchestrator читает `.agents/agents/<id>/agent.md` и передаёт его инструкции доступному runtime subagent вместе с task/snapshot/scope/output. **Markdown сам не регистрирует native agents и не подключает MCP.** Registry — проектный routing contract, не неподтверждённая конфигурация Codex API.

Пример: «Используй kidsmap-orchestrator из .agents, режим AUDIT. Проверь owner pricing, выбери нужных специалистов, сохрани доказательства без исправления кода». Orchestrator выбирает Django/DB/public/SEO/QA по impact и задаёт каждому отдельный report path. При отсутствии subagent tools роли выполняются последовательно с честной маркировкой ограничений.

Первый запуск active ролей использует новые определения; discovery не считается formal audit. [RUN_LOG](../docs/agent-audits/RUN_LOG.md) фиксирует реальные запуски. Orchestrator cross-review идёт после индивидуальных отчётов.

## Активный состав

|ID|Основная ответственность|
|---|---|
|kidsmap-orchestrator|Routing/scope/cross-review/приоритеты|
|django-reviewer|Backend/domain contracts|
|database-reviewer|PG integrity, migrations/legacy, DB performance|
|frontend-admin|Admin presentation/accessibility|
|frontend-reviewer|Public/owner/account UI|
|seo-reviewer|Indexability/metadata/schema/SEO subsystem|
|security-reviewer|Auth/permissions/input/output/storage/secrets|
|integration-reviewer|QA automation/invariants/baseline/CI|
|browser-qa|Actual rendered browser behavior|
|release-reviewer|Infrastructure/release/recovery|
|analytics-reviewer|GA/funnel/events/privacy/reporting|

Performance покрывают владельцы слоя; localization — UI/SEO/browser; data-quality — backend+DB. В agents/15directories:11active и4retained inactive; ничего не удалено. Семь копий `kidsmap_extra_agents` сохранены и не образуют второй реестр.

knowledge/ содержит компактные общие факты; rules/ — audit contract/routing; workflows/ — семь коротких последовательностей; skills/ сохранён. MCP config декларирует Chrome DevTools/Playwright/Context7, availability проверяется в runtime; Codebase Memory на срезе не подключён. Пустой root `.codex` сохранён, native directory configuration поверх него не создавалась.
