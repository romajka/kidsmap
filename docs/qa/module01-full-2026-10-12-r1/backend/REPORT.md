# ACCEPT-01 backend contracts and endpoint negatives

Role: django-reviewer, execution `/root/accept01_contracts`; definition `.agents/agents/django-reviewer/agent.md`; 2026-10-12. AUDIT ONLY, own report/probe files only. Checkout `/home/ramin/kidsmap`, branch `task33-progress`, HEAD `e4e05cc213b34e2d771ecb854901bfd016d1db51`; tracked diff empty at inspection; prior START and concurrent root/integration reports are preserved. `active_run: NONE` unchanged. PRODUCTION NOT RUN. This is bounded backend evidence, not native browser acceptance or full module PASS.

## 1. State and contract map

Actual source supersedes dated September knowledge. Owner/admin publication readiness is now shared: `services/permanent_place_rules.py:15–19` delegates to `place_readiness.evaluate_form_readiness`; the old documented divergence is historical.

| Intent | Verified AS-IS source contract | Browser acceptance implication |
|---|---|---|
| Create / save draft | `publication_forms.py:71–101` creates inactive draft base and versioned candidate; validated entered values/files still required | Save partial draft, reload and relogin; compare candidate, not incomplete live base |
| Names/descriptions/taxonomy/contacts/location/age/main and cover photo/gallery | `publication.py:18–31,305–317` whitelist + only defined immediate fields; other content candidate until review | Public approved card must retain old values through pending/rejection |
| Opening hours | `publication.py:20,305–317`: schedule/mode/structured days/localized note immediate only explicit save | Updated opening hours may be public before remaining content approval; private autosave must not apply them |
| Amount-only prices | `publication.py:305–317,344–372`: scalar amounts and unchanged-plan-shape amount edits may apply immediately; pending/new CONDITIONS gate amounts | Check amount-only separately from mode/format/conditions/title/product/role edits |
| Price mode/conditions and structural or nested plans | CONDITIONS line21; `_immediate` and `propose` gate; nested pricing not immediate whitelist | Compare old approved prices until review; amount edits while conditions pending remain gated |
| Submit/reject/resubmit/approve | `publication.py:320–424`: atomic actor/target/revision locking; rejection nonblank reason; approval rechecks author authority, dependencies, schema, changed fields, source snapshot/readiness | Use moderation hub native form with reason/version; old live survives reject |
| New publication vs existing live | `publication.py:401–411`: new/nonpublic readiness check; existing published compatibility explicit | Existing live compatibility is not permission to create incomplete new live content |
| Two tabs | `publication_forms.py:10–39` signed live snapshot/dependencies/source token; `publication.py:329–338` candidate CAS | Open both before first save; stale second save must refuse, keep input, never overwrite first |
| Autosave retry/recovery | `server_drafts.py:71–120`, `server_draft_api.py:15–103`: actor-private UUID, source/schema/expected version, exact retry idempotence,409 submitted_fields | Lost response/retry same UUID should not duplicate; stale update must visibly conflict |
| Photo explicit-save retry | `photo_views.py:74–134` authenticated request UUID, cache single-flight409/success retry reuse, normalized budget/action/controller | Double submit/lost response through native save-photos transport; cache behavior distinct from DB CAS |

Opening hours are Place schedule days/intervals (`place_schedule.py:300–450,514–650`), with regular/always_open/by_appointment/variable/events modes (`models/place.py:29–39`). Lesson timetable is OfferingGroup.schedule_text (`publication.py:307`) and activities/groups/nested pricing, not Place opening-hours semantics. Unknown/nonregular open status returns unknown rather than confirmed closed (`place_schedule.py:616–627`). Price modes are tariffs/free/free_entry_paid_services/events (`models/place.py:41–49`); kind/currency/product/charge-role are independent plan dimensions.

## 2. Strengths

Fresh source confirms canonical object-bound permissions and publication pipeline. `business_team.py:42–121` re-reads active actors/current targets/current grants; informational affiliation and null-place legacy grants do not authorize network edits. `place_access.py:52–76` creator fallback ends on handover; owner does not gain publish. `publication.py:151–161,320–424` rechecks ACL inside write/review boundary. Price normalizer/replacement/projection (`pricing_plans.py:184,297,603`) and schedule validator/sync are shared consumers.

