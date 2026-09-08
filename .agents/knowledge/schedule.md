# Schedule — verified LOCAL source, 2026-09-08

Owner: django-reviewer; data transition: database-reviewer. [Current snapshot](current-snapshot.md).

- `models/place.py:Place.SCHEDULE_MODE_CHOICES`: regular, always_open, by_appointment, variable, events. ScheduleDay/ScheduleInterval store structured hours; text schedule remains compatibility input.
- `services/place_schedule.py`: parse_schedule_payload, is_meaningful_schedule, validate_schedule_payload, sync_place_schedule, build_public_schedule_rows, build_public_schedule_summary, build_open_status. Verify names from source before editing.
- `forms.py:PlaceScheduleEditorFormMixin`, admin generated config, owner forms and volunteer proposals consume schedule. `place_readiness._check_schedule` requires meaningful structured days for regular. Owner permanent_place_rules accepts text; public content_quality is separate compatibility visibility.
- `services/seo.py:build_place_seo_payload` handles always_open and structured regular hours. New mode needs explicit schema/translation/open-status decisions; events mode does not itself require an Event row.
- Admin JSON export currently omits structured days and legacy schedule. Do not assert full round-trip preservation.
- Parser's malformed-input fallback and sync's deletion of old days require caller-validation/transaction checks before any data-loss conclusion.

Verification plan: all five modes; transitions regular → other → regular and treatment of retained days/text; empty/closed days, multiple/overlapping intervals, malformed JSON preserving existing data, open status/timezone boundaries, legacy text, owner/admin/volunteer round trips, RU/AZ/EN and catalog/map/detail consistency, SEO hours. `build_open_status` returns `{}` when hours cannot answer the question; this differs from a populated result with `is_open=false`. Unknown/nonregular must not be rendered as confirmed closed.
Targeted labels: catalog.testcases.place_readiness, catalog.testcases.legacy_migrations, catalog.testcases.test_json_roundtrip_audit, catalog.testcases.test_place_json_and_pricing_modes; add actual owner/admin suites selected by callers.
No application tests run in team authoring. New requirements are not assertions that existing paths already agree.
