# Specialist onboarding backend audit — 2026-11-04

Role: `django-reviewer`; execution: delegated `/root/specialist_backend_audit`; definition `.agents/agents/django-reviewer/agent.md`. AUDIT ONLY. Parent snapshot: LOCAL HEAD `b7659e79` plus existing dirty WORKTREE; production UNKNOWN, never accessed. Application files unchanged. Parent expressly authorized isolated synthetic probes after source review; all created records use `backend-audit-516eaf29` prefix and do not overlap browser fixtures.

## 1. State and actual flow

- `/ru/account/` → `/ru/account/places/specialists/create/` → `/ru/account/specialists/proposals/new/`; saved proposal `/ru/account/specialists/proposals/<uuid>/`.
- Submit requires name, format, at least one specialization, biography in one language, phone OR WhatsApp, at least one working language, and an active valid practice location for offline/both. Photo, prices, education, experience, certificates are optional. Source: `src/catalog/forms.py:2349–2430`, `src/catalog/forms_specialist_locations.py:16–22`.
- Draft persists `SpecialistProposalDraft`; submit creates pending `Specialist`. `profile_subject=self` additionally requests `SpecialistClaim`; `other` does not. No ownership is granted on submit. Source: `src/catalog/services/specialist_proposal_drafts.py:55–108`.
- Admin publication and identity confirmation are separate decisions. Identity review is `/ru/account/specialists/<id>/review/`, requiring active staff with `catalog.review_specialist_claim`. Source: `src/catalog/services/specialist_domain.py:49–53,95–128`.
- Publication changes the profile out of `pending`, so it disappears from `/admin/catalog_moderation/moderationspecialist/`. It remains in the complete specialist list and may still have an unresolved identity request. Source: `src/catalog/proxy_apps/catalog_moderation/admin.py:131–148`.

## 2. Strengths

- Proposal writes lock the actor/draft, check versions, reject another author's access, discard authority fields, and make repeated submit idempotent.
- Draft photos use private storage and an author-only endpoint; draft attachment authorization is separate from verified-person document upload.
- Identity approval rechecks reviewer permissions and conflicting existing verified accounts under locks; submitting a self declaration alone grants no management rights.
- Existing tests cover self/other, private photo persistence, stale drafts, duplicate submit and ownership boundaries. These are source observations; test execution belongs to the lead.

## 3. Confirmed problems

### SB-01 — P1: view-only staff can publish specialists

Environment: LOCAL isolated SQLite. **Runtime reproduced** with `view_specialist=True`, `change_specialist=False`, non-superuser staff. Posting `action=mark_published`, `_selected_action=<own synthetic pending id>`, `index=0`, `select_across=0` returns HTTP 302 and sets `status=published,is_active=True` through both the ordinary admin list and moderation proxy.

Source: `src/catalog/domain_admin/specialist.py:760–767` has neither action permission declaration nor an internal change-permission check. `mark_draft`, `mark_pending`, `mark_rejected` at 774–807 share the pattern. `src/catalog/proxy_apps/catalog_moderation/admin.py:49–55` additionally builds actions without permission filtering. The installed Django admin keeps actions lacking `allowed_permissions`, accepts view-or-change access to changelist, and invokes selected actions (`.venv/lib/python3.12/site-packages/django/contrib/admin/options.py:1020–1046,1589–1645,1978–2018`).

Impact: a staff account authorized only to inspect can change public availability. Confidence high. Owner: django-reviewer + security-reviewer. Required acceptance: view-only GET allowed, every mutation POST denied with no row changes, authorized moderator actions still work. CSRF was not enforced in this permission probe; this is **not** a claim of CSRF bypass or production exploitation.

### SB-02 — P2: “Return for revision” leaves the initial applicant unable to revise

Environment: LOCAL isolated SQLite. **Runtime reproduced**: create self application, leave identity pending, apply `return_for_revision` as superuser. HTTP 302, profile becomes `draft`; original proposal still has `submitted_at`; applicant profile-edit GET returns 404; draft-resume GET redirects to workspace.

Source: proxy `return_for_revision` simply calls `mark_draft` (`src/catalog/proxy_apps/catalog_moderation/admin.py:57–59`); edit requires verified person (`src/catalog/controllers/specialist_workspace.py:175–178,313–315`), and submitted proposals redirect instead of reopening (`:556–560`). Workspace exposes only an identity-claim link for this initial applicant (`src/catalog/templates/pages/specialist_workspace.html:46–54`).

Impact: explicit request to correct the application cannot be followed. Separate identity approval can unlock editing, but the return action neither performs it nor explains this dependency. Confidence high. Owner: django-reviewer + frontend-reviewer. Acceptance: return restores a scoped author-editable proposal while preserving identity protections, and resubmit returns the same intended profile to the queue.

### SB-03 — P2: publication removes the profile queue item but leaves identity/management unresolved

Environment: LOCAL isolated SQLite. **Runtime state reproduced**: publishing a self application leaves its claim `pending` and verified person null. Source publication at `src/catalog/domain_admin/specialist.py:761–767` only changes profile fields; identity approval at `src/catalog/services/specialist_domain.py:113–127` only changes ownership/claim fields. Queue filters profile `status=pending` (`src/catalog/proxy_apps/catalog_moderation/admin.py:140`).

The split itself is a legitimate security boundary. The integration gap is discoverability: specialist admin exposes read-only identity fields (`src/catalog/domain_admin/specialist.py:458–459,1164–1167`) while identity decisions live in the account workspace (`src/catalog/templates/pages/specialist_workspace.html:64,110`). No review link was found in the inspected specialist admin templates. Admin rendered discoverability must be verified by the lead before presenting this as a fully reproduced UI finding.

