# Coordinate location release — 2026-09-16

User explicitly authorized push and production deployment, including the prepared changes and the museum correction. This supersedes the earlier read-only restriction for this release.

Scope: coordinate assignment, migration 0114, shared accessible animated preview, staff exceptions, prepared readiness unification and admin missing-field hints. Deploy existing branch `seo-indexability-20260916`, whose server and remote base is f8005bb0. No main-branch CI/full-suite trigger.

Preflight: clean server checkout; PostgreSQL/Redis healthy. Previous image 6c58d0c07e7a6128cf88d51ea96627631628e20fad8f06c9ff1eee2ff30b7cd6 retained as `kidsmap-web:before-coordinate-20260916`. Server-only recovery directory `/opt/kidsmap-coordinate-release-20260916` contains source reference, environment, database dump and static archive. Dump restored successfully into disposable isolated PostgreSQL17: 339 places. No backup or credentials copied into repository.

Migration adds metadata columns and override history; no bulk rewrite of existing place geography. The previous application image can run with the additive schema retained. Rollback should restore the saved application image and static archive, not overwrite later editorial data by restoring the whole database.

Fresh targeted checks: 22 coordinate server tests and 5 JS tests passed. Readiness/volunteer selection initially exposed five known RU assertion/AZ locale mismatches. Those five tests now explicitly use RU; business assertions unchanged. Final targeted result recorded after rerun. Full suite intentionally not run per user instruction.

Production museum lookup found two cards for the National Museum of Art: 320 already Sabail; 207 incorrectly Narimanov at 40.363203,49.831753. Correct only the identified erroneous administrative assignment after preview, retaining both records and their other content.

Readiness rerun: 78 tests, OK (1 skipped). One regression expectation was updated for the required new behavior: clearing coordinates also clears the district, so the form correctly reports three missing requirements (coordinates, phone, region), not two. The test now explicitly asserts the district error. Fixed the pre-existing RU map-point translation placeholder and supplied AZ/EN translations for the prepared district/region labels.
