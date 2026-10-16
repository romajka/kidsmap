# MOD-QA-10 — русские уведомления публикации

OPEN P3, LOCAL current WORKTREE,2026-10-16. Admin, Place queue. AZ/EN×6widths: открыть published row actions → Unpublish → подтвердить при delayed response. Факт: русский loading toast «Снятие с публикации...». Ожидание: выбранный язык.12localeFAIL transport.js.result.json, явный SIMULATED transport при настоящем JS/UI. Loading/repeat/conflict/error controls PASS. Native-publication.js.result.json дополнительно подтверждает настоящий AZ success на390: «… переведена в черновики»; источник executeTogglePublication содержит2loading+2success literals. PNG full-loading-az/en-*,full-native-draft-az-390.

P3: операция/данные работают, текст не соответствует locale. Ранее MOD06 принимал толькоconfirmation; action/toasts были NOT RUN. Не связывать с единственным renderer stall после AZ publish: он отдельно UNKNOWN, свежий AZ390repro прошёл, source stack не получен. [Concrete6file PLAN](MOD-QA-10-PLAN.md), [unapplied candidate](MOD-QA-10-proposed.diff). UI/PO/JS пока не исправлены.

Самостоятельный запрос: «KidsMap: PLAN/IMPLEMENT MOD-QA-10 внутри08. Прочитай этот finding/PLAN, учти отдельную запись о renderer incident и новые runtime/source checks. После явного approval только6files иtargeted RED→GREEN/browser, без повторного полного корпуса/модуля09/production/commit/push/deploy».
