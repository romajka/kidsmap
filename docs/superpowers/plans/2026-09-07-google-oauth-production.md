# Google OAuth production configuration plan

**Goal:** Validate the existing Google integration, configure the supplied OAuth client through production environment variables, and stop before real OAuth until the operator securely supplies the secret.

**Architecture:** Preserve the fixed Django routes and django-allauth bridge. Reuse existing accounts through verified normalized email, with the unique email index as a production activation prerequisite. Keep the unrelated dirty worktree out of any deployment.

**Tech Stack:** Django 6.0.2, django-allauth[socialaccount]==65.19.2, PostgreSQL 17, Docker Compose web/Gunicorn, existing nginx HTTPS proxy.

**Spec:** User attachment `C:/Users/Ramin/.codex/attachments/24d7f678-b6fb-4ace-8519-db43cec5a8b6/pasted-text.txt`.

## Constraints

- Callback stays `https://kidsmap.az/auth/google/callback/`, outside locale prefixes.
- Use `GOOGLE_OAUTH_CLIENT_ID` and `GOOGLE_OAUTH_CLIENT_SECRET`. The operator enters the secret on the server; never copy it into source, Git, terminal output or reports.
- Scopes remain `openid`, `email`, `profile`; Google Auth Platform stays Testing.
- Do not merge/delete/reassign accounts or manually change production DB. Duplicate normalized emails block activation.
- Back up changed configuration on the server with restrictive permissions before editing it. Do not copy secret-bearing backups into the repository.
- Do not restart PostgreSQL/nginx or deploy unrelated local changes. No commit/push.
- Execute inline under the user's explicit configuration/testing authorization. Any identity ownership decision remains with the user.

## Tasks

- [x] Read existing provider, routes, migration, Compose env forwarding, and prior release report. Local HEAD is `df6fef3784a6bae6b7ddce90cd41a392d9f9e6bf` with pre-existing dirty Google integration and unrelated features.
- [x] Attempt fresh production identity inspection using SSH batch authentication. Result: authentication rejected; ask for restored SSH-key access without soliciting credentials in chat.
- [x] Run existing Google/auth/password-reset suites with `DJANGO_TESTING=1`, a fresh disposable database/media root, in-memory cache/email, no production environment inheritance, and blocked external HTTP. Results: 77 local SQLite tests and 80 release-image PostgreSQL17 tests passed.
- [x] Verify generated HTTPS callback, Google scopes and locale redirects from the actual installed allauth/Django code with synthetic credentials. Record package versions and source fingerprints. Three extra contract tests include verified-existing-user linking and complete password reset.
- [x] After SSH access was restored, inspect `/opt/kidsmap` commit/status, active web image, effective provider/domain/HTTPS settings (only booleans/non-secret settings), Compose mechanism and migrations. Check duplicates using aggregate SQL in an explicit read-only transaction with timeouts.
- [x] Duplicates still exist: stop dependent activation; preserve account ownership and report aggregate counts (2 groups / 6 users). Secret configuration alone does not resolve this gate.
- [x] Back up exact changed server configuration with mode 0600 in a root-only directory, configure the supplied public Client ID through existing env names, and inspect env forwarding without displaying secret values. Only the prepared release Compose forwards OAuth; active Compose awaits the gated release.
- [x] Exclude `.env`, `.env.*` and `.tmp` from Docker build context while retaining the empty `.env.example`; mirror this in the backed-up server `.dockerignore` before the operator enters the secret. No production image rebuilt or activated.
- [x] Stop at the missing-secret gate with the exact server env path/edit command and required application-service recreation command in the status report; no service restarted.
- [x] After the user supplies the secret and prerequisites pass, use the scoped release only, standard migrations and the `web` service only. Verify live linking for an Audience test user returns the same existing User without duplicates before declaring Google Login ready. Completed under the user's renewed explicit deployment authorization; see [activation report](../../GOOGLE_OAUTH_ACTIVATION_2026-09-07.md). Email ownership and administrator changes were separately confirmed by the user before release.

## Deliverables

- This plan and `docs/GOOGLE_OAUTH_PRODUCTION_STATUS_2026-09-07.md`, containing sanitized fresh evidence, exact test command/results, historical evidence clearly dated, and outstanding gates.
- An ignored isolated verification runner under `.tmp/`; no production credentials, user data, or Google network calls in automated tests.
