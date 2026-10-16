# Full ownership-request preview implementation plan

Goal: a reviewer can inspect every saved card section, unpublished content and
the submitted candidate without publishing, editing or tracking the card.

Architecture: a GET-only admin preview route resolves the ownership request,
checks concrete request and Place object permissions, and renders a dedicated
read-only context. Reuse publication snapshots, readiness, pricing and schedule
serializers. Keep existing approve/reject confirmation and POST services.

Scope authorized by the user's request: functional and visual completion of
card inspection from the ownership-request list. Preserve all existing dirty
work, including the preceding sidebar fix. No production, commit/push/deploy.

Files:
- `src/catalog/domain_admin/owner.py`: protected preview route and entry links.
- `src/catalog/services/admin_place_preview.py`: complete saved/candidate context.
- `src/catalog/templates/admin/catalog/placeownershiprequest/preview.html` and
  `preview_fields.html`: review content, translations, gallery, nested offers.
- `static/admin/css/pages/kidsmap_ownership_preview.css` and
  `static/admin/js/kidsmap_ownership_preview.js`: responsive sections, languages,
  accessible native photo dialog and keyboard behavior.
- `src/catalog/testcases/test_ownership_admin_preview.py`: regression/ACL/read-only
  tests; locale PO additions and isolated browser evidence in this folder.

Acceptance:
- [x] New route reproduces the current missing preview before implementation.
- [x] Pending/unpublished and published Places both render without a public GET.
- [x] All descriptions/languages, contacts, prices (including inactive and group
  tariffs), structured/text schedules, photos/captions and request details render.
- [x] Submitted candidate takes precedence; partial patch retains the complete
  base. Changed versions are prominently flagged and cannot look approvable.
- [x] Anonymous, owner, volunteer and insufficient staff access are denied;
  GET writes no Place, revision, audit, engagement or tracking rows; POST is 405.
- [x] Links lead to existing decision confirmations; ownership and publication
  decisions have distinct labels and explanatory text.
- [x] Real authenticated synthetic browser flow: list → preview → sections →
  gallery → language controls → confirmation/back, RU/AZ/EN and narrow widths.
- [x] Fresh targeted Django and browser checks; record exact limits in REPORT.md.
