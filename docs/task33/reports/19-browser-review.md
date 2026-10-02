# Stage19 — independent rendered browser QA

Task / mode / authorization / snapshot: stage19 only, bounded browser-qa AUDIT of approved implementation; 2026-10-02, executor `/root/stage19_browser`, canonical `.agents/agents/browser-qa/agent.md`. LOCAL HEAD `c52b871ce5c18656a9eaf9854e66255c2629364e`; tested application is dirty WORKTREE. Ownership is this report and disposable `/tmp/task33-19-browser*` harness/artifacts. No application changes, production access, commit/push/deploy or stage20 execution.

Harness: canonical QA04 disposable PostgreSQL17, Unix socket, Docker `network=none`, tmpfs data, isolated LocMem cache/email/media and clean environment with no external credentials. Django Client bridge on loopback8799, Chromium140.0.7339.16 / cached Playwright1.55.0. Browser blocks every external origin (Google Fonts/Maps transport NOT VERIFIED). Synthetic approved ExactNetwork organization and branches; CrossGroup19 has ART8–12 and EDU4–6 on separate Activities; Matched19 has ART4–6 plus unmatched EDU4–6/ART8–12 groups; Legacy19 has no real Activity/group; synthetic favorite belongs to the local fixture account. No production records used.

Codebase Memory callable; `list_projects` confirms repository root, `index_status` ready. Catalog/home templates have partial parse coverage; source/actual DOM are authoritative. This review does not certify a complete graph coverage or production deployment.

## Baseline / intermediate evidence

- First restricted sandbox launches `/tmp/task33-19-browser-baseline` and `baseline2` did not start DB: isolation safety socket creation blocked with `PermissionError`. This is an environment failure, no application result. Escalated isolated execution was approved.
- `.venv/bin/python /tmp/task33-19-browser/launcher.py --mode probe --output /tmp/task33-19-browser-baseline3` and `node /tmp/task33-19-browser/overflow.cjs /tmp/task33-19-browser-baseline3` → exit0, QA04 PASS/cleanup PASS. RU1024 document1059 vs viewport1024 reproduces B18-04 (35px overflow).
- Fresh intermediate `/tmp/task33-19-browser-run1` matrix:147/147 HTTP200/correct locale, JS page errors0, same-origin response errors0/static4040. Five catalog surfaces had35px overflow at768/1024/1280 across3 languages (45 affected cells); home/favorites were clear. Exact ART age5 returned only Matched19; zero ART age17 empty; old price999/price_asc params preserved the correct result; approved Org query returned3 branches; general catalog retained Legacy19. Matched group card presentation was not wired at the process's initial source import, so that intermediate result is **not final acceptance evidence**.
- `node /tmp/task33-19-browser/orb.cjs /tmp/task33-19-browser-run1` → exit0. Rendered RU1024 browser A/B: overflow35 before →0 after hiding `.faq-hero-orb1,.faq-hero-orb2`. This identifies catalog hero decorative orbs as B18-04 source, rather than changed cards. UI owner added a clipped decoration container while keeping hero overflow visible for suggestions. Fresh final layout verification follows below.
- Intermediate reused bridge encountered favicon `FileResponse.content` incompatibility; reviewer corrected the disposable bridge to consume `streaming_content`. This is a harness issue, not application failure. No same-origin browser404 or page exception resulted.

## Final acceptance

Final2 fresh backend/UI snapshot `/tmp/task33-19-browser-final2`: **147/147** cells across catalog, ART/age5 matched, zero ART/age17, Org-name results, obsolete price params, home and authenticated favorites ×AZ/RU/EN ×320/360/390/768/1024/1280/1440. All HTTP200, actual locale correct, overflow0. No page JS exceptions, same-origin response errors or static404. Console236 resource messages arise from deliberately aborted external transport; actual external Fonts/Maps remain NOT VERIFIED. Full-page RU390/RU1280 screenshots for seven surfaces and focused matched-card crops were captured.

- Exact result has one Matched19 Place, one DrawingMatched19 group4–6, 25AZN only; unrelated cheaper English/older group absent. CrossGroup19 and unknown Legacy19 excluded from category+age. General catalog includes Legacy19; zero result useful and empty. Browser prices999/price_asc do not hide exact result; no budget inputs or price sort choices in any tested surface.
- Org-name results have3 unique branches, explicit Org result link and each card's Org link. Home/favorites reuse group presentation; synthetic Matched19's three groups are present in unfiltered home rails/favorite, one group in filtered results. Home renders several editorial rails; one Place in different home rails is intentional, not a duplicate catalog reader.
- Card keyboard Enter reaches detail, Back retains `category=ART&age_from=5&age_to=5`, resize390→1280 preserves one result and overflow0. Actual desktop language dropdown click RU→EN retains category/age query and one result. Focused final3 uses visible mobile-filter control, opens selected ART age5–5, Escape closes and restores focus. Org result Enter reaches Organization page; Legacy direct detail still accessible.
- B18-04 is **closed** for all147 tested cells. Scoped orb container fixed overflow without clipping the suggestions parent.