## 3. Real problems

No confirmed new application finding in this bounded source/negative-probe scope. Runtime outcome recorded below when completed. This does not close gallery file corpus, native UI transitions or full role matrix.

## 4. Tech debt

Graph coverage best-effort. Full generation `2026-10-12T05:58:46Z`, metadata match/no recorded issue for publication/publication_forms/place_access/server_draft_api. Index metadata inventory truncated; template parse partial and ignored scratch remain gaps. `get_architecture`, `search_graph(propose)`, `trace_path` inbound found20 callsites; publication route/form wiring checked in exact source. Three exploratory trace parameter errors corrected; no application effect. No dead-code inference from graph absence.

## 5. Risks and storage boundary

Private ServerDraft photo storage is outside MEDIA_ROOT (`server_drafts.py:125–132`), served via actor-authorized endpoint. Form candidate main/gallery images are stored in normal media (`publication_forms.py:38–49,112–133`); no automatic claim that possession of such a URL is private. Candidate gallery DB rows/order remain gated; `publication.py:183–197` rejects foreign/duplicate IDs/missing upload and `:292–299` applies keep/delete after approval. `photo_gallery.py:10–19` requires exact nonduplicate order coverage. Direct-public-storage privacy is a separate boundary; no actual secret/photo disclosure proven here.

## 6. Dead/legacy candidates

None proposed for deletion. Scalar price fallback/projections and existing-live readiness compatibility remain intentional live consumers; do not remove based on old docs.

## 7. Checks and gaps

Own backend probes use PostgreSQL TEST DB `test_accept01_backend_20261012_r1` on owned START loopback PG, no root UI DB writes. Own LocMem cache/media/private-media/email, fresh root ACCEPT locale manifest verified before django.setup with sole LOCALE_PATHS, env allowlist/DJANGO_TESTING=1, no .env loading, external socket connect/connect_ex denied. Fictional fixture ORM is setup, not evidence of native UI save. Assertions/readback occur inside disposable test transactions; no production/read-only-server contact.

Exact command: `.venv/bin/python docs/qa/module01-full-2026-10-12-r1/backend/run_probes.py > docs/qa/module01-full-2026-10-12-r1/backend/probes.txt 2>&1`.

Attempt1 exit1: 10 tests,10 FAIL in own preservation comparator because freshly-created fixture scalar integers differ from DB Decimal serialization after refresh. All source values equal semantically; own QA setup repaired by refreshing fixture before baseline. Existing tests/assertions/application files untouched. Raw `probes-attempt1.txt` retained; no application regression claim.

Final outcome: exit0,10 tests PASS,0FAIL/0ERROR/0SKIP in2.066s; Django check0 issues. Own TEST DB destroyed by runner; root UI/START DB and server untouched. [Exact output](probes.txt). All endpoint/service negatives described above freshly reproduced; this is test-client/service evidence, not native browser transitions.

NOT RUN by this agent: native UI lifecycle; rendered18-cell state/role matrix; full Django/JS corpus (integration reviewer owns separately); all gallery formats/budget/corruption/order/delete UI; genuine concurrency races; browser lost-response/network recovery; live providers/GPS/screenreader/production. Source classification does not substitute for these.

## 8. Recommendations / named handoff

Root kidsmap-orchestrator/browser-qa: exercise the real owner → draft/reload/relogin → error/correction → submit → hub reject reason → resubmit → hub approve → public → published edit workflow. Use real UI sends, exact candidate/live comparison and stale second-tab preservation. Endpoint source expected outcomes: foreign owner edit GET/POST302 denial redirect, save-photos403 with valid UUID, thumbnail404, gallery-delete302 denial redirect; private draft UUID foreign403 vs nonexistent404; stale draft409 includes submitted_fields; current owner publish/draft302 denial, unchanged live. Platform publication active staff+change_place only (`business_team.py:42–49`).

Integration-reviewer: reuse this endpoint evidence; independently evaluate configured corpus/discovery and group/pricing/schedule/photo impacted consumers, never infer full suite from custom10 probes.

