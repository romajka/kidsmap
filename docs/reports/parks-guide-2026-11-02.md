# Parks guide — local review, 2026-11-02

## Scope and snapshot

User authorized the first of five parent guides: all Baku including outer districts, AZ/RU/EN, useful search-oriented content and generated illustrated assets with animation. Publication remains subject to user review. Implemented only the parks guide.

LOCAL HEAD: `b7659e79a25d2ae8d23cd505ec46755683223c09`, branch `codex/admin-draft-recovery-2026-10-26`. Application changes are uncommitted WORKTREE. Existing unrelated 72-line addition to `docs/agent-audits/MASTER_AUDIT.md` preserved. No production data/schema/config edits, deployment, commit or push.

Preview: http://127.0.0.1:8766/ru/parents/parks/ (AZ `/parents/parks/`, EN `/en/parents/parks/`). Dedicated local container `kidsmap-qa-parks-20261102`, PostgreSQL 17, network disabled; separate Unix socket, test DB and preview DB. Runtime and evidence under `.tmp/parks-guide-20261102/`; no credentials inherited. Cache/mail/media/locales isolated, integrations/analytics disabled.

## Delivered

- New `PARKS_GUIDE`, complete natural AZ/RU/EN editorial copy. Six FAQ and two illustrated outing scenarios. No fabricated publication date, attendance, rankings or amenities.
- Six featured places plus a complete deduplicated directory of currently public Baku parks, grouped into native district disclosures. Address and price come from shared public presentation. Full content remains in server HTML; keyboard and no-JS access are retained.
- Category-and-district catalog links, internal links from home and existing Baku guide, related link back to the broader guide.
- Unique titles/descriptions, one H1, clean canonical, reciprocal language alternatives and x-default, automatic localized sitemap entries, Article/BreadcrumbList matching visible copy. Existing safe JSON-LD serializer retained; no fake rating or promise of FAQ rich results.
- Three generated editorial illustrations, four optimized WebP files including responsive hero. Total stored WebP bytes: 469366. Hero loads eagerly; below-fold assets lazily. Existing short reveal animation extended to new sections; reduced-motion respected. Native disclosures avoid a long mobile list.

Intent hypotheses: parks/playgrounds in Baku; parks by district; free admission versus paid extras; walking with a stroller; seaside walks; playground suitability. These are editorial intent groups, not measured search volumes. One substantial page covers related questions; no duplicated keyword pages. Search Console/query volume and live ranking changes NOT RUN.

## Data and sources

Read-only HTTPS GET of two public category pages and all 17 published park cards on 2026-11-02. Local preview uses their public names/descriptions/addresses/price labels/photos; schedules copied from their public JSON-LD solely for local visibility. No private records copied. This is a preview snapshot, not a live synchronization or a new production publication. Tests use fictional isolated fixtures.

Primary references consulted: [Azerbaijan Travel, Baku Boulevard](https://azerbaijan.travel/feel-bakus-mediterranean-atmosphere-stroll-along-the-boulevard-19909), [Boulevard administration FAQ](https://www.bulvar.gov.az/ru/questions). General SEO guidance: [Google helpful content](https://developers.google.com/search/docs/fundamentals/creating-helpful-content), [localized pages](https://developers.google.com/search/docs/specialty/international/localized-versions). Venue amenities were not independently inspected.

Open source-data issue: botanical garden card 311 has conflicting district text and structured district. The parks guide groups botanical gardens separately and omits their district and description teaser, retaining name/address/price/link. Original catalog record is unchanged. No recommendation of Zirya picnics or currently operating rides; existing card records restrictions. Age 0+ is not treated as playground-equipment eligibility.

Asset paths and exact built-in generation prompts: `docs/reports/parks-guide-assets-2026-11-02.json`. Artwork is editorial; at user request, redundant illustration disclaimers are omitted from the page and image descriptions. Public park photos remain separate.

## Verification

RED: new parks tests failed on the missing route before implementation. Unknown-price fixture initially lacked a valid public tariff and was correctly excluded; corrected fixture to an active `on_request` tariff, preserving assertions and visibility rules. Botanical district leakage reproduced in both teasers, then suppressed. District deep-link JS test failed before extending hash handling.

Final Django command:

```sh
.venv/bin/python .tmp/parks-guide-20261102/runner.py test catalog.testcases.test_parks_guide catalog.testcases.test_parent_guides catalog.testcases.test_home_parent_intent catalog.testcases.test_seo_indexability catalog.testcases.test_seo_landing_visibility --noinput --keepdb
```

PASS: 54 tests, 31.054 seconds, exit 0 (`accepted-tests.log`). Includes public/hidden/outside-city selection, outer Baku, complete directory beyond six featured cards, unknown/free/free-entry distinctions, disabled taxonomy, localized metadata/alternates/sitemap/query cleanup, previous parent/home guides and representative SEO contracts.

```sh
NODE_PATH=/home/ramin/kidsmap/.tmp/phone-dom/node_modules node --test scripts/tests/parent_guide_links.test.cjs
.venv/bin/python .tmp/parks-guide-20261102/runner.py check
git diff --check
```

PASS: 9 Node checks, Django check, whitespace check. First Node invocation without NODE_PATH could not resolve the already installed jsdom; explicit existing dependency path resolved it, no installation/source alteration.

Browser: Chromium through Playwright CLI, real DOM/screenshots. Public preview has 17 directory entries, six featured places. Interaction acceptance: 25 local destination links HTTP 200, district hash opens disclosure, FAQ keyboard/deep-link behavior, reduced-motion, no-JS directory/disclosures; no console/network errors (`browser-interactions2.log`). Initial interaction harness checked hashchange before dispatch and reused an already-open FAQ on same-document navigation; corrected harness waits for open state and starts from a new document. No product change was needed for those harness timings.

Responsive acceptance PASS: 39 states — 21 parks states (three languages, seven viewport widths from 320 to 1440 px) and 18 home/sport/Baku-guide regression states. No overflow, page errors or failed responses. Evidence: `responsive-final.log`; screenshots: `output/playwright/parks-20261102/`. Desktop/mobile screenshots visually inspected after scrolling to load lazy artwork/photos. Physical devices/Safari, full project suite, production rendering/deployment, Google indexing/ranking/traffic NOT RUN.

## Next step

User reviews the first page and requests any edits. Publication is separate; set `published` only on actual first release and verify deployed multilingual HTML, sitemap/static assets and Search Console afterward. Do not start the other four guides automatically.
