# Точные команды и выходы

PowerShell, cwd C:/kidsmap. Это execution ledger, не команда повторного использования уже занятого стенда. Новому run нужны собственные имя/порты/scratch.

Bootstrap / own stand:

```powershell
.venv/Scripts/python.exe docs/qa/module11-2026-10-11-r1/prepare.py
.venv/Scripts/python.exe docs/qa/module11-2026-10-11-r1/run.py snapshot
wsl.exe -- docker run --name kidsmap-module11-20261011-r1 -e POSTGRES_HOST_AUTH_METHOD=trust -e POSTGRES_USER=module11 -e POSTGRES_DB=module11 -p 127.0.0.1:55442:5432 -d postgres:17-alpine
wsl.exe -- sh -c 'exec sleep 86400'
wsl.exe -- docker start kidsmap-module11-20261011-r1
.venv/Scripts/python.exe docs/qa/module11-2026-10-11-r1/run.py migrate
.venv/Scripts/python.exe docs/qa/module11-2026-10-11-r1/seed.py
.venv/Scripts/python.exe docs/qa/module11-2026-10-11-r1/seed-extra.py
.venv/Scripts/python.exe docs/qa/module11-2026-10-11-r1/seed-private.py
.venv/Scripts/python.exe docs/qa/module11-2026-10-11-r1/run.py serve
.venv/Scripts/python.exe docs/qa/module11-2026-10-11-r1/run.py serve-errors
Stop-Process -Id 18872 # only after exact own command-line identity check
.venv/Scripts/python.exe docs/qa/module11-2026-10-11-r1/run.py serve-public-safe
```

prepare/snapshot/seed complete exit0. PG image17.11; own fresh Docker volume. Initial migration attempt failed with connect timeout after WSL idle shutdown (exit1); own keepalive/start→pg_isready→175 migrations exit0. Initial seed-private Event.is_active attempt failed (exit1); own seed corrected before visibility checks, idempotent re-run exit0. Main processes intentionally remain running: no completion exit. Own PID18872 replaced by2428 for DEBUGFalse error rendering; other stands untouched.

HTTP/readback/build verification:

```powershell
.venv/Scripts/python.exe -X utf8 docs/qa/module11-2026-10-11-r1/http-audit.py
.venv/Scripts/python.exe -X utf8 docs/qa/module11-2026-10-11-r1/http-proof.py
.venv/Scripts/python.exe -X utf8 docs/qa/module11-2026-10-11-r1/http-final.py
.venv/Scripts/python.exe -X utf8 docs/qa/module11-2026-10-11-r1/readback.py
.venv/Scripts/python.exe -X utf8 docs/qa/module11-2026-10-11-r1/build-previews.py
.venv/Scripts/python.exe -X utf8 docs/qa/module11-2026-10-11-r1/build-report.py
& 'C:/Program Files/nodejs/node.exe' docs/qa/module11-2026-10-11-r1/check-js.cjs
.venv/Scripts/python.exe -X utf8 docs/qa/module11-2026-10-11-r1/verify.py
git diff --check
```

Final successful HTTP scripts exit0 (semantic FAIL are stored separately). Initial http-proof own namespace __file__ setup error exit1 /0checks; corrected re-run67observations exit0. AST/JSON/secrets/preservation report final in verification.json. JS syntax exit0.

Browser session module11-r1, Playwright CLI cached, Chromium153.0.8010.12; scratch/playwright config uses isolated headless browser. Initial CLIopen beforeHTTPREADY ERR_CONNECTION_REFUSED exit1; later native navigation succeeds. One CLI--help diagnostic uv assertion exit1, not app evidence.

