# Shared engineering contract

All active roles follow this contract in addition to the audit safety rules. Scope and existing user authorization travel with the handoff; reports are assigned by the orchestrator, not permanently fixed to a historical audit filename.

## Discover with bounded context

1. Check callable Codebase Memory tools, then `list_projects`; choose the current repository, verify root/freshness with `index_status`. If absent, index with `persistence=false`; never add graph caches to Git. Project tool responses can be large: project only root/status/generation and relevant coverage gaps into context; do not echo the whole index inventory. Pagination/coverage limitations must remain visible.
2. Use `get_architecture` once for broad discovery; `search_graph` for symbols, `trace_path` for callers/callees/impact, and routes/module relationships as relevant. Check pagination; narrow broad results before paging.
3. READ FIRST is a navigation list, not an instruction to read every listed document fully. Always read current snapshot, shared contracts and relevant source-map rows; read architecture fully once per broad task, then only the domain sections and specialized knowledge required by impact. The map's actual path is `.agents/knowledge/source-of-truth.md`. Check index coverage for cited paths and scopes behind negative claims. Static/docs may be excluded; templates may be partially parsed.
4. Verify critical conclusions in actual source and route/template/command wiring. Use `rg` for literal/template/static/config searches and uncovered paths. Graph absence never proves dead code.
5. If tools are unavailable, state UNKNOWN/unavailable and use bounded source search. Do not reinstall MCP or reread the entire repository for every handoff.

## Evidence and implementation

CHECK → EVIDENCE → CONCLUSION. Cite snapshot and file:symbol/line. Distinguish LOCAL HEAD, dirty WORKTREE and PRODUCTION. Historical observations do not establish today's runtime. AS-IS is verified implementation; TO-BE and PLANNED remain proposals. Unknown facts are UNKNOWN, not guesses.

Discover → Impact → concrete Plan → Implement only within existing approved scope → Verify → Handoff. AUDIT skips implementation and stops at recommendations. Agent-system maintenance permits definitions/knowledge/workflows/reports only. No application fixes in this task.

Backend remains final validator. Draft, submit, publication, public visibility and UI completeness are distinct contracts; check their actual differences. Never reproduce business enums/rules manually in JavaScript. Legacy/identity ambiguity → manual_review. Risk outside scope → STOP / ESCALATE, preserving completed authorized work.

Tests require DJANGO_TESTING=1 plus disposable DB/cache/media/email and disabled external integrations. Record exact command, snapshot, exit/counts and NOT RUN scope. Distinguish REGRESSION, PRE-EXISTING BASELINE FAILURE and ENVIRONMENT FAILURE; historical failures need reproduction before attribution. Never change assertions merely for green.

## Compact handoff

Task / mode / authorization / snapshot:
Changed (or none):
Evidence (files/symbols, commands, graph gaps):
Business impact:
DB impact:
Security impact:
Tests executed / not run:
UNKNOWN / manual_review / risks:
Needs next (named role, bounded question, acceptance check):

Receiving agent verifies the cited boundary and snapshot, reuses proven evidence, and expands only for gaps or changed source. Audit reports use the nine audit sections when conducting a full domain audit; a bounded impact task uses this compact handoff.

## Browser acceptance

For affected UI: AZ/RU/EN; widths 390, 768, 1024, 1280, 1440; serious redesign also 320/360. Check actual DOM, console, network/static404, horizontal overflow, icons/ligatures, focus/keyboard, dropdown/sticky/modal/toast/forms and error/loading/empty states. Source inspection and jsdom are not rendered browser evidence. Use isolated fixtures, not production actions that emit tracking or save data.
