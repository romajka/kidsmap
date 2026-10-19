# SITE06 bounded impact / source verification

Lead: django-reviewer responsibilities with security-reviewer/integration-reviewer/browser checks executed sequentially by /root. No independent delegation claimed.

Codebase Memory project C-kidsmap matches C:/kidsmap; ready51523nodes/280457edges,120partial parses. Freshness generation is not exposed by current File nodes (only name/qualified_name/label/file_path properties); current-content coverage is UNKNOWN. Search reports ajax_upload at986, actual source at1067; get_code_snippet returned a different current range. Trace includes ambiguous save/get edges to unrelated modules/docs; these are rejected as impact evidence. Graph is navigation only, not a source-of-truth snapshot. Current-source hashes and bounded actual wiring below are authoritative. No graph cache copied into this package.

|Producer/boundary|Verified consumer/sink|Plan impact|
|---|---|---|
|`static/admin/js/kidsmap_site_media.js` real file input/drop|`SiteGalleryImageAdmin.get_urls` → admin_view → ajax_upload|JSON400 is already handled by restoring preview/status/removing loaders; retain JS, note Russian wrappers as SITE11|
|ajax main-image field|SiteSettings row lock → save(update_fields=[field,updated_at]) → cache clear → public logo/hero fields|Validate before writes, preserve SITE01 authority and SITE15 partial-write/lock semantics|
|ajax gallery placement|SiteGalleryImage.objects.create → post_save signal → responsive_images.generate_variants|Validate known placement/content before create, so bad files never reach derivative work|
|Six visible proxy settings forms and direct analytics editor|_SettingsRevisionForm.clean → _post_clean → ModelAdmin save/log|Validate NEW file values after revision check, field errors before instance construction; stale409 remains first|
|Gallery add/change ModelForms|SiteGalleryImageAdmin → gallery file save/log/signal|New file validation form; leave no-upload/old references/deletion alone|
|Public templates/context SiteSettings logo|`img src` media path → browser decode|Native proof200/success with naturalWidth0 after corrupt upload, then decode recovery after valid upload|
|Shared error template|Existing form shell CSS icon/content grid at473/475|Generic heading currently30px and overlaps; wrap generic error content with existing classes; source/site15 conflict branch preserved|
|Existing image_uploads.py photo normalizer|Owner/place/account workflows, WebP flatten/encode and HEIF support|Do not reuse/modify: different art/vector/transparency contract|
|CatalogContentSettings shared-template consumer|Model __str__ TypeError before rendering|SITE19 stays OPEN; native controls beyond exception NOT RUN; no model/admin-class change|

No DB/schema/model/dependency change. New source modules only after approval: dedicated validator+new regression file; root cohort would grow1029→1031. No publication, pricing, schedule, SEO, routes, staff presets or data cleanup change. Candidate restrictions are proposed policy; confirmed corruption acceptance is current AS-IS. Manual/non-admin ORM writers remain outside this admin-upload boundary.
