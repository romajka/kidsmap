# Latest production release — 2026-09-15

Live runtime and URL verification completed by2026-09-15 06:23 UTC.

User authorization: «примени все последние правки», including earlier production and push authorization. This release includes all application changes from bfc2c28e plus verified release corrections. Previous production source:47859f54; localized URLs had already been activated for338 places.

## Scope and corrections

Admin AZ/RU/EN localization, language chooser, sorting and place editor; public header/menu; owner pricing/schedule editor and draft workflow. No new model/migration/dependency change, no repeat URL backfill. Final candidate source: `3aec046c3acedf83f68025ed53c23e034e14947e`; every tracked source file matched the committed SHA-256 inventory before building.

Before activation, corrected: owner Save-and-leave used browser storage that cannot persist uploaded photos; explicit admin RU/EN routes conflicted with a different language cookie and returned404; missing contextual Copy/Open translations; Russian gettext format/plural errors preventing the image build; new mobile sorting control overflow.

The owner flow now awaits successful server draft persistence before navigating. Error/offline/validation cases retain the form. Russian plural forms and lost format arguments were corrected in a bounded19-entry patch. Restored76 additional AZ/EN contextual entries lost during extraction (volunteer workspace/actions and count labels), verbatim from the previously committed translations. Compiled contextual lookups and count boundaries0/1/2/5 pass. Locale-sensitive regression tests explicitly choose the asserted language while retaining their original business assertions. The concurrency test creates its own required category after a previous transactional test flushes migration seed data.

Static consumer query versions were unified. Actual production uses hashed manifest filenames; this is defensive consistency, not evidence of a production stale-cache defect.

## Verification

Final candidate image `sha256:df2a418d96d22e218702391c9d792b967461ea32b51dc456ab3b50dd443501b8`: **753 tests PASS in600.771s**, zero failures/errors; Django checks pass; no migration drift. Image label matches3aec046c. Activation/live verification recorded below.

The initial image753-test run was stopped after known failures to avoid unnecessary server load. A complete local753-test diagnostic run ended with11 failures and1 error (312.218s): locale-sensitive test assumptions, missing AZ count contexts, missing category fixture, and two map expectations affected by a shared synthetic browser media directory. The latter passed with an empty isolated media directory; no map application code or assertions were changed. Focused reruns passed:152 owner tests,3 additional locale cases,4 media/concurrency cases. Final image verification below uses fresh tmpfs media and a no-network disposable PostgreSQL17 instance, DJANGO_TESTING=1 and synthetic credentials; only fixture password hashing is changed to MD5 for speed. No production database/cache/media or credentials are used by tests.

Real isolated browser verification on80d1df89 application source:45 admin cases (list/add/edit ×AZ/RU/EN ×five widths), zero JS and HTTP400+ errors. Actual language and sorting clicks pass. JSON names-only import/save/reload preserves pricing, structured schedule and URL triplet. Uploaded photo plus blocked localStorage persists as a server draft and an existing media file; HTTP500 and actual invalid-phone validation retain form data. Six owner header/form cases at390/1280 pass without overflow. Nine JS save-and-leave regressions pass.

Known limit: existing admin list layout overflows at390px in three language cases; the new sorting control fits and works. This release does not claim a comprehensive mobile redesign, a full accessibility audit or external integration certification. No synthetic staff or place records were added to production for UI testing.

## Production verification

Activated the exact3aec046c image above. Clean server checkout matches; `.env` is byte-identical to the pre-release snapshot; LOCALIZED_PLACE_URLS_ENABLED remains true. PostgreSQL and Redis were not restarted. `migrate --check` and production settings check passed; no new migrations were needed. Static collection succeeded.

Before/after aggregate Place audit matches exactly:338 total,75 public, all338 original AZ URLs preserved, zero missing public names/slugs, zero unexpected populated slugs. The fingerprint of all other Place fields is unchanged. Hidden untranslated-name fallbacks remain12 RU/13 EN, as before this deployment.

External HTTPS sweep:225 final language pages return200 with self-canonical, reciprocal hreflang and sitemap entries;123 changed legacy URLs return301 to the exact final200 target; zero errors (147.33s,3 workers,20s request timeout). All789 hidden language paths return404. Eleven changed hashed CSS/JS assets return200 and their SHA-256 values match the collected candidate files exactly.

Evidence: [aggregate verification](latest-production-release-verification.json), [isolated rendered browser checks](latest-production-release-browser.md). [Live browser checks](latest-production-release-live-browser.md): fresh AZ/RU/EN home loads at390/1280 pass header/menu interactions; explicit RU/EN admin login honors conflicting cookies sent to the actual admin host. No JS/HTTP400+ errors observed. The font-enabled RU desktop probe records3px document overflow; the cause/baseline was not established. Initial navigation/resize stability failures and optional resource exclusions are documented; no claim of perfect whole-site layout is made.

## Recovery

Server-only directory `/opt/kidsmap-latest-release-20260915`: fresh post-URL-activation DB backup, environment snapshot, previous source/image reference, static archive. Database restore into disposable no-network PostgreSQL17 succeeded with338 places. Previous image7328e063 supports localized URLs; retain flag1 and localized slug data during any rollback. Do not revert0113 or restore the whole DB over later editorial changes for a UI issue. Only web is replaced; PostgreSQL/Redis are retained.

## Exact affected test selection

Candidate image runner calls `check`, `makemigrations --check --dry-run`, then the equivalent of:

```sh
python -m django test \
  catalog.testcases.test_admin_i18n \
  catalog.testcases.test_place_sorting_and_filtering \
  catalog.testcases.permanent_place_wizard \
  catalog.testcases.owner \
  catalog.testcases.test_volunteer_admin \
  catalog.testcases.test_volunteer_dashboard \
  catalog.testcases.test_localized_place_admin \
  catalog.testcases.test_localized_place_urls \
  catalog.testcases.test_localized_place_seo \
  catalog.testcases.test_localized_place_backfill \
  catalog.testcases.test_place_json_and_pricing_modes \
  catalog.testcases.pricing_plans_relational \
  catalog.testcases.public \
  catalog.testcases.admin \
  catalog.testcases.test_json_roundtrip_audit \
  catalog.testcases.catalog \
  catalog.testcases.test_indexnow \
  catalog.testcases.test_volunteer_json_prompt \
  --noinput
```

The full repository CI suite was not run by this release; this753-test selection covers the changed workflows and localized URL contracts. The final documentation push uses `[skip ci]` to avoid an unrelated generic automatic redeployment after the exact candidate was manually verified and activated.

## Publication

Application fixes and these evidence-only documents are published together. Any post-activation checkout advance changes only `docs/`; the running image and complete application source remain3aec046c.
