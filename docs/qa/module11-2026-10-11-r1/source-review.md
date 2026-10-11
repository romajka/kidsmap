# Module 11 — bounded SEO source handoff

Role: `seo-reviewer`; definition: `.agents/agents/seo-reviewer/agent.md`. Mode **AUDIT ONLY**, authorized support task. Read-only source/graph discovery; ownership only this file and `source-map.json`. Application, assertions, fixtures, DB, existing evidence and journal were not changed by this specialist.

Snapshot: **C:/kidsmap**, branch **task33-progress**, HEAD **8d188b316f800fbedf0b1e376905dfd4924cb1b6**, source read **2026-10-11 09:19 UTC**. Dirty WORKTREE belongs to the parent snapshot; production/runtime/active_run attestation is the lead's responsibility. The 56 current source hashes in `source-map.json` delimit this source review. If those files drift, recheck the affected contract. Historical knowledge was navigation only.

## Memory freshness and scope

Codebase Memory is callable in this run. `list_projects({})` selected `C-kidsmap`, root C:/kidsmap; git metadata matches HEAD/branch. Initial full generation was 2026-10-10T16:47:47Z, latest coverage generation 2026-10-11T09:18:17Z. Recording is truncated (initial ignored inventory 11385 total / 2000 stored). Coverage checked 39 initial exact paths plus 17 source/test supplements (56 total): every file reports **metadata_changed**, 5 templates report partial parsing. The src/catalog scope listed76 coverage gaps; pagination10+66 completed, src/config1 gap completed. Direct source fallback covers every cited implementation. Full graph correspondence to WORKTREE is **UNKNOWN**. No forced reindex/install/cache export.

Graph `search_graph` found 5 selected SEO symbols, `trace_path` found 15 inbound callers/tests for build_place_seo_payload; no pagination remained. Initial regex file_pattern returned no nodes: not treated as absence. Architecture scoped routes/entry-points supplied no useful route inventory. All contracts below are verified directly in current files; template/dynamic Django/ORM relationships use source fallback.

## Actual routes and identity

| Entity | Route/name and handler | Rename/slug contract |
|---|---|---|
| Place | `src/catalog/urls.py:251` /place/<pk>-<str:slug>/, place_detail; views.py:393 | `place_urls.py:34` + Place.save (models/place.py:627) initializes missing per-language slugs under locked previous row, ignores supplied replacement. Rename keeps saved slugs. Flag-off uses legacy slug; flag-on uses populated localized slug. Wrong/current-old slug and query => permanent redirect after public-state fetch. |
| Place legacy | urls.py:250 /place/<pk>/; :269 root <pk>-<slug>; views.py:388 | PK identifies current entity, single direct 301 expected to current language path. No slug history required because PK remains. Query dropped by detail path. |
| Organization | urls.py:103 /organizations/<uuid:public_id>/, controllers/public_details.py:17 | Immutable UUID identity (models/catalog_structure.py:87–88), no name slug. Rename should keep URL. |
| Activity | urls.py:104 /activities/<pk>/, public_details.py:179 | PK identity; approved inheritance/local text affects content, not route. Program itself has no public detail route; embedded in Organization and Activity. |
| Specialist | urls.py:262 /specialists/<slug>/, views.py:2868 | Unique slug-only identity. models/specialist.py:234 generates only when empty; rename does not auto-change a populated slug. Current handler exact slug lookup, no alias resolver found. Explicit slug edits need separate URL policy verification. |
| Event | urls.py:255 /event/<pk>-<str:slug>/, views.py:1295 | PK + populated slug, models/place.py:998 generates only empty slug. Wrong slug 301 after is_public; repeated ordinary rename should retain saved slug. Query cleanup middleware can precede this redirect. |
| SEO landing | urls.py:147 /catalog/<seo_slug>/, SeoController.build_landing_context (controllers/seo_controller.py:26) | CatalogContentSettings.seo_pages (models/site.py:765): optional per-language config, fallback content_data. Actual base/district landing pages are content_data.py:158–327 (e.g. kruzhki-v-baku, dzudo-dlya-detey-v-baku). No alias/history redirect registry found in the inspected handler. |

