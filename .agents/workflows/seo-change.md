# SEO

Lead: `seo-reviewer`. Read [routing](../rules/agent-orchestration.md) and [shared contract](../rules/audit-contract.md); specialist details come from registry definitions.

Check visibility/model impact → canonical/hreflang/robots/sitemap/schema plan → security review of serialization → approval → changes → isolated tests/browser head.

Verification: SEO audit/fix commands may WRITE even dry-run; source/SELECT/local fixtures only during audit. No invented schema facts.

Output: scoped evidence/plan, exact tested snapshot and handoff. First audit returns findings only; stop for MASTER_AUDIT decision, never auto-fix.

Support: django-reviewer для data/visibility; frontend-reviewer; security-reviewer для serialization; integration-reviewer → browser-qa.

Use [engineering contract](../rules/engineering-contract.md) for graph-first discovery, exact snapshot and compact handoff. Existing authorization persists; approval is required only when the concrete scope is not already authorized.
