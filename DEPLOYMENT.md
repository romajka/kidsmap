# KidsMap Runbook

## Local (Linux/macOS)
```bash
cd /home/ramin/kidsmap
source .venv/bin/activate
python manage.py migrate
python manage.py collectstatic --noinput
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

## Docker (local)
```bash
# build + run
docker compose up --build

# run in background
docker compose up -d --build

# stop
docker compose down

# logs
docker compose logs -f web
```

## Production release checklist
1. Set env vars: `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=0`, `DJANGO_ALLOWED_HOSTS`, `GOOGLE_MAPS_API_KEY`.
2. Run `python manage.py migrate`.
3. Run `python manage.py collectstatic --noinput`.
4. Run `python manage.py check`.
5. Verify:
   - `/healthz`
   - `/sitemap.xml`
   - `/robots.txt`
   - `/admin/`

## Backup suggestion
1. Daily DB backup (`db.sqlite3`) with timestamp.
2. Daily `media/` backup.
