# SOCIAL-QA-10 — scoped LOCAL closure

2026-10-18 Asia/Baku, /root, canonical kidsmap-orchestrator; no independent-agent claims. User «дальше» approved the exact two-file plan after the scope question; see approval.json and approved-candidate-manifest.json.

## 1. Состояние

**SOCIAL-QA-10 CLOSED LOCAL**, включая alias ADJ-ANONYMOUS-LOGIN-08. Module09 остаётся OPEN для SOCIAL-QA-11/P3. C:/kidsmap, branch codex/module09-transfer-2026-10-16-r1, HEAD852938d96764ae315b92859e3651e5ea62054a36, dirty source1025. Staged empty, task33-progress e4e05cc213b34e2d771ecb854901bfd016d1db51, active_run NONE. Dirty WORKTREE и productionUNKNOWN отделены от HEAD.

## 2. Изменение и результат

Четыре декоратора в src/catalog/controllers/workflow_notifications.py явно задают login_url="account_login". Их порядок над require_GET/POST и тела обработчиков сохранены. Добавлен согласованный src/catalog/testcases/test_social_qa10_notification_login.py с8методами. Exact applied.diff соответствует кандидату; остальные1023исходных файла сохранены.

Guest inbox302→локализованный auth/login200 сохраняет next. Настоящий password login возвращает в исходный inbox, включая query/reload. Global LOGIN_URL, shared auth/routes/templates/JS/CSS/PO/services/schema не менялись.

## 3. Причина

До исправления четыре login_required использовали неподдерживаемый default accounts/login. Теперь они используют существующий named account_login по принятому в проекте шаблону. Исходные18native404 и4failed candidate methods/24subtest failures остались в неизменённом recheck package.

## 4. Технический долг

Generic LOGIN_URL для сторонних потребителей не менялся. В исследованном source default decorators были только у этих четырёх views; graph сам по себе полноту не доказывает. Рефакторинга не было.

## 5. Безопасность и границы

Auth остаётся outermost; CSRF/method/recipient/ownership/currentness не ослаблены. Guest action next остаётся исходным action URL, authenticated GET туда сохраняет405. Автоматического POST replay нет; expired POST UX redesign вне плана. Проверены foreign404, revoked403/no grant и неизменность business aggregates. Записи fictional sessions/last_login ожидаемы при настоящем входе; значения сессий и пароли не экспортированы.

## 6. Legacy / сохранность

Удалений и cleanup чужих ресурсов не было. Предыдущие16evidence packages, source history/sharedMO/.cbmignore/refs/index/activeNONE и entry-container identities проверяются verification.json. Actual state deltas фиксируются отдельно, без восстановления чужих процессов.

## 7. Проверки

-12targeted methods GREEN:8new+4shared,0F/0E/exit0,1.461s; assertions unchanged. Exact command/log/exit в evidence/green-tests.sh, green-tests.log и green-tests.exit.
-18guest native cells AZ/RU/EN×360/390/768/1024/1280/1440:216controlPASS,54action redirect header probes; named target/next/hidden next/form/keyboard/Space/focus/overflow.
-3реальных password flows (AZ390/RU768/EN1440):24controlPASS, Enter submit/302/original inbox/reload/session present. Без OAuth/force-login helper.
-28local HTTP guardsPASS:9authenticated GET405,9missing-CSRF403,9foreign404,1revoked403/feedback. Business counts unchanged; canceled invitation remains canceled.
-268top-level browser/HTTP checksPASS,21nativePNG.0console/pageerrors/unexpected local HTTP/local failed/external blocked requests in completed scripts.

First browser attempt failed in the harness: input[name=next] matched Google/password forms. guest-attempt1-cli.txt retains exit1. Scoped password-form selector fixed the harness; no application/assertion change, no incomplete cell claimedPASS. Complete18-cell retry passed.

Fresh owned app m09s10-fix-r1-app, loopback33400, own media/private-media/cache/locmem email/3MO; current owned isolated QA PostgreSQL reused after volume/internal-network/running/no-published-port proof. New test_m09s10_fix_r1; repository read-only, own scratchRW. Runtime verifies1025sources and sole locale manifest before django.setup. No checkout.env/production credentials.

NOT RUN: unchanged full module corpus repeat, global suite, production, real OAuth/SMTP/external integrations, physical devices/screenreader/cross-browser. Historical169method full acceptance belongs only to preceding1024source snapshot. Manual visual sample: login-ru-390.png and inbox-en.png via view_image; all21 images manually reviewed is not claimed.

## 8. Handoff

Далее отдельный PLAN SOCIAL-QA-11: nested main в typed reviews/inbox. Нужны current1025-source/MO recheck, конкретный diff и approval нового scope. SOCIAL01–10 scoped closures retained, module09OPEN; module10 не начат. Guide получает append этой closure с сохранением прежних bytes.

## 9. Приоритет

SOCIAL10/P2 CLOSED LOCAL; известный SOCIAL11/P3 OPEN. Global/release/production/module09PASS не заявляются. Без commit/push/deploy/reset/clean/stash/checkout switch/автоматического active_run.

Actual entry-container state deltas: [{"name": "m09s06-fix-r1-app", "before": "running", "after": "exited", "cause": "UNKNOWN; no agent stop/restart of entry container"}]. Идентичности сохранены; причинаUNKNOWN, чужих stop/restart не было.
