# Living Map across public pages

The user approves the current hero and authorizes extending its animated background to every public page, with pointer/click response and vertical journeys continuing into the footer.

- [x] Test public route eligibility and full-height route geometry, including narrow screens and content exclusion.
- [x] Move the single Canvas and its assets from the homepage to shared base, gated by an explicit public visitor-page allowlist. Account, authentication and owner workflows stay outside this decorative scope.
- [x] Preserve existing hero stories. Add continuous vertical trails down both page edges, traveling light segments and destination icons in available space. Connect their ends to the footer. Add bounded, passive click/tap ripples; reduced motion remains static.
- [x] Verify representative public pages in three languages and desktop/mobile widths, navigation and FAQ, no added overflow/Canvas interaction interception, route continuity at the footer, lifecycle and frame cadence. Capture rendered motion evidence and document limits in `docs/LIVING_MAP_PUBLIC.md`.

Scope: shared template/context flag; living-map CSS/JS and focused tests/docs only. No database/schema changes, production operations, commits or push. Preserve unrelated dirty worktree changes.
