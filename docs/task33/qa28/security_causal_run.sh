#!/bin/bash
set -euo pipefail
revision=$1
test "$revision" = current || test "$revision" = v2
root=/mnt/c/kidsmap
checkout=/root/km28-security
if test "$revision" = v2; then
    checkout=/root/km28-security-v2-probe
    test ! -e "$checkout"
    cp -a /root/km28-image-context "$checkout"
    ln -s /root/kidsmap-task33/.venv "$checkout/.venv"
fi
# Inject only this explicit QA fixture into our own external test mirror.
cp "$root/docs/task33/qa28/security_concurrency_probe.py" "$checkout/src/catalog/testcases/test_qa28_security_concurrency_probe.py"
output=/tmp/task33-stage28-security-causal-$revision
retained=/root/task33-evidence/stage28-security-causal-$revision-20261003
test ! -e "$output"
test ! -e "$retained"
cd "$checkout"
set +e
.venv/bin/python docs/task33/qa04/run.py --mode all --output "$output" \
 --label catalog.testcases.test_task33_ownership.OwnershipConcurrencyTests \
 --label catalog.testcases.test_qa28_security_concurrency_probe.OwnershipStructureRetryProbe
result=$?
set -e
test -d "$output" && cp -a "$output" "$retained"
.venv/bin/python "$root/docs/task33/qa28/security_collect.py" "$retained" \
 "$root/docs/task33/reports/28-security-causal-$revision.json" \
 "Five unchanged original ownership concurrency cases plus one explicit external QA ordering probe"
exit "$result"
