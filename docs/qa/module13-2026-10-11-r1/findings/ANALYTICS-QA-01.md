# ANALYTICS-QA-01 — Staff без model permission читает общую статистику — fresh module13 corroboration

ID **ANALYTICS-QA-01**, P2; root cause group **GLOBAL-ANALYTICS-ACL**. Role: staff. LOCAL `http://localhost:8831/admin/catalog/siteanalytics/`; checkout `C:/kidsmap`, HEAD `8d188b316f800fbedf0b1e376905dfd4924cb1b6`, dirty WORKTREE `e13c36f2af3aca03513ff860a1dee7c02a8cb2ab8214c89bcffd7dd5fe5914b1`. PRODUCTION NOT RUN.

**Steps:** Same permissionless staff opens site analytics.

**Expected:** Model-authorized access only;403.

**Actual:** 200 with global analytics surface.

**Fresh evidence:** [acl-native.result.txt](../acl-native.result.txt); [normalized matrix](../matrix.json), [screenshot manifest](../screenshots-manifest.json). [Original ID/source analysis](../../module12-2026-10-11-r1/findings/ANALYTICS-QA-01.md) is historical context, not fresh runtime proof.

**Cause / confidence:** fresh trigger is confirmed; prior source analysis below is retained with attribution. Source references: src/catalog/domain_admin/site.py. No exact clean-HEAD UI replay for this trigger; introduction/regression date UNKNOWN. PLACE-QA-06 specifically classifies generated-runtime-assets failure; the separate donor test comparison does not change the browser runtime.

Root cause: changelist_view не вызывает model permission check; admin wrapper проверяет лишь active staff.

**Priority:** P2; bounded incorrect UI, permission surface, readback or event collection contract; no production exploitation or critical data loss proven.

**Fix scope / dependencies:** retain prior canonical source references and business contracts; review current dirty edits first. Network grant aliases share one implementation. Generated catalogs and missing source translations have different causes. [Standalone repair prompt](ANALYTICS-QA-01-repair.txt). Audit findings do not authorize implementation.
