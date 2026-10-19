# SITE14 plan — ongoing immediate-fix authorization

Fresh current-source native route.abort reproduced all3languages: DB/logs unchanged, Back goes to account/profile, reopening loses input (6failed observations). Fresh backend4methods: editable recovery marker fails, readonly/other-form/no-write controls pass.

Add per-tab, per-actor, per-form recovery for the six editable shared SiteSettings editors only. Explicit allowlist of publicly displayed text/link/boolean/number settings; never store CSRF/revision/secret/hidden/file fields. Snapshot on input/change/submit for the actual native settings Save/Continue/Exit buttons. Thirty-minute TTL, bounded data, safe storage exceptions; no automatic application or submission. Reopening offers localized Restore input / Delete draft. Restore keeps current server revision, dispatches field events, focuses recovered field. Exact matching normalized saved values on a fresh GET clear the draft; validation POST retains it. Explicit Delete draft clears it. Unconfirmed transport never yields a save success claim.

Scope: shared_settings_change_form.html; new kidsmap_settings_draft.js and scoped CSS; new4method backend regression; three new messages and existing Restore input translation in AZ/RU/EN PO, isolated current MO build. No backend save/permissions/revision/schema/file-storage changes.

Verify cumulative backend including concurrency/save-exit controls; native abort→Back→reopen→explicit recovery→retry save→reload cleanup, all3languages6widths, keyboard, actor/form isolation, validation error retention, explicit discard and actual public footer value; restore original fixture values. SIMULATED transport only; real disconnect/other browsers NOT RUN. Existing authorization covers implementation without another approval. No production/commit/push/deploy.

Source refinement: generic legacy unsaved guard does not mount on shared settings (no data-km-admin-form/#place_form). Its initial edits were restored to exact entry bytes; no new navigation modal is added. Actual native save-exit, validation, explicit draft delete and TTL are tested. Initial observer failures retained.
