# FEATURE

Lead: `django-reviewer`. Read [routing](../rules/agent-orchestration.md) and [shared contract](../rules/audit-contract.md); specialist details come from registry definitions.

Confirm source-of-truth and exact LOCAL/PRODUCTION diff → identify DB/security/public impact → domain plan → user approval → bounded implementation → integration-reviewer regression → affected UI/SEO/browser → release only under separate explicit scope.

Verification: Existing readiness/pricing/schedule/permission invariants; no second business-logic implementation.

Output: scoped evidence/plan, exact tested snapshot and handoff. First audit returns findings only; stop for MASTER_AUDIT decision, never auto-fix.

Support: database-reviewer при DB impact; security-reviewer при auth/permissions; frontend owner, seo-reviewer при public impact; integration-reviewer; browser-qa при UI.

Use [engineering contract](../rules/engineering-contract.md) for graph-first discovery, exact snapshot and compact handoff. Existing authorization persists; approval is required only when the concrete scope is not already authorized.
