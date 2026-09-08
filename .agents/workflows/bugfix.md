# BUG

Lead: `domain owner`. Read [routing](../rules/agent-orchestration.md) and [shared contract](../rules/audit-contract.md); specialist details come from registry definitions.

Reproduce safely → classify NEW REGRESSION/baseline/environment → systematic root cause → concrete plan → approval → minimal fix → original trigger and regressions.

Verification: Do not edit assertions for green; record exact failing snapshot/command and not-run scope.

Output: scoped evidence/plan, exact tested snapshot and handoff. First audit returns findings only; stop for MASTER_AUDIT decision, never auto-fix.

Support: integration-reviewer; security-reviewer при trust boundary; остальные только по impact.

Use [engineering contract](../rules/engineering-contract.md) for graph-first discovery, exact snapshot and compact handoff. Existing authorization persists; approval is required only when the concrete scope is not already authorized.
