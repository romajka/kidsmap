# Module 11 — integration-reviewer support

2026-10-11, AUDIT ONLY. Assigned ownership: targeted existing-test capture and this bounded handoff. Application code, migrations, assertions and other agents' QA were not edited. The parent owns the full module report, stand, browser and journal.

## Snapshot and isolation

Checkout `C:/kidsmap`; HEAD `8d188b316f800fbedf0b1e376905dfd4924cb1b6`; branch `task33-progress`. This is the parent's **dirty WORKTREE**, not a clean-HEAD result. Initial targeted-test before/after source set: 2,788 files, SHA-256 digest `e13c36f2af3aca03513ff860a1dee7c02a8cb2ab8214c89bcffd7dd5fe5914b1`, with zero changed source paths during execution. [Parent snapshot](snapshot.json) carries the foreign dirty state and active_run. PRODUCTION is NOT RUN.

Parent READY attested an isolated PostgreSQL database at `127.0.0.1:55442`. Django creates/drops only `test_module11`; the browser stand's `module11` is not seeded or otherwise mutated by these runners. `DJANGO_TESTING=1`; process-local LocMem cache/email; separate `.tmp/module11-20261011-r1/unit-media` and `unit-private-media`; outbound socket guard; empty external integration credentials. Parent `run.py` is executed directly or verbatim via runpy; it remains unchanged by this specialist.

## Fresh executed checks

| Run | Methods | PASS | FAIL | ERROR | Skipped | Exit | Test body / wall |
|---|---:|---:|---:|---:|---:|---:|---|
| Current stand, localized URLs enabled | 110 | 106 | 3 | 1 | 0 | 1 | 147.282s / 233.672s |
| Legacy wrapper attempt 01 | 0 executed | — | — | — | — | 1 | no test body / 2.110s |
| Legacy wrapper attempt 02 | 0 executed | — | — | — | — | 1 | no test body / 141.500s |
| Legacy wrapper attempt 03, localized URLs disabled | 4 | 4 | 0 | 0 | 0 | 0 | 13.636s / 88.797s |

The primary Django summary is `Ran 110 tests`, `FAILED (failures=4, errors=2)`: those six entries include subtests, belonging to three failed methods and one errored method. They are not six separate methods or six product defects. Exact argv, source digests, method inventory, output hashes and durations: [tests-command.json](tests-command.json). Sanitized native output: [tests.log](tests.log). No raw child output or credentials were written before sanitization.

Exact wrapper command:

```powershell
.venv/Scripts/python.exe docs/qa/module11-2026-10-11-r1/tests-run.py --ready
```

The complete child command is recorded as structured argv in `tests-command.json` and invokes `.venv/Scripts/python.exe docs/qa/module11-2026-10-11-r1/run.py test <34 labels> --verbosity=2`. `run.py` supplies `verbosity=1` to call_command, so effective verbosity is 1. No assertions were relaxed or rewritten.

| Existing targeted group | Methods | Enabled result |
|---|---:|---|
| test_localized_place_urls (including PostgreSQL concurrent first translation) | 13 | 13 PASS |
| test_localized_place_seo | 16 | 16 PASS |
| test_seo_indexability | 11 | 11 PASS |
| test_seo_landing_visibility | 4 | 4 PASS |
| test_judo_seo_landing | 3 | 3 PASS |
| test_task33_localization | 21 | 21 PASS |
| public.PublicLanguageConsistencyTests | 10 | 7 PASS / 2 FAIL / 1 ERROR |
| PlaceSchemaOrgSeoTests | 6 | 6 PASS |
| Selected TestPublicPagesSmoke methods | 23 | 22 PASS / 1 FAIL |
| Selected TestCatalogEnhancements query methods | 3 | 3 PASS |

## Failure attribution

[settings.py:65](../../../src/config/settings.py:65) defaults `LOCALIZED_PLACE_URLS_ENABLED` to `DEBUG and not TESTING`; standard testing therefore uses False. The audit stand explicitly enables this feature in its own qa_settings. The affected older `public.py` assertions assume one AZ/legacy slug under every language prefix, rather than deriving each language's path.

[place_urls.py:16](../../../src/catalog/services/place_urls.py:16) selects the saved language slug when enabled; [Place.get_absolute_url](../../../src/catalog/models/place.py:611) delegates to that language path. [place_detail](../../../src/catalog/views.py:393) permanently redirects a wrong-language slug. Both current behavior and intentional redirect contracts pass in the specialized localized suites. These primary failures establish a **test configuration compatibility mismatch**, not an application defect.

| Affected existing method | Fresh enabled evidence | Attribution |
|---|---|---|
| test_public_pages_keep_system_text_in_url_language_across_requests | tests.log:31 and :39; RU/EN requests use `place.slug` (AZ) and receive 301, while test asserts 200 | Feature flag / fixture URL mismatch |
| test_place_review_list_has_no_extra_framed_wrapper | tests.log:23; RU AZ-slug request is 301 and assertContains expects 200 | Same mismatch; does not establish a wrapper visual defect |
| test_place_review_block_uses_the_page_language_for_all_system_copy | tests.log:5 and :14; parses `id="reviews"` from a 301 response and raises ValueError | Same mismatch; does not establish missing rendered reviews |
| test_sitemap_includes_all_languages_and_hreflang_alternates | tests.log:47; assertion wants `/ru/place/100-keyfiyyetli-usaq-derneyi/`, actual final RU URL is `/ru/place/100-mesto-dlya-sitemap/`, EN `/en/place/100-sitemap-place/` | Same mismatch; final language URLs are the intended feature behavior |

