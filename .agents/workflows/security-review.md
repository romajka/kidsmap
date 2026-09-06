# SECURITY

Lead: `security-reviewer`. Read [routing](../rules/agent-orchestration.md) and [shared contract](../rules/audit-contract.md); specialist details come from registry definitions.

Trace concrete trust boundary → source/isolated proof → severity/confidence/affected snapshot → plan → approval → domain fix → negative/concurrency tests where relevant.

Verification: No production attack/private downloads/secrets. Distinguish latent design risk from demonstrated exposure.

Output: scoped evidence/plan, exact tested snapshot and handoff. First audit returns findings only; stop for MASTER_AUDIT decision, never auto-fix.
