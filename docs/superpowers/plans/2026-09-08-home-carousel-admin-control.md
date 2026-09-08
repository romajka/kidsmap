# Home Carousel Admin Control Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let administrators choose the exact permanent places and the number of cards shown in the homepage carousel.

**Architecture:** `SiteSettings.home_recommendations_limit` is the single persisted carousel capacity (1–24, default 4). The existing place-admin recommendation editor remains the only selection and ordering UI; its save endpoint validates the requested capacity and selected IDs atomically. The home controller reads that setting for the rail, while keeping its four-item SEO recommendation payload unchanged.

**Tech Stack:** Django models and migrations, Django admin, Django test client, server-rendered templates, vanilla JavaScript and existing admin CSS.

**Spec:** User request and carousel reference screenshot, 2026-09-08.

## Global Constraints

- Only published, public permanent places are selectable.
- The editor order is the public carousel order.
- Capacity must be 1–24; reducing capacity below selected cards must be rejected without changing the saved selection.
- Existing four-place default and public SEO payload must remain compatible.
- Use native labelled number inputs and retain keyboard controls for moving cards.

---

### Task 1: Persist and enforce carousel capacity

**Files:**
- Modify: `src/catalog/models/site.py`
- Create: `src/catalog/migrations/0104_sitesettings_home_recommendations_limit.py`
- Modify: `src/catalog/domain_admin/place.py`
- Modify: `src/catalog/controllers/home_controller.py`
- Modify: `src/catalog/testcases/admin.py`

**Interfaces:**
- Consumes: POST JSON `{ "place_ids": [int], "limit": int }` at `catalog_place_home_recommendations_save`.
- Produces: JSON `{ "ok": true, "max_items": int, "results": [...] }` and `SiteSettings.home_recommendations_limit`.

- [ ] **Step 1: Write the failing end-to-end test**

```python
def test_admin_can_expand_carousel_and_home_uses_that_limit(self):
    response = self.client.post(
        reverse("admin:catalog_place_home_recommendations_save"),
        data=json.dumps({
            "place_ids": [place.pk for place in self.places],
            "limit": 5,
        }),
        content_type="application/json",
    )

    self.assertEqual(response.status_code, 200)
    self.assertEqual(response.json()["max_items"], 5)
    home = self.client.get("/ru/")
    self.assertEqual([place.pk for place in home.context["home_rail_places"]], [place.pk for place in self.places])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `DJANGO_TESTING=1 ./.venv/bin/python manage.py test src.catalog.testcases.admin.TestAdminHomeRecommendations.test_admin_can_expand_carousel_and_home_uses_that_limit -v 1`

Expected: FAIL with HTTP 400 because the endpoint currently hard-codes a maximum of four places.

- [ ] **Step 3: Write minimal implementation**

Add `home_recommendations_limit` as a validated positive small integer to `SiteSettings`, migration default 4. Make `save_home_recommendations_view` validate 1–24, reject excess selected IDs, persist the setting and selected order in one transaction, and return the effective limit. Read that setting for the home rail; continue using four cards for `popular_places` SEO data.

- [ ] **Step 4: Run test to verify it passes**

Run: `DJANGO_TESTING=1 ./.venv/bin/python manage.py test src.catalog.testcases.admin.TestAdminHomeRecommendations.test_admin_can_expand_carousel_and_home_uses_that_limit -v 1`

Expected: PASS.

### Task 2: Expose capacity in the existing place-admin editor

**Files:**
- Modify: `src/catalog/templates/admin/catalog/place/change_list.html`
- Modify: `src/catalog/templates/admin/catalog/place/home_recommendation_editor.html`
- Modify: `static/admin/js/kidsmap_home_recommendations.js`
- Modify: `static/admin/css/pages/kidsmap_home_recommendations.css`
- Modify: `src/catalog/testcases/admin.py`

**Interfaces:**
- Consumes: `home_recommendation_editor.max_items` from the changelist context.
- Produces: `data-home-recs-limit` input; save payload always contains the current `limit`.

- [ ] **Step 1: Write the failing rendered-admin test**

```python
response = self.client.get(reverse("admin:catalog_place_changelist"))
self.assertContains(response, 'data-home-recs-limit', html=False)
self.assertContains(response, 'value="4"', html=False)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `DJANGO_TESTING=1 ./.venv/bin/python manage.py test src.catalog.testcases.admin.TestAdminHomeRecommendations.test_place_list_renders_visual_home_recommendation_editor -v 1`

Expected: FAIL because the editor contains no capacity input.

- [ ] **Step 3: Write minimal implementation**

Add a labelled `type="number"` input with `min="1"`, `max="24"`, helper text and current setting. Update the accordion summary dynamically. In JavaScript, reject a reduction below selected cards before sending; otherwise save the limit with the card IDs and restore the previous value after a failed request.

- [ ] **Step 4: Run tests to verify behavior**

Run: `DJANGO_TESTING=1 ./.venv/bin/python manage.py test src.catalog.testcases.admin.TestAdminHomeRecommendations -v 1`

Expected: PASS.

### Task 3: Verify runtime and responsive admin UI

**Files:**
- No production files.

- [ ] **Step 1: Run migration and Django checks**

Run: `DJANGO_TESTING=1 ./.venv/bin/python manage.py makemigrations --check --dry-run && DJANGO_TESTING=1 ./.venv/bin/python manage.py check`

- [ ] **Step 2: Inspect the editor in a browser**

At 1440px and 768px, check the current count, capacity input, add/remove controls, drag order, keyboard move buttons and visible focus states. At 375px, check that the input and buttons remain reachable and no horizontal overflow is introduced.

- [ ] **Step 3: Check browser console**

Expected: no JavaScript errors after opening the editor and changing capacity.
