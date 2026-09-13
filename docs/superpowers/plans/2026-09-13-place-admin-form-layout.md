# Place Admin Form Layout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the Place edit form fit the available admin workspace at 1366, 1440, 1600 and 1920px without page-level horizontal scrolling, clipped field labels, or a sidebar that makes data entry impractical.

**Architecture:** The Place form has its own template and stylesheet: `change_form.html` renders the main column, a sticky summary aside and a narrow-screen action bar; `kidsmap_place_form.css` owns that layout. The breakpoint must be based on the viewport after allowing for Jazzmin's persistent left navigation, so the Place summary moves below the form before its fixed-width aside constrains the central editing column. Existing Event, user and region forms continue to use the separate legacy shared shell and must be audited independently before any shared CSS change.

**Tech Stack:** Django admin templates, scoped CSS Grid/Flexbox, vanilla JavaScript, Django `TestCase`, Playwright CLI for rendered-browser verification.

**Spec:** User request of 2026-09-13: desktop Place editing form must remain readable with the sidebar open; eliminate unnecessary horizontal scroll; inspect age, location, photo, verification and other sections at 1366/1440/1600/1920px; audit other admin forms for the same defect.

## Global Constraints

- Preserve the current Place form's DOM data hooks and JavaScript behavior: `data-km-admin-form`, accordion controls, media, location, price and schedule editors.
- Do not mask an overflow defect with `overflow-x: hidden`; every visible control must remain reachable and its label readable.
- Keep native buttons and current keyboard/focus behavior. If a responsive control is added, it requires an accessible name and correct `aria-expanded` / `aria-controls` state.
- Do not modify production data, schema, configuration, deploy state, or unrelated admin forms without rendered evidence of the same fault.
- Run Django tests only with `DJANGO_TESTING=1` and use an isolated test database.
- Do not commit or push as part of this task.

---

## File map

- Modify: `src/catalog/testcases/admin.py` — HTML contract coverage for the Place layout, including the responsive action bar and form sections that must remain mounted.
- Modify: `static/admin/css/pages/kidsmap_place_form.css` — scoped responsive grid, sidebar, navigation, field-grid and sticky-action-bar rules.
- Modify only if browser audit proves an equivalent defect: `static/admin/css/pages/kidsmap_admin_form_shell.css` — shared legacy shell used by Event, ownership request, review, user, region and settings forms; no Place rules belong here.
- Inspect, do not change unless an accessibility gap is found: `src/catalog/templates/admin/catalog/place/change_form.html` and `static/admin/js/kidsmap_place_form.js` — template structure and behavior hooks for the form.

### Task 1: Lock the rendered Place-form contract before changing layout

**Files:**
- Modify: `src/catalog/testcases/admin.py:1334-1365`
- Inspect: `src/catalog/templates/admin/catalog/place/change_form.html:83-241`

**Interfaces:**
- Consumes: `PlaceAdmin.render_change_form()` context and Django admin add-form route `admin:catalog_place_add`.
- Produces: a regression test that proves CSS and JS continue to receive `km-pf__shell`, `km-pf__layout`, `km-pf__main`, `km-pf__side`, `km-pf__stickybar`, the accordion hooks, and every primary section.

- [ ] **Step 1: Extend the failing HTML contract test.**

  Add exact assertions to `TestAdminOwnershipModerationUX.test_place_admin_change_form_uses_step_layout`:

  ```python
  self.assertContains(response, "admin/css/pages/kidsmap_place_form.css")
  self.assertContains(response, 'class="km-pf__layout"', html=False)
  self.assertContains(response, 'class="km-pf__main"', html=False)
  self.assertContains(response, 'class="km-pf__side"', html=False)
  self.assertContains(response, 'class="km-pf__stickybar"', html=False)
  for section_id in ("basics", "pricing", "location", "media", "verification"):
      self.assertContains(response, f'id="{section_id}"', html=False)
  ```

- [ ] **Step 2: Run the focused test and confirm the current structure is captured.**

  Run:

  ```powershell
  $env:DJANGO_TESTING='1'; .\.venv\Scripts\python.exe manage.py test catalog.testcases.admin.TestAdminOwnershipModerationUX.test_place_admin_change_form_uses_step_layout --noinput
  ```

  Expected: PASS before and after the CSS work. A failure means the template contract changed and must be reconciled before styling continues.

- [ ] **Step 3: Preserve the template and hook names.**

  Do not rename or remove `data-pf-sidebar`, `data-pf-stickybar`, `data-pf-nav`, `data-place-accordion-*`, `data-km-schedule-editor`, `data-gallery-root` or `data-km-admin-form`. The layout correction must be CSS-only unless a browser test identifies an accessibility need that CSS cannot solve.

- [ ] **Step 4: Re-run the focused test.**

  Run the command from Step 2. Expected: PASS.

### Task 2: Correct the Place shell's desktop breakpoint and width budget

