# EVENT-QA-05 — translate EventAdmin publication validation message

COMPLETE LOCAL. Approved locale scope plus adjacent block implemented/verified; no business-rule change.

Fresh native photo-clear error AZ/EN contains Russian sentence despite localized heading and Photo/Şəkil label. PNG: docs/qa/module04-full-2026-10-13-r1/screenshots/photo-clear-verified-en-390.png and AZ counterpart. Exact own freshly compiled gettext proof: admin-message-locale-proof.json. Existing msgid is absent/untranslated in AZ/EN. This is a pre-existing locale gap exposed by corrected published-photo gate, not a server validation regression or production claim.

Checkout /home/ramin/kidsmap; task33-progress; HEAD e4e05cc213b34e2d771ecb854901bfd016d1db51 +preserved approved dirty WORKTREE; active_run NONE.

Only two source files: locale/az/LC_MESSAGES/django.po and locale/en/LC_MESSAGES/django.po. Append/update only one exact msgid; preserve earlier four module04 translations and every other entry.

```po
msgid "Нельзя опубликовать мероприятие. Обязательны для заполнения: {}"
```
AZ msgstr: `Tədbiri dərc etmək olmaz. Aşağıdakı sahələr mütləq doldurulmalıdır: {}`
EN msgstr: `The event cannot be published. Complete the required fields: {}`

Retain brace placeholder and existing RU/error rule. No template/backend/schema/ACL/CAS/dependency/test assertion change. Own QA scripts/report/guide status only. No commit/push/deploy/production.

RED: exact gettext returns original RU in AZ/EN and18 native admin error PNG show mixed copy. GREEN: new RU/AZ/EN isolated profile locales-v3 built through scripts/build_isolated_locales.py, verify manifest and sole LOCALE_PATHS before own process restart. Assert formatted message with literal Photo/Şəkil and current native alert text; repeat only affected admin error/locale cells RU/AZ/EN×360/390/768/1024/1280/1440. Keep prior backend141 accepted methods and unrelated UI matrices; no full rerun. Preserve old/shared MO and all previous evidence. Final module acceptance must explicitly close this ID or leave it OPEN.

## Approval and build receipt

User: «Да, добавь перевод и заверши модуль». Existing entry was fuzzy, not absent: replace only its translation and remove fuzzy. The first QA patch precondition assumed absent and stopped without source change; locales-v3 compiled before the corrected patch is retained unused. Final owned profile is locales-v4 (fresh current PO), not a reused output.

## Supplemental approval boundary — adjacent plural instruction

Awaiting separate approval for this addition; do not apply it based on the original one-msgid approval.

Fresh publication-copy.result.json: primary validation sentence now localized, but the same alert also displays Russian «Исправьте проблему ниже и сохраните мероприятие ещё раз.» Its plural gettext PO block has empty msgstr[0]/[1] in AZ/EN. Whole-alert Cyrillic assertion correctly fails12 language/width cells; do not weaken it.

Same two PO files, same EVENT-QA-05, no application logic or new files. Fill only that existing plural block, preserving literal newline/indentation in msgid/msgid_plural:
- AZ singular: Aşağıdakı xətanı düzəldin və tədbiri yenidən saxlayın.
- AZ plural: Aşağıdakı xətaları düzəldin və tədbiri yenidən saxlayın.
- EN singular: Fix the issue below and save the event again.
- EN plural: Fix the issues below and save the event again.

Fresh owned locales-v5; manifest verify and own runtime restart only. Repeat affected whole-alert18 cells and a two-error plural native POST on390/1440 for RU/AZ/EN, preserve raw failed cells. No backend/full test rerun. This precise adjacent block completes the same alert localization; all unrelated PO entries remain untouched.

## Supplemental approval receipt

User: «Да, переведи весь этот блок и заверши». Adjacent singular/plural block approved2026-10-13, same two PO files.

## Final execution handoff

COMPLETE LOCAL; authoritative report docs/qa/module04-full-2026-10-13-r1/REPORT.md and verification.json. Checkpoint hypotheses/failed probes above remain history; final7-file diff and current locales-v6 evidence take priority. No commit/push/deploy/production.
