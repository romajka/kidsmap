# SOCIAL-QA-10 Implementation Plan

> For agentic workers: execute inline, task-by-task under the canonical KidsMap engineering contract. Generic skill suggestions for separate execution skills, delegation or commits are overridden by the repository/user scope: no application implementation until approval of this exact plan; no commit/push/deploy.

**Goal:** guest notification URLs reach the existing localized login route instead of404, with next and all authorization/method/CSRF guards preserved.

**Architecture:** explicitly bind the four notification login_required decorators to the existing named account_login route. This matches location_resolution and explicit account CBVs. Keep login_required outermost, require_GET/POST and the complete handler bodies unchanged; do not change global LOGIN_URL, shared auth views, routes or templates.

**Tech Stack:** current Django6.0.2/Python3.12.15/PostgreSQL17.11, existing localization and unittest/TestCase conventions; no dependencies/schema changes.

**Spec:** current finding SOCIAL-QA-10 (alias ADJ-ANONYMOUS-LOGIN-08), ../module09-full-2026-10-17-pc-r1/findings/SOCIAL-QA-10.md; exact candidate and source snapshot in this folder.

## Global constraints

- Branch codex/module09-transfer-2026-10-16-r1, HEAD852938d96764ae315b92859e3651e5ea62054a36; task33-progress e4e05cc213b34e2d771ecb854901bfd016d1db51; active_run NONE. Preserve approved dirty SOCIAL01–09 bytes, index and existing artifacts/processes.
- App whitelist: src/catalog/controllers/workflow_notifications.py and new src/catalog/testcases/test_social_qa10_notification_login.py only. SOCIAL11, settings, JS/CSS/templates/PO/routes/services/DB schema are outside scope.
- Tests DJANGO_TESTING=1, owned isolated PostgreSQL/testDB/cache/media/private-media/locmem email, no production credentials. Current RU/AZ/EN MO, manifest verification before django.setup, sole LOCALE_PATHS; shared MO untouched.
- No automatic replay of POST after login. Authenticated GET to read/accept/reject must still405; existing action next semantics retained. This scope fixes login target resolution and inbox GET login recovery, not expired POST UX redesign or automatic action resumption.
- No commit/push/deploy/production/reset/clean/stash/dirty checkout switch/automatic active_run or old PNG download.

## Impact map / decision

Graph generation2026-10-16T18:56:53Z; relevant metadata unavailable/changed, so route/decorator findings verified directly. Graph trace inbox→_render_inbox confirms the rendering path, not decorator completeness. Direct current source search finds four unparameterized login_required decorators, all in this controller. The location resolver explicitly specifies account_login; account dashboard/favorites/profile/deletion CBVs specify reverse_lazy(account_login); engagement helpers build their own login redirect. A global LOGIN_URL change would also change defaults for third-party callers and is unnecessary for the confirmed module issue.

1. catalog.urls maps account_notifications and read/accept/reject to these four views; account_login exists at localized auth/login/.
2. django login_required resolves a named login_url at request time; use the established local project pattern, preserving locale/next construction.
3. _mine, invitation currentness/locks/ownership/read-only denial, notifications/outbox and all POST bodies are unchanged.
4. LoginForm, safe-next validation, logout/session expiry and shared guards remain unchanged; focused tests below verify observed contracts.

## Task1 — reviewed regression and exact minimal repair

**Files:** modify src/catalog/controllers/workflow_notifications.py (four decorator lines); create src/catalog/testcases/test_social_qa10_notification_login.py. No other application files.

**Interfaces:** consumes named account_login/account_notifications/account_notification_read/account_notification_accept/account_notification_reject and current request.user authentication. Produces the same handlers/status/DB semantics with the correct login redirect route. New class SocialQA10NotificationLoginTests contains8 methods.

