# Localized place URLs: isolated release scope

2026-09-14. Bounded release-reviewer preparation, authorized server implementation delegated to root. LOCAL HEAD `ef91dbe761f340a2c4d37bdc0b96638522aa6edf`. Root reports clean production checkout at the same HEAD; this agent did not contact production. Shared WORKTREE contains unrelated unfinished changes; none were reverted or committed by this agent.

## Deliverable

- `/tmp/kidsmap-url-release-prep/source`: HEAD source plus selected feature changes.
- `/tmp/kidsmap-url-release-prep/localized-place-urls.patch`: 32 files, 157990 bytes, applies to that exact HEAD.
- `/tmp/kidsmap-url-release-prep/manifest.json`: exact base and SHA256 for every resulting file.
- `prepare.py`, `verify_patch.py` in the same directory document reproducible selection and verification. They do not contact production.

Parent may add approved release operations/fixes and update the manifest; hashes here describe the handoff snapshot only. No secrets, production records, media, environment files or user-level logs were copied into the preparation tree.

## Included scope

Core/runtime: `src/catalog/models/place.py`, `services/place_urls.py`, migration `0113_place_localized_slugs.py`, backfill command, `views.py`, `context_processors.py`, `indexnow_signals.py`, `services/indexnow.py`, `services/volunteer_places.py`, `volunteer_middleware.py`.

Admin: `templates/admin/catalog/place/change_form.html`, `form/section_basics.html`, new `form/localized_urls.html`, `templates/admin/volunteer/edit.html`; `static/admin/js/kidsmap_place_json_import.js`, new `kidsmap_place_urls.js`, new `css/pages/kidsmap_place_urls.css`.

Partial files:

- `src/catalog/domain_admin/place.py`: only `localized_url_preview_view` and its `get_urls` registration. Sorting labels/descending ordering excluded.
- `docker-compose.yml`: only the web environment mapping `LOCALIZED_PLACE_URLS_ENABLED: "${LOCALIZED_PLACE_URLS_ENABLED:-0}"`, explicitly assigned as a required release fix by root.
- `src/config/settings.py`: only `LOCALIZED_PLACE_URLS_ENABLED` declaration. Jazzmin translations/language chooser excluded.
- `locale/{az,ru,en}/LC_MESSAGES/django.po`: append only 10 contextual URL strings and two URL heading/help strings. Existing HEAD entries and metadata retained unchanged. Current unrelated locale re-extraction had collapsed contextual Copy/Open in AZ/EN into generic entries: the release deliberately restores the required context using those existing translations. All 12 strings per language are present and nonempty.

Evidence: four new `test_localized_place_*` modules, `scripts/test_localized_place_urls.cjs`, original plan, local browser/release/validation reports.

Excluded: admin list/search/table redesign, public header changes, icon build/sprite changes, unrelated admin i18n and middleware changes, `test_admin_i18n.py`, place sorting tests and all other dirty/untracked files. The scope report itself is separate from the 32-file release patch.

## Dependencies and activation

- Migration adds three blank noneditable `varchar(60)` slug fields after catalog0112; no automatic catalogue data mutation. Backfill separately writes only empty localized fields with optimistic comparison and transaction timeouts.
- Existing pricing endpoint, staff permissions, volunteer ownership filtering, public URL builder, transliteration helper, schedule/pricing scripts and Django gettext catalogues are HEAD dependencies already present in the isolated tree.
- The shared basics template adds the URL block to staff and volunteer forms; both pages load its JS/CSS. The preview endpoint is POST, admin-protected, with volunteer ownership checks and public visibility gating.
- Production setting defaults false. **HEAD did not forward `LOCALIZED_PLACE_URLS_ENABLED`; the isolated release now adds the explicit web mapping with default0.** Root still must set the intended flag for staged/active containers and verify the effective boolean without printing the environment.
- Dockerfile compiles message catalogues into the image. New static assets and JSON-import cache-buster must be collected into the actual nginx-served static path. Compare deployed hashes after release.
- `.dockerignore` currently excludes `.env`, `.env.*`, `.git`, local caches and backup directory. Build from the isolated reviewed context, retaining its ignore file; do not copy server secrets/media/dumps into it.

## Staged release and recovery recommendations

Use a named candidate image built from the isolated tree; stage with explicit flag false. Retain the current image identifier and effective runtime configuration privately. Resolve schema compatibility and test backup restoration before touching production schema. Do not invoke `deploy-server.sh` as a convenience: it also fetches/checks out/stashes and can incorporate the wrong scope. `release-server.sh` additionally mutates site defaults and clears collected static; direct reviewed migration/static steps are narrower.

