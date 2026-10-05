# Event Calendar Implementation Plan

**Goal:** implement only Task33 stage27: public list/calendar, retained filters and accessible desktop month/mobile day views using approved admin-public-03-r1.

**Architecture:** existing Event query is authoritative. A presentation-only calendar service groups real approved Event IDs over Baku half-open days; no generated occurrences or new schema. Native same-path GET links/forms carry canonical filter state through back/forward/reload; only list paginates12.

**Tech Stack:** Django6/PostgreSQL17, existing templates/CSS tokens/Material Symbols/gettext; no new framework or font.

**Spec:** ../prompts/27.md, decisionsD09/D10, accepted design/public/events.html and shared03 prototype. Direct user “дальше” continues with the next27 only;28/production/commit/push/merge/deploy remain outside authorization.

## Snapshot and ownership

Entry342/342 dirty files + tracked binary patch preserved, dependency26 source158 SHA MATCH. HEAD015d031d8eb17114bd860159dde805b38df3c13c on task33-progress. Root frontend-reviewer owns public template/includes/events_landing.css, scoped locale and final reports/journal. Bounded django-reviewer implementation owns new services/event_calendar.py, only build_events_landing_context, test_task33_event_calendar.py and27-backend.md. Independent browser-qa owns qa27/application_* and27-browser*; independent integration reviewer follows frozen implementation, owning its own tests/report only. All preserve incoming work.

## Task1 — server presentation contract

- [x] Write meaningful calendar/full HTTP tests; execute isolated RED before application implementation. Fixtures:14 approved same-month records, a midnight ending record, an overnight multi-day record, past cancelled/online and rejected/private records. Assert month contains all14 despite list12; selected-day hand-derived IDs, Baku midnight exclusive edge, literal leap-month days, invalid/mismatched month/date empty.
- [x] Implement `build_event_calendar(params, events, now=None, path='') -> dict`: valid/month/month_label/selected_date/weeks/days/selected_events/prev_url/next_url/list_url/calendar_url/today_url/quick_urls. Each day: iso/date/in_month/selected/today/events/count/url. Group actual Event objects intersecting [Baku day start,next midnight); bound generation to a single real month. Reject malformed/year overflow and explicit selected day outside month. No database writes or inferred organizer.
- [x] Add context `event_calendar`, `events_mode`, `events_mode_urls`, `events_quick_urls`, `event_format_choices`; retain existing events/calendar_events/page_obj compatibility. Calendar query stays unpaginated; list remains paginator12. URL whitelist retains q/category/age/format/district/free/sort, mode and valid periods. Day/month/mode links omit page. Quick date chips clear conflicting period keys and preserve other filters; free chip retains date/mode.
- [x] GREEN in isolated QA04, then scoped source review. Feature gate remains existing fail-closed SiteSettings.events_section_enabled; enable only disposable local fixture, no global/default/env/production setting change.

## Task2 — approved UI

- [x] Capture current real browser RED missing calendar/mode and dropping quick-chip filters before templates change.
- [x] Update `catalog/events_landing.html`, new `catalog/includes/event_calendar.html` and `event_listing_card.html`, bounded `static/css/events_landing.css`. Mode links use server URLs, filter GET form uses current selected values; desktop month has weekday headings and real Event links, mobile day selector and selected-day list. Semantic native links/buttons/labels, visible focus, aria-current, zero/error state and long-title wrap; no clipped interactive content. Calendar does not render list pagination.
- [x] Shared card shows honest past/cancelled/rescheduled state, Baku interval, online/no geography or immutable address, external Event contact and links to actual typed reviews. Missing price stays unknown; no quota or venue rating sorting. Owner/admin organizer/venue/online authority already implemented26 is preserved and verified through retained integration flows.
- [x] AZ/RU/EN labels preserve existing source provenance; no frontend copy of backend format enum. Public form submits bounded period values; mode/month/day URLs preserve search/filter state. Local browser tests cover keyboard/day selection, filter chips, back/forward/reload and empty-month cases.

## Task3 — independent acceptance and final snapshot

- [x] Fresh Task33 regression plus independent HTTP/calendar negative review, exact commands/exits/discovery counts/cleanup and source freezes. Existing full application NOT_GREEN remains explicit; no whole-application claim.
- [x] Actual Chromium AZ/RU/EN×320/360/390/768/1024/1280/1440: list/calendar/selectedday/zero/archive and retained owner/admin. Month>12, multi-day boundary, online/cancel/reschedule, truthful review/contact, keyboard/history/reload, console/network/static and overflow. Source inspection is not rendered evidence; external integrations stubbed and NOT_RUN.
- [x] Review every27 acceptance criterion, preserve342 entry files, record source SHA+dirty inventory without report self-hash; update27 report, README and implementation-status. DONE/active_run NONE only after all executors/checks complete.28 and production require separate instruction.
