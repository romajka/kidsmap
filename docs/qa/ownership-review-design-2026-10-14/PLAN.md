# Ownership review design

Explicit local UI implementation authorization from the user. Keep moderation,
publication, permissions and preview routes intact; no production or Git writes.

1. Add read-only review statistics and an actual displayed-versus-live change
   summary in `catalog/services/admin_place_preview.py`. Count complete name +
   description language pairs, stored/available photos, nested groups, and existing
   readiness items. Compare full snapshots, preserve explicit cleared values.
   Add isolated tests for changed/unchanged/current snapshots before implementation.
2. Redesign `placeownershiprequest/preview.html` and its scoped CSS: compact
   photo/title hero, version/source, four useful metrics, accessible changes list,
   section navigation and clear decision sidebar. Preserve every field/photo,
   preview and moderation link. Add no fake engagement statistics.
3. Add scoped JS for active section navigation and small reduced-motion-aware
   transitions. Keep language filters, details and accessible gallery unchanged.
   Add exact RU/AZ/EN messages without rewriting existing locale files.
4. Verify targeted existing admin + website preview tests, isolated read-only
   requests, and actual Chromium user paths at 390/768/1024/1440 in RU/AZ/EN:
   navigation, versions, all-language content, photo modal, keyboard, missing data,
   long titles, no horizontal overflow and reduced motion. Save screenshots and
   precise limits. Leave the user-requested local stand running for manual review.

Execution stays in this session. Changes are confined to the review presentation,
locale additions and task-owned evidence; existing dirty work is preserved.
