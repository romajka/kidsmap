# SOCIAL-QA-01 — Сохранённая оценка не восстанавливается в редакторе — fresh module13 corroboration

ID **SOCIAL-QA-01**, P2; root cause group **REVIEW-RATING-READBACK**. Role: outsider. LOCAL `http://localhost:8831native review forms for Place2, Activity1, Specialist1 and Event1`; checkout `C:/kidsmap`, HEAD `8d188b316f800fbedf0b1e376905dfd4924cb1b6`, dirty WORKTREE `e13c36f2af3aca03513ff860a1dee7c02a8cb2ab8214c89bcffd7dd5fe5914b1`. PRODUCTION NOT RUN.

**Steps:** Choose rating4 and fictional literal HTML text, submit pending review, reload editor.

**Expected:** Saved rating4 selected while content remains escaped.

**Actual:** Persisted candidate content survives but all four editor rating controls reopen empty. Public approved text escapes correctly.

**Fresh evidence:** [social-private.result.txt](../social-private.result.txt); [normalized matrix](../matrix.json), [screenshot manifest](../screenshots-manifest.json). [Original ID/source analysis](../../module09-2026-10-10-r1/findings/SOCIAL-QA-01.md) is historical context, not fresh runtime proof.

**Cause / confidence:** fresh trigger is confirmed; prior source analysis below is retained with attribution. Source references: src/catalog/templates/catalog/typed_reviews.html. No exact clean-HEAD UI replay for this trigger; introduction/regression date UNKNOWN. PLACE-QA-06 specifically classifies generated-runtime-assets failure; the separate donor test comparison does not change the browser runtime.

- Первопричина (source verified): `src/catalog/templates/catalog/typed_reviews.html:24`. Ни одна option не получает selected; template не читает candidate/current rating.

**Priority:** P2; bounded incorrect UI, permission surface, readback or event collection contract; no production exploitation or critical data loss proven.

**Fix scope / dependencies:** retain prior canonical source references and business contracts; review current dirty edits first. Network grant aliases share one implementation. Generated catalogs and missing source translations have different causes. [Standalone repair prompt](SOCIAL-QA-01-repair.txt). Audit findings do not authorize implementation.
