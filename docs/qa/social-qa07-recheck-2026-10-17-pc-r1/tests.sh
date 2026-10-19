#!/bin/sh
set -eu
qa=/mnt/c/kidsmap/.tmp/social07-pc-plan-r1
set +e
docker exec m09s07-plan-r1-app python "$qa/runtime.py" test candidate_tests.SocialQA07TitleTests > "$qa/tests.log" 2>&1
result=$?
printf '%s\n' "$result" > "$qa/tests.exit"
tail -n 9 "$qa/tests.log"
exit "$result"
