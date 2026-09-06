# KidsMap orchestration

Canonical [registry](../registry.json), shared [audit contract](audit-contract.md). Старое правило автоматически исправлять findings заменено: в AUDIT исправлений нет; APPROVED IMPLEMENT ограничен согласованным scope. [Предыдущая редакция](history/agent-orchestration-before-20260906.md) сохранена как non-operative history.

## Routing matrix

|Type|Lead|Support по impact|Order|required verification|
|---|---|---|---|---|
|FEATURE|django-reviewer|DB/security/UI/SEO|domain→DB/security→QA→browser приUI|инварианты,migrations,permissions,negative/regression|
|BUG|владелец failing domain|integration-reviewer,security при trust boundary|reproduce/classify baseline→root cause→plan→approved fix→QA|exact trigger и regression|
|UI REDESIGN admin|frontend-admin|django для forms/actions,browser-qa|contracts→UI plan→approved UI→rendered|round-trip,keyboard/mobile/modals|
|UI REDESIGN public|frontend-reviewer|SEO/analytics/security|domain→UI→QA→browser|AZ/RU/EN,375/768/1024/1440,next/canonical/events|
|DB MIGRATION|database-reviewer|django/security/QA/release|usage audit→manual_review/plan→isolated dry-run→backup/approval→apply/verify|idempotency,constraints,checkpoint/rollback|
|SEO|seo-reviewer|django/frontend/security|visibility→metadata/schema→isolated QA→browser head|canonical/hreflang/robots/sitemap/JSON-LD|
|SECURITY|security-reviewer|domain owner,DB/release,QA|trace boundary→safe proof→plan→approved fix→negativeQA|input/output/storage/permissions,no prod attack|
|PERFORMANCE|измеряемого слоя owner|DB дляORM;UI дляassets;analytics дляGA;QA baseline|measure→hypothesis→plan→approved change→remeasure|representative evidence,no premature indexes|
|RELEASE|release-reviewer|DB/security/QA/orchestrator|revision→checks/backup/recovery→explicit approval→deploy→verify|image/schema/static/media/health,actual rollback|

## Concrete handoffs

- Public pricing: django-reviewer→database-reviewer приdata impact→frontend-reviewer→seo-reviewer→integration-reviewer→browser-qa.
- Migration/legacy cleanup: database-reviewer lead owns transition audit/dry-run/manual_review; django confirms semantics. No second generic cleanup role.
- Auth/OAuth/upload: django→security→QA→browser; production activation separately release-reviewer.
- Analytics: analytics-reviewer→django/frontend-admin→QA; external latency hypotheses require measurement.

## Dispatcher and cross-review

1. Name mode, exact snapshot, scope, output and existing authorization.
2. Read actual active definitions; at most3parallel specialists, disjoint writable reports. Never10agents editing app.
3. Pass definition, task/evidence, prohibitions and expected output. Discovery workers are not formal first role runs.
4. Collect executed/not-tested evidence. Invoke kidsmap-orchestrator after individual audits.
5. Merge one cause into one master ID; preserve role IDs/evidence, qualify false positives/severity and dependencies.
6. AUDIT stops at recommendations/user decisions. APPROVED IMPLEMENT changes only approved scope then runs required checks.

Inactive compatibility roles: code-reviewer→orchestrator; data-quality→database/backend; localization→UI/SEO/browser; performance→layer owners. Original content remains. Do not dispatch all11for a trivial task.
