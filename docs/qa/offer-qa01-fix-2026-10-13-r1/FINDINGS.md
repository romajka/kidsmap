# Findings — scoped OFFER-QA-01 repair

| ID | Current status | Evidence / limit |
|---|---|---|
| OFFER-QA-01 | CLOSED LOCAL in executed scope | RED→GREEN;38 unique target methods; owner→reviewer→public18 cells; READ ONLY18 archived groups/history/projection; native full nested admin import and public Place detail. |
| OFFER-QA-02–08 | OPEN / fresh recheck pending | Historical7 IDs; not implemented or accepted here. |
| OFFER-QA-09 | OPEN, P2, confirmed pre-existing baseline | A name-only candidate for a Place priced by groups has no approve button despite valid published tariffs. Current native UI plus exact pre-patch service source reproduction. Separate scope, not patched. |

## OFFER-QA-09 — Partial review omits existing grouped pricing

Environment: own LOCAL fictional PostgreSQL/browser, current WORKTREE. Not production. Root sequential evidence, no independent execution claimed.

Native reproduction: admin imports a complete nested tree removing a group, saves and approves successfully. Then imports only name_en with correct schema/source version. Hidden nested tree stays unchanged, candidate saves, public remaining group stays visible. `/admin/volunteer/review/<own-place>/` shows a false price readiness requirement and no approve button. Proposed name remains in candidate; live grouped tariff20 exists. Returning that own candidate through the native UI retains live20 and archived removal history.

Cause: unchanged `src/catalog/services/volunteer_places.py:review_form` builds trusted review form data from scalar/direct-pricing snapshot plus partial payload; missing nested_pricing is not filled from the current complete live tree. `src/catalog/services/place_readiness.py` reads nested plans only from cleaned_data, therefore misses the existing group tariff. Do not weaken pricing validation or replace the canonical business contract.

[Native state](admin-inspect.result.json), [PNG](screenshots/partial-import-review-price-blocked.png), [raw native attempt](admin-browser.result.attempt1791890498.json), [baseline proof](partial-baseline.json), [baseline exact command](partial-prepatch-baseline-corrected.command.json). Baseline probe loads pricing_plans.py/publication.py directly from HEAD only after hashes match both pre-repair entry files; runs in disposable test DB. Both pre-patch source services reproduce the same missing price requirement. Other relevant readiness/review sources are preserved by hash. First diagnostic used field=price instead of actual code=price / field=pricing_plans; corrected probe and raw failure retained. Existing application/test assertions unchanged.

Confidence HIGH; limited blocked moderation workflow, P2. Future ownership: Django review adapter, targeted regression, native owner/admin partial changes; no fix approved. No matching historical ID found in the bounded guide/module13 text search; broader cross-module dedup UNKNOWN. Keep this finding separate from OFFER-QA-01 closure and outside historical73/76 queue counts.
