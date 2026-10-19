# SOCIAL-QA-09 — CONFIRMED OPEN/P2, PLAN COMPLETE

Execution /root,2026-10-17 Asia/Baku. One django-reviewer lead, SEO/frontend/browser checks sequentially by same agent; canonical .agents/registry/contracts used, no independent subagents. PLAN only; application changes0, approval PENDING. LOCAL HEAD852938d96764ae315b92859e3651e5ea62054a36, branch codex/module09-transfer-2026-10-16-r1, source1023/dirty03–08 retained. Production UNKNOWN/not accessed.

## Finding / cause

Fresh own isolated runtime reproduces SOCIAL-QA-09 for guest and author across RU/AZ/EN and6widths. Actual pagination2/3 request gets301 to the same base feed without query: active page1 and first12items again. Actual select likes+Apply similarly loses sort and returns popular. Service review feed page2 is a working shared control. SeverityP2/confidenceHIGH/reproducible; no access bypass/data loss/production incident claimed.

Current source differs in class name from historical report: src/catalog/middleware.py:CleanPublicQueryMiddleware (~64–92) calls filtered_query_string_for_path before controller. src/catalog/services/public_urls.py:PUBLIC_QUERY_PARAMS owns site_reviews:{sort,page}, but lacks place_reviews. src/catalog/urls.py binds place_reviews; controllers/place_reviews_controller.py:build_context legitimately reads sort/page, normalizes sort, uses Paginator12. Current header language_switch_query uses the same shared filter. These edges verified against source, not just graph.

Proposed runtime patch: one allowlist line place_reviews:{sort,page}; plus new nine-method regression file. Unknown/next/utm still removed, only2owned keys retained. No middleware/controller/template/context/JS/CSS/PO/schema/service algorithm change. Canonical/hreflang for this feed remain base URLs without query and full current DEFAULT_ROBOTS_CONTENT; UI language switch retains allowed query. This is preservation of existing policy, not a new SEO policy or full SEO certification. Catalog default cleanup/site noindex rules remain separate.

## Current RED proof

Native36cells guest/author×RU/AZ/EN×360/390/768/1024/1280/1440:540controlPASS/216sourceFAIL. Seeded29approved fictional PlaceReview and29SiteReview, distinct literal likes/dislikes/date distributions. Real anchors/focus-Enter/page2/page3 and real sort select/submit, redirect status/Location chains, active page, exact review texts checked. Shared site page2 shows the expected different12items. All normal documents fit; business review/vote aggregates unchanged;0pageerrors/requestfailed/HTTPfailures/consoleerrors.108matrixPNG.

SEO/query probes6rows:23controlPASS/10sourceFAIL,3additionalPNG. Mixed query cleanup preserves neither legal query nor language-switch params for place feed; legacyAZ does the same. Actual desktop language menu click loses query; metadata canonical/hreflang/robots stay current base policy. Site mixed query preserves sort/page and catalog removes only redundant defaults/foreign keys. These are source failures under investigation, not application PASS.

Current candidate9unique methods:8failed/1passed,33assertion/subtest failures/0errors,1.987s,expected exit1. Covers guest/author/lang page2, pages1/2/3 exact rows,4sort choices, combinedquery/pagination href, unknowncleanup, repeated/default/legacyAZhelper, language/canonical/robots, invalid fallback, shared controls. Tests executed outside application as candidate_tests.SocialQA09FeedQueryTests; new application test path absent. AST and exact proposed.diff git apply --check --ignore-space-change exit0; candidate not applied/live rendering NOTRUN.

Two prior candidate/logs also retained: robots expected shortened index,follow though current source constant has extra directives; assertion was not reached behind301. Corrected that expectation to full existing policy before implementation approval and reran exact current candidate, same33query failures. Pagination href assertion was also made entity-independent using html.unescape, matching the existing literal ampersand template. Both corrected assertions were unreachable behind301. All three9method runs have same33query failures; current exact candidate1.987s. No app patch or weakening of query expectations; do not sum runs as27unique methods or99different defects.

## Isolation / source / limits

New own m09s09-plan-r1-app/pg/internal network/volume; Python3.12.15/Django6.0.2/PostgreSQL17.11/Chromium155.0.8059.12. RO repository bind, own scratch RW, cleared env/DJANGO_TESTING1, separate normal m09s09_plan_r1/testDB test_m09s09_plan_r1/cache/media/private-media/locmem email. Fresh native RU/AZ/EN MO/verify manifest/sole LOCALE_PATHS before setup. Owned headless browser/session/loopback33369, external browser requests blocked by localhost allowlist. Normal fixture seed finished before matrix; isolated testDB concurrency does not change normal fixtures. No POST review/vote actions or external integrations executed.

All1023source hashes unchanged and future application test absent.12previous current-PC packages bytes/manifests retained,44entrycontainer ID/names retained,+2own=46; one entry state changed: m09s04-fix-r1-app running→exited,exit0/OOMfalse. Command is Python sleep86400, so finite helper lifetime is a possible explanation; exact termination cause UNKNOWN. No stop/restart/delete command issued for this container. Raw selected state fields retained in foreign-container-state.json. Other entry states match; current own09 app/PG running/live hashes confirmed. No foreign restart; this does not establish whole-machine process continuity. HEAD/branch/index/task33-progress/active_run:NONE/sharedMO/.cbmignore preserved. Guide gets new PLAN09 note with reverse-hash proof of old bytes. No reset/clean/stash/switch/commit/push/deploy/production.

Graph C-kidsmap ready rootC:/kidsmap, generation2026-10-16T18:56:53Z/120partial files. Relevant code metadata_changed/coverage unavailable, template partial34/56/62; critical edges source reviewed. No graph completeness/deletion/cache export/reindex claim.

## Decision / next step

Exact scope public_urls.py + new test_social_qa09_feed_query.py; one-line runtime change, no migrations or new strings. IMPLEMENTATION_PLAN.md contains hashes/code/gates,9new+3affected existing tests and native/post-reload/shared/SEO acceptance. Approval required by AGENTS/guide PLAN→IMPLEMENT; previous03–08 approvals do not authorize09.

SOCIAL01–08 scoped LOCAL closures retained, SOCIAL09OPEN/P2/module09OPEN. ADJ-ANONYMOUS-LOGIN-08 remains separate OPEN/P2, not silently fixed or discarded. Implementation09/GREEN/fullACCEPT09/global/adjacent login fix/production/physical/realSR/fullWCAG/otherbrowsers/external services NOTRUN. After scoped09 the next full module acceptance must follow ACCEPT-09 explicitly; global corpus separately, no automatic module10.