**Files:**
- Modify: `static/admin/css/pages/kidsmap_place_form.css:126-135,496-514,3004-3118,3956-3987`
- Inspect: `src/catalog/templates/admin/catalog/place/change_form.html:151-240`

**Interfaces:**
- Consumes: the existing `km-pf__layout` grid with `km-pf__main` and `km-pf__side`, plus the action bar that is always present in the DOM.
- Produces: two-column editing only where the remaining workspace can support it; a one-column form plus the existing action bar at narrower desktop widths.

- [ ] **Step 1: Add a CSS regression checklist as comments adjacent to the responsive rules.**

  Document the actual width budget, not a generic mobile breakpoint: Jazzmin's left navigation consumes roughly 300px, therefore a 1366px viewport leaves about 1066px for the Place page. State that the 2-column mode requires enough room for the main form, 20px gap and the 230–300px aside.

- [ ] **Step 2: Change the responsive mode boundary before the central column becomes cramped.**

  Keep the large-screen layout expressed with shrinkable tracks:

  ```css
  .km-pf .km-pf__layout {
    grid-template-columns: minmax(0, 1fr) clamp(230px, 18vw, 300px);
    gap: 20px;
  }
  ```

  Replace the current `@media (max-width: 1100px)` two-column collapse condition with a documented desktop threshold that covers 1366px and 1440px with the admin navigation visible (start at `max-width: 1535px`, then adjust only if rendered measurements prove a different threshold). In that mode:

  ```css
  .km-pf .km-pf__layout { grid-template-columns: minmax(0, 1fr); }
  .km-pf .km-pf__side { position: static; min-width: 0; max-height: none; }
  .km-pf .km-pf-side__card { max-height: none; }
  .km-pf .km-pf__stickybar { display: flex; }
  ```

  Preserve the `minmax(0, 1fr)` / `min-width: 0` protections on the page root, main column and field wrappers. Do not introduce global overflow clipping.

- [ ] **Step 3: Make the narrow action bar fit instead of creating a second overflow source.**

  In `.km-pf__stickybar`, add `min-width: 0` and `flex-wrap: wrap`; make the progress bar flex and shrink safely:

  ```css
  .km-pf .km-pf__stickybar { min-width: 0; flex-wrap: wrap; }
  .km-pf .km-pf__stickybar > .km-pf-bar { flex: 1 1 180px; min-width: 0; }
  ```

  Retain the visible, native Save and Publish buttons. Their labels may wrap only at genuinely narrow mobile widths; do not reduce type solely to force one line.

- [ ] **Step 4: Run the focused server-side form tests.**

  Run:

  ```powershell
  $env:DJANGO_TESTING='1'; .\.venv\Scripts\python.exe manage.py test catalog.testcases.admin.TestAdminOwnershipModerationUX.test_place_admin_change_form_uses_step_layout catalog.testcases.admin.TestAdminOwnershipModerationUX.test_place_admin_add_form_hides_change_only_inlines_and_collapses_system_fields --noinput
  ```

  Expected: PASS. These tests protect template composition; rendered widths are verified in Task 4.

### Task 3: Make each Place section shrink and reflow without clipped labels

**Files:**
- Modify: `static/admin/css/pages/kidsmap_place_form.css:321-460,736-830,837-964,1562-1593,3303-3902,3956-3987`
- Inspect: `src/catalog/templates/admin/catalog/place/form/section_pricing.html`, `section_location.html`, `section_media.html`, `section_verification.html`, `pricing_editor.html`

**Interfaces:**
- Consumes: the existing section classes `km-pf-grid--2`, `km-pf-grid--3`, `km-pf-age`, `km-schedule-editor`, field labels and `<main>` editors.
- Produces: semantic content reflow for age/pricing, location/contacts, media, schedule and verification while retaining existing inputs and JS selectors.

- [ ] **Step 1: Audit the actual widest item in every primary section at the four target widths.**

  Record, from browser inspection, `document.documentElement.scrollWidth`, `document.documentElement.clientWidth`, the bounding rectangle of `#content-main`, and the first overflowing descendant if they differ. Inspect the Age / duration row, three-column address and contacts grids, pricing-plan editor, gallery controls, schedule table and verification panel. Do not rely on CSS source alone.

- [ ] **Step 2: Reflow field groups from available form width, not the outer viewport.**

  Keep `repeat(..., minmax(0, 1fr))` for multi-field grids. At the same desktop threshold as Task 2, convert only the crowded three-column location, contacts and translated custom-price grids to two equal columns; at the existing narrow breakpoint convert them to one column. Use the established classes rather than adding fixed widths or new wrapper markup.

  Preserve the age range as paired fields where it fits, but ensure `.km-pf-age__range`, `.km-pf-age__duration` and `.km-pf-age__flags` can wrap and have `min-width: 0`. At narrow widths, stack the range, flags and duration in reading order without hiding the open-ended-age or adult-program controls.

