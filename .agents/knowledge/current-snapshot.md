# Current verified snapshot — 2026-09-08

LOCAL HEAD at start: `d75b34f4db5d4ba484cf8392ff3ae0c9939031e2`; worktree initially clean. This task changes only agent-system files and reports. PRODUCTION now: UNKNOWN; not contacted. The September 6 live observations remain historical evidence, never current deployment facts.

## Rechecked architecture and drift

- Main Django app remains catalog with Jazzmin/moderation proxy. `src/config/settings.py:INSTALLED_APPS` now has allauth and Google provider committed. Google/wizard/photo/phone and migration0101 must no longer be called untracked. Current deployed availability is UNKNOWN.
- Volunteer workspace is implemented: `services/staff_roles.py` → `volunteer_middleware.py` → `domain_admin/volunteer.py` → `services/volunteer_places.py` → `volunteer_forms.py`, `models/volunteer.py`. [Permissions](permissions.md) owns this map.
- Owner/admin readiness conflict remains in source: `forms.py` calls `permanent_place_rules.publication_errors`; admin uses `place_readiness.evaluate_form_readiness`. Description120, regular text and non-tariff price modes differ. Existing-live compatibility and public visibility are separately intentional paths.
- JSON importer is `static/admin/js/kidsmap_place_json_import.js` plus admin normalize/form/save, not `management/commands/import_places.py` (CSV, writes). Export omits structured schedule; importer/migration signals need separate round-trip checks.
- Shared card include is used in home/catalog/account_favorites; map popups, detail and volunteer card have other markup. Shared public card currently has no schedule row; its price value is a complete formatted label and currency property is empty. Price/schedule semantics still come from backend. Admin template roots have loader precedence; volunteer workspace adds another staff surface. Consumer evidence: [D](../../docs/agent-audits/validation-D.md).
- SEO includes LocalBusiness/Offer/hours in `services/seo.py`, plus sitemap/public URLs and state-writing audit/fix subsystem. Real Event model and temporary Place coexist.
- Analytics role remains justified by FunnelEvent/SiteVisit, tracking, GA reporting and admin statistics. `admin_analytics._ga_period_key(90)` still maps to year. No external GA validation.
- Current `.dockerignore` excludes `.env` and `.env.*`. Historical active-image inclusion does not establish current local build behavior or today's deployed image.
- CI source runs PostgreSQL17/Redis, Django checks/migrations/tests and push-main deployment; browser checks not in this workflow. No fresh app suite, browser, DB introspection, CI run or production probe executed for team authoring.

## Runtime and memory

Installed local CLI: `codex-cli 0.132.0`. Official [custom-agent documentation](https://learn.chatgpt.com/docs/agent-configuration/subagents) specifies standalone `.codex/agents/*.toml` with name, description and developer_instructions. Those files load the single canonical Markdown definition, inherit parent model/tools/permissions, and do not duplicate domain rules. Discovery requires a new local session; current collaboration tools receive definitions explicitly.

Codebase Memory is callable now. `list_projects` initially empty; indexed repository with persistence=false, project `home-ramin-kidsmap`. Initial fast index reported static/docs exclusions; later validation D observed a full index with cited static assets covered. Template parse gaps still required source fallback. Neither initial exclusions nor later coverage are permanent guarantees: check mode/generation/freshness and exact paths per task. Graph artifacts and private records are not repository deliverables.

Historical knowledge pages retain dated evidence; this snapshot supersedes only their current-state assertions. Recheck source symbols before changing anything.
