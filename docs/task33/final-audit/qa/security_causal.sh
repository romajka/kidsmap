#!/bin/bash
set -euo pipefail
root=/mnt/c/kidsmap/docs/task33/final-audit
checkout=/root/km28-security
output=/tmp/task33-final-audit-security-causal-20261004
retained=/root/task33-evidence/final-audit-security-causal-20261004
test ! -e "$output"
test ! -e "$retained"
cp "$root/qa/security_concurrency_probe.py" "$checkout/src/catalog/testcases/test_qa28_security_concurrency_probe.py"
cd "$checkout"
set +e
.venv/bin/python docs/task33/qa04/run.py --mode all --output "$output" \
 --label catalog.testcases.test_task33_ownership.OwnershipConcurrencyTests \
 --label catalog.testcases.test_qa28_security_concurrency_probe.OwnershipStructureRetryProbe
result=$?
set -e
test -d "$output" && cp -a "$output" "$retained"
.venv/bin/python "$root/qa/security_collect.py" "$retained" "$root/security-causal.json" \
 "Fresh five original concurrency cases plus QA-only deterministic structure retry and ACL probe"
exit "$result"
