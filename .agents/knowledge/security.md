# Security knowledge — KidsMap

AS-IS discovery: 2026-09-06, local `df6fef3` plus pre-existing working changes. Production clean `86a0b8c` is a distinct snapshot. This map identifies trust boundaries, not a whole-system security certification. See [source of truth](source-of-truth.md), [database](database.md), [testing](testing.md), and the first security audit.

## Boundaries and source files

| Boundary | Source / required invariant |
| --- | --- |
| Password registration/login/reset | `src/catalog/views.py:1643`, `:1707`, `:1754`; `forms.py:566`, `:807`; `controllers/auth_controller.py`; retain existing authentication semantics and generic reset responses |
| Email OTP | `services/email_verification.py`: cooldown, expiry, attempts and verification; repository persistence must agree with service decisions |
| Google OAuth (local changes) | `google_auth.py:88`, `:108`, `:130`; `src/config/urls.py:29`; `settings.py:67`: POST start + CSRF, fixed callback, state/PKCE, verified email, atomic identity linking, no stored provider tokens |
| Auth redirects | `services/auth_redirects.py`; reject external destinations and auth-loop destinations, preserve supported language |
| Ownership/roles | `services/place_access.py`, `services/ownership_use_cases.py`, `controllers/ownership_controller.py`, owner controllers and `repositories/django_repositories.py`; enforce user/object scope on the backend |
| Admin actions | `domain_admin/`, custom admin site/views; staff visibility is not proof of permission to mutate every object |
| Images | `services/image_uploads.py:21`, `:92`; `photo_views.py:26`, `:51`, `:74`; real format, source bytes/pixels/dimension limits, normalization, object ownership and batch limits |
| Phone reveal | `phone_views.py:18`; POST/CSRF, public visibility, throttling and no-store; phone data handling differs between local and production |
| Specialist documents | `models/specialist.py:388`, `views.py:1814`; private/owner/staff/public-verified document access must hold at storage and web-server layers too |
| JSON/import | `domain_admin/place.py`, import/export services and `management/commands/import_places.py`; inspect actual schema, allowlists, file/URL handling and write permissions before calling anything |
| Event tracking | `views.py:154-204`, `:544`; endpoint is deliberately CSRF-exempt with origin/rate checks; controller validates payload. Inspect safeguards before claiming CSRF vulnerability |
| Runtime settings | `src/config/settings.py:143-153`, `:347-423`; HTTPS/cookies/HSTS, PostgreSQL enforcement, production Redis and secret placeholder checks |

Google OAuth credentials being present in settings code does not mean a Google Cloud client exists or production login works. Real provider access and callback configuration are separate operational evidence.

## Production evidence and urgent auth finding

See [read-only evidence](../../docs/agent-audits/PRODUCTION_READ_ONLY.md) E4/E7 and [security audit](../../docs/agent-audits/security.md). Active image `.env` contains populated secret settings (booleans only checked), app PostgreSQL role is superuser, nginx serves media without a protected_docs exception but document rows are0. Anonymous verification-login bypass was reproduced on isolated fresh fixtures; production matching code and10active verified records establish affected preconditions. No production exploit or incident history was tested. This finding overrides any earlier assumption that OTP handling is safe merely because challenge hashing/expiry exist.

## Confirmed source risks requiring review, not automatic fixes

- **Private-media separation:** specialist documents use default FileSystemStorage under `protected_docs/specialists/`; authenticated download logic exists, but generic media serving (`src/config/urls.py:62-68`, `src/config/views.py:136`) and the repository nginx `/media/` alias (`deploy/nginx/kidsmap.az.conf`) do not exclude that subtree. If a file exists and its path is known, direct media access can bypass the view. Check deployed nginx/storage and document counts without downloading private files; distinguish latent source defect from confirmed live exposure.
- **Build context:** `Dockerfile:18` copies the complete context; `.dockerignore:1-12` omits `.env*` and temporary credential/config paths. Environment files can enter image layers despite Git ignore. Verify image membership using booleans/path metadata only, never secret contents. Root `.env#` is tracked but its eight-byte content has no environment assignments; do not misreport it as a credential leak.
- **Authentication abuse controls:** the password login/reset entry points above do not show application-level throttling. Review upstream controls and actual exposure before assigning severity; absence alone is not authentication bypass or a critical issue.

For every finding report prerequisites, source evidence, affected snapshot, actual impact, confidence and unverified assumptions. Follow data-flow from input to sink for XSS/SSRF/injection; `safe`, `innerHTML`, an integer ID or `csrf_exempt` alone is not proof of exploitation.

## Audit safety

No destructive security testing, production attack traffic, account takeover simulation, unsolicited email, data export, production changes or credential rotation in this phase. Do not read private documents to prove their availability. Do not print passwords, tokens, cookies, credential JSON, DSNs or environment values; report setting names and configured/not-configured only. Do not commit `.env`, dumps, logs, temporary browser state or memory graph databases.

Use read-only source inspection and isolated fixtures for negative permission/CSRF/redirect/upload cases. Follow [testing](testing.md) before any Django test, including cache and database isolation. Defer production configuration changes to a concrete plan and explicit user approval; this audit's authorization overrides any older deployment authorization.
