# Bayesian Place Rating Sorting Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a public Place rating sort that accounts for both average rating and review confidence while preserving real user-facing rating values and keeping Popularity independent.

**Architecture:** Store immutable, versioned calibration snapshots for the global prior. Derive `C` and `m` from the same public approved-review population that feeds `Place.rating_avg` and `Place.rating_count`. Apply the Bayesian formula as a queryset annotation only when `sort=rating`; do not persist or serialize the internal score. Keep `reviews_desc`, homepage recommendations and future Popularity scoring on separate code paths.

**Tech Stack:** Django models and migrations, Django ORM expressions, PostgreSQL-compatible constraints, server-rendered templates, Django `TestCase`, management commands.

**Spec:** `docs/product/place-rating-ranking-spec.md`

## Global Constraints

- The score is `WR = (v * R + m * C) / (v + m)` and may use only eligible Place-review ratings.
- `C` and `m` come from a versioned calibration; do not insert arbitrary production constants in application code or migrations.
- Public cards, map payloads, filters and schema continue to use real `rating_avg` and `rating_count`.
- `reviews_desc` remains review-count sorting. Do not add Favorites, likes, views, contact actions, route actions or paid placement to rating sorting.
- A missing or invalid active calibration disables rating sorting and normalizes `sort=rating` to `new`; it never falls back to raw average sorting.
- New copy supports AZ/RU/EN and the selected sort survives existing normalized query and pagination behavior.
- Tests run only with `DJANGO_TESTING=1` and isolated database/cache/media.
- Production remains read-only during this plan; do not activate calibration, deploy, migrate production, commit or push.

---

### Task 1: Lock the ranking math and edge cases with unit tests

**Files:**

- Create: `src/catalog/services/rating_ranking.py`
- Create: `src/catalog/testcases/test_rating_ranking.py`

**Interfaces:**

- Produces: `RatingCalibrationValues` immutable value object.
- Produces: `calculate_weighted_rating(*, rating_avg: float, rating_count: int, prior_mean: float, prior_weight: float) -> float | None`.
- Produces: `derive_rating_calibration(*, rating_count: int, rating_sum: int, rating_sum_squares: int, rated_place_count: int, confidence_z: float, margin_stars: float) -> RatingCalibrationValues`.

- [ ] **Step 1: Write failing formula tests**

```python
def test_small_perfect_sample_is_below_large_stable_sample(self):
    calibration = RatingCalibrationValues(prior_mean=4.0, prior_weight=15.0)
    one_review = calculate_weighted_rating(rating_avg=5.0, rating_count=1, calibration=calibration)
    stable_rating = calculate_weighted_rating(rating_avg=4.3, rating_count=100, calibration=calibration)
    self.assertLess(one_review, stable_rating)

def test_unrated_place_has_no_internal_score(self):
    calibration = RatingCalibrationValues(prior_mean=4.0, prior_weight=15.0)
    self.assertIsNone(calculate_weighted_rating(rating_avg=0.0, rating_count=0, calibration=calibration))
```

Also cover one and two reviews, a well-supported higher average, exact formula values and invalid negative/non-finite inputs.

- [ ] **Step 2: Run the focused test and confirm the missing-service failure**

```powershell
$env:DJANGO_TESTING='1'
.\.venv\Scripts\python.exe manage.py test catalog.testcases.test_rating_ranking --noinput
```

Expected: FAIL because `catalog.services.rating_ranking` does not exist.

- [ ] **Step 3: Implement the pure formula**

Return `None` for `rating_count == 0`. Validate `1 <= rating_avg <= 5`, `1 <= prior_mean <= 5`, positive count and positive finite prior weight. Use `math.fsum` or equivalent stable arithmetic and keep display rounding outside this service.

- [ ] **Step 4: Implement deterministic calibration derivation**

Derive the population mean and variance from count, sum and sum of squares:

```python
prior_mean = rating_sum / rating_count
variance = max(0.0, rating_sum_squares / rating_count - prior_mean ** 2)
standard_deviation = math.sqrt(variance)
prior_weight = max(1, math.ceil((confidence_z * standard_deviation / margin_stars) ** 2))
```

