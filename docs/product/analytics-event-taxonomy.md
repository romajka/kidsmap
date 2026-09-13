# KidsMap analytics event taxonomy

This document is the versioned contract for local product analytics. Version 2 events use server-derived identity and subjects. GA4 transport is separate from the local event store.

| Event | Subject | Allowed metadata | Source of truth | Metric |
|---|---|---|---|---|
| `organization_view` | Organization ID; unavailable until architecture №33 | none | future organization page render | Views |
| `place_view` | active Place ID | `category` | successful Place detail render | Views |
| `activity_view` | Activity ID; unavailable until architecture №33 | none | future activity page render | Views |
| `favorite_added` | active Place ID | none | committed `PlaceLike` creation | Favorite additions |
| `favorite_removed` | active Place ID | none | committed `PlaceLike` deletion | Favorite removals |
| `phone_click` | active Place ID | none | public phone link | Contact actions |
| `whatsapp_click` | active Place ID | none | public WhatsApp link | Contact actions |
| `website_click` | active Place ID | none | public website link | Contact actions |
| `social_click` | active Place ID | `network` from a server allowlist | public social link | Contact actions |
| `directions_click` | active Place ID | none | public route link | Directions |

The v1 read aliases are `place_open` → `place_view`, `cta_call` → `phone_click`, `cta_whatsapp` → `whatsapp_click`, `cta_instagram` → `social_click`, and `favorite_toggle` with `action=saved|removed` → the matching Favorite event. Historical rows are read in place and are not rewritten.

The v2 envelope contains `schema_version`, one `subject_type` and `subject_id`, `occurred_at`, keyed and versioned `visitor_key_hash` and `session_key_hash`, plus bounded `source`, `page_type`, `language`, `device_class`, `referrer_domain`, `campaign`, and allowlisted `event_meta`. Raw session keys, IP addresses, full user agents, full referrer URLs, client timestamps, client identity, and arbitrary metadata are not stored.

Authenticated visitors are unique by a keyed user hash across sessions. Anonymous visitors are unique by a keyed session hash. Sessions are unique by the keyed session hash. Staff, bots, inactive accounts, and active `AnalyticsActorExclusion` records are excluded from owner metrics. Organization rollups must query raw events and count distinct hashes once; they must not sum Place-level unique totals.

Unresolved product decisions remain: the analytics retention period, the first reliable collection time, the owner dashboard activation date, the public Favorites threshold, the approved public wording/surfaces, and Organization/Activity identifiers from architecture №33. No historical backfill exists for actions that were never collected.
