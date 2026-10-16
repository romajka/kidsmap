# Module06 public map and filters Implementation Plan

> Execution: sequential in this chat; targeted verification after each patch, one module corpus, no commit/push/deploy/production.

**Goal:** close PUBLIC-QA-01/02/04 and accept PUBLIC-QA-03 on fresh isolated locales, then perform ACCEPT-06.
**Architecture:** preserve catalog filtering, map membership, grouping, publication and ACL. Repair popup geometry, SDK lifecycle and responsive stacking in existing public presentation layer.
**Tech Stack:** existing Django SSR, vanilla JS/CSS, native Chromium. External map SDK is SIMULATED, never production keys.
**Spec:** docs/qa/module06-2026-10-10-r1/FINDINGS.md and ACCEPT-06 in continuation guide.

## Snapshot and authorization
Checkout /home/ramin/kidsmap, branch task33-progress, HEAD e4e05cc213b34e2d771ecb854901bfd016d1db51 + preserved dirty WORKTREE, active_run NONE.
User requested entire module06 through local acceptance. User approved this exact plan through request_user_input_async: Да, одобряю весь этот план. PUBLIC-QA-01/02/04 and the three application files are APPROVED IMPLEMENT; PUBLIC03 fresh locale check and ACCEPT06 included.
Own run docs/qa/module06-full-2026-10-14-r1, unique loopback PostgreSQL/cache/media/private media/email and browser session. No checkout .env loaded; external network blocked.

## Exact application files
- static/js/catalog_map.js: PUBLIC01 geometry and PUBLIC02 failure/timeout/retry lifecycle.
- static/css/pages/catalog_places.css: PUBLIC01 bounded scrollable desktop card and PUBLIC04 stacking context only while responsive drawer is open.
- src/catalog/templates/catalog/place_list.html: PUBLIC02 SDK error hook and localized error/retry labels, using existing language-specific data attributes.
No site.css, models, migrations, business rules, permissions, existing tests, PO translations or shared MO overwrite planned. Fresh PO compilation is QA-only. New cause requiring other application files needs a separate bounded supplement.

## Tasks
- [x] PUBLIC01: retain failing native popup/close recheck. Limit desktop card height to actual map height minus padding; clamp top after side selection; contain scrolling while close remains reachable. Keep mobile, marker selection/motion/focus behavior. Verify RU/AZ/EN x360/390/768/1024/1280/1440, long shared venue, native close/Escape/focus, resize and late repositioning.
- [x] PUBLIC02: retain configured dummy SDK transport failure recheck. Add explicit script-error handling and bounded wait; error/status plus keyboard-accessible retry in current map area, preserve list and close. Retry replaces only failed SDK attempt, guards stale errors/timeouts and duplicate initialization; valid late callback recovers, initialized map is not rebuilt. Use RU/AZ/EN data labels consistent with existing template. Check abort, bounded timeout, retry failure/success, late callback, repeated open/close and duplicate markers/listeners using SIMULATED adapter; native transitions only.
- [x] PUBLIC04: retain native hit-test/category click RED matrix. Remove layout stacking context only under open responsive drawer with sufficient specificity; preserve desktop normal hero, backdrop, sticky header, map. Verify native pointer, keyboard, Escape/Tab/Shift+Tab, scroll and drawer open/close matrix and combined filters/reload.
- [x] PUBLIC03: compile current RU/AZ/EN PO using existing isolated helper; verify manifest and sole LOCALE_PATHS before Django setup. Verify unchanged section-switch tests plus native language selector/mobile/desktop labels. No patch if fresh catalogs resolve historic ignored-MO defect.
- [x] ACCEPT06: explicit backend labels and discovery counts for catalog/search/map/home/public filters/visibility/details/events/living map; one module corpus, targeted affected repeats only when actual source changes. Native home/lists/details/search/filter/sort/pagination/Back/Forward/reload, exact same-group matching, list/count/map, shared/coincident/missing points, private exclusion, admin save/reload/public/cache changes, gallery/contact/empty/failure, all18 language-width cells. Record limitations rather than global PASS.
- [x] Reviewable incoming-to-final diff, exact commands/exits/counts, runtime/source/locale match, PNG hashes, preserved foreign WORKTREE/active_run/stands, ID status and bounded NOT RUN. Update only module06 status after acceptance.

## Existing recheck evidence
pointer-final.result.json: actual native interception by hero at affected mobile widths.
map-geometry.result.json: negative desktop top/card560/map400 and native close timeout on all12 desktop cells.
SDK fresh recheck receipt will be appended before implementation; original source has no script error hook/terminal timeout.
Historical reports retained. Production, real SDK/tiles/GPS, real devices/screen reader/global corpus and other modules NOT RUN.

## Supplement PUBLIC-QA-05 — marker Escape propagation (APPROVED)
Fresh SDK recovery and sdk-escape-debug.result.json: first Escape closes popup and focuses marker; next Escape leaves map open. Existing marker keydown stops propagation, so catalog document handler never receives it. This is an independent existing keyboard cause, not a translation/SDK transport issue.
Exact file: static/js/catalog_map.js only. Add scoped capture handling on current map element for Escape originating from a map marker: close active popup first, otherwise close map and restore opener focus. Preserve marker Enter/Space/arrows, chooser handling and unrelated overlays. Guard current state, bind once. No marker library changes. Native reproduction against HEAD catalog_map.js with same unchanged marker library before patch; then fresh RU/AZ/EN x6 widths, popup/map Escape and repeated open/close plus retry no duplication. User explicitly approved supplement: Да, исправь и заверши 6-й модуль. Baseline HEAD route reproduction confirmed FAIL before patch.

## Verified implementation details within approved causes
PUBLIC01 also observes actual map element size (ResizeObserver, disconnected on panel replacement): window resize alone measured intermediate grid width and left the popup beyond its right edge. RED resize-probe then resize-final GREEN.
PUBLIC02 resets/clears SDK wait timer on an empty result set: real-clock empty→nonempty RED left Loading indefinitely, targeted GREEN starts a fresh bounded wait. Browser transport remains SIMULATED.
Native staff save preserves live and creates a pending candidate. Acceptance follows real reviewer approval before expecting public/cache changes; unpublish is deliberately rejected while a candidate is unresolved. No business rules/assertions changed for earlier incorrect QA expectations.

## Supplement PUBLIC-QA-06 — desktop map action labels (APPROVED)
Fresh visual review and map-action-labels.result.json: RU/AZ/EN x768/1024/1280/1440 fail, mobile360/390 PASS. Three columns reserve auto width for the phone button and leave Details/Route only50–63px including28px padding; labels extend beyond their buttons. This is independent of popup height/SDK loading.
Exact file: static/css/pages/catalog_places.css only. Scope .catalog-map-desktop-card .catalog-map-card-actions: two equal columns for Details/Route, phone reveal button on a separate full-width row. Preserve mobile, actual links/phone API, close, scroll, focus and existing business rules. Recheck same18 label-containment assertions RED→GREEN, native Details and phone reveal, popup close/scroll. No backend full rerun for CSS. Report new ID06 and actual limits. User explicitly approved: Да, исправь и заверши модуль.
QA adapter note: own map-adapter-current.js gives the simulated SDK overlay pane its own z-index0 context; this prevents fake marker-over-card overlap introduced by the old adapter. Projection, app positioning and labels are unmodified; real SDK/tiles remain NOT RUN.
