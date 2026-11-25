# KidsMap Runbook

## Local (Linux/macOS)
```bash
cd /home/ramin/kidsmap
source .venv/bin/activate
./scripts/migrate.sh
GOOGLE_MAPS_API_KEY="YOUR_KEY" GOOGLE_MAPS_MAP_ID="YOUR_MAP_ID" python manage.py runserver 0.0.0.0:8000
```

## Local (Windows PowerShell)
```powershell
cd C:\path\to\kidsmap
.venv\Scripts\activate
python manage.py migrate
$env:GOOGLE_MAPS_API_KEY="YOUR_KEY"
$env:GOOGLE_MAPS_MAP_ID="YOUR_MAP_ID"
python manage.py runserver 0.0.0.0:8000
```

## Publish and deploy

Review and commit only the intended files, push a feature branch, and merge through
`main` after the quality job passes. Never use an automatic stash to hide server edits.

The production workflow passes its exact tested `${{ github.sha }}` to the release
runner. It does not resolve `main` again as the version to build. Deploy jobs are
serialized without cancelling a running activation; the server uses the same
`/run/lock/kidsmap-release.lock` as dedicated releases.

For an operator-triggered deployment after that exact commit passes CI:

```bash
./scripts/deploy-production.sh <40-character-tested-SHA>
```

Both CI and this helper load the runner from that commit, so an older server
checkout cannot silently run the former unsafe script.

## Fast local suites
Для локальной проверки и AI-сессий используйте выборочные сьюты вместо полного `manage.py test`:

```bash
./scripts/run_kidsmap_tests.sh smoke
./scripts/run_kidsmap_tests.sh auth
./scripts/run_kidsmap_tests.sh public
./scripts/run_kidsmap_tests.sh admin
./scripts/run_kidsmap_tests.sh owner
./scripts/run_kidsmap_tests.sh catalog
./scripts/run_kidsmap_tests.sh full
```

## Pinned code-only server releases

```bash
cd /opt/kidsmap
./scripts/deploy-server.sh <40-character-tested-SHA>
```

The installed wrapper must already contain the pinned runner. For the first upgrade
use CI or `deploy-production.sh`, which loads it from the reviewed commit.

The runner refuses dirty checkouts, stale/non-main commits, unrelated live revisions,
uncommitted image overlays, changed Compose settings, and pending migrations.
It builds a clean `git archive` with an allowlisted Docker context. It does not modify
the checkout, stash changes, apply migrations, seed data, or restart PostgreSQL/Redis.
The live image revision label is the source of truth; server `HEAD` may be older.

Before activation it checks the candidate, migration drift and the applied migration
set, then saves the exact previous image ID, resolved Compose configuration, static
files and hashes. These contain secrets and stay in a private mode-0700 directory
under `/opt/kidsmap-releases/`. Keep these directories while their Compose files are
referenced by a running container.

A failure before activation leaves the existing application alone. A failure during
static collection, container replacement or health verification restores the previous
static manifest and immutable image. It verifies runtime settings and health again.
It never restores an old database over current user writes. If recovery fails, the
journal blocks further deployments until explicit recovery:

```bash
./scripts/deploy-server.sh --rollback /opt/kidsmap-releases/<release-directory>
```

A stopped/unlabelled application, initial installation, configuration changes or schema
migrations need a separate reviewed maintenance procedure: enumerate writers, prepare
and test database/media backups, assess backward compatibility, apply the batch, and
verify the schema before returning to the code-only path. `scripts/release-server.sh`
is a manual migration tool; do not use it to bypass a blocked automatic release.

If baseline-source-drift.json lists image overlays, reconcile those source files into
the release branch first. Do not remove the guard or relabel the image to force a pass.

## Fix `git pull` on server via SSH to GitHub
If server deploy fails with `Permission denied (publickey)` or `Could not read from remote repository`, configure GitHub SSH on the VPS once:

```bash
cd /opt/kidsmap
chmod +x ./scripts/setup-github-ssh.sh
./scripts/setup-github-ssh.sh
```

What happens:
1. Generates `~/.ssh/id_ed25519` if it does not exist.
2. Adds `github.com` to `known_hosts`.
3. Writes `~/.ssh/config` with the correct identity file.
4. Prints the public key that must be added in GitHub.

Then:
1. Copy the printed public key.
2. Add it in GitHub:
   - either account-level `Settings -> SSH and GPG keys`
   - or repo-level `Repository -> Settings -> Deploy keys` with read access
