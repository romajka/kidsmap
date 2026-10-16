# Module03 — source preflight and concrete plan

2026-10-13, root sequential, PLAN ONLY.

Checkout `/home/ramin/kidsmap`, branch `task33-progress`, HEAD `e4e05cc213b34e2d771ecb854901bfd016d1db51`, dirty WORKTREE, active_run NONE. [snapshot.json](snapshot.json) hashes22268 pre-existing nonignored files; contains only paths/hashes/status, no environment credentials.

Read actual AGENTS/canonical registry/orchestrator/architecture/source-of-truth/audit-contract and relevant skills. Verified three historical findings against current source, not runtime:

- SPEC-QA-01: upload_document checks size/suffix only before writing. Caller graph includes certificates UI and profile document batch. Existing security/workspace upload fixtures contain fake PDF prefixes, which must become genuine fictional PDFs without changing assertions.
- SPEC-QA-02: CAS throws before full_clean; form.add_error triggers clean; OwnerSpecialistForm normalizes persisted FieldFile; template reads mutated instance.photo.url. Proposed bounded fix only normalizes new uploads in this form.
- SPEC-QA-03: broad8px/overflow-hidden descendant rule applies to header/nav markup; narrow to actual progress track.

Graph has template parse gaps; actual lines read. Inbound traversal pages completed. Counts prove source navigation, not behavior acceptance.

Concrete plan: [2026-10-13-module03-spec-qa01-03.md](../../superpowers/plans/2026-10-13-module03-spec-qa01-03.md). Needs approval of this exact file/scope. Three IDs remain OPEN. No application edits, dependency installation, runtime startup, DB writes, browser transitions or tests yet. Runtime RED, regression GREEN, full ACCEPT-03: NOT RUN. Historical PASS/FAIL remain historical.

Existing WORKTREE/active_run/stands left untouched. No commit/push/deploy/production.

## Subsequent approved execution

All planned repairs and two explicitly approved supplemental scopes are now LOCAL accepted. Final source-bound evidence: [module03-full report](../module03-full-2026-10-13-r1/REPORT.md). The PLAN ONLY / NOT RUN statements above describe this preflight checkpoint.
