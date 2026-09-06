# Place phone reveal implementation plan

**Goal:** Public place phones are fetched only after a user action; revealed numbers remain callable on mobile.
**Architecture:** Shared POST endpoint with CSRF, publication filtering, no-store responses and per-client throttling. Shared accessible browser control for cards, details and map popups. Remove phone data from initial HTML, map payloads and SEO.
**Tech stack:** Django, native JavaScript, existing KidsMap styles.
**Spec:** User request in this conversation, 2026-09-06.

- [x] Add failing integration tests in `src/catalog/testcases/phone_reveal.py`: initial pages contain no numbers; POST reveals public contacts; private places, GET, missing CSRF and excessive requests are rejected.
- [x] Add `src/catalog/phone_views.py` and route in `src/catalog/urls.py`; return phones and callable URLs only for published places.
- [x] Update public place templates, SEO and map serializers; retain owner editing and site support contacts.
- [x] Add `static/js/place_phone_reveal.js`: loading, retry, keyboard access, callable links, synchronized controls and map support. Include in base template.
- [x] Run targeted Django tests, JavaScript checks and available browser verification. Review diff for accidental changes.

Verification: 61 Django tests and 3 DOM interaction tests passed. Browser unavailable. Existing map query-count failure also reproduced with the HEAD controller (5 queries versus an expected 4).
