# Stage20 — independent rendered browser review

Task / mode / authorization / snapshot: stage20 only, browser-qa AUDIT of approved implementation, executor `/root/stage20_browser`, canonical `.agents/agents/browser-qa/agent.md`; 2026-10-02. LOCAL HEAD `c52b871ce5c18656a9eaf9854e66255c2629364e`; app under test is dirty WORKTREE, not HEAD. Owned this report and disposable `/tmp/task33-20-browser*` harness/artifacts only. No application fixes, production access, schema changes, commit/push/deploy.

Harness: unchanged QA04 isolated PostgreSQL17 with Docker network=none/tmpfs data/Unix socket; clean environment, LocMem cache/email, temporary media, no production credentials. Django Client loopback8799 synthetic fixture bridge; cached Playwright1.55.0/real Chromium. All external origins aborted. Explicit **Google Maps transport double**, actual application marker/overlay/popup code; dummy cluster transport has no cluster geometry. Real Maps/CDN/tile/service delivery **NOT RUN**. Synthetic confirmed Location has SharedArt20 and SharedEdu20 independent Place records, Nearby20 standalone at nearby coordinates, NoCoords20 null coords and InvalidCoords20 legacy invalid coords injected only into disposable fixture. ART4–6 price25, EDU4–6 price30; unmatched cheaper EDU8–12 price1 belongs to SharedArt20.

Codebase Memory callable; root current project verified. Catalog JS best-effort coverage; home JS changed metadata and catalog template partial parsing, so actual source/DOM used. Coverage/freshness gaps do not prove missing code.

## Executed

- ` .venv/bin/python /tmp/task33-20-browser/launcher.py --mode probe --output /tmp/task33-20-browser-prep1` → restricted environment failure, isolation safety socket PermissionError; no application result or DB started. Isolated escalated launches authorized.
- `run1/run2` setup failed before browser because synthetic invalid coords normal save hit district validation and Activity fixture lacked canonical approved Organization membership. Harness corrected; no application failure attribution.
- `run3` rendered first-cell shared grouping assertion failed because fixture assigned venue while changing address in same ordinary save. New application boundary correctly cleared association. Fixture now saves address then explicitly confirms Location. Base QA public places disabled only in disposable fixture to isolate expected map members/media.
- Fresh `run4` launcher and `node /tmp/task33-20-browser/check.cjs /tmp/task33-20-browser-run4`: **105/105** rendered cells catalog, exactART/age5, exactEDU/age5, zeroART/age17, home ×AZ/RU/EN ×320/360/390/768/1024/1280/1440. HTTP200/correct actual locale/overflow0. Catalog keeps two independent shared cards and null/invalid-coordinate list entries; one shared point has two members, nearby point has separate identity; invalid/null no phantom pin. ART exact has one member/group and25; EDU exact gives SharedEdu20; zero map empty. Home shared member payload consistent. **550 assertions succeeded**, JS exceptions0/same-origin HTTPerrors0/static4040.
- run4 focused real keyboard Enter opened shared catalog popup with both business names; route CTA includes only coordinate destination. Escape closed popup and restored marker focus. Original browser command then exited1 at pointer activation timeout: fake no-cluster Nearby marker overlaps Shared marker (3.6px fake separation), so pointer delivery intercepted. This is explicitly a transport-double geometry limitation, not a confirmed app issue. Original failed JSON retained; final focused run uses actual keyboard activation, never force-click or weaker data assertions.

## Final focused catalog acceptance

Fresh `final5`: `.venv/bin/python /tmp/task33-20-browser/launcher.py --mode probe --output /tmp/task33-20-browser-final5`; `node /tmp/task33-20-browser/final.cjs /tmp/task33-20-browser-final5` → browser exit0, **134/134** assertions PASS. Latest source21/21 exact matched cells HTTP/lang/overflow0/filter member25. Catalog2 marker buttons =1 shared venue +1 standalone Nearby. Shared popup displays both business links, backend matched offers/groups, localized fallback disclosure. Keyboard Enter/Escape restores marker focus. Resize1280→390 keeps shared member popup and overflow0. Actual transport unavailable retains all5 list cards/layout0; Google loader text remains loading because external script was deliberately aborted. RU390/1280 screenshots captured and RU390 inspected. Source11/11 SHA identical from final5 start to final6 current snapshot.

Initial home `?q=NoMatchUnique20` hypothesis: real browser normalized301 to `/ru/`, with map/form present; home query unsupported by existing URL policy, not a genuine initial zero-map trigger. No whitelist/wrapper change requested from review. AJAX zero/reset remains the relevant tested user flow.

`final5` home followup initially failed vendor InfoWindow fake `shouldFocus` omission; corrected transport double to emulate vendor focus. `final6`: home Enter shared popup/Escape/restore focus3/3 PASS, then hidden native select activation timed out. This was a harness selector issue; final7 uses the actual visible category dropdown. Post-cleanup console probe returned loopback refusal; no console evidence claimed from it. Original failed records retained. Final home acceptance follows below.

