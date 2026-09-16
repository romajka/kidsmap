# Coordinate location release — 2026-09-16

User explicitly authorized push and production deployment, including the prepared changes and the museum correction. This supersedes the earlier read-only restriction for this release.

Scope: coordinate assignment, migration 0114, shared accessible animated preview, staff exceptions, prepared readiness unification and admin missing-field hints. Deploy existing branch `seo-indexability-20260916`, whose server and remote base is f8005bb0. No main-branch CI/full-suite trigger.

Preflight: clean server checkout; PostgreSQL/Redis healthy. Previous image 6c58d0c07e7a6128cf88d51ea96627631628e20fad8f06c9ff1eee2ff30b7cd6 retained as `kidsmap-web:before-coordinate-20260916`. Server-only recovery directory `/opt/kidsmap-coordinate-release-20260916` contains source reference, environment, database dump and static archive. Dump restored successfully into disposable isolated PostgreSQL17: 339 places. No backup or credentials copied into repository.

Migration adds metadata columns and override history; no bulk rewrite of existing place geography. The previous application image can run with the additive schema retained. Rollback should restore the saved application image and static archive, not overwrite later editorial data by restoring the whole database.

Fresh targeted checks: 22 coordinate server tests and 5 JS tests passed. Readiness/volunteer selection initially exposed five known RU assertion/AZ locale mismatches. Those five tests now explicitly use RU; business assertions unchanged. Final targeted result recorded after rerun. Full suite intentionally not run per user instruction.

Production museum lookup found two cards for the National Museum of Art: 320 already Sabail; 207 incorrectly Narimanov at 40.363203,49.831753. Correct only the identified erroneous administrative assignment after preview, retaining both records and their other content.

Readiness rerun: 78 tests, OK (1 skipped). One regression expectation was updated for the required new behavior: clearing coordinates also clears the district, so the form correctly reports three missing requirements (coordinates, phone, region), not two. The test now explicitly asserts the district error. Fixed the pre-existing RU map-point translation placeholder and supplied AZ/EN translations for the prepared district/region labels.

## Production result

Application revision `30a7a78b1ff96997880a116bdbaf6166a9a12921`, image `sha256:90ac338769b6fe28a796a2cd6bbfc91f2e3c77c7ca03d036f1c04334b89fc876`, activated successfully. Migration 0114 applied; `migrate --check`, `makemigrations --check --dry-run`, and Django `check` passed. Environment byte-identical to pre-release snapshot. Only web replaced; existing PostgreSQL/Redis containers retained and healthy.

Seven runtime source hashes match the reviewed local source. Actual runtime preview resolves museum coordinates to Baku/Sabail in AZ/RU/EN. Public health/home/RU catalog/EN catalog return 200. Three changed hashed static assets return 200 with byte-for-byte SHA-256 matches. Live Chromium at 390px loaded RU public home and RU admin login with HTTP200 and no JS page errors. A plain urllib request to the unprefixed admin login returned403; actual localized browser login loaded200. No authenticated production editing was performed as a browser smoke test.

Museum card207 corrected from `baku_narimanov` to `baku_sabail`, city `baku`, geometry version `baku-b2fff81f4da4cbab`. Correction ran in a transaction with expected coordinate/value guards, recorded administrative audit entries, and asserted every unrelated concrete field remained unchanged. Card320 was already Sabail and was left intact. The total remains339 places.

Recovery artifacts remain server-only at the path above. No whole-suite rerun. Full interactive map dragging and authenticated production volunteer/owner editing remain outside live smoke evidence; those editor flows were checked with isolated local fixtures before release.