Impact: moderator can believe acceptance is complete after the item disappears while the applicant still cannot manage the profile. Confidence high for state transition, medium for UI discoverability. Owner: frontend-admin + django-reviewer. Acceptance: visible outstanding identity state and direct reviewer navigation, with independent publication and identity decisions clearly named.

### SB-04 — P2: invalid contact satisfies submission readiness

Environment: LOCAL isolated SQLite. **Service runtime reproduced**: otherwise valid application with `phone='definitely not a phone'` submits and stores that value. `src/catalog/forms.py:2383–2386` only checks non-empty phone/WhatsApp; model fields are plain strings (`src/catalog/models/specialist.py:180–181`).

Impact: an application can pass required-contact validation with unusable contact details. Confidence high for backend; normal browser formatting/validation was not tested by this role. Owner: django-reviewer + frontend-reviewer. Acceptance: supported real phone formats accepted consistently, meaningless strings rejected at the server, helpful field-level error.

### SB-05 — P2: anonymous specialist entry loses its destination at login

Environment: LOCAL isolated SQLite. **HTTP reproduced**: anonymous GET `/ru/account/specialists/proposals/new/` returns 302 to login without `next`. Source: `src/catalog/controllers/specialist_workspace.py:165–166` redirects only to `account_login`.

Impact: bookmarked/shared form and expired-session re-entry lose the intended specialist destination; the user must rediscover it after authentication. Homepage→account flow may preserve its own next, so this does not assert every login entry fails. Confidence high. Owner: django-reviewer + frontend-reviewer. Acceptance: login preserves a validated local destination, including draft resume; normal login fallback remains intact.

## 4. Tech debt

Legacy `views.owner_specialist_create/edit` are not the routed handlers: `src/catalog/urls.py:228–229` routes to workspace profile. Audit/implementation must follow current routes. Shared moderation action dispatch has a broader permission boundary than specialist business services.

## 5. Risks and unknowns

- Saving an already published verified profile uses the same record and sets `draft` or `pending` (`src/catalog/services/owner_specialist_use_cases.py:88`). Thus edits can take the live card out of the public queryset; whether the product wants this or separate candidate revisions requires a decision. Not runtime-probed here.
- PostgreSQL concurrent locking, real email/OTP delivery, Google OAuth, production configuration, real document verification and public production exposure are NOT RUN/UNKNOWN.
- No broad assertion that all admin actions are vulnerable: runtime proof is specifically specialist publication through two routes. Adjacent actions require bounded follow-up.

## 6. Dead/legacy candidates

No deletion recommendation. Legacy route implementations are candidates for wiring review only; graph absence alone is not dead-code proof.

## 7. Checks executed and gaps

Executed: instruction/role/contracts read; memory quick pass (used only for historical navigation, current behavior verified independently); `git status --short`; graph list/index/architecture/search/trace/coverage; exact source reads; installed Django source inspection; isolated synthetic probe.

Exact runtime command (exit **0**):

```bash
.venv/bin/python .tmp/specialist-e2e-20261104/run.py shell -c "exec(open('.tmp/specialist-e2e-20261104/backend_audit_probe.py').read())"
```

Runner clears inherited environment, sets `DJANGO_TESTING=1`, uses disposable SQLite `.tmp/specialist-e2e-20261104/qa.sqlite3`, LocMem cache, isolated public/private media, local file email, disabled analytics/external integrations. Result: two unauthorized-publication reproductions, one blocked-revision reproduction, invalid-phone persistence, anonymous-next loss. Expected 404 from denied applicant edit was logged. Client default CSRF checks were disabled; real browser CSRF handling is lead-owned.

Graph: `home-ramin-kidsmap`, root `/home/ramin/kidsmap`, ready/full, generation `2026-11-03T06:17:07Z`; inspected Python paths metadata-match/no recorded gaps. Templates have partial parsing (`specialist_workspace.html:17,20,21,23,24`; specialist admin change form:602; change list:93,105), verified using direct source. Root `templates/admin/catalog/specialist/` does not exist; actual admin override is `src/catalog/templates/admin/catalog/specialist/`. Some exploratory `rg` commands returned exit 2 for guessed nonexistent paths; resolved to actual paths before conclusions.

Not run by this role: application test suites (lead owns), rendered desktop/mobile/language matrix, real login/OTP flow, browser upload and successful post, PostgreSQL concurrency, production. No claim of complete end-to-end acceptance.

## 8. Recommendations and handoff

`kidsmap-orchestrator`: merge these runtime observations with browser evidence; report the two concrete workflow blockers and permissions defect before polish. Preserve the distinct identity/publication decisions.

`security-reviewer` / `django-reviewer`: scoped implementation plan for SB-01 first; audit all specialist mutation actions and moderation dispatch, with read-only staff negative regression coverage.

`frontend-admin` / `frontend-reviewer`: verify acceptance/identity discoverability and returned-application recovery in rendered UI; show full status without implying publication grants management.

Changed: assigned report plus authorized ignored scratch probe/fixtures only. DB impact: isolated synthetic rows only; no schema changes. Production unchanged. Application fixes require explicit scoped implementation authorization.

## 9. Priority

P0: none demonstrated. P1: SB-01 confirmed local authorization defect. P2: SB-02/04/05 confirmed local behavior; SB-03 state split confirmed, rendered discoverability pending lead. P3: legacy wiring/documentation cleanup only after functional issues.
