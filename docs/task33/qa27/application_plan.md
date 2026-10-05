# Stage27 independent browser execution plan

Executor `/root/stage26_browser`, canonical browser-qa, stage27 scope; retained runtime handle is not a stage26 rerun. Application edits belong to parent. Own mirror `/root/km27-browser-frozen`, port8787, CLI sessionapplication27, independent QA04 PostgreSQL17 network-none/tmpfs/Unixsocket, clean environment and libpq/network guards, locmem cache/email and isolated media.

Planned actual matrix AZ/RU/EN ×320/360/390/768/1024/1280/1440:

- Calendar current selected day, matching month list, empty calendar, archived calendar.
- Physical/online/past/cancelled/rescheduled public details with typed review, event contact and approved snapshot/state/schema parity.
- Retained owner create/edit and Event admin change/add.

That is13 surfaces/273 contexts before interaction checks. Exact final counts derive from actual executed rows, not this plan. Actual interactions check native mode/month/day URLs, back/forward/reload, quick chips and GET filters, calendar>12 while list paginates12, selected mobile day, all-month desktop, keyboard focus and no overflow, long title, multi-day end-exclusive membership. Actual owner/admin POST save/publication retains stage26 integrity assertions; no copying stage26 PASS counts.

Synthetic future month is next local Baku month, selected15th.18 named matching events across six days, very long unbroken title, additional multi-day14–17 (exclusive), online, cancelled and rescheduled fixtures. Previous-month archive and zero-query fixtures; expected IDs derive persisted service-created events and explicit fixture periods. Approved current EventReview5 with pending edit1 and foreign pending target remain separated. Venue is moved after publication to distinguish captured vs current geography.

Selectors agreed with parent: `[data-events-mode]`, `#events-calendar`, `.events-calendar-grid`, `.events-calendar-day[data-date]` nativehref/aria-current=date, `#events-day-list [data-event-id]`, `#events-filters` details with GET inputs, `[data-events-quick]`. IDs on calendar/list cards are semantic Event identities, not generated occurrences. Parent interface decision: calendar→list mode clears selected date and retains month, yielding equal filtered whole-month membership; mobile selected-day list is a separately labelled subset. Do not demand day preservation in list mode or equate a selected-day subset with full month.

Feature contract: existing `SiteSettings.events_section_enabled` only. ON in disposable local fixture; OFF actual `/events/`410 with no exposed calendar, then restore ON. Source `views.events_landing` returns Gone410; helper `require_events_section_enabled` raises404 for other consumers. Earlier root404 assumption corrected from actual view before full runtime. This existing gate does not fall back to old list and no new global calendar flag is invented. Production/defaultFalse remains untouched. Stage28/production/real integrations/native device/full screen-reader/deploy/commit/push NOT_RUN.

Minimal browserRED authorized separately after root backendRED: frozen current route/calendar/quickchip checks. Full runtime only after root finalREADY. Each run records source SHA, actual received CSS SHA/runtime source paths, raw DOM/screenshots outsideGit, safe aggregates and launcher cleanup. Independent rendered review follows actual screenshots.
