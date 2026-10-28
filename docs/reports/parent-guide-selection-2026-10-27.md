# Baku guide: duplicate cards and free admission

27 October 2026, Asia/Baku. APPROVED IMPLEMENT: user requested both corrections and supplied production access. Work performed sequentially by the current agent.

LOCAL HEAD: fab76031, branch codex/admin-draft-recovery-2026-10-26, initially dirty. The controller already contained an unpublished price-summary fix; it was preserved and incorporated. Unrelated changes were retained. PRODUCTION base: 97cb7825d, image kidsmap:published-place-search-20261027-97cb7825d47b. Base controller file matched the active image before changes.

Changes: only src/catalog/controllers/parent_guides.py was published. Tests added to src/catalog/testcases/test_parent_guides.py locally. No migrations, catalog record writes, static changes, commit or push.

Cause: venue records 207 and 320 identify the same museum (same multilingual names and official site, approximately 86 m between coordinates). Guide deduplication formerly used only database PKs. Free FAQ formerly filtered Place.price_mode=free, missing parks whose canonical tariff summaries report free while price_mode=tariffs.

Fix: group guide candidates only when normalized name/category/website match and coordinates are within 150 m; missing coordinates require an identical nonempty address. Keep separate branches with different locations. Apply this to the six-card selection and FAQ, filling vacant slots from remaining candidates. Free FAQ uses the existing public card price summary, with three links maximum. Published/active/local visibility and existing taxonomy filters remain in force. Duplicate catalog records remain stored; this is display deduplication, not a data merge. Near-identical venues without matching names and websites are intentionally not collapsed.

Evidence and tests:

- Production read-only SQL transactions used explicit READ ONLY, statement_timeout=20s, lock_timeout=2s. No private records or credentials were exported.
- RED against the unchanged production controller: duplicate test failed in AZ/RU/EN with two museum records instead of one; free-tariff test failed in AZ/RU/EN with [] instead of three parks. Initial fixture validation errors were corrected before the final RED run.
- Local PostgreSQL isolation: DJANGO_TESTING=1 before setup, cleared environment, disposable test_guide_selection_20261027 database, LocMem cache/email, scratch media, external integrations disabled. Fixture coordinates for an outside-Baku record were assigned directly because current local location validation resolves published fixtures from coordinates.
- GREEN command: `/home/ramin/kidsmap/.venv/bin/python .tmp/guide-fix-20261027/runner.py test catalog.testcases.test_parent_guides catalog.testcases.test_home_parent_intent --noinput --keepdb` — exit 0, 29 tests, 0 failures/errors. Logs: .tmp/guide-fix-20261027/green.log. This disposable test DB was retained under --keepdb.
- New release image: `docker run --rm --network=none -e DJANGO_TESTING=1 -e DJANGO_DEBUG=1 -e DJANGO_SETTINGS_MODULE=config.settings kidsmap:parent-guide-selection-20261027-r1 python manage.py check` — exit 0, no issues.
- Candidate code exercised against production data before activation in a read-only transaction, with rendering replaced by context inspection to avoid request tracking. AZ/RU/EN assertions passed.
- Live health 200. Guide, sport guide and homepage: 9/9 HTTP 200 across AZ/RU/EN. Canonical remains the corresponding guide URL; robots remains index,follow. 12 representative localized venue links returned 200.
- Real browser: AZ/RU/EN at widths 390/768/1024/1280/1440. Six distinct venue links; three free park links; FAQ expands; no horizontal overflow, broken images or captured console errors. Browser viewport reset after checks. Evidence: .tmp/guide-fix-20261027/browser-verification.json and free-faq-production.jpg.
- Current selection: Rasulzade Park, National Museum of Art (207), Moka Kids Zefir Mall, Baku Zoo, Ganjlik Park, Tusi-Bohm Planetarium. Free FAQ: Rasulzade Park (81), Ganjlik Park (205), Nizami Ganjavi Park (206).

Release/recovery:

- Active image: kidsmap:parent-guide-selection-20261027-r1 (d5d16cf8820c), built FROM the previously active image with only this controller copied in.
- Active image and local controller SHA256: 3bf9c0e778bbdfbe856d37c8c72c41bed56dce8321aeede63e2a6ddb01ef6e01.
- Server source /opt/kidsmap/src/catalog/controllers/parent_guides.py updated to match. Production checkout has only that file modified. Base Git revision remains 97cb7825d; GitHub was not updated. Future Git-only releases need to include this patch.
- Previous image retained. Previous controller, compose override and image name are retained server-side under /opt/kidsmap-releases/20261027-parent-guide-selection/. Overrides were kept server-side with mode 0600 and were not printed/copied into local artifacts.
- Activation used docker compose with the production base file and release override, `up -d --no-deps --no-build web`. Startup only checks migration readiness. Rollback would restore parent_guides.before.py and recreate web with previous.override.json. No rollback was needed; rollback execution was NOT RUN.

NOT RUN: full-project suite, production DB mutation/migration tests, Google recrawl or Search Console ranking verification. These results establish corrected page content, not a change in which URL Google chooses for any query.
