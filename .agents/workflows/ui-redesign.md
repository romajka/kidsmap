# UI REDESIGN

Lead: `frontend-admin or frontend-reviewer`. Read [routing](../rules/agent-orchestration.md) and [shared contract](../rules/audit-contract.md); specialist details come from registry definitions.

Read server contracts → choose admin/public owner → UI plan → approval → scoped presentation work → QA round-trip → browser-qa on local fixtures.

Verification: AZ/RU/EN,390/768/1024/1280/1440; serious UI also 320/360, keyboard/focus/dialog/errors; do not invent readiness/price/schedule semantics in JS.

Output: scoped evidence/plan, exact tested snapshot and handoff. First audit returns findings only; stop for MASTER_AUDIT decision, never auto-fix.

Support: django-reviewer для form/domain; seo-reviewer и analytics-reviewer для public links/CTA; integration-reviewer → browser-qa.

Use [engineering contract](../rules/engineering-contract.md) for graph-first discovery, exact snapshot and compact handoff. Existing authorization persists; approval is required only when the concrete scope is not already authorized.
