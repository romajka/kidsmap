# ACCESS-QA-03 — управление сотрудниками сети отсутствует в кабинете — fresh module13 corroboration

ID **ACCESS-QA-03**, P2; root cause group **NETWORK-GRANT-UI**. Role: owner. LOCAL `http://localhost:8831/ru/account/organizations/1/`; checkout `C:/kidsmap`, HEAD `8d188b316f800fbedf0b1e376905dfd4924cb1b6`, dirty WORKTREE `e13c36f2af3aca03513ff860a1dee7c02a8cb2ab8214c89bcffd7dd5fe5914b1`. PRODUCTION NOT RUN.

**Steps:** Repeat ORG-QA-02 network employee-management inspection.

**Expected:** Native grant management under current ACL/CAS contract.

**Actual:** Same missing surface as ORG-QA-02; preserve both historical IDs, count one cause and one repair scope.

**Fresh evidence:** [cross-effects.result.txt](../cross-effects.result.txt); [normalized matrix](../matrix.json), [screenshot manifest](../screenshots-manifest.json). [Original ID/source analysis](../../module07-2026-10-10-r1/FINDINGS.md) is historical context, not fresh runtime proof.

**Cause / confidence:** fresh trigger is confirmed; prior source analysis below is retained with attribution. Source references: src/catalog/templates/pages/organization_workspace.html, static/js/organization_workspace.js. No exact clean-HEAD UI replay for this trigger; introduction/regression date UNKNOWN. PLACE-QA-06 specifically classifies generated-runtime-assets failure; the separate donor test comparison does not change the browser runtime.

- Подтверждённая причина: `src/catalog/templates/pages/organization_workspace.html:462` и `:482` отображают grants/invitations без management forms; `static/js/organization_workspace.js:301` обрабатывает invite. Серверные `grant`, `cancel`, `confirm` существуют в business-team API/service.

**Priority:** P2; bounded incorrect UI, permission surface, readback or event collection contract; no production exploitation or critical data loss proven.

**Fix scope / dependencies:** retain prior canonical source references and business contracts; review current dirty edits first. Network grant aliases share one implementation. Generated catalogs and missing source translations have different causes. [Standalone repair prompt](ACCESS-QA-03-repair.txt). Audit findings do not authorize implementation.