News/articles: direct search across all Python in **src/catalog and src/config**, plus public route/model wiring, found no News/Article model, news_detail/article_detail, news/ or articles/ routes. This is bounded current source absence, not a claim about uninspected external services. `og:type=article` for Place is Open Graph classification, not an articles module.

## Language, metadata and visibility contracts

- `src/config/urls.py:54`: i18n_patterns, default AZ unprefixed; RU /ru and EN /en. Legacy default-language prefix route at :48 → config/views.py:136 returns 301 to unprefixed path with only route-owned params.
- `src/config/settings.py:65`: LOCALIZED_PLACE_URLS_ENABLED defaults to **DEBUG and not TESTING**. An isolated DJANGO_TESTING=1 stand must explicitly record intended flag; test both flags without calling its own default production behavior.
- `public_urls.py:13`: route-specific query allowlist; place_list page=1 and sort=new removed only when a single exact default. `middleware.py:63` skips private paths/POST, combines slash/query cleanup; Place detail routes defer cleanup to handler to avoid extra hop.
- `context_processors.py:125` builds canonical, hreflang, x-default, language navigation. Place and Organization/Activity set _seo_place/_seo_entity; `public_languages.py:9` includes RU/EN only when name+description are actually translated; Activity also requires any supplement in that language and resolves current approved Program/snapshot source. Fallback-content canonical becomes AZ while navigation language_urls retains all shells. Displayed fallback is not persisted translation.
- Generic pages, Specialist and Event currently have no _seo_entity binding here; they receive generic configured-language alternates. Verify runtime content/locale claim separately.
- `context_processors.py:179`: private listed URL names noindex; route queries noindex according to QUERY_NOINDEX_URL_NAMES. Catalog valid page-only pagination uses effective rendered page canonical, indexable only if input exactly agrees; filters use stable sorted query canonical and noindex. Other lists must be checked against their actual contract rather than copying catalog policy.
- `base.html:14–35`: title, description, robots/googlebot, canonical/alternates/x-default, Open Graph/Twitter. HTML autoescaping applies. Context supplies absolute public origin from public_urls.py:45. Requested local configured PUBLIC_BASE_URL must be recorded; do not call a different origin a code bug.
- `seo.py:16`: JSON-LD serializer escapes <, > and & as Unicode escapes, preserving parsed data. All reviewed generated schema payloads use it. Historical script-termination finding must be rechecked fresh; source indicates an implemented protection.
- `seo.py:370`: Place LocalBusiness uses approved present reader/canonical content language, actual offers/hours/geo, omitted hours/offers for approved closed operating state. Temporary Place is still LocalBusiness; Event has a separate current payload at :590.
- `seo.py:542`: Organization/Course schema uses same approved presentation. Current provider link appears only when present() exposes active approved Organization. `public_presentation.py:208` only uses approved current Program or permitted detached snapshot, never candidate revisions.
- Event schema uses approved occurrence context (EventScheduled/Cancelled/Rescheduled, actual start/end with Baku timezone, online VirtualLocation, validated finite physical coordinates, organizer/reviews/previousStartDate). Do not infer nonexistent price/image claims: runtime payload must be compared with actual public facts.
- Place SSR detail and legacy resolve **published_place_queryset** (place_controller.py:677/680 → content_quality.py:361), which only requires published/active/not deleted. Catalog and sitemap use stricter **public_place_queryset** (content_quality.py:241): quality/price/schedule/contact/age, temporary flag and expiry, approved closed-state exclusion. Published legacy detail visibility and catalog visibility are distinct; mismatch alone is not automatic privacy evidence.
- Organization published/approved/unarchived, Activity published/unarchived + active published undeleted parent: public_presentation.py:35; controllers/public_details.py checks present.visible before payload. Event disabled section yields empty410 and otherwise published/undeleted/positive start-end; past/cancelled remain public by is_public (models/place.py:963). Specialist disabled section404, otherwise published+active.
- `config/urls.py:21` sitemap registry: static, places, organizations, activities, seo, specialists; **no EventSitemap registration**. Place/Org/Activity per-item languages use available_languages. Specialist uses all configured languages and status+active; SEO landing index threshold **5 matching public places in every configured language** (seo_landing_visibility.py:15/122) and common slug.
- Robots is config/views.py:76 with private section/language disallows and canonical sitemap; dedicated admin-host robots allows crawling public redirects while disallowing admin. Host middleware CanonicalPublicHostMiddleware/AdminHostRedirectMiddleware must be tested under isolated local host simulation only.