3. Verify on server:

```bash
ssh -T git@github.com
cd /opt/kidsmap
git fetch origin main
git pull --ff-only origin main
```

Expected `ssh -T` behavior: GitHub usually returns a success message with exit code `1`. That is normal.

## Nginx production config for static/media cache and compression
Repo now includes a ready production vhost:

`deploy/nginx/kidsmap.az.conf`

It does three important things:
1. Serves `/static/` directly from `/opt/kidsmap/staticfiles/` with long-lived immutable cache.
2. Serves `/media/` directly from `/opt/kidsmap/media/` with explicit cache headers.
3. Enables gzip for CSS, JS, JSON, SVG and similar text assets before requests hit Django.

Install/update it on the server:

```bash
cd /opt/kidsmap
sudo cp deploy/nginx/kidsmap.az.conf /etc/nginx/sites-available/kidsmap
sudo ln -sfn /etc/nginx/sites-available/kidsmap /etc/nginx/sites-enabled/kidsmap
sudo nginx -t
sudo systemctl reload nginx
```

If you use Certbot and another existing site file, merge the `location /static/`, `location /media/`, `gzip ...` and `proxy_pass` parts into the active server block instead of blindly replacing the whole file.

Optional Brotli:
- the config includes commented Brotli directives
- enable them only if `nginx -V` shows a Brotli module
- otherwise keep gzip only

Quick validation:

```bash
curl -I https://kidsmap.az/static/css/site.css
curl -I https://kidsmap.az/static/js/home_hero_slider.js
curl -I https://kidsmap.az/media/site/gallery/home-hero-01-family-studio.jpg
```

Expected headers:
1. `/static/...` -> `Cache-Control: public, max-age=31536000, immutable`
2. `/media/...` -> `Cache-Control: public, max-age=86400`
3. CSS/JS should be served by nginx, not proxied through Django
4. When client sends `Accept-Encoding: gzip`, nginx should return `Content-Encoding: gzip` for compressible assets

## Auto-deploy on push (GitHub Actions)
Repo includes workflow: `.github/workflows/deploy.yml`  
It has two stages:
1. `quality`: runs migrations + `makemigrations --check --dry-run` + `check` + `test` against PostgreSQL in CI.
2. `deploy`: runs the runner from the exact tested commit only after `quality` passes on push to `main`.

Set these repository secrets in GitHub (`Settings -> Secrets and variables -> Actions`):
1. `DEPLOY_HOST` (example: `157.173.119.227`)
2. `DEPLOY_USER` (example: `root`)
3. `DEPLOY_SSH_KEY` (private SSH key that can access the server)

## Docker (local)
```bash
# one-time: copy env template
cp .env.example .env

# build image and run release tasks
docker compose build web
docker compose up -d db
docker compose run --rm web ./scripts/release-server.sh

# run in background
docker compose up -d web

# stop
docker compose down

# logs
docker compose logs -f web

# run only migrations in web container
docker compose run --rm web ./scripts/migrate.sh
```

