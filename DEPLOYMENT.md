# KidsMap Runbook

## Local (Linux/macOS)
```bash
cd /home/ramin/kidsmap
source .venv/bin/activate
./scripts/migrate.sh
GOOGLE_MAPS_API_KEY="YOUR_KEY" python manage.py runserver 0.0.0.0:8000
```

## Local (Windows PowerShell)
```powershell
cd C:\path\to\kidsmap
.venv\Scripts\activate
python manage.py migrate
$env:GOOGLE_MAPS_API_KEY="YOUR_KEY"
python manage.py runserver 0.0.0.0:8000
```

## Deploy via Git
```bash
git add -A
git commit -m "update"
git push origin main
```

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

## Server Deploy (one command)
Run this on server after each `git push`:
```bash
cd /opt/kidsmap
./scripts/deploy-server.sh
```
What it does:
1. Stashes local server edits (if any).
2. Fetches and fast-forwards the selected branch from `origin`.
3. Rebuilds the web image, runs explicit release tasks, then starts containers.
4. Verifies there is no model/migration drift (`makemigrations --check --dry-run`).
5. Runs `python manage.py check`.
6. Runs smoke checks for `/`, `/catalog/`, `/admin/` (with redirect follow and final `200`).

Optional custom branch:
```bash
./scripts/deploy-server.sh release
```

Useful overrides:
```bash
APP_BASE_URL=http://127.0.0.1:8000 ./scripts/deploy-server.sh main
REMOTE=origin ./scripts/deploy-server.sh main
BACKUP_DIR=/opt/backups ./scripts/deploy-server.sh main
```

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
sudo cp deploy/nginx/kidsmap.az.conf /etc/nginx/sites-available/kidsmap.az.conf
sudo ln -sf /etc/nginx/sites-available/kidsmap.az.conf /etc/nginx/sites-enabled/kidsmap.az.conf
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
1. `quality`: runs migrations + `makemigrations --check --dry-run` + `check` + `test` against MariaDB in CI.
2. `deploy`: runs `./scripts/deploy-server.sh main` only after `quality` passes on push to `main`.

Set these repository secrets in GitHub (`Settings -> Secrets and variables -> Actions`):
1. `DEPLOY_HOST` (example: `157.173.119.227`)
2. `DEPLOY_USER` (example: `root`)
3. `DEPLOY_SSH_KEY` (private SSH key that can access the server)

## Docker (local)
```bash
# one-time: copy env template
cp .env.example .env

# build image and run release tasks
docker compose -f docker-compose.yml build web
docker compose -f docker-compose.yml up -d db
docker compose -f docker-compose.yml run --rm web ./scripts/release-server.sh

# run in background
docker compose -f docker-compose.yml up -d web

# stop
docker compose -f docker-compose.yml down

# logs
docker compose -f docker-compose.yml logs -f web

# run only migrations in web container
docker compose -f docker-compose.yml run --rm web ./scripts/migrate.sh
```

## Production release checklist
1. Set env vars: `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=0`, `SERVE_MEDIA_FILES=0`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS`, `GOOGLE_MAPS_API_KEY`, `GOOGLE_ANALYTICS_MEASUREMENT_ID`, `GOOGLE_ANALYTICS_PROPERTY_ID`, `GOOGLE_APPLICATION_CREDENTIALS`, `DB_*`, `EMAIL_*`, `DEFAULT_FROM_EMAIL`, `MEDIA_CACHE_MAX_AGE`. Secrets must not be empty or placeholders.
2. Avoid editing tracked files on server (`docker-compose.yml`, `src/config/settings.py`); keep server-specific values in `.env`.
3. Ensure server can access GitHub via SSH (`./scripts/setup-github-ssh.sh` + `ssh -T git@github.com`).
4. Install/update nginx config from `deploy/nginx/kidsmap.az.conf`.
5. Run `./scripts/deploy-server.sh`.
6. Run `docker compose -f docker-compose.yml run --rm web ./scripts/release-server.sh` manually only if you need to re-apply release tasks.
7. Keep `SECURE_HSTS_PRELOAD=0` until every subdomain has been audited for permanent HTTPS support.
8. Ensure `MEDIA_ROOT_HOST` and `STATIC_ROOT_HOST` exist and are writable by container UID/GID `10001`; Nginx must serve the same directories directly.
9. Run `python manage.py check` (optional extra).
10. Verify:
   - `/healthz`
   - `/sitemap.xml`
    - `/robots.txt`

After deploying the image optimization pipeline for the first time, generate
responsive WebP variants for existing uploads:

```bash
docker compose -f docker-compose.yml exec -T web python manage.py optimize_images
```

The command is idempotent. Public media filenames are content/versioned by the
storage backend, so Nginx serves them with a one-year immutable cache policy.
   - `/admin/`

## Production performance follow-up
After deploy, validate that static/media are not the new bottleneck:

```bash
cd /opt/kidsmap
docker compose -f docker-compose.yml run --rm web ./scripts/release-server.sh
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

## Backup suggestion
1. The database backups are run separately from deployments (removed from `./scripts/deploy-server.sh`).
2. Set up a daily cron job to run `./scripts/backup-db.sh` once a day, which automatically retains a maximum of 5 backups.
3. Back up `media/` on the same schedule as the database.
4. To intentionally restore and republish the three featured demo clubs on the target server, run `docker compose -f docker-compose.yml exec -T web python manage.py restore_featured_places --force`. This overrides manual hiding, so use it only when that is intended.
