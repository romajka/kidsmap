#!/bin/bash
set -euo pipefail
root=/mnt/c/kidsmap/docs/task33/final-audit
checkout=/root/km28-security
output=/tmp/task33-final-audit-security-20261004
retained=/root/task33-evidence/final-audit-security-20261004
test ! -e "$output"
test ! -e "$retained"
# Remove only our previously introduced external diagnostic; canonical source untouched.
python3 - <<'PY'
from pathlib import Path
path=Path('/root/km28-security/src/catalog/testcases/test_qa28_security_concurrency_probe.py')
assert path.parent.resolve()==Path('/root/km28-security/src/catalog/testcases')
if path.is_file() and not path.is_symlink():path.unlink()
PY
cd "$checkout"
.venv/bin/python "$root/qa/security_snapshot.py" before
set +e
.venv/bin/python docs/task33/qa04/run.py --mode all --output "$output" \
 --label catalog.testcases.test_task33_specialist_security_review \
 --label catalog.testcases.test_task33_specialist_screens_security \
 --label catalog.testcases.test_task33_specialist_privacy \
 --label catalog.testcases.test_task33_specialist_transfer \
 --label catalog.testcases.test_task33_specialist_retention \
 --label catalog.testcases.test_task33_event_security \
 --label catalog.testcases.test_task33_event_owner_contract \
 --label catalog.testcases.test_task33_event_queries \
 --label catalog.testcases.test_task33_notifications \
 --label catalog.testcases.test_task33_review_independent \
 --label catalog.testcases.test_task33_r1_cohort \
 --label catalog.testcases.test_task33_r1_owner_safety \
 --label catalog.testcases.test_task33_volunteer_hub \
 --label catalog.testcases.test_task33_ownership \
 --label catalog.testcases.test_task33_organization_workspace \
 --label catalog.testcases.test_task33_publication \
 --label catalog.testcases.test_task33_public_details \
 --label catalog.testcases.test_task33_event_public \
 --label catalog.testcases.test_task33_event_admin_precision
result=$?
set -e
.venv/bin/python "$root/qa/security_snapshot.py" after
test -d "$output" && cp -a "$output" "$retained"
.venv/bin/python "$root/qa/security_collect.py" "$retained" "$root/security-results.json" \
 "Final audit fresh selected260 security; historical259/260 is separate immutable stage28 evidence"
exit "$result"
