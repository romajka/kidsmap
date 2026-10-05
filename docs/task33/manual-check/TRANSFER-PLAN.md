# Git handoff implementation plan — 2026-10-05

Goal: push all application/work reports to task33-progress and reproduce the synthetic manual preview on another computer. User explicitly authorizes commit/push; production/main remain outside scope.

Architecture: keep the legacy preview default intact, add a portable opt-in using the current checkout and interpreter, a separate owned PostgreSQL container/volume/QA-root, local source hashes, and the same idempotent synthetic seed. No real database dumps or environment files enter Git. Historical completion/final-audit remain immutable.

Tasks:
- [x] Inspect Git branch/remote/ahead-behind, file sizes, staged secret patterns and archived contents. Remove pre-existing tracked env/SQLite backup from the new tip only, keep local copies and ignore paths; no history rewrite.
- [x] Add portable.py; start.py owns portable paths/manifest; serve.py binds the chosen loopback port and invokes the same 100-place seed; add_demo_places.py retains default behavior and writes portable runtime evidence outside the repository; seed.py avoids writing portable fixtures into Git.
- [x] On a separate owned port/database reproduce clean migrations, base fixtures, 100 extra places/images, login/admin/catalog, restart idempotence and isolated network/cache/mail. Default legacy preview must remain running and data untouched.
- [x] Write TRANSFER.md with clone/pull, Python/WSL/Docker dependencies, start/stop, passwords, URLs and update steps. Record exact verification and historical evidence hashes.
- [ ] Stage all authorized app/report files, verify index/no secrets/size/diff-check, commit, normal push task33-progress, compare remote SHA and report result. No main/deploy/force push.

QA helper paths are excluded from the application's 2761-file snapshot. Historical reports are not relabelled as fresh tests; no broad backend rerun is needed for packaging-only changes.
