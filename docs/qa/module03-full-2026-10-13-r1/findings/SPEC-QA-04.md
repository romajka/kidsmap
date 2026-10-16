# SPEC-QA-04 — mobile navigation buttons have no visible arrows

CLOSED LOCAL, P3, fresh LOCAL baseline2026-10-13. Checkout /home/ramin/kidsmap, task33-progress, HEAD e4e05cc213b34e2d771ecb854901bfd016d1db51 + approved dirty WORKTREE. Not a proven regression; missing glyph wiring predates the height fix.

Reproduce: verified-person/author specialist editor, RU/AZ/EN360/390/768. Header is now readable and32px buttons are fully visible, but both buttons have no arrow glyph. Native controls and their translated accessible names still work, as demonstrated by keyboard/step-transition checks.

Evidence: [RU390 detail](../screenshots/progress-detail-ru-390.png), other8 `progress-detail-*.png`; loading PNG also shows empty controls. Actual markup `src/catalog/templates/pages/owner_specialist_create.html:135` and136 uses unsupported `fas fa-chevron-left/right`. Bounded search across actual templates/styles/scripts finds no Font Awesome loader/class wiring. Local `static/img/icon/coolicons.iconjar/icons/chevron-left.svg` and right.svg exist; site.css defines corresponding variables.

Impact: direction of mobile navigation is unclear for sighted users. No demonstrated data loss, ACL bypass or blocked submit. Original SPEC-QA-03 clipping and this glyph omission are separate root causes.

Concrete repair plan: [2026-10-13-spec-qa04-mobile-arrow-glyphs.md](../../../superpowers/plans/2026-10-13-spec-qa04-mobile-arrow-glyphs.md), only static/css/pages/specialists.css. Approved in this chat; CSS-only repair accepted by180 native/layout checks, actual glyph screenshots, SVG200 and no added external transport. [Acceptance](../arrows-acceptance.json). No production claim.
