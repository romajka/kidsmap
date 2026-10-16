# MOD-QA-09 — русский счётчик в AZ/EN

OPEN P3, LOCAL dirty WORKTREE e4e05cc/task33-progress,2026-10-16. Admin, Place/Event/Specialist, AZ/EN×6widths. Открыть очередь → поиск → «Фильтры». Ожидание: подпись количества на выбранном языке; факт: «Найдено … карточек», при этом количество/фильтры верны.36actual locale FAIL в initial+final-resume matrix. PNG full-filter-place-en-360/full-filter-event-az-1440 и остальные18target frames на каждый язык. Точные names/hashes в ../png-manifest.json.

Причина подтверждена: обе записи msgid «Найдено %(count)s карточек» в AZ/EN fuzzy с placeholder total вместо count. Fresh native compiler правильно исключает их; shared MO не использовались. P3 по ограниченному copy/UX эффекту, не повреждение фильтрации/данных. Владелец frontend-admin/localization; renderer MOD08 не причина. [Concrete3file PLAN](MOD-QA-09-PLAN.md), [unapplied candidate](MOD-QA-09-proposed.diff). Не исправлено без нового approval.

Самостоятельный запрос: «KidsMap: PLAN/IMPLEMENT MOD-QA-09 внутри модуля08. Прочитай этот finding и MOD-QA-09-PLAN.md. После явного одобрения реализуй только указанные3files, targeted RED→GREEN, fresh isolated locales/browser. Уже выполненный полный ACCEPT-08 не повторяй целиком; сохранить чужой WORKTREE/active_run/стенды. Без09модуля/production/commit/push/deploy».

Дополнительно та же причина у metadata msgid «создано»: корректные Created/Yaradılıb помечены fuzzy. Два native1440контроля вынесены в created-label-recheck.js.result.json и2PNG; pending PLAN уточнён до этих2entries в тех же2PO+newtest, candidate/manifest обновлены, application0changes.
