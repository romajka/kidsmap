# ORG-QA-05 — LOCAL SCOPED ACCEPTED

2026-10-13 Asia/Baku. Root, kidsmap-orchestrator `.agents/agents/kidsmap-orchestrator/agent.md`, последовательное исполнение, не independent review. Scope одобрен ответом «да делай» на два дополнения. [Authorization](authorization.json), [точный план](../org-qa03-fix-2026-10-13-r1/PLAN-ORG-QA-05.md).

## 1. Состояние области

P2 ORG-QA-05 закрыт LOCAL. В существующее `.km-columns-details` в `static/admin/css/pages/kidsmap_changelist.css` добавлена единственная строка `margin-left: auto`. После переноса кнопка остаётся справа, её dropdown шириной170 не выходит слева за viewport; global overflow не скрывался, таблица/transport/ACL не менялись.

Checkout `/home/ramin/kidsmap`, task33-progress, HEAD e4e05cc213b34e2d771ecb854901bfd016d1db51 +dirty WORKTREE, active_run NONE. [Entry](entry.json), [current snapshot](entry-final.json). Только свой новый runtime/DB/profile; чужие source/assertions/processes/evidence сохранены.

## 2. Сильные стороны / RED→GREEN

RED до fix: [native baseline comparison](../org-qa03-fix-2026-10-13-r1/columns-baseline.result.json), RU390 dropdown x=-31.296875; baseline CSS hash совпадает с entry, проблема существовала до ORG-QA-03. Mouse checkbox был вне viewport. После patch [browser.result.json](browser.result.json): **66PASS,0FAIL,0pageerrors,0localnetwork errors**. 36 open-popup cells RU/AZ/EN×360/390/768/1024/1280/1440×sidebar transitions,18reload states и12affected shared consumers (Event/Specialist/PlaceOwnershipRequest/PlaceReview×3langs). Native mouse hide/restore, keyboard Space hide/restore, focus и реальные bounds проверены; selected-column preference сохраняется после reload. Checkbox фокус виден светло-зелёным halo в оригинальных PNG; outline:none отдельно не означает невидимый focus. [PNG manifest](png-manifest.json) —36 оригинальных screenshots, без изменения их pixels.

## 3. Реальные проблемы

Подтверждённая причина исправлена; новых findings в scope не обнаружено. Исторические wrong selector/timeout attempts и temporary addStyleTag proposal не переписаны и не подменяют новый GREEN.

## 4. Tech debt

Shared toolbar/columns layout остаётся существующим; глобальный редизайн не делался.

## 5. Risks / isolation

Собственный runtime/URL/PID в [server.json](server.json), startup/disk source match [runtime-version-final.json](runtime-version-final.json); own DB orgqa05_20261013_r1, только свой PG17.10 loopback127.0.0.1:35715. DJANGO_TESTING=1, unique cache/media/private-media/email/cookies/browser. Fresh isolated RU/AZ/EN [manifest](locale-manifest.json) build/verify exit0, sole LOCALE_PATHS before setup, no .env/production credentials/shared MO overwrites. Новые DB cloned только из собственного fictional QA. Никаких old stand restarts/stops.

## 6. Dead/legacy

Не исследовано и ничего не удалено.

## 7. Tests gaps / NOT RUN

CSS mirror tests не добавлялись. Обязательные server/shared contracts проверены в едином248-test module02 run; общий проектный корпус и real external integrations/production NOT RUN. Внешние fonts blocked и явно отражены в console ledger, console не объявляется пустым.

## 8. Handoff

Scope закрыт. Общий module02 вывод/сохранность/current hashes/commands/exits в [финальном REPORT](../module02-full-2026-10-13-r2/REPORT.md) и verification. Module03 автоматически не запускался.

## 9. Приоритеты

ORG-QA-05 P2 LOCAL SCOPED ACCEPTED. Production deployment/acceptance не заявляются. Commit/push/deploy не выполнялись.