No NEW REGRESSION or pre-existing **application** defect is confirmed by this test slice. Historical reports are not fresh evidence, and pristine-HEAD comparison was NOT RUN. Broad regression attribution remains UNKNOWN.

Legacy attempt 01 and attempt 02 are **QA HARNESS ERROR**, separate from app/test findings: the specialist's wrapper initially rejected Django's internal migration and then internal check command. Both stopped before test methods ran. Only the owned wrapper was adjusted to permit internal migrate/createcachetable/check on `test_module11:55442`. All attempt logs/commands are preserved: [attempt 01](tests-legacy.log), [attempt 01 command](tests-legacy-command.json), [attempt 02](tests-legacy-attempt02.log), [attempt 02 command](tests-legacy-attempt02-command.json).

The fresh default/legacy repeat **passes all four unchanged methods**, exit 0, body 13.636s / wall 88.797s, with zero source changes. [Attempt 03 output](tests-legacy-attempt03.log) and [exact commands/settings/snapshot](tests-legacy-attempt03-command.json) confirm that the same assertions pass with LOCALIZED_PLACE_URLS_ENABLED=False. This verifies the feature-flag compatibility attribution; it does not convert the original enabled run into PASS and does not certify a pristine HEAD.

```powershell
.venv/Scripts/python.exe docs/qa/module11-2026-10-11-r1/tests-legacy.py
.venv/Scripts/python.exe docs/qa/module11-2026-10-11-r1/tests-legacy.py --attempt02
.venv/Scripts/python.exe docs/qa/module11-2026-10-11-r1/tests-legacy.py --attempt03
```

## Side effects and simulated integrations

These existing tests use fictional ORM fixtures and internal Django TestClient requests, not the user's required browser transitions. They provide targeted backend regression evidence only. PostgreSQL transaction/concurrency tests did run; all media references and generated fixture data belong to test resources.

`test_localized_place_seo` tests notification URLs with a mocked `catalog.indexnow_signals.enqueue_indexnow_urls`; calls marked `captureOnCommitCallbacks(execute=True)` still stay under that mock. Other selected tests have empty INDEXNOW_KEY; [indexnow_enabled](../../../src/catalog/services/indexnow.py:39) and [enqueue_indexnow_urls](../../../src/catalog/services/indexnow.py:181) prevent real submission. These are **SIMULATED integrations**, not live IndexNow/Search Console evidence. URLs containing the public domain are expected text in locally generated metadata/TestClient requests, not production connections.

`test_seo_audit_system` was intentionally NOT RUN: it calls state-writing audit/fix and rollback routines, including audit_seo/apply_seo_fixes/audit_internal_links/audit_schema/seo_report. Whole TestPublicPagesSmoke was intentionally NOT RUN because an unrelated method calls `collectstatic(clear=True)`; only listed methods were selected. No full suite, CI, browser, actual crawler/Rich Results/Search Console or external provider was executed by this support role.

## Memory coverage and checks on QA artifacts

Codebase Memory first: callable list_projects returned project `C-kidsmap`, root `C:/kidsmap`, and index_status reported ready. Graph search had 152 matches / 80 returned / has_more true; bounded source reads were used for the selected test groups rather than an exhaustive graph claim. Exact cited paths returned `coverage_unavailable` and `metadata_changed` (generation initially `2026-10-11T09:18:17Z`, later `09:25:41Z`). Freshness/coverage completeness is UNKNOWN; actual source was inspected. No MCP cache, reindex or private graph inventory was written to artifacts.

QA runner AST parse and synthetic CSRF-token sanitation sample passed (exit 0); this verifies the owned capture helper, not application behavior. Final verification: both QA scripts parse; all four saved logs match their recorded on-disk SHA-256; counts match native summaries; referenced local evidence exists; no known scratch credential or unredacted CSRF token is present in the owned artifacts. Windows newline translation is accounted for by recording the on-disk hash and preserving the originally computed normalized-text hash separately in metadata.

## Named handoff

**seo-reviewer / kidsmap-orchestrator:** use the 106 PASS methods as bounded fresh backend evidence; keep the enabled/legacy test configuration distinction and the four affected old test methods out of confirmed product findings unless independent runtime reproduction establishes an actual defect. Browser roles remain responsible for rendered RU/AZ/EN × requested widths, native save/reload, UI errors and console/network.

**integration-reviewer (future approved test maintenance):** separately review whether old public.py tests should derive URLs by language or explicitly declare the legacy feature flag. No assertion change is authorized by this audit, and no repair prompt for an unconfirmed product defect is generated here.