## Commands and indirect writes — current source

| Entry | Side effect from current code | Audit disposition |
|---|---|---|
| audit_seo | SEOAuditEngine.run_audit, seo_audit_engine.py:49 creates run; :68 deletes old issues for non-targeted audit; :83 creates issues; :100 persists totals. Uses Django Client, not browser/upstream. | NOT RUN by specialist; not read-only. |
| apply_seo_fixes --apply | seo_fix_engine.py:75 Place save, :110 SEOChange create, :123/:127 change/issue updates, :39 cache.clear; HTTP recheck can trigger app writes. | NOT RUN; outside app-fix authorization. |
| apply_seo_fixes dry-run | **Current** seo_fix_engine.py:98 returns unsaved SEOChange before create/recheck/status/cache clear. Historical doc says dry-run writes, which does not match this version's explicit branch. Query/model access remains; no execution in this support task. | NOT RUN; source-only side-effect classification. |
| rollback_seo_change | seo_fix_engine.py:157 saves Place, :163/:167 change/issue writes; command invokes rollback. | NOT RUN. |
| seo_report | Existing SEO aggregate/history ORM reads, stdout only in reviewed handle. | NOT RUN; avoid copying private issue payloads. |
| audit_sitemap / --check-live | Django Client sitemap render; live option means Client page GET, not external browser. No direct DML in handle, but SiteSettings.get_solo may create defaults and public handlers can track/refresh ratings. | NOT RUN; use isolated custom probes. |
| SEO admin buttons/actions | domain_admin/seo.py:61 audit, :81 apply, :100 delete, :313/:322 issue save, :377 rollback. | NOT RUN. |
| public GET/render | Place/Specialist rating mismatch refresh; Org/Activity track_subject_view subject events if LOCAL_ANALYTICS_STORAGE_ENABLED. | Lead must keep DB/cache/media/email isolated; GET is not inherently a production read-only proof. |
| IndexNow | apps imports indexnow_signals; indexnow.py:39 enabled by nonempty key, not automatically disabled by TESTING. Public model saves can enqueue external transport when enabled. | Explicit blank synthetic key and outbound block; real IndexNow/Search Console NOT RUN. |

## Hypotheses for fresh reproduction (not confirmed defects)

No SEO-QA ID assigned by source review; source is insufficient for browser/functional acceptance.

1. Event/Org/Activity templates override meta_description but not meta_description_og/twitter_description or og_image; Specialist overrides only title/meta_description and retains base OG/Twitter title/schema. Place overrides OG image but retains generic OG/Twitter descriptions and Twitter logo. Compare server head and browser preview across all languages with distinct fixture name/description/photo. Sources: base.html:29–35, detail templates' opening blocks.
2. Event and Specialist generic hreflang might advertise fallback-only translations unlike Place/Org/Activity. Empty RU/EN versus actually complete translations; compare shell lang, canonical, schema name/description, locale, alternates and sitemap reciprocal links. Canonical source policy may intentionally differ; report actual effect.
3. Published Event absent from sitemap while detail is public. Verify positive fixture, disabled flag and current XML first; missing sitemap is an integration gap only if required contract supports inclusion.
4. Event wrong slug + forbidden query may require cleanup301 then slug301; Place explicitly avoids that second hop. Test /az legacy prefix variants, slash, original/renamed entity and multiple rename; graph/middleware patterns do not prove loops.
5. Activity parent can pass soft visible() but fail strict public_place_queryset used by ActivitySitemap. Check published incomplete, closed, expired-temporary and disabled-event parent independently. Retained legacy direct access must be separated from unauthorized/candidate exposure.
6. SEO landing rename/admin slug replacement may404 the old configured slug because handler has no alias registry. Only confirm after genuine UI save/reload if editing exists; stable static slugs do not constitute rename failure.
7. Place build_detail_context builds SEO **before** mismatch rating refresh (place_controller.py:742/749). With deliberately inconsistent fixture aggregates, compare first response JSON-LD rating and visible review count, then reload. This is a hypothesis; no data mutation performed here.
8. Explicit Specialist slug edits may orphan previous slug URL; ordinary name rename does not. Distinguish exposed editable field policy from unsupported direct ORM mutation before assigning failure.