Exact commands: `.venv/bin/python /tmp/task33-19-browser/launcher.py --mode probe --output /tmp/task33-19-browser-final2`; `node /tmp/task33-19-browser/check.cjs /tmp/task33-19-browser-final2` → exit0/QA04cleanup PASS. Matrix and first focused flows succeeded; final2 script then stopped at a selector timeout selecting the first hidden duplicate mobile button. This harness error is recorded in original `results.json`, not relabeled application success. `node /tmp/task33-19-browser/assert.cjs /tmp/task33-19-browser-final2` → exit1,512 assertions pass,5 unfinished focused assertions.

Fresh `/tmp/task33-19-browser-final3`:21/21 matched cells recheck HTTP/lang/overflow0/group4–6/price25; TECH category exists in actual select even though only an Activity snapshot has TECH and its Place category is EDU. Suggestions6/6 return HTTP200: q=DrawingMatched19 gives matched25 only, q=ExactNetwork gives approved Org and3 unique branches. Mobile/Org/directLegacy focused flows passed with `:visible` selector, no JS/same-origin errors. Commands launcher `--output /tmp/task33-19-browser-final3` and `node /tmp/task33-19-browser/focused.cjs /tmp/task33-19-browser-final3` → exit0,QA04PASS/cleanupPASS. Combined final2 matrix plus final3 corrected focused evidence is explicitly attributed in final3/results.json; `node /tmp/task33-19-browser/assert.cjs /tmp/task33-19-browser-final3` → **517/517** pass,exit0.

Late API finding **B19-01**, LOCAL WORKTREE,P2,high confidence: suggestions q=DrawingMatched19 correctly price25 but still report Place6–12 instead of matched4–6; `lang=ru/en` place URLs remain default AZ while Org URLs correctly localized. Evidence final3/focused.json, source `views.catalog_search_suggestions` age_str/get_absolute_url. Sent to django-reviewer lead for scoped correction. Fresh final4 suggestion and `/catalog/new/` acceptance is pending after late consumer fix; this report does not yet claim final stage completion.

Named handoff: `/root` django-reviewer lead owns backend/card preparation and final stage disposition; `/root/stage19_ui` owns catalog/template/CSS findings. Real external Maps/Fonts/analytics delivery, physical devices, full site suite and production NOT RUN.

## Late consumer verification — final4

Fresh launcher `/tmp/task33-19-browser-final4` plus `node /tmp/task33-19-browser/new-final.cjs /tmp/task33-19-browser-final4` → exit0,QA04PASS/cleanupPASS. This browser command records observations; acceptance postprocessor `node /tmp/task33-19-browser/assert-final.cjs /tmp/task33-19-browser-final4` → exit1,157/232 assertions pass,75 fail, all in `/catalog/new/`. Main matched-card21/21 remains HTTP/lang/layout/precision PASS after timeline CSS scope change. Suggestions6/6 now use matched4–6 age, price25 and correct localized Place URLs; **B19-01 closed**. Mobile state/Escape focus, Org keyboard and legacy direct-page probes pass again. No JS or same-origin response errors.

- **B19-02,P2,LOCAL WORKTREE,high confidence rendered effect:** initial target `/catalog/new/?category=ART&age_from=5&age_to=5` yields Legacy19/Matched19/CrossGroup19 and older8–12 groups in21/21 cells. The target has both age parameters. Backend/client normalization attribution UNKNOWN because this pass did not retain final browser URL; `_build_normalized_query_params` excludes age for force_new_only, so a subsequent normalization may discard requested age. Root owns investigation; assertions were kept unchanged.
- **B19-03,P2,LOCAL WORKTREE,high confidence:** `/catalog/new/` document overflow445/701/957/949px at768/1024/1280/1440 across AZ/RU/EN (12/21). Mobile320/360/390 clear. Owner frontend-reviewer; inspect grid minimum width/parent track sizing in the rendered new-page layout. This is a distinct new-page layout finding; maincatalog B18-04 stays closed.
- Attempted timeline screenshot after QA04 had already stopped returned loopback ECONNREFUSED; no screenshot was captured and none is claimed. `/new` evidence is real Chromium DOM/layout, `final4/focused.json`, not source inference.

Final4 source11 SHA are stored in `/tmp/task33-19-browser-final4/source-sha.json`; latest consumer findings remain open pending scoped fixes and fresh `/new` acceptance. Named handoff `/root` django-reviewer for B19-02 and `/root/stage19_ui` frontend-reviewer for B19-03.

## Causal follow-up before final6

Disposable debug5 browser confirmed normalized final URL `/ru/catalog/new/?category=ART` had lost requested age. Lead identified `CleanPublicQueryMiddleware` + `PUBLIC_QUERY_PARAMS['place_new']` and `_build_normalized_query_params` age exclusion; scoped whitelist/common-normalizer/UI hidden-input fixes followed.

