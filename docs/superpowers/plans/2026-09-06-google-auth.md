# Google authentication implementation plan

**Goal:** Add Google registration/login to the existing KidsMap accounts without duplicate email identities.

**Architecture:** django-allauth 65.19.2 handles the authorization-code exchange, state and OIDC validation. A social adapter bridges its verified identity to the existing Django User, UserProfile, UserEmailVerification and Django session login; existing password/OTP routes remain authoritative. Standard allauth SocialAccount and EmailAddress models record identity and verification, with no stored tokens.

**Tech stack:** Django 6.0.2, django-allauth, PostgreSQL production / SQLite development.

**Spec:** User attachment `pasted-text.txt`, 18 sections, supplied 2026-09-06.

## Constraints and audit

- Default auth.User and ModelBackend; no existing social provider. Registration generates a username from email, creates inactive User and sends OTP. Google registration uses the same username generator and an unusable password.
- Email uniqueness currently exists only in forms. Add a database unique expression index on nonempty lower(trim(email)); refuse migration on existing duplicates rather than merge users automatically. No new User fields.
- Never activate an inactive account through OAuth: is_active also represents administrative suspension and cannot safely distinguish it from pending registration.
- Preserve profile, password, permissions and memberships when linking. Accept only an explicitly boolean verified email. Reject conflicting identity ownership.
- Keep RU/AZ/EN, local next URLs, CSRF-protected POST start, one fixed callback route, online access and only openid/email/profile scopes.
- Preserve pre-existing workspace edits. Execute inline; no commits or publishing requested.

## Tasks

- [x] Write integration tests in `src/catalog/testcases/test_google_auth.py`: POST start and mocked Google HTTP callback; new/repeat/link flows; invalid/unverified/missing claims; state/cancel/network errors; next and locale; inactive/conflicting accounts; permissions, password reset, session rotation, DB uniqueness. Run before implementation to observe missing route and missing constraint failures.
- [x] Add dependency and provider env configuration in `requirements.txt`, `src/config/settings.py`, `.env.example`, `docker-compose.yml`. Register fixed `/auth/google/` and `/auth/google/callback/` in `src/config/urls.py`; do not include allauth password/signup URLs.
- [x] Implement `src/catalog/google_auth.py`: thin Google views, social adapter, localized errors, atomic account creation/linking and verification synchronization. Use `SocialAccount(provider='google', uid=sub)` and existing username/profile rules; Django `login(..., backend='django.contrib.auth.backends.ModelBackend')` retains existing sessions and permissions.
- [x] Add reversible migration `0101_unique_user_email.py`, validating existing normalized duplicates before a unique index. Test direct case/whitespace duplicate insert and update. Catch concurrent constraint failures as a retryable auth error.
- [x] Extend `UserPasswordResetForm.get_users` only for active Google users whose current email is verified; preserve standard password accounts. Test actual reset email, token completion and subsequent password login.
- [x] Add shared `auth/includes/google_button.html`, scoped CSS and localized copy to login/register, preserving next/language through OAuth state. Check keyboard focus and desktop/mobile using Playwright.
- [x] Run auth/owner regression suites, migration drift/system checks and browser QA. Document exact Google Cloud callback URI, env vars, deployment migration and external credential limitation in `docs/GOOGLE_OAUTH.md`.

## Verification commands

```powershell
$env:DJANGO_TESTING='1'
.venv/Scripts/python.exe manage.py test catalog.testcases.test_google_auth catalog.testcases.auth_flow catalog.testcases.auth_access catalog.testcases.test_password_reset catalog.testcases.owner --noinput
.venv/Scripts/python.exe manage.py check
.venv/Scripts/python.exe manage.py makemigrations --check --dry-run
```

Real Google network requests are excluded from tests. Browser QA uses an isolated local database and fake provider HTTP responses only in test code; live authorization requires operator-owned OAuth credentials.