The production startup script refuses startup with pending migrations. Apply the approved additive migration before starting candidate production web. Keep public activation false until catalogue backfill and semantic URL review finish. Start/replace only web; do not restart PostgreSQL/Redis/global nginx for this feature without a concrete need.

Before public activation, retaining false and old behavior is supported. After permanent redirects are served, recovery must retain true, all localized fields and the compatible `place_detail`/canonical URL resolver. Returning to the pre-feature resolver risks cached redirect loops. Preserve a tested feature-compatible image and config; an old image alone is not a sufficient recovery plan. Never reverse0113 or restore the entire production DB over subsequent editorial changes simply to undo UI trouble.

## Checks and limits

Executed, all exit0:

- `verify_patch.py`: forward `git apply --check`, apply against exact HEAD in a fresh temporary directory, then SHA256 equality for all32 outputs.
- `git apply --check --reverse /tmp/kidsmap-url-release-prep/localized-place-urls.patch` from isolated source.
- `msgfmt --check` for all three isolated PO files, output under `/tmp`.
- `node --check` for both URL JS and JSON importer.
- Python `compileall` for URL service, model, admin and backfill command.

An initial reverse-check against the shared dirty WORKTREE failed only on deliberately excluded locale re-extraction; it was not an integration failure. The correct isolated tree reverse-check and clean HEAD forward-check passed.

Initial handoff did not run application/DB suites; the follow-up below records the newly executed isolated suite. Still not run by this agent: rendered browser suites, Docker build, real backup/restore, production migration/backfill/deploy or public HTTP checks. The historical705 tests and75 browser combinations belong to the prior dirty-WORKTREE validation and must not be presented as newly executed against this release artifact. Codebase graph tools were not used; this bounded hunk-selection task relied on exact git diff/source/report evidence.

Next: root verifies staged candidate, reviews all production URL candidates, integrates any scoped fixes, applies and verifies release, then commits/pushes only the authorized feature scope.


## Isolated release validation (follow-up)

Root explicitly assigned the one-line compose mapping and a fresh isolated release test run. The mapping was absent in a pre-change YAML assertion; after addition, system PyYAML parsed both compose files and confirmed the exact disabled-default substitution. The project venv has no PyYAML, so the first parser attempt failed before inspection; no dependencies were installed.

Runtime introspection confirmed `catalog.models.place` loads from `/tmp/kidsmap-url-release-prep/source/src/`, `TESTING=True`, PID-isolated media, LocMem cache/email. First test setup encountered the known root-level compatibility-package collision, fixed by running from the preparation directory. Restricted-network DB connection failed; automatic escalation review timed out once, and the explicitly permitted retry succeeded for the disposable local PostgreSQL test container only.

The first completed404-test attempt started without compiled gettext `.mo` files and failed47 translation assertions (104.217s). This is a preparation failure: the Dockerfile always compiles those catalogues. All three catalogues were then compiled into the isolated source and the full404 tests rerun in a new process with a new test DB/media. Do not count the initial run as a pass.

Exact test command (runner contains only sanitized `env -i`, isolated settings/source paths, and the shared Python interpreter):

```bash
/tmp/kidsmap-url-release-prep/run-tests test \
  catalog.testcases.test_localized_place_urls \
  catalog.testcases.test_localized_place_backfill \
  catalog.testcases.test_localized_place_seo \
  catalog.testcases.test_localized_place_admin \
  catalog.testcases.test_volunteer_json_prompt \
  catalog.testcases.test_volunteer_admin \
  catalog.testcases.test_volunteer_dashboard \
  catalog.testcases.test_indexnow \
  catalog.testcases.pricing_plans_relational \
  catalog.testcases.test_place_json_and_pricing_modes \
  catalog.testcases.public \
  catalog.testcases.test_json_roundtrip_audit --noinput
```

Patch snapshot under test: SHA256 `77be02bf35009475be190cbfa5332edd34261648de2e3e5b49eb784b9c965309`,32 files. Generated `.mo` files are image/test preparation outputs and are excluded from the source patch. Full synthetic logs remain under `/tmp/kidsmap-url-release-prep/`.

**Final compiled-catalogue run:404 tests,112.795s, OK, exit0.** Fresh `check`: no issues, exit0. Post-test clean HEAD patch application and all32 resulting SHA256 comparisons passed, confirming source remained the recorded snapshot during verification. Expected synthetic invalid-image and mocked IndexNow error messages occurred within passing tests. The missing staticfiles directory warning remains a test-environment limitation; no rendered-browser/static deployment assertion is made here.
