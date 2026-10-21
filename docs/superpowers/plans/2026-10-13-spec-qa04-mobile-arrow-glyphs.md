# SPEC-QA-04 — visible mobile navigation arrows

Status: AWAITING APPROVAL. Supplemental to accepted SPEC-QA-01–03 and acceptance-test-portability plans. No implementation yet.

Fresh current visual baseline P3, not a regression from the height fix: mobile stepper displays two empty32px buttons. Original markup uses `i.fas.fa-chevron-left/right`, but actual templates/styles/scripts do not load Font Awesome or define these classes. Existing local chevron SVG and --icon-arrow-left/right variables are available. Actual PNG: docs/qa/module03-full-2026-10-13-r1/screenshots/progress-detail-ru-390.png; all9 RU/AZ/EN mobile detail images show this. Height/text unclipping SPEC-QA-03 is fixed; glyph absence is a separate root cause.

Checkout /home/ramin/kidsmap, task33-progress, HEAD e4e05cc213b34e2d771ecb854901bfd016d1db51, dirty WORKTREE, active_run NONE.

Only application file: `static/css/pages/specialists.css`.

- Add a16px pseudo-element inside .km-step-arrow using currentColor and the existing local SVG masks via --icon-arrow-left/right. Scope prev/next by existing data-owner-prev/data-owner-next attributes.
- Hide only the unsupported direct .fas children inside these two stepper controls to avoid empty grid cells. No template/JS/font/dependency/localization/domain/ACL/CAS change.
- Keep32px hit area, native buttons, existing translated aria-labels, disabled states, focus styles, navigation handlers and bottom controls.

Proposed CSS:
```css
.km-step-arrow > .fas { display: none; }
.km-step-arrow::before {
  content: "";
  width: 16px;
  height: 16px;
  background: currentColor;
  -webkit-mask: var(--icon-arrow-left) center / contain no-repeat;
  mask: var(--icon-arrow-left) center / contain no-repeat;
}
.km-step-arrow[data-owner-next]::before {
  -webkit-mask-image: var(--icon-arrow-right);
  mask-image: var(--icon-arrow-right);
}
```

Fresh rendered RED already captured in9 detail PNG; record computed icon width/content/mask before patch. GREEN: author+person RU/AZ/EN×360/390/768/1024/1280/1440; screenshot visible glyphs, all5 native transitions and keyboard focus. Native disabled first/last buttons remain, desktop stepper unchanged. Local SVG network200 and no added outside requests. A few shared public/documents views confirm stylesheet scope. No tests mirroring CSS; do not repeat154 backend tests for this CSS-only repair. Retain previous accepted matrices by source provenance; rerun only affected arrow/layout cells.

Evidence under docs/qa/module03-full-2026-10-13-r1 and final snapshot/runtime/PNG manifest. Preserve all prior raw results/foreign files/active_run/stands. Module03 full verdict remains INCOMPLETE until this new finding has acceptance or is explicitly left OPEN. No commit/push/deploy/production/module04 work.

## Execution handoff2026-10-13

Approved in this chat; implementation and applicable verification COMPLETE LOCAL. Authoritative report: docs/qa/module03-full-2026-10-13-r1/REPORT.md. Earlier readiness/pending text describes the planning checkpoint; no commit/push/deploy/production.
