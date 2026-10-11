# PLACE-QA-06 — Скомпилированные переводы этого WORKTREE устарели — fresh module13 corroboration

ID **PLACE-QA-06**, P2; root cause group **COMPILED-LOCALE-FRESHNESS**. Role: admin. LOCAL `http://localhost:8831/admin/catalog/place/2/change/ and /en/admin/catalog/place/2/change/`; checkout `C:/kidsmap`, HEAD `8d188b316f800fbedf0b1e376905dfd4924cb1b6`, dirty WORKTREE `e13c36f2af3aca03513ff860a1dee7c02a8cb2ab8214c89bcffd7dd5fe5914b1`. PRODUCTION NOT RUN.

**Steps:** Open AZ and EN admin Place forms at all six widths on the attested native runtime.

**Expected:** Map-disabled explanatory message uses active language.

**Actual:** 12 cells show Russian message. Active correct AZ/EN PO entries exist, compiled runtime MO keys are absent. Runtime assets unchanged; historical isolated-builder repair claim does not prove they were selected on this PC.

**Fresh evidence:** [browser-review/locale-check.result.json](../browser-review/locale-check.result.json); [normalized matrix](../matrix.json), [screenshot manifest](../screenshots-manifest.json). [Original ID/source analysis](../../module01-2026-10-09-r2/findings/PLACE-QA-06.md) is historical context, not fresh runtime proof.

**Cause / confidence:** fresh trigger is confirmed; prior source analysis below is retained with attribution. Source references: locale/az/LC_MESSAGES/django.mo, locale/en/LC_MESSAGES/django.mo. No exact clean-HEAD UI replay for this trigger; introduction/regression date UNKNOWN. PLACE-QA-06 specifically classifies generated-runtime-assets failure; the separate donor test comparison does not change the browser runtime.

**Первопричина / уверенность:** locale/az/LC_MESSAGES/django.mo, locale/en/LC_MESSAGES/django.mo; config LOCALE_PATHS. Подтверждены GNUTranslations lookup, source .po и git ignore. Уверенность высокая; это не доказательство дефекта текущих .po или production.

**Priority:** P2; bounded incorrect UI, permission surface, readback or event collection contract; no production exploitation or critical data loss proven.

**Fix scope / dependencies:** retain prior canonical source references and business contracts; review current dirty edits first. Network grant aliases share one implementation. Generated catalogs and missing source translations have different causes. [Standalone repair prompt](PLACE-QA-06-repair.txt). Audit findings do not authorize implementation.
