# Dashboard native visual followup

User authorized newly found related defects. Native RED:60observations,0errors from current real DOM/computed styles and saved PNG. Original disabled report functional state now passes; UI followup fixes low-contrast active controls/status, a280px notice caused by reusing chart-empty, and actual KPI label/icon clipping at360 and1440. These are not hidden or dismissed as browser harness failures.

Exactly two files: templates/admin/catalog/site_analytics.html reuses existing compact km-ga4-notice and km-ga4-notice__text instead of chart-empty, keeping role=status/retry and all text; bumps CSS version. static/admin/css/kidsmap_statistics.css changes scoped brand green to existing KidsMap#136F38, muted text to readable existing gray,3-column minmax grid matching actual3cards,1column≤480, header gap/min-width/wrapping. No global public UI/JS/schema/data change. Existing stats CSS is used only by this dashboard.

Acceptance: actual18cells/3languages/six widths in each disabled/filled/empty/error/partial state; contrasts≥4.5, notice≤120px, content geometry without clipping, no document overflow; keyboard period/retry/focus and old targeted backend regressions unchanged. No runtime style injection. Preserve initial failed outputs and screenshots.