Reject fewer than 30 eligible reviews, fewer than 10 rated public Places, non-positive confidence/margin and non-finite results. Store `confidence_z=1.96` and `margin_stars=0.5` as explicit policy inputs in callers, not hidden inside the formula.

- [ ] **Step 5: Run the unit tests**

```powershell
$env:DJANGO_TESTING='1'
.\.venv\Scripts\python.exe manage.py test catalog.testcases.test_rating_ranking --noinput
```

Expected: all formula, calibration and validation tests pass.

### Task 2: Add immutable calibration versions and activation rules

**Files:**

- Create: `src/catalog/models/rating_ranking.py`
- Modify: `src/catalog/models/__init__.py`
- Create: `src/catalog/migrations/0105_rating_ranking_calibration.py` (use the next free migration number after other approved plans)
- Create: `src/catalog/testcases/test_rating_ranking_models.py`

**Interfaces:**

- Produces: `RatingRankingCalibration` with `DRAFT`, `ACTIVE` and `RETIRED` states.
- Produces: `activate_rating_calibration(*, calibration, actor, now=None) -> RatingRankingCalibration` in `catalog.services.rating_ranking`.

- [ ] **Step 1: Write failing model-constraint tests**

Cover unique version, one active row, `1 <= prior_mean <= 5`, positive prior weight, positive population counts, valid confidence/margin, required activation actor/time and rejection of direct edits to active or retired rows.

- [ ] **Step 2: Implement the calibration model**

```python
class RatingRankingCalibration(models.Model):
    version = models.PositiveIntegerField(unique=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT, db_index=True)
    prior_mean = models.DecimalField(max_digits=7, decimal_places=5)
    prior_weight = models.DecimalField(max_digits=9, decimal_places=4)
    population_review_count = models.PositiveIntegerField()
    population_place_count = models.PositiveIntegerField()
    population_rating_sum = models.PositiveBigIntegerField()
    population_rating_sum_squares = models.PositiveBigIntegerField()
    population_standard_deviation = models.DecimalField(max_digits=7, decimal_places=5)
    confidence_z = models.DecimalField(max_digits=6, decimal_places=4)
    margin_stars = models.DecimalField(max_digits=5, decimal_places=3)
    source_cutoff = models.DateTimeField()
    calculated_at = models.DateTimeField(auto_now_add=True)
    activated_at = models.DateTimeField(null=True, blank=True)
    activated_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
```

Add database check constraints and a conditional unique constraint for the active status. Default ordering is newest version first.

- [ ] **Step 3: Implement transactional activation**

Lock all active/draft calibration rows, revalidate the candidate, retire the old active version and activate the candidate in one transaction. Reject candidates whose stored inputs no longer reproduce their `C` and `m`. Model admin exposes diagnostics but makes active and retired rows read-only.

- [ ] **Step 4: Generate and validate the migration**

```powershell
$env:DJANGO_TESTING='1'
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe manage.py test catalog.testcases.test_rating_ranking_models --noinput
```

Expected: migration state matches models and all activation/immutability tests pass.

### Task 3: Build a safe calibration command from public review evidence

**Files:**

- Create: `src/catalog/management/commands/calibrate_place_rating_ranking.py`
- Modify: `src/catalog/services/rating_ranking.py`
- Create: `src/catalog/testcases/test_rating_ranking_command.py`

**Interfaces:**

- Produces: `build_place_rating_calibration_proposal(*, confidence_z: float, margin_stars: float, source_cutoff=None) -> RatingRankingCalibration`.
- Produces CLI: `manage.py calibrate_place_rating_ranking --confidence-z 1.96 --margin-stars 0.5 --dry-run`.
- Produces CLI: `manage.py calibrate_place_rating_ranking --confidence-z 1.96 --margin-stars 0.5 --activate --actor-user-id 42`, where `42` is an isolated-test fixture user; the release runbook records the real authorized actor ID.

- [ ] **Step 1: Write a failing eligibility-population test**

Create public approved, pending, rejected, junk-content, invalid and non-public-Place reviews. Assert that only reviews passing `public_review_queryset()` and belonging to `public_place_queryset()` contribute to count, sum, sum of squares and distinct rated Place count.

