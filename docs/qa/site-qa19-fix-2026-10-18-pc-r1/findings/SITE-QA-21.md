# SITE-QA-21 — desktop catalog JSON cards overflow their narrow grid column

**OPEN / P2 / LOCAL, 2026-10-18.** Newly reachable UI defect after the existing pre-render500 is removed. No CSS/template/layout change in this fix; not a production observation.

With the original short fictional JSON restored by a real native save, superuser GET in RU/AZ/EN at1280/1440 produces an entire form398–468px wide inside a1022px content area. The grid reserves320px for actions; its main column measures60–130px. Visible section cards are wider than that column and geometrically overlap the actions area. JSON textareas measure **73.52px RU /83.80px EN /93.59px AZ**, despite desktop viewport1440. [Native rectangles/ancestor chain](../evidence/browser-layout.json), [derived visible-card assessment](../evidence/desktop-layout-assessment.json), full-page PNGs `desktop-layout-{az,ru,en}-{1280,1440}.png`. Original36-cell matrix independently records those textarea widths; desktop screenshots were visually inspected.

The initial diagnostic's main-grid-rectangle nonoverlap check passes because the overflowing visible card exceeds that rectangle. The retained assessment checks actual card boundaries:6cells/12intended failures. No result is relabeled as a passing layout. Short-fixture restoration2checks pass; pageerrors0. This is not a long-brand fixture or global horizontal-scroll proof.

Source boundary: shared settings template's `#content-main.km-place-form-page` within Jazzmin's `.row`, `.km-place-form-layout`/`.km-place-form-main` and `static/admin/css/pages/kidsmap_admin_form_shell.css` grid/container rules. Template/CSS/source SHA equal fix entry. Measured parent is flex `.row`; shrink-to-content form plus fixed action column and card overflow explain the immediate geometry. The full winning CSS cascade and minimal repair remain **UNCONFIRMED**, to be established in a separate plan. Do not claim one proven CSS-line fix.

Impact: structured JSON editing on desktop is reduced to a few characters per line, and section content extends into the action column. P2 bounded editor usability, not data loss/permission failure. Valid/invalid/retry saves pass independently. This differs from SITE08's mobile text/file overflow; the mobile hidden-save limitation remains tracked there. Translation correction is outside this finding.

Owner: frontend-admin. Next: bounded source/cascade diagnosis and concrete shared-shell plan; preserve all consumers, values, keyboard, view-only authority and error states in3languages across360–1440. No CSS/template fix approved/applied in SITE19.

Count reconciliation is in [SITE20](SITE-QA-20.md) and the fix report:15OPEN (11P2/4P3) after original19 closure and2new findings.
