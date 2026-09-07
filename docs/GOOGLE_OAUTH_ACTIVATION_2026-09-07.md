# Google OAuth activation — 7 September 2026

## Scope and authorization

The user explicitly resumed Google Login deployment after supplying the server-side
Client Secret and confirming email ownership and full administrator access for
the two selected accounts. The earlier audit-only pause does not describe this
newly authorized deployment. No Git commit/push or unrelated feature deployment.

Before this release, the confirmed administrator email assignment was applied in
one transaction. Four duplicate emails were cleared, the friend's selected account
received full administrator rights, and passwords and all user foreign-key counts
were preserved. Fresh read-only verification found zero duplicate email groups.

## Release and recovery

- Previous live image: `sha256:47e941626be808071d0a48ea06283f4aae959f71c15a31d37597e0c0cf340d1c`.
- Prepared OAuth image: `kidsmap-web:google-20260906`,
  `sha256:3f44ada8b182bd15cd03f03b65852fa67c2bf25c837dd3276bfebfe7bda9d424`.
- Prepared source: `/opt/kidsmap-releases/google-20260906`.
- Application/static/source comparison between the two images found exactly the
  14 OAuth integration files listed in the server-side release manifest. All 14
  prepared source files match the image after newline normalization.
- Effective Compose environment differs from the previous live web container only
  in `GOOGLE_OAUTH_CLIENT_ID` and `GOOGLE_OAUTH_CLIENT_SECRET`. Values were not logged.
- The image does not contain `.env`. A `.env#` file contains only a four-byte
  comment, with no assignments or secret material; no rebuild was needed.
- Restricted server backup:
  `/opt/backups/kidsmap-google-activation-20260907T050750Z`.
  Contains a fresh database archive, configuration, previous container metadata,
  static files and scoped source backups. Secret-bearing artifacts remain on the
  server; none are copied into this repository.
- The database archive was successfully restored into a disposable PostgreSQL 17
  container on an internal network. Production volumes/credentials were not used
  by that rehearsal. Copied user data was not printed or exported from the server.
- Rollback uses the previous web image, saved Compose/source and preserved static
  assets. Additive OAuth tables/index can remain: the previous image passed
  `migrate --check` and system checks against the rehearsed new schema. A full DB
  restore over concurrent production activity is not the rollback mechanism.

## Verification before activation

The existing server runner was copied into the new backup directory and executed:

```text
python3 /opt/backups/kidsmap-google-activation-20260907T050750Z/run_pg.py
```

It ran `check`, `makemigrations --check --dry-run`, and the Google/auth/access/reset
suites, including the three additional existing-account/reset/locale/proxy checks:
**80 tests, 66.192 seconds, OK, exit 0**. Disposable PostgreSQL 17, synthetic
credentials, `DJANGO_TESTING=1`, temporary media, LocMem cache/email, blocked
unexpected external HTTP; no production mounts or credentials.

Read-only production preflight passed. The pending plan contains only nine
`account` migrations, six `socialaccount` migrations and
`catalog.0101_unique_user_email`.

### Rehearsal findings

An initial exact-user-row assertion failed because stock allauth
`account.0006_emailaddress_lower` lowercases existing `auth.User.email` values.
Inspection of the installed migration and a field-level comparison confirmed one
email changed only in letter case; no user was created/deleted. The final check
explicitly requires unchanged account IDs and every other field, and exactly
`old_email.lower()` for email. It passed. This is a documented migration effect,
not a modification of application tests or a suppressed unexplained failure.

One diagnostic rerun hit PostgreSQL's temporary initialization-server shutdown.
The rehearsal readiness probe was corrected to use TCP `127.0.0.1`, ensuring the
final PostgreSQL server is accepting connections before restoring the archive.

Final rehearsal: archive restore, standard migrations, unique index, user-field
invariants, system checks and old-image schema compatibility all passed, exit 0.
Disposable containers and networks were removed by the runners.

## Activation and live checks

Activation completed using the reviewed server-side `activate.py`, exit 0:

- All 16 pending OAuth migrations applied through standard Django migration
  commands. `migrate --check` and system checks pass.
- Static files were collected incrementally, retaining old hashed assets.
- The 14 reviewed source files and OAuth Compose were installed in
  `/opt/kidsmap`; fresh hashes match the release manifest. The Git checkout remains
  based on the previous production revision with these scoped working-tree changes;
  it is not a deployment of local `main` or its unrelated accumulated features.
