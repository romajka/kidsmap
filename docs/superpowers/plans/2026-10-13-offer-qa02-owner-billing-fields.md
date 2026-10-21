# OFFER-QA-02 — Owner billing fields — Implementation Plan

> Execution: sequential in this chat after concrete scope approval. User instructions override skill defaults about delegation/commits. No commit/push/deploy/production.

**Status:** COMPLETE LOCAL — user approved this concrete five-file plan with «дальше». Only OFFER-QA-02 closed.

**Goal:** Let an owner create/save/reopen regular membership and installment group tariffs and explicitly set quantity/unit using the existing canonical pricing contract.

**Architecture:** Add missing controls to the existing owner group editor, sourcing quantity-unit enums from PricingPlan through offering_editor_choices. Keep server validation/constraints unchanged; use existing ui_copy RU/AZ/EN captions and current field serializer. Show only billing controls relevant to the selected mode, preserving unsaved values while toggling. Existing server normalization still clears irrelevant billing values upon actual save.

**Tech Stack:** Existing Django/Python/PostgreSQL/native JS/CSS, native browser QA. No dependencies/schema changes.

**Spec:** PLAN OFFER-QA-02 in docs/qa/continuation-and-repair-prompts-2026-10-11.md; historical docs/qa/module05-2026-10-10-r1/findings/OFFER-QA-02.md; fresh docs/qa/offer-qa02-recheck-2026-10-13-r1/REPORT.md.

## Exact approved-to-be scope

Only OFFER-QA-02. Do not fix OFFER-QA-03–09 or repeat01. Preserve existing dirty files and archive repair01 in pricing_plans.py. No publication/service-rule/ACL/CAS/model/constraint/public pricing changes, assertions weakening, UI redesign or unrelated localization.

Exactly5 existing application files:

1. `static/js/owner_place_offerings.js`: group plan advanced controls and billing visibility only.
2. `src/catalog/services/pricing_plans.py`: `offering_editor_choices` only, add canonical quantity_units; preserve approved complete_tree writer.
3. `src/catalog/services/permanent_place_wizard.py`: `ui_copy` only,4 new captions.
4. `locale/az/LC_MESSAGES/django.po`: exactly3 existing fuzzy unit entries Час/Месяц/Смена.
5. `locale/en/LC_MESSAGES/django.po`: same3 entries. RU entries already explicit/current; no RU PO change.

Evidence/automated rendered regression scripts: new `docs/qa/offer-qa02-fix-2026-10-13-r1/` (fresh suffix if existing); this plan status and current module05 references in two QA guides. Preserve prior reports. No new Django assertions mirroring metadata, no jsdom/source-only UI acceptance. Existing canonical pricing behavioral tests reused narrowly; saved native browser replay is the meaningful regression test for the UI gap.

## Task 1: RED and minimal integration

- [x] Snapshot current source/HEAD/branch/dirty/active_run. Reuse only verified own resources, never historical ports or another stand. Prepare a new own implementation profile with current RU/AZ/EN isolated build/sole LOCALE_PATHS before setup, own DB/cache/media/private-media/email; no .env or production credentials. Leave previous compiled profiles untouched.
- [x] Save/run positive native browser regression before patch: attempt to enter recurring count and complete save/reload. It must fail because count control is absent. Fresh recheck already records control_count0 and native recurring/installment422; preserve this RED evidence.
- [x] Extend choices using canonical model choices, without enumerating values in JS:

```python
# offering_editor_choices result only
'quantity_units': [(value, str(label))
                   for value, label in PricingPlan.QUANTITY_UNIT_CHOICES],
```

- [x] Add explicit captions to existing `ui_copy`:

```python
plan_interval_count=t('Количество периодов', 'Dövrlərin sayı', 'Number of periods'),
plan_billing_cycles=t('Количество платежей', 'Ödənişlərin sayı', 'Number of payments'),
plan_quantity=t('Количество', 'Miqdar', 'Quantity'),
plan_quantity_unit=t('Единица количества', 'Miqdar vahidi', 'Quantity unit'),
```

- [x] Replace only current billing controls block with the existing field helper integration and append quantity/unit:

```javascript
const billing = field(extra, plan, 'billing_mode', ui.plan_billing,
  'select', {choices: choices.billing_modes});
const interval = field(extra, plan, 'billing_interval', ui.plan_interval,
  'select', {choices: [['', '—'], ...choices.billing_intervals]});
const count = field(extra, plan, 'billing_interval_count',
  ui.plan_interval_count, 'number');
const cycles = field(extra, plan, 'billing_cycles',
  ui.plan_billing_cycles, 'number');
field(extra, plan, 'quantity', ui.plan_quantity, 'number');
field(extra, plan, 'quantity_unit', ui.plan_quantity_unit, 'select',
  {choices: [['', '—'], ...choices.quantity_units]});
function billingVisibility() {
  interval.closest('label').hidden = billing.value !== 'recurring';
  count.closest('label').hidden = billing.value !== 'recurring';
  cycles.closest('label').hidden = billing.value !== 'installment';
}
billing.addEventListener('change', billingVisibility);
billingVisibility();
```

