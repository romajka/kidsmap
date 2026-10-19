#!/bin/sh
qa=/mnt/c/kidsmap/.tmp/module09-full-pc-r1
docker exec m09full-r1-app python "$qa/runtime.py" test catalog.testcases.test_task33_reviews catalog.testcases.test_task33_review_independent catalog.testcases.test_review_confirmation catalog.testcases.test_place_review_cooldown catalog.testcases.test_favorite_metrics catalog.testcases.test_public_favorite_count catalog.testcases.test_task33_notifications catalog.testcases.test_task33_notification_crashes catalog.testcases.test_social_qa01_rating_readback catalog.testcases.test_social_qa02_rejection_feedback catalog.testcases.test_social_qa03_conflict_recovery catalog.testcases.test_social_qa07_activity_review_title catalog.testcases.test_social_qa08_invitation_feedback catalog.testcases.test_social_qa09_feed_query catalog.testcases.public.TestReviewEnhancements catalog.testcases.admin.ReviewAdminModerationTests catalog.testcases.admin.TestReviewRatingSyncAndAdminBulkActions catalog.testcases.catalog.ContentModerationPublicVisibilityTests > "$qa/tests.log" 2>&1
result=$?
printf '%s\n' "$result" > "$qa/tests.exit"
tail -n 14 "$qa/tests.log"
exit "$result"
