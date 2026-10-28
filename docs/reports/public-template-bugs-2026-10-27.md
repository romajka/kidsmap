# Public language and template fixes — 2026-10-27

Mode: user-authorized LOCAL implementation, executed sequentially in the current chat. No independent agent audit claimed.
Snapshot: HEAD `fab76031b4e10d3536f7cc7bf50cc054b5a56bff`, branch `codex/admin-draft-recovery-2026-10-26`, pre-existing dirty WORKTREE. `active_run: none` in task33 status. Branch has no upstream. No commit/push/deploy.

## Changed

- `src/catalog/templates/pages/add_place.html`: RU `24 часа`, EN `24 hours`, AZ `24 saat`.
- `locale/ru/LC_MESSAGES/django.po`: reactivate obsolete `Избранное`; its absence allowed the default AZ catalog to supply `Seçilmişlər` on the RU about page.
- `locale/en/LC_MESSAGES/django.po`: fill `%(minutes)s min`; review the previously fuzzy empty-review heading and activate `No reviews with text yet.`.
- `locale/az/LC_MESSAGES/django.po`: activate the matching AZ empty-review heading.
- `src/catalog/templates/catalog/place_detail.html`: label both summary/fact cells `Тип места` / `Place type` and consistently show the actual permanent/temporary type. Class format belongs to individual tariffs; tariff badges now reuse existing translated `Групповые` / `Индивидуальные` / `Свободное посещение` messages. This also fixes the adjacent EN/AZ Russian badge fallback found in browser QA.
- `src/catalog/controllers/parent_guides.py`: identify free venues using the same prepared public price summary as catalog cards. This recognizes explicit free mode, free active primary tariffs, and legitimate zero-valued legacy price ranges. Reuse the prepared batch, preserve Baku/category/public visibility, and list all free matches instead of truncating to three. Unknown, trial-only, mixed and paid-services admission prices do not count as wholly free.
- `src/catalog/testcases/test_public_template_bugs.py`: ten consumer regressions covering the above and unique server carousel output.

No application models, migrations, production records or pricing semantics were changed.

## Production observations (read-only public pages)

Direct GETs reproduced the RU about/AZ favorites, EN empty-review Russian fallback and empty free FAQ. Public homepage map data lists free venues 287, 206, 205 and 81. No private records or production DB inspection.

The reported carousel duplication is NOT reproduced on the current live site: raw response has four originals with IDs 80, 73, 78, 21 exactly once. A real browser has four originals plus eight scrolling copies; all copies have `aria-hidden="true"` and no sequentially focusable links/buttons. Carousel application code therefore required no change. A server regression and local rendered checks protect that contract.

Sonic's public page displayed `Individual` in its summary, `Permanent place` in its facts, and group classes in the description. The template now distinguishes place type from class format. The stored class-format record was not inspected or overwritten, and no claim is made that a production data correction or deployment occurred.

## Verification

Fresh isolated PostgreSQL 17 container `kidsmap-template-qa-20261027`, network disabled, owned Unix socket and DB/role `qa_stage04`. `DJANGO_TESTING=1`; inherited credentials cleared before settings load; isolated LocMem cache/email/media/private-media, external integrations disabled. Fresh AZ/RU/EN gettext catalogs compiled under `.tmp`, shared `.mo` files untouched.

Initial RED: visible locale/type/free-price failures reproduced. Fixture preparation errors (wrong product enum and coordinate-derived district) were corrected before acceptance. The favorites regression was narrowed to the visible chip after a broad assertion also matched legitimate inline AZ dictionaries; the corrected regression failed against the original isolated catalogs and passed against the fixed catalogs. An initial RU duplicate gettext entry was replaced by reactivating the existing obsolete entry; all three final catalogs compiled successfully. A mistyped test class caused a loader error and was replaced by the actual six smoke methods. None of these aborted attempts is counted as PASS.

Final command (exit 0, **107 tests OK**, 37.576s):

```bash
.venv/bin/python .tmp/template-bugs-20261027/run.py test \
  catalog.testcases.test_public_template_bugs \
  catalog.testcases.test_parent_guides \
  catalog.testcases.test_home_parent_intent \
  catalog.testcases.pricing_plans \
  catalog.testcases.test_place_json_and_pricing_modes \
  catalog.testcases.public.TestPublicFilterCounts \
  catalog.testcases.public.PublicLanguageConsistencyTests \
  catalog.testcases.public.TestPublicPagesSmoke.test_add_place_and_legal_pages_open_in_languages \
  catalog.testcases.public.TestPublicPagesSmoke.test_add_place_page_explains_free_listing_moderation_and_actions_in_all_languages \
  catalog.testcases.public.TestPublicPagesSmoke.test_about_page_shows_extended_project_description \
  catalog.testcases.public.TestPublicPagesSmoke.test_en_reviews_page_sets_html_lang_and_translates_apply_button \
  catalog.testcases.public.TestPublicPagesSmoke.test_home_rail_uses_the_catalog_place_card \
  catalog.testcases.public.TestPublicPagesSmoke.test_home_place_card_reveals_first_number_on_demand \
  --keepdb --noinput -v1
```

`run.py` is an ignored local helper clearing the inherited environment and explicitly selecting the disposable profile `/tmp/kidsmap-task33-qa04-templates-20261027/settings.py`; run it only while its owned QA runtime exists.

Django system checks and migration drift check passed. Final gettext compilation passed for all three languages. `git -c core.whitespace=cr-at-eol diff --check -- <six changed source paths>` passed; the ordinary check treats the repository's existing CRLF as trailing whitespace.

Rendered browser acceptance: **90 final states** = six pages (home/add/about/reviews/detail/guide) × AZ/RU/EN × 390/768/1024/1280/1440. All requested text checks passed; no page overflow; four original rail cards; every browser copy aria-hidden with no sequential focus targets. Detail shows two consistent place-type cells, localized duration and localized tariff format. Free FAQ contains all four synthetic zero-price parks (plus two other eligible synthetic fixtures); its accordion was opened and inspected. Final browser error log empty. Screenshot inspection covered the mobile detail and the FAQ. A transient browser resize timeout was resumed at the missing state; a cached pre-final template was discarded by restarting only the owned local server before the final matrix.

Safe local evidence: `.tmp/template-bugs-20261027/{entry.json,before/,own-changes.diff,final-107.log,red*.log,green*.log,server-final.log,green-locales-v2/manifest.json}`. Entry hashes confirm every unrelated pre-existing dirty/untracked file remains unchanged.

NOT RUN: full-project suite, post-deploy verification, production data correction, release, commit, push, Google indexing checks. Production remains unchanged. The owned browser tab/server/container were stopped after verification; evidence and source remain for review.