Use existing input/JSON serialization and grid/classes. Do not inject count=1, quantity=1 or unit=lesson defaults to bypass required input. Numeric controls retain integer semantics. Do not add hidden required/min constraints that prevent focusing controls inside collapsed details; server remains final validator and invalid0 must be explicitly checked. If numeric step handling needs adjustment, scope it to these new integer controls only, preserving prices/ages.

Visibility: recurring shows interval/count, hides cycles; installment shows cycles, hides interval/count; one_time hides all3. Hidden values are retained in the current unsaved object so switching back before saving preserves input. Canonical server clean clears inactive values on actual saved mode; do not promise those inactive values survive a saved one_time conversion. Optional quantity/unit are always available together. Blank is no specification, not a fabricated default.

## Task 2: exactly6 PO translations and current locale proof

- [x] For AZ existing Час use `Saat`, Месяц `Ay`, Смена `Növbə`; EN `Hour`, `Month`, `Shift`. Remove fuzzy markers/obsolete previous-msgid references only on these six entries. Source refs retained. Do not edit city Гах or other tariff labels (e.g. По запросу); those remain separate scope.
- [x] Build current RU/AZ/EN via `scripts/build_isolated_locales.py` into the implementation profile's new isolated directory; verify manifest source hashes and load exactly its locale root before django.setup. No shared MO overwrite or prior profile recompilation.
- [x] Prove native Django under actual default-AZ fallback: RU remains Russian and AZ/EN hour/month/shift labels are genuine correct compiled translations. Check these shared choices in actual owner unit selector and the registered Place admin nested PricingPlan editor; no broad localization repair.

## Task 3: native persistence and targeted tests

- [x] Re-run saved positive rendered regression GREEN with native field changes/save/reload; READ ONLY readback checks candidate payload and stable tariff ID. For published Place edits, approved live stays unchanged until actual moderation. Exercise complete nested candidate approval so separate OPEN09 partial-name review is not silently patched.
- [x] Native scenarios: membership recurring month/count1 and count2; installment cycles3; lesson quantity8/unitlesson and hour quantity2; valid blank optional quantity/unit; switch recurring→installment→one_time→recurring before saving preserves unsaved count/cycles; after saved one_time, canonical interval/count/cycles are cleared. Save/reopen recurring and installment values.
- [x] Invalid0 count/cycles and mismatched quantity/unit reject saving, retain input and leave previous candidate/live version/IDs unchanged. If client HTML validation blocks a negative attempt, record that separately; prove canonical server zero rejection with a targeted own PostgreSQL test/request. Do not weaken existing assertions or perform checked transitions through ORM.
- [x] RU/AZ/EN×360/390/768/1024/1280/1440 in this editor: active/hide controls, labels, native selection/save/reload, keyboard/focus, errors/conflicts, geometry, console/network. Fresh PNG/manifest; all fixture setup fictional and distinct. No full unrelated module UI replay.
- [x] Run only existing focused methods through isolated runtime:

```text
catalog.testcases.test_task33_pricing.GroupPricingTests.test_target_scoped_roundtrip_and_foreign_ids
catalog.testcases.test_task33_pricing.GroupPricingTests.test_trial_fee_and_membership_preserve_regular_headline
```

They protect roundtrip/IDs/ACL boundaries and recurring public price semantics. Since model/business logic is unchanged, do not repeat the previous38-case repair01 suite or whole module05 after every patch. Exact command/exit/count/discovery labels recorded. Native UI RED→GREEN is the regression evidence for missing controls; backend methods are affected-contract guards, not falsely claimed failing before this UI patch.
- [x] Preserve all prior WORKTREE/active_run/common MO/stands, prove runtime source match, exact source5 diff, commands/exits/counts, screenshot hashes and NOT RUN. Close only02 with evidence. Module05 remains IN PROGRESS; full ACCEPT-05 once after its repairs, global tests later.

## Boundaries / handoff

OFFER03 wrong error focus and OFFER09 partial-name review remain OPEN, not accepted by this repair. Other missing tariff fields, other translations, public billing wording or independent defects require a separate concrete scope. If CSS changes are actually needed beyond the existing grid, present an explicit extension first; no CSS is currently included. No new approval needed inside these five specified files/entries.

Validation route clarification: standalone PricingPlan admin is not registered. The actual affected shared consumer is PlaceAdminForm.offering_choices in the Place nested pricing editor; it was checked natively on RU/AZ/EN, including real staff save/approval/reload. No application scope expansion.

[REPORT](../../qa/offer-qa02-fix-2026-10-13-r1/REPORT.md), [verification](../../qa/offer-qa02-fix-2026-10-13-r1/verification.json), [exact scoped diff](../../qa/offer-qa02-fix-2026-10-13-r1/application.diff).2 focused backend guards; native18 cells plus optional/admin/focus/console. Existing other billing/role translations remain outside exact PO scope, carried into06 recheck. Module05 full/global/production NOT RUN.
