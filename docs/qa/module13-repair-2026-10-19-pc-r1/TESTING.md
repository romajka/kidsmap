# Module13 quality execution

Canonical complete discovery: KidsMapTestRunner with no labels. Explicit labels/patterns remain scoped. scripts/run_kidsmap_tests.sh full delegates to the same no-label manage.py test; use only with an explicitly isolated testing profile, never credentials from a deployment environment.

Linux CI provisions a fresh qa_stage04 PostgreSQL and real Unix socket, then runs:

    python scripts/run_isolated_quality.py --profile-root "$QUALITY_PROFILE_ROOT" --socket-dir "$QUALITY_SOCKET_DIR"

The root must be a new /tmp/kidsmap-task33-qa04-* directory. Socket directory must actually be checkout .tmp/kidsmap-task33-qa04-socket-*/socket. The official image keeps /var/run/postgresql for its bootstrap and adds the mounted socket; TCP and container network are disabled. The CLI verifies actual socket/server/database/role, clears inherited env, compiles current PO into a fresh checkout .tmp descendant, supplies strict historical guard helper, checks migrations/system and runs all methods sequentially. Existing guards and business assertions are unchanged. A new PostgreSQL instance is required; retained test DBs are evidence, not a reset target.

Local execution used the exact CLI in dedicated network-none app/PG containers with current-source RO mount and separate own socket/data/profile/locale storage. See evidence/qa04-r5-setup.json and qa04-r5-backend.json for actual IDs/args. Do not reuse their historical paths on another computer. Raw logs/private synthetic cookie configs are ignored scratch and are intentionally absent from the artifact package.

CI additionally runs original standalone Python and Node unit/DOM checks. The3 fixture-authenticated browser scripts have separate explicit native configurations; they are excluded by name from unit-only invocation and were executed successfully in this local acceptance. YAML/Bash syntax and deploy preservation were verified locally; actual GitHub execution remains NOT RUN.
