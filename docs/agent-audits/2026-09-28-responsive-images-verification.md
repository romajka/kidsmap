# Responsive photos: implementation and production verification

Date: 2026-09-28. Executor: `/root`, direct execution, no delegated reviews. Authorized scope: resized photos and responsive markup, with existing push/deploy authorization. Runtime code revision: `5c4909e29b5d4718c9c8d1378b006009cd0d0c1d`.

## Change

WebP derivatives are generated at up to 320/640/960/1280 px, without upscaling. Source revision includes filename, modification time and byte size; URLs change on source replacement. EXIF orientation and aspect ratio are respected; animated/corrupt/oversized sources retain original fallback. Original files are never overwritten.

Rendering reads pre-generated manifests and does not resize or write files. Hero markup and shared catalog/home cards use srcset/sizes and intrinsic dimensions. Card blur backgrounds also use small derivatives, avoiding a simultaneous download of the original. New Place photo/cover and SiteGalleryImage saves prepare variants; an explicit command generates existing photos and static hero defaults. No new dependencies, schema, environment or web-server config changes.

Concurrent `home.html`/`home_redesign.css` changes were preserved in LOCAL WORKTREE and excluded from this release. The committed home template contains only this task's six photo-block replacements; the partial index was checked against the remaining worktree diff.

## Tests

RED: existing HomeController gallery serialization lacked `image_srcset`, producing the expected assertion failure. The hero include test initially failed because the new include did not exist.

Isolated PostgreSQL 17 container `kidsmap-responsive-test-pg`, bound only to 127.0.0.1:55438; test-only authentication, no production DB/cache/email/integration credentials. `DJANGO_TESTING=1`, temporary media, LocMem cache/email, external integration keys disabled. Runner `/tmp/kidsmap-staff-test-runner.py` inserts the real src directory before Django setup and selects an isolated test DB. The direct manage.py invocation initially selected the historical root config wrapper and could not import config.test_runner; the isolated runner avoids that wrapper.

Commands (test DB URL uses test-only credentials):

```sh
DJANGO_TESTING=1 DJANGO_DEBUG=1 DATABASE_URL=postgresql://postgres:test-only@127.0.0.1:55438/postgres KIDSMAP_STAFF_TEST_DB=test_responsive_pg .venv/bin/python /tmp/kidsmap-staff-test-runner.py catalog.testcases.test_responsive_images catalog.testcases.test_home_public_metrics
DJANGO_TESTING=1 DJANGO_DEBUG=1 DATABASE_URL=postgresql://postgres:test-only@127.0.0.1:55438/postgres KIDSMAP_STAFF_TEST_DB=test_responsive_ru .venv/bin/python /tmp/kidsmap-responsive-ru-runner.py catalog.testcases.image_uploads
DJANGO_TESTING=1 DJANGO_DEBUG=1 DATABASE_URL=postgresql://postgres:test-only@127.0.0.1:55438/postgres KIDSMAP_STAFF_TEST_DB=test_responsive_catalog .venv/bin/python /tmp/kidsmap-staff-test-runner.py catalog.testcases.catalog.PublicSlugTests catalog.testcases.test_catalog_expansion_banner
```

Results: **15 + 14 + 5 = 34 passed**, no skips. Existing image-upload tests were run with explicit Russian language in their isolated runner because three assertions require Russian error substrings; the initial combined run under default AZ exposed that assumption. A new card-test fixture initially omitted the required category and was corrected by creating a real Category/Place; assertions were retained. No production assertion was weakened. Full repository suite was not rerun for this scoped image change.

Coverage: decoded output widths/aspect ratio, originals unchanged, no upscale, EXIF, repeatability, replacement URLs, corrupt/animated/missing derivative fallback, rendering without file writes, upload callbacks, dry run/apply, rendered hero metadata and card blur URLs. Python compilation and git diff --check passed.

## Deployment and media

