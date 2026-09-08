# DevOps audit — 2026-09-08

Role release-reviewer, executed locally by coordinator /root after reading actual `.agents/agents/release-reviewer/agent.md`. Not an independently spawned release worker. LOCAL HEAD d75b34f4db5d4ba484cf8392ff3ae0c9939031e2; application source unchanged, pre-existing agent documents dirty. Production current runtime UNKNOWN; no server commands/connections.

## 1. Состояние области

Source flow: nginx → web/Gunicorn → PostgreSQL17 and Redis; legacy MariaDB is profile-gated. Application image built from source; media/static bind-mounted. deploy-server builds web, runs release migrations/static, activates new image, then drift/check/smoke. Codebase Memory exact coverage checked for seven scripts/config paths; nginx excluded, read source directly.

## 2. Сильные стороны

Current `.dockerignore` excludes env files; September6 image finding cannot describe today's local build. PostgreSQL config requires explicit credentials/URL; startup refuses pending migrations outside debug. Deploy uses strict bash and health/smoke checks; baseline app retained while building new image. These are source properties, not current live health evidence.

## 3. Реальные проблемы

### OPS-01 — P1: failed dump reported successful, retention still deletes older backups

Source `scripts/backup-db.sh:2,19,24,34-37`: no pipefail, pipeline status comes from gzip. If docker/pg_dump fails but gzip succeeds, script prints success and runs retention against real older backups. Concrete effect: no usable new DB dump, old recovery points may be removed.

Isolated reproduction executed against a byte-identical copy under `/tmp/kidsmap-backup-audit-wdhaol5c`; docker was a shell function returning23, all files synthetic in /tmp. Result: copied script hash equals source; simulated dump exit23; backup script exit0; success message true; old synthetic20-day backup removed; one newly generated gzip archive. No Docker daemon, real DB, existing backup directory or production data accessed. Evidence summary result.json stays in scratch; no dumps copied to repository.

### OPS-02 — P2: failure trap restarts service without restoring previous release

Source `scripts/deploy-server.sh:22-32,65-78`, `scripts/release-server.sh:13-30`: trap only calls compose up web; no previous image/revision/schema record or restoration. Migrations/static replacement precede new-image verification. A failure after schema change or activation can leave the failed/new version rather than the previous working deployment. Script contains no pre-deploy backup invocation. This establishes missing automated recovery, not a current outage. External operator backup/rollback practices UNKNOWN.

## 4. Tech debt

Release and recovery guarantees are implicit across several scripts. Failure trap name “ensure running” is accurate but insufficient as rollback. Separate documented DB/image/static compatibility checkpoints are needed before a future approved release.

## 5. Risks

Compose publishes web8000 on all host interfaces; intended nginx boundary depends on firewall, current exposure UNKNOWN. Nginx media alias serves files directly; specialist document privacy belongs to security report and is not duplicated as an independent master cause. CI push main can deploy; this audit does not push. ManifestStaticFilesStorage is enabled outside DEBUG/TESTING when WhiteNoise installed, so raw source static links do not alone prove cache-busting failure.

## 6. Dead/legacy candidates

Legacy MariaDB profile remains explicitly configured. Usage/retirement UNKNOWN; do not delete. No scripts/images/backups removed by audit except synthetic fixtures subject to copied-script test within /tmp.

## 7. Tests gaps

`bash -n scripts/backup-db.sh scripts/deploy-server.sh` and `sh -n scripts/release-server.sh scripts/start-server.sh` exited0; syntax checks do not establish safe recovery. No actual restore drill, image build, PostgreSQL migration rollout, active nginx config or live health test executed. Add isolated dump-failure and recovery drills as future validation, not production tests.

## 8. Recommendations

Prioritize reliable dump failure detection before retention and independent backup verification. Then specify prior-image/schema/static recovery and preflight backup acceptance for release workflow. Changes require separate approved implementation scope; nothing fixed here. DB reviewer owns migration compatibility, security owns media boundaries, QA owns test execution ledger.

## 9. P0/P1/P2/P3

No P0 proved. OPS-01 P1 reproduced on exact script copy with synthetic failure; OPS-02 P2 source-confirmed recovery gap. Current production occurrence/backup integrity/firewall remain UNKNOWN. Handoff to orchestrator for deduplication and priority; no deployment or cleanup authorized by findings.
