# Public section switches — local verification

User-authorized local implementation, LOCAL HEAD2da9d33 plus dirty WORKTREE. Prior directory changes preserved. Concurrent public_entities.css edits belong to other work and were not reverted. Production NOT_RUN; no commit/push.

## Administration

Open `/admin/catalog/sitevisibilitysettings/` or Administration → Site settings → Sections. Three independently persisted controls share one section: Show Events, Show Educators and specialists, Show Organizations. Save and continue / Save and exit apply changes; check again and save to restore visibility. Data is never deleted by a flag. Existing Event/Specialist owner-interface behavior is retained. Organization administration and owner workspace remain available while its public section is hidden.

Organization OFF removes directory/detail routes (404), desktop/mobile/footer links, catalog/autocomplete discovery, organization link blocks on Place/Activity cards/details and static/entity sitemap entries. Places and inherited approved content/contacts remain available. Existing Event OFF returns410 and Specialist OFF404. Existing flags retain their values; additive migration0135 defaults Organizations toTrue to preserve the preceding directory behavior.

Admin form: labelled controls with native checked semantics, help text, visible focus, separate responsive rows. The old visibility-only CSS assumed a single checkbox and narrowed the content to52px, causing overlap when grouped; replaced with scoped site_sections.css and a visibility-only rendering branch. Other shared-settings forms keep the standard fieldset renderer.

## Evidence

RED: `/tmp/kidsmap-section-switches-red`:4 tests failed as expected (3 failures, missing-feature import error).

Final command:

```sh
PATH="$PATH:/snap/bin" python3 docs/task33/qa04/run.py --output /tmp/kidsmap-section-switches-final --label catalog.testcases.test_public_section_switches --label catalog.testcases.events_feature --label catalog.testcases.specialists --label catalog.testcases.test_organization_directory --label catalog.testcases.test_task33_public_details
```

44/44 PASS, Django checks clean, disposable PostgreSQL/media/cache isolation and cleanup PASS. Full historical suite NOT_RUN. Owned synthetic preview applied migration0135 on restart; makemigrations catalog --check --dry-run returned No changes detected.

Rendered browser verification through actual admin form saves: all flags OFF, then each flag individually ON;12 link/HTTP assertions passed. Disabled routes410/404/404, enabled routes200. Actual admin Organization changelist remains200. All three original flags restoredTrue. Synthetic totals preserved:4 organizations,133 places,9 specialists.

Admin layout at390,768,1200,1440px: no horizontal overflow, no label/input overlap, all5 rendered fields have correctly associated labels, checkbox keyboard focus visible. Screenshots inspected after fixing layout. Ignored evidence `.tmp/section-switch-browser.log`, `.tmp/section-switch-layout.log`, `.tmp/section-switches-admin-390.png`, `.tmp/section-switches-admin-1440.png`.

## Manual check

1. Open Sections, switch off a section, Save and continue.
2. Reload the public homepage: corresponding desktop/mobile/footer links disappear. Open its saved URL: section is unavailable.
3. For Organizations, search the catalog for a network: organization links disappear while place cards remain available. Organizations are still editable in admin.
4. Enable it and save: menu links and pages return. Other two flags keep their state.
5. Inspect controls at phone width, and use Tab/Space to toggle followed by Save. No server restart is required for a saved flag.

Visual acceptance remains awaiting_user_review. Existing unrelated specialist map localized-coordinate JS issue is outside this scope.
