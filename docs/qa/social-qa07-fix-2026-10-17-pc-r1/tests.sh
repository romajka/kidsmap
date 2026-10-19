#!/bin/sh
set -u
qa=/mnt/c/kidsmap/.tmp/social07-pc-fix-r1
docker exec m09s07-fix-r1-app python "$qa/runtime.py" test catalog.testcases.test_social_qa07_activity_review_title.SocialQA07TitleTests catalog.testcases.test_social_qa03_conflict_recovery.TypedReviewConflictRecoveryTests.test_stale_draft_renders_with_latest_version_and_no_write catalog.testcases.test_social_qa03_conflict_recovery.TypedReviewConflictRecoveryTests.test_conflicting_script_text_is_escaped_and_preserved > "$qa/tests.log" 2>&1
result=$?
printf '%s\n' "$result" > "$qa/tests.exit"
tail -n 19 "$qa/tests.log"
exit "$result"
