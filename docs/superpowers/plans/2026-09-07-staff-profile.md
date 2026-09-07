# Staff profile implementation plan

**Goal:** A usable local employee profile with editable account data and accurate creator statistics.
**Architecture:** Extend the existing StaffAccessUser admin, Django forms and permissions. Statistics use Place.created_by; live place status and VolunteerPlaceRevision status remain separate. No schema or production changes.
**Stack:** Django 6, server templates, existing admin CSS tokens, Playwright.
**Spec:** User request of 2026-09-07 and attached staff screenshots.

- [x] Add isolated regression tests: creator versus owner count, volunteer role/filter, independent live/revision statistics, filtering/pagination, saved deactivation, forged privilege POST.
- [x] Correct StaffAccessUser queryset and role display; add bounded profile statistics and place listing with permission-aware links. Preserve account flags on edit; privileged fields readonly for non-superusers.
- [x] Add a dedicated staff change template with account/profile/access sections, simple permissions selects under collapsed advanced access, statistics and place filters. Retain Django validation, CSRF and inline management.
- [x] Verify tests and real browser save, errors, permissions, 375/768/1024/1440 layouts, RU/AZ/EN. Update roles documentation and leave local preview running. No commit or deployment.
