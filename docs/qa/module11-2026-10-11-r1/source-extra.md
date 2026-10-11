# Module 11 — source supplement and HEAD comparison

Task: bounded follow-up to the lead's fresh native observations, **AUDIT ONLY**. Role seo-reviewer, actual definition .agents/agents/seo-reviewer/agent.md; shared contracts and parent authorization retained. Assigned ownership **only source-extra.md and source-extra-map.json**. Other source/evidence/scripts/run/state were preserved.

Snapshot: C:/kidsmap, task33-progress, HEAD **8d188b316f800fbedf0b1e376905dfd4924cb1b6**; source checked **2026-10-11 09:54 UTC**. Fifteen cited repository files match their HEAD Git blobs, including staged changes in the comparison (`git diff HEAD`). Source/worktree SHA256 and blob IDs are in source-extra-map.json. This is a scoped comparison; it does not say the entire dirty checkout is clean. Installed dependency Django6.0.2/Jazzmin3.0.1 confirmed from local dist-info metadata, not external internet. Four dependency-file SHA256 values recorded. Runtime/active_run/full app digest remains the lead's attestation.

Codebase Memory refreshed: selected C-kidsmap; symbol search returned36 selected nodes with has_more=false. Coverage14 exact files plus the previously covered urls.py path (source-map.json), generation2026-10-11T09:51:18Z; all metadata_changed, five public templates partial. Actual source overrides graph hints. No index installation/reindex/export.

## 1. CatalogContentSettings editor500: precise causal source

**Native finding is attributed to /root**, not independently reproduced by this source specialist: GET /admin/catalog/catalogcontentsettings/1/change/ returns500 with `__str__ returned non-string (type __proxy__)`.

- src/catalog/models/site.py:10 imports **gettext_lazy as _**.
- src/catalog/models/site.py:784–785, CatalogContentSettings.__str__: returns `_("Контент каталога")`, a lazy proxy, without coercion to str.
- Installed Django .venv/Lib/site-packages/django/contrib/admin/options.py:1911 constructs changeform context `"subtitle": str(obj) if obj else None` before custom render_change_form. Python's __str__ contract requires a string; returning the lazy proxy causes the supplied error.
- src/catalog/domain_admin/site.py:1092–1125 exposes existing singleton editor/seo_pages_json; its custom render cannot bypass the earlier stock changeform str(obj) call.

Classification: source cause present unchanged in LOCAL HEAD and current reviewed WORKTREE; **pre-existing baseline source**, not introduced by this audit. Runtime reproduction/date is fresh only through root evidence. This blocks genuine UI editing/rename of SEO landing JSON; dependent native landing-rename workflow remains **NOT RUN** until a future scoped fix.

Suggested owner/dependencies: **django-reviewer**, frontend-admin checks editor/error rendering; SEO landing save/read schema is downstream. Suggested P2: one admin configuration editor unavailable, public landing pages may remain functional. No DB schema/migration change implied. Scope for later repair: model __str__ string contract plus actual changeform regression and native render under AZ/RU/EN; retain lazy model verbose_name where valid. No code changed.

No matching existing ID found in the bounded historical module03/08/10 findings inspected. Historical search is a checklist/dedup aid, not fresh500 evidence or exhaustive proof of novelty.

## 2. Specialist checkboxes: false-positive correction, no module11 defect

Initial lead observation: all29 specialization inputs carried required, unchecked inputs failed checkValidity,0 POST after attempted Save. Source explains **attributes**, while the initial claimed native validation blocker was wrong.

Confirmed source chain:

1. src/catalog/models/specialist.py:143 declares ManyToMany specializations without blank=True: model/form requires a **nonempty selection**, not every specialization.
2. src/catalog/domain_admin/specialist.py:28–32 SpecialistAdminForm.Meta uses standard **CheckboxSelectMultiple**.
3. Installed Django admin/options.py:212 wraps the M2M widget in **RelatedFieldWidgetWrapper**; admin/widgets.py:262 wrapper inherits Widget and does not delegate use_required_attribute to the inner checkbox widget.
4. forms/widgets.py:364 base Widget.use_required_attribute returns not is_hidden; forms/boundfield.py:270–291 therefore passes required=True for the required wrapped field.
5. admin/widgets.py:349 renders inner widget with these attrs, yielding required on each input. The inner CheckboxSelectMultiple itself explicitly returns False from use_required_attribute at forms/widgets.py:943–946, but outer wrapper has already supplied attrs.
6. src/catalog/templates/admin/catalog/specialist/change_form.html:7 has **novalidate**. Native submit does not enforce browser required checkboxes.
7. static/admin/js/specialist_admin.js has navigation/status/search/error ARIA handlers, no required assignment or checkValidity submit gate in the reviewed source.

**Root correction received2026-10-11:** rendered form.noValidate=true; actual button raises normal confirmation dialog; Playwright auto-dismissed it, causing0POST. With dialog.accept the request POSTed200 and showed the expected server error because the initial legacy fixture had both/onsite format without a practice location. Lead corrects only the QA context/dialog acceptance and fills the actual practice-place control, then continues the native save. No application fix is warranted by the checkbox observation.

Separately, the earlier event-specialist.js clickSave helper called every control.checkValidity() before clicking and returned false on those checkbox attributes. That preflight was **QA harness logic**, not application submission. specialist-rename.result.txt was a later10-second waitForResponse timeout; it does not by itself prove browser validation blocked POST. The source supplement has not rewritten either lead artifact.

