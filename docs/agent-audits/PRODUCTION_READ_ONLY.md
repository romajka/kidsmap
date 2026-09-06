# Production evidence — 2026-09-06

This is a sanitized observation report, not production logs or a database export. All server actions in this task were inspection commands, file reads/stat, catalog queries, aggregate SELECTs, non-executing EXPLAIN and transactions explicitly marked READ ONLY. No restart/deploy/config/data/migration/backup/cleanup operations were run in this task.

## E1 — identity and runtime

- Ubuntu24.04.4 LTS; host timezone observed CEST (application Asia/Baku).
- Checkout `/opt/kidsmap`, clean branch `readiness-legacy-migration`, HEAD `86a0b8cf64a8835f310a608a3428c60f1fc5341a`.
- LOCAL main `df6fef3784a6bae6b7ddce90cd41a392d9f9e6bf` plus dirty/untracked features. Python LOCAL3.14.0 versus production3.12.13.
- Production image source SHA256 matched `git show 86a0b8c:<path>` for eight sampled files: requirements, settings, URLs, SEO, readiness, content_quality, Place model and backup script. This is sampled image provenance, not an exhaustive image attestation.
- Web: Gunicorn23.0.0/Django6.0.2, psycopg3.2.10, redis client5.2.1, WhiteNoise6.9.0. No allauth installed in active image; local65.19.2.
- nginx1.24.0 and Docker services active; web running; PostgreSQL/Redis containers healthy. No separate application virtualenv: packages live in the Python Docker image. Gunicorn is managed through container restart policy/start-server.sh.
- Effective DEBUG=false, TESTING=false; secure session/CSRF cookies, HttpOnly session, SSL redirect true, HSTS31536000; cache Redis, DB PostgreSQL. Google OAuth not configured.

## E2 — database connection and schema

- PostgreSQL17.10; database size23MB; one application schema public,50 tables.
- Queries used `BEGIN READ ONLY`, default_transaction_read_only where psql was used, statement timeout15–20s and lock timeout2s. `SHOW transaction_read_only` returned on.
- **Application DB connection role is superuser**, with createdb/createrole too. This is confirmed through the application's connection, not inferred from the root SSH login.
- Constraints:72 FK,67 CHECK,24 UNIQUE,50 PRIMARY KEY; zero unvalidated constraints. All72 FK orphan count queries returned0. These checks cover declared FKs, not every semantic relationship.
- No invalid indexes. Prefix/column-coverage heuristic found no unindexed FK candidate. This does not establish optimal indexes for all workloads.
- Existing pricing composite indexes `(place_id,is_active,charge_role,currency)` and `(place_id,sort_order,id)`; unique schedule `(place_id,weekday)`; funnel composite day/event and event/created indexes. auth_user has unique username, no normalized email unique index.
- Non-executing EXPLAIN for a limited published Place listing selected seq scan + sort;321 rows makes this insufficient evidence of an index defect. EXPLAIN ANALYZE was not run.
-119 applied migrations: catalog100 through0100_place_price_mode; auth12; admin3; contenttypes2; sessions1; catalog_moderation1. allauth migrations and local catalog0101 absent.

## E3 — exact data aggregates

| Domain / table | Rows |
|---|---:|
| Place |321|
| PricingPlan |78 across25 places|
| PlaceScheduleDay / Interval |2100 /2948|
| Category / Subcategory |17 /106|
| Region / District / MetroStation |73 /12 /27|
| User / UserProfile / UserEmailVerification |18 /18 /10|
| User permission rows / auth groups |136 /0|
| Ownership request / request audit |6 /12|
| Team membership / invitation |0 /0|
| PlaceChangeAudit / Django admin log |437 /779|
| PlacePhoto / PlaceLike |53 /10|
| PlaceReview / reaction |1 /1|
| SiteReview / reaction / SiteGalleryImage |1 /4 /9|
| FunnelEvent / SiteVisit |15165 /0|
| SEOAuditRun / SEOIssue / SEOChange |6 /68 /0|
| Event / EventPhoto |0 /0|
| Specialist / SpecialistDocument / practice locations / specialist reviews |0 /0 /0 /0|
| Specialist specializations / specialist schedules and intervals |29 /0 and0|
| Django sessions |74|

Largest tables: FunnelEvent7528kB, Place1288kB, schedule intervals432kB, days360kB. pg_stat row estimates were separated from exact counts above.

