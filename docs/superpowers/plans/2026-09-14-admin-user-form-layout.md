# Admin User Form Layout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the Django Admin user change form stable and usable at 1024px, 1280px, and 1440px, especially the `user_permissions` selector, without changing user permissions or other admin forms.

**Architecture:** `HiddenBaseUserAdmin` renders `admin/catalog/user/change_form.html`; it enables Django's native `filter_horizontal` selector for `user_permissions`. The template currently also applies place-form classes (`km-place-form-*`), so the page inherits an unrelated sidebar/grid system. Remove that class coupling, make the user form's own CSS the sole layout owner, and scope selector fixes to the permissions field.

**Tech Stack:** Django Admin templates, native `SelectFilter2` permissions selector, CSS Grid, Django test runner, Playwright CLI.

**Spec:** User request, 2026-09-14 — repair the user edit form layout, rights section, desktop responsiveness, and check comparable Django Admin forms.

## Global Constraints

- Do not change models, permission assignment logic, `filter_horizontal`, routes, or JavaScript behavior.
- Keep native Django controls, labels, keyboard flow, and visible focus styles intact.
- Scope every new selector under `.km-user-profile-page`; do not modify shared place-form CSS to fix the user screen.
- Browser checks use a disposable local database and a test-only staff account; never use production accounts or production URLs.

---

### Task 1: Lock the layout boundary with a regression test

**Files:**
- Modify: `src/catalog/testcases/admin.py` near `TestAdminOwnershipModerationUX.test_user_change_form_has_no_groups_block_and_uses_profile_actions`
- Test: `src/catalog/testcases/admin.py`

**Interfaces:**
- Consumes: `admin:auth_user_change`, `HiddenBaseUserAdmin`, `admin/catalog/user/change_form.html`
- Produces: a rendered-admin regression test proving that the user form does not opt into place-form layout classes and retains the native permissions input.

- [ ] **Step 1: Write the failing test**

Add this test to `TestAdminOwnershipModerationUX`:

```python
def test_user_change_form_uses_isolated_profile_layout(self):
    response = self.client.get(
        reverse("admin:auth_user_change", args=[self.owner_user.id])
    )

    self.assertEqual(response.status_code, 200)
    content = response.content.decode("utf-8")
    self.assertIn("km-user-profile-page", content)
    self.assertNotIn("km-place-form-page", content)
    self.assertNotIn("km-place-form-layout", content)
    self.assertContains(content, 'name="user_permissions"', html=False)
```

- [ ] **Step 2: Run it and verify the red state**

```bash
DJANGO_TESTING=1 ./.venv/bin/python manage.py test catalog.testcases.admin.TestAdminOwnershipModerationUX.test_user_change_form_uses_isolated_profile_layout --noinput -v 2
```

Expected: FAIL because the current template emits `km-place-form-page` and `km-place-form-layout`.

### Task 2: Give the user form its own layout and readable permissions selector

**Files:**
- Modify: `src/catalog/templates/admin/catalog/user/change_form.html:163-351`
- Modify: `static/admin/css/pages/kidsmap_user_profile.css:34-603`

**Interfaces:**
- Consumes: existing `.km-user-*` elements and Django's `.selector`, `.selector-available`, `.selector-chooser`, `.selector-chosen` markup.
- Produces: a dedicated user form grid and a full-width, two-list permission selector on wide viewports.

- [ ] **Step 1: Remove place-form classes from the user template**

Replace every paired user/place class in the existing-user branch with its user-only equivalent:

```html+django
<div id="content-main" class="km-user-profile-page">
  <div class="km-user-profile-shell">
    <header class="km-user-hero">
      …
    </header>
    <div class="km-user-layout">
      <main class="km-user-main">
        <section class="km-user-section">
          <header class="km-user-section__head">…</header>
          <div class="km-user-section__body">…</div>
        </section>
      </main>
      <aside class="km-user-sidebar">…</aside>
    </div>
  </div>
</div>
```

Replace the place-form error and sidebar/action class names with `km-user-profile-alert`, `km-user-sidebar-card`, and `km-user-actions-group`; preserve all buttons, names, URLs, and template conditions unchanged.

- [ ] **Step 2: Add the missing user-only CSS primitives**

In `kidsmap_user_profile.css`, define the classes introduced above. Keep the shell capped at `1400px`, use `box-sizing: border-box`, and use this desktop grid:

```css
.km-user-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(288px, 320px);
  gap: 24px;
  align-items: start;
}

.km-user-section__body {
  min-width: 0;
}

.km-user-profile-alert {
  display: grid;
  gap: 4px;
  padding: 16px 18px;
  border: 1px solid var(--km-u-danger-border);
  border-radius: 12px;
  background: var(--km-u-danger-bg);
  color: var(--km-u-danger-text);
}
```

- [ ] **Step 3: Make only the permission selector wide and stable**

Add these scoped rules after the generic user field rules:

```css
.km-user-profile-page .field-user_permissions {
  min-width: 0;
}

.km-user-profile-page .field-user_permissions .selector {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 32px minmax(0, 1fr);
  align-items: center;
  gap: 12px;
  width: 100%;
  max-width: none;
}

.km-user-profile-page .field-user_permissions .selector-available,
.km-user-profile-page .field-user_permissions .selector-chosen,
.km-user-profile-page .field-user_permissions .selector select {
  min-width: 0;
  width: 100%;
}

.km-user-profile-page .field-user_permissions .selector-chooser {
  width: 32px;
  margin: 0;
  padding: 0;
  transform: none;
}
```

Do not use fixed widths for either permission list; labels and translated option names must be allowed to wrap normally within the list.

- [ ] **Step 4: Add responsive behavior without squeezing the desktop form**

Add the following breakpoints after the desktop rules:

```css
@media (max-width: 1180px) {
  .km-user-layout { grid-template-columns: minmax(0, 1fr); }
  .km-user-sidebar { position: static; }
}

@media (max-width: 700px) {
  .km-user-profile-page .field-user_permissions .selector { grid-template-columns: minmax(0, 1fr); }
  .km-user-profile-page .field-user_permissions .selector-chooser {
    display: flex;
    align-items: center;
    justify-content: center;
    width: auto;
  }
}
```

- [ ] **Step 5: Run the focused test and verify the green state**

```bash
DJANGO_TESTING=1 ./.venv/bin/python manage.py test catalog.testcases.admin.TestAdminOwnershipModerationUX.test_user_change_form_uses_isolated_profile_layout --noinput -v 2
```

Expected: PASS.

### Task 3: Check adjacent admin forms and real browser behavior

**Files:**
- Verify: `src/catalog/templates/admin/catalog/staffaccessuser/change_form.html`
- Verify: `src/catalog/templates/admin/catalog/place/change_form.html`
- Verify: `src/catalog/templates/admin/catalog/event/change_form.html`
- Verify: `src/catalog/templates/admin/catalog/region/change_form.html`

**Interfaces:**
- Consumes: test-only server, native Django Admin JS, Playwright CLI.
- Produces: evidence that the user form works at desktop widths and that other change forms remain visually isolated.

- [ ] **Step 1: Run the related Django tests**

```bash
DJANGO_TESTING=1 ./.venv/bin/python manage.py test catalog.testcases.admin.TestAdminOwnershipModerationUX catalog.testcases.test_staff_profile --noinput -v 2
```

Expected: PASS, including the existing staff-profile route and permission-boundary tests.

- [ ] **Step 2: Start a test-only local server**

Use an already provisioned disposable database URL, never a production connection:

```bash
DJANGO_TESTING=1 DATABASE_URL="$KIDSMAP_TEST_DATABASE_URL" ./.venv/bin/python manage.py runserver 127.0.0.1:8000 --noreload
```

Create and use a test-only superuser in that disposable database, then open the user change route.

- [ ] **Step 3: Inspect in a real browser**

At 1024px, 1280px, and 1440px, verify the user edit route with Playwright:

```bash
/home/ramin/.codex/skills/playwright/scripts/playwright_cli.sh open http://127.0.0.1:8000/admin/auth/user/<test-user-id>/change/ --headed
/home/ramin/.codex/skills/playwright/scripts/playwright_cli.sh snapshot
/home/ramin/.codex/skills/playwright/scripts/playwright_cli.sh screenshot --path output/playwright/admin-user-form-<width>.png
```

Acceptance: no horizontal overflow; 1280px and 1440px keep a usable right action column; 1024px uses a single readable column; the two permissions lists and their move buttons are fully visible; Save, password-change, and delete actions do not overlap the form.

- [ ] **Step 4: Verify adjacent forms without modifying them**

Open staff-user, place, event, and region change forms at 1024px and 1440px.

Acceptance: their own layouts still render; no user-only `.km-user-profile-page` rule changes their dimensions, permission controls, or actions.

- [ ] **Step 5: Check keyboard access and console**

Tab from the first field through both permission lists, add/remove controls, and Save. Confirm a visible focus indicator and no browser-console errors.
