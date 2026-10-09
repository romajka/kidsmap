# Remove optional listing verification badges

User authorizes removing Verified markers and ability to assign them across places/specialists and related public listing interfaces. Preserve all concurrent dirty work. No production/commit/push.

1. RED tests: legacy verified records render no public badge/filter; admin forms/actions no longer expose assignment; publication remains available.
2. Remove place/specialist public badges, filters and verification marketing claims. Retire verified query filtering and query whitelist. Keep email/person ownership confirmation, publication readiness, review/document moderation and internal pricing-source approval contracts.
3. Remove Place/Specialist admin optional is_verified controls, bulk actions, columns/filter/stats and old state badges; exclude field from admin forms so forged POST cannot set it. Retain legacy DB columns/data for compatibility; migration0136 only makes the retained flags noneditable; no data deletion. Do not offer the badge through proxies.
4. Targeted isolated PostgreSQL tests, rendered public/admin checks including legacy True records, restart owned local preview preserving synthetic data. Report exact tested scope and manual inspection links.

Execution complete locally. Final isolated74/74 PASS including updated explicit legacy contracts; rendered badge/admin controls28 contexts PASS. Migration0136 state matches models, legacy data retained. Evidence: docs/qa/retired-verification-badges-2026-10-05.md. Full suite/production NOT_RUN; visual acceptance awaiting_user_review.