- Place status:237 draft,83 published,1 rejected. Published status count does not equal public-visible count.
- All321 have price_mode=tariffs; schedule modes regular320/variable1; no temporary Place.
- Legacy JSON nonempty2; scalar price range230, monthly228, per-lesson1, per-eight-lessons0. **266 places have scalar prices and no relational plans.** Scalars can also be current projections; do not call all populated scalar rows obsolete.
- Structured schedule coverage300 places; text schedule3 (overlap possible). No duplicate place/weekday groups.
-202 places lack at least one coordinate;256 have primary photo references;8 have owner references. These include drafts; do not classify all as broken public cards.
-0 Place/Subcategory category mismatches in join; string location semantics were not exhaustively validated.
-2 normalized nonempty email duplicate groups involve6 users;18 users include1 superuser and6 staff. No identities/email values are stored here. Local migration0101 requires owner decisions before activation.

## E4 — storage/security boundaries

- `/app/media` and `/app/staticfiles` map to `/opt/kidsmap/media` and `/opt/kidsmap/staticfiles`; host sizes210MB/118MB. No source-code bind mount in current compose.
-309 primary/gallery references checked with file stat:2 missing,0 resolved outside media root. No document contents read. Missing references require classification before repair/delete.
- Active image contains `/app/.env`. Boolean-only check confirmed populated secret-bearing settings (Django secret, DB URL/password, SMTP password); **values were neither printed nor copied**. COPY build context + missing .env exclusion is a confirmed packaging risk, not proof of external disclosure.
- Effective nginx `/media/` aliases the whole media directory with no protected_docs exception.0 SpecialistDocument rows: private-document bypass is a latent boundary issue, not observed exposure of existing documents.
- Host port8000 listens on all IPv4/IPv6 interfaces; PostgreSQL5432 not host-published. External reachability of8000/firewall posture was not established.
- `nginx -T` passed. Effective config includes public/admin hosts, /static and /media aliases, proxy to127.0.0.1:8000, body limit25MB. Other hosted applications were observed but not audited.

## E5 — operations/backups/log aggregates

- Root cron runs backup-db.sh at03:40; `/etc/cron.d/kidsmap-db-backup` also schedules it at03:15 (host timezone). Review duplicated schedules/retention together; do not remove either during audit.
-4 regular `.sql.gz` files observed; all four passed gzip decompression and contained dump header/completion markers. This is file-integrity evidence, **not a restore test**.
- A previous task restored its separate pre-OAuth dump on an isolated PostgreSQL and ran186 tests. That historical result is not a restore drill of the regular backup schedule in this task.
- Backup script source uses a pg_dump|gzip pipeline without pipefail; dump failure can be masked before retention. Current valid artifacts do not refute this failure path.
- Disk145GB total,73GB used,72GB free (~51% used). Backup artifact presence/size checked; no off-host backup destination, recovery objective or restore schedule verified.
- Recent2000 shared nginx access-log entries:200=1668,404=304,301=17,400=8,499=1,502=1,403=1. Shared log includes other activity/scanners; not a KidsMap availability/error-rate metric. Raw lines/URLs/IPs are not retained in repository reports.
- Certbot/logrotate/system timers active. No application-specific systemd worker timer was established; cron and process-local IndexNow are documented in code.

## E6 — limits and reproducibility

Read-only probes used information_schema, pg_tables/pg_constraint/pg_indexes/pg_stat_user_tables, django_migrations, counts/joins and file metadata. No arbitrary row samples, tokens, private documents or secret values were exported. Runtime flags, DB privileges, schema and source hashes are point-in-time evidence. Browser observations and local regression results live in their separate role reports. Recheck drift before any future implementation or deployment.

## E7 — verification-authentication boundary follow-up

Read-only aggregate query found10 active users with is_verified UserEmailVerification records. Production `services/email_verification.py` and `views.py` SHA256 exactly match their files at86a0b8c; service/controller/repository are unchanged between that commit and local HEAD. The security role reproduced anonymous authentication with an incorrect code on a fresh isolated in-memory SQLite fixture, CSRF checks enabled, with no pending signup session. See security.md for full source trace and evidence limits. **No corresponding request was sent to production, and no incident/exploitation history was established.** The live code/data preconditions are present; this is an urgent fix decision, not permission granted by this audit to change code.
