#!/bin/bash
set -euo pipefail
# Sequential security role, only after root final GREEN and artifact3 freeze.
root=/mnt/c/kidsmap
test -d /root/km28-release3
for name in results source; do
    report="$root/docs/task33/reports/28-security-$name.json"
    preserved="$root/docs/task33/reports/28-security-$name-v2.json"
    if test ! -e "$preserved"; then cp "$report" "$preserved"; fi
done
bash "$root/docs/task33/qa28/security_run.sh" all stage28-security-release3-final-20261003 \
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
/root/kidsmap-task33/.venv/bin/python "$root/docs/task33/qa28/security_collect.py" \
 /root/task33-evidence/stage28-security-release3-final-20261003 \
 "$root/docs/task33/reports/28-security-results.json" \
 "Fresh final release3 security and Event admin/owner precision scope; full suite owned by root"
