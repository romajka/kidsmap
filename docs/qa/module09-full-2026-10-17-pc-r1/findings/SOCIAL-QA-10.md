# SOCIAL-QA-10 — гостевой переход на вход заканчивается 404

OPEN / P2 / LOCAL. Canonical alias of existing ADJ-ANONYMOUS-LOGIN-08; one issue, not two. Exact introduction UNKNOWN; present in current-source baseline before SOCIAL08. Production UNKNOWN.

Role guest. URLs: `/account/notifications/`, `/ru/account/notifications/`, `/en/account/notifications/`. Reproduced RU/AZ/EN×360/390/768/1024/1280/1440 (18 cases), `adjacent-feed.json` and native `png/anonymous-login-*.png`.

Steps: log out; navigate directly to notifications. Expected login form with a usable return path. Actual302 to `/accounts/login/?next=...`, followed by404. The supported localized `/auth/login/` route returns200 and renders the real form. No access bypass demonstrated; recovery into a protected module is broken for a guest/direct link or expired session.

Source: `src/catalog/controllers/workflow_notifications.py:61` uses `@login_required` without explicit login_url; `src/catalog/urls.py:182` defines `account_login` at auth/login. Current runtime-info records LOGIN_URL=/accounts/login/; current settings contain no override. Cause is route/default-setting mismatch, not stale invitation handling.

Scope proposal for a separate PLAN: choose the correct shared named LOGIN_URL or bounded decorator wiring after impact analysis of all default guards; add focused guest/authenticated, localized next, safe return, POST/CSRF/ACL tests. Do not alter invitation guards or public review policies. No fix performed. Historical ADJ evidence remains immutable; this canonical finding supersedes its tracking alias only.

PriorityP2: user cannot reach login through this supported protected URL, while direct real login works. Local runtime source verified; source1024 unchanged by audit.
