# KidsMap agent entry point

Use [.agents/README.md](.agents/README.md), [.agents/registry.json](.agents/registry.json) and the actual definition of `kidsmap-orchestrator`. This is the single canonical system; do not dispatch duplicate package or inactive compatibility roles.

- Read [architecture](.agents/knowledge/architecture.md), [source-of-truth](.agents/knowledge/source-of-truth.md) and [audit contract](.agents/rules/audit-contract.md). Verify source; distinguish LOCAL HEAD, dirty WORKTREE and PRODUCTION.
- Workflow: DISCOVER → AUDIT → ARCHITECTURE MAP → ROLE DESIGN → READ-ONLY AUDITS. Future implementation requires a concrete plan and user approval for its scope. Existing authorization persists; do not request it repeatedly.
- The2026-09-06 agent-system task authorizes definitions, knowledge, orchestration, workflows and reports only. No application fixes/deletions/commit/push. Earlier Google deployment work is paused by this audit scope.
- Production strictly read-only: no data/schema/config/env changes, migration/deploy/restart/backup scripts/cleanup. Some SEO audit and dry-run commands write. SQL uses explicit read-only transactions and timeouts.
- Never print/copy secrets, env values, user-level records, production logs/dumps or graph caches into repository artifacts. Use aggregates/booleans/source references.
- One lead, minimal support; at most3parallel specialists with disjoint report ownership. Load the real role file before spawning available runtime subagents. If delegation is unavailable, say so and run named roles sequentially; do not claim independent execution.
- Active roles are registry.active. Retained compatibility definitions and `kidsmap_extra_agents` copies are historical, not extra active workers.
- Tests require DJANGO_TESTING=1, isolated DB/cache/media and no production credentials. Report exact commands/snapshot/failures/not-tested scope; no assertion changes merely to obtain green.
- Use applicable existing skills; user instructions take precedence. UI rules/source inspection are not rendered-browser evidence.

Routing: [agent-orchestration](.agents/rules/agent-orchestration.md). Final audit decision artifact: [MASTER_AUDIT](docs/agent-audits/MASTER_AUDIT.md). Stop at recommendations and await the user's decision before implementing findings.
