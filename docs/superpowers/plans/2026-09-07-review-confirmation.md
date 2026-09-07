# Review confirmation implementation plan

**Goal:** Make successful review submission and pending moderation visible in RU/AZ/EN.
**Authorization:** User explicitly requests implementation; limited to review submission feedback, no moderation strategy changes, deployment or commits.
**Architecture:** Shared existing flash/toast styles, shared progressively enhanced submission script. JSON for AJAX, Django messages + redirect otherwise. Persistent confirmation adjacent to form; retain input on AJAX errors; lock duplicate requests.
**Spec:** User request in this session, 2026-09-07.

- [x] Add regression tests in `src/catalog/testcases/test_review_confirmation.py`: POST redirect renders confirmation, AJAX returns success only after save, pending reviews excluded, duplicate updates same row, validation errors never success, RU/AZ/EN.
- [x] Run isolated SQLite tests with DJANGO_TESTING=1 and no inherited credentials; first reproduce missing confirmation.
- [x] Update `src/catalog/views.py` with shared review response helper, JSON success/error and tagged POST messages; preserve moderation services.
- [x] Add shared notification include and `static/js/review_submission.js`; connect three review forms and existing toast. Keep form text on errors; reset/hide form only on confirmed success. Prevent duplicate in-flight submissions.
- [x] Add gettext RU/AZ/EN copy; compile catalogues. Use existing flash/toast CSS without modifying pre-existing CSS changes.
- [x] Run Django regression tests and real browser checks with isolated synthetic fixtures, mobile/desktop, three languages, validation/network/server errors and console checks.

**Result:** See `docs/REVIEW_CONFIRMATION_2026-09-07.md`: 28 Django tests and Chromium checks passed. Also removed transient approved first save without changing moderation strategy.

## Follow-up: заполненный текст, но нет оценки

User authorizes review-case audit and fixes on 2026-09-07. Scope: reproduce the exact missing-rating UI, make readiness truthful and accessible, check typing/rating order, short/blank/long text, keyboard, prompt chips, pending requests, retries, all three review endpoints and locales. Preserve manual moderation and unrelated header work. Add failing browser regression first, then targeted UI fixes, rerun Django/browser checks and refresh local workers for user testing.

Follow-up completed: regression reproduced, readiness/labels/retry/chip bounds fixed, unsupported anonymity control removed without backend policy changes. 38 Django tests and expanded Chromium suite passed; actual localhost login and missing-rating scenario checked. Detailed evidence is in the report's follow-up section.
