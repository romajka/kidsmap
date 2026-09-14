# Official System Email Sender Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ensure every KidsMap system email is sent as `KidsMap <info@kidsmap.az>` and no runtime setting can continue using the legacy Gmail sender.

**Architecture:** Django account emails already converge on `settings.DEFAULT_FROM_EMAIL`: registration codes, password reset, account-deletion confirmation, staff notifications, and the SMTP test command use that setting. The tracked defaults already name `KidsMap <info@kidsmap.az>`; the outstanding work is to verify and correct the running production container's environment, then prove delivery from the official sender.

**Tech Stack:** Django email backend, Docker Compose, Brevo SMTP relay.

**Spec:** User request, 2026-09-14 — move all KidsMap account/system emails to the official sender, with `info@kidsmap.az` as the proposed address.

## Global Constraints

- Do not print or commit SMTP credentials, `.env` contents, or recipient addresses.
- Production changes require explicit release approval; do not run deploy, restart, or mail-send commands before it.
- The verified sender/domain in Brevo must be `info@kidsmap.az` / `kidsmap.az` before production mail is sent.
- Keep the display sender exactly `KidsMap <info@kidsmap.az>`; `SERVER_EMAIL` must be `info@kidsmap.az`.

---

### Task 1: Prove the account-mail sender contract locally

**Files:**
- Modify: `src/catalog/testcases/test_password_reset.py`
- Modify: `src/catalog/testcases/auth_flow.py` only if the existing registration-code assertion no longer covers `mail.outbox[0].from_email`

**Interfaces:**
- Consumes: `settings.DEFAULT_FROM_EMAIL`, `UserPasswordResetView`, `catalog.services.email_verification._send_code`
- Produces: regression coverage that fails if either registration verification or password reset ceases to use `KidsMap <info@kidsmap.az>`.

- [ ] **Step 1: Write the failing password-reset sender assertion**

Add this to the password-reset test that posts a valid local user email, after the request:

```python
self.assertEqual(mail.outbox[0].from_email, "KidsMap <info@kidsmap.az>")
```

- [ ] **Step 2: Run the focused test to verify it fails for the intended old-sender configuration**

Run in an isolated test environment with `DEFAULT_FROM_EMAIL` temporarily set to the legacy sender only for this red check:

```bash
DJANGO_TESTING=1 DEFAULT_FROM_EMAIL='KidsMap <legacy@gmail.com>' ./.venv/bin/python manage.py test catalog.testcases.test_password_reset.PasswordResetTests -v 2
```

Expected: FAIL on the `from_email` assertion because the sender is the temporary legacy value.

- [ ] **Step 3: Keep the sender source centralized**

Do not add per-view sender strings. Confirm the password reset view leaves `from_email` unset so Django falls back to `DEFAULT_FROM_EMAIL`, and retain `from_email=settings.DEFAULT_FROM_EMAIL` in direct `send_mail()` calls.

- [ ] **Step 4: Run the focused tests with the official sender**

```bash
DJANGO_TESTING=1 DEFAULT_FROM_EMAIL='KidsMap <info@kidsmap.az>' ./.venv/bin/python manage.py test catalog.testcases.test_password_reset catalog.testcases.auth_flow.TestEmailVerificationFlow -v 2
```

Expected: PASS; password-reset and registration-code messages have the official sender.

### Task 2: Correct the production runtime sender

**Files:**
- Modify outside Git only: `/opt/kidsmap/.env` (or the authorized production secret store that supplies the Compose environment)
- Verify: `docker-compose.yml:98-110`, `src/config/settings.py:163-198`

**Interfaces:**
- Consumes: Docker Compose environment variables `DEFAULT_FROM_EMAIL` and `SERVER_EMAIL`
- Produces: an effective running Django settings value of `KidsMap <info@kidsmap.az>` for account mail and `info@kidsmap.az` for server error reports.

- [ ] **Step 1: Inspect the running web container without exposing values**

Run an approved read-only check that reports only one of `kidsmap`, `legacy_gmail`, `other`, `empty`, or `unset` for `DEFAULT_FROM_EMAIL` and `SERVER_EMAIL`.

Expected: both report `kidsmap`; otherwise proceed to Step 2.

- [ ] **Step 2: Set the two production variables in the approved secret source**

Set exactly these non-secret values:

```dotenv
DEFAULT_FROM_EMAIL=KidsMap <info@kidsmap.az>
SERVER_EMAIL=info@kidsmap.az
```

Do not change `EMAIL_HOST`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, or any provider credential as part of this task.

- [ ] **Step 3: Verify Brevo sender authorization before release**

In Brevo, confirm that `info@kidsmap.az` or the `kidsmap.az` domain is an authenticated sender identity. If it is not verified, stop: DNS/provider verification is required before a release can safely claim delivery from that address.

- [ ] **Step 4: Release only with explicit production approval**

Use the approved release workflow to recreate the web container from the updated environment. Do not use deployment scripts merely to inspect state.

### Task 3: Verify real delivery and regressions after release

**Files:**
- Verify only: `src/catalog/services/email_verification.py:49-77`, `src/catalog/views.py:2095-2110`, `src/catalog/services/account_deletion.py:221-267`, `src/catalog/services/staff_role_workflow.py:185-215`

**Interfaces:**
- Consumes: the deployed settings and verified SMTP sender identity
- Produces: production evidence that automatic account messages originate from the official address.

- [ ] **Step 1: Send one approved non-user test message**

Run the existing command with an authorized internal recipient:

```bash
./.venv/bin/python manage.py send_test_email approved-internal-recipient@example.invalid --subject 'KidsMap sender verification'
```

Expected: one delivered message showing `From: KidsMap <info@kidsmap.az>`.

- [ ] **Step 2: Exercise password reset with a designated test account**

Submit a password reset for the designated non-user test account and inspect the received message headers.

Expected: `From: KidsMap <info@kidsmap.az>`.

- [ ] **Step 3: Exercise registration confirmation with a designated test account**

Register a designated non-user test account, request its code, and inspect the received message headers.

Expected: `From: KidsMap <info@kidsmap.az>`.

- [ ] **Step 4: Record only aggregate evidence**

Record the deployed revision, the two sanitized environment classifications, and pass/fail for each delivery check. Do not record SMTP credentials, mail contents, recipient addresses, or full headers.