- [ ] **Step 3: Replace navigation scrolling with reflow where it is avoidable.**

  In the narrow rules, replace `.km-pf__nav { overflow-x: auto; }` and fixed 150px nav items with a wrapping grid or `flex-wrap: wrap` that preserves native anchor controls and their full accessible labels. Keep `aria-current` behavior owned by `kidsmap_place_form.js`; no script change is required for CSS wrapping.

- [ ] **Step 4: Restrict horizontal scrolling to an intrinsically tabular editor.**

  The schedule editor may retain a local scroll container only while its wide table variant is visible. When the schedule rules switch rows to a single-column representation, remove its need for table-width scrolling. Page root, shell, main column, section cards, field grids and sticky action bar must never become horizontal scroll containers.

- [ ] **Step 5: Check accessible responsive behavior.**

  Tab through accordion buttons, form controls, nav anchors and sticky Save/Publish. Confirm the visible focus indicator remains, labels are associated with controls, each button has text or an accessible name, and no element becomes keyboard-inaccessible after wrapping.

### Task 4: Verify rendered layout and audit the other admin form shells

**Files:**
- Inspect: `src/catalog/templates/admin/catalog/place/change_form.html`
- Inspect: `static/admin/css/pages/kidsmap_place_form.css`
- Inspect: `src/catalog/templates/admin/catalog/event/change_form.html`, `user/change_form.html`, `region/change_form.html`
- Inspect conditionally: `static/admin/css/pages/kidsmap_admin_form_shell.css`

**Interfaces:**
- Consumes: a local, non-production Django instance with an authorized test admin and a Place containing values for every primary section.
- Produces: screenshots and measured overflow results for Place, Event, User and Region; a shared-shell fix only when the audit reproduces the defect outside Place.

- [ ] **Step 1: Start an isolated local test instance and authenticate as its test administrator.**

  Use no production host, credentials or data. Follow the repository's test setup (`DJANGO_TESTING=1`) and create the test user only in the isolated test database. Open the Place add and change pages through the local server.

- [ ] **Step 2: Use Playwright CLI for each required desktop viewport.**

  Confirm `npx` exists, then use the repository-supported wrapper:

  ```powershell
  $env:PWCLI = 'C:\Users\Ramin\.codex\skills\playwright\scripts\playwright_cli.sh'
  & $env:PWCLI open http://127.0.0.1:<port>/admin/catalog/place/<place-id>/change/ --headed
  & $env:PWCLI snapshot
  & $env:PWCLI screenshot --path output/playwright/place-admin-1366.png
  ```

  Repeat at viewport widths 1366, 1440, 1600 and 1920px, with the Jazzmin left sidebar open. Take snapshots for Basics/Age, Location, Media, Schedule and Verification. At every viewport verify all of the following:

  ```text
  document.documentElement.scrollWidth === document.documentElement.clientWidth
  #content-main.scrollWidth <= #content-main.clientWidth
  each visible input/select/textarea has a visible associated label
  the right summary is beside the form only where the form remains readable;
  otherwise it follows the form and the sticky action bar remains usable
  ```

  Save screenshots only under `output/playwright/`; do not add them to Git.

- [ ] **Step 3: Exercise a representative edit without saving production data.**

  On the isolated page, edit age, address, one contact, a photo selection and a schedule interval; navigate between accordion sections and use keyboard Tab. Verify no control jumps off-screen and no new page-level horizontal scrollbar appears. Do not submit against a non-test database.

- [ ] **Step 4: Audit Event, User and Region at 1366 and 1440px.**

  Their templates load `kidsmap_admin_form_shell.css`, which is explicitly separate from the Place stylesheet. Record per route whether root or content overflow occurs. If all pass, leave the shared stylesheet unchanged. If a reproducible shared-shell overflow appears, add a narrowly scoped, component-specific CSS fix and a corresponding Django HTML contract test; do not copy Place rules into the legacy shell.

- [ ] **Step 5: Run final automated checks.**

  Run:

  ```powershell
  $env:DJANGO_TESTING='1'; .\.venv\Scripts\python.exe manage.py test catalog.testcases.admin.TestAdminOwnershipModerationUX --noinput
  ```

  Expected: PASS. Report the exact browser viewport results, any untested route, and any existing unrelated test failure rather than claiming visual success from source inspection.

## Self-review

- The plan directly covers desktop container width, summary-sidebar budget, global vs local horizontal scroll, field labels, Age, Location, Photos, Schedule and Verification.
- It separates the Place-specific stylesheet from the legacy shared shell and makes other-form changes conditional on reproduced evidence.
- It keeps the current form hooks, accessibility semantics and data-entry actions intact.
- The plan contains no database, production, deploy, commit or push operation.

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-09-13-place-admin-form-layout.md`. Implementation requires approval under the repository rule in `AGENTS.md`: “Future implementation requires a concrete plan and user approval for its scope.”