- The prepared image is active in `kidsmap-web`, started
  `2026-09-07T05:15:30.781916313Z`. PostgreSQL and Redis retain their July 22 start
  times. No global service restart occurred.
- An HTTP 502 was observed during web-container replacement. The automatic
  readiness check subsequently returned HTTP 200, and fresh login requests pass.
- Fresh production verification confirms both configured OAuth parameters, the
  unique email index, no duplicate SocialApp configuration and both selected full
  administrators retaining usable passwords.

Browser verification on the live site:

- AZ/RU/EN login and registration pages at widths 375 and 1440: all HTTP 200,
  localized Google buttons visible, stylesheet loaded, no horizontal overflow.
- Clicking the Russian Google button reaches the real Google account sign-in page
  for `kidsmap.az`, without `redirect_uri_mismatch` or an OAuth configuration error.
- Live POST/CSRF/session flow for all three languages produces the fixed HTTPS
  callback, exactly `openid email profile`, and PKCE S256. Cancellation returns the
  localized login page with its expected message. GET on OAuth start returns 405;
  POST without CSRF returns 403. No OAuth state or tokens were printed.

The user then completed a real Google login and confirmed returning to KidsMap.
A fresh read-only database check verified that the Google identity is attached to
the **original selected administrator**, with exactly one account for that
normalized email, full administrator access, a usable password, and verified email
records in both allauth and KidsMap. No Google tokens are stored. The other selected
administrator retains full access. This confirms a real Google exchange and
existing-account linking, not just a simulated callback or successful redirect.

All disposable verification/rehearsal containers and networks are gone. Backups
and restricted operational scripts remain on the server for recovery. No commit,
push, or CI deployment was performed.

## Remaining verification limits

The user's real login covered the existing administrator account. Live new-user
signup, the friend's Google login and a live password-reset email were not run;
automated tests cover their relevant application contracts. Google Cloud audience
and publishing settings were not changed or independently inspected; the previous
report records Testing mode. Do not infer public availability for every Google
account from this successful existing-user login.

## Follow-up: auth scenarios and local preview

At the user's request, live login and registration were checked again in AZ/RU/EN:
all six pages return HTTP 200 and contain the localized Google POST form with the
correct language field. Both surfaces use the same OAuth endpoint.

The local virtual environment lacked allauth; the pinned
`django-allauth[socialaccount]==65.19.2` dependency was installed. The isolated
runner `.tmp/verify_google_auth_20260907.py` executed system checks, migration drift
checks, Google/auth/access/password-reset suites and owner regressions:
**187 tests, 338.493 seconds, OK, exit 0**. No migration drift. The oversized image
rejection line in the log belongs to an expected negative owner-upload test.

In addition to the existing security and account tests, the scratch runner adds
12 end-to-end combinations: login/registration × AZ/RU/EN × new/existing account.
Each follows the rendered form into a real application callback with mocked Google
HTTP, checks account creation/reuse and privileges, and repeats login in another
session to verify reuse. Existing tests cover inactive accounts, conflicting
identities, state expiry/replay, cancellation/provider/network errors, invalid OIDC
claims, safe redirects, CSRF, duplicate email constraints and password reset.

Local preview:

- Start command: `.venv/bin/python .tmp/local_preview.py`.
- Bound to `127.0.0.1:8001`; port 8000 was already occupied and was left alone.
- Dedicated SQLite/media/email files under `.tmp/local-preview-20260907`; no
  production environment, users, credentials or database are loaded.
- Fifteen demo places and a separate test superuser. The existing demo seeder
  references retired taxonomy codes; the scratch setup maps only its local demo
  templates to current categories/subcategories. Application code is unchanged.
- Browser-confirmed admin and public password login, home, catalog, account profile,
  place administration and user administration; these pages return HTTP 200.
- Login/registration Google buttons are visible at mobile width 375 without
  horizontal overflow. Real OAuth is intentionally unconfigured locally; its
  missing-configuration flow returns a friendly localized login error. Real Google
  sign-in remains on `kidsmap.az`.
- Local outgoing test emails are written to the preview's `emails` directory.
  Scratch setup, runners and development data are ignored by Git.
