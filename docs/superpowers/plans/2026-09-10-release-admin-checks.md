# Release admin checks — 2026-09-10

Role: integration-reviewer; LOCAL WORKTREE based on `d59bbc1a37bda44e1d91e1375a85c820b4a6151e`. User authorized all-current-changes release. Parent expanded this bounded review to fix RegionAdmin regressions and the ownership moderation permission gate. No production actions, commits or pushes by this role.

## Changes and evidence

- RegionAdmin metrics were stored indefinitely on the singleton ModelAdmin. A real second GET after creating one district still reported 12 instead of 13. Metrics now live on the request; row display functions bind that request's metrics, avoiding per-row aggregate queries and cross-request state.
- RegionAdmin Cyrillic search replaced its incoming filtered queryset with all regions. `content_status=empty&q=baku` returned populated Baku. Search now respects the input queryset.
- Ownership moderation accepted an ordinary staff user's POST without model permissions, changing request status and place owner. This pre-existing authorization defect was reproduced both on the dirty worktree and pristine HEAD (1 negative test failed in each); the parent authorized its narrow correction. Both concrete/proxy routes now consult the concrete ownership ModelAdmin permission; valid model-permission staff and superusers remain supported. Production exploitation is UNKNOWN.
- Changes owned: `src/catalog/domain_admin/specialist.py`, `src/catalog/domain_admin/owner.py` (permission gate only), added regression tests in `src/catalog/testcases/test_region_admin.py` and `src/catalog/testcases/admin.py`. Other contributors' changes preserved.

## Isolation and commands

Clean `env -i`, `DJANGO_TESTING=1`, SQLite `:memory:`, disposable `/tmp/kidsmap-release-admin-media`, LocMem cache/email, no external keys/credentials. Local helper `/tmp/kidsmap_release_admin_settings.py` supplies these settings; MD5 password hasher only speeds isolated tests. No live/local application database is read or written by these tests.

Commands run from `/tmp`, using prefix:

```sh
env -i PATH=/usr/bin:/bin HOME=/tmp LANG=C.UTF-8 DJANGO_TESTING=1 DJANGO_DEBUG=1 PYTHONPATH=/tmp:/home/ramin/kidsmap/src DJANGO_SETTINGS_MODULE=kidsmap_release_admin_settings /home/ramin/kidsmap/.venv/bin/python -m django
```

Suffixes:

- `check` — exit 0, no issues.
- `makemigrations --check --dry-run` — exit 0, no changes.
- `test catalog.testcases.test_region_admin --noinput --verbosity 1` — 10 passed, 11.271s; two bug probes failed before the fix.
- `test catalog.testcases.admin.OwnershipRequestAdminModerationTests --noinput --verbosity 1` — 6 passed, 1.443s. Negative unprivileged GET/POST approve/reject and positive explicit moderation permission covered.
- `test catalog.testcases.admin catalog.testcases.test_region_admin catalog.testcases.test_volunteer_admin catalog.testcases.test_volunteer_dashboard --noinput --verbosity 1` — final snapshot: 283 tests, 270 passed, 12 baseline failures, 1 PostgreSQL-only skip, 97.734s, exit 1. No new failing label compared with pristine HEAD.

Original default-hasher broad run: 279 tests, 12 failures, 1 PostgreSQL-only skip, 457.741s.

Original fast broad run: 283 tests, 13 failures, 1 PostgreSQL-only skip, 102.319s. One failure was an intermediate proxy permission issue then fixed; targeted 6 passed afterward. All remaining 12 failures reproduced on pristine HEAD archive using the same isolated settings and exact labels: 12 tests, 12 failures, 4.418s. No assertions changed to obtain green.

Baseline failure labels:
- `catalog.testcases.admin.TestAdminOwnershipModerationUX.test_admin_index_dashboard_summary_uses_real_database_counts`
- `catalog.testcases.admin.TestAdminOwnershipModerationUX.test_admin_place_changelist_renders_filter_select_options`
- `catalog.testcases.admin.TestAdminOwnershipModerationUX.test_place_admin_change_form_shows_visibility_controls`
- `catalog.testcases.admin.TestAdminOwnershipModerationUX.test_place_admin_changelist_searches_by_azerbaijani_name`
- `catalog.testcases.admin.TestAdminOwnershipModerationUX.test_place_admin_changelist_shows_stats_and_quick_filter_counts`
- `catalog.testcases.admin.TestAdminOwnershipModerationUX.test_place_admin_changelist_uses_compact_search_panel`
- `catalog.testcases.admin.TestAdminOwnershipModerationUX.test_place_admin_restore_view_confirms_and_restores_place`
- `catalog.testcases.admin.TestAdminOwnershipModerationUX.test_place_admin_shows_coordinates_and_map_readiness_statuses`
- `catalog.testcases.admin.TestAdminOwnershipModerationUX.test_place_review_admin_change_form_shows_full_text_panel`
- `catalog.testcases.admin.TestAdminOwnershipModerationUX.test_user_change_form_has_no_groups_block`
- `catalog.testcases.admin.TestAdminTemporaryEventInputs.test_place_change_page_renders_single_compact_datetime_inputs`
- `catalog.testcases.admin.TestAdminTemporaryEventInputs.test_place_changelist_filters_by_staff_member_who_added_card`

## Limits and handoff

No PostgreSQL concurrency/constraints validation: no psql; local snap Docker blocked by read-only runtime-dir sandbox. Source/admin template review is not rendered-browser evidence; parent owns real admin/public browser checks. No production state evaluated by this role. No broad backend/full project suite or real external integration calls run.

Codebase Memory available: project `home-ramin-kidsmap`, root verified, full index generation `2026-09-10T11:32:24Z`; relevant Python paths reported no recorded parse gaps before fixes. Changed templates have known partial parsing, inspected by direct source. Graph is best-effort, actual dirty source used for conclusions.

Named handoff: kidsmap-orchestrator / release owner — verify final snapshot and retain baseline-failure disclosure; don't label full suite green. Django/security owner — preserve new ownership ACL invariant; no further authority expansion requested.
