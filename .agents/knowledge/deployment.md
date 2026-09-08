# Deployment and operations knowledge

> Актуализация 2026-09-08: [current snapshot](current-snapshot.md) уточняет LOCAL HEAD, volunteer workspace, MCP и native agents. Текст ниже — датированный срез 2026-09-06; production факты и untracked/dirty пометки не описывают сегодняшнее состояние. Перед использованием перепроверить source.

See [production observations](../../docs/agent-audits/PRODUCTION_READ_ONLY.md), especially E1/E4/E5. Read-only is default. No deployment, restart, env change or migration is authorized by this knowledge file.

## Actual path

`nginx1.24 →127.0.0.1:8000→Docker web/Gunicorn23→PostgreSQL17 + Redis7.4` on Ubuntu24.04.4. Checkout `/opt/kidsmap`; active branch readiness-legacy-migration at86a0b8c; local main df6fef3 with dirty features. Code is built into image; runtime mounts only media/staticfiles. Eight sampled image source hashes match production commit.

| Concern | Source of truth |
|---|---|
|Image build|`Dockerfile`, `.dockerignore`, `requirements.txt`|
|Services/environment/mounts|`docker-compose.yml`; inspect effective settings without exposing values|
|Start/process|`scripts/start-server.sh` and current container state|
|Deploy|`scripts/deploy-server.sh`; `.github/workflows/deploy.yml`|
|Migrations/static|`scripts/release-server.sh`|
|Backup/retention|`scripts/backup-db.sh` + both live cron entries|
|Proxy/static/media|`deploy/nginx/kidsmap.az.conf` + effective nginx config|
|Health|`src/config/urls.py` `/healthz` (no trailing slash)|

CI quality uses Python3.12/PostgreSQL17/Redis and Django migrations/check/drift/tests; push main then runs deploy-server via SSH. No latest CI run was fetched during audit. Local Python3.14 is a parity difference.

## Observed boundaries

- DEBUGfalse, SSL redirect/secure cookies/HSTS active; Redis cache and PostgreSQL enforced by settings. PostgreSQL port not host-published; web8000 binds all interfaces, external firewall reachability unverified.
- Media210MB/static118MB. Nginx direct media alias bypasses application route permissions unless separately denied. Specialist documents currently0; storage design still needs review.
- **Active image includes populated `.env`**. Docker ignore coverage is insufficient; future fix must consider existing image distribution/history and secret rotation based on exposure assessment. Do not print/copy secrets or rotate them during audit.
- Backup schedules03:15 cron.d and03:40 root cron;4regular gzip files valid with dump completion markers. No current regular-backup restore drill or off-host copy confirmed.
- Backup pipeline lacks pipefail before retention. Deploy failure trap does not restore old image/schema. These are real recovery risks, not proof that current service is down.
- Shared host has other applications; do not restart/change global services or audit unrelated applications without scope.

## Release handoff

Require exact reviewed revision/diff, clean scope, schema impact, preflight data counts, verified recoverable backup and rollback compatibility, then explicit user release approval. Existing explicit approval carries forward only within its scope; audit task overrides earlier broad deployment activity. Never call deploy-server to inspect state: it stashes/fetches/checkouts/builds/migrates/restarts.

After an approved future deployment verify active image/revision, migrations, static/media, health, localized auth/public/admin behavior. Failure recovery must name actual previous image and schema compatibility; `docker compose up web` alone is not rollback.

`DEPLOYMENT.md` remains useful history but includes stale MariaDB/db service, backup and cache examples; source + live evidence win. Google release prepared earlier is not active and not a reason to resume it during audit.
