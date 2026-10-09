# Optional listing verification retired — local checks

User authorized removing Verified markers and the ability to assign them across public listings/admin. LOCAL HEAD2da9d33 plus dirty WORKTREE. Preceding organization-directory/section-switch changes and concurrent event/public-detail changes preserved. Production NOT_RUN; no commit/push.

## Behavior

Place and Specialist public badges and verified-only controls removed. Old verified query parameters are removed by existing clean-query middleware; filters no longer use the flags. Removed catalogue100% verified claim and verified-place marketing copy. Optional is_verified fields retained for compatibility but noneditable (state migration0136); all admin fieldsets, bulk assignment/removal actions, badge columns, filters and optional verification metrics retired. Existing legacy True values do not affect rendering.

Price caution no longer depends on the optional badge and does not claim open-source provenance for all prices. Actual email/person/ownership confirmation, publication readiness, moderation, document consent and pricing approval remain intact. Historical audit records/data are retained. Demo seed scripts can retain historical boolean values, but there is no UI/form badge assignment and they cannot cause a public marker.

Updated three existing admin assertions and the legacy price-caution test to reflect the explicitly requested retirement. Publication/date and note escaping assertions retained; these are contract updates, not suppressed failures.

## Evidence

RED `/tmp/kidsmap-remove-badges-red`:3 tests failed on existing public badges, admin editable field/action and verified-only search.

Final exact command:

```sh
PATH="$PATH:/snap/bin" python3 docs/task33/qa04/run.py --output /tmp/kidsmap-remove-badges-acceptance --label catalog.testcases.test_retired_verification_badges --label catalog.testcases.test_task33_publication --label catalog.testcases.test_task33_specialist_security_review --label catalog.testcases.test_public_section_switches --label catalog.testcases.test_organization_directory --label catalog.testcases.test_legacy_pricing_notes --label catalog.testcases.admin.TestAdminTemporaryEventInputs.test_place_management_controls_are_compact_and_not_duplicated --label catalog.testcases.admin.TestAdminOwnershipModerationUX.test_place_admin_change_form_uses_readonly_service_dates_instead_of_raw_datetime_widgets --label catalog.testcases.admin.TestAdminSpecialistChangeList.test_change_list_uses_catalog_dashboard_and_real_specialist_metrics
```

74/74 PASS, Django checks clean, PostgreSQL/media/cache isolated, owned disposable container cleanup PASS. Stronger fixture ensures a ready published Place with legacyTrue actually appears in catalog; name assertion and no-badge assertion passed in the final run. Full historical suite NOT_RUN.

Owned synthetic preview restarted, migration0136 applied without clearing records. makemigrations catalog --check --dry-run: No changes detected. Legacy flags:6 specialistsTrue,0 placesTrue; both model fields editableFalse.

Rendered browser badge/control checks: RU/AZ/EN ×390/1440px × catalogue/specialist list/specialist detail/place detail (24 contexts), plus Place/Specialist admin list/edit pages (4 contexts), all PASS. No optional badge/filter/assignment inputs/actions and no public horizontal overflow. Existing specialist localized-coordinate map JS baseline is outside this check; no claim that every site's JS flow is green. Local ignored evidence `.tmp/badges-browser.log`, `.tmp/place-admin-no-badge.png`.

## Manual acceptance

1. Reload catalogue and specialist list/details: no Verified marker or verified-only filter.
2. Open old `/ru/specialists/?verified=1`: parameter is cleaned and ordinary published profiles remain discoverable.
3. Edit a Place or Specialist in admin: no optional Verified control. Bulk action menus lack mark/unmark verified, publication/moderation actions remain.
4. Inspect a previously verified specialist: same public profile remains, marker is absent. Section visibility switches remain independently usable.

Visual acceptance awaiting_user_review. No application data or historical audit records deleted.