B19-03 real RU1024 A/B identified the hidden native sort mirror, not timeline grid/images. Native `select.results-toolbar-sort-select.visually-hidden` had width996/right1677.72: document overflow654. Image width100% and grid/card min-width0 left654. Hidden sort select width/height1px!important reduced36; removing only decorative FAQ hero orbs reduced0, with drawer untouched. Timeline grid966/cards306/images304 already fit. Lead/UI owner fixed native sort mirror dimensions and extended decorative clip scope to new-page body. Evidence `/tmp/task33-19-browser-debug5/new-overflow.json`; loopback browser A/B command `node /tmp/task33-19-browser/new-overflow.cjs /tmp/task33-19-browser-debug5` exit0, QA04cleanupPASS. Screenshot `timeline-ab-ru-1024.png` records mutated diagnostic DOM, not final UI acceptance.

Final6 fresh runtime acceptance follows; earlier failures remain historical evidence, not silently removed.


## Final review decision — final6

Fresh QA04 `/tmp/task33-19-browser-final6` after all bounded fixes: **42/42** rendered cells `/catalog/new/` and shared matched cards ×AZ/RU/EN ×320/360/390/768/1024/1280/1440 PASS. HTTP200, correct actual locale, overflow0, final URL preserves age5–5/categoryART, one Place Matched19, one group DrawingMatched19 aged4–6 and price25. Unknown Legacy19 and CrossGroup19 are absent; unrelated groups/Place age6–12/description absent. Snapshot-only TECH category option exists21/21 on each tested surface. New timeline RU390/1280 screenshots were captured and inspected: `final6/timeline-ru-390.png`, `timeline-ru-1280.png`.

Actual `/new` language dropdown RU→EN preserved age/category and one matched group. Suggestions6/6 preserve correct matched age/price and localized Place/Org URLs. Mobile visible-control open shows ART age5–5, Escape closes and restores focus; Org Enter reaches detail, Legacy direct detail remains available. JS exceptions0/same-origin response errors0. **B19-01, B19-02 and B19-03 are CLOSED**; earlier report entries remain historical and are superseded by this final6 result. Maincatalog B18-04 remains closed.

Commands: `.venv/bin/python /tmp/task33-19-browser/launcher.py --mode probe --output /tmp/task33-19-browser-final6`; `node /tmp/task33-19-browser/new-recheck.cjs /tmp/task33-19-browser-final6`; `node /tmp/task33-19-browser/assert-final6.cjs /tmp/task33-19-browser-final6` → each exit0, **275/275** final assertions PASS; QA04 PASS/child exit0/cleanup PASS. Final source hashes12/12 MATCH after browser completion. Earlier complete main matrix147/147 plus focused21/21 and517 attributed assertions still cover catalog/zero/Org/oldprice/home/favorites/back/resize/main-locale; final6 verifies the changed new consumer, common matched styles and API.

Final source SHA256 boundary (dirty WORKTREE, not HEAD):

- `src/catalog/services/catalog_search.py`: `9f2fda3818873b0a75551ed8ec4f8d7169ff474fe165d06f8c6d7080fa4cdbdd`
- `src/catalog/services/filtering.py`: `6be65b4147c74330416c7202d58b044d966d0a0f4462c6d368ca7e7cc3311012`
- `src/catalog/services/public_presentation.py`: `82064b06286d98c2747b3f18269f5463cfe50ba8f27a08b2ab92df4c0092bf99`
- `src/catalog/controllers/place_controller.py`: `48a37587b49cf82f418f26f31d55d2bb201dc0d82974c6ab7dbe253092afc7ac`
- `src/catalog/controllers/home_controller.py`: `e97396ecbbc6c58dc5914b7f02e12abfbdf630fbb30f741fe0f8fcc3405a1f13`
- `src/catalog/controllers/account_controller.py`: `31b2a74977eec34d55c7aed9e1f7db4fd86e24ab61c186a9ec6151fcf4bd4d86`
- `src/catalog/templates/catalog/place_list.html`: `357990a4acb61c8fe59755550bb7b4815d09a3df9cf852b46ce84f85a127eebf`
- `src/catalog/templates/catalog/includes/place_card.html`: `cc44e2969f668a66cff4197b46b7f5b56115a0e609b804a9ae9d70fa5961287c`
- `static/css/pages/catalog_places.css`: `276b95f113b6ad05287e1f7287f4b08849d28762138fcc6409e2544ef2e306cc`
- `src/catalog/views.py`: `e357a2164044e8c55c1db7527475b2465ea36b35888a7017315d7e879c913e87`
- `static/css/site.css`: `3f67b646cd6ee3c86d05605d4cb96cf013d82fe55389c4bc20037fe1dd9f5efd`
- `src/catalog/services/public_urls.py`: `116df05669474671fdeafa72221e7d1581723b27557595c879c163e12398e6ef`

Reviewer changed no application source, DB/schema or production state. No open browser finding in the bounded tested stage19 scope. Actual external Google Fonts/Maps/analytics delivery, physical devices, full website suite and production remain NOT RUN. External resource aborts are intentional; browser transport stubbing does not prove external integrations. Query count/timing and backend negative/concurrency behavior belong to lead/integration evidence, not this browser result.

Named final handoff: `/root` canonical django-reviewer lead to integrate this independent report, final source boundaries and remaining NOT RUN limits into reports/19.md and implementation-status. Only stage19 accepted browser scope is reviewed; no readiness claim for the whole site or production.
