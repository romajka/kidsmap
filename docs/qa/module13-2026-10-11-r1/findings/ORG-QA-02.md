# ORG-QA-02 — владелец не может отозвать сетевой доступ через кабинет — fresh module13 corroboration

ID **ORG-QA-02**, P2; root cause group **NETWORK-GRANT-UI**. Role: owner. LOCAL `http://localhost:8831/ru/account/organizations/1/`; checkout `C:/kidsmap`, HEAD `8d188b316f800fbedf0b1e376905dfd4924cb1b6`, dirty WORKTREE `e13c36f2af3aca03513ff860a1dee7c02a8cb2ab8214c89bcffd7dd5fe5914b1`. PRODUCTION NOT RUN.

**Steps:** Invite fictional employee EDITOR/all_network; recipient accepts via notifications; then find native revoke action in organization team.

**Expected:** Existing network employee permissions can be revoked through authorized cabinet.

**Actual:** UI contains invitation/refresh controls but no employee or grant revoke action. Detach does remove effective branch-editor rights; this is a separate successful check.

**Fresh evidence:** [cross-effects.result.txt](../cross-effects.result.txt); [normalized matrix](../matrix.json), [screenshot manifest](../screenshots-manifest.json). [Original ID/source analysis](../../module02-2026-10-09-r1/findings/ORG-QA-02.md) is historical context, not fresh runtime proof.

**Cause / confidence:** fresh trigger is confirmed; prior source analysis below is retained with attribution. Source references: src/catalog/templates/pages/organization_workspace.html. No exact clean-HEAD UI replay for this trigger; introduction/regression date UNKNOWN. PLACE-QA-06 specifically classifies generated-runtime-assets failure; the separate donor test comparison does not change the browser runtime.



**Priority:** P2; bounded incorrect UI, permission surface, readback or event collection contract; no production exploitation or critical data loss proven.

**Fix scope / dependencies:** retain prior canonical source references and business contracts; review current dirty edits first. Network grant aliases share one implementation. Generated catalogs and missing source translations have different causes. [Standalone repair prompt](ORG-QA-02-repair.txt). Audit findings do not authorize implementation.
