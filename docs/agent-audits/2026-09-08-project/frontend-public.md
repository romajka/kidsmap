# Frontend public audit — 2026-09-08

Role: frontend-reviewer; execution identity `/root/audit_qa`, sequential after frontend-admin/integration-reviewer, **not an independently spawned second reviewer**. Definition read: `.agents/agents/frontend-reviewer/agent.md`. Skills: kidsmap-ui-design, frontend-design, fixing-accessibility. LOCAL HEAD `d75b34f4db5d4ba484cf8392ff3ae0c9939031e2`, unchanged application WORKTREE; PRODUCTION UNKNOWN/uncontacted. Source-only bounded review of public card/catalog/home/favorites/map and owner wizard. Independent browser QA belongs to `/root/audit_browser`; no new tests, browser sessions or application edits here.

## 1. Состояние области

Verified shared card consumers: `pages/home.html:336`, `catalog/place_list.html:852`, `pages/account_favorites.html:116` include `catalog/includes/place_card.html`. Detail/map popup/volunteer card have separate markup. Card prices use backend `card_price_badge_value/currency` and contacts include phone_reveal. Catalog/home map code consumes `has_phone` and constructs shared phone-reveal buttons (`catalog_map.js:301`, `home_map.js:294`); legacy test expectations of raw phone fields are not the intended current wire contract. Owner permanent form loads server copy/rules JSON and enhances original named fields in `permanent_place_wizard.js`.

Codebase Memory coverage reused current metadata for wizard script; known partial-template parsing means source search is authoritative for markup/consumers. No computed style, real overflow or external map rendering personally measured.

## 2. Сильные стороны

A common card protects price/contact parity across three public surfaces. Favorite buttons expose aria-pressed and localized add/remove labels. Phone reveal supplies loading state and error descriptions (`place_phone_reveal.js:273,332–339`); raw tel assertions failing does not make reveal flow broken. Wizard uses server JSON configuration, restores named controls, focuses step headings/errors, keeps native controls as form values, tracks dirty state and offers browser draft recovery. These are implemented mechanisms, not evidence of full browser correctness.

## 3. Реальные проблемы

**UIP-01 — P2: enhanced subcategory clear action is unavailable by ordinary keyboard navigation.** LOCAL, high source confidence, browser hypothesis sent. `static/js/permanent_place_wizard.js:391–399` creates a `span` role=button inside the main trigger button, without tabindex or keyboard handling; only click listener at572 clears selection. Native select is clipped and removed from Tab order at436–437 (`permanent_place_wizard.css:84`). Trigger Enter/Space opens the menu, rather than operating nested clear span. Trigger: choose subcategory, navigate solely with Tab/Shift+Tab/Enter/Space, attempt the visible clear action. Impact: mouse-only clear control plus nested interactive semantics; users can choose a different option, but that does not provide keyboard access to the explicit clear action. Owner frontend-reviewer/a11y; next step separate native clear button, preserve label/selection/focus, verify selection and clearing with keyboard. Menu additionally uses listbox/option roles with only Escape key handling at601–607, lacking an intentional arrow-key model; review this alongside the clear fix, not as a separate inflated finding.

Previously established cross-surface findings, not duplicated: **QA-03** header drawer contains three untranslated Russian messages on AZ/EN (`includes/header.html:335,355,445`), confirmed by earlier local Django response tests and absent matching msgids in locale source. **UIA-03** applies to owner `pages/includes/permanent_place_field.html:13–15` too: help/server errors/client errors render without target IDs, while fields can reference generated help/error IDs. Browser agent received drawer and wizard scenarios. Owner/admin publication parity remains backend-owned **BE-02**, not a new UI finding: client `issues()` repeats description/tariff gate and cannot substitute canonical readiness.

## 4. Tech debt

Shared card has no schedule row although home map popup does (`home_map.js:285–290`); this is a product-information tradeoff requiring a design decision, not proof of a functional bug. Card currency span may be empty because formatter already provides a complete label; this is not duplicate-currency evidence. Three price editors and client-side gate calculations need one backend contract, but no UI enums should be rewritten during audit.

## 5. Risks

Reused public tests include stale phrase/layout assertions. “Password reset” vs “Reset password”, direct tel links vs reveal controls, and count-copy changes do not establish user-visible malfunction without checking current intent/rendering. Some localization/ARIA failures may mix real missing translations with obsolete wording; QA-03's three literal messages are separately verified. Actual Maps provider success, geolocation permissions, real device scroll/keyboard, contrast and all width/locale combinations remain browser-owned/NOT VERIFIED here. Browser recovery and async upload concurrency were not newly exercised.

## 6. Dead/legacy candidates

No files recommended for deletion. Raw phone contract assertions are review candidates, not instructions to restore raw fields or remove tests. Separate map/detail/card templates have active consumers; similar markup is not dead code. Legacy owner paths and scalar/schedule compatibility require backend/data evidence before cleanup.

## 7. Tests gaps

No new suites or browser sessions in this role. Earlier integration-reviewer evidence on same unchanged source: 375 selected executions with12 failure records in public.py, plus163 with one map-query-budget failure; total538 executions, not unique coverage. Source-only review does not expand those test claims. Add keyboard-only subcategory selection/clear, invalid-field description reference checks, mobile drawer locale tests and parity scenarios across home/catalog/favorites/map. Existing default discovery omits wizard/media/phone tests; see QA-01.

## 8. Recommendations

First make the enhanced subcategory controls independently keyboard-operable and correctly associated with labels/errors. Repair confirmed drawer translation gaps; align tests to approved copy and reveal behavior after review, without weakening coverage. Use browser QA to determine visual priorities across320/390/768/1024/1280/1440 and AZ/RU/EN. Consolidate backend-derived readiness and price semantics in a separate approved implementation scope; retain form names, recovery and upload contracts.

## 9. P0/P1/P2/P3

No public-UI P0/P1 established. P2 UIP-01 keyboard-inaccessible clear action; inherited QA-03/UIA-03 retain their original IDs/owners. Missing card schedule is an undecided design candidate, no severity assigned. Visual polish and production usability remain ungraded without rendered evidence.
