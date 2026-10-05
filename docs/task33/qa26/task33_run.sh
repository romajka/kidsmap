#!/bin/bash
set -euo pipefail
stamp=$1
labels=()
for source in /mnt/c/kidsmap/src/catalog/testcases/test_task33_*.py; do
    module=$(basename "$source" .py)
    labels+=(--label "catalog.testcases.$module")
done
/bin/bash /mnt/c/kidsmap/docs/task33/qa26/backend_run.sh all "$stamp" "${labels[@]}"
