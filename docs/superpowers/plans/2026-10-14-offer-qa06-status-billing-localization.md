# OFFER-QA-06 Status and Billing Localization Implementation Plan

**Goal:** Убрать подтверждённый русский fallback четырёх status badge строк в AZ/EN и шести перенесённых из OFFER02 role/billing captions.
**Architecture:** Только точечное изменение gettext каталогов. Существующий helper собирает current PO в собственный изолированный профиль; sole LOCALE_PATHS устанавливается до django.setup. Бизнес-статусы и price enum values остаются неизменными.
**Tech Stack:** Django gettext, existing PO catalogs, GNU msgfmt, native browser.
**Spec:** docs/qa/module05-2026-10-10-r1/findings/OFFER-QA-06.md; docs/qa/offer-qa06-recheck-2026-10-14-r1/REPORT.md; inherited tariff-caption gap in docs/qa/offer-qa02-fix-2026-10-13-r1/REPORT.md:47.

## Authorization / exact bounds
APPROVED IMPLEMENT completed locally2026-10-14, including explicit pending-label addition. See docs/qa/offer-qa06-fix-2026-10-14-r1/REPORT.md. Sequential root; no delegated work required. No commit/push/deploy/production; preserve dirty WORKTREE, active_run and existing stands. No test assertion changes or backend/full suite reruns.
Only OFFER-QA-06 and the same gettext catalog cause documented for role/billing captions in OFFER02. Other IDs excluded.
Application files allowed:
- `locale/az/LC_MESSAGES/django.po`: add the first four missing entries, correct/confirm the last six existing fuzzy entries and remove fuzzy only for these six.
- `locale/en/LC_MESSAGES/django.po`: same exact ten msgids.
- `locale/ru/LC_MESSAGES/django.po`: add Russian identity msgstr only for the first four msgids, preventing default-AZ fallback into incomplete RU catalog. Six billing/role RU entries are already correct and remain unchanged.
Exactly24 locale entries across3files. Existing owner/verification translations already working stay unchanged. No broad reformatting, mass fuzzy removal, other enum captions, tab/model/link headings, backend, JS, templates, shared MO, dependency/build/deployment changes. Same msgid Registration fee is shared by product_type/charge_role: check both consumers.

## Approved translation values proposed

| msgid | AZ | EN |
|---|---|---|
| Публикация занятия: %(status)s | Məşğələnin dərc statusu: %(status)s | Activity publication: %(status)s |
| Условия подтверждены | Şərtlər təsdiqlənib | Conditions verified |
| Условия не подтверждены | Şərtlər təsdiqlənməyib | Conditions not verified |
| Отдельный статус проверки не установлен | Ayrıca yoxlama statusu təyin edilməyib | No separate verification status |
| Основной | Əsas | Primary |
| Дополнительный | Əlavə | Additional |
| Регистрационный взнос | Qeydiyyat haqqı | Registration fee |
| Разовая оплата | Birdəfəlik ödəniş | One-time payment |
| Регулярная оплата | Müntəzəm ödəniş | Recurring payment |
| Оплата частями | Hissə-hissə ödəniş | Payment in installments |

Preserve exact `%(status)s` placeholder and formatting flags. No user-entered names are translated. New RU entries use msgstr equal to msgid.

## Task 1 — Catalog repair and focused acceptance
- [x] Recheck checkout HEAD/branch/dirty/active_run, incoming PO hashes and runtime-source binding. Use own unique LOCAL QA profile/fixtures; no .env/production credentials or foreign process control. Keep raw recheck evidence.
- [x] Preserve RED: current verified locale runtime gives source fallback for10 listed msgids in AZ/EN;9 native Program/Activity/Group390 cells have6 AZ/EN FAIL. Existing owner/ownership labels correctly translated, so no stale-MO-only repair.
- [x] Patch only24 catalog entries above; no changes to other incoming edits or business enum values.
- [x] Build fresh RU/AZ/EN via scripts/build_isolated_locales.py into own new ignored directory with native msgfmt; run manifest verify, enforce sole LOCALE_PATHS before django.setup. Record PO/MO hashes, helper hash and exits. Never overwrite common MO.
- [x] Targeted native Django gettext checks for exact translations/placeholder across3languages; inspect role/billing choices plus product_type registration_fee through real service, not a hand-maintained fake choice implementation. Keep RU identity coverage to guard cross-language fallback. Native compiler checks, no backend suite.
- [x] Native Program/Activity/Group status tabs RU/AZ/EN ×360/390/768/1024/1280/1440. Fixture variants cover conditions verified/unverified, draft/pending/published/rejected labels; existing ownership labels remain correct. Full labels readable inside readonly/tab bounds after locale text expansion; keyboard tabs/focus unchanged.
- [x] Native owner tariff advanced section: three languages, affected role and one-time/recurring/installment options, dropdown opening/selection, existing code values unchanged. Shared registration_fee product option also checked. Save/reload fictional candidate and explicit READ ONLY readback with timeouts verifies live data untouched. Inactive billing behavior not reimplemented. Compare user text with system labels; unrelated form headings excluded and documented.
- [x] Record console/network, screenshots/PNG hashes, exact commands/exits/counts, incoming-WORKTREE diff/preservation, runtime and locale receipts. If all scoped checks pass, close only OFFER06 and update scoped status links. Full ACCEPT05/global/external/production NOT RUN. Native UI supplement only when a changed source/failure/gap requires it.

QA/document scope: new `docs/qa/offer-qa06-fix-2026-10-14-r1/`, this plan progress, scoped links in docs/qa/continuation-and-repair-prompts-2026-10-11.md and docs/qa/module-acceptance-prompts.md; own ignored `.tmp` profile. Historical reports retained. Wider locale cleanup requires another scope; do not hide it inside this plan. Next finding07 only after user selects it.

## Additional scope APPROVED — uncontexted pending label

Fresh status-diagnostic.txt and variants.result.json prove AZ/EN pending badges still render Russian «На проверке». Existing active PO entry uses `msgctxt "volunteer admin"`; PublicationState uses ordinary gettext without context. Original plan incorrectly treated the existing contextual entry as applicable. Native4cells FAIL; real Django/model choices confirm missing ordinary translation, not stale MO.

Proposed addition only: add active context-free msgid «На проверке» to the same3PO files, msgstr RU «На проверке», AZ «Yoxlamadadır», EN «Under review». Preserve contextual volunteer entry and obsolete history. Total becomes27 locale entries. No business/model/JS changes. Rebuild only own fresh locale directory/profile; verify real gettext + Activity.get_status_display; repeat only four failed pending cells plus RU pending guard, retain passed unchanged targeted evidence with source provenance. No full suite rerun. User explicitly approved this addition on2026-10-14;27locale entries authorized.

Completion note: RU ordinary pending entry reactivated from obsolete identity record because GNU msgfmt rejects duplicate definitions; original preserved in incoming-ru.po/Git history.27entries,350native+60Django assertions,3READONLY cells,96acceptedPNG. Full module/global/production NOT RUN.
