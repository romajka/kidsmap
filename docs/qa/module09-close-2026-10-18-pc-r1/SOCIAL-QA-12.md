# SOCIAL-QA-12 — P3 OPEN: устаревшая реакция открывает ошибку браузера

Роль: авторизованный пользователь, реагирующий на чужой отзыв. Свежо проверены Place/Specialist, RU/AZ/EN,390/1440. Current dirty source1025, HEAD852938d96764ae315b92859e3651e5ea62054a36; production UNKNOWN.

1. Открыть опубликованный отзыв и оставить вкладку с его revision_id.
2. В другой сессии одобрить новую редакцию этого же отзыва.
3. Нажать «Полезно» в старой вкладке.

Ожидание: отказ409 без записи голоса, понятное сообщение в KidsMap и GET-переход к актуальным отзывам; решение о повторной реакции принимает пользователь.

Факт: server409 и защита данных работают. Но ответ пустой, Chromium показывает собственную страницу HTTP ERROR409 без меню/контекста KidsMap. В12финальных пробах счётчики/реакции/публичная версия не изменились; прямой GET исходной страницы возвращает200 и новый token. Это подтверждённый UX-дефект, не потеря данных и не обход ACL/CAS. P3: затронут редкий конфликт версии; данные защищены, ручной возврат возможен.

Причина: typed_reviews.review_action ловит ReviewConflict и возвращает HttpResponse(status=409). reactions._toggle_review_reaction корректно сравнивает requested/current revision и выбрасывает конфликт. Не менять service guard или статус409. Точное введение UNKNOWN; source для сервера уже такой при полной приёмке, production не проверялся. Отсутствие main на странице браузера само по себе не отдельный дефект SOCIAL11.

Evidence: evidence/stale-recovery.json, native PNG recovery-*-409.png и recovery-*-recovered.png, DBreadback.12status409/12console resource diagnostics/12net::ERR_HTTP_RESPONSE_CODE_FAILURE ожидаемы для фактического пустого ответа и сохранены. Остальные unexpected network/pageerrors0. Одна Place/AZ390 проба восстановлена явной подстановкой исходного stale token после прерванного первого захвата; SIMULATED stale-form transport, backendPOST реальный. Остальные11 — формы, открытые до native moderation.

Два исторических screenshot gaps Place/Specialist теперь разрешены свежими captures; исходные NOTRUN и QA failures не переписаны. Новый ID нужен для фактического поведения recovery, а не для ошибки старого screenshot harness.

Repair: IMPLEMENTATION_PLAN_SOCIAL12.md и proposed-social12.diff. Candidate не применён. Нужен отдельный scope approval; SOCIAL01–11 approvals действуют в прежних границах.
