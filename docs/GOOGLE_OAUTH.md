# Google login in KidsMap

## Architecture and account policy

KidsMap keeps Django 6.0.2 `auth.User`, `ModelBackend`, existing password/OTP
views and session cookies. `django-allauth[socialaccount]==65.19.2` handles the
Google authorization-code/OIDC exchange. Only its provider integration is exposed;
its alternative password/signup routes are not installed. The social adapter bridges
the validated identity to the existing account flow using Django `login()`.

- A first Google login creates an active User with email, available first/last name,
  an unusable password and the existing deterministic username generator. No phone,
  avatar, role, owner membership or other personal data is fabricated. UserProfile
  is created with existing defaults.
- Matching email means `lower(trim(email))`. An active existing User is reused,
  with the existing password, username, names, permissions, groups and profile retained.
- Linking requires a valid email and an explicitly boolean `email_verified=true`
  (or Google's userinfo `verified_email=true`). Unverified/missing/invalid email is rejected.
- A Google subject is stored as `SocialAccount(provider="google", uid=sub)`.
  Repeated login uses this stable identity; Google name/email changes do not overwrite
  the user's chosen local profile. Conflicting owners or a different Google subject
  already attached to the email's User are rejected without merging or creating users.
- A matching current local email is marked verified in both allauth `EmailAddress`
  and KidsMap `UserEmailVerification`. Pending OTP material for that active account
  is cleared. No additional verification email is sent. On email changes, allauth
  retains only one primary address per User.
- Inactive users remain inactive. KidsMap currently uses `is_active=False` for both
  pending registration and account suspension, with no reliable independent reason
  flag. OAuth therefore does not auto-reactivate them: complete the existing OTP
  registration or ask support to review the account. No duplicate User is created.
- Google-only users can establish a password using the existing reset-email/token
  flow. This is allowed only when their current local email is verified. Ordinary
  password-user reset eligibility is unchanged.

Protocol references: [allauth Google provider](https://docs.allauth.org/en/latest/socialaccount/providers/google.html),
[Google OpenID Connect](https://developers.google.com/identity/openid-connect/openid-connect).

## Google Cloud setup

1. Open Google Cloud Console, choose the project, and configure Google Auth Platform
   branding, audience and data access (OAuth consent screen). Use the KidsMap name,
   support contact and the site's privacy/terms URLs. For a public service use the
   appropriate external audience; while in testing, add the intended test users.
2. Create an OAuth client of type **Web application**. Use separate clients for local
   development and production when possible.
3. Register exact **Authorized redirect URIs**, including the final slash:

   | Environment | Redirect URI |
   |---|---|
   | Local hostname | `http://localhost:8000/auth/google/callback/` |
   | Local IP | `http://127.0.0.1:8000/auth/google/callback/` |
   | Production | `https://kidsmap.az/auth/google/callback/` |

   Add a different port explicitly if used. There are no `/ru/` or `/en/` callback
   variants: locale and the safe return URL travel in session-backed OAuth state.
   Start and finish using the same host (`localhost` and `127.0.0.1` are different).
4. **Authorized JavaScript origins are not needed for this server-side redirect
   integration.** It does not embed the Google JavaScript SDK or One Tap.
5. Request only `openid`, `email`, `profile`. Access is online; no offline access
   or refresh-token consent is requested. Complete Google's publishing requirements
   for your actual audience before making the production client available.

Google requires the callback to match the registered redirect URI:
[Google OIDC setup and authorization request](https://developers.google.com/identity/openid-connect/openid-connect).
The button uses Google's multicolor G on a neutral surface:
[Google branding guidance](https://developers.google.com/identity/branding-guidelines).

## Environment and deployment

Set these only in the server environment or untracked deployment `.env`:

```dotenv
GOOGLE_OAUTH_CLIENT_ID=your-web-client-id.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=your-client-secret
```

`.env.example` has empty entries; `docker-compose.yml` forwards both variables to
the web service. Do not also create a Google SocialApp in Django admin: configuration
has one source, the environment. Ambiguous/missing configuration returns a friendly
login error. Client secrets and Google tokens are never rendered in templates.

Local Django does not automatically load `.env`; export the values in the shell
before running `manage.py runserver`, or use Compose's environment handling.

```powershell
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe manage.py migrate --noinput
.venv/Scripts/python.exe manage.py check
.venv/Scripts/python.exe manage.py runserver 127.0.0.1:8000
```

For production, deploy the updated image, set both credentials, run migrations, and
restart workers. Keep the existing production PostgreSQL, Redis, HTTPS and secure
cookie settings. The reverse proxy must pass the correct public host and HTTPS
scheme so the callback is `https://kidsmap.az/auth/google/callback/`. Do not switch
cookie domain or secret key as part of OAuth setup; existing sessions remain valid.

## Database migration and duplicate protection

Apply standard allauth `account`/`socialaccount` migrations and
`catalog.0101_unique_user_email`. No User fields or token fields were added.

The KidsMap migration adds `kidsmap_user_email_ci_unique`, a unique expression index
on `LOWER(TRIM(auth_user.email))`, excluding empty email. It applies to every writer,
including ordinary registration, profile changes, admin and concurrent OAuth callbacks.
This is intentionally a database-only migration because Django owns `auth.User`;
the project's model state does not redefine or monkey-patch that model. Supported
databases are PostgreSQL (production) and SQLite (development).

Before adding the index, the migration rejects pre-existing normalized duplicate
emails. It does **not** merge/delete users or pick an arbitrary owner. An operator
can inspect duplicate groups with this read-only query:

```sql
SELECT LOWER(TRIM(email)) AS normalized_email, COUNT(*) AS users
FROM auth_user
WHERE TRIM(email) <> ''
GROUP BY LOWER(TRIM(email))
HAVING COUNT(*) > 1;
```

Resolve account ownership explicitly before retrying the migration. Back up the
database before deployment. The index has a reverse migration. Existing accounts
with blank email are preserved. On 2026-09-06 the local SQLite contained no duplicate
groups; a local backup was made and the new migrations applied successfully.

Account/profile/identity/verification creation is atomic. A late uniqueness conflict
rolls back the new User and returns a retryable error. An existing-email collision
after ordinary registration/profile form validation becomes a form error. No
partial account is committed when social linking fails.

## Security and redirects

- OAuth start is POST-only with Django CSRF protection. Provider parameters are
  server-controlled; request `scope`, `auth_params` or `process=connect` cannot widen
  access or change the operation.
- allauth creates random session-bound, single-use state with a 600-second lifetime,
  uses PKCE S256 and validates Google's issuer, audience and expiry. The standard
  server-to-server TLS token exchange uses allauth's documented OIDC validation.
- Existing subject ownership, matching-email ownership, active status and verified
  email are checked before login. An authenticated browser cannot attach or switch
  to another person's identity via the callback.
- Django login rotates the session key. Google sessions use browser-close expiry,
  matching the existing password login's default without “remember me”.
- `next` is checked before OAuth and again before the final redirect. External hosts,
  unsafe schemes and auth-page loops in RU/AZ/EN are rejected. The fallback is the
  localized existing account profile.
- Only email claims are retained as social metadata. No access, refresh or ID tokens
  are persisted in the database/session or logged by this integration. Outbound
  provider requests have a 10-second timeout.
- Cancellation, bad state, invalid claims, conflicts, unavailable provider/network
  and missing configuration show short localized messages and a persistent accessible
  alert on the existing login page. Provider exception text is not exposed.

## Validation and manual smoke test

Automated callbacks replace only Google HTTP responses; account creation, OIDC
claim checks, database constraints, verification, session login and reset tokens
execute real production code. No real Google requests occur in backend tests.

```powershell
$env:DJANGO_TESTING='1'
.venv/Scripts/python.exe manage.py test catalog.testcases.test_google_auth catalog.testcases.auth_flow catalog.testcases.auth_access catalog.testcases.test_password_reset --noinput
.venv/Scripts/python.exe manage.py test catalog.testcases.owner --noinput
.venv/Scripts/python.exe manage.py makemigrations --check --dry-run
```

With real credentials, manually test a new Google user, a repeat login, an existing
active password user's matching verified email, password login/reset after linking,
logout, consent cancellation and returning to an owner page through `next`. Confirm
one User and one Google identity remain, with profile and permissions unchanged.

Implementation QA on 2026-09-06: 27 Google tests and 50 existing auth/reset tests
passed. The 109 owner tests also passed in the broader regression run. An old
reset-email test was updated to check the login, recipient and working reset link
instead of obsolete copy and a retired logo filename. `check` and migration drift
checks passed; standard and project migrations applied to local SQLite.

Browser QA used Firefox and an isolated copied database with a test-only fake Google
response. Login/register were checked in RU/AZ/EN at 375, 768, 1024 and 1440 px, without
horizontal overflow. Keyboard Tab/Enter, visible focus, successful profile redirect,
cancellation and invalid-state alerts were exercised. No application JS exceptions
were found; the existing external Tawk widget produced resource/console errors in
the unfiltered run. It was stubbed for the isolated auth-flow check.

Live Google consent/token exchange with real credentials and production PostgreSQL
concurrency were not exercised here. Configure the real OAuth client and run the
production smoke test before enabling the button for real users.

## Files changed for this integration

| File | Change |
|---|---|
| `src/catalog/google_auth.py` | Google routes, adapter, atomic linking and localized failures |
| `src/config/settings.py` | allauth apps/middleware, provider config and env values |
| `src/config/urls.py` | Fixed Google start/callback routes |
| `src/catalog/migrations/0101_unique_user_email.py` | Duplicate preflight and reversible unique email index |
| `src/catalog/forms.py` | Password reset eligibility for verified Google-only accounts |
| `src/catalog/views.py` | Registration/profile race conflicts become form errors |
| `src/catalog/services/auth_redirects.py` | Google routes and cross-language auth-loop protection |
| `src/catalog/templates/auth/login.html` | Shared Google button and scoped stylesheet |
| `src/catalog/templates/auth/register.html` | Shared Google button and scoped stylesheet |
| `src/catalog/templates/auth/includes/google_button.html` | RU/AZ/EN accessible POST button |
| `static/css/components/google_auth.css` | Button, focus, hover and separator styles |
| `src/catalog/testcases/test_google_auth.py` | 27 targeted integration/security/regression tests |
| `src/catalog/testcases/auth_flow.py` | Correct obsolete reset-email expectations |
| `requirements.txt` | Pinned allauth socialaccount dependency |
| `.env.example` | Empty Google credential entries |
| `docker-compose.yml` | Pass Google env values into web service |
| `docs/superpowers/plans/2026-09-06-google-auth.md` | Audit and implementation checklist |
| `docs/GOOGLE_OAUTH.md` | Setup, policy, migration, verification and limitations |

Other pre-existing/concurrent workspace edits are outside this integration.
