# ORG-QA-05 — меню «Колонки» обрезается слева на телефоне

2026-10-13 LOCAL, P2, root cause отдельно от ORG-QA-03. Checkout `/home/ramin/kidsmap`, HEAD e4e05cc213b34e2d771ecb854901bfd016d1db51, task33-progress +dirty WORKTREE, active_run NONE. IMPLEMENTATION NOT RUN.

`columns-baseline.result.json`: RU390 меню x=-31.296875..138.703125, checkbox x≈-20; mouse action невозможно. QA override исходного CSS по entry hash и нынешний patched CSS дают тот же FAIL, значит baseline, не regression нового wrap. Предыдущий controls run сохранён с timeout/неудачным selector как QA attempts; visual screenshots подтверждают реальные clipped controls.

Причина: на телефоне sort и columns переносятся на две строки; последняя кнопка стоит слева, меню шириной170 выравнивается по её правому краю и выходит в минус. Минимальный fix: в существующее правило `.km-columns-details` в `static/admin/css/pages/kidsmap_changelist.css` добавить `margin-left: auto`, чтобы columns-control занимал правый край доступной строки. Не меняет business logic/ACL/transport/таблицу и не скрывает overflow.

Scope approval: только ORG-QA-05; application file один указанный CSS, собственный unique QA run `docs/qa/org-qa05-fix-2026-10-13-r1/` (или следующий rN), current guide status и module02 full report. После approval — точечный RED→GREEN real browser RU/AZ/EN ×360/390/768/1024/1280/1440 с sidebar, open dropdown rectangles и mouse/keyboard checkbox hide/restore/reload, visible focus, console/network, PNG hashes, source/provenance и shared panel controls. CSS-only tests не писать для копирования implementation. Затем одна полная ACCEPT-02; другие новые findings не исправлять без своего плана.

No commit/push/deploy/production, preserve чужой WORKTREE/active_run/стенды.
