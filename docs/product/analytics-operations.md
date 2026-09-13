# Analytics operations

Deploy in this order: schema, dual-read code, approved retention configuration, local collection, quality burn-in, owner analytics, then any public Favorites display. Local collection and owner analytics are disabled by default.

Set a dedicated `ANALYTICS_IDENTITY_HASH_KEY` and an explicit positive `ANALYTICS_RAW_EVENT_RETENTION_DAYS` before enabling `LOCAL_ANALYTICS_STORAGE_ENABLED`. A current versus previous 30-day report requires at least 60 days of usable history. Set `ANALYTICS_COLLECTION_STARTED_AT` only after the first reliable event is observed. Key rotation changes visitor continuity and must be recorded with a new hash version.

Run `reconcile_place_favorite_counts --dry-run` before applying repairs. Run `audit_analytics_quality` for aggregate-only diagnostics. Run `purge_analytics_events --dry-run` before every first purge or retention change. The scheduler owner must monitor command exit status and retry failed batches; rollback disables collection and owner UI without removing schema. Backup expiry remains governed by the approved backup retention policy and may delay physical disappearance from encrypted backups.

Public Favorites stays disabled until the product owner approves a non-null threshold, localized wording, and surfaces. Organization and Activity aggregation stays unavailable until architecture #33 supplies stable relations. No pricing, paid analytics, export, AI insight, or historical reconstruction is implied.

## Implementation verification

Implementation was verified on local branch `main` at baseline commit `a66842f` in the existing dirty worktree. No production reads or writes, deployment, commit, or push were performed.

- Analytics contract, event schema v2, metrics, Favorites, owner access, public threshold, retention commands, and tracking regression: 49 tests passed.
- Owner module regression: 150 tests passed.
- Account deletion and authentication regression: 64 tests passed.
- Existing admin analytics regression: 4 tests passed.
- Migrations `0108` through `0111` applied successfully to an isolated SQLite database; `makemigrations --check --dry-run` reports no model drift.
- Rendered owner analytics was checked in Firefox at 360, 768, 1366, and 1440 pixels in AZ, RU, and EN. The page had one `main` landmark, no horizontal overflow, and no console errors or warnings.
- The broader catalog module stops on a pre-existing query-budget assertion: `CatalogMapQueryEfficiencyTests.test_map_serialization_query_count_does_not_grow_with_schedules` expects four queries while the current map serializer issues a fifth query for related `Event` rows. The failing query path is outside this analytics change.

Before activation, approve the analytics retention period, provision the identity hash key, and set the collection start timestamp. Keep `LOCAL_ANALYTICS_STORAGE_ENABLED`, `OWNER_ANALYTICS_ENABLED`, and the public Favorites display disabled until those prerequisites and the public threshold/wording are approved.
