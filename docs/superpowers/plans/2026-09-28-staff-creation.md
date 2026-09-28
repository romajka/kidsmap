# Staff creation validation implementation plan

**Goal:** Return an email field validation error rather than HTTP 500 when a new staff account uses an existing user's email.

**Authorization:** User explicitly requested this fix and staff creation regression checks. Local implementation only; production remains read-only. No commit, push, deployment or migration.

**Architecture:** StaffAccessUser is a proxy of auth.User. Migration 0101 creates a database-only unique index on LOWER(TRIM(email)) for nonempty email. The admin creation form does not currently validate this index. Keep the existing role, permission and profile workflows.

**Files:** `src/catalog/domain_admin/user.py`, `src/catalog/testcases/test_staff_creation.py`.

- [x] Reproduce duplicate email HTTP 500 with a real admin POST; test failed with `IntegrityError` on `kidsmap_user_email_ci_unique` for both creators and three case/whitespace variants.
- [x] Add `clean_email()` to StaffAccessUserCreationForm: strip email, compare against LOWER(TRIM(auth_user.email)), raise a translated email field error if taken, allow empty email as the existing index does.
- [x] Run creation and validation regressions on isolated SQLite and PostgreSQL 17, with `DJANGO_TESTING=1`, local cache/email/media and no production credentials.
- [x] Verify two superadmins can create moderator, content manager and volunteer; verify profile, password, role audit, groups and permissions. Verify GET in AZ/RU/EN and invalid username/email/password/role errors; verify limited staff cannot create accounts.
- [x] Record production evidence and verification limits. Existing logs show seven POST 500s, GET 200s; original exception traceback is absent from retained container output. Read-only production form accepts a duplicate email; production database contains the unique index. This establishes a concrete defect, not the input behind every historical 500.

Implementation:

```python
def clean_email(self):
    email = self.cleaned_data.get("email", "").strip()
    if email and User.objects.annotate(
        normalized_email=Lower(Trim("email")),
    ).filter(normalized_email=email.lower()).exists():
        raise ValidationError(_("Пользователь с таким email уже существует."), code="unique")
    return email
```

Acceptance: valid staff creation still succeeds; duplicate email produces HTTP 200 with an email validation error and no new User/Profile/role audit. No schema changes. Concurrent insertion after validation remains a separate database race requiring transactional handling if expanded into scope.