- [ ] **Step 2: Write failing dry-run and activation tests**

Assert that dry-run creates no rows, output contains aggregate values only, activation requires an authorized staff actor, version numbers increase monotonically and a second activation retires the first version.

- [ ] **Step 3: Implement aggregate collection**

Use database `Count`, `Sum`, `Max` and `Count('place_id', distinct=True)` expressions. Reuse the exact public review and Place predicates from `content_quality.py`. Do not read review text or user/session fields. Calculate `rating_sum_squares` with a typed ORM expression that works on PostgreSQL and the isolated SQLite test database.

- [ ] **Step 4: Implement command modes**

`--dry-run` prints proposed version, aggregate population, `C`, standard deviation and `m` without writing. `--activate` writes and activates only after validation and explicit actor authorization. The two modes are mutually exclusive; an invocation without either exits with a usage error.

- [ ] **Step 5: Run command tests**

```powershell
$env:DJANGO_TESTING='1'
.\.venv\Scripts\python.exe manage.py test catalog.testcases.test_rating_ranking_command --noinput
```

Expected: eligibility, privacy, validation, dry-run and activation tests pass.

### Task 4: Apply Bayesian ordering to the public Place catalogue

**Files:**

- Modify: `src/catalog/services/rating_ranking.py`
- Modify: `src/catalog/services/filtering.py:8-67, 227-236`
- Modify: `src/catalog/controllers/place_controller.py:59-103`
- Modify: `src/catalog/testcases/public.py:2137-2155`
- Modify: `src/catalog/testcases/test_rating_ranking.py`

**Interfaces:**

- Produces: `get_active_rating_calibration() -> RatingRankingCalibration | None`.
- Produces: `apply_weighted_rating_ordering(queryset, calibration) -> QuerySet`.
- Produces: `rating_sort_available` in public catalogue context.
- Consumes: `Place.rating_avg` and `Place.rating_count` maintained by `Place.refresh_rating_stats()`.

- [ ] **Step 1: Write failing catalogue ordering tests**

Activate a fixture calibration with `C=4.0`, `m=15`, then assert:

```python
response = self.client.get(reverse('place_list'), {'sort': 'rating'})
ordered_names = [place.name for place in response.context['places']]
self.assertLess(ordered_names.index('Stable 4.3'), ordered_names.index('Single 5.0'))
self.assertLess(ordered_names.index('Supported 4.8'), ordered_names.index('Stable 4.3'))
self.assertLess(ordered_names.index('Single 5.0'), ordered_names.index('Unrated'))
```

Add deterministic tie/pagination coverage. Assert `reviews_desc` still orders by count first.

- [ ] **Step 2: Write a failing unavailable-calibration test**

With no active calibration, request `sort=rating`. Assert `selected['sort'] == 'new'`, newest ordering is used and `rating_sort_available` is false.

- [ ] **Step 3: Implement the ORM annotation**

Use typed `Value`, `F`, `ExpressionWrapper` and `Case` expressions:

```python
score = (F('rating_count') * F('rating_avg') + Value(m * C)) / (F('rating_count') + Value(m))
```

Annotate a rated/unrated flag and the internal score only for `rating_count__gt=0`. Order by rated flag, score, count, real average, creation time and primary key as defined by the product contract. Query the active calibration only for `sort=rating`; do not add per-Place queries.

- [ ] **Step 4: Normalize rating sort availability**

Let `PlaceListFilters.apply()` change unavailable `rating` to `new` before `selected()` and normalized URLs are built. Expose availability separately so the template can hide the option without guessing from query parameters.

- [ ] **Step 5: Run catalogue tests**

```powershell
$env:DJANGO_TESTING='1'
.\.venv\Scripts\python.exe manage.py test `
  catalog.testcases.test_rating_ranking `
  catalog.testcases.public.TestCatalogEnhancements.test_catalog_can_sort_places_by_review_count --noinput
```

Expected: Bayesian, unavailable, no-review, deterministic pagination and legacy count-sort tests pass.

### Task 5: Add clear localized UI without exposing the internal score

**Files:**