## 9. Priority

No new P0/P1/P2/P3 application ID assigned here. Full ACCEPT remains dependent on root/browser/integration evidence and explicit NOT RUN. No application fixes, commit/push/deploy, foreign process stops, active_run writes or production access.

## Follow-up: native recovery and tariff selectors (source-only)

Requested by root after native edits. `static/js/owner_place_continuous.js:11–18,75–117`: `draft_current=1` changes only browser localStorage key by appending `:current`; it does not force canonical publication candidate or bypass ServerDraft. Conflict action `[data-pc-conflict-actions] a` opens another tab and retains `draft_id` (`:39–48`), preserving old input in the original key. No native discard button exists in this continuous form.

To inspect canonical server-rendered candidate without overriding original input: native navigate to current edit URL with `?draft_current=1&fresh=1`, without `draft_id`, only when its `:current` local key is absent. `restore()` returns early for fresh1 and no local copy (`:80`). If a `:current` copy exists too, preserve original tabs/evidence and use a separate isolated browser context, native login, edit URL `?fresh=1`; do not delete storage or manipulate hidden versions. Plain fresh1 with existing same-key local copy still restores it.

Draft POST (`:127`) uses HTML `sourceVersion` and `expected_version=draftVersion`; stale409 halts and preserves browser copy. Server exact matching UUID/create retry version1 expected0 is idempotent (`server_drafts.py:100–110`); subsequent updates require current version. Explicit form/photo save marks associated ServerDraft materialized, excluding it from future resume (`server_drafts.py:198–217`, JS`:94–100`), and clears only the view's local key on success (`JS:290`). A permanently unsaved status requires browser/network evidence before assigning a finding.

Native tariff selectors: expand collapsed `.owner-tariff-row.is-collapsed` via first edit button in `.owner-tariff-actions` or row click; then click `.owner-tariff-row.is-expanded details.owner-tariff-advanced > summary` (RU «Дополнительные условия», AZ «Əlavə şərtlər», EN «Additional terms»). First select in that details is price kind exact/free/from/range/on_request (`owner_pricing_plans.js:1104–1140`). Kind change rerenders controls, so resolve locators again; details-open state is retained. Min/max appear as numeric inputs within the advanced grid after from/range selection. CORRECTION after root actual DOM inspection: current owner continuous renders NO price_mode field or policy buttons. `permanent_place_wizard.py:234–248` tariff step contains no fields; continuous template inserts only nested/direct editors. Shared JS lookup of id_price_mode is therefore null on this consumer. Owner-native free/events/free_entry policy coverage unavailable through that control; verify admin separately, and do not mutate pricing JSON or inject a selector. Earlier selector advice was incorrect for this consumer. This paragraph is source navigation, not browser PASS.

### Follow-up: explicit-photo CAS and saved-photo promotion

Root fresh native two-tabs test reports first valid save succeeds, stale second save-photos422 with errors.__all__ Candidate version conflict; source agrees: `owner_places_controller.py:745–750` attaches caught publication ValidationError to form; `photo_views.py:117–120` maps every result.form error to422. This transport differs from private draft409. `owner_place_continuous.js:198` localizes Candidate version conflict in rendered error summary, so response English alone is not untranslated UI proof. However explicit-save failure `:290` does showErrors and setStatus(error), without halted=true/conflict state; `setStatus` hides current-copy recovery action except conflict. Retry may repeat stale token. Potential recovery finding requires root native screenshot/retry evidence; candidate/live remains protected. No finding ID assigned here independently.

Saved gallery promotion `permanent_place_photos.js:205–222` materializes selected and previous-main files via sequential fetch/blob, busy>0 throughout. Save during this period returns local wait errors at`:225`, without HTTP send; this is not endpoint422. Root must separate pseudo422 harness from genuine request/response. After busy0, errors could involve saved filename/content format mismatch because materialize creates File with item.name and fetched blob type; currently a hypothesis, not defect evidence. Gallery max10 comes rules.maxGallery; existing photos count. Native add rejects when length reaches max (`:196`) while backend slots equal10-existing+deleted (`forms.py:1690–1698`).