Disposition: **EXCLUDED FALSE POSITIVE / QA HARNESS** for module11; no SEO-QA ID, no severity. Native name/slug saves resume after fixture requirements and dialogs are handled. The required-attribute quirk can affect validity APIs, but no independent current application impact is established here.

Historical nearest: **MOD-QA-07** is a different bug (server error summary iterates an AdminField HTML string into characters) and remains separate. Its earlier native submit path accepted the confirmation then reached server validation. **SPEC-QA-01/02/03** are document corruption/photo conflict/mobile clipping, not this checkbox hypothesis. Historical records are not reused as fresh PASS.

## 3. Editable Specialist slug: source boundary; native outcome pending lead

- src/catalog/domain_admin/specialist.py:769 includes **slug** in editable fieldsets; readonly_fields at:456 does not include it, form Meta fields="__all__".
- src/catalog/models/specialist.py:136 defines unique slug;:230–243 builds public URL from slug and only creates a new slug when the current one is empty. Ordinary name rename preserves existing slug.
- src/catalog/views.py:2868/2881 resolves public Specialist with exact slug + published + active; no old-slug redirect lookup in this handler.
- src/catalog/urls.py:262 uses /specialists/<slug>/ rather than a stable ID+slug path. No alias/history model or resolver was found in the bounded current Specialist routing/save sources.

Source is unchanged from HEAD. Therefore explicitly changing an editable slug has a source-supported risk of old-link404; **confirmed defect status still requires root's genuine UI save → reload → old URL → new URL**, including all AZ/RU/EN shells. Do not use direct ORM-save as proof. Do not merge with normal name rename.

Owner/dependencies: **seo-reviewer + django-reviewer**, frontend-admin for explicit slug editing/validation. Potential P2 if existing public inbound links fail after a supported edit. Future scoped policy may retain canonical identity or resolve historical slugs; no implementation chosen here, no migration assumed.

## 4. Generic Open Graph/Twitter: exact blocks and corrected Place image scope

**Runtime observations attributed to root:** fixture entity pages expose generic descriptions; after native Event photo upload/reload the visible entity photo changes while OG still uses site logo. This specialist only verified source and HEAD equivalence.

Base src/catalog/templates/base.html:

- :29 OG title uses title_plain fallback KidsMap;:34 Twitter title uses title_plain_twitter fallback KidsMap.
- :30 OG description uses **og_description / meta_description_og**, distinct from normal **meta_description** at:15.
- :35 Twitter description uses **twitter_description / meta_description_twitter**, also distinct.
- :32/:36 OG/Twitter image defaults to site-settings logo or static logo; it does not automatically use entity photo.

Actual child templates:

| Entity | Title overrides | Description override | Images |
|---|---|---|---|
| Place | place_detail.html:4–6 normal+OG/Twitter title supplied | :7 only normal meta_description; OG/Twitter description stays base generic | **:9 AND :10 override both OG image and Twitter image with seo_image_url** |
| Organization/Activity | public_entity_detail.html:3–5 normal+OG/Twitter title | :6 only normal meta_description | base logo |
| Event | event_detail.html:4–6 normal+OG/Twitter title | :7 only normal meta_description | base logo; visible photo at:22–23 reads event.photo.url |
| Specialist | specialist_detail.html:5 only normal title | :6 only normal meta_description | base logo; OG/Twitter title also falls back KidsMap |

This **corrects a mistake in initial source-review hypothesis1**: Place Twitter image does not remain logo. Both Place social-image blocks already exist. Retain only the actual generic-description finding for Place and any separately verified fixture-specific image failure. Old source-review/source-map artifacts are preserved; this supplement takes precedence for that assertion.

All listed templates and seo.py compare equal to HEAD in this scoped review. Source cause: child blocks populate normal metadata but don't override separate social blocks; entity image context is not consumed by base fallback. Browser bot behavior, external link unfurling and real search-engine indexing remain NOT RUN. A local visual preview must be explicitly labeled SIMULATED preview if the lead renders one.

Suggested owner/dependencies: **frontend-reviewer + seo-reviewer**, django-reviewer for approved/fallback content-image semantics; shared base and child templates. Generic descriptions across five entity kinds share one cause and should normally be consolidated rather than five duplicate defects. Missing Specialist social title and Event/Org/Activity social images can be distinct triggers with shared implementation dependency. Final IDs/severity/dedup belong to lead's verified runtime evidence.

## Executed / not run and named handoff

Executed: canonical role/contracts retained; current source/installed-framework source, graph symbol/coverage, HEAD/worktree Git blob comparison15/15 match; dependency metadata and4 hashes; bounded historical dedup search; read root's two QA helpers/result files for attribution correction. Exact read-only commands represented in source-extra-map.json. Source inspection had an early missing guessed specialist_proposals.py path and a wrong rg -ErrorAction invocation; neither produced app evidence or caused writes. Actual cited source exists and was read.

**NOT RUN by specialist:** browser/HTTP, fixtures/DB, test suite/management commands, source execution, external integrations, commits/push/deploy. Runtime claims are root-attributed; no independent reproduction claimed. Only the two assigned supplement files were created. No application or assertion changes.

Named handoff **kidsmap-orchestrator → integration-reviewer/browser-qa**: exclude checkbox false positive; verify native Specialist edit with accepted dialog and lawful practice location, then old/new slug URLs. Keep CatalogContentSettings editor500 as baseline/root-reproduced with source cause. Consolidate actual social-metadata symptoms and apply the corrected Place image boundary. **django-reviewer** owns __str__/slug identity semantics; **frontend-reviewer/seo-reviewer** own social blocks with approved-content fallback. Findings do not authorize implementation.