- Modify: `src/catalog/templates/catalog/place_list.html:626-633, 763-768`
- Modify: `src/catalog/testcases/public.py`
- Modify: `locale/az/LC_MESSAGES/django.po` if translation extraction introduces new gettext strings
- Modify: `locale/ru/LC_MESSAGES/django.po` if translation extraction introduces new gettext strings
- Modify: `locale/en/LC_MESSAGES/django.po` if translation extraction introduces new gettext strings

**Interfaces:**

- Consumes: `rating_sort_available` and `selected.sort`.
- Produces: AZ `Reytinq üzrə`, RU `По рейтингу`, EN `Highest rated`.
- Corrects the AZ `reviews_desc` label to mean “most reviewed” rather than generic popularity.

- [ ] **Step 1: Write failing response tests for the option and selected state**

Assert the option is present in all three languages only with an active calibration, selected for `sort=rating`, absent without calibration and preserved in pagination/filter query strings.

- [ ] **Step 2: Render the new option**

Add the conditional `rating` option beside existing sort choices. Keep `reviews_desc` as a separate option with review-count wording in every language.

- [ ] **Step 3: Prove the adjusted score stays internal**

With a Place whose real rating is `5.0 / 1` and weighted score is `4.0625`, assert the HTML and map payload show `5.0` and `1` and do not contain `4.0625`, `weighted_rating` or `rating_rank_score`. Keep the existing map serializer fields unchanged.

- [ ] **Step 4: Run public rendering tests**

```powershell
$env:DJANGO_TESTING='1'
.\.venv\Scripts\python.exe manage.py test catalog.testcases.public.TestCatalogEnhancements catalog.testcases.test_rating_ranking --noinput
```

Expected: localized UI, real-rating display and query preservation tests pass.

### Task 6: Add audit diagnostics and regression verification

**Files:**

- Modify: `src/catalog/management/commands/recalculate_ratings.py`
- Create: `src/catalog/management/commands/audit_place_rating_ranking.py`
- Create: `src/catalog/testcases/test_rating_ranking_audit.py`
- Modify: `docs/product/place-rating-ranking-spec.md` only if implemented behavior requires an approved contract amendment

**Interfaces:**

- Produces CLI: `manage.py audit_place_rating_ranking` with aggregate-only output and non-zero exit on integrity failures.
- Consumes: `public_review_queryset()`, active calibration and stored Place rating aggregates.

- [ ] **Step 1: Write failing aggregate-integrity tests**

Create a deliberately stale Place aggregate and assert the audit reports the mismatch count without review/user data. Cover no active calibration, multiple-active defense, invalid values, calibration age and at least 20% eligible-population growth.

- [ ] **Step 2: Implement read-only audit diagnostics**

The command reports booleans and aggregate counts only. It performs no repairs. Keep `recalculate_ratings` as an explicit repair command and make it reuse the same eligible-review predicate so audit and repair cannot disagree.

- [ ] **Step 3: Check query behavior**

Use `assertNumQueries` around catalogue rendering to prove rating sorting adds one calibration query and no per-Place queries. Capture `QuerySet.explain()` against a production-sized isolated fixture and compare rating ordering with the current `reviews_desc` baseline. If computed sorting is too slow for the approved response-time budget, amend the architecture to a versioned materialized score before production activation; do not add an unversioned cached field.

- [ ] **Step 4: Run the focused regression suite**

```powershell
$env:DJANGO_TESTING='1'
.\.venv\Scripts\python.exe manage.py test `
  catalog.testcases.test_rating_ranking `
  catalog.testcases.test_rating_ranking_models `
  catalog.testcases.test_rating_ranking_command `
  catalog.testcases.test_rating_ranking_audit `
  catalog.testcases.public.TestCatalogEnhancements `
  catalog.testcases.admin.TestReviewRatingSyncAndAdminBulkActions `
  catalog.testcases.test_place_review_cooldown --noinput
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
```

Expected: all focused tests pass and migration state is clean.

- [ ] **Step 5: Prepare a production activation runbook without executing it**

Record the exact dry-run command, aggregate proposal, authorized reviewer, activation command, audit command and rollback to the previous calibration version. Production migration, activation and deployment require the separately approved release procedure and are outside this implementation plan.
