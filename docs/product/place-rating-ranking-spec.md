# KidsMap Place Rating Ranking Contract

## Purpose

KidsMap ranks Places by a confidence-adjusted rating when a user explicitly selects rating sorting. The rank must use both the visible average and the number of trustworthy reviews, so one accidental five-star review does not receive the same confidence as a long review history.

The public card continues to show the real arithmetic average and the real review count. The adjusted value is an internal ordering score only.

## First release scope

This contract applies to the public Place catalogue and the `sort=rating` query value.

It does not change:

- the visible `Place.rating_avg` or `Place.rating_count` values;
- the minimum-rating filter, which continues to compare the visible arithmetic average;
- `reviews_desc`, which remains a separate sort by review count;
- homepage recommendations or any future Popularity score;
- Event or Specialist ranking.

## Eligible evidence

Only a `PlaceReview` accepted by `catalog.services.content_quality.public_review_queryset()` contributes to ranking. Therefore a review must be approved, have approved moderation status, contain a rating from 1 through 5 and pass the existing public junk-content rule.

Calibration uses only reviews attached to Places visible through `public_place_queryset()` at the calibration snapshot. Pending, rejected, hidden, invalid and non-public-Place reviews do not influence `C`, `m`, `R` or `v`.

`Place.rating_avg` and `Place.rating_count` remain the stored aggregates used for each Place. Existing review save, delete and moderation flows must keep those aggregates synchronized from the same public-review predicate.

## Bayesian weighted score

For every Place with at least one eligible review:

```text
weighted_rating = (v * R + m * C) / (v + m)
```

- `R` is the Place's real arithmetic average, stored as `rating_avg`.
- `v` is the Place's eligible review count, stored as `rating_count`.
- `C` is the review-weighted global mean from the active calibration snapshot.
- `m` is the active calibration's prior strength, expressed as a review count.

The formula pulls small samples toward `C`. As `v` grows, the score approaches the Place's real average. Review count does not become a separate popularity bonus.

## Calibration of C and m

The calibration job derives both values from eligible review data and stores the inputs and result as an immutable version.

`C` is calculated as:

```text
C = sum(all eligible rating values) / eligible review count
```

This is a review-weighted mean, not an unweighted mean of Place averages.

`m` is the sample size required to estimate a rating mean with 95% confidence and a target half-width of 0.5 stars, using the observed population standard deviation `s`:

```text
m = max(1, ceil((1.96 * s / 0.5) ^ 2))
```

The confidence level and half-width are stored with the calibration version. A later product decision may change them only by creating and activating a new version; it must not rewrite historical calibration rows.

A proposal is invalid when it has fewer than 30 eligible reviews, fewer than 10 rated public Places, a mean outside 1 through 5, a non-finite variance or a non-positive prior strength. Invalid data must not produce an active calibration or a guessed fallback.

## Calibration lifecycle

Calibration versions have `draft`, `active` and `retired` states. At most one version is active.

1. A management command calculates a proposal and prints aggregate, non-personal diagnostics.
2. A dry run does not write a calibration.
3. Explicit activation stores the version, derivation parameters, population counts, source cutoff and actor.
4. Activating a new version retires the previous active version in one transaction.
5. Active and retired versions are immutable through the application and admin.

Recalibration is deliberate rather than automatic. It should be reviewed quarterly or after the eligible-review population grows by at least 20%, whichever comes first. A new review immediately changes its Place's `R` and `v`; it does not silently change global `C` and `m`.

If no valid calibration is active, the catalogue does not offer rating sorting and a supplied `sort=rating` value normalizes to the default `new` order. KidsMap must never fall back to raw average ordering while presenting the request as confidence-adjusted rating sorting.

## Ordering contract

For `sort=rating`, the catalogue orders Places by:

1. Places with at least one eligible review before unrated Places.
2. Weighted rating descending.
3. Eligible review count descending.
4. Real average descending.
5. Creation time descending.
6. Primary key descending.

The final keys make pagination deterministic. The count and average are tie-breakers only; they do not alter the Bayesian formula.

Places with no eligible reviews have no weighted rating. They appear after all rated Places and use creation time and primary key for stable ordering.

Places with one or two reviews receive no special hardcoded penalty. Their small `v` makes the active prior dominate naturally.

## Example

With a calibration of `C = 4.0` and `m = 15`:

```text
5.0 from 1 review   -> (1 * 5.0 + 15 * 4.0) / 16  = 4.0625
4.3 from 100 reviews -> (100 * 4.3 + 15 * 4.0) / 115 = 4.2609
4.8 from 20 reviews  -> (20 * 4.8 + 15 * 4.0) / 35  = 4.4571
```

This example shows both intended effects: a one-review maximum is strongly shrunk, while a well-supported materially better average can still rank first. The real card labels remain `5.0 · 1 review`, `4.3 · 100 reviews` and `4.8 · 20 reviews`.

## Popularity boundary

Rating and Popularity are separate products.

The rating score may use only review ratings and their sample size. It must not use Favorites, Place likes, views, contact reveals, website clicks, route builds, recency boosts or paid placement.

If a public Popularity sort is introduced, it needs its own named service, documented inputs, abuse controls and tests. `DjangoPlaceRepository.top_popular()` and the curated homepage order remain outside this rating change.

The existing Azerbaijani label for `reviews_desc` must describe review count rather than generic popularity, matching the Russian and English meaning.

## Privacy, audit and observability

Calibration diagnostics contain aggregate counts, mean, variance, `C`, `m` and timestamps only. They must not contain review text, user identity, session keys or individual ratings.

Activation records who activated the calibration and when. Admin access is read-only for active and retired rows. Operational checks report:

- whether exactly one active calibration exists;
- whether current `rating_avg` and `rating_count` match eligible review aggregates;
- active calibration age and review-population growth since its snapshot;
- invalid or non-finite calibration values.

## Acceptance criteria

- The catalogue exposes a localized `sort=rating` option only with a valid active calibration.
- With the example calibration, `4.3 / 100` ranks above `5.0 / 1`.
- A well-supported higher average can rank above a lower average, proving that the implementation is not count-only.
- Unrated Places follow all rated Places.
- Pending, rejected and junk reviews affect neither Place aggregates nor calibration.
- Cards, map payloads and structured data continue to expose only the real average and count.
- `reviews_desc` retains its existing count-first behavior.
- Homepage recommendation/popularity behavior is unchanged.
- Ordering is deterministic across pagination.
