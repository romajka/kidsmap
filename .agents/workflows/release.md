# RELEASE

Lead: `release-reviewer`. Read [routing](../rules/agent-orchestration.md) and [shared contract](../rules/audit-contract.md); specialist details come from registry definitions.

Exact reviewed revision/diff → tests/schema preflight → recoverable backup/known previous image/rollback compatibility → explicit user approval → deploy/migrate/static → verify → documented recovery if needed.

Verification: Audit authorization never permits release. deploy-server/backup/release commands are not read-only; inspect them instead. Existing Google release remains paused.

Output: scoped evidence/plan, exact tested snapshot and handoff. First audit returns findings only; stop for MASTER_AUDIT decision, never auto-fix.

Support: database-reviewer → security-reviewer → integration-reviewer; browser-qa для smoke; orchestrator для итогового handoff.

Use [engineering contract](../rules/engineering-contract.md) for graph-first discovery, exact snapshot and compact handoff. Existing authorization persists; approval is required only when the concrete scope is not already authorized.
