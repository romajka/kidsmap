# ANALYTICS-QA-03 — Легитимный Origin с портом отклонён — fresh module13 corroboration

ID **ANALYTICS-QA-03**, P2; root cause group **ANALYTICS-ORIGIN-PORT**. Role: guest. LOCAL `http://localhost:8831/ru/events/track/`; checkout `C:/kidsmap`, HEAD `8d188b316f800fbedf0b1e376905dfd4924cb1b6`, dirty WORKTREE `e13c36f2af3aca03513ff860a1dee7c02a8cb2ab8214c89bcffd7dd5fe5914b1`. PRODUCTION NOT RUN.

**Steps:** Open fictional ready Place1 on localhost:8831, reveal phone and invoke native tracked phone action.

**Expected:** Accepted legitimate same-origin event;200 with documented delta.

**Actual:** Native request returns403. No Origin proxy/adapter applied; rejected delta cannot establish a recorded click.

**Fresh evidence:** [redirect-counters.result.txt](../redirect-counters.result.txt); [normalized matrix](../matrix.json), [screenshot manifest](../screenshots-manifest.json). [Original ID/source analysis](../../module12-2026-10-11-r1/findings/ANALYTICS-QA-03.md) is historical context, not fresh runtime proof.

**Cause / confidence:** fresh trigger is confirmed; prior source analysis below is retained with attribution. Source references: src/catalog/views.py. No exact clean-HEAD UI replay for this trigger; introduction/regression date UNKNOWN. PLACE-QA-06 specifically classifies generated-runtime-assets failure; the separate donor test comparison does not change the browser runtime.

Root cause: allowed_hosts удаляет port, Django url_has_allowed_host_and_scheme сравнивает полный netloc.

**Priority:** P2; bounded incorrect UI, permission surface, readback or event collection contract; no production exploitation or critical data loss proven.

**Fix scope / dependencies:** retain prior canonical source references and business contracts; review current dirty edits first. Network grant aliases share one implementation. Generated catalogs and missing source translations have different causes. [Standalone repair prompt](ANALYTICS-QA-03-repair.txt). Audit findings do not authorize implementation.
