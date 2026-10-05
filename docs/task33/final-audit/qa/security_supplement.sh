#!/bin/bash
set -euo pipefail
root=/mnt/c/kidsmap/docs/task33/final-audit
output=/tmp/task33-final-audit-security-supplement-20261004
retained=/root/task33-evidence/final-audit-security-supplement-20261004
test ! -e "$output"
test ! -e "$retained"
cd /root/km28-security
set +e
.venv/bin/python docs/task33/qa04/run.py --mode all --output "$output" \
 --label catalog.testcases.test_google_auth.GoogleAuthTests.test_start_contract_csrf_scopes_pkce_and_fixed_callback \
 --label catalog.testcases.test_google_auth.GoogleAuthTests.test_invalid_expired_and_replayed_state \
 --label catalog.testcases.test_google_auth.GoogleAuthTests.test_identity_email_conflict_does_not_switch_or_merge_users \
 --label catalog.testcases.test_google_auth.GoogleAuthTests.test_logged_in_browser_cannot_attach_someone_elses_identity \
 --label catalog.testcases.test_google_auth.GoogleAuthTests.test_unsafe_next_and_auth_loop_fall_back_to_local_profile \
 --label catalog.testcases.test_google_auth.GoogleAuthTests.test_invalid_oidc_issuer_audience_expiry_and_subject \
 --label catalog.testcases.auth_flow.TestAuthValidationAndNextSecurity.test_register_rejects_external_next_redirect \
 --label catalog.testcases.auth_flow.TestAuthValidationAndNextSecurity.test_login_rejects_external_next_redirect \
 --label catalog.testcases.photo_workflow.PhotoWorkflowTests.test_prepare_requires_authentication_and_reports_bad_file \
 --label catalog.testcases.photo_workflow.PhotoWorkflowTests.test_pixel_limit_rejects_before_full_decode \
 --label catalog.testcases.image_uploads.TestOwnerImageNormalization.test_mime_mismatch_has_clear_validation_error_and_is_logged \
 --label catalog.testcases.image_uploads.TestOwnerImagePersistenceFailures.test_user_cannot_delete_photo_from_another_users_card
result=$?
set -e
test -d "$output" && cp -a "$output" "$retained"
.venv/bin/python "$root/qa/security_collect.py" "$retained" "$root/security-supplement.json" \
 "Fresh12 explicit common identity/redirect/upload trust-boundary negatives; mocked OAuth is not live OAuth"
exit "$result"
