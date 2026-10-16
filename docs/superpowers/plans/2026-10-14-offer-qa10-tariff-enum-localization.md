# OFFER-QA-10 Tariff Enum Localization Implementation Plan

**Goal:** Nine shared tariff/group system choices render in RU/AZ/EN without Russian fallback in AZ/EN.
**Architecture:** Correct only existing gettext entries for the enumerated nine msgids. Business enum codes and canonical pricing/ACL/CAS/candidate/live contracts stay intact. Rebuild and verify current PO only in the owned QA profile before Django setup.
**Tech Stack:** Django gettext, GNU msgfmt, existing isolated-locale helper, native Chromium.
**Spec:** `docs/qa/module05-full-2026-10-14-r1/FINDINGS.md`, OFFER-QA-10; current native `enum-localization.result.json`1PASS/2FAIL.

## Authorization and exact scope

APPROVED2026-10-14 by user «закончи окончательно».18AZ/EN entries repaired; RU unchanged. Locale finding CLOSED LOCAL, full module05 FAIL due new OFFER11; see docs/qa/offer-qa10-fix-2026-10-14-r1/REPORT.md. Full-module request authorizes recheck and completion of already approved repairs, not expansion into these explicitly excluded locale entries. Sequential root, no delegation. No commit/push/deploy/production. Preserve concurrent foreign changes, active_run NONE and other stands. A prior module06 locale task is unrelated.

Only application files permitted:
- `locale/az/LC_MESSAGES/django.po`
- `locale/en/LC_MESSAGES/django.po`
- `locale/ru/LC_MESSAGES/django.po`

Only the nine msgids below: eighteen AZ/EN translations and Russian identity coverage for the same nine where missing/fuzzy/obsolete. Already effective RU entries stay byte-preserved. Keep contexts, placeholders, other translations and metadata. Clear fuzzy only for these entries. If an existing target RU entry is obsolete, reactivate that same record rather than creating a compiler-rejected active/obsolete duplicate; preserve its original in QA incoming snapshot. No broad PO rewriting or unrelated duplicate cleanup.

| msgid | AZ | EN | RU |
|---|---|---|---|
| Абонемент | Abunə | Membership | Абонемент |
| Лагерь | Düşərgə | Camp | Лагерь |
| Тур | Tur | Tour | Тур |
| Дополнительная услуга | Əlavə xidmət | Additional service | Дополнительная услуга |
| Точная цена | Dəqiq qiymət | Exact price | Точная цена |
| Диапазон | Qiymət aralığı | Price range | Диапазон |
| По запросу | Sorğu əsasında | On request | По запросу |
| Год | İl | Year | Год |
| Индивидуальный | Fərdi | Individual | Индивидуальный |

QA/docs: new own `docs/qa/offer-qa10-fix-2026-10-14-r1/` (choose a fresh suffix if occupied), this plan progress, module05 acceptance supplement, scoped status links and own ignored profile. No Python/business/template/JS/CSS/schema/dependency/common MO changes. Foreign duplicate `Редактировать карточку` causing final RU compile failure is outside scope: verify whether its author has resolved it; if still present, report blocker, do not bypass manifest gate or edit it.

## Task 1 — exact baseline and catalog repair

- [x] Re-read snapshot/dirty/active_run and preserve all current foreign PO edits. Save incoming copies/hashes outside secrets, compare named entries only; inspect fuzzy/context/obsolete status. Keep native RED1PASS/2FAIL.
- [x] Set exact translations above, preserve target enum code values and all non-target entries. No assertion weakening or bulk fuzzy removal.
- [x] Build RU/AZ/EN through `scripts/build_isolated_locales.py` into a new owned locale directory. A compilation failure is BLOCKED, not PASS. Verify manifest against current PO; set sole LOCALE_PATHS before django.setup. Never overwrite shared MO.

## Task 2 — targeted locale and native checks

- [x] Real Django override/gettext and `offering_editor_choices` in own READ ONLY transaction: all nine labels×three languages, including RU default-AZ fallback protection and exact enum code preservation. Ensure previous OFFER06 role/billing/status captions still translate. No hand-maintained fake serializer as proof.
- [x] Native owner and admin tariff/group editors RU/AZ/EN×360/390/768/1024/1280/1440. Open affected selectors and actual advanced fields; options/labels do not clip/overflow; keyboard Tab/Shift+Tab/Space/Enter/Escape and focus work. Save/reload a fictional affected enum choice through the real user transition; verify READ ONLY codes and price/candidate/live preservation. Do not use ORM for the tested save.
- [x] Fresh PNG/manifest, console/network, exact commands/exits/counts and runtime/source binding. External services disabled/SIMULATED as declared. Repeat only affected locale/browser checks and the previous failed localization diagnostic. Reuse334 backend results with unchanged Python/test hashes; do not rerun entire module corpus for this PO-only patch.

## Task 3 — acceptance supplement and handoff

- [x] Minimal three-PO diff with only scoped entries. Refresh verification/report and full ACCEPT05 supplement: close OFFER10 only if native/locale checks pass and runtime/current locales bind. Keep original full audit FAIL and compile/drift/harness evidence.
- [x] Reconcile remaining NOT RUN/foreign input blockers. Full-module current PASS requires evidence; do not declare production/global completion. Offer module06 PLAN only after module05 acceptance closes, do not start it automatically.

Progress:84real Django checks and432native caption/keyboard checks/36cells PASS;4native owner save/reload checks PASS. Actual admin Select2 selection/save/reload revealed separate OFFER11, so that task remains incomplete and full module05 is FAIL. Final runtime rejected stale catalogs after foreign PO drift; no bypass. All334backend methods not rerun. New one-JS PLAN11 awaits approval.

Final2026-10-14: OFFER11 CLOSED LOCAL; module05 ACCEPT LOCAL PASS, docs/qa/module05-full-2026-10-14-r2/REPORT.md.505native accepted checks/36cells/45PNG, fresh15READONLY and84locale checks;334corpus reused,6projection methods repeated for proven foreign helper extraction. Final runtime/source/sole fresh locales MATCH. Old failures kept, no module06 started.
