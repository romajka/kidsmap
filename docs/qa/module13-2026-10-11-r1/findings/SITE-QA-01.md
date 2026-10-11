# SITE-QA-01 — Staff без model permissions меняет глобальный логотип — fresh module13 corroboration

ID **SITE-QA-01**, P1; root cause group **GLOBAL-MEDIA-ACL**. Role: staff. LOCAL `http://localhost:8831/admin/catalog/sitegalleryimage/ and ajax-upload/`; checkout `C:/kidsmap`, HEAD `8d188b316f800fbedf0b1e376905dfd4924cb1b6`, dirty WORKTREE `e13c36f2af3aca03513ff860a1dee7c02a8cb2ab8214c89bcffd7dd5fe5914b1`. PRODUCTION NOT RUN.

**Steps:** Staff actor has0 model permissions. Open global media editor, upload fictional PNG through its native chooser, reload and visit home.

**Expected:** 403 and no global media write.

**Actual:** Page200, upload200 and public logo changes; current synthetic stand only.

**Fresh evidence:** [acl-native.result.txt](../acl-native.result.txt); [normalized matrix](../matrix.json), [screenshot manifest](../screenshots-manifest.json). [Original ID/source analysis](../../module10-2026-10-10-r1/findings/SITE-QA-01.md) is historical context, not fresh runtime proof.

**Cause / confidence:** fresh trigger is confirmed; prior source analysis below is retained with attribution. Source references: templates/MO, src/catalog/domain_admin/site.py. No exact clean-HEAD UI replay for this trigger; introduction/regression date UNKNOWN. PLACE-QA-06 specifically classifies generated-runtime-assets failure; the separate donor test comparison does not change the browser runtime.

**Первопричина / гипотеза:** Подтверждено: custom changelist_view обходит super при отсутствии placement; AJAX handlers не проверяют has_change_permission. admin_site.admin_view допускает активный staff, но не добавляет model-level authorization.

**Priority:** P1; permissionless staff can alter shared branding, so the effect crosses object ownership.

**Fix scope / dependencies:** retain prior canonical source references and business contracts; review current dirty edits first. Network grant aliases share one implementation. Generated catalogs and missing source translations have different causes. [Standalone repair prompt](SITE-QA-01-repair.txt). Audit findings do not authorize implementation.
