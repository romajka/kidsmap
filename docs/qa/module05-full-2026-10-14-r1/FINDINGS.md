# ACCEPT-05 findings, 2026-10-14

Sequential root; LOCAL fictional own PostgreSQL/Chromium only. Incoming dirty WORKTREE preserved. No independent agents or production evidence.

## OFFER-QA-10 — untranslated shared tariff enum captions (OPEN, P3)

Actor owner; EN/AZ `/account/places/2/edit/?fresh=1` on this run's isolated stand. Native saved Activity/Group/Plan, open tariff panel; `Price kind` displays Russian `Точная цена`. Real rendered select options and server-delivered `pc-offering-choices` expose the same nine missing captions in both AZ and EN:

`Абонемент`, `Лагерь`, `Тур`, `Дополнительная услуга`, `Точная цена`, `Диапазон`, `По запросу`, `Год`, `Индивидуальный`.

Expected: application choices use selected UI language while business enum codes stay unchanged. Actual: eighteen untranslated options across two languages. Fictional names/content are excluded. Source: `catalog.services.pricing_plans.offering_editor_choices`, `PricingPlan`/`OfferingGroup` lazy gettext labels; existing AZ/EN PO entries are fuzzy or missing effective translations. GNU msgfmt excludes fuzzy suggestions. This is current PO content, not simply stale shared MO: own fresh validated v2 catalogs reproduce it. Earlier OFFER06 intentionally covered11msgids and documented unrelated enum captions outside its approved scope.

Evidence: [native three-language diagnostic](enum-localization.result.json), [EN viewport](screenshots/enum-localization-en-390.png), [AZ viewport](screenshots/enum-localization-az-390.png), [locale v2 manifest](locale-manifest-v2.json), [initial native EN observation](screenshots/final-consumers-en-390-owner-viewport.png). Native diagnostic1PASS/2FAIL, pageerrors0. Data saves and all334 backend methods pass; severity P3 is user-facing language inconsistency, not price/ACL corruption. Confidence HIGH for owner; admin uses the same serializer, fresh rendered admin acceptance is still required after repair.

Exact proposed plan: [2026-10-14-offer-qa10-tariff-enum-localization.md](../../superpowers/plans/2026-10-14-offer-qa10-tariff-enum-localization.md). Only these nine msgids in RU/AZ/EN PO; no logic/JS/schema/common MO. Await concrete scope approval. Full ACCEPT05 is FAIL until repaired/rechecked; OFFER01–09 scoped closures remain bounded evidence.

## Concurrent input/runtime blocker — separate from module defect

Foreign admin/ownership-preview and PO files changed repeatedly while this audit ran. None were written/reverted by this task. [Initial drift](concurrent-foreign-drift.json), [later drift](concurrent-drift-at-final.json), [subsequent drift](concurrent-drift-after-last-refresh.json). Full runtime/source receipts are phased; a prior MATCH does not prove later foreign edits.

Final `build_isolated_locales.py build` into own `locales-v3` exited1: copied RU PO duplicate `Редактировать карточку`, first obsolete definition and new active definition, msgfmt line18248/20808 in that copied source. Evidence [compiler output](locale-final-build-v3.txt), [command](locale-final-build-v3.command.json). This source belongs to concurrent foreign changes; no fix, normalization or obsolete-history deletion attempted. An incomplete manifest must not launch Django. Final own runtime refresh exited1 and process exited; own PostgreSQL retained; foreign processes untouched. Later foreign edits may resolve this: verify current source and build a new unique catalog before reusing any stand. Do not bypass locale verification or reuse stale MO.

This is an input/environment blocker, not another demonstrated module05 business regression. It does not erase earlier executed checks, and blocks any current full PASS. New repair is scoped to OFFER-QA-10; duplicate foreign entry is outside that plan.

Follow-up: foreign RU source changed after that failure, so a new owned v4 build passed exit0 ([command](locale-report-build-v4.command.json)). It changed again before startup: strict `verify` rejected stale catalog ([diagnostic](runtime-v4-failure.txt), [startup](report-runtime-v4.command.json) exit1). Thus the initial duplicate is historical; final blocker is ongoing concurrent PO drift/current runtime unavailable. No verification bypass, no further build/restart loop.
