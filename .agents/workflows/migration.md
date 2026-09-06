# DB MIGRATION

Lead: `database-reviewer`. Read [routing](../rules/agent-orchestration.md) and [shared contract](../rules/audit-contract.md); specialist details come from registry definitions.

CODE+DB+MIGRATIONS+BEHAVIOR audit → classify legacy/manual_review → plan → isolated idempotent dry-run/rollback/checkpoint → verified backup → explicit user approval → apply → verify.

Verification: Current task stops at audit. Unknown price/email ownership cannot be guessed; no production DML/DDL or fake migration.

Output: scoped evidence/plan, exact tested snapshot and handoff. First audit returns findings only; stop for MASTER_AUDIT decision, never auto-fix.