## Production release checklist
1. Set env vars: `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=0`, `SERVE_MEDIA_FILES=1`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS`, `GOOGLE_MAPS_API_KEY`, `GOOGLE_MAPS_MAP_ID`, `GOOGLE_ANALYTICS_MEASUREMENT_ID`, `GOOGLE_ANALYTICS_PROPERTY_ID`, `GOOGLE_APPLICATION_CREDENTIALS`, `INDEXNOW_KEY`, `DB_*`, `EMAIL_*`, `DEFAULT_FROM_EMAIL`, `MEDIA_CACHE_MAX_AGE`.
2. Avoid editing tracked files on server (`docker-compose.yml`, `src/config/settings.py`); keep server-specific values in `.env`.
3. Ensure server can access GitHub via SSH (`./scripts/setup-github-ssh.sh` + `ssh -T git@github.com`).
4. Install/update nginx config from `deploy/nginx/kidsmap.az.conf`.
5. Run the pinned release with the exact SHA from a successful quality job.
6. Pending migrations stop automatic deployment; use the reviewed maintenance procedure described above.
7. Run `python manage.py check` (optional extra).
8. Verify:
   - `/healthz`
   - `/sitemap.xml`
   - `/robots.txt`
   - `/admin/`

## IndexNow

The key is never stored in git. Generate a value containing 8-128 letters,
numbers or hyphens and put it only in `/opt/kidsmap/.env`:

```bash
python -c 'import secrets; print(secrets.token_hex(16))'
sudoedit /opt/kidsmap/.env
```

Required and optional values:

```dotenv
INDEXNOW_KEY=replace-with-generated-key
INDEXNOW_ENDPOINT=https://api.indexnow.org/indexnow
INDEXNOW_TIMEOUT_SECONDS=3
INDEXNOW_MIN_INTERVAL_SECONDS=3600
```

After the application is restarted, verify the public key file. Replace the
placeholder in the URL with the same environment value:

```bash
curl -fsS https://kidsmap.az/replace-with-generated-key.txt
```

Preview the current batch without contacting IndexNow:

```bash
docker compose exec -T web python manage.py submit_indexnow --dry-run
```

Send one canonical URL as a controlled manual check:

```bash
docker compose exec -T web python manage.py submit_indexnow --limit 1 --force
```

Send all current public place URLs and indexable SEO landing URLs:

```bash
docker compose exec -T web python manage.py submit_indexnow
```

Automatic submissions run after a content change commits. Redis stores a
60-second per-URL lease and starts the `INDEXNOW_MIN_INTERVAL_SECONDS`
cooldown only after HTTP 200 or 202. A failed submission releases its lease,
so another edit can send the URL immediately. This also works without cron.
The first change after upgrading may resend a URL because older Redis markers
included failed submissions.

To retry transient failures even when nobody edits the content, optionally
install this entry on the Docker host with `crontab -e`:

```cron
* * * * * cd /opt/kidsmap && docker compose exec -T web python manage.py indexnow_retry
```

Each run sends up to 10,000 due URLs. HTTP 429, 5xx and network failures
schedule up to three automatic retries in Redis, due 1, 5 and 30 minutes
after the preceding failure. A successful edit clears any pending retry.
HTTP 400, 403 and 422 end the retry sequence and log an error. Check the
IndexNow key and URL before manually resubmitting.

## Production performance follow-up
After deploy, validate that static/media are not the new bottleneck:

```bash
cd /opt/kidsmap
docker compose run --rm web ./scripts/release-server.sh
curl -I https://kidsmap.az/static/css/site.css
curl -I https://kidsmap.az/static/js/home_map.js
curl -I https://kidsmap.az/media/site/your-heavy-file.png
find /opt/kidsmap/media -type f \( -name '*.png' -o -name '*.jpg' -o -name '*.jpeg' -o -name '*.webp' \) -printf '%s %p\n' | sort -nr | head -20
```

What to verify:
1. Static responses include long-lived `Cache-Control`.
2. Media responses include `Cache-Control` and correct `Content-Type`.
3. The old public TTF font is no longer requested from the homepage.
4. The largest production media files are identified explicitly instead of guessed.
5. CSS/JS are compressed by nginx when requested with `Accept-Encoding: gzip`.

If large production PNG/JPG files are still live but absent from git, replace them with optimized files under the same path so current URLs keep working.

## SMTP test (Brevo or other provider)
```bash
python manage.py send_test_email your-address@example.com
```
If SMTP is configured correctly, command prints `Test email sent ...`.

## Service emails (workflow outbox)
Moderation decisions, team invitations and similar events are written to an outbox
in the same transaction as the change; nothing is emailed until the outbox runner sends it.
Without a schedule these emails stay `pending` forever (the account inbox still shows them).

1. Check SMTP first: `docker compose exec -T web python manage.py send_test_email you@example.com`.
2. Preview what is due: `docker compose exec -T web python manage.py deliver_workflow_outbox`.
3. Schedule the runner (every 2 minutes) with `crontab -e`:
   ```
   */2 * * * * cd /opt/kidsmap && ./scripts/deliver-workflow-outbox.sh >> /var/log/kidsmap-outbox.log 2>&1
   ```
4. Failed SMTP attempts are retried with backoff (2, 4, 8, 16 minutes) and marked `failed` after 5 attempts.

## Backup suggestion
1. The database backups are run separately from deployments (removed from `./scripts/deploy-server.sh`).
2. Set up a daily cron job to run `./scripts/backup-db.sh` once a day, which automatically retains a maximum of 5 backups.
3. Back up `media/` on the same schedule as the database.
4. To restore the three featured demo clubs manually on the target server, run `docker compose exec -T web python manage.py restore_featured_places`.
