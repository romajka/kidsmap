# PostgreSQL cutover runbook

This is a one-way production cutover. Migration `0073` deliberately refuses
to run on MariaDB/MySQL. Keep the old MariaDB volume and pre-cutover web image
until the rollback window closes.

## Required production environment

```dotenv
DB_ENGINE=postgres
DB_NAME=kidsmap_prod
DB_USER=kidsmap_app
DB_PASSWORD=<new strong PostgreSQL password>
DB_HOST=postgres
DB_PORT=5432
REDIS_URL=redis://redis:6379/0

LEGACY_DB_NAME=kidsmap_prod
LEGACY_DB_USER=<current MariaDB user>
LEGACY_DB_PASSWORD=<current MariaDB password>
LEGACY_DB_ROOT_PASSWORD=<current MariaDB root password>
```

## Cutover order

1. Pull the prepared code without running the automatic deploy script.
2. Tag the currently running application image as `kidsmap-web:pre-postgres`.
3. Start `postgres` and `redis`, then build the new `web` image.
4. Run all migrations against the empty PostgreSQL database.
5. Put the site into maintenance mode or stop `web` so MariaDB becomes
   read-only from the application's point of view.
6. Create a final MariaDB SQL backup and a Django JSON fixture. The fixture
   must use `--natural-foreign --natural-primary` and exclude
   `contenttypes.contenttype` and `auth.permission`.
7. Run `flush --noinput` on PostgreSQL and load the fixture.
8. Run `database_inventory` against both databases and require exact per-model
   equality before starting the new application.
9. Start `web` with PostgreSQL, run Django checks and smoke-test `/`,
   `/catalog/`, and `/admin/login/`.
10. Keep MariaDB stopped but intact during the rollback window.

## Fixture command shape

```bash
python manage.py dumpdata --all \
  --natural-foreign --natural-primary \
  --exclude contenttypes.contenttype \
  --exclude auth.permission \
  --output /app/backups/kidsmap-cutover.json
```

## Validation

```bash
python manage.py database_inventory
python manage.py check
python manage.py makemigrations --check --dry-run
```

Do not delete `mariadb_data`, the final SQL dump, or the pre-cutover image
until production has been stable and explicitly accepted.
