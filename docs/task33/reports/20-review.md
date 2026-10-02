# Stage20 — independent integration review

Task/mode: bounded AUDIT by real runtime `/root/stage20_integration`, canonical integration-reviewer; report-only ownership assigned by `/root`. User authorizes only stage20. Application/status/production edits by this reviewer: none. Parent owns active_run `20261002-123827Z`; dependency19 DONE and accepted checkpoints verified in current journal. LOCAL HEAD `c52b871ce5c18656a9eaf9854e66255c2629364e`, dirty WORKTREE; HEAD does not represent implemented source.

Evidence: `services/map_payload:map_identity` groups only explicit confirmed Place binding + confirmed active Location; no address/coordinate inference. Confirmed address-only venue suppresses points, unconfirmed/archived venue falls back to valid Place coordinates and separate Place identity. `serialize_map_places` applies backend filters, stage18/19 presentation and member grouping; no phone number payload. `public_map_api:public_map` GET-only/no-cache, member-based count. `place_controller:build_list_context` retains coordinate-less cards/count and member-based map count. `catalog_structure:preserve_place_structure` and `publication:_apply` detach only target on changed persisted address/coordinates; no Location or Event write. `public_presentation:present` uses map_identity for missing marker. `catalog_map:getRouteUrl` serializes coordinates only; group member cards escape names/text and use independent public URLs/phone reveal buttons. `home_map:serverFilterUpdater` uses shared endpoint, abort + generation checks, clears stale markers before request/on failure; visual clustering does not establish organization identity.

Codebase Memory list_projects/index_status/get_architecture/check_index_coverage executed. Current project/root match, full generation2026-10-02T12:47:04Z; map_payload/catalog_structure/home_map metadata_match best-effort. Coverage recording truncated (2000/2031 ignored records), templates parse_partial; all critical conclusions verified actual source. No graph absence used as proof.

Six reviewer-owned private probes in `/tmp/task33-stage20-review-probes.py`: database rejects missing Location confirmation; in-memory unconfirmed Location never groups; stale structural instance preserves current bound venue; unsaved changed address excluded from partial save keeps binding; entire historical Event row immutable after persisted address+coord Place save; hidden member excluded from localized/query endpoint; invalid numeric boundaries (bool/nonfinite/out of range) rejected. Injection adds methods before canonical discovery without assertion changes. QA04 original settings/guards/container ownership and cleanup retained.

Exact command (cwd `/home/ramin/kidsmap`):

```bash
./.venv/bin/python /tmp/task33-stage20-review-run.py --mode all --label catalog.testcases.test_task33_map --label catalog.testcases.test_task33_home_map --label catalog.testcases.test_task33_search --output /tmp/kidsmap-task33-stage20-independent2
```

Independent1 same command/output suffix1: exit2 ENVIRONMENT_FAILURE at safety socket PermissionError; seven safety tests, one environment error, no DB started, scratch removed. Independent2: exit2,46 tests/0F2E/0skip,20.919s; canonical40 and other four reviewer probes PASS. Two errors were reviewer fixtures: NULL Location.confirmed_at violates required DB confirmation; coordinate40.2 full save rejected by existing unresolved district guard. No application changes/assertion changes. Private fixture corrected to explicit DB rejection + defensive in-memory identity and supported40.4093 coordinate, preserving complete Event-row assertion. Independent3 repeat active; final results below.

DB/security impact: no migration or external access by reviewer; disposable owned PostgreSQL17 networknone, tmpfs PGDATA, isolated socket/cache/media/locmem email, clean environment with no production credentials. No broad identity/ownership merge. Browser by this reviewer NOT RUN; source/negative tests do not prove rendered acceptance. Full application suite, external Maps/SMTP/analytics, production/commit/push/deploy and21+ NOT RUN. Application baseline NOT_GREEN not reclassified.

Named handoff: `/root` / frontend-reviewer aggregates independent runtime checks and separate browser acceptance, final hashes and criteria before reporting stage20 DONE. Legacy `Place.is_map_ready` still describes Place coordinates; public map/card consumers use map_identity. No changed legacy Event map consumer claim.

Final JS delta source checked: map payload localized fallback label; popup title lang/content-language/fallback marker, catalog route requires valid finite/range/nonzero coords; homepage serialized points validated before popup. Independent `node --check static/js/catalog_map.js` and `node --check static/js/home_map.js` exit0. These syntax checks are not browser evidence.

Independent3: exit1,46 tests/0F1E/0skip,20.954s, cleanup PASS. All40 canonical and five reviewer probes PASS; Event-row probe still used longitude49.87 outside the covered fixture pair, so pre-existing geography readiness rejected write. Final private fixture uses documented supported pair40.4093,49.8671 (test_location_resolution/test_location_assignment); independent4 same labels/output suffix4 active. No application/assertion changes.