- Production began clean at `3092e9b0`; code was pushed and fast-forwarded to `5c4909e2`.
- Built web image: `sha256:d4e23a28ce954676c73d63db2972c4ae56f0e2e567a0c863bb2f11ac111ab51e`.
- Previous running image retained as `kidsmap-web:rollback-responsive-20260928`.
- Generation ran in a one-off container before replacing the web service. Model references were read inside READ ONLY PostgreSQL transactions with 15s statement / 2s lock timeout; encoding happened after closing the transaction.
- First APPLY: sources=282, generated=279, failed=3. **281 existing originals SHA256-checked before/after; all unchanged.**
- Remaining original fallbacks: one missing source, two beyond the 12000 px / 50 MP source safety bounds. No source file was deleted or altered to resolve these legacy references.
- Second APPLY: ready=279, generated=0, failed=3. **908 WebP files**, derivative directory about **37 MB**. Small originals have fewer sizes because they are not upscaled.
- Only web container was recreated, started 08:36:45 UTC. No migrations, database updates, Redis changes or static collection were needed for this release.
- Eight changed runtime files were compared against the running container by SHA256; all matched committed source.
- Django check --deploy completed with existing configuration warnings security.W009/W019/W021; this task did not alter security configuration. The build/check output remains private in `/opt/kidsmap-releases/20260928-responsive-images/`.

## Browser and HTTP evidence

Chromium CLI, a dedicated browser session, actual production. Cold mobile comparison uses 390×844, DPR1 and cleared browser cache. ResourceTiming sum includes transferred headers; cross-origin resources without timing access can undercount. This is a short laboratory sample, not field p75/p95 or a simulated slow phone/network.

| Cold home metric | Audit baseline | After |
|---|---:|---:|
| All resource transfer | 12,302,994 bytes | 944,614 bytes |
| Image-initiated transfer | 11,659,054 bytes | 300,674 bytes |
| Resource requests | 87 | 87 |
| load event | 13.25 s | 6.44 s |

Image-initiated transfer decreased **97.4%**, total resource transfer **92.3%** in these samples. CSS image transfers are included in the total rather than the image-initiated subtotal. Baseline source: `2026-09-28-performance.md`, E5. Backend TTFB remains about 2.4–2.7 s in public curl measurements; this release does not claim to resolve the backend bottleneck.

Cold desktop 1280×900: all resources 970,390 bytes, image-initiated 325,892 bytes, load 6.13 s. Hero main displayed about 298 px and loaded a 320 px derivative. Mobile hero main displayed 180 px and loaded a 320 px derivative. At DPR2, hero selected 640 px variants; mobile catalog selected 960 px variants for 376 px cards when source resolution allowed, and retained the capped 334 px size for an originally small photo.

AZ/RU/EN hero images loaded; no broken images in the checked pages. The first six catalog cards loaded after scrolling into view. Native lazy loading defers additional foreground card images. Mobile document width equals viewport width (390 px); desktop decorative overflow remains outside this task (1290 px document at a 1280 px viewport in the sample). Screenshots were visually inspected at mobile/desktop widths; photo proportions/layout preserved. Browser console errors: zero; the home page retains a Google Maps warning.

HTTP: health, main, catalog, RU/EN home all 200. A generated WebP was 200, Content-Type image/webp, public max-age=604800, nosniff. Desktop/mobile currentSrc consistently points to derivative URLs.

LCP was 6.95 s in the after sample versus 5.06 s in the audit sample: **no LCP improvement claim**. The carousel changes slides every 5s and animations/late candidates can affect the observed result; isolating their contribution was not part of this image-transfer change. Load-event and transfer improvements above are measured, not an SLA guarantee.

## Recovery and limits

Rollback: run the prior retained web image; originals and old markup URLs remain intact. Derivatives are additive and need not be deleted. Private release receipt records aggregate results only, without file/user records or secrets.

Not tested: real devices/3G, field Core Web Vitals, peak traffic, exhaustive gallery/detail/account pages, every legacy image or color-profile comparison. Two oversized source files and one missing reference remain fallback cases; other performance recommendations from the audit have not been implemented.
