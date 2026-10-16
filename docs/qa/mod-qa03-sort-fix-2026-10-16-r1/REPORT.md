# MOD-QA-03 SORT — scoped LOCAL PASS; whole ID OPEN

2026-10-16, `/root`, roles kidsmap-orchestrator → django-reviewer/integration-reviewer/browser-qa performed sequentially by the lead; no independent specialists claimed. Canonical definitions under `.agents/agents/`. Authority: user “дальше” continues the previously shown `mod-qa03-menu-fix-2026-10-15-r1/SORT_IMPLEMENTATION_PLAN.md` exact four-file scope. Production NOT RUN.

## 1. State and snapshot

Actual checkout `/home/ramin/kidsmap`, branch `task33-progress`, HEAD `e4e05cc213b34e2d771ecb854901bfd016d1db51`, dirty WORKTREE, `active_run: NONE`. Entry: [entry.json](entry.json); accepted current process/source: [runtime-source-final.json](runtime-source-final.json), [runtime-info.json](runtime-info.json). Current interpreter Python3.12.3, Django6.0.2, own175migrations. Running owned HTTP PID38833 on loopback45135; own PostgreSQL loopback55023/database `mod03_sort_fix_r1`; paths and actual loaded module origins are in source evidence. Historical PID/ports were not reused as evidence.

MOD01/02 prior LOCAL PASS retained. MOD03 existing CSS/menu results retained without full repeat; SORT cause is now scoped LOCAL PASS. Whole MOD03 stays OPEN because search-form filter loss and unmatched Event/Specialist column controls remain. MOD04–08/full08/global/production NOT RUN.

## 2. What changed and why

Django rejected the shared toolbar `sort` query as a field lookup on Event/Specialist, redirecting to `?e=1` and losing q. Added hidden parameter consumption and whitelisted ordering/context in NEW `src/catalog/domain_admin/queue_sorting.py`; integrated only EventAdmin in `src/catalog/domain_admin/place.py` and only SpecialistAdmin in `src/catalog/domain_admin/specialist.py`; NEW `src/catalog/testcases/test_mod_qa03_queue_sorting.py` contains6 regression methods. Exact isolated delta: [implementation.patch](implementation.patch), excluding inherited foreign edits.

Six keys: created/updated ascending/descending; canonical name ascending/descending; pk ties follow the same direction. Default/unknown uses updated_desc. Existing Place translated labels reused. Search/filter/queryset/permissions remain in standard admin path. Existing Specialist select_related/prefetch/document guards preserved. No CSS/JS/templates/PO/model/schema/action changes in this approved patch.

## 3. Reproduction and remaining real problems

Fresh6-method RED:41 assertion failures, no fixture/assertion weakening; actual e=1 redirects. Native fresh RED2FAIL and exact postpatch2PASS in [native-red.js.result.json](native-red.js.result.json) / [native-green-recheck.js.result.json](native-green-recheck.js.result.json). First early test run had PostgreSQL connection-refused before readiness and is retained separately as infrastructure failure in tests-red.txt; it is not counted as TDD reproduction. Pagination fixture corrected to installed Django one-based p=2 before GREEN; assertions retained.

Separate **OPEN P2**: native Event RU360 search submit removes status before sorting. [Retained interrupted assertions](native-matrix-interrupted-ru.json), [cause](NATIVE_SEARCH_FILTER_OPEN.md), [concrete three-file next PLAN](SEARCH_FILTER_IMPLEMENTATION_PLAN.md). Shared search template uses Jazzmin admin_extra_filters, which removes visible list_filter parameters from this independent search form. No fix for that cause was made. Matrix explicitly starts combined q+status sorting from a valid address URL; native search-only original sort trigger also passes. Do not claim the combined search-form submission is fixed.

## 4. Targeted verification and evidence

Exact argv/exits/durations: [commands.jsonl](commands.jsonl); executable semantic gate: [final_gate.py](final_gate.py); final results: [verification.json](verification.json).

