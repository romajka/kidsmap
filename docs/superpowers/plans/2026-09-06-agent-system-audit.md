# KidsMap agent system and first audit plan

**Goal:** Consolidate the existing agent system around verified local and production architecture; run every active role in audit-only mode and deliver a reconciled decision report.

**Architecture:** Root `AGENTS.md` routes to one canonical `.agents/` registry, shared knowledge, scoped role files and short workflows. Existing overlapping definitions remain preserved as documented compatibility roles, not parallel active agents. Reports live in `docs/agent-audits/`.

**Tech stack:** Django 6.0.2, PostgreSQL 17 production, Redis, nginx/Gunicorn/Docker; repository Markdown instructions and runtime subagent tools.

**Spec:** User's 33-section attachment supplied 2026-09-06, filename `pasted-text.txt` (agent-system request).

## Global constraints

- DISCOVER → AUDIT → ARCHITECTURE MAP → AGENT DESIGN → CREATE → individual READ-ONLY AUDITS → CROSS-REVIEW.
- Production: only inspection and database read-only transactions. No deploy, restart, migrations, data changes, configuration edits, cleanup or chmod/chown.
- This task may write agent definitions, knowledge, orchestration, workflows and audit reports only. Preserve all pre-existing application changes.
- No secrets, production logs/dumps or memory caches in repository deliverables. Record aggregates and references, not user identities.
- No deletions, commits or pushes. Cleanup is recommendations only.
- Existing Google OAuth activation is outside this task and paused.
- User explicitly requests specialist execution. Use bounded parallel discovery; execute newly defined roles only after shared architecture and role design exist. They may write only their assigned report.

## Execution

- [x] Inventory existing agents/rules/skills/MCP and capture the pre-task file hash manifest in ignored local scratch storage.
- [ ] Audit backend, UI/SEO/analytics, QA/infrastructure and project knowledge against source. Read-only production OS/runtime/Git/settings and PostgreSQL schema/data aggregate inspection.
- [ ] Write `.agents/knowledge/architecture.md` first; document LOCAL, PRODUCTION and stale TO-BE statements distinctly. Complete database/business/legacy/testing/SEO/security/admin/public/deployment/source-of-truth knowledge.
- [ ] Decide active roster and disposition of all existing definitions. Write `.agents/README.md`, `registry.json`, scoped `agent.md` files, `AGENTS.md`, orchestration and seven workflows; retain old paths without duplication of active responsibility.
- [ ] Invoke each active role with its actual definition and shared knowledge; preserve nine-part evidence-based reports in `docs/agent-audits/`.
- [ ] Run an independent orchestrator reconciliation: deduplicate, qualify false positives and severity, list dependencies and execution order in `MASTER_AUDIT.md`; collect cleanup candidates without executing them.
- [ ] Validate all required sections, role/knowledge/workflow references, registry uniqueness, report completeness, absence of embedded secrets, and unchanged application/server state. Display Git status and diff summary without staging, commit or push.

## Evidence and verification

- Production SQL uses `BEGIN READ ONLY`, statement/lock timeouts and catalog/aggregate SELECTs; no EXPLAIN ANALYZE on production.
- Existing test logs are labelled historical scoped evidence, not a fresh full-suite pass. Any new tests must use isolated local test storage and never production connection values.
- Browser QA uses public GET/render inspection; no production form submission or account mutation. Google Cloud login window is not touched by this audit.
- Reports include environment, source references, executed checks, not-run checks, confidence and P0–P3 with impact rationale.
- Structural validation is a task-local script; it is not an application test or a claim that Markdown files are automatically registered native agents.
