# SOCIAL-QA-04 — Страница уведомлений не подключает оформление кабинета

- Severity: **P2 OPEN**. Execution identity /root; 2026-10-10-r1; LOCAL isolated QA09, HEAD 8d188b316f800fbedf0b1e376905dfd4924cb1b6, source unchanged. Production applicability UNKNOWN. Classification PRE-EXISTING BASELINE; reproducibility fresh, confidence HIGH.
- Роль: получатель уведомлений, все роли. URL/endpoint: `/ru/account/notifications/, /account/notifications/, /en/account/notifications/`.
- Шаги: Войти, открыть пустой/заполненный inbox на360/390 и PC.
- Ожидание: Навигация кабинета и строки/кнопки уведомлений имеют существующее оформление, понятные состояния и фокус.
- Факт: Синие browser-default ссылки, стандартные кнопки, маркеры списка; account-main-layout display:block во всех18cells. Соседнее избранное с тем же navigation оформлено.
- Доказательство: matrix notifications scenes; proof:notification-account-styles18 FAIL; probe css list; [matrix](../matrix.json), raw result artifacts соответствующих scripts, [свежий PNG](../screenshots/proof-notification-ru-390.png), [manifest](../screenshots-manifest.json).
- Первопричина (source verified): `src/catalog/templates/pages/account_notifications.html:1; static/css/pages/account_profile.css:811; static/css/pages/organization_workspace.css:823`. Template использует account/org классы, но не определяет extra_head для соответствующих CSS; runtime stylesheet list это подтверждает. Внешние fonts blocked не объясняют отсутствие локальных правил.
- Impact / обоснование: Ограниченный подтверждённый сбой пользовательского сценария/доступности; компрометация, постоянная потеря данных и production авария не установлены.
- Область исправления: Подключить правильные существующие стили кабинета и аккуратно определить необходимые inbox rows/buttons. Проверить empty/read/unread/invite/revoked состояния, keyboard и18cells.
- Owner/dependencies: frontend-reviewer; общая навигация и scoped inbox styles, без прав/данных/глобального редизайна.
- Repair: [самостоятельный копируемый промпт](../repair-prompts/SOCIAL-QA-04.txt). Приложение в этом запуске не исправлялось.
