#!/bin/sh
qa=/mnt/c/kidsmap/.tmp/social10-pc-plan-r1
docker exec m09s10-plan-r1-app python "$qa/runtime.py" test candidate_tests.SocialQA10NotificationLoginTests catalog.testcases.test_social_qa08_invitation_feedback.SocialQA08InvitationFeedbackTests.test_auth_get_and_csrf_guards_are_unchanged catalog.testcases.test_social_qa08_invitation_feedback.SocialQA08InvitationFeedbackTests.test_foreign_and_nonexistent_notice_remain_404 catalog.testcases.test_social_qa08_invitation_feedback.SocialQA08InvitationFeedbackTests.test_revoked_invitation_explains_denial_for_both_kinds_and_locales catalog.testcases.auth_flow.TestAuthValidationAndNextSecurity.test_login_rejects_external_next_redirect > "$qa/red-tests.log" 2>&1
result=$?
printf '%s\n' "$result" > "$qa/red-tests.exit"
tail -n 12 "$qa/red-tests.log"
exit "$result"
