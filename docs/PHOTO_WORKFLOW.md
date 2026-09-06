# Owner photo workflow

The permanent-place wizard prepares photos sequentially through an authenticated, CSRF-protected endpoint. Preparation returns WebP without writing temporary media records or files to persistent storage. The final save uses the existing owner controllers, permissions and transactions. Failed saves retain selected files in the browser; a request ID prevents an ordinary retry from creating a second place.

## Limits and memory

- Sources: JPG, PNG, WebP, HEIC/HEIF/HIF; 15 MiB per file, 50 million pixels and 12000 pixels per side.
- Prepared photo: WebP, longest side at most 2400 px, at most 2 MiB.
- Main photo plus at most 10 gallery photos: at most 22 MiB in the final form request. Nginx retains its 25 MiB body limit, leaving room for fields and multipart framing. Preparation sends only one original at a time, so a gallery of large HEIC originals does not become one oversized request.
- Browser previews: at most 320 px, with object URLs released when removed. Existing photo previews come from an authenticated thumbnail endpoint. Browsers do not decode the original HEIC or a full-resolution camera image for preview.
- Server processing checks dimensions before decoding, reads the uploaded file directly, reduces before orientation/color conversion, and avoids the extra full-resolution encoding copy.

On a controlled 6000×4000 JPEG in separate Windows processes, peak working set was 392.1 MiB for the previous normalizer and 209.1 MiB for the updated normalizer; output was 6902 bytes in both runs. Processing time was 0.885 s versus 0.604 s. This is one synthetic image, not a guarantee for all formats or concurrent traffic.

The reduction order follows the [Pillow thumbnail documentation](https://pillow.readthedocs.io/en/stable/reference/Image.html) and [in-place EXIF orientation API](https://pillow.readthedocs.io/en/stable/reference/ImageOps.html). Unneeded HEIF thumbnails are disabled according to the [pillow-heif plugin guidance](https://github.com/bigcat88/pillow_heif/blob/master/docs/pillow-plugin.rst).

## Interaction

Files accumulate across selections and drops. SHA-256 detects repeated selected content, including renamed files; prepared-file hashes also reject duplicates within the current selection. No perceptual matching or historical-original fingerprint database is introduced.

Each photo shows queued, uploading/processing, ready-to-save, saved or error state. Invalid files have named messages; transient preparation errors can be retried. Gallery photos can be reordered with arrow buttons or dragging. Making a gallery photo main swaps the previous main into that slot. Existing gallery order and deletion IDs are validated on the server before persistence.

Text-only browser drafts never restore stale photo ordering or deletion flags. Reloading still requires reselecting photos that were not saved; submission errors do not reload the form.

## Deployment and verification

`pillow-heif==1.5.0` was already pinned in requirements and is now installed in the local environment. The Docker build checks decoder registration after installing dependencies. Rebuild/restart the web service and publish the updated static assets together. No database migration is required.

Run the photo tests with:

```text
python manage.py test catalog.testcases.photo_workflow catalog.testcases.image_uploads catalog.testcases.permanent_place_wizard --noinput
npm install --prefix .tmp/phone-dom --no-save --package-lock=false jsdom
node --test scripts/test_photo_editor.cjs
```

DOM tests cover accumulation, duplicates, limits, file drop, ordering buttons, promotion, retries, fallback preview support and failed replacement recovery. When `.tmp/photo-form.html` exists, they also exercise the photo editor inside HTML rendered by Django, including stale browser-draft recovery. Canvas/decoding and network are platform test doubles; server image conversion tests use actual image files, including HEIC.

Final focused verification: 48 Django tests passed, including the updated 15 MiB photo-limit contract. Eight photo-editor DOM tests and three phone-reveal DOM regression tests passed. Django system and JavaScript syntax checks passed. The expanded owner run initially reported an unrelated password-reset email assertion; a final isolated recheck of that test also passed with the current workspace.

Native browser visual/mobile verification was unavailable in this session. No production deployment was performed.
