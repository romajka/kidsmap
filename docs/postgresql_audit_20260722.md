# PostgreSQL cutover audit — 2026-07-22

This report is intentionally stored on `postgres-cutover-20260722`. It does
not authorize a production cutover or a merge to `main`.

## Why categories returned after deploys

The root cause is confirmed in Git history. Before commit `c22953b`, every
release ran:

```sh
python manage.py seed_catalog_taxonomy
```

The command used `update_or_create()` with `is_active` in `defaults`. A deploy
therefore reactivated categories disabled in the admin. A category that had
been physically deleted was recreated because its code still existed in the
seed list.

Commit `c22953b` removed the command from `scripts/release-server.sh`, made an
unforced seed a no-op when categories already exist, and stopped forced seeds
from changing `is_active` on existing rows.

One remaining gap was found and fixed on this branch: the models implement
`archive()` and `restore()`, but Django Admin's standard delete hooks were not
overridden. `CategoryAdmin` and `SubcategoryAdmin` now route both single and
bulk deletion through soft-delete, so admin actions cannot physically remove
taxonomy rows.

## Automatic data creation audit

| Mechanism | Result |
| --- | --- |
| `seed_catalog_taxonomy` | Exists, but is no longer called by deploy/release. Unforced runs skip an existing taxonomy. |
| Other seed commands | `seed_catalog_demo_places` is manual and not called by startup or deploy. |
| Fixtures / `loaddata` | No application fixtures and no automatic `loaddata` invocation were found. |
| Import/populate commands | `import_places` is manual. It updates places, not categories. |
| `get_or_create` / `update_or_create` | Taxonomy writes are confined to the manual seed and one historical migration. |
| Data migrations | `0044` creates the original taxonomy once. It cannot rerun during a normal deploy while migration history is intact. Other data migrations don't recreate categories. |
| `AppConfig.ready()` | Only patches the Jazzmin paginator. It performs no database writes. |
| `post_migrate` / signals | No project receiver recreates categories or loads fixtures. |
| Entrypoint | Checks migration state, then starts Gunicorn. No seed or import runs. |
| Release script | Runs migrations, safe site defaults, translations, static files, and checks. Taxonomy seed is not called. |
| Deploy script | Builds one web image, runs the release script, and recreates the web service. No fixture load. |
| Dockerfile | Installs dependencies and starts `start-server.sh`. No data population. |
| Compose | Defines one `web` service. Public and admin hosts are routes of the same Django process. |
| Cache | Production uses shared Redis, avoiding per-worker stale local-memory cache. Cache does not create database rows. |

## Large legacy tables

Exact counts and date ranges were read from the stopped legacy MariaDB volume
through an isolated container with no network and no published port. MariaDB
`information_schema` row estimates are included only where useful; the
`COUNT(*)` values below are authoritative.

| Table | Exact rows | MariaDB total size | Date range | Needed by project | PostgreSQL estimate | Recommendation |
| --- | ---: | ---: | --- | --- | ---: | --- |
| `catalog_sitevisit` | 23,148,183 | 5,428,412,416 B (5.06 GiB) | `day`: 2026-03-11 — 2026-07-07 | No. Local visit persistence is disabled and the current PostgreSQL table is empty. | 6–8 GiB including indexes | Do not migrate. If re-enabled later, retain 30–90 days with scheduled deletion. |
| `django_session` | 23,147,960 | 5,311,938,560 B (4.95 GiB) | `expire_date`: 2026-03-25 — 2026-08-04; Django sessions have no creation timestamp | No. Sessions are temporary and users can authenticate again. | 5–7 GiB including indexes | Do not migrate. Run `clearsessions` regularly. |
| `catalog_funnelevent` | 15,165 | 7,946,240 B (7.58 MiB) | `created_at`: 2026-03-11 07:12:48 UTC — 2026-07-07 12:40:39 UTC | Potentially useful product analytics; some rows retain links to users and places. | Current PostgreSQL copy is 7,708,672 B | Keep at most 180 days. At the audited cutoff this retains the whole table. |

The first two tables alone account for about 10 GiB and 46.3 million rows.
They are technical state, not business records.

## Proposed retention decision

1. Exclude `catalog_sitevisit` completely.
2. Exclude `django_session` completely.
3. Transfer `catalog_funnelevent` for the last 180 days. At the current cutoff,
   this is all 15,165 rows; future repeat runs will remain bounded.
4. Transfer business audit records such as Django admin logs and ownership
   audits because they explain real administrative changes and are small.

The migration command implements this retention policy. Explicitly marked
`seed:catalog-demo*` rows are reviewed and removed only from the test target by
a separate dry-run-first cleanup command; the source and its backup remain
untouched.

## Isolated server rehearsal

The rehearsal ran on the production server without changing or restarting the
production `web`, `postgres`, or `redis` containers. It used a separate Git
worktree, Docker network, PostgreSQL container, and persistent volume
`kidsmap_pg_rehearsal_20260722`. The legacy MariaDB volume was attached only to
an isolated temporary source container and was not an application target.

Results after fixing generated permission-ID mapping, UTC conversion, and
migration-seed pruning:

| Check | Result |
| --- | ---: |
| Copied business tables | 41 |
| Source rows in scope | 16,866 |
| PostgreSQL rows in scope | 16,866 |
| Skipped rows | 0 |
| Content types mapped by natural key | 56 / 56 |
| Permissions mapped by natural key | 224 / 224 |
| Foreign-key / mandatory-relation checks | 64 passed |
| PostgreSQL sequences checked | 37 passed |
| Duplicate slugs | 0 |
| Final verification failures | 0 |

The transfer was run repeatedly against the same target. Every repeat selected
and upserted the same 16,866 rows without duplicates. `--prune-target` removed
27 Metro rows created by PostgreSQL data migrations but absent from MariaDB.
String primary-key sets are compared exactly because MariaDB and PostgreSQL
collations can legitimately return different textual `MIN/MAX` values.

Functional checks passed on the transferred test database: an existing staff
account opened Django Admin, an existing user opened favorites, taxonomy
create/rename/soft-delete worked, a place update survived a closed database
connection, and photo upload, review, favorite, and ownership-request writes
worked. All rehearsal records, files, and sessions were then deleted. A release
re-run reported no pending migrations; the web container was rebuilt,
recreated, and restarted successfully.

HTTP and Playwright checks returned 200 for the home page, catalog, filtered
catalog, admin login, and AZ/RU/EN pages. The catalog rendered 52 cards and the
map panel received 52 points with zero browser console errors or warnings. The
interactive Google layer showed its expected fallback because the rehearsal
container was intentionally not given the production Google Maps API key.

## Legacy content issues found (not migration loss)

The final data comparison still reports content-quality items for manual
review; they exist in MariaDB and were preserved exactly:

- two missing media files: Place `id=1` photo
  `places/rlyrlvtRQ5zj1DKp8nOA30zuBN2fj4bHUvF4PgVG.webp` and PlacePhoto `id=1`
  `places/gallery/LuxuryLiving.jpg`;
- 413 blank optional translation cells, mostly multilingual additional-info
  and extra-condition fields; required display names/descriptions account for
  only a small part of that total;
- 12 repeated normalized `Place.phone1` values and one repeated user-profile
  phone value. These can represent branches or duplicate accounts and must not
  be deleted automatically.

Detailed JSON reports remain on the server in
`/opt/kidsmap-pg-rehearsal/reports/`. The test PostgreSQL container is stopped,
but its persistent volume is retained for review. Temporary web, Redis,
legacy-source containers, static volume, test uploads, and sessions were
removed. The original MariaDB volume is intact.