|Command|Exit|Seconds|Result|
|---|---:|---:|---|
|`.venv/Scripts/python.exe docs/qa/module11-2026-10-11-r1/drive.py probe.js`|0|7.05|[probe.result.txt](probe.result.txt)|
|`.venv/Scripts/python.exe docs/qa/module11-2026-10-11-r1/drive.py browser-matrix.js`|0|355.42|[browser-matrix.result.txt](browser-matrix.result.txt)|
|`.venv/Scripts/python.exe docs/qa/module11-2026-10-11-r1/drive.py keyboard.js`|1|4.14|[keyboard.result.txt](keyboard.result.txt)|
|`.venv/Scripts/python.exe docs/qa/module11-2026-10-11-r1/drive.py native-probe.js`|0|10.81|[native-probe.result.txt](native-probe.result.txt)|
|`.venv/Scripts/python.exe docs/qa/module11-2026-10-11-r1/drive.py keyboard.js`|0|144.27|[keyboard.result.txt](keyboard.result.txt)|
|`.venv/Scripts/python.exe docs/qa/module11-2026-10-11-r1/drive.py rename.js`|1|72.89|[rename.result.txt](rename.result.txt)|
|`.venv/Scripts/python.exe docs/qa/module11-2026-10-11-r1/drive.py rename.js`|1|50.31|[rename.result.txt](rename.result.txt)|
|`.venv/Scripts/python.exe docs/qa/module11-2026-10-11-r1/drive.py editors.js`|1|4.52|[editors.result.txt](editors.result.txt)|
|`.venv/Scripts/python.exe docs/qa/module11-2026-10-11-r1/drive.py editors.js`|0|14.27|[editors.result.txt](editors.result.txt)|
|`.venv/Scripts/python.exe docs/qa/module11-2026-10-11-r1/drive.py admin-errors.js`|0|4.14|[admin-errors.result.txt](admin-errors.result.txt)|
|`.venv/Scripts/python.exe docs/qa/module11-2026-10-11-r1/drive.py admin-errors.js`|0|3.33|[admin-errors.result.txt](admin-errors.result.txt)|
|`.venv/Scripts/python.exe docs/qa/module11-2026-10-11-r1/drive.py rename.js`|1|99.28|[rename.result.txt](rename.result.txt)|
|`.venv/Scripts/python.exe docs/qa/module11-2026-10-11-r1/drive.py focus-proof.js`|0|38.02|[focus-proof.result.txt](focus-proof.result.txt)|
|`.venv/Scripts/python.exe docs/qa/module11-2026-10-11-r1/drive.py event-specialist.js`|0|30.52|[event-specialist.result.txt](event-specialist.result.txt)|
|`.venv/Scripts/python.exe docs/qa/module11-2026-10-11-r1/drive.py place-program-rename.js`|0|73.28|[place-program-rename.result.txt](place-program-rename.result.txt)|
|`.venv/Scripts/python.exe docs/qa/module11-2026-10-11-r1/drive.py organization-rename.js`|0|27.69|[organization-rename.result.txt](organization-rename.result.txt)|
|`.venv/Scripts/python.exe docs/qa/module11-2026-10-11-r1/drive.py specialist-rename.js`|1|16.84|[specialist-rename.result.txt](specialist-rename.result.txt)|
|`.venv/Scripts/python.exe docs/qa/module11-2026-10-11-r1/drive.py specialist-editor-proof.js`|0|7.44|[specialist-editor-proof.result.txt](specialist-editor-proof.result.txt)|
|`.venv/Scripts/python.exe docs/qa/module11-2026-10-11-r1/drive.py specialist-form-probe.js`|0|7.09|[specialist-form-probe.result.txt](specialist-form-probe.result.txt)|
|`.venv/Scripts/python.exe docs/qa/module11-2026-10-11-r1/drive.py specialist-form-probe.js`|0|7.8|[specialist-form-probe.result.txt](specialist-form-probe.result.txt)|
|`.venv/Scripts/python.exe docs/qa/module11-2026-10-11-r1/drive.py specialist-clean.js`|1|13.94|[specialist-clean.result.txt](specialist-clean.result.txt)|
|`.venv/Scripts/python.exe docs/qa/module11-2026-10-11-r1/drive.py specialist-clean.js`|0|9.81|[specialist-clean.result.txt](specialist-clean.result.txt)|
|`.venv/Scripts/python.exe docs/qa/module11-2026-10-11-r1/drive.py specialist-clean.js`|0|42.94|[specialist-clean.result.txt](specialist-clean.result.txt)|
|`.venv/Scripts/python.exe docs/qa/module11-2026-10-11-r1/drive.py relations.js`|0|52.08|[relations.result.txt](relations.result.txt)|
|`.venv/Scripts/python.exe docs/qa/module11-2026-10-11-r1/drive.py admin-errors.js`|0|11.26|[admin-errors.result.txt](admin-errors.result.txt)|
|`.venv/Scripts/python.exe docs/qa/module11-2026-10-11-r1/drive.py private-errors.js`|0|5.05|[private-errors.result.txt](private-errors.result.txt)|
|`.venv/Scripts/python.exe docs/qa/module11-2026-10-11-r1/drive.py visibility.js`|0|105.34|[visibility.result.txt](visibility.result.txt)|
|`.venv/Scripts/python.exe docs/qa/module11-2026-10-11-r1/drive.py conflict-network.js`|0|21.38|[conflict-network.result.txt](conflict-network.result.txt)|
|`.venv/Scripts/python.exe docs/qa/module11-2026-10-11-r1/drive.py post-change.js`|0|122.23|[post-change.result.txt](post-change.result.txt)|
|`.venv/Scripts/python.exe docs/qa/module11-2026-10-11-r1/drive.py previews.js`|0|13.42|[previews.result.txt](previews.result.txt)|

