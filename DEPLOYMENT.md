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
python manage.py collectstatic --clear --noinput
$env:GOOGLE_MAPS_API_KEY="YOUR_KEY"
python manage.py runserver 0.0.0.0:8000
```

## Deploy via Git
```bash
git add -A
git commit -m "update"
git push origin main
```

## Server Deploy (one command)
Run this on server after each `git push`:
```bash
cd /opt/kidsmap
./scripts/deploy-server.sh
```
What it does:
1. Stashes local server edits (if any).
2. Pulls latest `origin/main`.
3. Rebuilds/restarts Docker containers.
4. Verifies there is no model/migration drift (`makemigrations --check --dry-run`).
5. Runs `python manage.py check`.
6. Restores the three featured public clubs if they were quarantined or edited.
7. Runs smoke checks for `/`, `/catalog/`, `/admin/` (with redirect follow and final `200`).

Optional custom branch:
```bash
./scripts/deploy-server.sh main
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

# build + run
docker compose up --build

# run in background
docker compose up -d --build

# stop
docker compose down

# logs
docker compose logs -f web

# run only migrations in web container
docker compose run --rm web ./scripts/migrate.sh
```

## Production release checklist
1. Set env vars: `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=0`, `SERVE_MEDIA_FILES=1`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS`, `GOOGLE_MAPS_API_KEY`, `GOOGLE_ANALYTICS_MEASUREMENT_ID`, `GOOGLE_ANALYTICS_PROPERTY_ID`, `GOOGLE_APPLICATION_CREDENTIALS`, `DB_*`, `EMAIL_*`, `DEFAULT_FROM_EMAIL`, `MEDIA_CACHE_MAX_AGE`.
2. Avoid editing tracked files on server (`docker-compose.yml`, `src/config/settings.py`); keep server-specific values in `.env`.
3. Ensure server can access GitHub via SSH (`./scripts/setup-github-ssh.sh` + `ssh -T git@github.com`).
4. Install/update nginx config from `deploy/nginx/kidsmap.az.conf`.
5. Run `./scripts/deploy-server.sh`.
6. Run `python manage.py check` (optional extra).
7. Verify:
   - `/healthz`
   - `/sitemap.xml`
   - `/robots.txt`
   - `/admin/`

## Production performance follow-up
After deploy, validate that static/media are not the new bottleneck:

```bash
cd /opt/kidsmap
docker compose exec -T web python manage.py collectstatic --clear --noinput
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
1. Run `./scripts/backup-db.sh` before each deploy. It writes a timestamped MariaDB dump to `backups/`.
2. Back up `media/` on the same schedule as the database.
3. To restore the three featured demo clubs after a deploy, run `./.venv/bin/python manage.py restore_featured_places` on the target server.
