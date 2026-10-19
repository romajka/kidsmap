#!/bin/sh
set -u
qa=/mnt/c/kidsmap/.tmp/social08-pc-plan-r1
docker exec m09s08-plan-r1-app python "$qa/runtime.py" test candidate_tests.SocialQA08InvitationFeedbackTests > "$qa/tests.log" 2>&1
result=$?
printf '%s\n' "$result" > "$qa/tests.exit"
tail -n 9 "$qa/tests.log"
exit "$result"
