# Validation B — Volunteer A / Place B

2026-09-08. Execution identity: `/root/security_discovery`, applying updated `.agents/agents/security-reviewer/agent.md` after routing through updated `kidsmap-orchestrator`. Same agent reused its discovery context. This is an updated-role evaluation, **not independent fresh-context discovery**, and not an executed application security test.

## Routing and scope

Question: «Почему Volunteer A не должен видеть Place B?» SECURITY → lead `security-reviewer`. This bounded source answer needs no additional worker. Future support: `django-reviewer` for changed permission contracts, then `integration-reviewer` for isolated negative tests; `release-reviewer` only if private storage/proxy exposure enters scope. Order: scoped routes/services → alternate permission paths → negative fixtures → handoff. No application fixes authorized here.

LOCAL HEAD verified with `git rev-parse HEAD`: `d75b34f4db5d4ba484cf8392ff3ae0c9939031e2`. Targeted `git diff --name-only --` across the eight source/test paths below returned empty. Agent definitions/knowledge are updated WORKTREE documents. PRODUCTION: UNKNOWN; not contacted.

## Evidence and answer

Volunteer A must not read or edit B's private workspace content: that grants access to another contributor's proposals and moderation state. This does **not** prohibit A from viewing an otherwise public Place B on the public website.

| Boundary | Verified LOCAL source |
|---|---|
| Role | `src/catalog/services/staff_roles.py:is_volunteer`, `can_use_volunteer_workspace`: group marker, authenticated active staff, superuser excluded from volunteer classification. |
| Object scope | `src/catalog/services/volunteer_places.py:own_places`: creator is current user, owner NULL, not deleted, not temporary. Knowing B's object ID does not satisfy the filter. |
| Direct routes | `src/catalog/domain_admin/volunteer.py:detail`, `edit`, `photo` retrieve from `workspace_places`/`own_places`; foreign IDs resolve to 404. |
| Lists and aggregates | `src/catalog/services/volunteer_dashboard.py:workspace_places` starts from `own_places`; A/B search/count regression fixtures already exist. |
| Alternate paths | `src/catalog/volunteer_middleware.py:VolunteerAccessMiddleware.process_view` blocks ordinary admin/owner/document routes, including localized aliases. `src/catalog/services/place_access.py:direct_place_permissions`, `staff_has_place_permission`, `has_place_permission` reject volunteers before owner/team/model grants. |
| Mutation/review | `volunteer_places.save_proposal`/`restart_proposal` reuse object scope; version/signed-base checks protect proposal state. `require_reviewer` requires active staff superuser; `review_proposal` rejects owner handover, stale/past review state and applies locks. Discovery source evidence reused after unchanged-source verification. |

Codebase Memory: current project/root confirmed; `index_status` ready; exact `own_places` graph search returned one function with no further page. Inbound trace returned five callers: `edit`, `photo`, `workspace_places`, `restart_proposal`, `save_proposal`. Coverage for all eight source/test files: `no_recorded_issue`, `metadata_match`, best-effort only. Template parsing gaps exist in the wider index; no rendered UI or exhaustive graph-completeness claim is made.

## Tests and handoff

Executed: source reads, graph discovery/trace/coverage, HEAD and targeted diff. No Django, DB, browser, production or provider checks. Present tests are not passing evidence:

- `catalog.testcases.test_volunteer_dashboard.VolunteerDashboardTests.test_all_foreign_object_methods_and_ajax_are_denied`: default/RU/EN GET/POST/AJAX detail/edit/photo plus forbidden admin bulk actions.
- Same class: `test_counts_search_and_filter_are_scoped_to_current_volunteer`, `test_foreign_private_place_not_disclosed_by_public_apis`, `test_owner_photo_routes_cannot_bypass_proposal`.
- `catalog.testcases.test_volunteer_admin.VolunteerAccessTests`: foreign object, accidental permissions, owner handover, CSRF, stale edits and review.
- `catalog.testcases.test_volunteer_admin.VolunteerConcurrencyTests.test_two_reviewers_cannot_apply_the_same_revision_twice`: needs isolated PostgreSQL; source inspection does not prove concurrency behavior.

Future targeted command, **NOT RUN**, only after `integration-reviewer` provisions disposable PostgreSQL/cache/media/email and disables external integrations under the testing contract:

```bash
DJANGO_TESTING=1 python manage.py test catalog.testcases.test_volunteer_admin catalog.testcases.test_volunteer_dashboard
```

Acceptance: separate A/B fixtures never disclose private B workspace content through routes, counts, search or photos; denied mutation leaves B unchanged; handover removes A's former workspace access; public B remains governed by public visibility rather than contributor identity. Actual fresh suite results, active middleware deployment and underlying media-storage privacy are UNKNOWN. A private/no-store application response alone does not prove a storage URL inaccessible.

Changed: this report only. Business impact: clarification of existing scope, no new rule. DB impact: none. Security impact: source-supported access boundary, no fresh exploit or production finding. Needs next: orchestrator reconcile validation with team outputs; future `integration-reviewer` run the bounded fixture acceptance above when tasked.

## Prompt evaluation and read budget

Updated routing/role/permissions knowledge successfully identifies concrete volunteer boundaries and correctly distinguishes public visibility. No blocking prompt deficiency found. Small maintenance issue: security SOURCE OF TRUTH list still emphasizes generic auth/media files; volunteer files are correctly supplied by OPERATING RULES and permissions knowledge, so no duplicate rule is needed. A broad READ FIRST list should remain subordinate to the engineering contract's domain-scoped reads to avoid repeated historical-doc loading.

Updated docs read: `.agents/agents/kidsmap-orchestrator/agent.md`, `.agents/agents/security-reviewer/agent.md`, `.agents/rules/engineering-contract.md`, `.agents/knowledge/current-snapshot.md`, `.agents/knowledge/permissions.md`, `.agents/registry.json`, `.agents/rules/agent-orchestration.md`. Earlier architecture/source-map/audit-contract reads reused; no broad rediscovery. Source/test reads: the six implementation files named in the evidence table plus `src/catalog/testcases/test_volunteer_admin.py` and `src/catalog/testcases/test_volunteer_dashboard.py` (eight total). Output reread for verification.

Post-update bounded phase tool budget: five Codebase Memory calls (`list_projects`, `index_status`, `search_graph`, `trace_path`, `check_index_coverage`), six shell calls including final report verification, one `apply_patch`; no subagent calls. Metadata-tool lookup used the existing tool catalog, not a network lookup. These counts exclude the explicitly reused discovery phase and functions.exec orchestration wrappers.

## Coordinator correction recheck

The original future command incorrectly named `src/manage.py`; coordinator caught this during review. Corrected above to root `manage.py`. Exact read-only checks: `rg --files -g manage.py -g 'engineering-contract.md'` returned `manage.py`; `sed -n '1,35p' manage.py` confirmed the root entrypoint adds `src` to the Python path and invokes Django management. No application command was executed; this correction is not a test pass.

Rechecked `.agents/rules/engineering-contract.md` using `rg -n 'READ FIRST|index_status|project|metadata|scoped|read' .agents/rules/engineering-contract.md`: line 9 now explicitly makes READ FIRST a navigation list with domain-scoped reading; line 7 requires projection of root/status/generation and relevant coverage gaps instead of echoing the index inventory. The read-budget concern above is therefore resolved by an explicit shared rule. Validation B's source-boundary conclusion remains valid; fresh-context behavior and execution results remain untested. Correction phase adds two shell calls (source/contract read and output verification) and one patch to the prior budget.
