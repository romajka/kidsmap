# EVENT-QA-06 — explicit RU entries prevent fallback to default AZ

COMPLETE LOCAL. Additional RU source file explicitly approved and verified.

Fresh own Django-native locale probe proves default LANGUAGE_CODE=az. Unlike plain gettext, Django falls back to default AZ when RU entries are absent. After adding AZ translations, RU currently receives AZ for «Шаги формы мероприятия», «Вперёд», «Тип организатора» and the singular/plural EventAdmin correction instruction. Browser publication-copy24 shows8 RU failures with AZ helper text; old Russian editing caption and publication reason remain correct. This is a regression introduced by the partial locale repair; must be fixed before module acceptance.

Evidence: docs/qa/module04-full-2026-10-13-r1/native-locale-proof.json; current publication-copy result/raw native PNG. Do not change LANGUAGE_CODE or mask it only in QA settings.

Checkout /home/ramin/kidsmap, task33-progress, HEAD e4e05cc213b34e2d771ecb854901bfd016d1db51 +preserved approved dirty WORKTREE, active_run NONE.

Only additional source: locale/ru/LC_MESSAGES/django.po.
- Add missing three exact msgids with identical Russian msgstr: Шаги формы мероприятия; Вперёд; Тип организатора.
- Replace existing singular-only correction-instruction entry with matching plural entry. Preserve exact msgid whitespace: `\n                Исправьте проблему ниже и сохраните мероприятие ещё раз.\n              `; msgid_plural uses «проблемы». RU msgstr[0] singular, [1]/[2] plural, with exact whitespace.
- Preserve all other RU entries and all approved AZ/EN repairs. No template/backend/settings/default-language/schema/ACL/CAS/dependency changes.

Fresh isolated RU/AZ/EN locales-v6 via helper, verify manifest/sole LOCALE_PATHS before own runtime restart. Native Django override probe must return expected own-language literals for all six Event UI messages plus singular/plural instruction. Actual browser RU/AZ/EN×360/390/768/1024/1280/1440: owner caption/navigation/organizer type accessible labels and EventAdmin full error alert; include plural cases390/1440. Check saved photo unchanged and compiled/source manifest. Preserve failed outputs; no weakened assertions and no full backend rerun. Existing141 methods retained, only affected locale cells repeated.

Own QA/report/status files permitted; no commit/push/deploy/production. This is the sole remaining confirmed locale regression; close only after actual native checks.

## Approval receipt

User: «Да, исправь RU и заверши модуль»,2026-10-13.

## Final execution handoff

COMPLETE LOCAL; authoritative report docs/qa/module04-full-2026-10-13-r1/REPORT.md and verification.json. Checkpoint hypotheses/failed probes above remain history; final7-file diff and current locales-v6 evidence take priority. No commit/push/deploy/production.
