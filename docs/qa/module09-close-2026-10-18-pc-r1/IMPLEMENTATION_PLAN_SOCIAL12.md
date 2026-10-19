# PLAN SOCIAL-QA-12 — approval pending

Цель: при stale reaction сохранить409 и отказ записи, но показать страницу KidsMap с явной GET-ссылкой к актуальным отзывам. Автоматического повтора голоса нет. Module09 остаётся OPEN.

## Ровно три файла

1. src/catalog/controllers/typed_reviews.py: только except ReviewConflict внутри review_action; если action == react, render catalog/review_reaction_conflict.html со status409, language и reverse typed_reviews(kind,target.pk). Прежний fallback409 для других action сохранить. Всё до catch (target visibility, login/active/self, CSRF, value/revision validation, locking/CAS) неизменно.
2. Новый src/catalog/templates/catalog/review_reaction_conflict.html: extends base, noindex/follow, один внешний main из base, div.container.typed-reviews.km-page-content, локализованные RU/AZ/EN H1/alert/GET-ссылка. Без старых текстов/рейтинга/данных автора, дополнительных form/POST/JS/автоповтора; существующие styles reused, sharedCSS/JS/PO неизменны.
3. Новый src/catalog/testcases/test_social_qa12_reaction_conflict.py:4meaningful methods, четыре kind/три locale, данные только fictional. Точный тестовый кандидат находится в candidate/ вместе с controller/template; SHA в candidate-manifest.json, полный diff в proposed-social12.diff. Тесты выполняются до app patch из собственного scratch module, не добавленного в приложение.

## Проверки и порядок

1. Подтвердить actual current source1025, exact candidate hashes, dirty/ref/index/activeNONE/preservation; при drift обновить план до применения.
2. Сохранить RED нового4method candidate на текущем коде: recovery assertion должен провалиться при409empty, control cases current reaction toggle/counters, anonymous/inactive/self403 и missingCSRF403 должны пройти. Expected RED не превращать вPASS. Результат этого запуска — REPORT/evidence; если setuperror, сначала исправить собственную QA isolation/fixture.
3. После approval применить ровно candidate3files; новый уникальный social-qa12-fix-2026-10-18-pc-r1 и новый owned runtime/DB-cache-media-private-media/current3MO. Без изменения существующих assertions, service guard, статусов/ACL/CAS/CSRF/PO/globalstyles. Новые source1027, кроме controller остальные1024старых source unchanged.
4. GREEN4methods и2affected shared methods из immutable full test-methods: TestReviewEnhancements.test_place_review_reaction_can_be_removed_and_not_duplicated, TestReviewEnhancements.test_place_review_reaction_requires_csrf_token (module catalog.testcases.public). Полный169/global corpus не повторять без новой причины.
5. Native stale→409app page→keyboard GET→200fresh page, четыре kind×RU/AZ/EN×360/390/768/1024/1280/1440. Реальные stale POST и readback no writes; дополнительно один свежий голос после осознанного повторного клика. Проверить status409, H1/alert, одинmain/nooverflow, Tab/Shift+Tab/Enter/focus, GET recovery без automaticPOST, privacy и отсутствие неожиданных console/page/networkerrors. PC/mobile/error PNG+manifest. Fictional auth helpers отдельно SIMULATED, backend actions реальные.
6. Сохранить exact commands/counts/exits, source hashes, snapshots/preservation/guide append-only. Только после evidence закрыть SOCIAL12 и пересмотреть module09; module10 автоматически не начинать.

Scope не включает улучшение других409(reply/report/moderation), публичных SEO-страниц, реакций legacy/site, схемы или DB production. Real screenreader/devices/cross-browser/external/global/production NOTRUN, если не выполнены отдельно. Никаких reset/clean/stash/checkout-switch/commit/push/deploy/active_run assignment. Rollback — только собственные согласованные hunks/newfiles с hash check, без Git reset/clean.

Approval требуется по AGENTS.md:6, новый ID/область. Предыдущие approvals SOCIAL01–11 повторно не запрашиваются. Candidate не применён; preview GREEN не заявляется.
