#!/bin/sh
qa=/mnt/c/kidsmap/.tmp/module09-full-pc-r1
docker exec m09full-r1-socket-app python "$qa/socket_runtime.py" test catalog.testcases.test_task33_notification_crashes catalog.testcases.test_task33_review_migration > "$qa/socket-tests.log" 2>&1
result=$?
printf '%s\n' "$result" > "$qa/socket-tests.exit"
tail -n 12 "$qa/socket-tests.log"
exit "$result"