Nonzero own browser harness attempts retained. Ambiguous fields/main selector, same-document goto null, waitForNavigation assumptions, race after language click, native confirm auto-dismiss, hidden Select2 not selected, and initial incomplete onsite fixture explain discarded attempts. Their FAIL/ERROR are not app findings. Latest specialist-clean is the valid native save/slug proof.

Django child commands (effective verbosity1, argv exact):

[tests-command.json](tests-command.json)

```text
C:\kidsmap\.venv\Scripts\python.exe C:\kidsmap\docs\qa\module11-2026-10-11-r1\run.py test catalog.testcases.test_localized_place_urls catalog.testcases.test_localized_place_seo catalog.testcases.test_seo_indexability catalog.testcases.test_seo_landing_visibility catalog.testcases.test_judo_seo_landing catalog.testcases.test_task33_localization catalog.testcases.public.PublicLanguageConsistencyTests catalog.testcases.test_place_json_and_pricing_modes.PlaceSchemaOrgSeoTests catalog.testcases.public.TestPublicPagesSmoke.test_legacy_az_urls_redirect_to_default_language_without_prefix catalog.testcases.public.TestPublicPagesSmoke.test_legacy_redirect_keeps_catalog_filter_but_drops_foreign_query catalog.testcases.public.TestPublicPagesSmoke.test_public_pages_without_trailing_slash_redirect_to_canonical_url catalog.testcases.public.TestPublicPagesSmoke.test_www_alias_redirects_permanently_to_canonical_origin catalog.testcases.public.TestPublicPagesSmoke.test_legacy_azerbaijani_reviews_url_redirects_to_canonical_reviews_page catalog.testcases.public.TestPublicPagesSmoke.test_canonical_host_redirect_does_not_capture_admin_subdomain catalog.testcases.public.TestPublicPagesSmoke.test_public_urls_on_admin_host_redirect_to_public_origin catalog.testcases.public.TestPublicPagesSmoke.test_public_seo_urls_ignore_request_host_when_origin_is_configured catalog.testcases.public.TestPublicPagesSmoke.test_seo_landing_breadcrumbs_include_the_catalog_level catalog.testcases.public.TestPublicPagesSmoke.test_catalog_page_renders_visible_breadcrumbs catalog.testcases.public.TestPublicPagesSmoke.test_filtered_catalog_breadcrumbs_match_the_place_card_trail catalog.testcases.public.TestPublicPagesSmoke.test_bare_place_segment_redirects_to_catalog catalog.testcases.public.TestPublicPagesSmoke.test_robots_txt_disallows_private_sections catalog.testcases.public.TestPublicPagesSmoke.test_sitemap_includes_all_languages_and_hreflang_alternates catalog.testcases.public.TestPublicPagesSmoke.test_sitemap_and_robots_use_configured_public_origin catalog.testcases.public.TestPublicPagesSmoke.test_sitemap_xml_is_valid_xml catalog.testcases.public.TestPublicPagesSmoke.test_sitemap_excludes_place_new catalog.testcases.public.TestPublicPagesSmoke.test_sitemap_excludes_draft_places catalog.testcases.public.TestPublicPagesSmoke.test_sitemap_excludes_deleted_places catalog.testcases.public.TestPublicPagesSmoke.test_sitemap_has_no_duplicate_urls catalog.testcases.public.TestPublicPagesSmoke.test_sitemap_lastmod_matches_model_updated_at catalog.testcases.public.TestPublicPagesSmoke.test_sitemap_does_not_contain_changefreq_or_priority catalog.testcases.public.TestPublicPagesSmoke.test_seo_landing_uses_matching_language_content_and_hreflang catalog.testcases.public.TestCatalogEnhancements.test_place_detail_drops_foreign_next_query_parameter catalog.testcases.public.TestCatalogEnhancements.test_catalog_keeps_its_own_filter_query_and_detail_links_are_clean catalog.testcases.public.TestCatalogEnhancements.test_language_switch_preserves_catalog_filters_only --verbosity=2
```
exit=1; wall=233.672s; body=147.282s

