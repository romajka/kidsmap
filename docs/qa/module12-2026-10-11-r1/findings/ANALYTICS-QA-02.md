# ANALYTICS-QA-02 — Событие принимается для активной приватной карточки

LOCAL dirty WORKTREE, HEAD8d188b3; AUDIT ONLY. Status: OPEN; severityP2; confidence HIGH within stated local/SIMULATED scope.

Role: guest. URL/endpoint: `/ru/events/track/`.

Steps: POST phone_click с place_id активного draft2 или archived4. Нативный same-origin порт сначала блокируется; независимый тест и узкий SIMULATED port-header proxy доходят до business validator.

Expected: Отказ, delta событий0 для непубличной карточки.

Actual: 200 {ok:true}, delta+1; contact_actions приватного объекта увеличивается. Ни контакт, ни private content в ответе не раскрываются.

Evidence: [contacts.result.txt](../contacts.result.txt), [native screenshot](../screenshots/private-event-corrupted-owner-ru-390.png). Source: `src/catalog/repositories/tracking_repositories.py:12`.

Root cause: find_active_for_event ограничивает active/deleted, не publication/public visibility.

Priority justification: Загрязнение аналитики приватных карточек; это не доказательство утечки контактов.

Attribution: relevant implementation unchanged against HEAD; pre-existing baseline source failure, no full clean-checkout or production run, new regression not established.

Repair ownership/dependencies: django-reviewer + analytics-reviewer; shared public visibility policy, dependency03 for native port stand.

Scope: Используй существующий shared public-visibility contract при разрешении analytics subject IDs. Проверь published/draft/pending/rejected/archived/inactive/deleted/foreign known IDs, delta0 при отказе; публичный чужой объект может легитимно получать гостевое событие.

[Copyable standalone repair prompt](ANALYTICS-QA-02-repair.txt). No fix performed.
