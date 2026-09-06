# Photo workflow implementation plan

**Goal:** Validate and prepare photos immediately, retain them on failed saves, support accumulation, ordering and main-photo selection.
**Architecture:** Authenticated sequential image preparation returns normalized WebP without persistent temporary media. Final AJAX form submission uses existing owner controllers and validated gallery ordering. Standard submissions remain available. Shared server limits configure the browser.
**Tech stack:** Django, Pillow/pillow-heif, native JavaScript and CSS.
**Spec:** Six photo-upload improvements requested in this conversation.

- [x] Test image pixel/byte limits, HEIC, preparation access/errors, gallery ordering and retry-safe AJAX persistence in `src/catalog/testcases/photo_workflow.py`.
- [x] Reduce allocations in `services/image_uploads.py`, enforce 50 MP / 12000 px / 15 MB source limits, 2400 px / 2 MB output and 22 MB final photo batch. Keep Nginx 25 MB with overhead.
- [x] Add authenticated preparation and final-save endpoints in `photo_views.py`; configure forms from server limits and persist validated gallery ordering via existing controllers.
- [x] Add a focused photo editor script and template: per-file validation/errors, sequential preparation, small previews, duplicate detection, accumulation, removal, main-photo swaps and accessible ordering controls / drag and drop.
- [x] Integrate final upload progress, saved/error states and retry with the existing wizard. Compact photo requirements only.
- [x] Run Django/DOM tests, syntax checks, and browser checks if available; document deployment and verification limits.

Verification: final targeted run 48 Django tests passed; 8 photo DOM tests and 3 phone DOM regression tests passed. Django check and JS syntax checks passed. Browser visual checks unavailable. See docs/PHOTO_WORKFLOW.md for the memory benchmark and deployment details.