- Own runtime `test catalog.testcases.test_mod_qa03_queue_sorting`: RED exit1,6 methods/41 assertion failures. GREEN adds two existing private-document visibility methods plus EventAdminReadinessTests: **19 methods PASS**, exit0. Full output [tests-green.txt](tests-green.txt).
- Native real browser: RU/AZ/EN via actual language-menu POST;360/390/768/1024/1280/1440;36 model×locale×viewport base cells,60 reachable sidebar cells;12 mobile-overlay cases explicitly excluded from background interactions. Six native options per cell: **360 real visible-ID order comparisons,360 exact translated-label/active-option comparisons**; search/filters, page2, reload, new-sort page reset, reset, keyboard focus. No response/style substitution.
- **1511 accepted native PASS**:1454 main matrix +55 targeted supplement +2 exact-trigger GREEN. No local console/page/network/HTTP errors in accepted checks. External resources blocked; font-network failures are explicit expected isolation diagnostics, not external integration verification.
- Raw matrix keeps6 FAIL from attempting a menu on first sorting fixture row: these rows lacked a public Event menu (new sorting fixture rows have no end_datetime). Only this smoke subset was repeated against the original published QA Queue2 fixture. Supplement55PASS includes6 actual menu keyboard/Escape-focus flows plus native invalid-sort/empty/reset cases. No full CSS/menu/module corpus repeat.
- RU/AZ controlling CLI processes exited143 while browser daemons continued. Their complete20-cell+4overlay checkpoints are retained as separate recovered JSON; final original epilogue assertions were not recovered or invented. EN complete result retained normally. See [checkpoint-recovery.json](checkpoint-recovery.json). Fresh final process/source gate, native supplement before/after fingerprint and PostgreSQL counters provide separate bounds.
- Own fresh PostgreSQL domain counters exactly equal initial fixture writes: each Event/Specialist110 inserts,107 timestamp updates,0deletes; no extra domain writes. Tests used separate test DB. Read-only evidence [domain-mutation-counters.json](domain-mutation-counters.json).
- **92 verified PNG**, SHA256/dimensions/phase [png-manifest.json](png-manifest.json). Representative RU mobile, AZ menu and EN desktop were visually inspected. Automated rendered geometry/focus/ID assertions cover the matrix; no claim of manually inspecting every screenshot.

## 5. Isolation and preservation

DJANGO_TESTING=1; own PG/cache/media/private-media/file-email and generated fictional fixtures. Runtime clears inherited environment before setup; no checkout .env or production credentials loaded. Egress restricted to own PostgreSQL; browser allows own loopback origin only. Copy of pypdf dependency verified against [dependency-manifest.json](dependency-manifest.json), no installation/network download.

Current RU/AZ/EN PO compiled in new own `.tmp/mod-qa03-sort-fix-2026-10-16-r1/locales` using build_isolated_locales.py, build/verify exit0. Manifest verified before django.setup; sole LOCALE_PATHS points to own copied locale root. All3 own MOs actually opened; shared checkout MO files untouched. [locale-manifest.json](locale-manifest.json).

Entry32129 file hashes:32126 unchanged; only approved existing2backend files plus appended guide status note differ. New helper/test and own QA directory added. No missing entry files. All71 entry foreign containers retain ID/state/ports; own72nd container added. No QA HTTP serve processes existed in fresh entry snapshot; older historical process continuity is not claimed. No foreign process/container lifecycle operations, reset/clean/stash/active_run assignment. HEAD/branch/active_run unchanged. [preservation.json](preservation.json). Process inventory was bounded to QA HTTP; no blanket continuity claim for every machine process.

## 6. Legacy and debt

No deletion/refactor. PlaceAdmin/PlaceSortFilter unchanged. Event/Specialist unsupported shared column targets remain OPEN/NOT RUN; CSS/menu historical artifacts preserved. Existing mixed dashboard translations visible in PNG are outside exact sort-label acceptance; no whole-UI localization PASS.

## 7. Evidence limits / NOT RUN

Two own fresh RED PNG paths were reused by exact GREEN harness, so those files now show GREEN. Fresh RED semantic2FAIL and unit RED are intact; fresh RED PNG unavailable. This limitation is recorded in TDD.md and manifest phase; no historical/foreign artifact overwritten. Interrupted attempts/controller errors retained, never counted as source GREEN. Full08, other module suites, all-modules acceptance, production, commit/push/deploy NOT RUN. Local result says nothing about production.

## 8. Next step

Approve the separate [three-file search-filter PLAN](SEARCH_FILTER_IMPLEMENTATION_PLAN.md) before implementing that new cause. It proposes one local template tag, one shared template loop and one regression module, with fresh RED→GREEN and targeted shared consumers. No repeat approval needed for the completed SORT scope. Do not start module09.

## 9. Priority and decision

SORT cause: **scoped LOCAL PASS**. New search-form loss: **P2 OPEN**. Unmatched columns: **OPEN/NOT RUN**. Historical MOD-QA-03 as a whole remains **OPEN**; no new historical ID invented. Further MOD04–08 plans and full ACCEPT08 remain pending.
