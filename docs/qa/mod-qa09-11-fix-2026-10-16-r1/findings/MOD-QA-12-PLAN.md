# PLAN MOD-QA-12 — читаемость уведомлений в списке мест

Новая причина, application patch НЕ применён. Приёмка переводов MOD10 обнаружила отдельный CSS-конфликт. Настоящее действие публикации RU390: после завершения анимации уведомление имеет тёмный фон rgb(22,33,26), текст rgb(15,23,42), фиксированную высоту44px; текст высотой72.875px выходит за рамку. Evidence: ../settled-toast.js.result.json, ../screenshots/SETTLED-success-ru-390.png. Это не ошибка скриншота во время анимации.

Причина: legacy .km-toast и .km-toast__icon в static/admin/css/pages/kidsmap_changelist.css применяются также к новой системе kidsmap_notifications. После устранения конфликта длинное непрерывное название требует переноса в title. Обе правки относятся к layout этого уведомления; тексты/данные/сервисы/публикацию не менять.

Точный scope — **1 существующий файл**:
- static/admin/css/pages/kidsmap_changelist.css: ограничить два legacy-селектора через #km-toast; добавить overflow-wrap:anywhere только для .km-toast-container .km-toast__title в этом page stylesheet. Остальные стили не менять.

Точный candidate: [MOD-QA-12-proposed.diff](MOD-QA-12-proposed.diff), unapplied SHA: [manifest](new-plans-manifest.json). Candidate только в QA. Feasibility через явно SIMULATED перехват CSS/JS response и вход уведомления: исходная версия показала18long-titleFAIL, уточнённый CSS дал18/18success +1domain control PASS; предыдущие18loading controls сохранены. Контраст17.85, long HTML-like name выводится как текст. Это доказательство осуществимости, **не application GREEN**.

После одобрения: только этот CSS patch; реальные loading/publish/unpublish уведомления на собственной карточке RU/AZ/EN×360/390/768/1024/1280/1440 после завершения анимации; contrast/geometry/long names, keyboard close, PNG/console/network. Проверить legacy #km-toast и смежный error toast представительно. Полный261test corpus не повторять. Никаких новых backend tests, зеркалящих CSS.
