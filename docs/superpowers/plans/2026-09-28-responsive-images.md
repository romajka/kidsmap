# Responsive images Implementation Plan

> Execute inline in this session; scope explicitly authorized by the user's request to implement resized images and srcset/sizes. Existing push/deploy authorization persists.

**Goal:** Hero and catalog cards load correctly sized WebP derivatives while retaining originals and fallback rendering.

**Architecture:** A media service writes immutable derivatives and a small manifest keyed by source filename, size and modification time. GET rendering reads ready manifests; it never resizes or writes media. Model upload signals and an explicit management command generate files. Shared card markup replaces both the image and its blurred background, so CSS cannot download the original alongside srcset.

**Tech Stack:** Django 6, existing Pillow, FileSystemStorage, Chromium.

**Spec:** `docs/agent-audits/2026-09-28-performance.md`, PERF-01; current user instruction.

## Constraints

- Preserve originals, proportions, EXIF orientation and transparency; no upscaling. Skip animated/unsupported/corrupt images and retain fallback.
- Sizes: 320/640/960/1280 px, plus the source width when smaller than the largest size. WebP quality 80. Source bounds reuse the image upload safeguards.
- No schema/data changes; derivative command reads model references and writes new media only. Dry run performs no writes.
- Missing derivatives, unavailable storage and invalid manifests must fall back to the original instead of HTTP 500.
- Preserve concurrent homepage/CSS edits. Stage only this task's homepage changes.
- Deployment uses the existing authorization; verify the committed snapshot and production browser selection before completion.

## Task 1: Generation and rendering contracts

Files: new `services/responsive_images.py`, `testcases/test_responsive_images.py`; modify `controllers/home_controller.py`, `templatetags/catalog_i18n.py`.

- [x] RED: real temporary JPG 1600×800; home gallery serialization must expose srcset after derivative generation. Existing code must fail the output assertion.
- [x] Implement `generate_variants(image, target_storage=None) -> dict` and `responsive_image(image, target_storage=None) -> dict`: keys src, srcset, preview, width, height. Use `ImageOps.exif_transpose`, LANCZOS, source revision hash, independently stored WebP widths. Publish manifest only after files are saved. Cache successfully read immutable manifests in bounded process memory; do not cache missing manifests.
- [x] Tests: decode generated files and assert 320×160 / 640×320, original bytes unchanged, no upscale, correct EXIF orientation, missing/corrupt fallback, GET does not create files, repeated command does not regenerate variants, replaced source produces a new URL.
- [x] Connect gallery context and simple template tag. Static fallback hero images use the same generator with static source storage and media destination.

## Task 2: Markup and ongoing generation

Files: `templates/pages/home.html`, `templates/catalog/includes/place_card.html`, `signals.py`, new `management/commands/generate_responsive_images.py`.

- [x] Replace six hero picture blocks with an include rendering responsive WebP, explicit intrinsic dimensions and separate main/side sizes. Keep existing fallback picture, labels, loading and first hero fetchpriority.
- [x] Shared card: srcset/sizes and intrinsic dimensions; blurred background uses the smallest derivative. Responsive sizes account for mobile single-column catalog and home carousel.
- [x] Post-save callbacks only for Place photo/cover and SiteGalleryImage. Existing complete manifests skip encoding; errors log only exception type and retain original image.
- [x] Command defaults to dry run; `--apply` generates referenced Place/gallery/static hero derivatives. Report aggregate generated/reused/failed counts, no filenames or personal records.
- [x] Integration tests verify rendered URLs, blur URL, original fallback, upload generation and dry-run side effects.

## Task 3: Verify and release

- [ ] Run isolated `DJANGO_TESTING=1` image/home/catalog tests with temp DB/cache/media and disabled integrations.
- [ ] Build committed snapshot and check deployment diff; push task files only. Generate production derivatives before switching web image so fallback is safe; retain previous image for rollback.
- [ ] Run server checks and generation aggregate verification. Compare source byte hashes before/after generation without exporting source records.
- [ ] Chromium cold mobile/desktop checks: currentSrc points to expected derivative sizes, HTTP200, no broken images, hero/card layout preserved; compare image transfer with audit baseline.
- [ ] Record exact tests, production revision, counts, browser metrics, limitations. Do not claim a backend TTFB fix.
