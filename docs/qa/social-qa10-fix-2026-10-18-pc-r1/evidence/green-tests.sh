#!/bin/sh
qa=/mnt/c/kidsmap/.tmp/social10-pc-fix-r1
docker exec m09s10-fix-r1-app python "$qa/runtime.py" test catalog.testcases.test_social_qa10_notification_login.SocialQA10NotificationLoginTests catalog.testcases.test_social_qa08_invitation_feedback.SocialQA08InvitationFeedbackTests.test_auth_get_and_csrf_guards_are_unchanged catalog.testcases.test_social_qa08_invitation_feedback.SocialQA08InvitationFeedbackTests.test_foreign_and_nonexistent_notice_remain_404 catalog.testcases.test_social_qa08_invitation_feedback.SocialQA08InvitationFeedbackTests.test_revoked_invitation_explains_denial_for_both_kinds_and_locales catalog.testcases.auth_flow.TestAuthValidationAndNextSecurity.test_login_rejects_external_next_redirect > "$qa/green-tests.log" 2>&1
result=$?
printf '%s\n' "$result" > "$qa/green-tests.exit"
tail -n 12 "$qa/green-tests.log"
exit "$result"