- [x] Write the complete candidate tests outside the app; exact runnable code is [candidate_tests.py](candidate_tests.py), intended destination stated above. No placeholders. The eight methods cover localized inbox/full next, GET actions/auth order, anonymous POST with valid CSRF/no business write, missing CSRF403, authenticated405 and read replay, password login/inbox return, external-next rejection and explicit shared account guards.
- [x] Run RED against unchanged current app: evidence/red-tests.sh invokes candidate_tests.SocialQA10NotificationLoginTests plus four explicit shared methods.12 total methods;4candidate methods fail with24 route-mismatch subtest assertion failures,4candidate pass and4existing shared pass;0 errors, exit1. No existing assertion changes. Full output retained.
- [ ] After human scope approval, revalidate source/index/refs/locale/isolation/preservation and exact candidate hashes. Stop for changed implementation cause or scope, not for unchanged already authorized routine steps.
- [ ] Apply exactly proposed.diff after git apply --check --ignore-space-change. Four occurrences of:

~~~python
@login_required
~~~

become:

~~~python
@login_required(login_url="account_login")
~~~

Preserve their ordering above @require_GET/@require_POST. The complete resulting file is candidate-controller.py, and the full eight-test addition is candidate_tests.py. candidate-manifest.json binds before/raw and candidate/diff hashes. No handler-body refactor.

- [ ] Build/verify fresh own RU/AZ/EN MO against the applied source; configure expected-source snapshot including the new test (1025source if nothing else changed). Keep the existing QA PG only after rechecking its owned volume/internal-network identity; use a new isolated testDB and private media/cache namespace.
- [ ] GREEN: run catalog.testcases.test_social_qa10_notification_login.SocialQA10NotificationLoginTests and exactly these shared methods (same runner and labels as RED, candidate_tests replaced with app module):
  - catalog.testcases.test_social_qa08_invitation_feedback.SocialQA08InvitationFeedbackTests.test_auth_get_and_csrf_guards_are_unchanged
  - catalog.testcases.test_social_qa08_invitation_feedback.SocialQA08InvitationFeedbackTests.test_foreign_and_nonexistent_notice_remain_404
  - catalog.testcases.test_social_qa08_invitation_feedback.SocialQA08InvitationFeedbackTests.test_revoked_invitation_explains_denial_for_both_kinds_and_locales
  - catalog.testcases.auth_flow.TestAuthValidationAndNextSecurity.test_login_rejects_external_next_redirect

Expected12PASS/0F0E/exit0, no weakening assertions. If a distinct cause appears, retain it and assess scope before additional fixes. Full unchanged ACCEPT09 corpus is not repeated merely for green; its169-method success still belongs only to the1024-source audit snapshot.

## Task2 — native acceptance and preservation

**Files:** new unique docs/qa/social-qa10-fix-2026-10-18-pc-r1 evidence; append only current module09 checkpoint to continuation guide. These are audit/status deliverables, not an expansion of the app whitelist.

- [ ] Real Chromium guest inbox→localized login at AZ/RU/EN×360/390/768/1024/1280/1440,18 native cells; all final200/form visible and next equals original inbox with harmless query. Current RED script recheck.js is the concrete repro; update expected recovery assertion for GREEN and include correct named-route paths.
- [ ] For one fictional account per language perform real password login through the redirected form and verify inbox return/reload. No OAuth substitution or fixture force-login for this round trip. Tab/ShiftTab/Enter/Escape/focus and no unexpected local console/network failures; native PNG. Do not pretend unchanged login UI was redesigned.
- [ ] Local HTTP probes for read/accept/reject guest redirects; authenticated GET405, missing CSRF403, foreign404 and revoked403/no grant retained. Guest action redirect keeps original next; following an action as GET after login remains405 by design, never automatically posts.
- [ ] Verify native/source/runtime/MO fingerprint, source other1023 files unchanged, exact two candidate files, prior15 packages/source history and sharedMO/.cbmignore/ref/index/activeNONE/container identities preserved; state changes recorded with UNKNOWN where appropriate. No restoration of unrelated container states.
- [ ] Save exact commands/exits/counts/initial failures/NOT RUN/SIMULATED, native PNG manifest and verification. Append scoped SOCIAL10 closure only after actual GREEN; module09 remains OPEN for SOCIAL11, global/production untested. Provide next PLAN SOCIAL11; no automatic fix11/module10.

## Approval request

Approve only this two-application-file scope: four explicit named-login decorators and the exact eight regression methods. Candidates and RED evidence are complete and reviewable. AGENTS.md requires a concrete plan and user approval for a new implementation scope; earlier SOCIAL01–09 approvals do not authorize this new finding.
