#!/bin/bash
set -euo pipefail
stamp=$1
shift
output=/tmp/task33-stage28-security-$stamp
retained=/root/task33-evidence/$stamp
test ! -e "$output"
test ! -e "$retained"
cd /root/km28-security
.venv/bin/python /mnt/c/kidsmap/docs/task33/qa28/security_snapshot.py
set +e
.venv/bin/python docs/task33/qa04/run.py --mode all --output "$output" "$@"
result=$?
set -e
test -d "$output" && cp -a "$output" "$retained"
.venv/bin/python /mnt/c/kidsmap/docs/task33/qa28/security_snapshot.py
exit "$result"
