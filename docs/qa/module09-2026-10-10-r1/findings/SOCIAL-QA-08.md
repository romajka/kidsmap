# SOCIAL-QA-08 — Отозванное приглашение оставляет пустую403страницу

- Severity: **P2 OPEN**. Execution identity /root; 2026-10-10-r1; LOCAL isolated QA09, HEAD 8d188b316f800fbedf0b1e376905dfd4924cb1b6, source unchanged. Production applicability UNKNOWN. Classification PRE-EXISTING BASELINE; reproducibility fresh, confidence HIGH.
- Роль: получатель приглашения. URL/endpoint: `/ru/account/notifications/<id>/accept/`.
- Шаги: Владелец отправляет приглашение через UI. Получатель оставляет inbox открытым; владелец отменяет приглашение. Получатель нажимает старую Accept.
- Ожидание: Доступ не выдан; интерфейс объясняет устаревшее/отозванное приглашение и предлагает вернуться/обновить inbox.
- Факт: 403 корректно запрещает выдачу прав, но body пустой, ссылок0; пользователь видит белую страницу. Native empty recipient case и БД CANCELLED/no grant подтверждены.
- Доказательство: favorites-notifications:revoked-invitation-denied; final-proof:stale-notification-403-safe PASS/usable-feedback FAIL; [matrix](../matrix.json), raw result artifacts соответствующих scripts, [свежий PNG](../screenshots/notification-403-feedback.png), [manifest](../screenshots-manifest.json).
- Первопричина (source verified): `src/catalog/controllers/workflow_notifications.py:63`. Исключение stale/ValidationError преобразовано в HttpResponseForbidden() без content/template/messages.
- Impact / обоснование: Ограниченный подтверждённый сбой пользовательского сценария/доступности; компрометация, постоянная потеря данных и production авария не установлены.
- Область исправления: Обработать собственное stale/cancelled приглашение понятным AZ/RU/EN состоянием с возвратом в inbox, сохранив403/guard и отсутствие повторного grant. Чужой ID остаётся без информационной утечки.
- Owner/dependencies: django-reviewer + frontend-reviewer + security-reviewer; не раскрывать чужое приглашение, не ослаблять проверки версии/владельца/email/expiry.
- Repair: [самостоятельный копируемый промпт](../repair-prompts/SOCIAL-QA-08.txt). Приложение в этом запуске не исправлялось.
