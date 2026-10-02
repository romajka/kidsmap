# Stage07 permission actions implementation plan

Goal: owner-only team assignment, selected/all-network Organization grants and fresh action resolver. Spec: docs/task33/prompts/07.md; approved scope only07.
Architecture: preserve concrete Place memberships; add OrganizationGrant/Invitation, immutable invitation payload plus ownership/scope snapshots; central services lock Organization→Place→grant/invitation. Existing controllers/repositories and list scopes consume the same resolver. No new screens or production writes.

- [ ] RED legacy manager team/review POST, stale invitation and stale scope tests; isolated QA04 PostgreSQL run.
- [ ] Add actions, Organization grant/invitation schema, Place action/version/expiry fields; migration0119 additive. Legacy null-place cannot authorize; legacy concrete memberships remain concrete.
- [ ] Implement `has_action(user,target,action)`, backend action configuration, scope listing; owner-only team/transfer; branch permission separate. Org/Program actions do not follow network Place actions.
- [ ] Implement `invite/accept/decide/change_grant/leave/suspended/confirm_member/create_branch` with locked fresh actor/owner/version/scope. Transfer cancels invitations/suspends grants through model/service hooks.
- [ ] Adapt legacy team repository/controller and owner review POST; refuse delegation/moderation on backend, catch domain refusals in adapters. Existing form role choices retain compatibility but lose moderation/delegation semantics.
- [ ] Tests literal selected/all/future/detach/transfer/revoke/account-role/expired/IDs/POST/CSRF plus real PG acceptance-transfer and write-revoke races; negative malformed actions/scope. Preserve previous assertions.
- [ ] Parent targeted05/06/07, full canonical comparison against06, isolated migration/checks; independent canonical reviewer own run and matching SHA.
- [ ] Report07/results/source manifest and journal, release own active_run only after handoff. No08/09/production/commit/push/deploy.

Exact harness: `python3 docs/task33/qa04/run.py --mode all --label catalog.testcases.test_task33_permissions --output /tmp/task33-07-<fresh-run>`; schema generation uses qa07 generator with unchanged QA04 environment/network/libpq guards.
