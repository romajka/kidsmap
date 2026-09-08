# Home Rail Catalog Cards Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Render the homepage discovery rail with the same full place cards as the catalog.

**Architecture:** The homepage rail will include the canonical `catalog/includes/place_card.html` partial for every selected place. The rail owns only its heading, scrolling container and item width, while the shared partial continues to own place data, actions and card layout.

**Tech Stack:** Django templates, Django test client, existing KidsMap CSS and vanilla JavaScript.

**Spec:** User reference screenshots in this conversation, 2026-09-08.

## Global Constraints

- Preserve the existing public place query, links, favourite action and phone-reveal behavior.
- Reuse the catalog card partial; do not copy its data rules into the homepage.
- Keep the rail usable at 375px, 768px and desktop widths.

---

### Task 1: Render canonical cards in the homepage rail

**Files:**
- Modify: `src/catalog/testcases/public.py:TestPublicPagesSmoke`
- Modify: `src/catalog/templates/catalog/includes/home_places_rail.html`
- Modify: `static/css/pages/home_redesign.css`

**Interfaces:**
- Consumes: `home_rail_places` from `HomeController` and the `place_card.html` template partial.
- Produces: a `.home-rail-item` containing `.card.place-card` for each homepage rail place.

- [ ] **Step 1: Write the failing test**

```python
def test_home_rail_uses_the_catalog_place_card(self):
    place = create_quality_place(
        name="Rail card place",
        name_ru="Карточка ленты",
        category="EDU",
        is_home_recommended=True,
        phone1="+994501112233",
    )
    response = self.client.get("/ru/")
    self.assertContains(response, 'class="home-places-rail"', html=False)
    self.assertContains(response, f'data-place-id="{place.pk}"', html=False)
    self.assertContains(response, 'class="card place-card"', html=False)
    self.assertContains(response, 'class="card-go-btn"', html=False)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `DJANGO_TESTING=1 ./.venv/bin/python manage.py test src.catalog.testcases.public.TestPublicPagesSmoke.test_home_rail_uses_the_catalog_place_card -v 2`

Expected: FAIL because the homepage rail still uses the simplified `home-rail-card` markup.

- [ ] **Step 3: Write minimal implementation**

Replace the rail's custom anchor markup with `{% include "catalog/includes/place_card.html" with place=place %}` and remove CSS that styles the removed custom card internals. Set `.home-rail-item` to the catalog card width and keep its flex sizing and scroll-snap behavior.

- [ ] **Step 4: Run test to verify it passes**

Run: `DJANGO_TESTING=1 ./.venv/bin/python manage.py test src.catalog.testcases.public.TestPublicPagesSmoke.test_home_rail_uses_the_catalog_place_card -v 2`

Expected: PASS.

- [ ] **Step 5: Verify page behavior**

Run: `DJANGO_TESTING=1 ./scripts/run_kidsmap_tests.sh public`

Check `http://127.0.0.1:8772/ru/` at desktop and 375px: card image, labels, price, rating, location, "Перейти" and phone action are visible; the rail scrolls horizontally without clipping controls.
