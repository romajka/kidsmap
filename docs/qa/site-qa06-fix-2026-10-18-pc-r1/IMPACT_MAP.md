# SITE06 applied boundary and review

This applies only the approved [seven-file plan](../site-qa06-recheck-2026-10-18-pc-r1/IMPLEMENTATION_PLAN.md). The immutable plan's [impact map](../site-qa06-recheck-2026-10-18-pc-r1/IMPACT_MAP.md) records graph/source reconciliation. Entry index status reported ready51523nodes/280457edges with partial parses; it is stale for these files, so it is navigation evidence only. Applied source/hash assertions are authoritative.

|Boundary|Actual applied wiring|Verification|
|---|---|---|
|Main/gallery AJAX|`SiteGalleryImageAdmin.ajax_upload`; existing admin/permission gates first, trusted destination then `validate_site_media_upload`, existing writes afterward|Real ingress30-method tests, SITE01 controls, native matrix/authority/boundaries|
|Settings/direct analytics forms|`_SettingsRevisionForm.clean`; revision first; only new UploadedFile; add_error removes bad upload before instance construction; `_add_site_media_error` links the visible shared summary and suppresses only duplicate inline output|Forms no-write/full snapshots; stale409/preview regressions; native branding/analytics/interleaves|
|Gallery add/change forms|`_SiteGalleryMediaForm`, form assigned on existing admin and the same linked media-error helper|Real add tests, native add/change/valid retry/no-upload and SVG partner form|
|Raster bytes|Dedicated validator:88, format/extension/MIME, verify then reopen/load, caps/dimensions/animation, finally rewind|PNG/JPEG/WebP byte equality; cap edges/truncation/APNG; additional WebP/rewind edge harness|
|SVG bytes|Dedicated validator static UTF-8 profile; declaration screening then parse original document and strict namespace/tag/attribute/budget checks|Server-only malicious fixtures; XML/budget cases; safe SVG logo/partner native decode/forms|
|Generic error shell|Shared template:50, existing icon/content classes; original plural body retained|Static literal equality, native geometry/focus/ARIA/Tab and inspected PNGs|
|Existing consumers|SITE15 locks/partial saves/conflict preview; SITE01 authority; public logo; existing image derivative signal|55 pre-existing methods plus native interleaves/delete/public decode|

No changes to public/client JS, CSS, photo normalizer, models/schema, settings, dependencies, presets or old assets. Invalid input is rejected before application storage/ORM/log writes; Django's temporary multipart parsing is outside that stored-media claim. Accepted originals retain metadata/trailing bytes and alpha. This is an admin upload boundary, not a global model validator, arbitrary SVG sanitizer or file-storage transaction layer. Genuine storage I/O failures remain outside this validation contract.

Inline review by /root; no independent specialist execution claimed. SITE19's pre-existing CatalogContentSettings direct editor500 occurs before shared-template rendering; its file controls beyond that failure remain NOT RUN. SITE08 layout and SITE11 untranslated existing wrappers remain open.