Business impact: verified venue membership does not collapse independent cards or Nearby Place identity; exact map members follow server filters. DB lifecycle/Event snapshot behavior belongs to lead's isolated backend evidence, not this browser claim. Security: route privacy and no external tracking/integrations in harness; direct phone reveal/ACL negative tests NOT RUN here.

Named handoff: `/root` frontend-reviewer lead integrates final browser evidence with backend/independent review and stage20 status. Actual external Maps/clustering/Fonts, physical devices, whole-site/full suite and production NOT RUN.

## Home final7 and console finding

Fresh `final7` launcher plus `node /tmp/task33-20-browser/deep.cjs /tmp/task33-20-browser-final7` → exit0, **31/31** assertions PASS acrossAZ/RU/EN. Actual visible category dropdownART updates live businesses3→2; age6 chip pressed=true updates2→1; unmatched search AJAX produces0 while map survives; reset restores3 and clears category/age/query. Home shared popup Enter displays both businesses; Escape closes and restores marker focus. Actual localized map API exactART age5 returns1 point/member, price25 and excludesHiddenCheap unmatched offering. JS exceptions0; QA04 childexit0/cleanupPASS. Source11/11 remains identical final5→final7.

**B20-01,P3,LOCAL dirty WORKTREE,high confidence:** home shared popup console reports malformed `<polyline>` clock SVG6 times/3 locales. Source `static/js/home_map.js:renderMemberPopupContent`, `points="12 6 12 16 14"` has odd5 numbers. Chromium diagnostic location points to vendor transport fake where application popup HTML is inserted; actual application markup source verified directly. Owner `/root/stage20_home` / lead. Sent scoped correction; finalconsole recheck pending. Three external Google Fonts resource errors are expected aborted transport and remain separate. Original console recorded in `/tmp/task33-20-browser-final7/deep.json`; no claim of clean browser console yet.


## Final review disposition — final8

B20-01 corrected by home owner: clock polyline now `12 6 12 12 16 14`. Fresh `.venv/bin/python /tmp/task33-20-browser/launcher.py --mode probe --output /tmp/task33-20-browser-final8`; `node /tmp/task33-20-browser/final8.cjs /tmp/task33-20-browser-final8` → each exit0, **47/47** assertions PASS over9 actual home popup cases AZ/RU/EN ×320/390/1280. Both business members visible in popup text, schedule SVG valid, document overflow0, Enter/Escape/marker focus correct. JS exceptions0, **application console errors0**, expected external Fonts abort messages9. QA04 childexit0/statusPASS/cleanupPASS. **B20-01 CLOSED**. Source11/11 hashes unchanged between final8 start/end; only home_map clock SVG changed from final7, so earlier complete105-cell/focused134/home31 evidence remains applicable with this exact bounded late change and fresh focused recheck.

Browser acceptance in bounded stage20 scope **PASS**, no remaining confirmed finding. Google transport double supports application HTML/focus/response synchronization testing, not actual Google InfoWindow chrome, third-party service, cluster algorithm geometry, route navigation, map key validity or production readiness. Real cluster/tile/CDN integration, external Fonts, physical devices, backend event/lifecycle invariants and whole-site suite NOT RUN here. Lead owns integration with independent backend133/46 and final stage disposition.

Final dirty source SHA256 (not HEAD; report does not hash itself):

- `static/js/catalog_map.js`: `f19b089b1a7efb86617d2ffec9fac14737d7fba49819d681dc1430d99ed102b8`
- `static/js/home_map.js`: `4ffaadacda530c6bf158bbe732cd5be137006c5e51a37c1fc11985f39c6fee8c`
- `static/js/google_maps_markers.js`: `7c3176e89f3f77fab5d6dc1171029db7d9f5255839dc3ff3c791a8a34fa490fe`
- `static/js/google_maps_motion.js`: `b2fbfa362caeb927c1dc5fa5245b1ff145169e2472164afb7799e457b119a8ad`
- `src/catalog/services/map_payload.py`: `67d0c2e3b93111eb34da02df2f6352a8fe691d79b14a5cdddc0bab6d0e942038`
- `src/catalog/controllers/place_controller.py`: `6afed29168763fe459d079e4764873800a64d5c4b1a686d7c5de4fbf06e9135b`
- `src/catalog/controllers/home_controller.py`: `83f13a09649b6abcdb04091afb070f427f457dd3801d38effa353b7523228872`
- `src/catalog/templates/catalog/place_list.html`: `2cb67d432a29b69ce3fd2d228579e59171a24e4fc6256072a67b64d9100b657b`
- `src/catalog/templates/pages/home.html`: `f0f3c8bc7f22558fede92a8c23f93b6e328a51868536ee7011be8db4d264eb8f`
- `src/catalog/templates/catalog/includes/place_card.html`: `e553153bc08e10d5f19e76c59807d42825cf3e8201df209948d773f74df54ff9`
- `static/css/pages/catalog_places.css`: `7a5eff82d3719be49bd5cf5f59f0b91544a5c3a432c45b612d824228bc06a055`
