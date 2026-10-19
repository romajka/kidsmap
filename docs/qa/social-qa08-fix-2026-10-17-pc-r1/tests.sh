#!/bin/sh
set -u
qa=/mnt/c/kidsmap/.tmp/social08-pc-fix-r1
docker exec m09s08-fix-r1-app python "$qa/runtime.py" test catalog.testcases.test_social_qa08_invitation_feedback.SocialQA08InvitationFeedbackTests catalog.testcases.test_task33_notifications.WorkflowIntegrationTests.test_invitation_inbox_post_only_recipient_scoped_and_revocation_suppresses_mail catalog.testcases.test_task33_notifications.WorkflowIntegrationTests.test_changed_email_cannot_read_old_address_notification catalog.testcases.test_task33_notifications.WorkflowIntegrationTests.test_csrf_required_for_inbox_actions > "$qa/tests.log" 2>&1
result=$?
printf '%s\n' "$result" > "$qa/tests.exit"
tail -n 10 "$qa/tests.log"
exit "$result"