Reviewed dirty source SHA256 (captured after final translation/JS changes; report not self-hashed):

```json
{
  "src/catalog/services/map_payload.py": "67d0c2e3b93111eb34da02df2f6352a8fe691d79b14a5cdddc0bab6d0e942038",
  "src/catalog/services/catalog_structure.py": "42722b850747ac933fd12f6c6b5bba135df5cfe5e676aff9e0803f4361209326",
  "src/catalog/services/publication.py": "86911a58cede93972f7479d2398fe67c4ca12d2e654d310c25d0f56ea1c706b0",
  "src/catalog/services/public_presentation.py": "224872cd42a6ba5582d9d11d69cc57d76cc7e544b5305207735e8573aa7323ae",
  "src/catalog/repositories/django_repositories.py": "768a97666b6da8faa037ac0b6da93d6f312bc1865e09fb8690b63586924331cd",
  "src/catalog/controllers/place_controller.py": "6afed29168763fe459d079e4764873800a64d5c4b1a686d7c5de4fbf06e9135b",
  "src/catalog/controllers/home_controller.py": "83f13a09649b6abcdb04091afb070f427f457dd3801d38effa353b7523228872",
  "src/catalog/controllers/public_map_api.py": "fe0bbd838ac87de20229d6a980c9aa24f792384928eaad749b732a1fc610acb3",
  "src/catalog/testcases/test_task33_map.py": "85f27cf8f188e58cadbdf7461c7d08e38f5b4bf935f41d6a545a6458bedf4f68",
  "src/catalog/testcases/test_task33_home_map.py": "aa449c1ae4476e8c986799c7fb678147f65452ff12a53d43991007d1c65a1438",
  "src/catalog/testcases/test_task33_search.py": "e82320179c528e9c7864a62d1fe3e49d0ab10743b34392d6247e3b65139940d5",
  "static/js/catalog_map.js": "f19b089b1a7efb86617d2ffec9fac14737d7fba49819d681dc1430d99ed102b8",
  "static/js/home_map.js": "4ffaadacda530c6bf158bbe732cd5be137006c5e51a37c1fc11985f39c6fee8c",
  "src/catalog/templates/catalog/includes/place_card.html": "e553153bc08e10d5f19e76c59807d42825cf3e8201df209948d773f74df54ff9"
}
```

## Final independent result

Independent4: **exit0,46/46 PASS,0 failures/errors/skips,20.059s** =40 canonical map/home/search +6 private negative/integration probes. `check` and `makemigrations --check --dry-run` PASS; PostgreSQL17 applied161/unapplied0; ownership-guarded cleanup PASS, both scratch roots removed. Reviewed source SHA13/14 unchanged after final test run; `test_task33_home_map.py` changed during run for lead late homepage reset/age probes. Independent4 does not claim those new tests. Homepage control delta reopened for targeted recheck. Earlier private fixture errors are not application regressions; final supported-coordinate Event assertion compares every persisted field, not just address. No confirmed blocker in assigned Python/backend-to-popup contract scope. Actual browser and real external Maps remain separate reviewer evidence/NOT RUN by this executor. Named handoff `/root` / frontend-reviewer for aggregate stage acceptance.

## Homepage hypothesis boundary — no application finding

Lead explored initial home `q`/age5 response with two temporary canonical tests. Those GETs redirect301 before HomeController: `public_urls:PUBLIC_QUERY_PARAMS` owns list/search parameters only; home is absent and `CleanPublicQueryMiddleware` strips them. Therefore `_selected_age` shortcut normalization and template map_places guard are not a reachable initial filtered-home mismatch under current routing. Parent confirmed this in browser. This reviewer verified actual route policy source. Exploratory tests removed, application source unchanged, original14/14 SHA now matches again. AJAX zero/reset remains separate browser evidence. No home URL policy change/next-stage work. Independent4 remains current for restored final source.

## Final glyph-only delta

After independent4, browser B20-01 identified an odd-coordinate SVG polyline in homepage schedule icon. Parent corrected points `12 6 12 16 14` to `12 6 12 12 16 14`. Reviewer source-read actual literal: valid three coordinate pairs; only `static/js/home_map.js` changed among14 reviewed artifacts. Independent `node --check static/js/home_map.js` exit0. Updated embedded home-map SHA; final14/14 current source matches. No DB rerun for SVG-only glyph;46/46 backend result retained on unchanged Python source. Parent browser final8 reports47/47,console0 and11/11SHA stable; that browser result belongs to browser executor, not this reviewer. B20-01 closed; no remaining confirmed integration blocker.