## Existing targeted tests — inspected, not executed here

Safe local labels (must use lead's disposable isolated settings/DB; no assertions modified):

- catalog.testcases.test_localized_place_urls — stable rename/injected slug/partial save/new translation/concurrent first translation/flag-off.
- catalog.testcases.test_localized_place_seo — direct wrong-slug+query redirects, hidden slug non-disclosure, metadata/sitemap, localized notification units (mocked).
- catalog.testcases.test_seo_indexability — catalog pagination/defaults/filters stable canonical, admin/public robots/host redirects.
- catalog.testcases.test_json_ld_serialization — script containment and exact parsed names.
- catalog.testcases.test_seo_landing_visibility —0/4/5 threshold with sitemap/internal links and query budget.
- catalog.testcases.test_judo_seo_landing — data/localization/query aggregates.
- catalog.testcases.test_task33_public_details — approved text/inheritance/detach, hidden parent/candidate isolation, links.
- catalog.testcases.test_task33_event_public — past/cancelled/rescheduled/online/organizer/schema script-safety/review isolation.
- catalog.testcases.test_place_json_and_pricing_modes.PlaceSchemaOrgSeoTests — hours, free/from Offer, temporary Place semantics.
- catalog.testcases.test_organization_directory — no private org/branch photo leaks, filter/sitemap/navigation.
- catalog.testcases.test_seo_audit_system — current dry-run0DML, apply/rollback commands mutate only test DB. Review invocation boundary before selecting it; explicit task forbids application fixes, even on audit stand except own QA fixtures.

Integration labels are evidence of existing assertions, not passing tests. Test execution result is **NOT RUN** by this support role. No independent browser/HTTP/DB/environment validation; production, search-engine indexing/rich-results/IndexNow are UNKNOWN/NOT RUN.

## Executed checks and handoff

Read AGENTS.md, canonical role/registry/contracts, current snapshot/navigation/source map, relevant pricing/schedule/security/public/business knowledge. Source/route/model/command inspection, literal search, Codebase Memory symbol/coverage/trace, 56 SHA256 hashes. Git HEAD/branch exit0; source reads/searches exit0 unless intentionally no-match. News/articles bounded search exact command below exit1/no matches (expected search result, not test failure). One early rg attempted outdated guessed paths (public_views, specialist_controller, models/organization, models/activity) and reported missing files; actual implementations were located through imports and read. Those guessed paths are not required project documents and were not substituted as evidence. No subprocess tests or management commands were started.

Representative exact commands (PowerShell, C:/kidsmap):

```powershell
git rev-parse HEAD
git branch --show-current
rg -n -i 'class (News|Article)|news_detail|article_detail|news/|articles/' src/catalog src/config -g '*.py'
rg -n '^(class|def) |canonical|redirect|hreflang|sitemap|seo' src/catalog/services/public_urls.py src/catalog/context_processors.py src/catalog/middleware.py src/catalog/sitemaps.py src/catalog/services/seo.py src/catalog/urls.py src/config/urls.py
rg -n '^class |^    def test_' src/catalog/testcases/test_localized_place_urls.py src/catalog/testcases/test_localized_place_seo.py src/catalog/testcases/test_seo_indexability.py src/catalog/testcases/test_json_ld_serialization.py src/catalog/testcases/test_seo_landing_visibility.py src/catalog/testcases/test_judo_seo_landing.py src/catalog/testcases/test_task33_event_schema.py src/catalog/testcases/test_task33_public_details.py
Get-FileHash -LiteralPath <each source-map.json path> -Algorithm SHA256
```

Changed: only two assigned QA handoff files. Business impact: identity/canonical/visibility boundaries mapped; no behavioral change. DB impact: none by specialist; indirect write points identified for lead's safe stand. Security impact: serializer/hidden-state paths reviewed, fresh hostile metadata/script containment still required.

**Named next: kidsmap-orchestrator → browser-qa/integration-reviewer.** Use current source hashes/parent snapshot, run independent isolated HTTP/head/sitemap and native rendered-browser paths for the hypotheses, record rendered reload and saved UI changes. Escalate confirmed raw-text/external URL behavior to **security-reviewer**, business visibility ambiguity to **django-reviewer**. No confirmed finding from source review; no full module PASS implied.



