# KidsMap agent inventory and disposition

Discovery date: 2026-09-06. Scope: repository definitions, orchestration, skills and tool configuration. Baseline: 13 canonical definitions in `.agents/agents/`, plus seven byte-identical package copies in `kidsmap_extra_agents/.agents/agents/`. No files are deleted. This inventory records the design decision; the active roster is the orchestrator's routing contract.

## Discovery and runtime truth

- Canonical location: `.agents/agents/<name>/agent.md`; preserve this existing system instead of adding an unrelated parallel agents tree.
- Existing routing: `.agents/rules/agent-orchestration.md` initially describes five reviewers and post-implementation fixes. Update it for DISCOVER → AUDIT → ARCHITECTURE → DESIGN → CREATE → first read-only audits; future implementation remains PLAN → APPROVAL → IMPLEMENT.
- `.agents/skills/` holds project UI, accessibility, planning, debugging, TDD and verification instructions; definitions should reference shared knowledge rather than repeat it.
- `.agents/mcp_config.json` declares Chrome DevTools, Playwright and Context7. No Codebase Memory declaration or callable Codebase Memory tool was found. Declaration does not prove an available connection.
- `.claude/settings.json` is tool permissions metadata. `.codex` is an empty **file**, not a native agent config directory. No root `AGENTS.md` existed at discovery; the new root routing document is the repository entry point.
- Markdown definitions/frontmatter are project instructions. They do **not** automatically register native Codex subagents or grant tools, permissions, model overrides, SSH or browser access. The coordinator must load the role and pass its bounded task to available delegation tools. An inactive pointer is a routing policy, not an assumed native-loader exclusion.

## Canonical disposition

| Existing definition | Decision | Active destination / reason |
| --- | --- | --- |
| `django-reviewer` | UPDATE | Backend lead: actual models, services, controllers, forms, repositories, permissions and integration contracts |
| `database-reviewer` | UPDATE | PostgreSQL, migrations, constraints, real data usage, data-quality/legacy classification and measured query/index review |
| `data-quality-reviewer` | MERGE | Database takes DB quality/cleanup evidence; Django retains readiness/business semantics. Preserve original path as inactive compatibility pointer |
| `frontend-reviewer` | UPDATE | Public catalog/place/map/owner/account UI; separate actual admin surface |
| `browser-qa` | UPDATE | Independent rendered browser verification, localized/responsive flows and explicit unavailable checks |
| `security-reviewer` | UPDATE | Authentication/OAuth, object access, uploads/imports/private media and runtime boundaries |
| `seo-reviewer` | UPDATE | Existing SEO subsystem, indexability, localized metadata/schema, sitemap/robots and slugs |
| `analytics-reviewer` | UPDATE | Keep: substantial own tracking, referral/funnel data and GA4 reporting warrant an owner |
| `release-reviewer` | UPDATE | DevOps/release owner: observed deployment, drift, backup/restore, nginx/static/media, health and rollback |
| `integration-reviewer` | REPLACE | Reuse existing path for QA automation/integration regression owner. External-service contracts move to Django/security/analytics; this intentional scope replacement must be explicit in the definition |
| `performance-reviewer` | MERGE | Measured performance responsibility moves to database/backend/admin/public owners and shared workflow; preserve inactive pointer |
| `localization-reviewer` | MERGE | AZ/RU/EN cross-cutting checks move to frontend/admin/SEO/browser; preserve inactive pointer |
| `code-reviewer` | MERGE | Cross-domain review and contradiction handling move to orchestrator; preserve inactive pointer |

Add `kidsmap-orchestrator` for task classification, scoped delegation, phase gates, reconciliation and final evidence; add `frontend-admin` because `domain_admin/`, admin templates/static and public owner interfaces are genuinely different source surfaces.

No standalone cleanup implementer is needed: database owns the evidence/classification ledger, Django owns business semantics, orchestrator obtains approval for any future cleanup. No component is removed merely because it looks old or a graph calls it dead.

## Duplicate package disposition

SHA-256 comparison found each of the following package files identical to its canonical counterpart at discovery. Decision for **each** is MERGE into canonical routing, retain the physical package file, and do not schedule it independently:

| Package copy in `kidsmap_extra_agents/.agents/agents/` | Canonical destination |
| --- | --- |
| `analytics-reviewer/agent.md` | `.agents/agents/analytics-reviewer/agent.md` |
| `database-reviewer/agent.md` | `.agents/agents/database-reviewer/agent.md` |
| `integration-reviewer/agent.md` | `.agents/agents/integration-reviewer/agent.md` (new QA scope; package remains historical) |
| `localization-reviewer/agent.md` | Historical pointer to shared localization owners |
| `performance-reviewer/agent.md` | Historical pointer to measured performance owners |
| `release-reviewer/agent.md` | `.agents/agents/release-reviewer/agent.md` |
| `seo-reviewer/agent.md` | `.agents/agents/seo-reviewer/agent.md` |

After canonical updates, copies will no longer necessarily be identical. The package is retained historical material, not a second source of truth. Future deletion requires separate user approval and a cleanup-candidate record.

## Designed active roster: 11

`kidsmap-orchestrator`, `django-reviewer`, `database-reviewer`, `frontend-admin`, `frontend-reviewer`, `seo-reviewer`, `security-reviewer`, `integration-reviewer` (QA automation), `browser-qa`, `release-reviewer`, `analytics-reviewer`.

Count reconciliation: 13 original canonical − four inactive merged pointers + two new roles = **11 active roles**. There are **15 retained canonical directories**, of which four are inactive pointers, plus **seven preserved package copies**. Removed files: **zero**. A native runtime may impose fewer concurrency slots; execute audits in bounded waves, not simultaneous code edits.

First execution of every active role is AUDIT ONLY. Reports must record state, strengths, evidence-backed problems, debt, risks, legacy candidates, test gaps, recommendations, P0/P1/P2/P3 and unverified areas. Orchestrator reconciles duplicates, disagreements, dependencies and false positives in `MASTER_AUDIT.md`. Do not automatically fix findings, commit or push.
