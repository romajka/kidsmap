# Release safety review

- Role: `release-reviewer`, `/root/release_safety`; definition `.agents/agents/release-reviewer/agent.md`.
- Mode: read-only review of release tooling. User deployment authorization supplied by orchestrator; no server access or production commands executed by this reviewer.
- Snapshot: LOCAL HEAD `e4e05cc213b34e2d771ecb854901bfd016d1db51`, dirty WORKTREE preserved. Payload is Git base `cfef63e3dbc93e971ac0e2ae963a17a3821ae27c` plus the 26 approved files, not the whole dirty tree.

## Decision before activation

**PASS for source-level release safety after correction.** Initial RS-01/RS-02 concerns below were fixed and rechecked before activation. Current reviewed `activate_remote.py` SHA256: `9feb066f9faab26bc5ca4702e7c6edb5546cdd1dfc07b471a2d4883302eb2cdf`. Runtime activation remains unverified by this reviewer.

1. **RS-01, RESOLVED, initial P1 operational assurance:** `activate_remote.py` exception branch initially emitted `ROLLED BACK` after unchecked rollback subprocess receipts and one immediate health request. A failed rollback could therefore receive a misleading success state. Require zero exits, actual previous image identity, unchanged environment/mounts, preserved other containers, and bounded readiness polling; otherwise emit `ROLLBACK_FAILED`.
2. **RS-02, RESOLVED, initial P2:** `running_remote.py` initially ran after the activation script had already committed its `ACTIVATED` receipt. A source/MO/system-check failure would escape automatic rollback. Execute those checks inside the activation `try` before success, or provide an explicit guarded rollback command with the same verification.

Corrections verified: source/MO/read-only schema/system checks now execute within activation rollback protection; rollback checks both command exits, bounded readiness, previous image, exact environment and other service IDs. Status distinguishes `ROLLED BACK VERIFIED` from `ROLLBACK FAILED`. Recommended completeness improvement: also compare restored mounts and `.env` file hash, matching the activation checks.

## Verified source boundaries

- `prepare.py`: exact before/after hashes, only 26 approved replacements/additions, clean Git archive base, isolated build context, forced fresh translation compilation, no local `.env`; package SHA verified locally.
- Payload manifest has 973 source paths (968 base + 5 additions); all present in context. The context also contains unchanged Git-base assets/config/scripts not covered by that source manifest; provenance is the exact Git archive, not an exhaustive image-vs-runtime manifest.
- `preflight_remote.py`: checks running baseline hashes, new paths absent, effective Compose environment and mount mapping, old web/image identity. Parent-generated `preflight.json` is attributed evidence, not this reviewer's live observation.
- `candidate_remote.py`: source integrity, no image `.env`, DEBUG/TESTING false, migration plan empty and Django checks inside an explicit read-only transaction with timeouts; only safe marked JSON returned.
- `activate_remote.py`: restricted server-only DB/static backup, `pg_restore --list` and gzip integrity checks; backup restore drill explicitly false. No migrations, data synchronization, media changes or DB restore are scheduled. Only web is recreated with `--no-deps --no-build`; other running service IDs are checked.
- `scripts/start-server.sh` only checks migrations before Gunicorn; no schema/application data write is performed by startup. General `release-server.sh` would migrate/synchronize data, but is not called.
- `ssh_run.py`: raw server output remains restricted scratch; report receives parsed safe JSON only.

## Checks and limits

Executed: source review of seven release Python files, Dockerfile/.dockerignore/Compose/start and release scripts; `ast.parse` for all seven Python files; package SHA and context manifest membership verification. All syntax checks passed, including the generated embedded runtime verification program after the corrections. No application edits, tests, server access, activation, rollback injection, restore drill or browser checks by this reviewer.

Codebase Memory: project `home-ramin-kidsmap` root verified and index ready. These newly generated QA scripts are inspected directly; graph coverage of this report folder is UNKNOWN, and no structural negative claim depends on graph absence.

Handoff: **kidsmap-orchestrator** — RS-01/RS-02 resolved; retain fresh candidate/activation/running receipts, and complete bounded live admin GET/browser verification without mutating real moderation records.
