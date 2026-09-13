# Place rating ranking operations

Bayesian rating sorting remains unavailable until a valid calibration is explicitly activated. The public catalogue falls back to `new` when no valid active calibration exists.

## Proposal and review

Run the proposal against the release environment without writing data:

```powershell
.\.venv\Scripts\python.exe manage.py calibrate_place_rating_ranking --confidence-z 1.96 --margin-stars 0.5 --dry-run
```

Record the aggregate output, review-population size, source cutoff, proposed `C` and `m`, reviewer, and review date in the release record. Output contains aggregate values only.

## Activation

After release approval, use the database ID of the authorized active Superadmin who performs the activation:

```powershell
.\.venv\Scripts\python.exe manage.py calibrate_place_rating_ranking --confidence-z 1.96 --margin-stars 0.5 --activate --actor-user-id <AUTHORIZED_USER_ID>
.\.venv\Scripts\python.exe manage.py audit_place_rating_ranking
```

Activation creates a new immutable version and retires the previous active version in one transaction. It does not modify visible `rating_avg` or `rating_count` values.

## Rollback

Rollback copies an earlier active or retired snapshot into a new version, preserving the original audit history:

```powershell
.\.venv\Scripts\python.exe manage.py rollback_place_rating_ranking --to-version <PREVIOUS_VERSION> --actor-user-id <AUTHORIZED_USER_ID>
.\.venv\Scripts\python.exe manage.py audit_place_rating_ranking
```

Do not edit or delete active and retired calibration rows. If the audit fails, remove rating sorting from the release path until the data or calibration issue is resolved through an approved change.

Review calibration quarterly or when eligible review volume has grown by at least 20% since the active snapshot. The audit command reports both signals and stored Place aggregate drift without exposing review text or user data.

## Local implementation verification

The implementation was verified on local branch `main` at baseline commit `a66842f` in the existing dirty worktree. No production access, deployment, production migration, calibration activation, commit, or push was performed.

- Formula, calibration lifecycle, catalogue ordering, localized option, command, rollback, and aggregate audit tests: 21 passed.
- Final focused regression including existing review-count sorting, rating synchronization, moderation actions, and review cooldown behavior: 36 passed.
- Focused compatibility run: 60 tests executed; 57 passed. The three failures are existing catalogue expectations outside rating ranking: two map tests expect legacy `phone` while the current serializer exposes `has_phone`, and one AZ accessibility test expects a comma-formatted rating label that the current template does not render.
- Django system checks, Python compilation, migration-state check, and diff whitespace check passed.
- Migration `0112_ratingrankingcalibration` applied successfully to an isolated SQLite database.
- Firefox rendered `sort=rating` with the localized selected option and the expected order `4.8 / 20`, `4.3 / 100`, `5.0 / 1`, then unrated. The visible cards retained their arithmetic averages and review counts; the console had no errors or warnings.
- An isolated SQLite fixture with 1,004 public Places returned the ordered IDs in approximately 241 ms and showed one database sort in `QuerySet.explain()`. This is a local regression signal, not a production PostgreSQL latency benchmark.