[tests-legacy-command.json](tests-legacy-command.json)

```text
C:\kidsmap\.venv\Scripts\python.exe C:\kidsmap\docs\qa\module11-2026-10-11-r1\tests-legacy.py --child
```
exit=1; wall=2.11s; body=Nones

[tests-legacy-attempt02-command.json](tests-legacy-attempt02-command.json)

```text
C:\kidsmap\.venv\Scripts\python.exe C:\kidsmap\docs\qa\module11-2026-10-11-r1\tests-legacy.py --child
```
exit=1; wall=141.5s; body=Nones

[tests-legacy-attempt03-command.json](tests-legacy-attempt03-command.json)

```text
C:\kidsmap\.venv\Scripts\python.exe C:\kidsmap\docs\qa\module11-2026-10-11-r1\tests-legacy.py --child
```
exit=0; wall=88.797s; body=13.636s

[extra-tests-command.json](extra-tests-command.json)

```text
C:\kidsmap\.venv\Scripts\python.exe C:\kidsmap\docs\qa\module11-2026-10-11-r1\run.py test catalog.testcases.test_json_ld_serialization catalog.testcases.test_task33_event_schema catalog.testcases.test_task33_public_details catalog.testcases.test_organization_directory
```
exit=1; wall=119.625s; body=29.137s

[extra-tests-event-public-command.json](extra-tests-event-public-command.json)

```text
C:\kidsmap\.venv\Scripts\python.exe C:\kidsmap\docs\qa\module11-2026-10-11-r1\run.py test catalog.testcases.test_task33_event_public
```
exit=0; wall=98.734s; body=3.679s

Final artifact verification: verify.py exit0; source drift0/2788, foreign unallowed changes0/15996, journal only line31 (row11), known secret/CSRF hits0, broken local links0, JS syntax0, git diff --check0. Initial own verifier attempt exit1 because verification.json had not yet been created; generated artifact then final verification succeeded. update-journal.py exit0, preserves all other journal bytes. Final Docker inspect/ps exits0; stand-final.json records actual own IDs, volume, ports/PIDs without env dump.

