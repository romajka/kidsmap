# Public organizations directory — local verification

Source: LOCAL HEAD `2da9d33abbc53d1ac71bcb7e15a0170bef6277d5` plus this uncommitted WORKTREE. User authorized separate public organizations page. Design status: awaiting_user_review. Production not tested or changed; no commit/push.

## Behavior

`/organizations/`, `/ru/organizations/`, `/en/organizations/`: published, approved, nonarchived organizations; name/description search; canonical persisted district filter; 12 cards per page. Zero-branch organizations remain visible. Counts, districts and photos only use active, published, nondeleted places with current confirmed affiliation ownership versions. Photographs are labelled as branch photos; no organization logos, aggregate ratings or prices are invented. Desktop/mobile menu, footer, detail backlink, sitemap and language-switch query whitelist integrated. Filtered directory pages use noindex,follow and clean canonical URLs.

## Automated evidence

Exact final command:

```sh
PATH="$PATH:/snap/bin" python3 docs/task33/qa04/run.py --output /tmp/kidsmap-org-directory-acceptance --label catalog.testcases.test_organization_directory --label catalog.testcases.test_task33_public_details --label catalog.testcases.test_seo_indexability --label catalog.testcases.test_localized_place_urls
```

43/43 tests PASS, Django checks clean. QA runner uses isolated PostgreSQL/cache/media and guards; owned disposable container removed. Full historical suite NOT RUN.

RED run: `/tmp/kidsmap-org-directory-red`, missing directory route failed all five initial contracts. During development, two raw Unicode test URLs were corrected to use Client query encoding (existing canonical-query middleware returns 301); two additional test fixtures were corrected to establish persisted district explicitly and resolve locale-prefixed URLs under the matching translation context. Assertions remain substantive: district search must return exactly one organization; hidden branches/photos must disappear.

Browser: RU/AZ/EN × widths 320,390,768,1100,1199,1200,1280,1440: 24 contexts PASS, four cards, every branch thumbnail decoded, no horizontal/header overflow, no page JS errors or local HTTP errors. Discovered desktop navigation overflow at1100 on RU/AZ; mobile header breakpoint changed from1099 to1199 and retested on both sides. Authenticated demo-owner header: RU/AZ/EN × widths1199,1200,1280,1440, 12 additional contexts PASS with no overflow. Form search and empty state PASS. Mobile menu → district/search → EN switch retaining filters → detail with10 branches → directory backlink → input focus PASS.

Ignored local evidence: `.tmp/org-directory-browser.json`, `.tmp/org-directory-browser.log`, `.tmp/org-directory-interactions.log`, `.tmp/org-directory-auth-check.log`, `.tmp/org-directory-1440.png`, `.tmp/org-directory-390.png`. The preview synthetic database was preserved: three new demo networks each have10 branches; existing demo organization has2.

## Manual acceptance

1. Open http://localhost:8780/ru/organizations/ or choose Organizations in the main menu.
2. Inspect each card: photos, name, description, districts, branch count and link. Open each new demo network; confirm10 branch cards and return with All organizations.
3. Search Точка роста; expect one card. Select Ясамальский; expect the same network. Search a nonexistent name; expect an empty state. Reset filters; expect all four organizations.
4. Change language with filters active; search and district remain selected. Inspect AZ/EN labels and localized descriptions.
5. At320/390px open the mobile menu and choose Organizations. Inspect wrapping, controls, photo crops and the absence of horizontal scrolling. At1200px inspect desktop navigation.
6. Use Tab and Enter for filters and organization links; focus outline must remain visible.

Known unrelated baseline: RU specialist detail map JavaScript syntax failure from localized decimal coordinates remains outside this page's scope. Directory browser checks are green; this report does not declare all website flows green.
