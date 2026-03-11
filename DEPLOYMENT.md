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
python manage.py collectstatic --noinput
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
6. Runs smoke checks for `/`, `/catalog/`, `/admin/` (with redirect follow and final `200`).

Optional custom branch:
```bash
./scripts/deploy-server.sh main
```

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
1. Set env vars: `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=0`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS`, `GOOGLE_MAPS_API_KEY`, `DB_*`, `EMAIL_*`, `DEFAULT_FROM_EMAIL`.
2. Avoid editing tracked files on server (`docker-compose.yml`, `src/config/settings.py`); keep server-specific values in `.env`.
3. Run `./scripts/deploy-server.sh`.
4. Run `python manage.py check` (optional extra).
5. Verify:
   - `/healthz`
   - `/sitemap.xml`
   - `/robots.txt`
   - `/admin/`

## SMTP test (Brevo or other provider)
```bash
python manage.py send_test_email your-address@example.com
```
If SMTP is configured correctly, command prints `Test email sent ...`.

## Backup suggestion
1. Daily MariaDB backup (`mysqldump`) with timestamp.
2. Daily `media/` backup.
