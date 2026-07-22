# PostgreSQL cutover runbook

Work must stay on `postgres-cutover-20260722` until the owner explicitly
approves the production cutover. Migration `0073` is a one-way PostgreSQL
boundary and deliberately refuses MariaDB and SQLite.

## Environment

Application processes receive one connection variable:

```dotenv
DATABASE_URL=postgresql://kidsmap_app:<url-encoded-password>@postgres:5432/kidsmap_prod
REDIS_URL=redis://redis:6379/0
```

`DB_NAME`, `DB_USER`, and `DB_PASSWORD` are used only by the official
PostgreSQL container to initialize its volume. Passwords belong in the server
`.env`, never in Git. During a rehearsal only, add a read-only legacy alias:

```dotenv
LEGACY_DATABASE_URL=mariadb://<reader>:<url-encoded-password>@db:3306/kidsmap_prod
```

Production settings reject a missing or non-PostgreSQL `DATABASE_URL`. There
is no MariaDB or SQLite fallback.

## Rehearsal on a separate PostgreSQL database

1. Take a final SQL backup of MariaDB and preserve its Docker volume.
2. Start a separate PostgreSQL service/volume and run `migrate --noinput`.
3. Keep the normal web application on its current database.
4. Run the repeatable batch transfer:

```bash
python manage.py migrate_legacy_database \
  --source legacy \
  --target default \
  --batch-size 1000 \
  --analytics-days 180 \
  --report /app/backups/migration-report.json
```

The command preserves primary keys and relations, upserts by primary key for
safe repeat runs, adapts values through the target Django fields, fills new
schema defaults, uses transactions per table, and resets PostgreSQL sequences.
It never transfers `django_session` or `catalog_sitevisit`. Funnel analytics
are limited to 180 days.

5. Review explicitly marked demo data, then remove it only from the test target:

```bash
python manage.py cleanup_migration_junk --database default
python manage.py cleanup_migration_junk --database default --apply
```

The first command is a dry run. The cleanup refuses a non-test database unless
`--allow-production` is deliberately supplied.

6. Verify counts, ID ranges, foreign keys, mandatory relations, duplicate
   slugs/phones, translations, image paths, and sequences:

```bash
python manage.py verify_database_transfer \
  --source legacy \
  --target default \
  --analytics-days 180 \
  --report /app/backups/verification-report.json
```

Any count, relationship, slug, or sequence failure makes the command exit
non-zero. Missing translations, duplicate phone values, and missing media are
reported for review because some may be valid legacy content issues.

7. Run the functional checklist on the test target: existing admin/user login,
   taxonomy create/rename/archive, place and photo editing, AZ/RU/EN pages,
   catalog, filters, map, reviews, favorites, owner requests, restart, rebuild,
   migrate, and redeploy.

## Production cutover (only after explicit approval)

Stop application writes, make the final backup, rerun the same transfer into a
fresh PostgreSQL target, require a clean verification report, then start every
web container with the same `DATABASE_URL`. Run smoke checks for `/`,
`/catalog/`, and `/admin/login/` after restart and rebuild.

Keep the MariaDB volume, final SQL dump, and pre-cutover web image throughout
the rollback window. Never use a rollback that silently changes production
back to SQLite or MariaDB.
