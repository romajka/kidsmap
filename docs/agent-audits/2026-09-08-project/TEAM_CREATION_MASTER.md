# KidsMap engineering team — final decision artifact

2026-09-08. Task: create/update and validate the engineering team, not fix application audit findings. Coordinator `/root` applied kidsmap-orchestrator; bounded workers and execution attribution are in [TEAM_VALIDATION](TEAM_VALIDATION.md).

## Team and disposition

Keep the existing **11 active IDs**, upgrade every active definition, and provide **11 native Codex adapters** without duplicating domain instructions. [README](../../.agents/README.md) lists each role's purpose; [registry](../../.agents/registry.json) defines exact paths. [Inventory](AGENT_INVENTORY.md) records all old definitions and KEEP/UPGRADE/MERGE/REPLACE history. Four inactive definitions and seven package copies preserved, zero useful definitions removed. Empty former `.codex` file preserved in history before directory creation.

Data migration/cleanup belongs to database-reviewer with Django semantics support; performance belongs to measured layer owners. Analytics remains a separate role because tracking/GA/admin reporting form a substantial subsystem. No duplicate cleanup, performance or package agents dispatched.

## Architecture and knowledge

[Current snapshot](../../.agents/knowledge/current-snapshot.md) separates committed LOCAL HEAD, this task's agent-only WORKTREE, and unknown current production. Historical September6 observations remain dated. [Source-of-truth map](../../.agents/knowledge/source-of-truth.md) now explicitly covers price modes/validation, contacts, volunteers, admin roles, JSON import and Google OAuth alongside the other required domains.

Shared knowledge has architecture/business/database/legacy/admin/public/SEO/security/testing/deployment/analytics plus focused [pricing](../../.agents/knowledge/pricing.md), [schedule](../../.agents/knowledge/schedule.md) and [permissions](../../.agents/knowledge/permissions.md). All roles use [engineering contract](../../.agents/rules/engineering-contract.md): graph→coverage→actual source, bounded reads, CHECK→EVIDENCE→CONCLUSION, UNKNOWN, scoped implementation, concrete verification and compact handoff.

[Orchestration](../../.agents/rules/agent-orchestration.md) selects one lead and conditional support; [seven workflows](../../.agents/workflows) contain lead/support/order/verification. Every role has the 15 requested sections, exact project surfaces, safe boundaries and next-role ownership. Native adapters inherit parent model/tools/permissions; no unsupported model choice or access grant added.

## Real source findings retained as recommendations

- Owner submission and admin readiness still differ for description length, legacy schedule and non-tariff pricing. Do not teach parity as implemented or automatically merge the rules.
- Volunteer scope is implemented across groups, middleware, queryset and services, with separate pending revisions and superadmin review; public visibility is a different boundary.
- JSON UI import differs from the CSV command; schedule export is incomplete, and pricing migration signals can rewrite scalar projections. No cleanup safety inferred from docstrings.
- Current local .dockerignore excludes env files; old deployed-image findings are historical, not fresh production assertions.

No current P0/P1 production conclusion is made. These are source-backed architectural constraints/recommendations; fixes require a separate concrete scope. Agent-system gaps addressed here are P2 (missing native integration/stale scope/memory guidance) and P3 (context cost/navigation/browser matrix).

## Verification decision

Four post-update role tasks, feedback repairs and repeat checks are documented in [TEAM_VALIDATION](TEAM_VALIDATION.md), with individual A/B/C/D reports. This validates impact analysis, routing, source use and handoff within those questions; it does not establish application correctness or native cold-spawn behavior.

Coordinator read all four reports and checked the cited corrections. **A/B/C/D accepted after feedback**: correct lead, verified domain source, disjoint ownership, explicit handoff/test plan and no unauthorized action. Context efficiency was imperfect on initial A/D reads; scoped READ FIRST and projected MCP metadata were added and rechecked. This is a recorded limitation, not a claimed token-cost benchmark. B's planned command error was caught and corrected. D's favorites/markup and C's unknown-hours distinctions were checked before accepting the knowledge updates.

Final structural run: `python3 docs/agent-audits/validate_team.py` exit0 — 11 active roles, 11 native adapters, 15 required sections, seven workflows, 24 linked documents checked, zero issues. `git diff --check` exit0. `git diff --quiet HEAD -- src static templates config scripts deploy Dockerfile .dockerignore docker-compose.yml requirements.txt .github` exit0 confirms unchanged tracked application/infra surfaces; validator also checks untracked scope and retained role/package preservation. No fresh application runtime pass is claimed.

`git diff --stat`: **35 tracked paths, 393 insertions, 134 deletions**. There are additionally **25 untracked deliverable files**, including 11 native adapters, four focused/current knowledge documents, shared contract, preserved empty placeholder and validation reports/script/plan. Git's ordinary diff stat omits untracked additions; no staging was performed. The zero-byte `.codex` deletion entry is its preserved file-to-directory transition, not discarded agent content.

Scope remains definitions/knowledge/orchestration/workflows/reports only. Application changes, data operations, deploy, commit and push were not performed. Stop after team validation; application recommendations await the user's next decision.
