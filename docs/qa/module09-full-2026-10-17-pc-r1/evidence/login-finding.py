from pathlib import Path
Q=Path(__file__).resolve().parent;O=Q.parents[1]/'docs/qa/module09-full-2026-10-17-pc-r1'
(O/'findings/SOCIAL-QA-10.md').write_text('''# SOCIAL-QA-10 — гостевой переход на вход заканчивается 404

OPEN / P2 / LOCAL. Canonical alias of existing ADJ-ANONYMOUS-LOGIN-08; one issue, not two. Exact introduction UNKNOWN; present in current-source baseline before SOCIAL08. Production UNKNOWN.

Role guest. URLs: `/account/notifications/`, `/ru/account/notifications/`, `/en/account/notifications/`. Reproduced RU/AZ/EN×360/390/768/1024/1280/1440 (18 cases), `adjacent-feed.json` and native `png/anonymous-login-*.png`.

Steps: log out; navigate directly to notifications. Expected login form with a usable return path. Actual302 to `/accounts/login/?next=...`, followed by404. The supported localized `/auth/login/` route returns200 and renders the real form. No access bypass demonstrated; recovery into a protected module is broken for a guest/direct link or expired session.

Source: `src/catalog/controllers/workflow_notifications.py:61` uses `@login_required` without explicit login_url; `src/catalog/urls.py:182` defines `account_login` at auth/login. Current runtime-info records LOGIN_URL=/accounts/login/; current settings contain no override. Cause is route/default-setting mismatch, not stale invitation handling.

Scope proposal for a separate PLAN: choose the correct shared named LOGIN_URL or bounded decorator wiring after impact analysis of all default guards; add focused guest/authenticated, localized next, safe return, POST/CSRF/ACL tests. Do not alter invitation guards or public review policies. No fix performed. Historical ADJ evidence remains immutable; this canonical finding supersedes its tracking alias only.

PriorityP2: user cannot reach login through this supported protected URL, while direct real login works. Local runtime source verified; source1024 unchanged by audit.
''',encoding='utf-8')
(O/'repair-prompts/SOCIAL-QA-10.txt').write_text('''KidsMap: PLAN SOCIAL-QA-10 only, canonical alias ADJ-ANONYMOUS-LOGIN-08. Read current guide and module09-full-2026-10-17-pc-r1 REPORT/findings/SOCIAL-QA-10.md, adjacent-feed.json, runtime-info and preservation verification. Keep dirty approved SOCIAL01–09 changes, HEAD852938d, transfer branch, index/task33-progress, active_run NONE and old evidence. Freshly confirm guest notifications302→/accounts/login/?next=...→404 versus actual localized /auth/login/200 on current source and fresh own RU/AZ/EN MO. Use graph-first impact analysis plus source for default login_required consumers. Propose the smallest correct named-login configuration/decorator fix, enumerate exact files and focused tests for localized next preservation, external-next safety, authenticated inbox, CSRF/POST/foreign/stale/revoked boundaries and affected shared auth guards. Prepare a concrete diff/plan and request approval of that scope before app changes. No full unchanged module rerun merely for green; preserve this acceptance as evidence only for matching source. Do not implement SOCIAL11 or module10 automatically. No commit/push/deploy/production/reset/clean/stash or old PNG download.
''',encoding='utf-8')
(O/'FINDINGS.md').write_text('''# ACCEPT-09 findings

AUDIT ONLY, current LOCAL WORKTREE, no application changes. Historical SOCIAL-QA-01–09 scoped closures retained; module09 OPEN.

- [SOCIAL-QA-10](findings/SOCIAL-QA-10.md), P2 OPEN: guest notifications → nonexistent login route404. Canonical alias of ADJ-ANONYMOUS-LOGIN-08; count once. [Next PLAN prompt](repair-prompts/SOCIAL-QA-10.txt).
- [SOCIAL-QA-11](findings/SOCIAL-QA-11.md), P3 OPEN: nested main landmarks on typed reviews/inbox. [PLAN prompt](repair-prompts/SOCIAL-QA-11.txt).

No P0/P1 established in executed scope. No regression introduction assigned without evidence. Production, physical screenreader and external services NOT RUN. Absence of main on admin/403 documents is recorded as an excluded structural observation, not counted as a new defect solely from that assertion.
''',encoding='utf-8')
print('SOCIAL10 canonical alias recorded from18 fresh failures; no application edits')
